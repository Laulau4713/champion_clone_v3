"""
Training Router.

Endpoints:
- GET /scenarios/{champion_id} - Generate training scenarios
- POST /training/start - Start training session
- POST /training/respond - User response in session
- POST /training/end - End session and get summary
- GET /training/sessions - List training sessions
- GET /training/sessions/{session_id} - Get session details
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import structlog

from config import get_settings
from database import get_db
from models import User, Champion, TrainingSession
from schemas import (
    ScenarioResponse, TrainingScenario,
    SessionStartRequest, SessionStartResponse,
    SessionRespondRequest, SessionRespondResponse,
    SessionEndRequest, SessionSummary, SessionResponse
)
from agents import PatternAgent, TrainingAgent

settings = get_settings()
logger = structlog.get_logger()

router = APIRouter(tags=["Training"])

# Initialize agents
pattern_extractor = PatternAgent()
training_bot = TrainingAgent()

# In-memory session context storage
# Note: In production, use Redis for persistence across restarts
active_sessions: dict[int, dict] = {}


# ============================================
# Dependencies (imported from auth router)
# ============================================

from api.routers.auth import get_current_user


# ============================================
# Rate Limiter (imported from main)
# ============================================

# Note: Rate limiter must be passed from main.py via dependency injection
# For now, we import and reference it when main.py includes this router


# ============================================
# Scenario Endpoints
# ============================================

@router.get("/scenarios/{champion_id}", response_model=ScenarioResponse)
async def generate_scenarios(
    champion_id: int,
    count: int = Query(3, ge=1, le=5, description="Number of scenarios to generate"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate training scenarios based on champion's patterns.

    Returns realistic sales scenarios that challenge users
    to apply the champion's techniques.
    """
    result = await db.execute(select(Champion).where(Champion.id == champion_id))
    champion = result.scalar_one_or_none()

    if not champion:
        raise HTTPException(status_code=404, detail="Champion not found")

    if not champion.patterns_json:
        raise HTTPException(
            status_code=400,
            detail="Champion not analyzed yet. Run POST /analyze/{champion_id} first."
        )

    logger.info("generating_scenarios", champion_id=champion_id, count=count)

    try:
        scenarios = await pattern_extractor.generate_scenarios(
            champion.patterns_json,
            count=count
        )

        return ScenarioResponse(
            champion_id=champion.id,
            champion_name=champion.name,
            scenarios=[TrainingScenario(**s) for s in scenarios]
        )

    except Exception as e:
        logger.error("scenario_generation_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Scenario generation failed: {str(e)}")


# ============================================
# Training Session Endpoints
# ============================================

