"""
Session Memory - Fast session state with Redis.

Used for:
- Active training sessions
- Conversation state
- Real-time scoring
"""

import os
import json
from typing import Optional, Any
from datetime import datetime, timedelta

import structlog

logger = structlog.get_logger()

# Try to import Redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis_not_available", message="Redis client not installed")

from .schemas import SessionState, ConversationTurn


class SessionMemory:
    """
    Session-based memory using Redis.

    Features:
    - Fast key-value storage
    - TTL for automatic expiration
    - Pub/Sub for real-time updates
    - Session state management
    """

    DEFAULT_TTL = 3600 * 4  # 4 hours
    KEY_PREFIX = "champion_clone:session:"

    def __init__(self, url: Optional[str] = None, ttl: int = DEFAULT_TTL):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.ttl = ttl
        self.client: Optional[redis.Redis] = None

        if REDIS_AVAILABLE:
            self.client = redis.from_url(self.url, decode_responses=True)
            logger.info("session_memory_initialized", url=self.url.split("@")[-1])
        else:
            logger.warning("session_memory_fallback", message="Using in-memory fallback")
            self._fallback_store: dict[str, Any] = {}

    def _key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"{self.KEY_PREFIX}{session_id}"

    async def store(
        self,
        key: str,
        value: Any,
        metadata: Optional[dict] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store a value.

        Args:
            key: Session key
            value: Value to store (will be JSON serialized)
            metadata: Not used for Redis (included for interface compatibility)
            ttl: Custom TTL in seconds

        Returns:
            True if successful
        """
        try:
            data = json.dumps(value) if not isinstance(value, str) else value

            if self.client:
                await self.client.setex(
                    self._key(key),
                    ttl or self.ttl,
                    data
                )
            else:
                self._fallback_store[key] = {
                    "data": data,
                    "expires": datetime.utcnow() + timedelta(seconds=ttl or self.ttl)
                }

            return True

        except Exception as e:
            logger.error("session_store_error", key=key, error=str(e))
            return False

    async def retrieve(self, key: str, limit: int = 1) -> Optional[Any]:
        """
        Retrieve a value.

        Args:
            key: Session key
            limit: Not used for Redis (included for interface compatibility)

        Returns:
            Stored value or None
        """
        try:
            if self.client:
                data = await self.client.get(self._key(key))
            else:
                entry = self._fallback_store.get(key)
                if entry and entry["expires"] > datetime.utcnow():
                    data = entry["data"]
                else:
                    data = None

            if data:
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return data

            return None

        except Exception as e:
            logger.error("session_retrieve_error", key=key, error=str(e))
            return None

    async def delete(self, key: str) -> bool:
        """Delete a session."""
        try:
            if self.client:
                await self.client.delete(self._key(key))
            else:
                self._fallback_store.pop(key, None)
            return True
        except Exception as e:
            logger.error("session_delete_error", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """Check if session exists."""
        try:
            if self.client:
                return await self.client.exists(self._key(key)) > 0
            else:
                entry = self._fallback_store.get(key)
                return entry is not None and entry["expires"] > datetime.utcnow()
        except Exception as e:
            logger.error("session_exists_error", key=key, error=str(e))
            return False

    async def extend_ttl(self, key: str, additional_seconds: int) -> bool:
        """Extend session TTL."""
        try:
            if self.client:
                return await self.client.expire(
                    self._key(key),
                    additional_seconds
                )
            else:
                entry = self._fallback_store.get(key)
                if entry:
                    entry["expires"] = datetime.utcnow() + timedelta(seconds=additional_seconds)
                    return True
            return False
        except Exception as e:
            logger.error("session_extend_error", key=key, error=str(e))
            return False

    async def get_all_keys(self, pattern: str = "*") -> list[str]:
        """Get all session keys matching pattern."""
        try:
            if self.client:
                full_pattern = f"{self.KEY_PREFIX}{pattern}"
                keys = await self.client.keys(full_pattern)
                return [k.replace(self.KEY_PREFIX, "") for k in keys]
            else:
                return list(self._fallback_store.keys())
        except Exception as e:
            logger.error("session_keys_error", error=str(e))
            return []

    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()


class TrainingSessionMemory(SessionMemory):
    """Specialized session memory for training sessions."""

    async def create_session(self, session_state: SessionState) -> bool:
        """Create a new training session."""
        return await self.store(
            session_state.session_id,
            session_state.to_dict()
        )

    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get a training session."""
        data = await self.retrieve(session_id)
        if data:
            return SessionState.from_dict(data)
        return None

    async def update_session(self, session_state: SessionState) -> bool:
        """Update a training session."""
        session_state.last_activity = datetime.utcnow()
        return await self.store(
            session_state.session_id,
            session_state.to_dict()
        )

    async def add_conversation_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        feedback: Optional[str] = None,
        score: Optional[float] = None
    ) -> bool:
        """Add a turn to session conversation."""
        session = await self.get_session(session_id)
        if not session:
            return False

        session.add_turn(role, content, feedback, score)
        return await self.update_session(session)

    async def complete_session(self, session_id: str) -> Optional[SessionState]:
        """Mark session as completed."""
        session = await self.get_session(session_id)
        if not session:
            return None

        session.status = "completed"
        await self.update_session(session)
        return session

    async def get_active_sessions(self, user_id: Optional[str] = None) -> list[SessionState]:
        """Get all active sessions, optionally filtered by user."""
        sessions = []
        keys = await self.get_all_keys()

        for key in keys:
            session = await self.get_session(key)
            if session and session.status == "active":
                if user_id is None or session.user_id == user_id:
                    sessions.append(session)

        return sessions
