"""
Memory System for Champion Clone.

Provides different memory backends:
- VectorMemory: Semantic search with Qdrant
- SessionMemory: Fast session state with Redis
- PersistentMemory: Long-term storage with PostgreSQL
"""

from .vector_store import VectorMemory
from .session_store import SessionMemory
from .schemas import (
    MemoryEntry,
    PatternMemory,
    VoiceProfile,
    SessionState,
    ConversationTurn
)

__all__ = [
    "VectorMemory",
    "SessionMemory",
    "MemoryEntry",
    "PatternMemory",
    "VoiceProfile",
    "SessionState",
    "ConversationTurn"
]
