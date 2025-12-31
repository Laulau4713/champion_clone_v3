"""
Integration Tests for Audit API.

Tests:
- GET /audit/session/{session_id}
- GET /audit/progress
- GET /audit/weekly-digest
- GET /audit/next-action
- GET /audit/compare-champion/{champion_id}

Security tests:
- Authentication required
- Authorization (own sessions only)
- Input validation
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, Champion, VoiceTrainingSession, VoiceTrainingMessage, Skill
from agents.audit_agent.schemas import PerformanceLevel


# ============================================
# Fixtures
# ============================================

@pytest.fixture
async def test_skill(db_session: AsyncSession) -> Skill:
    """Create a test skill."""
    skill = Skill(
        name="Ecoute Active",
        slug="ecoute_active",
        level="intermediate",
        description="Skill d'ecoute active",
        order=1
    )
    db_session.add(skill)
    await db_session.commit()
    await db_session.refresh(skill)
    return skill


@pytest.fixture
async def voice_session(
    db_session: AsyncSession,
    test_user: User,
    test_skill: Skill
) -> VoiceTrainingSession:
    """Create a voice training session for testing."""
    session = VoiceTrainingSession(
        user_id=test_user.id,
        skill_id=test_skill.id,
        level="intermediate",
        scenario_json={"context": "B2B cold call", "prospect_type": "PME"},
        starting_gauge=50,
        current_gauge=75,
        gauge_history=[50, 55, 60, 70, 75],
        positive_actions=4,
        negative_actions=1,
        hidden_objections=["price", "timing"],
        discovered_objections=["price"],
        triggered_events=[],
        reversal_triggered=False,
        converted=True,
        status="completed",
        score=78.5,
        completed_at=datetime.utcnow()
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    # Add messages
    messages = [
        VoiceTrainingMessage(
            session_id=session.id,
            role="prospect",
            text="Bonjour, je suis presse.",
            detected_patterns=[],
            gauge_impact=0
        ),
        VoiceTrainingMessage(
            session_id=session.id,
            role="user",
            text="Je comprends, je serai bref. J'ai une solution qui pourrait vous faire gagner du temps.",
            detected_patterns=["empathy", "value_proposition"],
            gauge_impact=10
        ),
    ]
    for msg in messages:
        db_session.add(msg)

    await db_session.commit()
    return session


@pytest.fixture
async def other_user_session(
    db_session: AsyncSession,
    test_skill: Skill
) -> VoiceTrainingSession:
    """Create a session belonging to another user."""
    other_user = User(
        email="other@example.com",
        hashed_password="hashed",
        full_name="Other User",
        is_active=True
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    session = VoiceTrainingSession(
        user_id=other_user.id,
        skill_id=test_skill.id,
        level="beginner",
        scenario_json={"context": "Test"},
        starting_gauge=50,
        current_gauge=60,
        status="completed"
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def champion_with_patterns(db_session: AsyncSession) -> Champion:
    """Create a champion with patterns for comparison."""
    champion = Champion(
        name="Top Seller",
        description="Expert B2B sales",
        status="ready",
        patterns_json={
            "openings": ["Bonjour, comment allez-vous?"],
            "objection_handlers": [
                {"objection": "trop cher", "response": "Je comprends"}
            ],
            "closes": ["Qu'en pensez-vous?"],
            "key_phrases": ["Je comprends", "Excellent point"],
            "tone_style": "professionnel et empathique",
            "success_patterns": ["empathy", "active_listening", "mirroring"]
        }
    )
    db_session.add(champion)
    await db_session.commit()
    await db_session.refresh(champion)
    return champion


# ============================================
# Mock Helpers
# ============================================

def mock_audit_response():
    """Return a mock Claude API response for audit."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = '''{
        "overall_score": 78.5,
        "performance_level": "bon",
        "skill_scores": {"empathy": 85, "listening": 75},
        "behavioral_analysis": {"silences": "good", "reactivity": "excellent"},
        "emotional_intelligence_score": 80,
        "adaptability_score": 75,
        "champion_alignment": 65,
        "champion_gaps": ["closing technique"],
        "turning_points": [{"moment": "objection handling", "gauge_change": 10, "reason": "good empathy"}],
        "missed_opportunities": [],
        "excellent_moments": [{"moment": "value proposition", "why_excellent": "concise and relevant"}],
        "summary": "Bonne session avec de l'empathie",
        "top_strength": "Empathie naturelle",
        "top_weakness": "Technique de closing",
        "immediate_action": "Pratiquer le closing",
        "audit_confidence": 0.85
    }'''
    return mock_response


def mock_progress_response():
    """Return a mock Claude API response for progress report."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = '''{
        "overall_trend": "improving",
        "score_evolution": [{"date": "2025-12-25", "score": 70}, {"date": "2025-12-30", "score": 78}],
        "avg_score": 74.0,
        "best_session_id": 1,
        "worst_session_id": 1,
        "skill_progression": {"ecoute_active": {"start_score": 60, "end_score": 78, "trend": "improving"}},
        "skills_mastered": [],
        "skills_struggling": [],
        "consistent_strengths": ["empathy"],
        "persistent_weaknesses": ["closing"],
        "improvement_velocity": 2.5,
        "focus_areas": ["closing", "objection handling"],
        "recommended_path": [{"skill": "closing", "action": "practice", "priority": 1}],
        "percentile_rank": 65,
        "comparison_to_average": 10
    }'''
    return mock_response


def mock_digest_response():
    """Return a mock Claude API response for weekly digest."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = '''{
        "sessions_completed": 3,
        "total_training_minutes": 45,
        "avg_score": 75.0,
        "best_moment": "Excellent handling of price objection",
        "score_vs_last_week": 5.0,
        "new_skills_unlocked": [],
        "achievements": ["3_sessions_week"],
        "weekly_goal": "Complete 5 sessions next week",
        "daily_tips": ["Monday: Focus on opening", "Tuesday: Practice empathy"],
        "motivational_message": "Great progress this week!",
        "streak_days": 5
    }'''
    return mock_response


def mock_comparison_response():
    """Return a mock Claude API response for champion comparison."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = '''{
        "overall_similarity": 65,
        "technique_similarity": 70,
        "tone_similarity": 60,
        "timing_similarity": 55,
        "missing_techniques": [{"technique": "mirroring", "importance": "high", "how_to_implement": "Repeat key words"}],
        "overused_techniques": ["filler_words"],
        "techniques_to_adopt": [{"technique": "mirroring", "priority": 1, "example": "I hear you say..."}],
        "habits_to_break": ["interrupting"]
    }'''
    return mock_response


# ============================================
# Authentication Tests
# ============================================

class TestAuditAuthentication:
    """Tests for authentication requirements."""

    @pytest.mark.asyncio
    async def test_audit_session_requires_auth(self, client: AsyncClient):
        """Should require authentication for session audit."""
        response = await client.get("/audit/session/1")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_progress_requires_auth(self, client: AsyncClient):
        """Should require authentication for progress report."""
        response = await client.get("/audit/progress")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_weekly_digest_requires_auth(self, client: AsyncClient):
        """Should require authentication for weekly digest."""
        response = await client.get("/audit/weekly-digest")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_next_action_requires_auth(self, client: AsyncClient):
        """Should require authentication for next action."""
        response = await client.get("/audit/next-action")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_compare_champion_requires_auth(self, client: AsyncClient):
        """Should require authentication for champion comparison."""
        response = await client.get("/audit/compare-champion/1")
        assert response.status_code == 401


# ============================================
# Authorization Tests
# ============================================

class TestAuditAuthorization:
    """Tests for authorization (access control)."""

    @pytest.mark.asyncio
    async def test_cannot_audit_other_users_session(
        self,
        client: AsyncClient,
        auth_headers: dict,
        other_user_session: VoiceTrainingSession
    ):
        """Should deny access to other user's session."""
        response = await client.get(
            f"/audit/session/{other_user_session.id}",
            headers=auth_headers
        )
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_admin_can_audit_any_session(
        self,
        client: AsyncClient,
        admin_auth_headers: dict,
        other_user_session: VoiceTrainingSession
    ):
        """Admin should access any session."""
        with patch('agents.audit_agent.agent.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_audit_response())
            mock_anthropic.return_value = mock_client

            response = await client.get(
                f"/audit/session/{other_user_session.id}",
                headers=admin_auth_headers
            )
            # Should not be 403
            assert response.status_code != 403


# ============================================
# Session Audit Tests
# ============================================

class TestSessionAudit:
    """Tests for GET /audit/session/{session_id}."""

    @pytest.mark.asyncio
    async def test_audit_session_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Should return 404 for non-existent session."""
        response = await client.get("/audit/session/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_audit_session_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        voice_session: VoiceTrainingSession
    ):
        """Should return audit for valid session."""
        with patch('agents.audit_agent.agent.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_audit_response())
            mock_anthropic.return_value = mock_client

            response = await client.get(
                f"/audit/session/{voice_session.id}",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == voice_session.id
            assert "overall_score" in data
            assert "performance_level" in data
            assert "summary" in data


# ============================================
# Progress Report Tests
# ============================================

class TestProgressReport:
    """Tests for GET /audit/progress."""

    @pytest.mark.asyncio
    async def test_progress_invalid_days_too_low(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Should reject days < 1."""
        response = await client.get("/audit/progress?days=0", headers=auth_headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_progress_invalid_days_too_high(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Should reject days > 90."""
        response = await client.get("/audit/progress?days=91", headers=auth_headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_progress_no_sessions(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Should return message when no sessions found."""
        response = await client.get("/audit/progress?days=7", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["sessions_analyzed"] == 0
        assert data["overall_trend"] == "no_data"

    @pytest.mark.asyncio
    async def test_progress_with_sessions(
        self,
        client: AsyncClient,
        auth_headers: dict,
        voice_session: VoiceTrainingSession
    ):
        """Should return progress report with sessions."""
        with patch('agents.audit_agent.agent.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_progress_response())
            mock_anthropic.return_value = mock_client

            response = await client.get("/audit/progress?days=7", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert "overall_trend" in data
            assert "avg_score" in data


# ============================================
# Weekly Digest Tests
# ============================================

class TestWeeklyDigest:
    """Tests for GET /audit/weekly-digest."""

    @pytest.mark.asyncio
    async def test_digest_no_activity(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Should return default digest for no activity."""
        # When no sessions exist, the endpoint returns a default response
        # without calling Claude (caught ValueError in router)
        with patch('api.routers.audit.AuditAgent') as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.generate_weekly_digest = AsyncMock(
                side_effect=ValueError("No sessions")
            )
            mock_agent_class.return_value = mock_agent

            response = await client.get("/audit/weekly-digest", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert data["sessions_completed"] == 0
            assert "daily_tips" in data

    @pytest.mark.asyncio
    async def test_digest_with_activity(
        self,
        client: AsyncClient,
        auth_headers: dict,
        voice_session: VoiceTrainingSession
    ):
        """Should return personalized digest with activity."""
        with patch('agents.audit_agent.agent.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            # First call for progress report, second for digest
            mock_client.messages.create = AsyncMock(side_effect=[
                mock_progress_response(),
                mock_digest_response()
            ])
            mock_anthropic.return_value = mock_client

            response = await client.get("/audit/weekly-digest", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert "motivational_message" in data


# ============================================
# Next Action Tests
# ============================================

class TestNextAction:
    """Tests for GET /audit/next-action."""

    @pytest.mark.asyncio
    async def test_next_action_new_user(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Should recommend first course for new user."""
        response = await client.get("/audit/next-action", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "action" in data
        assert "skill_slug" in data
        assert "reason" in data


# ============================================
# Champion Comparison Tests
# ============================================

class TestChampionComparison:
    """Tests for GET /audit/compare-champion/{champion_id}."""

    @pytest.mark.asyncio
    async def test_compare_champion_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Should return 404 for non-existent champion."""
        response = await client.get("/audit/compare-champion/99999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_compare_champion_no_patterns(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """Should return 400 for champion without patterns."""
        champion = Champion(
            name="New Champion",
            description="Not analyzed",
            status="uploaded",
            patterns_json=None
        )
        db_session.add(champion)
        await db_session.commit()
        await db_session.refresh(champion)

        response = await client.get(
            f"/audit/compare-champion/{champion.id}",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "no extracted patterns" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_compare_champion_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        champion_with_patterns: Champion,
        voice_session: VoiceTrainingSession
    ):
        """Should return comparison with valid champion."""
        with patch('agents.audit_agent.agent.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_comparison_response())
            mock_anthropic.return_value = mock_client

            response = await client.get(
                f"/audit/compare-champion/{champion_with_patterns.id}",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["champion_id"] == champion_with_patterns.id
            assert "overall_similarity" in data
            assert "missing_techniques" in data


# ============================================
# Input Validation Tests (Security)
# ============================================

class TestInputValidation:
    """Tests for input validation and security."""

    @pytest.mark.asyncio
    async def test_session_id_must_be_integer(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Should reject non-integer session_id."""
        response = await client.get("/audit/session/abc", headers=auth_headers)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_session_id_must_be_positive(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Should handle negative session_id."""
        response = await client.get("/audit/session/-1", headers=auth_headers)
        # Either 422 (validation) or 404 (not found)
        assert response.status_code in [404, 422]

    @pytest.mark.asyncio
    async def test_days_must_be_integer(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Should reject non-integer days parameter."""
        response = await client.get("/audit/progress?days=abc", headers=auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_champion_id_must_be_integer(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Should reject non-integer champion_id."""
        response = await client.get("/audit/compare-champion/abc", headers=auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_sql_injection_in_session_id(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Should not be vulnerable to SQL injection."""
        response = await client.get(
            "/audit/session/1; DROP TABLE users;--",
            headers=auth_headers
        )
        # Should be rejected as invalid input
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_large_days_value(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Should handle extremely large days value."""
        response = await client.get("/audit/progress?days=999999", headers=auth_headers)
        assert response.status_code == 400


# ============================================
# Error Handling Tests
# ============================================

class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_api_error_handling(
        self,
        client: AsyncClient,
        auth_headers: dict,
        voice_session: VoiceTrainingSession
    ):
        """Should handle API errors gracefully."""
        with patch('agents.audit_agent.agent.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(
                side_effect=Exception("API Error")
            )
            mock_anthropic.return_value = mock_client

            response = await client.get(
                f"/audit/session/{voice_session.id}",
                headers=auth_headers
            )

            assert response.status_code == 500
            assert "Audit failed" in response.json()["detail"]
