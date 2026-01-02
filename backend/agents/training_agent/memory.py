"""
Training Agent Memory - Session state with Redis.
"""

from memory.schemas import SessionState
from memory.session_store import TrainingSessionMemory


class TrainingAgentMemory:
    """
    Memory interface for Training Agent.

    Uses Redis for fast session state management.
    """

    def __init__(self):
        self.session_memory = TrainingSessionMemory()

    async def store(self, key: str, value: dict, metadata: dict | None = None) -> bool:
        """Store session data."""
        return await self.session_memory.store(key, value)

    async def retrieve(self, key: str, limit: int = 1) -> dict | None:
        """Retrieve session data."""
        return await self.session_memory.retrieve(key)

    async def create_session(self, session_state: SessionState) -> bool:
        """Create new training session."""
        return await self.session_memory.create_session(session_state)

    async def get_session(self, session_id: str) -> SessionState | None:
        """Get session by ID."""
        return await self.session_memory.get_session(session_id)

    async def update_session(self, session_state: SessionState) -> bool:
        """Update session state."""
        return await self.session_memory.update_session(session_state)

    async def add_turn(
        self, session_id: str, role: str, content: str, feedback: str | None = None, score: float | None = None
    ) -> bool:
        """Add conversation turn to session."""
        return await self.session_memory.add_conversation_turn(
            session_id=session_id, role=role, content=content, feedback=feedback, score=score
        )

    async def complete_session(self, session_id: str) -> SessionState | None:
        """Mark session as completed."""
        return await self.session_memory.complete_session(session_id)

    async def get_active_sessions(self, user_id: str | None = None) -> list[SessionState]:
        """Get active sessions."""
        return await self.session_memory.get_active_sessions(user_id)

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        return await self.session_memory.delete(session_id)
