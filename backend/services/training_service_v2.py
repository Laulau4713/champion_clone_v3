"""
Service de training V2 - Avec jauge émotionnelle et mécaniques avancées.

Intègre:
- Jauge émotionnelle dynamique (0-100)
- Détection comportementale en temps réel
- Objections cachées
- Événements situationnels
- Retournements de situation
- Indices comportementaux
- Cohérence mémorielle

Ce service remplace/étend le TrainingService original.
"""

import json
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.content_agent.agent import ContentAgent
from config import get_settings
from domain.exceptions import (
    ExternalServiceError,
    NotFoundError,
    SessionNotActiveError,
    SessionNotFoundError,
    ValidationError,
)
from models import (
    DifficultyLevel,
    Sector,
    Skill,
    User,
    UserProgress,
    UserSkillProgress,
    VoiceTrainingMessage,
    VoiceTrainingSession,
)
from services.event_service import EventService
from services.jauge_service import BehavioralDetector, JaugeService
from services.voice_service import voice_service

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

settings = get_settings()
logger = structlog.get_logger()


@dataclass
class ProspectResponseV2:
    """Réponse enrichie du prospect V2."""

    text: str
    audio_base64: str | None
    mood: str
    jauge: int  # -1 si caché (medium/expert)
    jauge_delta: int  # 0 si caché
    behavioral_cue: str | None
    is_event: bool
    event_type: str | None
    feedback: dict | None
    conversion_possible: bool

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "audio_base64": self.audio_base64,
            "mood": self.mood,
            "jauge": self.jauge,
            "jauge_delta": self.jauge_delta,
            "behavioral_cue": self.behavioral_cue,
            "is_event": self.is_event,
            "event_type": self.event_type,
            "feedback": self.feedback,
            "conversion_possible": self.conversion_possible,
        }


