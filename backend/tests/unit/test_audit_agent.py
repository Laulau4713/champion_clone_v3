"""
Unit Tests for AuditAgent.

Tests:
- JSON parsing
- Session context building
- Performance level calculation
- Object construction
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from agents.audit_agent.agent import AuditAgent
from agents.audit_agent.schemas import (
    SessionAudit, UserProgressReport, ChampionComparison,
    WeeklyDigest, PerformanceLevel
)


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def audit_agent(mock_db_session):
    """Create an AuditAgent with mocked dependencies."""
    with patch('agents.audit_agent.agent.anthropic.AsyncAnthropic'):
        agent = AuditAgent(mock_db_session)
        agent.client = MagicMock()
        return agent


@pytest.fixture
def mock_voice_session():
    """Create a mock VoiceTrainingSession."""
    session = MagicMock()
    session.id = 1
    session.user_id = 123
    session.skill_id = 1
    session.level = "intermediate"
    session.scenario_json = {"context": "Test scenario"}
    session.starting_gauge = 50
    session.current_gauge = 75
    session.gauge_history = [50, 55, 60, 75]
    session.positive_actions = 3
    session.negative_actions = 1
    session.hidden_objections = ["price"]
    session.discovered_objections = ["price"]
    session.triggered_events = []
    session.reversal_triggered = False
    session.converted = True
    session.created_at = datetime.utcnow() - timedelta(minutes=10)
    session.completed_at = datetime.utcnow()
    session.feedback_json = {}
    return session


@pytest.fixture
def mock_message():
    """Create a mock VoiceTrainingMessage."""
    msg = MagicMock()
    msg.role = "user"
    msg.text = "Bonjour, je comprends votre situation"
    msg.created_at = datetime.utcnow()
    msg.detected_patterns = ["empathy", "active_listening"]
    msg.gauge_impact = 5
    msg.behavioral_cues = ["positive_tone"]
    return msg


# ============================================
# JSON Parsing Tests
# ============================================

class TestJsonParsing:
    """Tests for _parse_json_response method."""

    def test_parse_clean_json(self, audit_agent):
        """Should parse clean JSON correctly."""
        text = '{"overall_score": 85, "summary": "Good session"}'
        result = audit_agent._parse_json_response(text)

        assert result["overall_score"] == 85
        assert result["summary"] == "Good session"

    def test_parse_json_with_markdown_blocks(self, audit_agent):
        """Should extract JSON from markdown code blocks."""
        text = '```json\n{"overall_score": 75}\n```'
        result = audit_agent._parse_json_response(text)

        assert result["overall_score"] == 75

    def test_parse_json_with_plain_markdown(self, audit_agent):
        """Should handle plain markdown blocks."""
        text = '```\n{"overall_score": 65}\n```'
        result = audit_agent._parse_json_response(text)

        assert result["overall_score"] == 65

    def test_parse_json_embedded_in_text(self, audit_agent):
        """Should extract JSON from surrounding text."""
        text = 'Here is the analysis:\n{"overall_score": 90}\nEnd of analysis.'
        result = audit_agent._parse_json_response(text)

        assert result["overall_score"] == 90

    def test_parse_invalid_json_raises_error(self, audit_agent):
        """Should raise ValueError for invalid JSON."""
        text = 'This is not valid JSON at all'

        with pytest.raises(ValueError) as exc_info:
            audit_agent._parse_json_response(text)

        assert "Could not parse JSON" in str(exc_info.value)

    def test_parse_json_with_nested_objects(self, audit_agent):
        """Should handle complex nested JSON."""
        text = '''{"overall_score": 80, "skill_scores": {"listening": 85, "empathy": 75}, "turning_points": [{"moment": "intro", "gauge_change": 10}]}'''
        result = audit_agent._parse_json_response(text)

        assert result["overall_score"] == 80
        assert result["skill_scores"]["listening"] == 85
        assert len(result["turning_points"]) == 1


# ============================================
# Session Context Building Tests
# ============================================

class TestSessionContextBuilding:
    """Tests for _build_session_context method."""

    def test_build_context_with_complete_session(self, audit_agent, mock_voice_session, mock_message):
        """Should build complete context from session and messages."""
        messages = [mock_message]

        context = audit_agent._build_session_context(mock_voice_session, messages)

        assert context["session_id"] == 1
        assert context["user_id"] == 123
        assert context["starting_gauge"] == 50
        assert context["final_gauge"] == 75
        assert context["converted"] is True
        assert len(context["transcript"]) == 1
        assert context["transcript"][0]["role"] == "user"

    def test_build_context_calculates_duration(self, audit_agent, mock_voice_session, mock_message):
        """Should calculate session duration correctly."""
        messages = [mock_message]

        context = audit_agent._build_session_context(mock_voice_session, messages)

        assert context["duration_minutes"] is not None
        assert context["duration_minutes"] >= 9  # ~10 minutes

    def test_build_context_without_completion_time(self, audit_agent, mock_voice_session, mock_message):
        """Should handle sessions without completion time."""
        mock_voice_session.completed_at = None
        messages = [mock_message]

        context = audit_agent._build_session_context(mock_voice_session, messages)

        assert context["duration_minutes"] is None

    def test_build_context_with_empty_messages(self, audit_agent, mock_voice_session):
        """Should handle empty message list."""
        context = audit_agent._build_session_context(mock_voice_session, [])

        assert context["transcript"] == []


# ============================================
# Performance Level Tests
# ============================================

class TestPerformanceLevelCalculation:
    """Tests for performance level determination in _build_session_audit."""

    def test_excellent_level_for_high_scores(self, audit_agent, mock_voice_session):
        """Should assign EXCELLENT for scores >= 85."""
        audit_data = {"overall_score": 90}

        audit = audit_agent._build_session_audit(mock_voice_session, audit_data)

        assert audit.performance_level == PerformanceLevel.EXCELLENT

    def test_bon_level_for_good_scores(self, audit_agent, mock_voice_session):
        """Should assign BON for scores 70-84."""
        audit_data = {"overall_score": 75}

        audit = audit_agent._build_session_audit(mock_voice_session, audit_data)

        assert audit.performance_level == PerformanceLevel.BON

    def test_moyen_level_for_average_scores(self, audit_agent, mock_voice_session):
        """Should assign MOYEN for scores 55-69."""
        audit_data = {"overall_score": 60}

        audit = audit_agent._build_session_audit(mock_voice_session, audit_data)

        assert audit.performance_level == PerformanceLevel.MOYEN

    def test_insuffisant_level_for_low_scores(self, audit_agent, mock_voice_session):
        """Should assign INSUFFISANT for scores 40-54."""
        audit_data = {"overall_score": 45}

        audit = audit_agent._build_session_audit(mock_voice_session, audit_data)

        assert audit.performance_level == PerformanceLevel.INSUFFISANT

    def test_critique_level_for_very_low_scores(self, audit_agent, mock_voice_session):
        """Should assign CRITIQUE for scores < 40."""
        audit_data = {"overall_score": 25}

        audit = audit_agent._build_session_audit(mock_voice_session, audit_data)

        assert audit.performance_level == PerformanceLevel.CRITIQUE

    def test_boundary_score_85(self, audit_agent, mock_voice_session):
        """Should assign EXCELLENT for exactly 85."""
        audit_data = {"overall_score": 85}

        audit = audit_agent._build_session_audit(mock_voice_session, audit_data)

        assert audit.performance_level == PerformanceLevel.EXCELLENT

    def test_boundary_score_70(self, audit_agent, mock_voice_session):
        """Should assign BON for exactly 70."""
        audit_data = {"overall_score": 70}

        audit = audit_agent._build_session_audit(mock_voice_session, audit_data)

        assert audit.performance_level == PerformanceLevel.BON


# ============================================
# Object Construction Tests
# ============================================

class TestObjectConstruction:
    """Tests for object construction methods."""

    def test_build_session_audit_with_full_data(self, audit_agent, mock_voice_session):
        """Should construct SessionAudit with all fields."""
        audit_data = {
            "overall_score": 80,
            "skill_scores": {"empathy": 85},
            "behavioral_analysis": {"silences": "good"},
            "emotional_intelligence_score": 75,
            "adaptability_score": 70,
            "champion_alignment": 60,
            "champion_gaps": ["closing"],
            "turning_points": [{"moment": "intro", "gauge_change": 5}],
            "missed_opportunities": [],
            "excellent_moments": [{"moment": "objection_handling", "why": "good empathy"}],
            "summary": "Good performance overall",
            "top_strength": "Active listening",
            "top_weakness": "Closing technique",
            "immediate_action": "Practice closing",
            "audit_confidence": 0.9,
        }

        audit = audit_agent._build_session_audit(mock_voice_session, audit_data)

        assert isinstance(audit, SessionAudit)
        assert audit.session_id == 1
        assert audit.overall_score == 80
        assert audit.emotional_intelligence_score == 75
        assert audit.top_strength == "Active listening"
        assert audit.audit_confidence == 0.9

    def test_build_session_audit_with_missing_fields(self, audit_agent, mock_voice_session):
        """Should use defaults for missing fields."""
        audit_data = {"overall_score": 50}

        audit = audit_agent._build_session_audit(mock_voice_session, audit_data)

        assert audit.skill_scores == {}
        assert audit.champion_gaps == []
        assert audit.summary == ""
        assert audit.audit_confidence == 0.8  # Default

    def test_build_champion_comparison(self, audit_agent):
        """Should construct ChampionComparison correctly."""
        data = {
            "overall_similarity": 65,
            "technique_similarity": 70,
            "tone_similarity": 60,
            "timing_similarity": 55,
            "missing_techniques": [{"technique": "closing", "importance": "high"}],
            "overused_techniques": ["filler_words"],
            "techniques_to_adopt": [{"technique": "mirroring", "priority": 1}],
            "habits_to_break": ["interrupting"],
        }

        comparison = audit_agent._build_champion_comparison(123, "champion_1", data)

        assert isinstance(comparison, ChampionComparison)
        assert comparison.user_id == 123
        assert comparison.champion_id == "champion_1"
        assert comparison.overall_similarity == 65
        assert len(comparison.missing_techniques) == 1

    def test_build_weekly_digest(self, audit_agent):
        """Should construct WeeklyDigest correctly."""
        data = {
            "sessions_completed": 5,
            "total_training_minutes": 45,
            "avg_score": 72.5,
            "best_moment": "Great objection handling on Thursday",
            "score_vs_last_week": 5.0,
            "new_skills_unlocked": ["closing"],
            "achievements": ["5_sessions_badge"],
            "weekly_goal": "Practice closing 3 times",
            "daily_tips": ["Monday: Focus on opening", "Tuesday: Practice empathy"],
            "motivational_message": "Keep up the good work!",
            "streak_days": 7,
        }

        digest = audit_agent._build_weekly_digest(123, data)

        assert isinstance(digest, WeeklyDigest)
        assert digest.user_id == 123
        assert digest.sessions_completed == 5
        assert digest.streak_days == 7
        assert len(digest.daily_tips) == 2


# ============================================
# Async Method Tests (with mocked API)
# ============================================

class TestAsyncMethods:
    """Tests for async methods with mocked Anthropic API."""

    @pytest.mark.asyncio
    async def test_audit_session_not_found(self, audit_agent, mock_db_session):
        """Should raise ValueError for non-existent session."""
        mock_db_session.get.return_value = None

        with pytest.raises(ValueError) as exc_info:
            await audit_agent.audit_session(999)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_progress_report_no_sessions(self, audit_agent, mock_db_session):
        """Should raise ValueError when no sessions found."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(ValueError) as exc_info:
            await audit_agent.generate_progress_report(123, days=7)

        assert "No completed sessions" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_weekly_digest_user_not_found(self, audit_agent, mock_db_session):
        """Should raise ValueError for non-existent user."""
        mock_db_session.get.return_value = None

        with pytest.raises(ValueError) as exc_info:
            await audit_agent.generate_weekly_digest(999)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_next_recommendation_new_user(self, audit_agent, mock_db_session):
        """Should return course recommendation for new user."""
        mock_db_session.scalar.return_value = None

        result = await audit_agent.get_next_recommendation(123)

        assert result["action"] == "course"
        assert result["skill_slug"] == "ecoute_active"
        assert "estimated_impact" in result

    @pytest.mark.asyncio
    async def test_get_next_recommendation_with_progress(self, audit_agent, mock_db_session):
        """Should analyze progress and recommend next action."""
        # Mock user progress
        mock_progress = MagicMock()
        mock_progress.id = 1
        mock_db_session.scalar.return_value = mock_progress

        # Mock skills progress
        mock_skill_progress = MagicMock()
        mock_skill_progress.is_validated = False
        mock_skill_progress.best_score = 60
        mock_skill_progress.quiz_passed = True
        mock_skill_progress.skill_id = 1
        mock_skill_progress.skill = MagicMock()
        mock_skill_progress.skill.slug = "empathy"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_skill_progress]
        mock_db_session.execute.return_value = mock_result

        # Mock skill lookup
        mock_skill = MagicMock()
        mock_skill.slug = "empathy"
        mock_db_session.get.return_value = mock_skill

        result = await audit_agent.get_next_recommendation(123)

        assert result["action"] == "training"
        assert "empathy" in result["skill_slug"]
