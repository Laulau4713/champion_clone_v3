"""
Achievements & Gamification endpoints.

Provides:
- GET /achievements - List all achievements with unlock status
- GET /achievements/unlocked - User's unlocked achievements
- GET /achievements/xp - User's XP and level
- POST /achievements/check - Check and unlock eligible achievements
"""

import json
from datetime import datetime
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from database import get_db
from models import User, UserAchievement, UserProgress, UserSkillProgress, UserXP, VoiceTrainingSession

logger = structlog.get_logger()
router = APIRouter(prefix="/achievements", tags=["Achievements"])

# Load achievements from JSON
CONTENT_DIR = Path(__file__).parent.parent.parent / "content"
with open(CONTENT_DIR / "achievements.json") as f:
    ACHIEVEMENTS_DATA = json.load(f)["achievements"]
    ACHIEVEMENTS_MAP = {a["id"]: a for a in ACHIEVEMENTS_DATA}


# ═══════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════


class AchievementResponse(BaseModel):
    id: str
    category: str
    name: str
    description: str
    icon: str
    color: str
    xp_reward: int
    unlocked: bool
    unlocked_at: datetime | None = None


class XPResponse(BaseModel):
    total_xp: int
    level: int
    xp_for_next_level: int
    xp_progress: float


class UnlockResult(BaseModel):
    newly_unlocked: list[AchievementResponse]
    total_xp_gained: int
    level_up: bool
    new_level: int | None = None


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════


