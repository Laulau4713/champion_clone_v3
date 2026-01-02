"""
Endpoints pour le parcours pédagogique.
- Progression utilisateur
- Cours du jour
- Skills et validation
- Quiz
- Sessions quotidiennes
"""

from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
import structlog

from database import get_db
from models import (
    User, Skill, Sector, Course, Quiz, DifficultyLevel,
    UserProgress, UserSkillProgress, DailySession
)
from api.routers.auth import get_current_user

logger = structlog.get_logger()
router = APIRouter(prefix="/learning", tags=["Learning"])


# ═══════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════

class SkillResponse(BaseModel):
    id: int
    slug: str
    name: str
    level: str
    description: str
    order: int
    pass_threshold: int
    scenarios_required: int

    class Config:
        from_attributes = True


class SkillDetailResponse(SkillResponse):
    learning_objectives: Optional[list] = None
    key_concepts: Optional[list] = None
    evaluation_criteria: Optional[list] = None
    emotional_focus: Optional[list] = None
    common_mistakes: Optional[list] = None


class SectorResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None

    class Config:
        from_attributes = True


class SectorDetailResponse(SectorResponse):
    vocabulary: Optional[list] = None
    prospect_personas: Optional[list] = None
    typical_objections: Optional[list] = None


class CourseResponse(BaseModel):
    id: int
    day: int  # Day number in the training program
    level: str
    title: str
    objective: Optional[str] = None
    duration_minutes: int
    skill_id: Optional[int] = None
    skill_slug: Optional[str] = None  # Added for frontend convenience

    class Config:
        from_attributes = True


class CourseDetailResponse(CourseResponse):
    key_points: Optional[list] = None
    common_mistakes: Optional[list] = None
    emotional_tips: Optional[list] = None
    takeaways: Optional[list] = None
    stat_cle: Optional[str] = None
    intro: Optional[str] = None
    full_content: Optional[str] = None


class QuizQuestionResponse(BaseModel):
    question: str
    options: list[str]


class QuizResponse(BaseModel):
    skill_id: int
    questions: list[QuizQuestionResponse]


class QuizSubmission(BaseModel):
    answers: list[str]


class QuizResultResponse(BaseModel):
    score: float
    passed: bool
    correct_count: int
    total_questions: int
    details: list[dict]


class UserProgressResponse(BaseModel):
    current_level: str
    current_day: int  # Current day in the training program
    sector_slug: Optional[str] = None
    started_at: datetime
    total_training_minutes: int
    total_scenarios_completed: int
    average_score: float
    skills_validated: int
    skills_total: int

    class Config:
        from_attributes = True


class SkillProgressResponse(BaseModel):
    skill_slug: str
    skill_name: str
    scenarios_completed: int
    scenarios_passed: int
    scenarios_required: int
    best_score: float
    average_score: float
    quiz_passed: bool
    is_validated: bool

    class Config:
        from_attributes = True


class DailySessionResponse(BaseModel):
    id: int
    date: datetime
    course_read: bool
    scripts_listened: int
    training_minutes: int
    scenarios_attempted: int
    average_score: Optional[float] = None
    is_complete: bool

    class Config:
        from_attributes = True


class StartSessionResponse(BaseModel):
    session_id: int
    day: int
    course: CourseDetailResponse
    skill: Optional[SkillResponse] = None


class SelectSectorRequest(BaseModel):
    sector_slug: str


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS - CONTENU (Public)
# ═══════════════════════════════════════════════════════════════

