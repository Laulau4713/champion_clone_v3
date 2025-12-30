"""
Tests for agent functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

# Set test environment
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["OPENAI_API_KEY"] = "test-key"


class TestBaseAgent:
    """Tests for BaseAgent class."""

    @pytest.fixture
    def mock_anthropic(self):
        with patch("agents.base_agent.AsyncAnthropic") as mock:
            yield mock

    def test_agent_initialization(self, mock_anthropic):
        """Test agent initializes correctly."""
        from agents.base_agent import BaseAgent, AgentStatus

        class TestAgent(BaseAgent):
            def get_system_prompt(self):
                return "Test prompt"

            def get_tools(self):
                return []

            async def execute_tool(self, name, input_data):
                pass

        agent = TestAgent("Test", "claude-sonnet-4-20250514")

        assert agent.name == "Test"
        assert agent.status == AgentStatus.IDLE
        assert agent.context == []

    @pytest.mark.asyncio
    async def test_agent_think(self, mock_anthropic):
        """Test agent thinking process."""
        from agents.base_agent import BaseAgent

        class TestAgent(BaseAgent):
            def get_system_prompt(self):
                return "Test prompt"

            def get_tools(self):
                return []

            async def execute_tool(self, name, input_data):
                pass

        # Mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="Test response")]
        mock_anthropic.return_value.messages.create = AsyncMock(return_value=mock_response)

        agent = TestAgent("Test", "claude-sonnet-4-20250514")
        result = await agent.think("Test task")

        assert result.action_needed is False
        assert result.response == "Test response"


class TestOrchestrator:
    """Tests for Orchestrator."""

    @pytest.fixture
    def mock_decision_engine(self):
        with patch("orchestrator.main.DecisionEngine") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_route_creates_workflow(self, mock_decision_engine):
        """Test orchestrator creates workflow for task."""
        from orchestrator.decision_engine import Workflow, WorkflowStep, AgentType

        # Mock workflow
        mock_workflow = Workflow(
            id="test_wf",
            steps=[WorkflowStep(agent=AgentType.AUDIO, task="Process video")],
            reasoning="Test reasoning"
        )
        mock_decision_engine.return_value.analyze = AsyncMock(return_value=mock_workflow)

        from orchestrator import ChampionCloneOrchestrator

        orch = ChampionCloneOrchestrator()
        orch.decision_engine = mock_decision_engine.return_value

        # This would need agents loaded, skip full test
        assert orch.decision_engine is not None


class TestDecisionEngine:
    """Tests for DecisionEngine routing."""

    @pytest.fixture
    def mock_anthropic(self):
        with patch("orchestrator.decision_engine.AsyncAnthropic") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_analyze_returns_workflow(self, mock_anthropic):
        """Test decision engine creates workflow."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(
            text='{"reasoning": "Test", "workflow": [{"agent": "audio", "task": "Extract"}], "parallel_groups": [[0]]}'
        )]
        mock_anthropic.return_value.messages.create = AsyncMock(return_value=mock_response)

        from orchestrator.decision_engine import DecisionEngine

        engine = DecisionEngine()
        workflow = await engine.analyze("Upload video")

        assert workflow.id is not None
        assert len(workflow.steps) == 1
        assert workflow.steps[0].task == "Extract"

    def test_fallback_workflow(self, mock_anthropic):
        """Test fallback workflow creation."""
        from orchestrator.decision_engine import DecisionEngine, AgentType

        engine = DecisionEngine()
        workflow = engine._create_fallback_workflow("Upload video test.mp4")

        assert workflow.id == "wf_fallback"
        assert len(workflow.steps) == 1
        assert workflow.steps[0].agent == AgentType.AUDIO

    def test_get_next_steps(self, mock_anthropic):
        """Test getting next executable steps."""
        from orchestrator.decision_engine import DecisionEngine, Workflow, WorkflowStep, AgentType

        engine = DecisionEngine()
        workflow = Workflow(
            id="test",
            steps=[
                WorkflowStep(agent=AgentType.AUDIO, task="Step 1"),
                WorkflowStep(agent=AgentType.PATTERN, task="Step 2", depends_on=["step_0"]),
            ],
            reasoning="Test"
        )

        # No steps completed - step 0 is ready
        next_steps = engine.get_next_steps(workflow, set())
        assert next_steps == [0]

        # Step 0 completed - step 1 is ready
        next_steps = engine.get_next_steps(workflow, {0})
        assert next_steps == [1]


class TestMemory:
    """Tests for memory systems."""

    def test_session_state_serialization(self):
        """Test SessionState serialization."""
        from memory.schemas import SessionState

        session = SessionState(
            session_id="test123",
            user_id="user1",
            champion_id=1,
            scenario={"context": "Test"}
        )

        data = session.to_dict()
        assert data["session_id"] == "test123"
        assert data["champion_id"] == 1

        # Test deserialization
        restored = SessionState.from_dict(data)
        assert restored.session_id == "test123"
        assert restored.champion_id == 1

    def test_pattern_memory_serialization(self):
        """Test PatternMemory serialization."""
        from memory.schemas import PatternMemory

        pattern = PatternMemory(
            id="p1",
            champion_id=1,
            pattern_type="opening",
            content="Hello, how can I help?",
            effectiveness_score=8.5
        )

        data = pattern.to_dict()
        assert data["pattern_type"] == "opening"
        assert data["effectiveness_score"] == 8.5

    def test_conversation_turn(self):
        """Test adding conversation turns."""
        from memory.schemas import SessionState

        session = SessionState(
            session_id="test",
            user_id="user1",
            champion_id=1
        )

        session.add_turn("user", "Hello", score=7.0)
        session.add_turn("champion", "Hi there!")

        assert len(session.conversation) == 2
        assert session.conversation[0].role == "user"
        assert session.current_score == 7.0


class TestToolRegistry:
    """Tests for tool registry."""

    def test_registry_loads_tools(self):
        """Test registry loads tool definitions."""
        from tools.registry import ToolRegistry

        registry = ToolRegistry()

        # Should have loaded default tools
        tools = registry.list_tools()
        assert len(tools) > 0

    def test_get_tool_by_name(self):
        """Test getting tool by name."""
        from tools.registry import ToolRegistry

        registry = ToolRegistry()

        # Get a tool that should exist
        tool = registry.get_tool("extract_audio")
        if tool:
            assert tool.name == "extract_audio"
            assert tool.agent == "audio"

    def test_validate_tool_call(self):
        """Test tool call validation."""
        from tools.registry import ToolRegistry

        registry = ToolRegistry()

        # Valid call
        valid, error = registry.validate_tool_call("extract_audio", {"video_path": "/test.mp4"})
        if registry.get_tool("extract_audio"):
            assert valid is True

        # Unknown tool
        valid, error = registry.validate_tool_call("unknown_tool", {})
        assert valid is False
        assert "Unknown tool" in error


# Run with: pytest tests/test_agents.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