@router.post("/training/start", response_model=SessionStartResponse)
async def start_training_session(
    request: Request,
    body: SessionStartRequest = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a new training session.

    Initializes a conversation where the user practices
    against an AI simulating a prospect, using the champion's patterns.
    """
    # Get champion
    result = await db.execute(select(Champion).where(Champion.id == body.champion_id))
    champion = result.scalar_one_or_none()

    if not champion:
        raise HTTPException(status_code=404, detail="Champion not found")

    if not champion.patterns_json:
        raise HTTPException(
            status_code=400,
            detail="Champion not analyzed. Run POST /analyze/{champion_id} first."
        )

    # Generate scenarios if needed
    scenarios = await pattern_extractor.generate_scenarios(champion.patterns_json, count=3)

    if body.scenario_index >= len(scenarios):
        body.scenario_index = 0

    scenario = scenarios[body.scenario_index]

    logger.info("starting_session", champion_id=champion.id, user=current_user.email)

    try:
        # Start the training bot session
        session_data = await training_bot.start_session(
            scenario=scenario,
            patterns=champion.patterns_json
        )

        # Create session record
        session = TrainingSession(
            user_id=str(current_user.id),
            champion_id=champion.id,
            scenario=scenario,
            messages=[
                {
                    "role": "champion",
                    "content": session_data["first_message"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            ],
            status="active"
        )
        db.add(session)
        await db.commit()

        # Store system prompt for session continuity
        active_sessions[session.id] = {
            "system_prompt": session_data["system_prompt"],
            "patterns": champion.patterns_json,
            "scenario": scenario
        }

        return SessionStartResponse(
            session_id=session.id,
            champion_name=champion.name,
            scenario=TrainingScenario(**scenario),
            first_message=session_data["first_message"],
            tips=session_data["tips"]
        )

    except Exception as e:
        logger.error("session_start_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/training/respond", response_model=SessionRespondResponse)
async def respond_in_session(
    request: Request,
    body: SessionRespondRequest = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Continue a training session with a user response.

    The AI will:
    1. Respond as the prospect
    2. Evaluate the user's response
    3. Provide feedback and score
    """
    # Get session
    result = await db.execute(
        select(TrainingSession)
        .where(TrainingSession.id == body.session_id)
        .options(selectinload(TrainingSession.champion))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    # Get session context
    session_context = active_sessions.get(session.id)
    if not session_context:
        # Rebuild context if lost (e.g., after server restart)
        session_context = {
            "system_prompt": training_bot.SYSTEM_PROMPT.format(
                scenario=session.scenario,
                patterns=session.champion.patterns_json,
                difficulty=session.scenario.get("difficulty", "medium").upper()
            ),
            "patterns": session.champion.patterns_json,
            "scenario": session.scenario
        }
        active_sessions[session.id] = session_context

    logger.info("processing_response", session_id=session.id)

    try:
        # Get prospect response
        prospect_response = await training_bot.get_prospect_response(
            user_message=body.user_response,
            conversation_history=session.messages,
            system_prompt=session_context["system_prompt"]
        )

        # Evaluate user's response
        evaluation = await training_bot.evaluate_response(
            user_response=body.user_response,
            patterns=session_context["patterns"],
            scenario=session_context["scenario"],
            conversation_history=session.messages
        )

        # Update session messages
        now = datetime.utcnow().isoformat()
        session.messages = session.messages + [
            {
                "role": "user",
                "content": body.user_response,
                "timestamp": now,
                "feedback": evaluation["feedback"],
                "score": evaluation["score"]
            },
            {
                "role": "champion",
                "content": prospect_response,
                "timestamp": now
            }
        ]

        # Check if session should complete
        session_complete = await training_bot.check_session_complete(
            messages=session.messages,
            scenario=session_context["scenario"]
        )

        if session_complete:
            session.status = "completed"
            session.ended_at = datetime.utcnow()

            # Generate summary
            summary = await training_bot.generate_session_summary(
                messages=session.messages,
                patterns=session_context["patterns"],
                scenario=session_context["scenario"]
            )
            session.overall_score = summary["overall_score"]
            session.feedback_summary = summary["feedback_summary"]

            # Clean up active session
            active_sessions.pop(session.id, None)

        await db.commit()

        return SessionRespondResponse(
            champion_response=prospect_response,
            feedback=evaluation["feedback"],
            score=evaluation["score"],
            suggestions=evaluation["suggestions"],
            session_complete=session_complete
        )

    except Exception as e:
        logger.error("response_processing_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")


@router.post("/training/end", response_model=SessionSummary)
async def end_training_session(
    request: Request,
    body: SessionEndRequest = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    End a training session early and get summary.
    """
    # Get session
    result = await db.execute(
        select(TrainingSession)
        .where(TrainingSession.id == body.session_id)
        .options(selectinload(TrainingSession.champion))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get session context
    session_context = active_sessions.get(session.id, {})
    patterns = session_context.get("patterns", session.champion.patterns_json)
    scenario = session_context.get("scenario", session.scenario)

    logger.info("ending_session", session_id=session.id)

    try:
        # Generate summary
        summary = await training_bot.generate_session_summary(
            messages=session.messages,
            patterns=patterns,
            scenario=scenario
        )

        # Update session
        session.status = "completed"
        session.ended_at = datetime.utcnow()
        session.overall_score = summary["overall_score"]
        session.feedback_summary = summary["feedback_summary"]
        await db.commit()

        # Clean up
        active_sessions.pop(session.id, None)

        # Calculate duration
        duration = int((session.ended_at - session.started_at).total_seconds())

        return SessionSummary(
            session_id=session.id,
            champion_name=session.champion.name,
            total_exchanges=len([m for m in session.messages if m.get("role") == "user"]),
            overall_score=summary["overall_score"],
            feedback_summary=summary["feedback_summary"],
            strengths=summary["strengths"],
            areas_for_improvement=summary["areas_for_improvement"],
            duration_seconds=duration
        )

    except Exception as e:
        logger.error("session_end_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")


@router.get("/training/sessions", response_model=list[SessionResponse])
async def list_sessions(
    user_id: Optional[str] = Query(None, description="Filter by user"),
    champion_id: Optional[int] = Query(None, description="Filter by champion"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """List training sessions with optional filters."""
    query = select(TrainingSession).order_by(TrainingSession.started_at.desc())

    if user_id:
        query = query.where(TrainingSession.user_id == user_id)
    if champion_id:
        query = query.where(TrainingSession.champion_id == champion_id)
    if status:
        query = query.where(TrainingSession.status == status)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return [SessionResponse.model_validate(s) for s in sessions]


@router.get("/training/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific session's details."""
    result = await db.execute(
        select(TrainingSession).where(TrainingSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse.model_validate(session)