@router.get("/skills", response_model=list[SkillResponse])
async def get_skills(
    level: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Liste tous les skills, optionnellement filtrés par niveau."""
    query = select(Skill).order_by(Skill.order)
    if level:
        query = query.where(Skill.level == level)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/skills/{slug}", response_model=SkillDetailResponse)
async def get_skill(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Détail d'un skill."""
    skill = await db.scalar(select(Skill).where(Skill.slug == slug))
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.get("/sectors", response_model=list[SectorResponse])
async def get_sectors(db: AsyncSession = Depends(get_db)):
    """Liste tous les secteurs disponibles."""
    result = await db.execute(select(Sector))
    return result.scalars().all()


@router.get("/sectors/{slug}", response_model=SectorDetailResponse)
async def get_sector(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Détail d'un secteur."""
    sector = await db.scalar(select(Sector).where(Sector.slug == slug))
    if not sector:
        raise HTTPException(status_code=404, detail="Sector not found")
    return sector


@router.get("/courses", response_model=list[CourseResponse])
async def get_courses(
    level: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Liste tous les cours."""
    query = select(Course, Skill.slug.label("skill_slug")).outerjoin(
        Skill, Course.skill_id == Skill.id
    ).order_by(Course.day)
    if level:
        query = query.where(Course.level == level)

    result = await db.execute(query)
    courses = []
    for row in result:
        course = row[0]
        courses.append({
            "id": course.id,
            "day": course.day,
            "level": course.level,
            "title": course.title,
            "objective": course.objective,
            "duration_minutes": course.duration_minutes,
            "skill_id": course.skill_id,
            "skill_slug": row[1]  # skill_slug from join
        })
    return courses


@router.get("/courses/{order}", response_model=CourseDetailResponse)
async def get_course_by_order(
    order: int,
    db: AsyncSession = Depends(get_db)
):
    """Récupère un cours par son ordre dans la progression."""
    result = await db.execute(
        select(Course, Skill.slug.label("skill_slug")).outerjoin(
            Skill, Course.skill_id == Skill.id
        ).where(Course.day == order)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Course not found")

    course = row[0]
    return {
        "id": course.id,
        "day": course.day,
        "level": course.level,
        "title": course.title,
        "objective": course.objective,
        "duration_minutes": course.duration_minutes,
        "skill_id": course.skill_id,
        "skill_slug": row[1],
        "key_points": course.key_points,
        "common_mistakes": course.common_mistakes,
        "emotional_tips": course.emotional_tips,
        "takeaways": course.takeaways,
        "stat_cle": course.stat_cle,
        "intro": course.intro,
        "full_content": course.full_content
    }


# Keep old endpoint for backward compatibility
@router.get("/courses/day/{day}", response_model=CourseDetailResponse, include_in_schema=False)
async def get_course_by_day_legacy(
    day: int,
    db: AsyncSession = Depends(get_db)
):
    """Legacy endpoint - use /courses/{order} instead."""
    return await get_course_by_order(day, db)


@router.get("/difficulty-levels")
async def get_difficulty_levels(db: AsyncSession = Depends(get_db)):
    """Liste les niveaux de difficulté."""
    result = await db.execute(select(DifficultyLevel))
    levels = result.scalars().all()
    return [
        {
            "level": l.level,
            "name": l.name,
            "description": l.description,
            "days_range": [l.days_range_start, l.days_range_end]
        }
        for l in levels
    ]


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS - PROGRESSION UTILISATEUR (Auth required)
# ═══════════════════════════════════════════════════════════════

@router.get("/progress", response_model=UserProgressResponse)
async def get_user_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère la progression de l'utilisateur."""
    progress = await db.scalar(
        select(UserProgress).where(UserProgress.user_id == current_user.id)
    )

    if not progress:
        # Créer une progression initiale
        progress = UserProgress(user_id=current_user.id)
        db.add(progress)
        await db.commit()
        await db.refresh(progress)

    # Compter les skills validés
    validated_count = await db.scalar(
        select(func.count(UserSkillProgress.id)).where(
            UserSkillProgress.user_progress_id == progress.id,
            UserSkillProgress.is_validated == True
        )
    )

    total_skills = await db.scalar(select(func.count(Skill.id)))

    # Récupérer le secteur si choisi
    sector_slug = None
    if progress.sector_id:
        sector = await db.get(Sector, progress.sector_id)
        sector_slug = sector.slug if sector else None

    return {
        "current_level": progress.current_level,
        "current_day": progress.current_day,
        "sector_slug": sector_slug,
        "started_at": progress.started_at,
        "total_training_minutes": progress.total_training_minutes,
        "total_scenarios_completed": progress.total_scenarios_completed,
        "average_score": progress.average_score,
        "skills_validated": validated_count or 0,
        "skills_total": total_skills or 13
    }


@router.get("/progress/skills", response_model=list[SkillProgressResponse])
async def get_skills_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère la progression par skill."""
    progress = await db.scalar(
        select(UserProgress).where(UserProgress.user_id == current_user.id)
    )

    if not progress:
        return []

    # Récupérer tous les skills avec leur progression
    skills_result = await db.execute(select(Skill).order_by(Skill.order))
    skills = skills_result.scalars().all()

    result = []
    for skill in skills:
        skill_progress = await db.scalar(
            select(UserSkillProgress).where(
                UserSkillProgress.user_progress_id == progress.id,
                UserSkillProgress.skill_id == skill.id
            )
        )

        result.append({
            "skill_slug": skill.slug,
            "skill_name": skill.name,
            "scenarios_completed": skill_progress.scenarios_completed if skill_progress else 0,
            "scenarios_passed": skill_progress.scenarios_passed if skill_progress else 0,
            "scenarios_required": skill.scenarios_required,
            "best_score": skill_progress.best_score if skill_progress else 0,
            "average_score": skill_progress.average_score if skill_progress else 0,
            "quiz_passed": skill_progress.quiz_passed if skill_progress else False,
            "is_validated": skill_progress.is_validated if skill_progress else False
        })

    return result


@router.post("/progress/select-sector")
async def select_sector(
    request: SelectSectorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Sélectionne un secteur pour le niveau expert."""
    sector = await db.scalar(
        select(Sector).where(Sector.slug == request.sector_slug)
    )
    if not sector:
        raise HTTPException(status_code=404, detail="Sector not found")

    progress = await db.scalar(
        select(UserProgress).where(UserProgress.user_id == current_user.id)
    )

    if not progress:
        progress = UserProgress(user_id=current_user.id)
        db.add(progress)

    progress.sector_id = sector.id
    await db.commit()

    logger.info("sector_selected", user_id=current_user.id, sector=sector.slug)
    return {"message": "Sector selected", "sector": sector.name}


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS - SESSION QUOTIDIENNE
# ═══════════════════════════════════════════════════════════════

@router.post("/session/start", response_model=StartSessionResponse)
async def start_daily_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Démarre la session quotidienne."""
    # Récupérer ou créer la progression
    progress = await db.scalar(
        select(UserProgress).where(UserProgress.user_id == current_user.id)
    )

    if not progress:
        progress = UserProgress(user_id=current_user.id)
        db.add(progress)
        await db.commit()
        await db.refresh(progress)

    # Vérifier s'il y a déjà une session aujourd'hui
    today = date.today()
    session = await db.scalar(
        select(DailySession).where(
            DailySession.user_progress_id == progress.id,
            func.date(DailySession.date) == today
        )
    )

    if not session:
        session = DailySession(
            user_progress_id=progress.id,
            date=datetime.utcnow()
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

    # Récupérer le cours du jour
    course = await db.scalar(
        select(Course).where(Course.day == progress.current_day)
    )

    if not course:
        raise HTTPException(status_code=404, detail="No course for this day")

    # Récupérer le skill associé
    skill = await db.get(Skill, course.skill_id) if course.skill_id else None

    logger.info("session_started", user_id=current_user.id, day=progress.current_day)

    return {
        "session_id": session.id,
        "day": progress.current_day,
        "course": course,
        "skill": skill
    }


@router.post("/session/{session_id}/complete-course")
async def complete_course_reading(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Marque le cours comme lu."""
    session = await db.get(DailySession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.course_read = True
    session.course_read_at = datetime.utcnow()
    await db.commit()

    return {"message": "Course marked as read"}


@router.post("/session/{session_id}/listen-script")
async def listen_script(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Incrémente le compteur de scripts écoutés."""
    session = await db.get(DailySession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.scripts_listened += 1
    await db.commit()

    return {"scripts_listened": session.scripts_listened}


@router.get("/session/today", response_model=Optional[DailySessionResponse])
async def get_today_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère la session du jour si elle existe."""
    progress = await db.scalar(
        select(UserProgress).where(UserProgress.user_id == current_user.id)
    )

    if not progress:
        return None

    today = date.today()
    session = await db.scalar(
        select(DailySession).where(
            DailySession.user_progress_id == progress.id,
            func.date(DailySession.date) == today
        )
    )

    return session


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS - QUIZ
# ═══════════════════════════════════════════════════════════════

@router.get("/quiz/{skill_slug}", response_model=QuizResponse)
async def get_quiz(
    skill_slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Récupère le quiz d'un skill (sans les réponses)."""
    skill = await db.scalar(select(Skill).where(Skill.slug == skill_slug))
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    quiz = await db.scalar(select(Quiz).where(Quiz.skill_id == skill.id))
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Retourner sans les réponses correctes
    questions = [
        {"question": q["question"], "options": q["options"]}
        for q in quiz.questions
    ]

    return {"skill_id": skill.id, "questions": questions}


@router.post("/quiz/{skill_slug}/submit", response_model=QuizResultResponse)
async def submit_quiz(
    skill_slug: str,
    submission: QuizSubmission,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soumet les réponses au quiz."""
    skill = await db.scalar(select(Skill).where(Skill.slug == skill_slug))
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    quiz = await db.scalar(select(Quiz).where(Quiz.skill_id == skill.id))
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Vérifier les réponses
    questions = quiz.questions
    if len(submission.answers) != len(questions):
        raise HTTPException(
            status_code=400,
            detail=f"Expected {len(questions)} answers, got {len(submission.answers)}"
        )

    correct_count = 0
    details = []

    for i, (question, answer) in enumerate(zip(questions, submission.answers)):
        is_correct = answer.upper() == question["correct"].upper()
        if is_correct:
            correct_count += 1

        details.append({
            "question_index": i,
            "your_answer": answer,
            "correct_answer": question["correct"],
            "is_correct": is_correct,
            "explanation": question.get("explanation", "")
        })

    score = (correct_count / len(questions)) * 100
    passed = score >= 80  # 80% pour passer

    # Mettre à jour la progression
    progress = await db.scalar(
        select(UserProgress).where(UserProgress.user_id == current_user.id)
    )

    if progress:
        skill_progress = await db.scalar(
            select(UserSkillProgress).where(
                UserSkillProgress.user_progress_id == progress.id,
                UserSkillProgress.skill_id == skill.id
            )
        )

        if not skill_progress:
            skill_progress = UserSkillProgress(
                user_progress_id=progress.id,
                skill_id=skill.id,
                quiz_attempts=0,
                quiz_score=0.0,
                scenarios_completed=0,
                scenarios_passed=0,
                best_score=0.0,
                average_score=0.0
            )
            db.add(skill_progress)

        skill_progress.quiz_attempts = (skill_progress.quiz_attempts or 0) + 1
        if score > (skill_progress.quiz_score or 0):
            skill_progress.quiz_score = score

        if passed:
            skill_progress.quiz_passed = True

            # Vérifier si le skill est entièrement validé
            if (skill_progress.scenarios_passed or 0) >= skill.scenarios_required:
                skill_progress.is_validated = True
                skill_progress.validated_at = datetime.utcnow()

        await db.commit()

    logger.info(
        "quiz_submitted",
        user_id=current_user.id,
        skill=skill_slug,
        score=score,
        passed=passed
    )

    return {
        "score": score,
        "passed": passed,
        "correct_count": correct_count,
        "total_questions": len(questions),
        "details": details
    }