class TrainingServiceV2:
    """
    Service de training avec mécaniques avancées V2.

    Flow typique:
    1. create_session() - Crée une session avec scénario, jauge, objections cachées
    2. process_user_message() - Analyse comportementale + génération réponse
    3. end_session() - Évaluation finale avec détail des patterns
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        if ANTHROPIC_AVAILABLE and settings.ANTHROPIC_API_KEY:
            self.claude = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            self.claude = None
            logger.warning("anthropic_not_available", message="Claude API not configured")

    async def create_session(self, user: User, skill_slug: str, sector_slug: str | None = None) -> dict:
        """
        Crée une session avec initialisation des mécaniques V2.
        """
        # Récupérer le skill
        skill = await self.db.scalar(select(Skill).where(Skill.slug == skill_slug))
        if not skill:
            raise NotFoundError("Skill", skill_slug)

        # Récupérer le secteur
        sector = None
        if sector_slug:
            sector = await self.db.scalar(select(Sector).where(Sector.slug == sector_slug))

        # Récupérer la progression utilisateur
        progress = await self.db.scalar(select(UserProgress).where(UserProgress.user_id == user.id))
        if not progress:
            progress = UserProgress(user_id=user.id)
            self.db.add(progress)
            await self.db.commit()
            await self.db.refresh(progress)

        level = progress.current_level

        # Récupérer la config du niveau
        level_db = await self.db.scalar(select(DifficultyLevel).where(DifficultyLevel.level == level))
        level_config = {}
        if level_db:
            level_config = {
                "starting_gauge": (level_db.emotional_state_system or {}).get("starting_gauge", 50),
                "conversion_threshold": (level_db.emotional_state_system or {}).get("conversion_threshold", 75),
                "gauge_volatility": (level_db.emotional_state_system or {}).get("gauge_volatility", "medium"),
                "jauge_modifiers": (level_db.emotional_state_system or {}).get("gauge_modifiers", {}),
                "mood_stages": (level_db.emotional_state_system or {}).get("mood_stages", []),
                "hidden_objections": level_db.hidden_objections or {},
                "situational_events": level_db.situational_events or {},
                "reversals": level_db.reversals or {},
                "feedback_settings": level_db.feedback_settings or {},
                "hints_system": level_db.hints_system or {},
            }

        # Initialiser les services
        jauge_service = JaugeService(level=level, level_config=level_config)
        event_service = EventService(level=level, level_config=level_config)

        # Générer le scénario
        content_agent = ContentAgent(db=self.db, llm_client=None)
        scenario = await content_agent.generate_scenario(skill=skill, level=level, sector=sector, use_cache=True)

        # Initialiser les objections cachées si activées
        hidden_objections = []
        hidden_config = level_config.get("hidden_objections", {})
        if hidden_config.get("enabled"):
            probability = hidden_config.get("probability", 0.3)
            if random.random() < probability:
                persona_objections = scenario.get("prospect", {}).get("hidden_objections", [])
                types = hidden_config.get("types", [])
                all_objections = types + persona_objections if persona_objections else types

                if all_objections:
                    max_hidden = hidden_config.get("max_hidden", 1)
                    if hidden_config.get("multiple_hidden"):
                        max_hidden = min(2, len(all_objections))

                    selected = random.sample(all_objections, min(max_hidden, len(all_objections)))
                    hidden_objections = [
                        {
                            "expressed": obj.get("expressed"),
                            "hidden": obj.get("hidden"),
                            "discovery_questions": obj.get("discovery_questions", []),
                            "discovered": False,
                        }
                        for obj in selected
                    ]

        # Créer la session
        starting_jauge = jauge_service.starting_jauge
        initial_mood = jauge_service.get_mood(starting_jauge)

        session = VoiceTrainingSession(
            user_id=user.id,
            skill_id=skill.id,
            sector_id=sector.id if sector else None,
            level=level,
            scenario_json=scenario,
            current_gauge=starting_jauge,
            starting_gauge=starting_jauge,
            gauge_history=[
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "value": starting_jauge,
                    "action": "session_start",
                    "delta": 0,
                }
            ],
            current_mood=initial_mood.mood,
            hidden_objections=hidden_objections,
            discovered_objections=[],
            triggered_events=[],
            positive_actions=[],
            negative_actions=[],
            questions_asked=[],
            conversion_blockers=[],
            status="active",
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        # Générer le message d'ouverture
        opening_text = scenario.get("opening_message", "Bonjour, comment puis-je vous aider ?")

        # Ajouter un indice comportemental selon l'humeur initiale
        if level != "easy":
            behavioral_cue = event_service.get_behavioral_cue(initial_mood.mood, 0)
            if behavioral_cue:
                opening_text = f"{behavioral_cue} {opening_text}"

        # Convertir en audio
        audio_base64 = None
        personality = scenario.get("prospect", {}).get("personality", "neutral")

        if voice_service.is_configured().get("elevenlabs"):
            try:
                audio_bytes, _ = await voice_service.text_to_speech(text=opening_text, personality=personality)
                audio_base64 = voice_service.audio_to_base64(audio_bytes)
            except Exception as e:
                logger.error("tts_error_opening", error=str(e))

        # Sauvegarder le message d'ouverture
        opening_message = VoiceTrainingMessage(
            session_id=session.id, role="prospect", text=opening_text, prospect_mood=initial_mood.mood
        )
        self.db.add(opening_message)
        await self.db.commit()

        logger.info(
            "training_session_v2_created",
            session_id=session.id,
            skill=skill_slug,
            level=level,
            starting_jauge=starting_jauge,
            hidden_objections_count=len(hidden_objections),
        )

        # Préparer la réponse
        show_jauge = level_config.get("feedback_settings", {}).get("show_gauge", level == "easy")

        return {
            "session_id": session.id,
            "scenario": {
                "title": scenario.get("title"),
                "context": scenario.get("context"),
                "prospect": {
                    "name": scenario.get("prospect", {}).get("name"),
                    "role": scenario.get("prospect", {}).get("role"),
                    "company": scenario.get("prospect", {}).get("company"),
                    "personality": personality,
                },
            },
            "skill": {"slug": skill.slug, "name": skill.name, "evaluation_criteria": skill.evaluation_criteria},
            "level": level,
            "jauge": starting_jauge if show_jauge else None,
            "mood": initial_mood.mood,
            "opening_message": {"text": opening_text, "audio_base64": audio_base64},
        }

    async def process_user_message(
        self, session_id: int, user: User, audio_base64: str | None = None, text: str | None = None
    ) -> ProspectResponseV2:
        """
        Traite un message avec toutes les mécaniques V2.
        """
        # Récupérer la session
        session = await self.db.get(VoiceTrainingSession, session_id)
        if not session or session.user_id != user.id:
            raise SessionNotFoundError(session_id)

        if session.status != "active":
            raise SessionNotActiveError(session_id, session.status)

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
                    raise ExternalServiceError("whisper", f"Speech transcription failed: {str(e)}")

        if not user_text:
            raise ValidationError("No text or audio provided")

        # Récupérer la config du niveau
        level_db = await self.db.scalar(select(DifficultyLevel).where(DifficultyLevel.level == session.level))
        level_config = {}
        if level_db and level_db.emotional_state_system:
            level_config = level_db.emotional_state_system

        # Initialiser les services
        jauge_service = JaugeService(level=session.level, level_config=level_config)
        behavioral_detector = BehavioralDetector()
        event_service = EventService(
            level=session.level,
            level_config={
                "situational_events": level_db.situational_events if level_db else {},
                "reversals": level_db.reversals if level_db else {},
            },
        )
        event_service.triggered_events = session.triggered_events or []
        event_service.reversal_triggered = session.reversal_triggered

        # Analyser le message utilisateur
        patterns = behavioral_detector.detect_patterns(user_text)

        # Vérifier les questions fermées consécutives
        if patterns["indicators"]["question_type"] == "closed":
            session.questions_asked = (session.questions_asked or []) + [{"type": "closed", "text": user_text[:100]}]
            if behavioral_detector.detect_closed_question_spam(session.questions_asked or []):
                patterns["negative"].append({"pattern": "closed_question_spam", "action": "closed_question_spam"})
        elif patterns["indicators"]["question_type"] == "open":
            session.questions_asked = (session.questions_asked or []) + [{"type": "open", "text": user_text[:100]}]

        # Vérifier budget demandé trop tôt
        messages_result = await self.db.execute(
            select(VoiceTrainingMessage)
            .where(VoiceTrainingMessage.session_id == session_id)
            .order_by(VoiceTrainingMessage.created_at)
        )
        history = messages_result.scalars().all()
        message_count = len(history)

        if behavioral_detector.detect_budget_question_too_early(user_text, message_count):
            patterns["negative"].append({"pattern": "budget_question_too_early", "action": "budget_question_too_early"})

        # Appliquer les impacts sur la jauge
        jauge_delta = 0
        actions_log = []

        for pos in patterns["positive"]:
            modification = jauge_service.apply_action(session.current_gauge + jauge_delta, pos["action"], "positive")
            jauge_delta += modification.delta
            actions_log.append(modification.to_dict())
            session.positive_actions = (session.positive_actions or []) + [pos["action"]]

        for neg in patterns["negative"]:
            modification = jauge_service.apply_action(session.current_gauge + jauge_delta, neg["action"], "negative")
            jauge_delta += modification.delta
            actions_log.append(modification.to_dict())
            session.negative_actions = (session.negative_actions or []) + [neg["action"]]

            # Vérifier les blockers
            if neg["action"] in jauge_service.CONVERSION_BLOCKERS:
                session.conversion_blockers = (session.conversion_blockers or []) + [neg["action"]]

        # Mettre à jour la jauge
        new_jauge = max(0, min(100, session.current_gauge + jauge_delta))
        session.current_gauge = new_jauge
        session.gauge_history = (session.gauge_history or []) + [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "value": new_jauge,
                "action": "user_message",
                "delta": jauge_delta,
                "patterns": patterns,
            }
        ]

        # Obtenir le nouveau mood
        mood_state = jauge_service.get_mood(new_jauge)
        session.current_mood = mood_state.mood

        # Sauvegarder le message utilisateur
        user_message = VoiceTrainingMessage(
            session_id=session.id,
            role="user",
            text=user_text,
            duration_seconds=speech_duration,
            detected_patterns=patterns,
            gauge_impact=jauge_delta,
        )
        self.db.add(user_message)

        # Vérifier les événements situationnels
        event = event_service.should_trigger_event(message_count=message_count, jauge=new_jauge)

        # Vérifier les retournements (seulement si pas d'événement)
        reversal = None
        if not event:
            reversal = event_service.should_trigger_reversal(
                jauge=new_jauge, closing_attempted=session.closing_attempted
            )
            if reversal:
                session.reversal_triggered = True
                session.reversal_type = reversal.type
                new_jauge = max(0, new_jauge - reversal.jauge_drop)
                session.current_gauge = new_jauge
                mood_state = jauge_service.get_mood(new_jauge)
                session.current_mood = mood_state.mood

        # Mettre à jour les événements déclenchés
        session.triggered_events = event_service.triggered_events

        # Vérifier la conversion
        conversion_possible, _ = jauge_service.check_conversion_possible(
            jauge=new_jauge, blockers=session.conversion_blockers or []
        )
        session.conversion_possible = conversion_possible

        # Générer la réponse du prospect
        prospect_text = await self._generate_prospect_response(
            session=session,
            user_text=user_text,
            mood=mood_state.mood,
            event=event,
            reversal=reversal,
            patterns=patterns,
            history=history,
        )

        # Ajouter un indice comportemental
        behavioral_cue = None
        if session.level != "easy":
            behavioral_cue = event_service.get_behavioral_cue(mood_state.mood, jauge_delta)
            if behavioral_cue:
                prospect_text = f"{behavioral_cue} {prospect_text}"

        # Convertir en audio
        scenario = session.scenario_json
        personality = scenario.get("prospect", {}).get("personality", "neutral")
        if mood_state.mood in ["hostile", "aggressive"]:
            personality = "impatient"
        elif mood_state.mood in ["interested", "ready_to_buy"]:
            personality = "friendly"

        audio_base64_response = None
        if voice_service.is_configured().get("elevenlabs"):
            try:
                audio_bytes, _ = await voice_service.text_to_speech(text=prospect_text, personality=personality)
                audio_base64_response = voice_service.audio_to_base64(audio_bytes)
            except Exception as e:
                logger.error("tts_error_response", error=str(e))

        # Sauvegarder la réponse
        prospect_message = VoiceTrainingMessage(
            session_id=session.id,
            role="prospect",
            text=prospect_text,
            prospect_mood=mood_state.mood,
            is_event=event is not None,
            event_type=event.type if event else None,
            behavioral_cues=[behavioral_cue] if behavioral_cue else [],
        )
        self.db.add(prospect_message)
        await self.db.commit()

        # Générer le feedback (visible selon config du niveau)
        feedback = None
        feedback_settings = level_config.get("feedback_settings", {}) if level_db else {}
        show_jauge = feedback_settings.get("show_gauge", session.level == "easy")
        show_tips = feedback_settings.get("show_tips", session.level == "easy")

        if show_tips or session.level == "easy":
            feedback = {
                "jauge": new_jauge if show_jauge else None,
                "jauge_delta": jauge_delta if show_jauge else None,
                "positive_actions": [p["pattern"] for p in patterns["positive"]],
                "negative_actions": [n["pattern"] for n in patterns["negative"]],
                "tips": self._generate_tips(patterns, mood_state.mood),
            }

        return ProspectResponseV2(
            text=prospect_text,
            audio_base64=audio_base64_response,
            mood=mood_state.mood,
            jauge=new_jauge if show_jauge else -1,
            jauge_delta=jauge_delta if show_jauge else 0,
            behavioral_cue=behavioral_cue,
            is_event=event is not None,
            event_type=event.type if event else None,
            feedback=feedback,
            conversion_possible=conversion_possible,
        )

    async def _generate_prospect_response(
        self,
        session: VoiceTrainingSession,
        user_text: str,
        mood: str,
        event: Any | None,
        reversal: Any | None,
        patterns: dict,
        history: list,
    ) -> str:
        """Génère la réponse du prospect via Claude."""

        scenario = session.scenario_json
        prospect = scenario.get("prospect", {})

        # Si événement, utiliser le texte de l'événement
        if event:
            return event.prospect_says

        # Si retournement, utiliser le texte du retournement
        if reversal:
            return reversal.prospect_says

        if not self.claude:
            return self._get_fallback_response(mood)

        # Construire l'historique pour Claude
        conversation_history = []
        for msg in history[-10:]:  # Derniers 10 messages
            role = "assistant" if msg.role == "prospect" else "user"
            conversation_history.append({"role": role, "content": msg.text})

        conversation_history.append({"role": "user", "content": user_text})

        # Construire le prompt système
        hidden_objections_text = ""
        if session.hidden_objections:
            undiscovered = [o for o in session.hidden_objections if not o.get("discovered")]
            if undiscovered:
                hidden_objections_text = f"""
