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


# ============================================
# VOICE TRAINING ENDPOINTS V2
# ============================================

from pydantic import BaseModel
from services.training_service_v2 import TrainingServiceV2
from services.voice_service import voice_service


class VoiceSessionStartRequest(BaseModel):
    """Request to start a voice training session."""
    skill_slug: str
    sector_slug: Optional[str] = None


class VoiceMessageRequest(BaseModel):
    """Request to send a message in voice training."""
    audio_base64: Optional[str] = None
    text: Optional[str] = None


class ProspectResponseSchemaV2(BaseModel):
    """Response from the prospect in voice training V2."""
    text: str
    audio_base64: Optional[str] = None
    mood: str  # hostile, aggressive, skeptical, neutral, interested, ready_to_buy
    jauge: int  # -1 if hidden (medium/expert levels)
    jauge_delta: int  # 0 if hidden
    behavioral_cue: Optional[str] = None  # (soupir), (prend des notes), etc.
    is_event: bool = False  # True if this is a situational event
    event_type: Optional[str] = None
    feedback: Optional[dict] = None
    conversion_possible: bool = False


# Keep old schema for backwards compatibility
class ProspectResponseSchema(BaseModel):
    """Response from the prospect in voice training (legacy)."""
    text: str
    audio_base64: Optional[str] = None
    emotion: str
    should_interrupt: bool
    interruption_reason: Optional[str] = None
    feedback: Optional[dict] = None


# Free trial constants
FREE_TRIAL_MAX_SESSIONS = 3


def is_premium_user(user: User) -> bool:
    """Check if user has a premium subscription."""
    return user.subscription_plan in ("starter", "pro", "enterprise")


@router.post("/voice/session/start")
async def start_voice_training_session(
    request: VoiceSessionStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new voice training session (V2 with emotional jauge).

    Uses the pedagogical skills/sectors system with V2 mechanics:
    - Emotional jauge (0-100)
    - Hidden objections (medium/expert)
    - Situational events (medium/expert)
    - Reversals (expert)

    Free trial users get 3 free sessions (easy/medium only).
    Returns 402 if trial expired and not premium.

    Returns scenario, opening message with audio, and initial jauge/mood.
    """
    # Check trial/premium status
    if not is_premium_user(current_user):
        if current_user.trial_sessions_used >= FREE_TRIAL_MAX_SESSIONS:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "TRIAL_EXPIRED",
                    "message": "Votre essai gratuit est termin\u00e9. Passez \u00e0 Premium pour continuer.",
                    "sessions_used": current_user.trial_sessions_used,
                    "max_sessions": FREE_TRIAL_MAX_SESSIONS
                }
            )

    service = TrainingServiceV2(db)

    try:
        session = await service.create_session(
            user=current_user,
            skill_slug=request.skill_slug,
            sector_slug=request.sector_slug
        )

        # Increment trial counter for free users
        if not is_premium_user(current_user):
            current_user.trial_sessions_used += 1
            await db.commit()

        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("voice_session_start_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/voice/session/{session_id}/message", response_model=ProspectResponseSchemaV2)
async def send_voice_message(
    session_id: int,
    request: VoiceMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message (audio or text) and receive prospect response (V2).

    If audio_base64 is provided, it will be transcribed via Whisper.

    V2 Response includes:
    - mood: Current emotional state of the prospect
    - jauge: Emotional jauge value (0-100, or -1 if hidden)
    - jauge_delta: Change since last message
    - behavioral_cue: Visual cue like "(soupir)" or "(prend des notes)"
    - is_event: True if this is a situational event
    - conversion_possible: Whether closing could succeed now
    - feedback: Tips and pattern analysis (in easy mode)
    """
    if not request.audio_base64 and not request.text:
        raise HTTPException(status_code=400, detail="audio_base64 or text required")

    service = TrainingServiceV2(db)

    try:
        response = await service.process_user_message(
            session_id=session_id,
            user=current_user,
            audio_base64=request.audio_base64,
            text=request.text
        )
        return response.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("voice_message_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.post("/voice/session/{session_id}/end")
async def end_voice_training_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    End the voice training session and get final evaluation (V2).

    Returns detailed V2 evaluation including:
    - overall_score: Final score (0-100)
    - final_jauge: Where the emotional jauge ended
    - jauge_progression: Change from start to end
    - positive_actions_count / negative_actions_count
    - converted: Whether the prospect was won over
    - points_forts / axes_amelioration
    - conseil_principal: Main advice for improvement
    """
    service = TrainingServiceV2(db)

    try:
        result = await service.end_session(
            session_id=session_id,
            user=current_user
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("voice_session_end_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")


@router.get("/voice/session/{session_id}")
async def get_voice_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a voice training session (V2).

    Returns full session data including:
    - current_jauge / starting_jauge
    - jauge_history: Timeline of jauge changes
    - positive_actions / negative_actions: Detected patterns
    - messages: Full conversation with behavioral analysis
    """
    service = TrainingServiceV2(db)
    session = await service.get_session(session_id, current_user)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.get("/voice/config")
async def get_voice_config(
    current_user: User = Depends(get_current_user)
):
    """
    Check voice service configuration status.

    Returns which services are available (ElevenLabs, Whisper).
    """
    return {
        "status": "ok",
        "services": voice_service.is_configured()
    }


@router.get("/voice/voices")
async def list_available_voices(
    current_user: User = Depends(get_current_user)
):
    """List available ElevenLabs voices."""
    if not voice_service.is_configured().get("elevenlabs"):
        raise HTTPException(status_code=503, detail="ElevenLabs not configured")

    try:
        voices = await voice_service.get_elevenlabs_voices()
        return {"voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice/quota")
async def check_voice_quota(
    current_user: User = Depends(get_current_user)
):
    """Check ElevenLabs character quota."""
    if not voice_service.is_configured().get("elevenlabs"):
        raise HTTPException(status_code=503, detail="ElevenLabs not configured")

    try:
        quota = await voice_service.check_elevenlabs_quota()
        return quota
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
