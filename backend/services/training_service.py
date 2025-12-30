"""
Service de training : gère les sessions d'entraînement avec voix.

Coordonne:
- ContentAgent pour la génération de scénarios
- VoiceService pour TTS/STT
- InterruptionService pour les interruptions selon la difficulté
- Claude pour les réponses du prospect
"""

import json
from typing import Optional
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from models import (
    User, Skill, Sector, DifficultyLevel,
    UserProgress, UserSkillProgress,
    VoiceTrainingSession, VoiceTrainingMessage
)
from services.voice_service import voice_service
from services.interruption_service import InterruptionService
from agents.content_agent.agent import ContentAgent
from config import get_settings

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

settings = get_settings()
logger = structlog.get_logger()


@dataclass
class ProspectResponse:
    """Réponse du prospect."""
    text: str
    audio_base64: Optional[str]
    emotion: str  # "neutral", "interested", "skeptical", "impatient"
    should_interrupt: bool
    interruption_reason: Optional[str]
    feedback: Optional[dict]


class TrainingService:
    """
    Gère les sessions d'entraînement complètes avec voix.

    Flow typique:
    1. create_session() - Crée une session avec scénario et message d'ouverture
    2. process_user_message() - Traite le message utilisateur et génère réponse
    3. end_session() - Termine et génère l'évaluation finale
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        if ANTHROPIC_AVAILABLE and settings.ANTHROPIC_API_KEY:
            self.claude = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            self.claude = None
            logger.warning("anthropic_not_available", message="Claude API not configured")

    async def create_session(
        self,
        user: User,
        skill_slug: str,
        sector_slug: Optional[str] = None
    ) -> dict:
        """
        Crée une nouvelle session d'entraînement.

        Args:
            user: Utilisateur courant
            skill_slug: Slug du skill à pratiquer
            sector_slug: Slug du secteur (optionnel)

        Returns:
            Session info avec scénario et message d'ouverture (audio inclus)
        """
        # Récupérer le skill
        skill = await self.db.scalar(
            select(Skill).where(Skill.slug == skill_slug)
        )
        if not skill:
            raise ValueError(f"Skill not found: {skill_slug}")

        # Récupérer le secteur (optionnel)
        sector = None
        if sector_slug:
            sector = await self.db.scalar(
                select(Sector).where(Sector.slug == sector_slug)
            )

        # Récupérer la progression utilisateur
        progress = await self.db.scalar(
            select(UserProgress).where(UserProgress.user_id == user.id)
        )
        if not progress:
            progress = UserProgress(user_id=user.id)
            self.db.add(progress)
            await self.db.commit()
            await self.db.refresh(progress)

        # Générer le scénario via ContentAgent
        content_agent = ContentAgent(db=self.db, llm_client=None)
        scenario = await content_agent.generate_scenario(
            skill=skill,
            level=progress.current_level,
            sector=sector,
            user_history=None,
            use_cache=True
        )

        # Créer la session en DB
        session = VoiceTrainingSession(
            user_id=user.id,
            skill_id=skill.id,
            sector_id=sector.id if sector else None,
            level=progress.current_level,
            scenario_json=scenario,
            status="active"
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        # Générer le message d'ouverture du prospect
        opening_text = scenario.get("opening_message", "Bonjour, comment puis-je vous aider ?")

        # Convertir en audio si ElevenLabs est configuré
        audio_base64 = None
        personality = scenario.get("prospect", {}).get("personality", "neutral")

        if voice_service.is_configured().get("elevenlabs"):
            try:
                audio_bytes, _ = await voice_service.text_to_speech(
                    text=opening_text,
                    personality=personality
                )
                audio_base64 = voice_service.audio_to_base64(audio_bytes)
            except Exception as e:
                logger.error("tts_error_opening", error=str(e))

        # Sauvegarder le message d'ouverture
        opening_message = VoiceTrainingMessage(
            session_id=session.id,
            role="prospect",
            text=opening_text
        )
        self.db.add(opening_message)
        await self.db.commit()

        logger.info(
            "training_session_created",
            session_id=session.id,
            skill=skill_slug,
            level=progress.current_level
        )

        return {
            "session_id": session.id,
            "scenario": {
                "title": scenario.get("title"),
                "context": scenario.get("context"),
                "prospect": {
                    "name": scenario.get("prospect", {}).get("name"),
                    "role": scenario.get("prospect", {}).get("role"),
                    "company": scenario.get("prospect", {}).get("company"),
                    "personality": personality
                }
            },
            "skill": {
                "slug": skill.slug,
                "name": skill.name,
                "evaluation_criteria": skill.evaluation_criteria
            },
            "level": progress.current_level,
            "opening_message": {
                "text": opening_text,
                "audio_base64": audio_base64
            }
        }

    async def process_user_message(
        self,
        session_id: int,
        user: User,
        audio_base64: Optional[str] = None,
        text: Optional[str] = None
    ) -> ProspectResponse:
        """
        Traite un message de l'utilisateur et génère la réponse du prospect.

        Args:
            session_id: ID de la session
            user: Utilisateur
            audio_base64: Audio de l'utilisateur en base64 (optionnel)
            text: Texte de l'utilisateur (optionnel, si pas d'audio)

        Returns:
            ProspectResponse avec texte, audio et feedback
        """
        # Récupérer la session
        session = await self.db.get(VoiceTrainingSession, session_id)
        if not session or session.user_id != user.id:
            raise ValueError("Session not found")

        if session.status != "active":
            raise ValueError("Session is not active")

        # Transcrire l'audio si fourni
        user_text = text
        speech_duration = 0.0

        if audio_base64 and voice_service.is_configured().get("whisper"):
            try:
                audio_bytes = voice_service.base64_to_audio(audio_base64)
                transcription = await voice_service.speech_to_text(audio_bytes)
                user_text = transcription["text"]
                speech_duration = transcription.get("duration", 0)
            except Exception as e:
                logger.error("stt_error", error=str(e))
                if not text:
                    raise ValueError(f"Speech transcription failed: {str(e)}")

        if not user_text:
            raise ValueError("No text or audio provided")

        # Sauvegarder le message utilisateur
        user_message = VoiceTrainingMessage(
            session_id=session.id,
            role="user",
            text=user_text,
            duration_seconds=speech_duration
        )
        self.db.add(user_message)

        # Récupérer l'historique des messages
        messages_result = await self.db.execute(
            select(VoiceTrainingMessage)
            .where(VoiceTrainingMessage.session_id == session_id)
            .order_by(VoiceTrainingMessage.created_at)
        )
        history = messages_result.scalars().all()

        # Construire le contexte
        scenario = session.scenario_json
        prospect = scenario.get("prospect", {})
        skill = await self.db.get(Skill, session.skill_id)

        # Vérifier si on doit interrompre (selon la difficulté)
        interruption_service = InterruptionService(level=session.level)

        # Compter les hésitations dans le texte
        hesitation_words = ["euh", "hum", "enfin", "donc", "voilà", "en fait", "peut-être", "je pense"]
        hesitation_count = sum(1 for w in hesitation_words if w in user_text.lower())

        interruption = interruption_service.should_interrupt(
            speaking_duration=speech_duration,
            hesitation_count=hesitation_count
        )

        # Générer la réponse du prospect via Claude
        prospect_response = await self._generate_prospect_response(
            scenario=scenario,
            skill=skill,
            history=history,
            user_message=user_text,
            should_interrupt=interruption.should_interrupt,
            interruption_phrase=interruption.phrase
        )

        # Déterminer la personnalité pour la voix
        personality = prospect.get("personality", "neutral")
        if interruption.should_interrupt:
            personality = "impatient"  # Voix plus agressive pour l'interruption

        # Convertir en audio si disponible
        audio_base64_response = None
        if voice_service.is_configured().get("elevenlabs"):
            try:
                audio_bytes, _ = await voice_service.text_to_speech(
                    text=prospect_response["text"],
                    personality=personality
                )
                audio_base64_response = voice_service.audio_to_base64(audio_bytes)
            except Exception as e:
                logger.error("tts_error_response", error=str(e))

        # Sauvegarder la réponse du prospect
        prospect_message = VoiceTrainingMessage(
            session_id=session.id,
            role="prospect",
            text=prospect_response["text"]
        )
        self.db.add(prospect_message)
        await self.db.commit()

        # Générer le feedback en temps réel
        feedback = await self._generate_realtime_feedback(
            skill=skill,
            user_message=user_text,
            prospect_response=prospect_response["text"],
            hesitation_count=hesitation_count
        )

        return ProspectResponse(
            text=prospect_response["text"],
            audio_base64=audio_base64_response,
            emotion=prospect_response.get("emotion", "neutral"),
            should_interrupt=interruption.should_interrupt,
            interruption_reason=interruption.reason,
            feedback=feedback
        )

    async def end_session(
        self,
        session_id: int,
        user: User
    ) -> dict:
        """
        Termine la session et génère l'évaluation finale.

        Args:
            session_id: ID de la session
            user: Utilisateur

        Returns:
            Evaluation complète avec scores et feedback
        """
        session = await self.db.get(VoiceTrainingSession, session_id)
        if not session or session.user_id != user.id:
            raise ValueError("Session not found")

        # Récupérer tous les messages
        messages_result = await self.db.execute(
            select(VoiceTrainingMessage)
            .where(VoiceTrainingMessage.session_id == session_id)
            .order_by(VoiceTrainingMessage.created_at)
        )
        messages = messages_result.scalars().all()

        # Récupérer le skill
        skill = await self.db.get(Skill, session.skill_id)

        # Générer l'évaluation finale via Claude
        evaluation = await self._generate_final_evaluation(
            scenario=session.scenario_json,
            skill=skill,
            messages=messages
        )

        # Mettre à jour la session
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        session.score = evaluation["overall_score"]
        session.feedback_json = evaluation

        # Mettre à jour la progression du skill
        progress = await self.db.scalar(
            select(UserProgress).where(UserProgress.user_id == user.id)
        )

        if progress:
            skill_progress = await self.db.scalar(
                select(UserSkillProgress).where(
                    UserSkillProgress.user_progress_id == progress.id,
                    UserSkillProgress.skill_id == skill.id
                )
            )

            if not skill_progress:
                skill_progress = UserSkillProgress(
                    user_progress_id=progress.id,
                    skill_id=skill.id,
                    scenarios_completed=0,
                    scenarios_passed=0,
                    best_score=0.0,
                    average_score=0.0
                )
                self.db.add(skill_progress)

            skill_progress.scenarios_completed = (skill_progress.scenarios_completed or 0) + 1
            if evaluation["overall_score"] >= skill.pass_threshold:
                skill_progress.scenarios_passed = (skill_progress.scenarios_passed or 0) + 1

            current_best = skill_progress.best_score or 0.0
            if evaluation["overall_score"] > current_best:
                skill_progress.best_score = evaluation["overall_score"]

            # Recalculer la moyenne
            total = skill_progress.scenarios_completed or 1
            current_avg = skill_progress.average_score or 0.0
            new_score = evaluation["overall_score"]
            skill_progress.average_score = ((current_avg * (total - 1)) + new_score) / total

            # Vérifier si le skill est validé
            scenarios_passed = skill_progress.scenarios_passed or 0
            if (scenarios_passed >= skill.scenarios_required
                    and skill_progress.quiz_passed):
                skill_progress.is_validated = True
                skill_progress.validated_at = datetime.utcnow()

            # Mettre à jour les stats globales
            progress.total_scenarios_completed = (progress.total_scenarios_completed or 0) + 1
            total_duration = sum(m.duration_seconds or 0 for m in messages if m.role == "user")
            progress.total_training_minutes = (progress.total_training_minutes or 0) + int(total_duration / 60)

        await self.db.commit()

        logger.info(
            "training_session_completed",
            session_id=session_id,
            score=evaluation["overall_score"],
            passed=evaluation.get("passed", False)
        )

        return {
            "session_id": session_id,
            "status": "completed",
            "evaluation": evaluation
        }

    async def _generate_prospect_response(
        self,
        scenario: dict,
        skill: Skill,
        history: list,
        user_message: str,
        should_interrupt: bool,
        interruption_phrase: Optional[str]
    ) -> dict:
        """Génère la réponse du prospect via Claude."""

        if not self.claude:
            # Fallback sans Claude
            return {
                "text": "Je comprends. Pouvez-vous m'en dire plus ?",
                "emotion": "neutral"
            }

        prospect = scenario.get("prospect", {})

        # Construire l'historique pour Claude
        conversation_history = []
        for msg in history:
            role = "assistant" if msg.role == "prospect" else "user"
            conversation_history.append({
                "role": role,
                "content": msg.text
            })

        # Ajouter le dernier message de l'utilisateur
        conversation_history.append({
            "role": "user",
            "content": user_message
        })

        interruption_instruction = ""
        if should_interrupt and interruption_phrase:
            interruption_instruction = f"\n\nINTERRUPTION: Tu dois interrompre le commercial. Commence ta réponse par: \"{interruption_phrase}\""

        system_prompt = f"""Tu es {prospect.get('name', 'un prospect')}, {prospect.get('role', 'professionnel')} chez {prospect.get('company', 'une entreprise')}.

