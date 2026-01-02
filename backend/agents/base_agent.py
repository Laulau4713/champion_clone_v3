"""
Base Agent - Abstract class for all Champion Clone agents.

Each agent is an autonomous unit capable of:
- Thinking: Analyzing tasks and deciding on actions
- Acting: Executing tools to accomplish tasks
- Remembering: Storing and retrieving from memory
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import structlog
from anthropic import AsyncAnthropic

logger = structlog.get_logger()


class AgentStatus(Enum):
    """Agent execution status."""

    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class AgentMessage:
    """Message in agent's context."""

    role: str  # "user", "assistant", "tool_result"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tool_use_id: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolResult:
    """Result from tool execution."""

    tool_name: str
    success: bool
    output: Any
    error: str | None = None
    execution_time_ms: float = 0


@dataclass
class ThinkResult:
    """Result from agent thinking."""

    action_needed: bool
    action: dict | None = None  # {"tool": "...", "input": {...}}
    response: str | None = None
    reasoning: str | None = None
    tool_use_id: str | None = None


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Each agent is specialized for a domain (audio, patterns, training)
    and has its own:
    - System prompt defining its role
    - Set of tools it can use
    - Memory system for persistence
    """

    def __init__(
        self,
        name: str,
        model: str = "claude-sonnet-4-20250514",
        max_context_messages: int = 50,
        max_iterations: int = 10,
    ):
        self.name = name
        self.model = model
        self.max_context_messages = max_context_messages
        self.max_iterations = max_iterations

        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.status = AgentStatus.IDLE
        self.context: list[AgentMessage] = []
        self.tools: list[dict] = []
        self.memory = None  # To be set by subclass

        self._iteration_count = 0

        logger.info("agent_initialized", name=name, model=model)

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the agent's system prompt defining its role and capabilities."""
        pass

    @abstractmethod
    async def execute_tool(self, name: str, input_data: dict) -> ToolResult:
        """Execute a specific tool. Implemented by each agent."""
        pass

    @abstractmethod
    def get_tools(self) -> list[dict]:
        """Return the list of tools available to this agent."""
        pass

    async def think(self, task: str, context: dict | None = None) -> ThinkResult:
        """
        Analyze a task and decide what action to take.

        Args:
            task: The task description
            context: Optional additional context

        Returns:
            ThinkResult with action decision
        """
        self.status = AgentStatus.THINKING
        self._iteration_count = 0

        # Add task to context
        self._add_to_context(
            AgentMessage(
                role="user",
                content=self._format_task(task, context),
            )
        )

        logger.info("agent_thinking", agent=self.name, task=task[:100])

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.get_system_prompt(),
                messages=self._get_messages_for_api(),
                tools=self.get_tools() if self.get_tools() else None,
            )

            return self._parse_response(response)

        except Exception as e:
            logger.error("agent_think_error", agent=self.name, error=str(e))
            self.status = AgentStatus.ERROR
            return ThinkResult(action_needed=False, response=None, reasoning=f"Error during thinking: {str(e)}")

    async def act(self, action: dict) -> ToolResult:
        """
        Execute an action using the specified tool.

        Args:
            action: Dict with 'tool' name and 'input' data

        Returns:
            ToolResult with execution outcome
        """
        self.status = AgentStatus.ACTING
        tool_name = action.get("tool")
        tool_input = action.get("input", {})

        logger.info("agent_acting", agent=self.name, tool=tool_name)

        start_time = datetime.utcnow()

        try:
            result = await self.execute_tool(tool_name, tool_input)

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time

            logger.info(
                "agent_action_complete", agent=self.name, tool=tool_name, success=result.success, time_ms=execution_time
            )

            return result

        except Exception as e:
            logger.error("agent_action_error", agent=self.name, tool=tool_name, error=str(e))
            return ToolResult(tool_name=tool_name, success=False, output=None, error=str(e))

    async def run(self, task: str, context: dict | None = None) -> dict:
        """
        Run the full think-act loop until completion.

        This is the main entry point for agent execution.
        It will:
        1. Think about the task
        2. Execute tools if needed
        3. Continue until task is complete or max iterations reached

        Args:
            task: The task to accomplish
            context: Optional additional context

        Returns:
            Dict with final result and execution trace
        """
        trace = []
        final_result = None

        while self._iteration_count < self.max_iterations:
            self._iteration_count += 1

            # Think phase
            think_result = await self.think(
                task if self._iteration_count == 1 else "Continue based on previous result", context
            )
            trace.append({"phase": "think", "result": think_result.__dict__})

            if not think_result.action_needed:
                # No more actions needed, we're done
                final_result = think_result.response
                self.status = AgentStatus.COMPLETED
                break

            # Act phase
            action_result = await self.act(think_result.action)
            trace.append({"phase": "act", "result": action_result.__dict__})

            # Add tool result to context for next iteration
            self._add_to_context(
                AgentMessage(
                    role="tool_result",
                    content=json.dumps(
                        {
                            "tool": action_result.tool_name,
                            "success": action_result.success,
                            "output": action_result.output,
                            "error": action_result.error,
                        }
                    ),
                    tool_use_id=think_result.tool_use_id,
                )
            )

            if not action_result.success:
                # Tool failed, let agent handle it in next think
                continue

        if self._iteration_count >= self.max_iterations:
            logger.warning("agent_max_iterations", agent=self.name)
            self.status = AgentStatus.ERROR

        return {
            "agent": self.name,
            "task": task,
            "result": final_result,
            "iterations": self._iteration_count,
            "status": self.status.value,
            "trace": trace,
        }

    async def remember(self, key: str, value: Any, metadata: dict | None = None) -> bool:
        """
        Store something in agent's memory.

        Args:
            key: Unique identifier
            value: Data to store
            metadata: Optional metadata

        Returns:
            True if successful
        """
        if self.memory is None:
            logger.warning("agent_no_memory", agent=self.name)
            return False

        try:
            await self.memory.store(key, value, metadata or {})
            logger.debug("agent_remembered", agent=self.name, key=key)
            return True
        except Exception as e:
            logger.error("agent_remember_error", agent=self.name, error=str(e))
            return False

    async def recall(self, query: str, limit: int = 5) -> list[dict]:
        """
        Retrieve from agent's memory.

        Args:
            query: Search query
            limit: Max results to return

        Returns:
            List of matching memory entries
        """
        if self.memory is None:
            logger.warning("agent_no_memory", agent=self.name)
            return []

        try:
            results = await self.memory.retrieve(query, limit)
            logger.debug("agent_recalled", agent=self.name, query=query[:50], count=len(results))
            return results
        except Exception as e:
            logger.error("agent_recall_error", agent=self.name, error=str(e))
            return []

    def _add_to_context(self, message: AgentMessage) -> None:
        """Add message to context, managing window size."""
        self.context.append(message)

        # Trim context if too long
        if len(self.context) > self.max_context_messages:
            # Keep first message (usually the task) and recent messages
            self.context = [self.context[0]] + self.context[-(self.max_context_messages - 1) :]

    def _get_messages_for_api(self) -> list[dict]:
        """Convert context to API message format."""
        messages = []

        for msg in self.context:
            if msg.role == "tool_result":
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {"type": "tool_result", "tool_use_id": msg.tool_use_id or "unknown", "content": msg.content}
                        ],
                    }
                )
            else:
                messages.append({"role": msg.role, "content": msg.content})

        return messages

    def _format_task(self, task: str, context: dict | None = None) -> str:
        """Format task with optional context."""
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            return f"{task}\n\nContext:\n{context_str}"
        return task

    def _parse_response(self, response) -> ThinkResult:
        """Parse Claude API response into ThinkResult."""
        # Check for tool use
        for block in response.content:
            if block.type == "tool_use":
                return ThinkResult(
                    action_needed=True,
                    action={"tool": block.name, "input": block.input},
                    tool_use_id=block.id,
                    reasoning=None,
                )

        # Text response (no tool use)
        text_content = ""
        for block in response.content:
            if block.type == "text":
                text_content += block.text

        # Add assistant response to context
        self._add_to_context(AgentMessage(role="assistant", content=text_content))

        return ThinkResult(action_needed=False, response=text_content, reasoning=None)

    def reset(self) -> None:
        """Reset agent state."""
        self.context = []
        self.status = AgentStatus.IDLE
        self._iteration_count = 0
        logger.info("agent_reset", agent=self.name)

    def get_status(self) -> dict:
        """Get current agent status."""
        return {
            "name": self.name,
            "model": self.model,
            "status": self.status.value,
            "context_length": len(self.context),
            "iteration": self._iteration_count,
        }