OBJECTIONS CACHÉES (ne les révèle que si le commercial pose les bonnes questions):
{json.dumps(undiscovered, ensure_ascii=False, indent=2)}
"""

        # Résumé des actions du commercial
        positive_summary = (
            ", ".join(
                [p.get("pattern", str(p)) if isinstance(p, dict) else str(p) for p in patterns.get("positive", [])[:3]]
            )
            or "Aucune"
        )
        negative_summary = (
            ", ".join(
                [n.get("pattern", str(n)) if isinstance(n, dict) else str(n) for n in patterns.get("negative", [])[:3]]
            )
            or "Aucune"
        )

        system_prompt = f"""Tu es {prospect.get("name", "un prospect")}, {prospect.get("role", "professionnel")} chez {prospect.get("company", "une entreprise")}.

PERSONNALITÉ: {prospect.get("personality", "neutral")}
HUMEUR ACTUELLE: {mood}
JAUGE ÉMOTIONNELLE: {session.current_gauge}/100

COMPORTEMENT SELON TON HUMEUR:
- Si hostile/aggressive: Réponses sèches, objections en rafale, menacer de raccrocher
- Si skeptical: Doute affiché, questions pièges, bras croisés métaphoriques
- Si neutral: Écoute sans enthousiasme, réponses courtes
- Si interested: Questions constructives, s'ouvre, partage des infos
- Si ready_to_buy: Signaux d'achat, questions pratiques