PERSONNALITÉ: {prospect.get('personality', 'neutral')}
HUMEUR: {prospect.get('mood', 'neutral')}
TES PROBLÈMES: {', '.join(prospect.get('pain_points', []))}
TON BESOIN CACHÉ: {prospect.get('hidden_need', 'non défini')}

CONTEXTE: {scenario.get('context', '')}

RÈGLES:
- Tu joues le rôle du prospect de manière réaliste
- Tu ne facilites pas la tâche au commercial
- Tu réagis naturellement selon ta personnalité
- Tes réponses sont courtes (1-3 phrases max)
- Tu peux poser des questions, lever des objections
- Si le commercial fait bien, tu t'ouvres progressivement
- Si le commercial fait mal, tu te fermes ou deviens sceptique{interruption_instruction}

Réponds en JSON:
{{"text": "ta réponse", "emotion": "neutral|interested|skeptical|impatient"}}
"""

        try:
            response = await self.claude.messages.create(
                model=settings.CLAUDE_SONNET_MODEL,
                max_tokens=300,
                system=system_prompt,
                messages=conversation_history
            )

            # Parser la réponse
            content = response.content[0].text

            # Essayer de parser comme JSON
            if content.strip().startswith("{"):
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    pass

            return {"text": content, "emotion": "neutral"}

        except Exception as e:
            logger.error("claude_prospect_error", error=str(e))
            return {
                "text": "Hmm, je vois. Continuez...",
                "emotion": "neutral"
            }

    async def _generate_realtime_feedback(
        self,
        skill: Skill,
        user_message: str,
        prospect_response: str,
        hesitation_count: int
    ) -> dict:
        """Génère un feedback en temps réel sur la dernière réponse."""

        if not self.claude:
            return {
                "points_positifs": [],
                "points_amelioration": [],
                "conseil": "Continuez à pratiquer !"
            }

        criteria = skill.evaluation_criteria or []

        prompt = f"""Évalue cette réponse commerciale pour le skill "{skill.name}".

