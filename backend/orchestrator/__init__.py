"""
Champion Clone Orchestrator.

The orchestrator is the central coordination layer that:
- Routes tasks to appropriate agents
- Manages multi-agent workflows
- Maintains global context
"""

from .main import ChampionCloneOrchestrator
from .decision_engine import DecisionEngine, WorkflowStep, Workflow

__all__ = [
    "ChampionCloneOrchestrator",
    "DecisionEngine",
    "WorkflowStep",
    "Workflow"
]
