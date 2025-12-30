"""
Champion Clone Agents.

Multi-agent system with specialized agents:
- AudioAgent: Video/audio processing and transcription
- PatternAgent: Sales pattern extraction and analysis
- TrainingAgent: Training session management
"""

from .base_agent import BaseAgent, AgentStatus, ToolResult, ThinkResult
from .audio_agent import AudioAgent
from .pattern_agent import PatternAgent
from .training_agent import TrainingAgent

__all__ = [
    "BaseAgent",
    "AgentStatus",
    "ToolResult",
    "ThinkResult",
    "AudioAgent",
    "PatternAgent",
    "TrainingAgent"
]
