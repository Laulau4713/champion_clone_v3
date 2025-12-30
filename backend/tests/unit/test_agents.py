"""
Unit Tests for Agent Tools.

Tests agent tools with mocked APIs (Groq, Whisper).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os
import json

# Set test environment
os.environ["GROQ_API_KEY"] = "test-groq-key"
os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"


# ============================================
# PatternTools Tests
# ============================================

class TestPatternTools:
    """Tests for PatternTools with mocked Groq API."""

    @pytest.fixture
    def mock_groq_response(self):
        """Create a mock Groq response."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "openings": ["Bonjour, comment allez-vous?"],
                "objection_handlers": [{"objection": "trop cher", "response": "Je comprends"}],
                "closes": ["Ça vous intéresse?"],
                "key_phrases": ["Je comprends"],
                "tone_style": "professionnel",
                "success_patterns": ["empathie"],
                "communication_techniques": []
            })))
        ]
        return mock_response

    @pytest.mark.asyncio
    async def test_extract_patterns_success(self, mock_groq_response):
        """Test successful pattern extraction."""
        with patch('agents.pattern_agent.tools.AsyncGroq') as mock_groq:
            mock_groq.return_value.chat.completions.create = AsyncMock(
                return_value=mock_groq_response
            )

            from agents.pattern_agent.tools import PatternTools
            tools = PatternTools()

            transcript = """
            Vendeur: Bonjour, comment allez-vous?
            Client: Bien merci.
            Vendeur: Je comprends que vous êtes occupé.
            """

            result = await tools.extract_patterns(transcript)

            assert result["success"] is True
            assert "patterns" in result
            assert len(result["patterns"]["openings"]) > 0

    @pytest.mark.asyncio
    async def test_extract_patterns_short_transcript(self):
        """Test extraction fails with short transcript."""
        with patch('agents.pattern_agent.tools.AsyncGroq'):
            from agents.pattern_agent.tools import PatternTools
            tools = PatternTools()

            result = await tools.extract_patterns("Too short")

            assert result["success"] is False
            assert "too short" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_generate_scenarios_success(self):
        """Test successful scenario generation."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps([
                {
                    "context": "Appel à froid",
                    "prospect_type": "PME",
                    "challenge": "Obtenir un RDV",
                    "objectives": ["Créer le rapport"],
                    "difficulty": "medium"
                }
            ])))
        ]

        with patch('agents.pattern_agent.tools.AsyncGroq') as mock_groq:
            mock_groq.return_value.chat.completions.create = AsyncMock(
                return_value=mock_response
            )

            from agents.pattern_agent.tools import PatternTools
            tools = PatternTools()

            patterns = {"openings": ["Bonjour"], "closes": ["Merci"]}
            result = await tools.generate_scenarios(patterns, count=1)

            assert result["success"] is True
            assert len(result["scenarios"]) == 1
            assert result["scenarios"][0]["difficulty"] == "medium"

    @pytest.mark.asyncio
    async def test_analyze_response_success(self):
        """Test response analysis."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "score": 8,
                "patterns_used": ["empathie"],
                "patterns_missed": [],
                "feedback": "Bonne réponse",
                "strengths": ["Écoute active"],
                "improvements": [],
                "champion_alternative": "Alternative"
            })))
        ]

        with patch('agents.pattern_agent.tools.AsyncGroq') as mock_groq:
            mock_groq.return_value.chat.completions.create = AsyncMock(
                return_value=mock_response
            )

            from agents.pattern_agent.tools import PatternTools
            tools = PatternTools()

            result = await tools.analyze_response_against_patterns(
                response="Je comprends votre situation",
                patterns={"openings": [], "key_phrases": ["Je comprends"]},
                context="Appel commercial"
            )

            assert result["success"] is True
            assert result["score"] == 8

    def test_validate_patterns(self):
        """Test pattern validation."""
        with patch('agents.pattern_agent.tools.AsyncGroq'):
            from agents.pattern_agent.tools import PatternTools
            tools = PatternTools()

            # Test with missing keys
            patterns = {"openings": ["test"]}
            validated = tools._validate_patterns(patterns)

            assert "openings" in validated
            assert "objection_handlers" in validated
            assert "closes" in validated
            assert isinstance(validated["openings"], list)

    def test_validate_scenario(self):
        """Test scenario validation."""
        with patch('agents.pattern_agent.tools.AsyncGroq'):
            from agents.pattern_agent.tools import PatternTools
            tools = PatternTools()

            scenario = {"context": "Test", "difficulty": "hard"}
            validated = tools._validate_scenario(scenario)

            assert "id" in validated
            assert validated["context"] == "Test"
            assert validated["difficulty"] == "hard"
            assert "objectives" in validated

    def test_get_default_scenario(self):
        """Test default scenario generation."""
        with patch('agents.pattern_agent.tools.AsyncGroq'):
            from agents.pattern_agent.tools import PatternTools
            tools = PatternTools()

            default = tools._get_default_scenario()

            assert "context" in default
            assert "difficulty" in default
            assert default["difficulty"] == "medium"


