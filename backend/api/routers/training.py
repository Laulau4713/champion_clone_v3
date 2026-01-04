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

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agents import PatternAgent, TrainingAgent
from config import get_settings
from database import get_db
from models import Champion, TrainingSession, User
from schemas import (
    ScenarioResponse,
    SessionEndRequest,
    SessionRespondRequest,
    SessionRespondResponse,
    SessionResponse,
    SessionStartRequest,
    SessionStartResponse,
    SessionSummary,
    TrainingScenario,
)

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

from api.routers.auth import get_current_user, require_enterprise_access

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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_enterprise_access),
):
    """
    Generate training scenarios based on champion's patterns.
    Requires Enterprise plan.

    Returns realistic sales scenarios that challenge users
    to apply the champion's techniques.
    """
    result = await db.execute(select(Champion).where(Champion.id == champion_id))
    champion = result.scalar_one_or_none()

    if not champion:
        raise HTTPException(status_code=404, detail="Champion not found")

    if not champion.patterns_json:
        raise HTTPException(status_code=400, detail="Champion not analyzed yet. Run POST /analyze/{champion_id} first.")

    logger.info("generating_scenarios", champion_id=champion_id, count=count)

    try:
        scenarios = await pattern_extractor.generate_scenarios(champion.patterns_json, count=count)

        return ScenarioResponse(
            champion_id=champion.id, champion_name=champion.name, scenarios=[TrainingScenario(**s) for s in scenarios]
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
    current_user: User = Depends(require_enterprise_access),
):
    """
    Start a new training session (Champion V1).
    Requires Enterprise plan.

    Initializes a conversation where the user practices
    against an AI simulating a prospect, using the champion's patterns.
    """
    # Get champion
    result = await db.execute(select(Champion).where(Champion.id == body.champion_id))
    champion = result.scalar_one_or_none()

    if not champion:
        raise HTTPException(status_code=404, detail="Champion not found")

    if not champion.patterns_json:
        raise HTTPException(status_code=400, detail="Champion not analyzed. Run POST /analyze/{champion_id} first.")

    # Generate scenarios if needed
    scenarios = await pattern_extractor.generate_scenarios(champion.patterns_json, count=3)

    if body.scenario_index >= len(scenarios):
        body.scenario_index = 0

    scenario = scenarios[body.scenario_index]

    logger.info("starting_session", champion_id=champion.id, user=current_user.email)

    try:
        # Start the training bot session
        session_data = await training_bot.start_session(scenario=scenario, patterns=champion.patterns_json)

        # Create session record
        session = TrainingSession(
            user_id=str(current_user.id),
            champion_id=champion.id,
            scenario=scenario,
            messages=[
                {
                    "role": "champion",
                    "content": session_data["first_message"],
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ],
            status="active",
        )
        db.add(session)
        await db.commit()

        # Store system prompt for session continuity
        active_sessions[session.id] = {
            "system_prompt": session_data["system_prompt"],
            "patterns": champion.patterns_json,
            "scenario": scenario,
        }

        return SessionStartResponse(
            session_id=session.id,
            champion_name=champion.name,
            scenario=TrainingScenario(**scenario),
            first_message=session_data["first_message"],
            tips=session_data["tips"],
        )

    except Exception as e:
        logger.error("session_start_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/training/respond", response_model=SessionRespondResponse)
async def respond_in_session(
    request: Request,
    body: SessionRespondRequest = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_enterprise_access),
):
    """
    Continue a training session with a user response (Champion V1).
    Requires Enterprise plan.

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
                difficulty=session.scenario.get("difficulty", "medium").upper(),
            ),
            "patterns": session.champion.patterns_json,
            "scenario": session.scenario,
        }
        active_sessions[session.id] = session_context

    logger.info("processing_response", session_id=session.id)

    try:
        # Get prospect response
        prospect_response = await training_bot.get_prospect_response(
            user_message=body.user_response,
            conversation_history=session.messages,
            system_prompt=session_context["system_prompt"],
        )

        # Evaluate user's response
        evaluation = await training_bot.evaluate_response(
            user_response=body.user_response,
            patterns=session_context["patterns"],
            scenario=session_context["scenario"],
            conversation_history=session.messages,
        )

        # Update session messages
        now = datetime.utcnow().isoformat()
        session.messages = session.messages + [
            {
                "role": "user",
                "content": body.user_response,
                "timestamp": now,
                "feedback": evaluation["feedback"],
                "score": evaluation["score"],
            },
            {"role": "champion", "content": prospect_response, "timestamp": now},
        ]

        # Check if session should complete
        session_complete = await training_bot.check_session_complete(
            messages=session.messages, scenario=session_context["scenario"]
        )

        if session_complete:
            session.status = "completed"
            session.ended_at = datetime.utcnow()

            # Generate summary
            summary = await training_bot.generate_session_summary(
                messages=session.messages, patterns=session_context["patterns"], scenario=session_context["scenario"]
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
            session_complete=session_complete,
        )

    except Exception as e:
        logger.error("response_processing_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")


@router.post("/training/end", response_model=SessionSummary)
async def end_training_session(
    request: Request,
    body: SessionEndRequest = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_enterprise_access),
):
    """
    End a training session early and get summary (Champion V1).
    Requires Enterprise plan.
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
            messages=session.messages, patterns=patterns, scenario=scenario
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
            duration_seconds=duration,
        )

    except Exception as e:
        logger.error("session_end_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")


