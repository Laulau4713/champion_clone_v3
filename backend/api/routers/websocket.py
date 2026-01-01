"""
WebSocket Router for real-time voice training.

Provides bidirectional communication for:
- Real-time audio streaming
- Instant gauge updates
- Live prospect responses
- Event notifications (reversals, situational events)
"""

import json
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError
import structlog

from config import get_settings
from database import AsyncSessionLocal
from models import User, VoiceTrainingSession
from services.training_service_v2 import TrainingServiceV2

settings = get_settings()
logger = structlog.get_logger()

router = APIRouter(tags=["WebSocket"])


# ============================================
# Connection Manager
# ============================================

class ConnectionManager:
    """Manages WebSocket connections for voice training sessions."""

    def __init__(self):
        # {session_id: {user_id: WebSocket}}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        # {user_id: session_id} for quick lookup
        self.user_sessions: Dict[int, int] = {}

    async def connect(self, websocket: WebSocket, session_id: int, user_id: int):
        """Accept and register a WebSocket connection."""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}

        self.active_connections[session_id][user_id] = websocket
        self.user_sessions[user_id] = session_id

        logger.info(
            "websocket_connected",
            session_id=session_id,
            user_id=user_id,
            total_connections=len(self.active_connections)
        )

    def disconnect(self, session_id: int, user_id: int):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            self.active_connections[session_id].pop(user_id, None)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

        self.user_sessions.pop(user_id, None)

        logger.info(
            "websocket_disconnected",
            session_id=session_id,
            user_id=user_id
        )

    async def send_to_session(self, session_id: int, message: dict):
        """Send a message to all connections in a session."""
        if session_id in self.active_connections:
            for websocket in self.active_connections[session_id].values():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error("websocket_send_error", error=str(e))

    async def send_to_user(self, session_id: int, user_id: int, message: dict):
        """Send a message to a specific user in a session."""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id].get(user_id)
            if websocket:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error("websocket_send_error", error=str(e))


manager = ConnectionManager()


# ============================================
# Authentication
# ============================================

async def get_user_from_token(token: str) -> Optional[User]:
    """Validate JWT token and return user."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            return None

        async with AsyncSessionLocal() as db:
            user = await db.get(User, int(user_id))
            return user

    except JWTError as e:
        logger.error("websocket_auth_error", error=str(e))
        return None


# ============================================
# WebSocket Endpoint
# ============================================

@router.websocket("/ws/voice/{session_id}")
async def voice_training_websocket(
    websocket: WebSocket,
    session_id: int,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time voice training.

    Connect with: ws://host/ws/voice/{session_id}?token={jwt_token}

    Client -> Server Messages:
    - {"type": "user_message", "text": "...", "audio_base64": "..."}
    - {"type": "end_session"}
    - {"type": "ping"}

    Server -> Client Messages:
    - {"type": "connected", "session_id": ..., "jauge": ..., "mood": ...}
    - {"type": "prospect_response", "text": "...", "audio_base64": "...", ...}
    - {"type": "gauge_update", "jauge": ..., "delta": ..., "mood": ...}
    - {"type": "reversal", "type": "...", "message": "..."}
    - {"type": "event", "event_type": "...", "message": "..."}
    - {"type": "session_ended", "evaluation": {...}}
    - {"type": "error", "message": "..."}
    - {"type": "pong"}
    """
    # Authenticate
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Verify session ownership
    async with AsyncSessionLocal() as db:
        session = await db.get(VoiceTrainingSession, session_id)
        if not session or session.user_id != user.id:
            await websocket.close(code=4004, reason="Session not found")
            return

        if session.status != "active":
            await websocket.close(code=4009, reason="Session not active")
            return

    # Connect
    await manager.connect(websocket, session_id, user.id)

    # Send initial state
    await websocket.send_json({
        "type": "connected",
        "session_id": session_id,
        "jauge": session.current_gauge,
        "mood": session.current_mood,
        "scenario": {
            "title": session.scenario_json.get("title"),
            "prospect_name": session.scenario_json.get("prospect", {}).get("name"),
        },
        "timestamp": datetime.utcnow().isoformat()
    })

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            elif message_type == "user_message":
                await handle_user_message(
                    websocket=websocket,
                    session_id=session_id,
                    user=user,
                    text=data.get("text"),
                    audio_base64=data.get("audio_base64")
                )

            elif message_type == "end_session":
                await handle_end_session(
                    websocket=websocket,
                    session_id=session_id,
                    user=user
                )
                break  # Close connection after ending

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })

    except WebSocketDisconnect:
        logger.info("websocket_client_disconnected", session_id=session_id, user_id=user.id)
    except Exception as e:
        logger.error("websocket_error", session_id=session_id, error=str(e))
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        manager.disconnect(session_id, user.id)


# ============================================
# Message Handlers
# ============================================

async def handle_user_message(
    websocket: WebSocket,
    session_id: int,
    user: User,
    text: Optional[str],
    audio_base64: Optional[str]
):
    """Process user message and send prospect response."""

    if not text and not audio_base64:
        await websocket.send_json({
            "type": "error",
            "message": "text or audio_base64 required"
        })
        return

    async with AsyncSessionLocal() as db:
        service = TrainingServiceV2(db)

        try:
            # Send "thinking" indicator
            await websocket.send_json({
                "type": "prospect_thinking",
                "timestamp": datetime.utcnow().isoformat()
            })

            # Process message
            response = await service.process_user_message(
                session_id=session_id,
                user=user,
                audio_base64=audio_base64,
                text=text
            )

            # Send gauge update first (for animation)
            await websocket.send_json({
                "type": "gauge_update",
                "jauge": response.jauge,
                "delta": response.jauge_delta,
                "mood": response.mood,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Small delay for gauge animation
            await asyncio.sleep(0.3)

            # Check for events/reversals
            if response.is_event:
                await websocket.send_json({
                    "type": "event",
                    "event_type": response.event_type,
                    "message": response.text,
                    "timestamp": datetime.utcnow().isoformat()
                })

            # Send prospect response
            await websocket.send_json({
                "type": "prospect_response",
                "text": response.text,
                "audio_base64": response.audio_base64,
                "mood": response.mood,
                "jauge": response.jauge,
                "jauge_delta": response.jauge_delta,
                "behavioral_cue": response.behavioral_cue,
                "is_event": response.is_event,
                "event_type": response.event_type,
                "feedback": response.feedback,
                "conversion_possible": response.conversion_possible,
                "timestamp": datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error("websocket_message_error", error=str(e))
            await websocket.send_json({
                "type": "error",
                "message": f"Failed to process message: {str(e)}"
            })


async def handle_end_session(
    websocket: WebSocket,
    session_id: int,
    user: User
):
    """End session and send evaluation."""

    async with AsyncSessionLocal() as db:
        service = TrainingServiceV2(db)

        try:
            result = await service.end_session(
                session_id=session_id,
                user=user
            )

            await websocket.send_json({
                "type": "session_ended",
                "session_id": session_id,
                "status": result["status"],
                "evaluation": result["evaluation"],
                "timestamp": datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error("websocket_end_session_error", error=str(e))
            await websocket.send_json({
                "type": "error",
                "message": f"Failed to end session: {str(e)}"
            })


# ============================================
# Utility: Send event to session
# ============================================

async def notify_session_event(session_id: int, event_type: str, data: dict):
    """Send an event notification to all users in a session."""
    await manager.send_to_session(session_id, {
        "type": event_type,
        **data,
        "timestamp": datetime.utcnow().isoformat()
    })