TES PROBLÈMES: {", ".join(prospect.get("pain_points", []))}
TON BESOIN CACHÉ: {prospect.get("hidden_need", "non défini")}

{hidden_objections_text}

ACTIONS POSITIVES DU COMMERCIAL: {positive_summary}
ACTIONS NÉGATIVES DU COMMERCIAL: {negative_summary}

RÈGLES:
- Réponds selon ton humeur actuelle ({mood})
- Réponses courtes (1-3 phrases max)
- Si le commercial fait bien, tu peux t'ouvrir un peu
- Si le commercial fait mal, tu te fermes
- Ne facilite JAMAIS la tâche
- Tu peux ajouter des indices comportementaux entre parenthèses: (soupir), (regarde l'heure), etc.

Réponds naturellement en tant que prospect."""

        try:
            response = await self.claude.messages.create(
                model=settings.CLAUDE_SONNET_MODEL, max_tokens=200, system=system_prompt, messages=conversation_history
            )

            return response.content[0].text

        except Exception as e:
            logger.error("claude_prospect_error", error=str(e))
            return self._get_fallback_response(mood)

    def _get_fallback_response(self, mood: str) -> str:
        """Réponse de fallback si Claude n'est pas disponible."""
        fallbacks = {
            "hostile": "Je n'ai pas le temps pour ça.",
            "aggressive": "Écoutez, je ne suis vraiment pas convaincu.",
            "skeptical": "Hmm... vous me dites ça, mais concrètement?",
            "resistant": "Je ne sais pas trop...",
            "neutral": "D'accord, continuez.",
            "interested": "C'est intéressant. Pouvez-vous m'en dire plus?",
            "ready_to_buy": "Oui, ça m'intéresse. Comment on procède?",
        }
        return fallbacks.get(mood, "Je comprends. Continuez...")

    def _generate_tips(self, patterns: dict, mood: str) -> list[str]:
        """Génère des conseils basés sur l'analyse."""
        tips = []

        if not patterns["positive"]:
            tips.append("Essaie de reformuler ce que le prospect vient de dire")

        if patterns.get("indicators", {}).get("hesitation_count", 0) > 2:
            tips.append("Trop d'hésitations - prends confiance!")

        if mood in ["hostile", "aggressive"]:
            tips.append("Le prospect se ferme - montre de l'empathie")

        if mood == "skeptical":
            tips.append("Il teste - reste calme et factuel")

        if mood == "interested":
            tips.append("Bon travail! Continue sur cette lancée")

        if mood == "ready_to_buy":
            tips.append("Il est prêt - tente un closing!")

        # Conseils basés sur les patterns négatifs
        for neg in patterns.get("negative", []):
            if neg["action"] == "closed_question_spam":
                tips.append("Pose des questions ouvertes (Comment? Pourquoi?)")
            elif neg["action"] == "interruption":
                tips.append("Laisse le prospect finir de parler")

        return tips[:3]  # Max 3 tips

    async def end_session(self, session_id: int, user: User) -> dict:
        """
        Termine la session et génère l'évaluation finale V2.
        """
        session = await self.db.get(VoiceTrainingSession, session_id)
        if not session or session.user_id != user.id:
            raise SessionNotFoundError(session_id)

        # Récupérer tous les messages
        messages_result = await self.db.execute(
            select(VoiceTrainingMessage)
            .where(VoiceTrainingMessage.session_id == session_id)
            .order_by(VoiceTrainingMessage.created_at)
        )
        messages = messages_result.scalars().all()

        # Récupérer le skill
        skill = await self.db.get(Skill, session.skill_id)

        # Générer l'évaluation finale
        evaluation = await self._generate_final_evaluation(session=session, skill=skill, messages=messages)

        # Mettre à jour la session
        session.status = "completed" if not session.converted else "converted"
        session.completed_at = datetime.utcnow()
        session.score = evaluation["overall_score"]
        session.feedback_json = evaluation

        # Mettre à jour la progression
        progress = await self.db.scalar(select(UserProgress).where(UserProgress.user_id == user.id))

        if progress:
            skill_progress = await self.db.scalar(
                select(UserSkillProgress).where(
                    UserSkillProgress.user_progress_id == progress.id, UserSkillProgress.skill_id == skill.id
                )
            )

            if not skill_progress:
                skill_progress = UserSkillProgress(user_progress_id=progress.id, skill_id=skill.id)
                self.db.add(skill_progress)

            skill_progress.scenarios_completed = (skill_progress.scenarios_completed or 0) + 1
            if evaluation["overall_score"] >= skill.pass_threshold:
                skill_progress.scenarios_passed = (skill_progress.scenarios_passed or 0) + 1

            if evaluation["overall_score"] > (skill_progress.best_score or 0):
                skill_progress.best_score = evaluation["overall_score"]

            # Recalculer la moyenne
            total = skill_progress.scenarios_completed or 1
            current_avg = skill_progress.average_score or 0
            skill_progress.average_score = ((current_avg * (total - 1)) + evaluation["overall_score"]) / total

            # Vérifier validation
            if (skill_progress.scenarios_passed or 0) >= skill.scenarios_required and skill_progress.quiz_passed:
                skill_progress.is_validated = True
                skill_progress.validated_at = datetime.utcnow()

            # Stats globales
            progress.total_scenarios_completed = (progress.total_scenarios_completed or 0) + 1
            total_duration = sum(m.duration_seconds or 0 for m in messages if m.role == "user")
            progress.total_training_minutes = (progress.total_training_minutes or 0) + int(total_duration / 60)

        await self.db.commit()

        logger.info(
            "training_session_v2_completed",
            session_id=session_id,
            score=evaluation["overall_score"],
            final_gauge=session.current_gauge,
            converted=session.converted,
        )

        return {"session_id": session_id, "status": session.status, "evaluation": evaluation}

    async def _generate_final_evaluation(self, session: VoiceTrainingSession, skill: Skill, messages: list) -> dict:
        """Génère l'évaluation finale V2 de la session."""

        # Calcul basé sur les métriques collectées
        positive_count = len(session.positive_actions or [])
        negative_count = len(session.negative_actions or [])
        final_gauge = session.current_gauge
        starting_gauge = session.starting_gauge

        # Score de base sur la jauge
        gauge_score = final_gauge * 0.4  # 40% du score basé sur la jauge finale

        # Bonus pour progression
        gauge_progression = final_gauge - starting_gauge
        progression_bonus = min(20, max(-20, gauge_progression * 0.3))

        # Bonus/malus pour patterns
        pattern_score = (positive_count * 3) - (negative_count * 4)
        pattern_score = max(-20, min(20, pattern_score))

        # Malus pour blockers
        blocker_penalty = len(session.conversion_blockers or []) * 10

        # Bonus pour conversion
        conversion_bonus = 15 if session.converted else 0

        # Score final
        overall_score = gauge_score + progression_bonus + pattern_score - blocker_penalty + conversion_bonus
        overall_score = max(0, min(100, overall_score))

        # Points forts et axes d'amélioration
        points_forts = []
        if positive_count > 3:
            points_forts.append("Bonne utilisation des techniques commerciales")
        if gauge_progression > 20:
            points_forts.append("Progression significative de la relation")
        if session.converted:
            points_forts.append("Conversion réussie!")
        if not session.reversal_triggered or session.current_gauge > 60:
            points_forts.append("Bonne gestion des situations difficiles")

        axes_amelioration = []
        if negative_count > positive_count:
            axes_amelioration.append("Réduire les erreurs comportementales")
        if gauge_progression < 0:
            axes_amelioration.append("Améliorer la relation avec le prospect")
        if session.conversion_blockers:
            blockers = session.conversion_blockers or []
            if "lost_temper" in blockers:
                axes_amelioration.append("Garder son calme sous pression")
            if "denigrated_competitor" in blockers:
                axes_amelioration.append("Ne pas dénigrer la concurrence")
        if session.interruption_count > 2:
            axes_amelioration.append("Laisser le prospect s'exprimer")

        # Si Claude est disponible, enrichir l'évaluation
        if self.claude:
            try:
                evaluation = await self._enrich_evaluation_with_claude(
                    session, skill, messages, overall_score, points_forts, axes_amelioration
                )
                return evaluation
            except Exception as e:
                logger.error("claude_evaluation_error", error=str(e))

        return {
            "overall_score": round(overall_score),
            "final_jauge": final_gauge,
            "jauge_progression": gauge_progression,
            "positive_actions_count": positive_count,
            "negative_actions_count": negative_count,
            "converted": session.converted,
            "points_forts": points_forts or ["Continue tes efforts!"],
            "axes_amelioration": axes_amelioration or ["Continue à pratiquer"],
            "conseil_principal": self._get_main_advice(session, overall_score),
            "passed": overall_score >= skill.pass_threshold,
        }

    async def _enrich_evaluation_with_claude(
        self,
        session: VoiceTrainingSession,
        skill: Skill,
        messages: list,
        base_score: float,
        points_forts: list[str],
        axes_amelioration: list[str],
    ) -> dict:
        """Enrichit l'évaluation avec Claude."""

        conversation = "\n".join([f"{'COMMERCIAL' if m.role == 'user' else 'PROSPECT'}: {m.text}" for m in messages])

        prompt = f"""Évalue cette session d'entraînement commercial V2.

SKILL: {skill.name}
NIVEAU: {session.level}

MÉTRIQUES COLLECTÉES:
- Jauge finale: {session.current_gauge}/100 (départ: {session.starting_gauge})
- Actions positives: {len(session.positive_actions or [])}
- Actions négatives: {len(session.negative_actions or [])}
- Conversion: {"Oui" if session.converted else "Non"}
- Blockers: {session.conversion_blockers or "Aucun"}

CONVERSATION:
{conversation[:3000]}

Analyse et complète cette évaluation en JSON (garde le score proche de {base_score}):
{{
    "overall_score": {base_score},
    "points_forts": {json.dumps(points_forts, ensure_ascii=False)},
    "axes_amelioration": {json.dumps(axes_amelioration, ensure_ascii=False)},
    "conseil_principal": "un conseil personnalisé",
    "analyse_detaillee": "2-3 phrases d'analyse"
}}"""

        response = await self.claude.messages.create(
            model=settings.CLAUDE_SONNET_MODEL, max_tokens=400, messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text

        # Extraire le JSON même si Claude ajoute du texte autour
        json_str = content.strip()
        if not json_str.startswith("{"):
            # Chercher le premier { et le dernier }
            start = json_str.find("{")
            end = json_str.rfind("}") + 1
            if start != -1 and end > start:
                json_str = json_str[start:end]

        try:
            result = json.loads(json_str)
            result["final_jauge"] = session.current_gauge
            result["jauge_progression"] = session.current_gauge - session.starting_gauge
            result["converted"] = session.converted
            result["passed"] = result.get("overall_score", base_score) >= skill.pass_threshold
            return result
        except json.JSONDecodeError as e:
            logger.warning("claude_json_parse_error", error=str(e), content=content[:200])
            # Fallback avec score de base
            return {
                "overall_score": base_score,
                "final_jauge": session.current_gauge,
                "jauge_progression": session.current_gauge - session.starting_gauge,
                "converted": session.converted,
                "passed": base_score >= skill.pass_threshold,
                "conseil_principal": self._get_main_advice(session, base_score),
                "analyse_detaillee": "Évaluation automatique basée sur la progression de la jauge.",
            }

    def _get_main_advice(self, session: VoiceTrainingSession, score: float) -> str:
        """Retourne un conseil principal basé sur la session."""

        if score >= 85:
            return "Excellent travail! Tu maîtrises les fondamentaux."
        elif score >= 70:
            return "Bon travail! Continue à affiner tes techniques."
        elif score >= 50:
            return "Tu progresses. Concentre-toi sur l'écoute active."
        else:
            if session.conversion_blockers:
                return "Attention aux erreurs critiques. Reste calme et professionnel."
            return "Continue à pratiquer les fondamentaux."

    async def get_session(self, session_id: int, user: User) -> dict | None:
        """Récupère les détails d'une session V2."""
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
            "current_gauge": session.current_gauge,
            "starting_gauge": session.starting_gauge,
            "current_mood": session.current_mood,
            "conversion_possible": session.conversion_possible,
            "converted": session.converted,
            "score": session.score,
            "feedback": session.feedback_json,
            "gauge_history": session.gauge_history,
            "positive_actions": session.positive_actions,
            "negative_actions": session.negative_actions,
            "messages": [
                {
                    "role": m.role,
                    "text": m.text,
                    "duration": m.duration_seconds,
                    "mood": m.prospect_mood,
                    "gauge_impact": m.gauge_impact,
                    "patterns": m.detected_patterns,
                    "is_event": m.is_event,
                    "event_type": m.event_type,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
            "created_at": session.created_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        }