@router.get("/training/sessions", response_model=list[SessionResponse])
async def list_sessions(
    user_id: str | None = Query(None, description="Filter by user"),
    champion_id: int | None = Query(None, description="Filter by champion"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_enterprise_access),
):
    """List training sessions with optional filters (Champion V1). Requires Enterprise plan."""
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_enterprise_access),
):
    """Get a specific session's details (Champion V1). Requires Enterprise plan."""
    result = await db.execute(select(TrainingSession).where(TrainingSession.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse.model_validate(session)


# ============================================
# UTILITIES FOR TRAINING
# ============================================

# Free trial constants
FREE_TRIAL_MAX_SESSIONS = 3


def is_premium_user(user: User) -> bool:
    """Check if user has a premium subscription."""
    return user.subscription_plan in ("starter", "pro", "enterprise")


# NOTE: V2 voice endpoints have been removed.
# Use V3 endpoints below (/playbooks, /modules, /v3/session/*)


# ============================================
# TRAINING V3 - PLAYBOOK + MODULE SYSTEM
# ============================================

from orchestrator.main import ChampionCloneOrchestrator
from schemas import (
    ModuleSummary,
    PlaybookSummary,
    V3MessageRequest,
    V3MessageResponse,
    V3SessionEndRequest,
    V3SessionEndResponse,
    V3SessionStartRequest,
    V3SessionStartResponse,
)

# Singleton orchestrator instance
_orchestrator: ChampionCloneOrchestrator | None = None


def get_orchestrator() -> ChampionCloneOrchestrator:
    """Get or create the orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ChampionCloneOrchestrator()
    return _orchestrator


@router.get("/playbooks", response_model=list[PlaybookSummary])
async def list_playbooks(
    current_user: User = Depends(get_current_user),
):
    """
    List available playbooks (V3).

    Playbooks contain product information, pitch elements, and objection handling.
    Used with a training module to create complete training sessions.
    """
    orchestrator = get_orchestrator()
    playbooks = await orchestrator.list_playbooks()
    return [PlaybookSummary(**p) for p in playbooks]


@router.get("/modules", response_model=list[ModuleSummary])
async def list_modules(
    current_user: User = Depends(get_current_user),
):
    """
    List available training modules (V3).

    Modules define the training methodology (BEBEDC, SPIN Selling, etc.)
    and the evaluation criteria for each session.
    """
    orchestrator = get_orchestrator()
    modules = await orchestrator.list_modules()
    return [ModuleSummary(**m) for m in modules]


@router.post("/v3/session/start", response_model=V3SessionStartResponse)
async def start_v3_session(
    request: V3SessionStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new V3 training session with playbook + module.

    This new system replaces the level-based approach (easy/medium/hard)
    with a more structured methodology:

    - **playbook_id**: The product/company to sell (e.g., 'automate_ai')
    - **module_id**: The training methodology (e.g., 'bebedc', 'spin_selling')

    Returns the first prospect message and session context.
    """
    # Check trial/premium status
    if not is_premium_user(current_user):
        if current_user.trial_sessions_used >= FREE_TRIAL_MAX_SESSIONS:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "TRIAL_EXPIRED",
                    "message": "Votre essai gratuit est terminé. Passez à Premium pour continuer.",
                    "sessions_used": current_user.trial_sessions_used,
                    "max_sessions": FREE_TRIAL_MAX_SESSIONS,
                },
            )

    orchestrator = get_orchestrator()

    try:
        result = await orchestrator.handle_training_start(
            playbook_id=request.playbook_id,
            module_id=request.module_id,
            user_id=str(current_user.id),
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to start session"))

        # Increment trial counter for free users
        if not is_premium_user(current_user):
            current_user.trial_sessions_used += 1
            await db.commit()

        return V3SessionStartResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("v3_session_start_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/v3/session/{session_id}/message", response_model=V3MessageResponse)
async def send_v3_message(
    session_id: str,
    request: V3MessageRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Send a message in a V3 training session.

    The system will:
    1. Evaluate the message according to the module criteria
    2. Update the emotional jauge based on detected patterns
    3. Generate a realistic prospect response

    Returns evaluation feedback, jauge state, and prospect response.
    """
    orchestrator = get_orchestrator()

    try:
        result = await orchestrator.handle_training_message(
            session_id=session_id,
            message=request.message,
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to process message"))

        return V3MessageResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("v3_message_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.post("/v3/session/{session_id}/end", response_model=V3SessionEndResponse)
async def end_v3_session(
    session_id: str,
    request: V3SessionEndRequest,
    current_user: User = Depends(get_current_user),
):
    """
    End a V3 training session and get the final report.

    The report includes:
    - Module evaluation (elements detected/missing, score)
    - Final result (module success × closing success matrix)
    - Detailed recommendations and coaching tips
    """
    orchestrator = get_orchestrator()

    try:
        result = await orchestrator.handle_training_end(
            session_id=session_id,
            closing_achieved=request.closing_achieved,
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to end session"))

        return V3SessionEndResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("v3_session_end_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")


@router.get("/v3/session/{session_id}")
async def get_v3_session_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get the current status of a V3 training session.

    Returns session metadata, progress, and jauge state.
    """
    orchestrator = get_orchestrator()

    try:
        result = await orchestrator.get_training_session_status(session_id)

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Session not found"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("v3_session_status_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")
