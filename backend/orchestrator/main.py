"""
Champion Clone Orchestrator - Main coordination layer.

Manages the lifecycle of multi-agent workflows:
1. Receives user requests
2. Routes to Decision Engine for workflow creation
3. Executes workflows across agents
4. Aggregates results
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

from .decision_engine import AgentType, DecisionEngine, Workflow, WorkflowStep

logger = structlog.get_logger()


@dataclass
class WorkflowExecution:
    """Tracks execution state of a workflow."""

    workflow_id: str
    request_id: str
    status: str = "pending"  # pending, running, completed, failed
    started_at: datetime | None = None
    completed_at: datetime | None = None
    results: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    current_step: int = 0


class ChampionCloneOrchestrator:
    """
    Central orchestrator for Champion Clone.

    Responsibilities:
    - Route user requests to appropriate agents
    - Manage multi-step workflows
    - Handle agent coordination
    - Aggregate and return results
    """

    def __init__(self):
        self.decision_engine = DecisionEngine()
        self.agents = {}
        self.active_workflows: dict[str, WorkflowExecution] = {}

        # Lazy load agents to avoid circular imports
        self._agents_loaded = False

    def _load_agents(self):
        """Lazy load agents."""
        if self._agents_loaded:
            return

        from agents.audio_agent.agent import AudioAgent
        from agents.pattern_agent.agent import PatternAgent
        from agents.training_agent.agent import TrainingAgent

        self.agents = {
            AgentType.AUDIO: AudioAgent(),
            AgentType.PATTERN: PatternAgent(),
            AgentType.TRAINING: TrainingAgent(),
        }

        self._agents_loaded = True
        logger.info("orchestrator_agents_loaded", count=len(self.agents))

    async def route(self, task: str, context: dict | None = None) -> dict:
        """
        Main entry point - route a task through the system.

        Args:
            task: User's request in natural language
            context: Optional additional context

        Returns:
            Dict with results and execution metadata
        """
        request_id = str(uuid.uuid4())[:8]
        logger.info("orchestrator_request", request_id=request_id, task=task[:100])

        self._load_agents()

        try:
            # 1. Analyze and create workflow
            workflow = await self.decision_engine.analyze(task, context)

            # 2. Execute workflow
            result = await self.execute_workflow(workflow, request_id, context)

            return result

        except Exception as e:
            logger.error("orchestrator_error", request_id=request_id, error=str(e))
            return {"request_id": request_id, "status": "error", "error": str(e), "task": task}

    async def execute_workflow(self, workflow: Workflow, request_id: str, context: dict | None = None) -> dict:
        """
        Execute a complete workflow.

        Args:
            workflow: The workflow to execute
            request_id: Unique request identifier
            context: Additional context to pass to agents

        Returns:
            Aggregated results from all steps
        """
        execution = WorkflowExecution(
            workflow_id=workflow.id, request_id=request_id, status="running", started_at=datetime.utcnow()
        )
        self.active_workflows[request_id] = execution

        logger.info(
            "workflow_started", workflow_id=workflow.id, steps=len(workflow.steps), reasoning=workflow.reasoning[:100]
        )

        completed_steps: set[int] = set()
        step_results: dict[str, Any] = {}

        try:
            while len(completed_steps) < len(workflow.steps):
                # Get steps ready for execution
                ready_steps = self.decision_engine.get_next_steps(workflow, completed_steps)

                if not ready_steps:
                    # No steps ready but not all complete - deadlock or dependency issue
                    logger.warning("workflow_deadlock", workflow_id=workflow.id)
                    break

                # Check if we should continue
                should_continue, reason = await self.decision_engine.should_continue(
                    step_results,
                    context.get("original_task", "") if context else "",
                    [workflow.steps[i] for i in range(len(workflow.steps)) if i not in completed_steps],
                )

                if not should_continue:
                    logger.info("workflow_early_stop", reason=reason)
                    break

                # Execute ready steps (potentially in parallel)
                if len(ready_steps) > 1:
                    # Parallel execution
                    tasks = [self._execute_step(workflow.steps[i], i, step_results, context) for i in ready_steps]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for i, result in zip(ready_steps, results, strict=False):
                        step_id = f"step_{i}"
                        if isinstance(result, Exception):
                            step_results[step_id] = {"status": "error", "error": str(result)}
                            execution.errors.append({"step": step_id, "error": str(result)})
                        else:
                            step_results[step_id] = result
                        completed_steps.add(i)

                else:
                    # Sequential execution
                    step_idx = ready_steps[0]
                    step_id = f"step_{step_idx}"

                    try:
                        result = await self._execute_step(workflow.steps[step_idx], step_idx, step_results, context)
                        step_results[step_id] = result
                    except Exception as e:
                        step_results[step_id] = {"status": "error", "error": str(e)}
                        execution.errors.append({"step": step_id, "error": str(e)})

                    completed_steps.add(step_idx)

                execution.current_step = len(completed_steps)

            # Mark workflow complete
            execution.status = "completed" if not execution.errors else "completed_with_errors"
            execution.completed_at = datetime.utcnow()
            execution.results = step_results

            duration_ms = (execution.completed_at - execution.started_at).total_seconds() * 1000

            logger.info(
                "workflow_completed",
                workflow_id=workflow.id,
                status=execution.status,
                steps_completed=len(completed_steps),
                duration_ms=duration_ms,
            )

            return {
                "request_id": request_id,
                "workflow_id": workflow.id,
                "status": execution.status,
                "reasoning": workflow.reasoning,
                "results": step_results,
                "errors": execution.errors,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            execution.status = "failed"
            execution.completed_at = datetime.utcnow()
            logger.error("workflow_failed", workflow_id=workflow.id, error=str(e))

            return {
                "request_id": request_id,
                "workflow_id": workflow.id,
                "status": "failed",
                "error": str(e),
                "partial_results": step_results,
            }

    async def _execute_step(
        self, step: WorkflowStep, step_index: int, previous_results: dict, context: dict | None
    ) -> dict:
        """
        Execute a single workflow step.

        Args:
            step: The step to execute
            step_index: Index of the step
            previous_results: Results from previous steps
            context: Additional context

        Returns:
            Step execution result
        """
        agent = self.agents.get(step.agent)
        if not agent:
            raise ValueError(f"Unknown agent: {step.agent}")

        logger.info("step_executing", step_index=step_index, agent=step.agent.value, task=step.task[:100])

        # Build step context with previous results
        step_context = {"previous_results": previous_results, "step_index": step_index, **(context or {})}

        # Execute with timeout
        try:
            result = await asyncio.wait_for(agent.run(step.task, step_context), timeout=step.timeout_seconds)
            return result

        except TimeoutError:
            logger.warning("step_timeout", step_index=step_index, timeout=step.timeout_seconds)
            raise TimeoutError(f"Step {step_index} timed out after {step.timeout_seconds}s")

    async def get_workflow_status(self, request_id: str) -> dict | None:
        """Get status of an active workflow."""
        execution = self.active_workflows.get(request_id)
        if not execution:
            return None

        return {
            "request_id": request_id,
            "workflow_id": execution.workflow_id,
            "status": execution.status,
            "current_step": execution.current_step,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "errors": execution.errors,
        }

    async def cancel_workflow(self, request_id: str) -> bool:
        """Cancel an active workflow."""
        execution = self.active_workflows.get(request_id)
        if not execution or execution.status not in ["pending", "running"]:
            return False

        execution.status = "cancelled"
        execution.completed_at = datetime.utcnow()
        logger.info("workflow_cancelled", request_id=request_id)
        return True

    def get_agent_statuses(self) -> dict:
        """Get status of all agents."""
        self._load_agents()
        return {agent_type.value: agent.get_status() for agent_type, agent in self.agents.items()}