# ============================================
# TrainingTools Tests
# ============================================

class TestTrainingTools:
    """Tests for TrainingTools with mocked Groq API."""

    @pytest.mark.asyncio
    async def test_generate_prospect_response_success(self):
        """Test prospect response generation."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content="Bonjour, je suis occupé en ce moment."
            ))
        ]

        with patch('agents.training_agent.tools.AsyncGroq') as mock_groq:
            mock_groq.return_value.chat.completions.create = AsyncMock(
                return_value=mock_response
            )

            from agents.training_agent.tools import TrainingTools
            tools = TrainingTools()

            result = await tools.generate_prospect_response(
                user_message="Bonjour, comment allez-vous?",
                conversation_history=[],
                scenario={"context": "Vente CRM", "difficulty": "medium"},
                patterns={"openings": ["Bonjour"]}
            )

            assert result["success"] is True
            assert "response" in result
            assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_evaluate_response_success(self):
        """Test response evaluation."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "score": 7,
                "feedback": "Bonne approche",
                "suggestions": ["Poser plus de questions"],
                "patterns_used": ["empathie"],
                "patterns_to_try": ["closing"]
            })))
        ]

        with patch('agents.training_agent.tools.AsyncGroq') as mock_groq:
            mock_groq.return_value.chat.completions.create = AsyncMock(
                return_value=mock_response
            )

            from agents.training_agent.tools import TrainingTools
            tools = TrainingTools()

            result = await tools.evaluate_response(
                user_response="Je comprends votre besoin",
                patterns={"openings": [], "key_phrases": []},
                scenario={"context": "test", "difficulty": "medium"},
                conversation_history=[{"role": "user", "content": "Bonjour"}]
            )

            assert result["success"] is True
            assert result["score"] == 7
            assert "feedback" in result

    @pytest.mark.asyncio
    async def test_generate_session_summary_success(self):
        """Test session summary generation."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "overall_score": 7.5,
                "feedback_summary": "Bonne session",
                "strengths": ["Communication claire"],
                "areas_for_improvement": ["Closing"],
                "patterns_mastered": ["Ouverture"],
                "patterns_to_practice": ["Objections"],
                "next_steps": ["Pratiquer le closing"]
            })))
        ]

        with patch('agents.training_agent.tools.AsyncGroq') as mock_groq:
            mock_groq.return_value.chat.completions.create = AsyncMock(
                return_value=mock_response
            )

            from agents.training_agent.tools import TrainingTools
            tools = TrainingTools()

            result = await tools.generate_session_summary(
                conversation=[
                    {"role": "user", "content": "Bonjour"},
                    {"role": "champion", "content": "Bonjour"}
                ],
                patterns={"openings": []},
                scenario={"context": "test"}
            )

            assert result["success"] is True
            assert result["overall_score"] == 7.5
            assert "strengths" in result

    @pytest.mark.asyncio
    async def test_generate_tips(self):
        """Test tips generation."""
        with patch('agents.training_agent.tools.AsyncGroq'):
            from agents.training_agent.tools import TrainingTools
            tools = TrainingTools()

            tips = await tools.generate_tips(
                scenario={"difficulty": "hard", "objectives": ["Convaincre"]},
                patterns={
                    "openings": ["Bonjour, je suis ravi de vous parler"],
                    "key_phrases": ["Je comprends parfaitement"]
                }
            )

            assert isinstance(tips, list)
            assert len(tips) > 0

    def test_check_session_complete_max_messages(self):
        """Test session completion by message count."""
        with patch('agents.training_agent.tools.AsyncGroq'):
            from agents.training_agent.tools import TrainingTools
            tools = TrainingTools()

            # 10+ user messages should end session
            conversation = [{"role": "user", "content": f"msg{i}"} for i in range(10)]

            assert tools.check_session_complete(conversation, {}) is True

    def test_check_session_complete_ending_phrase(self):
        """Test session completion by ending phrase."""
        with patch('agents.training_agent.tools.AsyncGroq'):
            from agents.training_agent.tools import TrainingTools
            tools = TrainingTools()

            conversation = [{"role": "champion", "content": "D'accord, on signe le contrat"}]

            assert tools.check_session_complete(conversation, {}) is True

    def test_check_session_not_complete(self):
        """Test session not complete."""
        with patch('agents.training_agent.tools.AsyncGroq'):
            from agents.training_agent.tools import TrainingTools
            tools = TrainingTools()

            conversation = [
                {"role": "user", "content": "Bonjour"},
                {"role": "champion", "content": "Bonjour, comment puis-je vous aider?"}
            ]

            assert tools.check_session_complete(conversation, {}) is False


# ============================================
# AudioTools Tests
# ============================================

class TestAudioTools:
    """Tests for AudioTools with mocked Whisper."""

    def test_init_without_api_keys(self):
        """Test AudioTools initializes without requiring API keys."""
        with patch('agents.audio_agent.tools.WHISPER_AVAILABLE', True):
            from agents.audio_agent.tools import AudioTools
            tools = AudioTools()

            assert tools._whisper_model is None  # Lazy loaded
            assert tools._whisper_model_size == "base"

    @pytest.mark.asyncio
    async def test_transcribe_file_not_found(self):
        """Test transcription with non-existent file."""
        with patch('agents.audio_agent.tools.WHISPER_AVAILABLE', True):
            from agents.audio_agent.tools import AudioTools
            tools = AudioTools()

            result = await tools.transcribe("/nonexistent/file.mp3")

            assert result["success"] is False
            assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_transcribe_whisper_not_available(self):
        """Test transcription when Whisper is not installed."""
        with patch('agents.audio_agent.tools.WHISPER_AVAILABLE', False):
            from agents.audio_agent.tools import AudioTools
            tools = AudioTools()

            # Create a temp file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                f.write(b'fake audio data')
                temp_path = f.name

            try:
                result = await tools.transcribe(temp_path)
                assert result["success"] is False
                assert "not installed" in result["error"].lower()
            finally:
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_analyze_audio_file_not_found(self):
        """Test audio analysis with non-existent file."""
        from agents.audio_agent.tools import AudioTools
        tools = AudioTools()

        result = await tools.analyze_audio("/nonexistent/file.mp3")

        assert result["success"] is False

    def test_clone_voice_no_elevenlabs(self):
        """Test voice cloning without ElevenLabs."""
        from agents.audio_agent.tools import AudioTools
        tools = AudioTools()
        tools.elevenlabs = None

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            tools.clone_voice("Test", ["/fake/path.mp3"])
        )

        assert result["success"] is False
        assert "not configured" in result["error"].lower()

    def test_text_to_speech_no_elevenlabs(self):
        """Test TTS without ElevenLabs."""
        from agents.audio_agent.tools import AudioTools
        tools = AudioTools()
        tools.elevenlabs = None

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            tools.text_to_speech("Hello", "voice_id")
        )

        assert result["success"] is False
        assert "not configured" in result["error"].lower()


# ============================================
# BaseAgent Tests
# ============================================

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

    def test_agent_get_status(self, mock_anthropic):
        """Test agent status retrieval."""
        from agents.base_agent import BaseAgent, AgentStatus

        class TestAgent(BaseAgent):
            def get_system_prompt(self):
                return "Test prompt"

            def get_tools(self):
                return [{"name": "test_tool"}]

            async def execute_tool(self, name, input_data):
                pass

        agent = TestAgent("TestAgent", "claude-sonnet-4-20250514")
        status = agent.get_status()

        assert status["name"] == "TestAgent"
        assert status["status"] == AgentStatus.IDLE.value
        # Check that status dict has expected keys
        assert "model" in status
        assert "context_length" in status or "iteration" in status

    def test_agent_reset(self, mock_anthropic):
        """Test agent reset."""
        from agents.base_agent import BaseAgent, AgentStatus

        class TestAgent(BaseAgent):
            def get_system_prompt(self):
                return "Test"

            def get_tools(self):
                return []

            async def execute_tool(self, name, input_data):
                pass

        agent = TestAgent("Test", "claude-sonnet-4-20250514")
        agent.context = [{"role": "user", "content": "test"}]

        agent.reset()

        assert agent.context == []
        assert agent.status == AgentStatus.IDLE

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

        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="Test response")]
        mock_anthropic.return_value.messages.create = AsyncMock(return_value=mock_response)

        agent = TestAgent("Test", "claude-sonnet-4-20250514")
        result = await agent.think("Test task")

        assert result.action_needed is False
        assert result.response == "Test response"

    @pytest.mark.asyncio
    async def test_agent_think_with_tool_use(self, mock_anthropic):
        """Test agent thinking with tool use."""
        from agents.base_agent import BaseAgent

        class TestAgent(BaseAgent):
            def get_system_prompt(self):
                return "Test prompt"

            def get_tools(self):
                return [{"name": "test_tool", "description": "A test tool"}]

            async def execute_tool(self, name, input_data):
                return MagicMock(success=True, output="Tool executed")

        # Mock response with tool_use
        mock_tool_use = MagicMock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.name = "test_tool"
        mock_tool_use.input = {"param": "value"}
        mock_tool_use.id = "tool_123"

        mock_response = MagicMock()
        mock_response.content = [mock_tool_use]
        mock_anthropic.return_value.messages.create = AsyncMock(return_value=mock_response)

        agent = TestAgent("Test", "claude-sonnet-4-20250514")
        result = await agent.think("Use a tool")

        assert result.action_needed is True
        assert result.action["tool"] == "test_tool"


# Run with: pytest tests/unit/test_agents.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
