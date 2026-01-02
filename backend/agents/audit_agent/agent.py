"""
AuditAgent - Evaluation independante des sessions de training.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Any

import anthropic
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from models import Skill, User, UserProgress, UserSkillProgress, VoiceTrainingMessage, VoiceTrainingSession

from .prompts import CHAMPION_COMPARISON_PROMPT, PROGRESS_REPORT_PROMPT, SESSION_AUDIT_PROMPT, WEEKLY_DIGEST_PROMPT
from .schemas import ChampionComparison, PerformanceLevel, SessionAudit, UserProgressReport, WeeklyDigest

settings = get_settings()
logger = structlog.get_logger()


class AuditAgent:
    """
    Agent d'audit independant pour evaluer les performances de training.

    Separe du TrainingAgent pour garantir une evaluation objective
    sans biais du LLM qui joue le prospect.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_SONNET_MODEL  # Sonnet pour l'audit (bon rapport qualite/cout)

    async def audit_session(self, session_id: int, champion_patterns: dict | None = None) -> SessionAudit:
        """
        Audit complet d'une session de training.

        Args:
            session_id: ID de la session a auditer
            champion_patterns: Patterns du champion pour comparaison (optionnel)

        Returns:
            SessionAudit avec analyse complete
        """
        # Recuperer la session
        session = await self.db.get(VoiceTrainingSession, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Recuperer les messages
        messages_result = await self.db.execute(
            select(VoiceTrainingMessage)
            .where(VoiceTrainingMessage.session_id == session_id)
            .order_by(VoiceTrainingMessage.created_at)
        )
        messages = messages_result.scalars().all()

        # Construire le contexte pour l'audit
        context = self._build_session_context(session, messages)

        # Ajouter les patterns champion si disponibles
        if champion_patterns:
            context["champion_patterns"] = champion_patterns

        # Appeler Claude pour l'audit
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=SESSION_AUDIT_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyse cette session de training:\n\n{json.dumps(context, ensure_ascii=False, indent=2, default=str)}",
                }
            ],
        )

        # Parser la reponse
        audit_data = self._parse_json_response(response.content[0].text)

        # Construire l'objet SessionAudit
        audit = self._build_session_audit(session, audit_data)

        # Sauvegarder l'audit en DB
        await self._save_audit(session_id, audit)

        logger.info(
            "session_audited", session_id=session_id, score=audit.overall_score, level=audit.performance_level.value
        )

        return audit

    async def generate_progress_report(self, user_id: int, days: int = 7) -> UserProgressReport:
        """
        Genere un rapport de progression sur X jours.

        Args:
            user_id: ID de l'utilisateur
            days: Nombre de jours a analyser

        Returns:
            UserProgressReport avec tendances et recommandations
        """
        # Recuperer les sessions de la periode
        period_start = datetime.utcnow() - timedelta(days=days)

        sessions_result = await self.db.execute(
            select(VoiceTrainingSession)
            .where(VoiceTrainingSession.user_id == user_id)
            .where(VoiceTrainingSession.created_at >= period_start)
            .where(VoiceTrainingSession.status == "completed")
            .order_by(VoiceTrainingSession.created_at)
        )
        sessions = sessions_result.scalars().all()

        if not sessions:
            raise ValueError(f"No completed sessions found for user {user_id} in last {days} days")

        # Construire le contexte
        context = {
            "user_id": user_id,
            "period": f"Last {days} days",
            "sessions": [
                {
                    "id": s.id,
                    "date": s.created_at.isoformat(),
                    "skill_id": s.skill_id,
                    "level": s.level,
                    "score": s.score,
                    "jauge_start": s.starting_gauge,
                    "jauge_end": s.current_gauge,
                    "converted": s.converted,
                    "positive_actions": s.positive_actions,
                    "negative_actions": s.negative_actions,
                }
                for s in sessions
            ],
            "total_sessions": len(sessions),
            "avg_score": sum(s.score or 0 for s in sessions) / len(sessions) if sessions else 0,
        }

        # Appeler Claude
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=PROGRESS_REPORT_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyse la progression de cet utilisateur:\n\n{json.dumps(context, ensure_ascii=False, indent=2, default=str)}",
                }
            ],
        )

        # Parser et construire le rapport
        report_data = self._parse_json_response(response.content[0].text)
        return self._build_progress_report(user_id, period_start, report_data, sessions)

    async def compare_to_champion(self, user_id: int, champion_id: str, champion_patterns: dict) -> ChampionComparison:
        """
        Compare les performances d'un utilisateur a un champion.

        Args:
            user_id: ID de l'utilisateur
            champion_id: ID du champion de reference
            champion_patterns: Patterns extraits du champion

        Returns:
            ChampionComparison avec analyse des gaps
        """
        # Recuperer les dernieres sessions de l'utilisateur
        sessions_result = await self.db.execute(
            select(VoiceTrainingSession)
            .where(VoiceTrainingSession.user_id == user_id)
            .where(VoiceTrainingSession.status == "completed")
            .order_by(VoiceTrainingSession.created_at.desc())
            .limit(10)
        )
        sessions = sessions_result.scalars().all()

        # Recuperer les transcripts
        user_techniques = []
        for session in sessions:
            messages = await self.db.execute(
                select(VoiceTrainingMessage)
                .where(VoiceTrainingMessage.session_id == session.id)
                .where(VoiceTrainingMessage.role == "user")
            )
            user_messages = messages.scalars().all()
            for msg in user_messages:
                if msg.detected_patterns:
                    user_techniques.append(msg.detected_patterns)

        context = {
            "user_id": user_id,
            "champion_id": champion_id,
            "champion_patterns": champion_patterns,
            "user_sessions_count": len(sessions),
            "user_detected_techniques": user_techniques,
            "user_avg_score": sum(s.score or 0 for s in sessions) / len(sessions) if sessions else 0,
        }

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            system=CHAMPION_COMPARISON_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Compare cet utilisateur au champion:\n\n{json.dumps(context, ensure_ascii=False, indent=2, default=str)}",
                }
            ],
        )

        comparison_data = self._parse_json_response(response.content[0].text)
        return self._build_champion_comparison(user_id, champion_id, comparison_data)

    async def generate_weekly_digest(self, user_id: int) -> WeeklyDigest:
        """
        Genere le digest hebdomadaire pour un utilisateur.

        Args:
            user_id: ID de l'utilisateur

        Returns:
            WeeklyDigest avec stats et motivation
        """
        # Recuperer l'utilisateur
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Generer le rapport de progression
        progress = None
        try:
            progress = await self.generate_progress_report(user_id, days=7)
        except ValueError:
            # Pas de sessions cette semaine
            pass

        # Construire le contexte
        context = {
            "user_name": user.full_name or user.email.split("@")[0],
            "user_id": user_id,
            "week_number": datetime.utcnow().isocalendar()[1],
            "year": datetime.utcnow().year,
            "has_activity": progress is not None,
        }

        if progress:
            context.update(
                {
                    "sessions_completed": progress.sessions_analyzed,
                    "avg_score": progress.avg_score_period,
                    "trend": progress.overall_trend,
                    "skills_mastered": progress.skills_mastered,
                    "skills_struggling": progress.skills_struggling,
                    "focus_areas": progress.focus_areas,
                }
            )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=WEEKLY_DIGEST_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Genere le digest hebdomadaire:\n\n{json.dumps(context, ensure_ascii=False, indent=2, default=str)}",
                }
            ],
        )

        digest_data = self._parse_json_response(response.content[0].text)
        return self._build_weekly_digest(user_id, digest_data)

    async def get_next_recommendation(self, user_id: int) -> dict[str, Any]:
        """
        Recommande la prochaine action optimale pour l'utilisateur.

        Returns:
            {
                "action": "training" | "course" | "quiz" | "review",
                "skill_slug": str,
                "reason": str,
                "estimated_impact": float
            }
        """
        # Recuperer la progression actuelle
        progress = await self.db.scalar(select(UserProgress).where(UserProgress.user_id == user_id))

        if not progress:
            # Nouvel utilisateur
            return {
                "action": "course",
                "skill_slug": "ecoute_active",
                "reason": "Commencez par le cours sur l'ecoute active pour poser les bases.",
                "estimated_impact": 20.0,
            }

        # Recuperer la progression par skill
        skills_result = await self.db.execute(
            select(UserSkillProgress).where(UserSkillProgress.user_progress_id == progress.id)
        )
        skills_progress = skills_result.scalars().all()

        if not skills_progress:
            return {
                "action": "course",
                "skill_slug": "ecoute_active",
                "reason": "Commencez par le premier cours pour debloquer les entrainements.",
                "estimated_impact": 20.0,
            }

        # Analyser pour trouver le meilleur next step
        skills_needing_work = [sp for sp in skills_progress if not sp.is_validated and (sp.best_score or 0) < 80]

        if not skills_needing_work:
            # Tous les skills sont valides ou > 80%
            return {
                "action": "training",
                "skill_slug": skills_progress[0].skill.slug
                if skills_progress and skills_progress[0].skill
                else "ecoute_active",
                "reason": "Maintien des acquis - continuez a pratiquer !",
                "estimated_impact": 5.0,
            }

        # Prioriser le skill avec le plus bas score qui n'est pas valide
        priority_skill = min(skills_needing_work, key=lambda x: x.best_score or 0)

        # Recuperer le skill pour avoir le slug
        skill = await self.db.get(Skill, priority_skill.skill_id)
        skill_slug = skill.slug if skill else "ecoute_active"

        # Determiner l'action
        if priority_skill.quiz_passed:
            action = "training"
            reason = f"Pratiquez {skill_slug} - votre score est de {priority_skill.best_score or 0:.0f}%"
        else:
            action = "quiz"
            reason = f"Passez le quiz de {skill_slug} pour valider la theorie"

        return {
            "action": action,
            "skill_slug": skill_slug,
            "reason": reason,
            "estimated_impact": min(20, 100 - (priority_skill.best_score or 0)),
        }

    # ═══════════════════════════════════════════════════════════════
    # METHODES PRIVEES
    # ═══════════════════════════════════════════════════════════════

    def _build_session_context(
        self, session: VoiceTrainingSession, messages: list[VoiceTrainingMessage]
    ) -> dict[str, Any]:
        """Construit le contexte pour l'audit de session."""

        # Construire la transcription
        transcript = []
        for msg in messages:
            transcript.append(
                {
                    "role": msg.role,
                    "text": msg.text,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                    "detected_patterns": msg.detected_patterns,
                    "gauge_impact": msg.gauge_impact,
                    "behavioral_cues": msg.behavioral_cues,
                }
            )

        duration_minutes = None
        if session.completed_at and session.created_at:
            duration_minutes = (session.completed_at - session.created_at).total_seconds() / 60

        return {
            "session_id": session.id,
            "user_id": session.user_id,
            "skill_id": session.skill_id,
            "level": session.level,
            "scenario": session.scenario_json,
            "starting_gauge": session.starting_gauge,
            "final_gauge": session.current_gauge,
            "gauge_history": session.gauge_history,
            "positive_actions": session.positive_actions,
            "negative_actions": session.negative_actions,
            "hidden_objections": session.hidden_objections,
            "discovered_objections": session.discovered_objections,
            "triggered_events": session.triggered_events,
            "reversal_triggered": session.reversal_triggered,
            "converted": session.converted,
            "transcript": transcript,
            "duration_minutes": duration_minutes,
        }

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        """Parse la reponse JSON de Claude."""
        # Nettoyer le texte
        text = text.strip()

        # Essayer de trouver le JSON
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # Fallback : essayer de trouver un objet JSON dans le texte
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            logger.warning("json_parse_failed", text_preview=text[:200])
            raise ValueError(f"Could not parse JSON from response: {text[:200]}...")

    def _build_session_audit(self, session: VoiceTrainingSession, audit_data: dict[str, Any]) -> SessionAudit:
        """Construit l'objet SessionAudit depuis les donnees Claude."""

        # Determiner le niveau de performance
        score = audit_data.get("overall_score", 0)
        if score >= 85:
            level = PerformanceLevel.EXCELLENT
        elif score >= 70:
            level = PerformanceLevel.BON
        elif score >= 55:
            level = PerformanceLevel.MOYEN
        elif score >= 40:
            level = PerformanceLevel.INSUFFISANT
        else:
            level = PerformanceLevel.CRITIQUE

        return SessionAudit(
            session_id=session.id,
            user_id=session.user_id,
            timestamp=datetime.utcnow(),
            overall_score=score,
            performance_level=level,
            skill_scores=audit_data.get("skill_scores", {}),
            behavioral_analysis=audit_data.get("behavioral_analysis", {}),
            emotional_intelligence_score=audit_data.get("emotional_intelligence_score", 0),
            adaptability_score=audit_data.get("adaptability_score", 0),
            champion_alignment=audit_data.get("champion_alignment", 0),
            champion_gaps=audit_data.get("champion_gaps", []),
            turning_points=audit_data.get("turning_points", []),
            missed_opportunities=audit_data.get("missed_opportunities", []),
            excellent_moments=audit_data.get("excellent_moments", []),
            summary=audit_data.get("summary", ""),
            top_strength=audit_data.get("top_strength", ""),
            top_weakness=audit_data.get("top_weakness", ""),
            immediate_action=audit_data.get("immediate_action", ""),
            audit_confidence=audit_data.get("audit_confidence", 0.8),
            audit_model=self.model,
        )

    def _build_progress_report(
        self, user_id: int, period_start: datetime, report_data: dict[str, Any], sessions: list[VoiceTrainingSession]
    ) -> UserProgressReport:
        """Construit l'objet UserProgressReport."""

        return UserProgressReport(
            user_id=user_id,
            period_start=period_start,
            period_end=datetime.utcnow(),
            sessions_analyzed=len(sessions),
            overall_trend=report_data.get("overall_trend", "stable"),
            score_evolution=report_data.get("score_evolution", []),
            avg_score_period=report_data.get("avg_score", 0),
            best_session_id=report_data.get("best_session_id", sessions[0].id if sessions else 0),
            worst_session_id=report_data.get("worst_session_id", sessions[0].id if sessions else 0),
            skill_progression=report_data.get("skill_progression", {}),
            skills_mastered=report_data.get("skills_mastered", []),
            skills_struggling=report_data.get("skills_struggling", []),
            consistent_strengths=report_data.get("consistent_strengths", []),
            persistent_weaknesses=report_data.get("persistent_weaknesses", []),
            improvement_velocity=report_data.get("improvement_velocity", 0),
            focus_areas=report_data.get("focus_areas", []),
            recommended_path=report_data.get("recommended_path", []),
            estimated_mastery_date=None,  # A calculer
            percentile_rank=report_data.get("percentile_rank", 50),
            comparison_to_average=report_data.get("comparison_to_average", 0),
        )

    def _build_champion_comparison(self, user_id: int, champion_id: str, data: dict[str, Any]) -> ChampionComparison:
        """Construit l'objet ChampionComparison."""

        return ChampionComparison(
            user_id=user_id,
            champion_id=champion_id,
            overall_similarity=data.get("overall_similarity", 0),
            technique_similarity=data.get("technique_similarity", 0),
            tone_similarity=data.get("tone_similarity", 0),
            timing_similarity=data.get("timing_similarity", 0),
            missing_techniques=data.get("missing_techniques", []),
            overused_techniques=data.get("overused_techniques", []),
            techniques_to_adopt=data.get("techniques_to_adopt", []),
            habits_to_break=data.get("habits_to_break", []),
        )

    def _build_weekly_digest(self, user_id: int, data: dict[str, Any]) -> WeeklyDigest:
        """Construit l'objet WeeklyDigest."""

        now = datetime.utcnow()

        return WeeklyDigest(
            user_id=user_id,
            week_number=now.isocalendar()[1],
            year=now.year,
            sessions_completed=data.get("sessions_completed", 0),
            total_training_minutes=data.get("total_training_minutes", 0),
            avg_score=data.get("avg_score", 0),
            best_moment=data.get("best_moment", ""),
            score_vs_last_week=data.get("score_vs_last_week", 0),
            new_skills_unlocked=data.get("new_skills_unlocked", []),
            achievements=data.get("achievements", []),
            weekly_goal=data.get("weekly_goal", ""),
            daily_tips=data.get("daily_tips", []),
            motivational_message=data.get("motivational_message", ""),
            streak_days=data.get("streak_days", 0),
        )

    async def _save_audit(self, session_id: int, audit: SessionAudit):
        """Sauvegarde l'audit dans la session."""
        session = await self.db.get(VoiceTrainingSession, session_id)
        if session:
            # Stocker l'audit dans le feedback_json
            session.feedback_json = session.feedback_json or {}
            session.feedback_json["audit"] = {
                "overall_score": audit.overall_score,
                "performance_level": audit.performance_level.value,
                "summary": audit.summary,
                "top_strength": audit.top_strength,
                "top_weakness": audit.top_weakness,
                "immediate_action": audit.immediate_action,
                "timestamp": audit.timestamp.isoformat(),
            }
            await self.db.commit()
