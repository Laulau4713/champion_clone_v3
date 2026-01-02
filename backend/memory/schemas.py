"""
Memory Schemas - Data structures for memory storage.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MemoryType(Enum):
    """Types of memory entries."""

    PATTERN = "pattern"
    VOICE_PROFILE = "voice_profile"
    SESSION = "session"
    TRANSCRIPT = "transcript"
    FEEDBACK = "feedback"


@dataclass
class MemoryEntry:
    """Base memory entry structure."""

    id: str
    type: MemoryType
    content: str
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    embedding: list[float] | None = None
    score: float | None = None  # Relevance score from search

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "score": self.score,
        }


@dataclass
class PatternMemory:
    """Sales pattern stored in vector memory."""

    id: str
    champion_id: int
    pattern_type: str  # opening, objection, close, key_phrase
    content: str
    context: str | None = None
    effectiveness_score: float = 0.0
    usage_count: int = 0
    examples: list[str] = field(default_factory=list)
    related_patterns: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "champion_id": self.champion_id,
            "pattern_type": self.pattern_type,
            "content": self.content,
            "context": self.context,
            "effectiveness_score": self.effectiveness_score,
            "usage_count": self.usage_count,
            "examples": self.examples,
            "related_patterns": self.related_patterns,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PatternMemory":
        return cls(
            id=data["id"],
            champion_id=data["champion_id"],
            pattern_type=data["pattern_type"],
            content=data["content"],
            context=data.get("context"),
            effectiveness_score=data.get("effectiveness_score", 0.0),
            usage_count=data.get("usage_count", 0),
            examples=data.get("examples", []),
            related_patterns=data.get("related_patterns", []),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
        )


@dataclass
class VoiceProfile:
    """Voice profile for a champion."""

    id: str
    champion_id: int
    name: str
    audio_samples: list[str] = field(default_factory=list)  # Paths to audio files
    elevenlabs_voice_id: str | None = None
    characteristics: dict = field(default_factory=dict)  # tone, pace, etc.
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "champion_id": self.champion_id,
            "name": self.name,
            "audio_samples": self.audio_samples,
            "elevenlabs_voice_id": self.elevenlabs_voice_id,
            "characteristics": self.characteristics,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ConversationTurn:
    """Single turn in a training conversation."""

    role: str  # user, champion, system
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    feedback: str | None = None
    score: float | None = None
    patterns_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "feedback": self.feedback,
            "score": self.score,
            "patterns_used": self.patterns_used,
        }


@dataclass
class SessionState:
    """Training session state stored in Redis."""

    session_id: str
    user_id: str
    champion_id: int
    scenario: dict = field(default_factory=dict)
    conversation: list[ConversationTurn] = field(default_factory=list)
    current_score: float = 0.0
    patterns_to_practice: list[str] = field(default_factory=list)
    tips: list[str] = field(default_factory=list)
    status: str = "active"  # active, paused, completed, abandoned
    system_prompt: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "champion_id": self.champion_id,
            "scenario": self.scenario,
            "conversation": [t.to_dict() for t in self.conversation],
            "current_score": self.current_score,
            "patterns_to_practice": self.patterns_to_practice,
            "tips": self.tips,
            "status": self.status,
            "system_prompt": self.system_prompt,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        conversation = [
            ConversationTurn(
                role=t["role"],
                content=t["content"],
                timestamp=datetime.fromisoformat(t["timestamp"]),
                feedback=t.get("feedback"),
                score=t.get("score"),
                patterns_used=t.get("patterns_used", []),
            )
            for t in data.get("conversation", [])
        ]

        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            champion_id=data["champion_id"],
            scenario=data.get("scenario", {}),
            conversation=conversation,
            current_score=data.get("current_score", 0.0),
            patterns_to_practice=data.get("patterns_to_practice", []),
            tips=data.get("tips", []),
            status=data.get("status", "active"),
            system_prompt=data.get("system_prompt", ""),
            started_at=datetime.fromisoformat(data["started_at"]) if "started_at" in data else datetime.utcnow(),
            last_activity=datetime.fromisoformat(data["last_activity"])
            if "last_activity" in data
            else datetime.utcnow(),
        )

    def add_turn(self, role: str, content: str, feedback: str | None = None, score: float | None = None):
        """Add a conversation turn."""
        turn = ConversationTurn(role=role, content=content, feedback=feedback, score=score)
        self.conversation.append(turn)
        self.last_activity = datetime.utcnow()
        if score is not None:
            self._update_score(score)

    def _update_score(self, new_score: float):
        """Update running average score."""
        user_turns = [t for t in self.conversation if t.role == "user" and t.score is not None]
        if user_turns:
            total = sum(t.score for t in user_turns if t.score)
            self.current_score = total / len(user_turns)
