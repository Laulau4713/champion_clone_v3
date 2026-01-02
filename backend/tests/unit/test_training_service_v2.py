"""
Unit Tests for TrainingServiceV2.

Tests:
- ProspectResponseV2 dataclass
- Session creation
- User message processing
- Session ending and evaluation
- Fallback responses
- Tips generation
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domain.exceptions import (
    NotFoundError,
    SessionNotActiveError,
    SessionNotFoundError,
    ValidationError,
)
from services.training_service_v2 import ProspectResponseV2, TrainingServiceV2

# ============================================
# ProspectResponseV2 Tests
# ============================================


class TestProspectResponseV2:
    """Tests for ProspectResponseV2 dataclass."""

    def test_to_dict(self):
        """Should convert to dictionary correctly."""
        response = ProspectResponseV2(
            text="Test response",
            audio_base64="base64audio",
            mood="neutral",
            jauge=55,
            jauge_delta=5,
            behavioral_cue="(soupir)",
            is_event=False,
            event_type=None,
            feedback={"tips": ["tip1"]},
            conversion_possible=False,
        )
        result = response.to_dict()

        assert result["text"] == "Test response"
        assert result["audio_base64"] == "base64audio"
        assert result["mood"] == "neutral"
        assert result["jauge"] == 55
        assert result["jauge_delta"] == 5
        assert result["behavioral_cue"] == "(soupir)"
        assert result["is_event"] is False
        assert result["event_type"] is None
        assert result["feedback"] == {"tips": ["tip1"]}
        assert result["conversion_possible"] is False

    def test_hidden_jauge_values(self):
        """Should support hidden jauge values."""
        response = ProspectResponseV2(
            text="Response",
            audio_base64=None,
            mood="skeptical",
            jauge=-1,  # Hidden
            jauge_delta=0,  # Hidden
            behavioral_cue=None,
            is_event=False,
            event_type=None,
            feedback=None,
            conversion_possible=True,
        )

        assert response.jauge == -1
        assert response.jauge_delta == 0

    def test_event_response(self):
        """Should support event responses."""
        response = ProspectResponseV2(
            text="Event response",
            audio_base64=None,
            mood="hostile",
            jauge=30,
            jauge_delta=-20,
            behavioral_cue=None,
            is_event=True,
            event_type="phone_ring",
            feedback=None,
            conversion_possible=False,
        )

        assert response.is_event is True
        assert response.event_type == "phone_ring"


# ============================================
# TrainingServiceV2 Initialization Tests
# ============================================


class TestTrainingServiceV2Init:
    """Tests for TrainingServiceV2 initialization."""

    def test_init_with_api_key(self):
        """Should initialize Claude client with API key."""
        mock_db = MagicMock()

        with (
            patch("services.training_service_v2.ANTHROPIC_AVAILABLE", True),
            patch("services.training_service_v2.settings") as mock_settings,
            patch("services.training_service_v2.anthropic") as mock_anthropic,
        ):
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            service = TrainingServiceV2(mock_db)
            mock_anthropic.AsyncAnthropic.assert_called_once_with(api_key="test-key")
            assert service.db == mock_db

    def test_init_without_api_key(self):
        """Should handle missing API key gracefully."""
        mock_db = MagicMock()

        with (
            patch("services.training_service_v2.ANTHROPIC_AVAILABLE", True),
            patch("services.training_service_v2.settings") as mock_settings,
        ):
            mock_settings.ANTHROPIC_API_KEY = None
            service = TrainingServiceV2(mock_db)
            assert service.claude is None

    def test_init_without_anthropic_module(self):
        """Should handle missing anthropic module."""
        mock_db = MagicMock()

        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            assert service.claude is None


# ============================================
# Fallback Response Tests
# ============================================


class TestFallbackResponses:
    """Tests for fallback responses."""

    def test_hostile_fallback(self):
        """Should return hostile fallback."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            response = service._get_fallback_response("hostile")
            assert "temps" in response.lower()

    def test_aggressive_fallback(self):
        """Should return aggressive fallback."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            response = service._get_fallback_response("aggressive")
            assert "convaincu" in response.lower()

    def test_skeptical_fallback(self):
        """Should return skeptical fallback."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            response = service._get_fallback_response("skeptical")
            assert "concr" in response.lower()

    def test_resistant_fallback(self):
        """Should return resistant fallback."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            response = service._get_fallback_response("resistant")
            assert "sais pas" in response.lower()

    def test_neutral_fallback(self):
        """Should return neutral fallback."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            response = service._get_fallback_response("neutral")
            assert "continuez" in response.lower()

    def test_interested_fallback(self):
        """Should return interested fallback."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            response = service._get_fallback_response("interested")
            assert "intéressant" in response.lower()

    def test_ready_to_buy_fallback(self):
        """Should return ready_to_buy fallback."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            response = service._get_fallback_response("ready_to_buy")
            assert "intéresse" in response.lower()

    def test_unknown_mood_fallback(self):
        """Should return default fallback for unknown mood."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            response = service._get_fallback_response("unknown_mood")
            assert "comprends" in response.lower()


# ============================================
# Tips Generation Tests
# ============================================


class TestTipsGeneration:
    """Tests for tips generation."""

    def test_tips_no_positive_patterns(self):
        """Should suggest reformulation when no positive patterns."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            patterns = {"positive": [], "negative": [], "indicators": {}}
            tips = service._generate_tips(patterns, "neutral")
            assert any("reformuler" in tip.lower() for tip in tips)

    def test_tips_too_many_hesitations(self):
        """Should warn about hesitations."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            patterns = {"positive": [], "negative": [], "indicators": {"hesitation_count": 5}}
            tips = service._generate_tips(patterns, "neutral")
            assert any("hésitations" in tip.lower() or "confiance" in tip.lower() for tip in tips)

    def test_tips_hostile_mood(self):
        """Should advise empathy for hostile mood."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            patterns = {"positive": [], "negative": [], "indicators": {}}
            tips = service._generate_tips(patterns, "hostile")
            assert any("empathie" in tip.lower() or "ferme" in tip.lower() for tip in tips)

    def test_tips_aggressive_mood(self):
        """Should advise empathy for aggressive mood."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            patterns = {"positive": [], "negative": [], "indicators": {}}
            tips = service._generate_tips(patterns, "aggressive")
            assert any("empathie" in tip.lower() or "ferme" in tip.lower() for tip in tips)

    def test_tips_skeptical_mood(self):
        """Should advise staying calm for skeptical mood."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            patterns = {"positive": [], "negative": [], "indicators": {}}
            tips = service._generate_tips(patterns, "skeptical")
            assert any("calme" in tip.lower() or "factuel" in tip.lower() for tip in tips)

    def test_tips_interested_mood(self):
        """Should encourage continuing for interested mood."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            patterns = {"positive": [], "negative": [], "indicators": {}}
            tips = service._generate_tips(patterns, "interested")
            assert any("travail" in tip.lower() or "lancée" in tip.lower() for tip in tips)

    def test_tips_ready_to_buy_mood(self):
        """Should suggest closing for ready_to_buy mood."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            patterns = {"positive": [], "negative": [], "indicators": {}}
            tips = service._generate_tips(patterns, "ready_to_buy")
            assert any("closing" in tip.lower() or "prêt" in tip.lower() for tip in tips)

    def test_tips_closed_question_spam(self):
        """Should advise open questions for closed question spam."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            patterns = {"positive": [], "negative": [{"action": "closed_question_spam"}], "indicators": {}}
            tips = service._generate_tips(patterns, "neutral")
            assert any("ouvertes" in tip.lower() for tip in tips)

    def test_tips_interruption(self):
        """Should advise letting prospect finish for interruption."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            patterns = {"positive": [], "negative": [{"action": "interruption"}], "indicators": {}}
            tips = service._generate_tips(patterns, "neutral")
            assert any("finir" in tip.lower() or "parler" in tip.lower() for tip in tips)

    def test_tips_max_three(self):
        """Should return max 3 tips."""
        mock_db = MagicMock()
        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            patterns = {
                "positive": [],
                "negative": [
                    {"action": "closed_question_spam"},
                    {"action": "interruption"},
                    {"action": "aggressive_closing"},
                    {"action": "defensive_reaction"},
                ],
                "indicators": {"hesitation_count": 5},
            }
            tips = service._generate_tips(patterns, "hostile")
            assert len(tips) <= 3


