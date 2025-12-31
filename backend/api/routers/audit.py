"""
Routes API pour l'AuditAgent.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from database import get_db
from models import User, VoiceTrainingSession
from api.routers.auth import get_current_user
from agents.audit_agent.agent import AuditAgent

logger = structlog.get_logger()

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/session/{session_id}")
async def audit_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Audit complet d'une session de training.
    Retourne une analyse independante et objective.
    """
    # Verifier que la session appartient a l'utilisateur
    session = await db.get(VoiceTrainingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    agent = AuditAgent(db)

    try:
        audit = await agent.audit_session(session_id)
        return {
            "session_id": audit.session_id,
            "overall_score": audit.overall_score,
            "performance_level": audit.performance_level.value,
            "summary": audit.summary,
            "top_strength": audit.top_strength,
            "top_weakness": audit.top_weakness,
            "immediate_action": audit.immediate_action,
            "turning_points": audit.turning_points,
            "missed_opportunities": audit.missed_opportunities,
            "excellent_moments": audit.excellent_moments,
            "emotional_intelligence_score": audit.emotional_intelligence_score,
            "adaptability_score": audit.adaptability_score,
            "behavioral_analysis": audit.behavioral_analysis,
            "champion_alignment": audit.champion_alignment,
            "champion_gaps": audit.champion_gaps,
            "audit_confidence": audit.audit_confidence,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("audit_session_failed", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")


@router.get("/progress")
async def get_progress_report(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Rapport de progression sur X jours.
    Analyse les tendances et recommandations.
    """
    if days < 1 or days > 90:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 90")

    agent = AuditAgent(db)

    try:
        report = await agent.generate_progress_report(current_user.id, days)
        return {
            "period": f"Last {days} days",
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "sessions_analyzed": report.sessions_analyzed,
            "overall_trend": report.overall_trend,
            "avg_score": report.avg_score_period,
            "score_evolution": report.score_evolution,
            "best_session_id": report.best_session_id,
            "worst_session_id": report.worst_session_id,
            "skill_progression": report.skill_progression,
            "skills_mastered": report.skills_mastered,
            "skills_struggling": report.skills_struggling,
            "consistent_strengths": report.consistent_strengths,
            "persistent_weaknesses": report.persistent_weaknesses,
            "improvement_velocity": report.improvement_velocity,
            "focus_areas": report.focus_areas,
            "recommended_path": report.recommended_path,
            "percentile_rank": report.percentile_rank,
            "comparison_to_average": report.comparison_to_average,
        }
    except ValueError as e:
        # Pas de sessions sur la periode
        return {
            "period": f"Last {days} days",
            "sessions_analyzed": 0,
            "message": str(e),
            "overall_trend": "no_data",
            "focus_areas": ["Commencez par une session d'entrainement !"],
        }


@router.get("/weekly-digest")
async def get_weekly_digest(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Digest hebdomadaire personnalise.
    Stats, motivation, tips pour la semaine.
    """
    agent = AuditAgent(db)

    try:
        digest = await agent.generate_weekly_digest(current_user.id)
        return {
            "week": f"Semaine {digest.week_number}, {digest.year}",
            "sessions_completed": digest.sessions_completed,
            "total_training_minutes": digest.total_training_minutes,
            "avg_score": digest.avg_score,
            "best_moment": digest.best_moment,
            "score_vs_last_week": digest.score_vs_last_week,
            "new_skills_unlocked": digest.new_skills_unlocked,
            "achievements": digest.achievements,
            "weekly_goal": digest.weekly_goal,
            "daily_tips": digest.daily_tips,
            "motivational_message": digest.motivational_message,
            "streak_days": digest.streak_days,
        }
    except ValueError:
        # Pas d'activite cette semaine
        return {
            "week": None,
            "sessions_completed": 0,
            "total_training_minutes": 0,
            "avg_score": 0,
            "motivational_message": "C'est le moment de commencer votre premiere session !",
            "weekly_goal": "Completez votre premiere session de training",
            "daily_tips": [
                "Lundi: Lisez le cours sur l'ecoute active",
                "Mardi: Passez le quiz pour valider vos connaissances",
                "Mercredi: Lancez votre premiere session d'entrainement",
                "Jeudi: Analysez votre feedback et notez vos points forts",
                "Vendredi: Recommencez une session pour progresser",
                "Samedi: Explorez un nouveau skill",
                "Dimanche: Revoyez vos progres de la semaine",
            ],
            "achievements": [],
            "streak_days": 0,
        }


@router.get("/next-action")
async def get_next_recommendation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Recommandation de la prochaine action optimale.
    """
    agent = AuditAgent(db)
    recommendation = await agent.get_next_recommendation(current_user.id)
    return recommendation


@router.get("/compare-champion/{champion_id}")
async def compare_to_champion(
    champion_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Compare les performances de l'utilisateur a un champion.
    """
    from models import Champion

    # Recuperer le champion et ses patterns
    champion = await db.get(Champion, champion_id)
    if not champion:
        raise HTTPException(status_code=404, detail="Champion not found")

    if not champion.patterns_json:
        raise HTTPException(
            status_code=400,
            detail="Champion has no extracted patterns yet"
        )

    agent = AuditAgent(db)

    try:
        comparison = await agent.compare_to_champion(
            current_user.id,
            str(champion_id),
            champion.patterns_json
        )
        return {
            "champion_id": champion_id,
            "champion_name": champion.name,
            "overall_similarity": comparison.overall_similarity,
            "technique_similarity": comparison.technique_similarity,
            "tone_similarity": comparison.tone_similarity,
            "timing_similarity": comparison.timing_similarity,
            "missing_techniques": comparison.missing_techniques,
            "overused_techniques": comparison.overused_techniques,
            "techniques_to_adopt": comparison.techniques_to_adopt,
            "habits_to_break": comparison.habits_to_break,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "champion_comparison_failed",
            user_id=current_user.id,
            champion_id=champion_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