RÉPONSE DU COMMERCIAL: "{user_message}"
RÉACTION DU PROSPECT: "{prospect_response}"
HÉSITATIONS DÉTECTÉES: {hesitation_count}

CRITÈRES D'ÉVALUATION:
{json.dumps(criteria, ensure_ascii=False, indent=2)}

Donne un feedback COURT (2-3 points max) en JSON:
{{"points_positifs": ["..."], "points_amelioration": ["..."], "conseil": "..."}}
"""

        try:
            response = await self.claude.messages.create(
                model=settings.CLAUDE_SONNET_MODEL,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            if content.strip().startswith("{"):
                return json.loads(content)

        except Exception as e:
            logger.error("claude_feedback_error", error=str(e))

        return {
            "points_positifs": [],
            "points_amelioration": [],
            "conseil": "Continue comme ça !"
        }

    async def _generate_final_evaluation(
        self,
        scenario: dict,
        skill: Skill,
        messages: list
    ) -> dict:
        """Génère l'évaluation finale de la session."""

        if not self.claude:
            return {
                "overall_score": 50,
                "criteria_scores": [],
                "points_forts": [],
                "axes_amelioration": ["Évaluation non disponible (Claude non configuré)"],
                "conseil_principal": "Configurez l'API Claude pour obtenir une évaluation détaillée.",
                "passed": False
            }

        # Construire la conversation
        conversation = "\n".join([
            f"{'COMMERCIAL' if m.role == 'user' else 'PROSPECT'}: {m.text}"
            for m in messages
        ])

        criteria = skill.evaluation_criteria or []

        prompt = f"""Évalue cette session d'entraînement commercial.

SKILL: {skill.name}
DESCRIPTION: {skill.description}

SCÉNARIO:
- Prospect: {scenario.get('prospect', {}).get('name')} - {scenario.get('prospect', {}).get('role')}
- Contexte: {scenario.get('context')}

CRITÈRES D'ÉVALUATION:
{json.dumps(criteria, ensure_ascii=False, indent=2)}

CONVERSATION:
{conversation}

Évalue en JSON:
{{
    "overall_score": 0-100,
    "criteria_scores": [
        {{"name": "critère", "score": 0-100, "comment": "..."}}
    ],
    "points_forts": ["..."],
    "axes_amelioration": ["..."],
    "conseil_principal": "...",
    "passed": true/false
}}

Le seuil de validation est {skill.pass_threshold}%.
"""

        try:
            response = await self.claude.messages.create(
                model=settings.CLAUDE_SONNET_MODEL,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            if content.strip().startswith("{"):
                return json.loads(content)

        except Exception as e:
            logger.error("claude_evaluation_error", error=str(e))

        return {
            "overall_score": 50,
            "criteria_scores": [],
            "points_forts": [],
            "axes_amelioration": ["Évaluation non disponible"],
            "conseil_principal": "Réessaie !",
            "passed": False
        }

    async def get_session(self, session_id: int, user: User) -> Optional[dict]:
        """Récupère les détails d'une session."""
        session = await self.db.get(VoiceTrainingSession, session_id)
        if not session or session.user_id != user.id:
            return None

        skill = await self.db.get(Skill, session.skill_id)
        sector = await self.db.get(Sector, session.sector_id) if session.sector_id else None

        messages_result = await self.db.execute(
            select(VoiceTrainingMessage)
            .where(VoiceTrainingMessage.session_id == session_id)
            .order_by(VoiceTrainingMessage.created_at)
        )
        messages = messages_result.scalars().all()

        return {
            "session_id": session.id,
            "status": session.status,
            "level": session.level,
            "skill": {"slug": skill.slug, "name": skill.name} if skill else None,
            "sector": {"slug": sector.slug, "name": sector.name} if sector else None,
            "scenario": session.scenario_json,
            "score": session.score,
            "feedback": session.feedback_json,
            "messages": [
                {
                    "role": m.role,
                    "text": m.text,
                    "duration": m.duration_seconds,
                    "created_at": m.created_at.isoformat()
                }
                for m in messages
            ],
            "created_at": session.created_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        }