# ============================================
# Main Advice Tests
# ============================================


class TestMainAdvice:
    """Tests for main advice generation."""

    def test_excellent_score_advice(self):
        """Should give excellent advice for high score."""
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_session.conversion_blockers = []

        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            advice = service._get_main_advice(mock_session, 90)
            assert "excellent" in advice.lower() or "maîtrise" in advice.lower()

    def test_good_score_advice(self):
        """Should give good advice for decent score."""
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_session.conversion_blockers = []

        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            advice = service._get_main_advice(mock_session, 75)
            assert "bon" in advice.lower() or "continue" in advice.lower()

    def test_average_score_advice(self):
        """Should give improvement advice for average score."""
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_session.conversion_blockers = []

        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            advice = service._get_main_advice(mock_session, 55)
            assert "écoute" in advice.lower() or "progresse" in advice.lower()

    def test_low_score_with_blockers_advice(self):
        """Should warn about blockers for low score."""
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_session.conversion_blockers = ["lost_temper"]

        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            advice = service._get_main_advice(mock_session, 35)
            assert "calme" in advice.lower() or "erreurs" in advice.lower()

    def test_low_score_without_blockers_advice(self):
        """Should encourage practice for low score without blockers."""
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_session.conversion_blockers = []

        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            advice = service._get_main_advice(mock_session, 35)
            assert "pratiquer" in advice.lower() or "fondamentaux" in advice.lower()


