"""
Integration Tests for Training API.

Tests training endpoints:
- GET /scenarios/{champion_id}
- GET /training/sessions
- GET /training/sessions/{session_id}
- POST /training/start
- POST /training/respond
- POST /training/end
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import Champion, TrainingSession, User

# ============================================
# Fixtures
# ============================================


@pytest.fixture
async def ready_champion(db_session: AsyncSession) -> Champion:
    """Create a champion with patterns for training."""
    champion = Champion(
        name="Sales Champion",
        description="Expert in B2B sales",
        transcript="Bonjour, je suis commercial...",
        patterns_json={
            "openings": ["Bonjour, comment allez-vous?"],
            "objection_handlers": [{"objection": "trop cher", "response": "Je comprends votre préoccupation"}],
            "closes": ["Ça vous intéresse d'en discuter?"],
            "key_phrases": ["Je comprends"],
            "tone_style": "professionnel",
            "success_patterns": ["empathie", "écoute active"],
        },
        status="ready",
    )
    db_session.add(champion)
    await db_session.commit()
    await db_session.refresh(champion)
    return champion


@pytest.fixture
async def unanalyzed_champion(db_session: AsyncSession) -> Champion:
    """Create a champion without patterns."""
    champion = Champion(name="New Champion", description="Not yet analyzed", status="uploaded")
    db_session.add(champion)
    await db_session.commit()
    await db_session.refresh(champion)
    return champion


@pytest.fixture
async def training_session(db_session: AsyncSession, ready_champion: Champion, test_user: User) -> TrainingSession:
    """Create a training session."""
    session = TrainingSession(
        user_id=str(test_user.id),
        champion_id=ready_champion.id,
        scenario={"context": "Appel à froid B2B", "prospect_type": "Directeur commercial PME", "difficulty": "medium"},
        messages=[
            {
                "role": "champion",
                "content": "Bonjour, que puis-je faire pour vous?",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ],
        status="active",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def completed_session(db_session: AsyncSession, ready_champion: Champion, test_user: User) -> TrainingSession:
    """Create a completed training session."""
    session = TrainingSession(
        user_id=str(test_user.id),
        champion_id=ready_champion.id,
        scenario={"context": "Test", "difficulty": "easy"},
        messages=[{"role": "champion", "content": "Bonjour"}, {"role": "user", "content": "Bonjour", "score": 7}],
        status="completed",
        overall_score=7.5,
        feedback_summary="Bonne session",
        ended_at=datetime.utcnow(),
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


# ============================================
# Scenario Generation Tests
# ============================================


class TestScenarios:
    """Tests for GET /scenarios/{champion_id} endpoint."""

    @pytest.mark.asyncio
    async def test_generate_scenarios_champion_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent champion."""
        response = await client.get("/scenarios/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_generate_scenarios_champion_not_analyzed(self, client: AsyncClient, unanalyzed_champion: Champion):
        """Should return 400 for unanalyzed champion."""
        response = await client.get(f"/scenarios/{unanalyzed_champion.id}")

        assert response.status_code == 400
        assert "not analyzed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_generate_scenarios_success(self, client: AsyncClient, ready_champion: Champion):
        """Should generate scenarios for analyzed champion."""
        # Mock the pattern agent
        with patch("api.routers.training.pattern_extractor") as mock_extractor:
            mock_extractor.generate_scenarios = AsyncMock(
                return_value=[
                    {
                        "id": "sc1",
                        "context": "Appel à froid",
                        "prospect_type": "PME",
                        "challenge": "Obtenir un RDV",
                        "objectives": ["Créer le rapport"],
                        "difficulty": "medium",
                        "expected_patterns": ["opening"],
                    }
                ]
            )

            response = await client.get(f"/scenarios/{ready_champion.id}")

            assert response.status_code == 200
            data = response.json()
            assert data["champion_id"] == ready_champion.id
            assert len(data["scenarios"]) == 1

    @pytest.mark.asyncio
    async def test_generate_scenarios_custom_count(self, client: AsyncClient, ready_champion: Champion):
        """Should respect count parameter."""
        with patch("api.routers.training.pattern_extractor") as mock_extractor:
            mock_extractor.generate_scenarios = AsyncMock(
                return_value=[
                    {
                        "id": f"sc{i}",
                        "context": f"Scenario {i}",
                        "prospect_type": "PME",
                        "challenge": "Obtenir un RDV",
                        "objectives": ["Test"],
                        "difficulty": "medium",
                        "expected_patterns": [],
                    }
                    for i in range(5)
                ]
            )

            response = await client.get(f"/scenarios/{ready_champion.id}?count=5")

            assert response.status_code == 200
            mock_extractor.generate_scenarios.assert_called_once()


# ============================================
# List Sessions Tests
# ============================================


class TestListSessions:
    """Tests for GET /training/sessions endpoint."""

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, client: AsyncClient):
        """Should return empty list when no sessions exist."""
        response = await client.get("/training/sessions")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_sessions_with_data(self, client: AsyncClient, training_session: TrainingSession):
        """Should return list of sessions."""
        response = await client.get("/training/sessions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == training_session.id
        assert data[0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_list_sessions_filter_by_status(
        self, client: AsyncClient, training_session: TrainingSession, completed_session: TrainingSession
    ):
        """Should filter sessions by status."""
        response = await client.get("/training/sessions?status=completed")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_list_sessions_filter_by_champion(
        self, client: AsyncClient, training_session: TrainingSession, ready_champion: Champion
    ):
        """Should filter sessions by champion."""
        response = await client.get(f"/training/sessions?champion_id={ready_champion.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(s["champion_id"] == ready_champion.id for s in data)

    @pytest.mark.asyncio
    async def test_list_sessions_filter_by_user(
        self, client: AsyncClient, training_session: TrainingSession, test_user: User
    ):
        """Should filter sessions by user_id."""
        response = await client.get(f"/training/sessions?user_id={test_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(s["user_id"] == str(test_user.id) for s in data)


# ============================================
# Get Session Tests
# ============================================


class TestGetSession:
    """Tests for GET /training/sessions/{session_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_session_success(self, client: AsyncClient, training_session: TrainingSession):
        """Should return session details."""
        response = await client.get(f"/training/sessions/{training_session.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == training_session.id
        assert data["status"] == "active"
        assert "messages" in data

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent session."""
        response = await client.get("/training/sessions/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_completed_session(self, client: AsyncClient, completed_session: TrainingSession):
        """Should return completed session with score."""
        response = await client.get(f"/training/sessions/{completed_session.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["overall_score"] == 7.5


# ============================================
# Start Session Tests
# ============================================


class TestStartSession:
    """Tests for POST /training/start endpoint."""

    @pytest.mark.asyncio
    async def test_start_session_unauthorized(self, client: AsyncClient):
        """Should require authentication."""
        response = await client.post("/training/start", params={"champion_id": 1, "scenario_index": 0})

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_start_session_champion_not_found(self, client: AsyncClient, auth_headers: dict):
        """Should return 404 for non-existent champion."""
        response = await client.post(
            "/training/start", params={"champion_id": 99999, "scenario_index": 0}, headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_start_session_champion_not_analyzed(
        self, client: AsyncClient, auth_headers: dict, unanalyzed_champion: Champion
    ):
        """Should return 400 for unanalyzed champion."""
        response = await client.post(
            "/training/start", params={"champion_id": unanalyzed_champion.id, "scenario_index": 0}, headers=auth_headers
        )

        assert response.status_code == 400
        assert "not analyzed" in response.json()["detail"].lower()


# ============================================
# End Session Tests
# ============================================


class TestEndSession:
    """Tests for POST /training/end endpoint."""

    @pytest.mark.asyncio
    async def test_end_session_unauthorized(self, client: AsyncClient):
        """Should require authentication."""
        response = await client.post("/training/end", params={"session_id": 1})

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_end_session_not_found(self, client: AsyncClient, auth_headers: dict):
        """Should return 404 for non-existent session."""
        response = await client.post("/training/end", params={"session_id": 99999}, headers=auth_headers)

        assert response.status_code == 404


# ============================================
# Respond in Session Tests
# ============================================


class TestRespondInSession:
    """Tests for POST /training/respond endpoint."""

    @pytest.mark.asyncio
    async def test_respond_unauthorized(self, client: AsyncClient):
        """Should require authentication."""
        response = await client.post("/training/respond", params={"session_id": 1, "user_response": "Hello"})

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_respond_session_not_found(self, client: AsyncClient, auth_headers: dict):
        """Should return 404 for non-existent session."""
        response = await client.post(
            "/training/respond", params={"session_id": 99999, "user_response": "Hello"}, headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_respond_session_not_active(
        self, client: AsyncClient, auth_headers: dict, completed_session: TrainingSession
    ):
        """Should return 400 for completed session."""
        response = await client.post(
            "/training/respond",
            params={"session_id": completed_session.id, "user_response": "Hello"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "not active" in response.json()["detail"].lower()