@router.get("", response_model=list[AchievementResponse])
async def get_all_achievements(
    category: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Liste tous les achievements avec leur statut de déverrouillage."""
    # Get user's unlocked achievements
    unlocked_result = await db.execute(select(UserAchievement).where(UserAchievement.user_id == current_user.id))
    unlocked_map = {ua.achievement_id: ua for ua in unlocked_result.scalars().all()}

    achievements = []
    for ach in ACHIEVEMENTS_DATA:
        if category and ach["category"] != category:
            continue

        unlocked = ach["id"] in unlocked_map
        achievements.append(
            {
                "id": ach["id"],
                "category": ach["category"],
                "name": ach["name"],
                "description": ach["description"],
                "icon": ach["icon"],
                "color": ach["color"],
                "xp_reward": ach["xp_reward"],
                "unlocked": unlocked,
                "unlocked_at": unlocked_map[ach["id"]].unlocked_at if unlocked else None,
            }
        )

    return achievements


@router.get("/unlocked", response_model=list[AchievementResponse])
async def get_unlocked_achievements(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Liste uniquement les achievements déverrouillés."""
    result = await db.execute(
        select(UserAchievement)
        .where(UserAchievement.user_id == current_user.id)
        .order_by(UserAchievement.unlocked_at.desc())
    )
    unlocked = result.scalars().all()

    achievements = []
    for ua in unlocked:
        ach = ACHIEVEMENTS_MAP.get(ua.achievement_id)
        if ach:
            achievements.append(
                {
                    "id": ach["id"],
                    "category": ach["category"],
                    "name": ach["name"],
                    "description": ach["description"],
                    "icon": ach["icon"],
                    "color": ach["color"],
                    "xp_reward": ach["xp_reward"],
                    "unlocked": True,
                    "unlocked_at": ua.unlocked_at,
                }
            )

    return achievements


@router.get("/xp", response_model=XPResponse)
async def get_user_xp(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Récupère les XP et niveau de l'utilisateur."""
    xp_data = await db.scalar(select(UserXP).where(UserXP.user_id == current_user.id))

    if not xp_data:
        # Create XP record if doesn't exist
        xp_data = UserXP(user_id=current_user.id)
        db.add(xp_data)
        await db.commit()
        await db.refresh(xp_data)

    return {
        "total_xp": xp_data.total_xp,
        "level": xp_data.level,
        "xp_for_next_level": xp_data.xp_for_next_level,
        "xp_progress": xp_data.xp_progress,
    }


@router.post("/check", response_model=UnlockResult)
async def check_and_unlock_achievements(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Vérifie et déverrouille les achievements éligibles."""
    # Get user's current unlocked achievements
    unlocked_result = await db.execute(select(UserAchievement).where(UserAchievement.user_id == current_user.id))
    already_unlocked = {ua.achievement_id for ua in unlocked_result.scalars().all()}

    # Get user stats for checking conditions
    stats = await _get_user_stats(current_user.id, db)

    # Check each achievement
    newly_unlocked = []
    total_xp = 0

    for ach in ACHIEVEMENTS_DATA:
        if ach["id"] in already_unlocked:
            continue

        if _check_achievement_condition(ach["condition"], stats):
            # Unlock this achievement
            user_ach = UserAchievement(user_id=current_user.id, achievement_id=ach["id"], xp_rewarded=ach["xp_reward"])
            db.add(user_ach)
            total_xp += ach["xp_reward"]

            newly_unlocked.append(
                {
                    "id": ach["id"],
                    "category": ach["category"],
                    "name": ach["name"],
                    "description": ach["description"],
                    "icon": ach["icon"],
                    "color": ach["color"],
                    "xp_reward": ach["xp_reward"],
                    "unlocked": True,
                    "unlocked_at": datetime.utcnow(),
                }
            )

            logger.info("achievement_unlocked", user_id=current_user.id, achievement=ach["id"], xp=ach["xp_reward"])

    # Update XP and level
    level_up = False
    new_level = None

    if total_xp > 0:
        xp_data = await db.scalar(select(UserXP).where(UserXP.user_id == current_user.id))
        if not xp_data:
            xp_data = UserXP(user_id=current_user.id)
            db.add(xp_data)

        old_level = xp_data.level
        xp_data.total_xp += total_xp

        # Check for level up
        while xp_data.total_xp >= xp_data.xp_for_next_level:
            xp_data.level += 1

        if xp_data.level > old_level:
            level_up = True
            new_level = xp_data.level
            logger.info("user_level_up", user_id=current_user.id, new_level=new_level)

    await db.commit()

    return {"newly_unlocked": newly_unlocked, "total_xp_gained": total_xp, "level_up": level_up, "new_level": new_level}


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════


async def _get_user_stats(user_id: int, db: AsyncSession) -> dict:
    """Get user statistics for achievement checking."""
    # Get progress data
    progress = await db.scalar(select(UserProgress).where(UserProgress.user_id == user_id))

    # Count completed courses (courses where user has passed the quiz or completed reading)
    # For now, use current_day as a proxy
    courses_completed = progress.current_day - 1 if progress else 0

    # Count sessions
    sessions_count = (
        await db.scalar(
            select(func.count(VoiceTrainingSession.id)).where(
                VoiceTrainingSession.user_id == user_id, VoiceTrainingSession.status == "completed"
            )
        )
        or 0
    )

    # Count conversions
    conversions = (
        await db.scalar(
            select(func.count(VoiceTrainingSession.id)).where(
                VoiceTrainingSession.user_id == user_id, VoiceTrainingSession.converted == True
            )
        )
        or 0
    )

    # Count perfect sessions (current_gauge = 100)
    perfect_sessions = (
        await db.scalar(
            select(func.count(VoiceTrainingSession.id)).where(
                VoiceTrainingSession.user_id == user_id, VoiceTrainingSession.current_gauge >= 100
            )
        )
        or 0
    )

    # Count expert conversions
    expert_conversions = (
        await db.scalar(
            select(func.count(VoiceTrainingSession.id)).where(
                VoiceTrainingSession.user_id == user_id,
                VoiceTrainingSession.level == "expert",
                VoiceTrainingSession.converted == True,
            )
        )
        or 0
    )

    # Get validated skills
    validated_skills = []
    if progress:
        skill_progress_result = await db.execute(
            select(UserSkillProgress).where(
                UserSkillProgress.user_progress_id == progress.id, UserSkillProgress.is_validated == True
            )
        )
        skill_progress_list = skill_progress_result.scalars().all()

        # Get skill slugs
        for sp in skill_progress_list:
            from models import Skill

            skill = await db.get(Skill, sp.skill_id)
            if skill:
                validated_skills.append(skill.slug)

    # Count reversals recovered and hidden objections discovered
    reversals_recovered = 0
    hidden_objections = 0
    sessions_result = await db.execute(select(VoiceTrainingSession).where(VoiceTrainingSession.user_id == user_id))
    for session in sessions_result.scalars().all():
        # Count reversals (sessions where reversal was triggered and converted)
        if session.reversal_triggered and session.converted:
            reversals_recovered += 1
        # Count discovered hidden objections from JSON array
        if session.discovered_objections:
            hidden_objections += len(session.discovered_objections)

    return {
        "courses_completed": courses_completed,
        "sessions_completed": sessions_count,
        "conversions": conversions,
        "training_minutes": progress.total_training_minutes if progress else 0,
        "validated_skills": validated_skills,
        "all_skills_count": len(validated_skills),
        "perfect_sessions": perfect_sessions,
        "reversals_recovered": reversals_recovered,
        "hidden_objections_discovered": hidden_objections,
        "expert_conversions": expert_conversions,
    }


def _check_achievement_condition(condition: dict, stats: dict) -> bool:
    """Check if an achievement condition is met."""
    cond_type = condition.get("type")

    if cond_type == "courses_completed":
        return stats["courses_completed"] >= condition["value"]

    elif cond_type == "sessions_completed":
        return stats["sessions_completed"] >= condition["value"]

    elif cond_type == "conversions":
        return stats["conversions"] >= condition["value"]

    elif cond_type == "training_minutes":
        return stats["training_minutes"] >= condition["value"]

    elif cond_type == "skill_validated":
        return condition["skill"] in stats["validated_skills"]

    elif cond_type == "all_skills_validated":
        # Assuming 17 total skills
        return stats["all_skills_count"] >= 17

    elif cond_type == "perfect_jauge":
        return stats["perfect_sessions"] > 0

    elif cond_type == "reversals_recovered":
        return stats["reversals_recovered"] >= condition["value"]

    elif cond_type == "hidden_objections_discovered":
        return stats["hidden_objections_discovered"] >= condition["value"]

    elif cond_type == "expert_conversion":
        return stats["expert_conversions"] > 0

    return False