# ============================================
# Session Creation Tests
# ============================================


class TestSessionCreation:
    """Tests for session creation."""

    @pytest.mark.asyncio
    async def test_create_session_skill_not_found(self):
        """Should raise error if skill not found."""
        mock_db = AsyncMock()
        mock_db.scalar = AsyncMock(return_value=None)
        mock_user = MagicMock()
        mock_user.id = 1

        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            with pytest.raises(NotFoundError) as exc_info:
                await service.create_session(mock_user, "nonexistent_skill")
            assert exc_info.value.resource == "Skill"
            assert exc_info.value.identifier == "nonexistent_skill"


# ============================================
# User Message Processing Tests
# ============================================


class TestUserMessageProcessing:
    """Tests for user message processing."""

    @pytest.mark.asyncio
    async def test_process_message_session_not_found(self):
        """Should raise error if session not found."""
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)
        mock_user = MagicMock()
        mock_user.id = 1

        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            with pytest.raises(SessionNotFoundError) as exc_info:
                await service.process_user_message(999, mock_user, text="Hello")
            assert exc_info.value.session_id == 999

    @pytest.mark.asyncio
    async def test_process_message_wrong_user(self):
        """Should raise error if session belongs to another user."""
        mock_session = MagicMock()
        mock_session.user_id = 999  # Different user
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=mock_session)

        mock_user = MagicMock()
        mock_user.id = 1

        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            with pytest.raises(SessionNotFoundError) as exc_info:
                await service.process_user_message(1, mock_user, text="Hello")
            assert exc_info.value.session_id == 1

    @pytest.mark.asyncio
    async def test_process_message_session_not_active(self):
        """Should raise error if session is not active."""
        mock_session = MagicMock()
        mock_session.user_id = 1
        mock_session.status = "completed"
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=mock_session)

        mock_user = MagicMock()
        mock_user.id = 1

        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            with pytest.raises(SessionNotActiveError) as exc_info:
                await service.process_user_message(1, mock_user, text="Hello")
            assert exc_info.value.session_id == 1
            assert exc_info.value.status == "completed"

    @pytest.mark.asyncio
    async def test_process_message_no_text_or_audio(self):
        """Should raise error if no text or audio provided."""
        mock_session = MagicMock()
        mock_session.user_id = 1
        mock_session.status = "active"
        mock_session.level = "easy"
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=mock_session)
        mock_db.scalar = AsyncMock(return_value=None)

        mock_user = MagicMock()
        mock_user.id = 1

        with (
            patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False),
            patch("services.training_service_v2.voice_service") as mock_voice,
        ):
            mock_voice.is_configured.return_value = {"whisper": False}
            service = TrainingServiceV2(mock_db)
            with pytest.raises(ValidationError, match="No text or audio"):
                await service.process_user_message(1, mock_user)


# ============================================
# Session Ending Tests
# ============================================


class TestSessionEnding:
    """Tests for session ending."""

    @pytest.mark.asyncio
    async def test_end_session_not_found(self):
        """Should raise error if session not found."""
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)
        mock_user = MagicMock()
        mock_user.id = 1

        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            with pytest.raises(SessionNotFoundError) as exc_info:
                await service.end_session(999, mock_user)
            assert exc_info.value.session_id == 999

    @pytest.mark.asyncio
    async def test_end_session_wrong_user(self):
        """Should raise error if session belongs to another user."""
        mock_session = MagicMock()
        mock_session.user_id = 999  # Different user
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=mock_session)

        mock_user = MagicMock()
        mock_user.id = 1

        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            with pytest.raises(SessionNotFoundError) as exc_info:
                await service.end_session(1, mock_user)
            assert exc_info.value.session_id == 1


# ============================================
# Get Session Tests
# ============================================


class TestGetSession:
    """Tests for getting session details."""

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        """Should return None if session not found."""
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)
        mock_user = MagicMock()
        mock_user.id = 1

        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            result = await service.get_session(999, mock_user)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_session_wrong_user(self):
        """Should return None if session belongs to another user."""
        mock_session = MagicMock()
        mock_session.user_id = 999  # Different user
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=mock_session)

        mock_user = MagicMock()
        mock_user.id = 1

        with patch("services.training_service_v2.ANTHROPIC_AVAILABLE", False):
            service = TrainingServiceV2(mock_db)
            result = await service.get_session(1, mock_user)
            assert result is None
