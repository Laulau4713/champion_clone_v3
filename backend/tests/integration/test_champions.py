"""
Integration Tests for Champions API.

Tests champion endpoints:
- GET /champions
- GET /champions/{id}
- DELETE /champions/{id}
- POST /upload
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, Champion


# ============================================
# Fixtures
# ============================================

@pytest.fixture
async def test_champion(db_session: AsyncSession) -> Champion:
    """Create a test champion in the database."""
    champion = Champion(
        name="Test Champion",
        description="A test champion for sales training",
        status="uploaded"
    )
    db_session.add(champion)
    await db_session.commit()
    await db_session.refresh(champion)
    return champion


@pytest.fixture
async def ready_champion(db_session: AsyncSession) -> Champion:
    """Create a ready champion with patterns."""
    champion = Champion(
        name="Ready Champion",
        description="Champion with patterns",
        transcript="Bonjour, je suis commercial...",
        patterns_json={
            "openings": ["Bonjour"],
            "closes": ["Merci"],
            "objection_handlers": []
        },
        status="ready"
    )
    db_session.add(champion)
    await db_session.commit()
    await db_session.refresh(champion)
    return champion


# ============================================
# List Champions Tests
# ============================================

class TestListChampions:
    """Tests for GET /champions endpoint."""

    @pytest.mark.asyncio
    async def test_list_champions_empty(self, client: AsyncClient):
        """Should return empty list when no champions exist."""
        response = await client.get("/champions")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_champions_with_data(
        self, client: AsyncClient, test_champion: Champion
    ):
        """Should return list of champions."""
        response = await client.get("/champions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Champion"
        assert data[0]["status"] == "uploaded"

    @pytest.mark.asyncio
    async def test_list_champions_filter_by_status(
        self, client: AsyncClient, test_champion: Champion, ready_champion: Champion
    ):
        """Should filter champions by status."""
        # Filter ready only
        response = await client.get("/champions?status=ready")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Ready Champion"

    @pytest.mark.asyncio
    async def test_list_champions_filter_no_results(
        self, client: AsyncClient, test_champion: Champion
    ):
        """Should return empty list when filter matches nothing."""
        response = await client.get("/champions?status=nonexistent")

        assert response.status_code == 200
        assert response.json() == []


# ============================================
# Get Champion Tests
# ============================================

class TestGetChampion:
    """Tests for GET /champions/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_champion_success(
        self, client: AsyncClient, test_champion: Champion
    ):
        """Should return champion details."""
        response = await client.get(f"/champions/{test_champion.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_champion.id
        assert data["name"] == "Test Champion"
        assert data["status"] == "uploaded"
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_champion_with_patterns(
        self, client: AsyncClient, ready_champion: Champion
    ):
        """Should return champion with patterns."""
        response = await client.get(f"/champions/{ready_champion.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["patterns_json"] is not None
        assert "openings" in data["patterns_json"]

    @pytest.mark.asyncio
    async def test_get_champion_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent champion."""
        response = await client.get("/champions/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ============================================
# Delete Champion Tests
# ============================================

class TestDeleteChampion:
    """Tests for DELETE /champions/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_champion_success(
        self, client: AsyncClient, test_champion: Champion, auth_headers: dict
    ):
        """Should delete champion successfully."""
        response = await client.delete(
            f"/champions/{test_champion.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify deleted
        get_response = await client.get(f"/champions/{test_champion.id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_champion_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Should return 404 for non-existent champion."""
        response = await client.delete(
            "/champions/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_champion_unauthorized(
        self, client: AsyncClient, test_champion: Champion
    ):
        """Should require authentication to delete."""
        response = await client.delete(f"/champions/{test_champion.id}")

        assert response.status_code == 401


# ============================================
# Upload Tests
# ============================================

class TestUploadChampion:
    """Tests for POST /upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_without_auth_fails(self, client: AsyncClient):
        """Should reject upload without authentication."""
        response = await client.post(
            "/upload",
            data={"name": "Test Champion"},
            files={"video": ("test.mp4", b"fake video content", "video/mp4")}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_invalid_extension(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Should reject invalid file extension."""
        response = await client.post(
            "/upload",
            data={"name": "Test"},
            files={"video": ("test.txt", b"not a video", "text/plain")},
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "extension" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_invalid_video_content(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Should reject file with wrong magic bytes."""
        response = await client.post(
            "/upload",
            data={"name": "Test"},
            files={"video": ("test.mp4", b"not real video data", "video/mp4")},
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_missing_name(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Should require name field."""
        # Create a fake MP4 with valid magic bytes
        fake_mp4 = b'\x00\x00\x00\x1cftypisom' + b'\x00' * 100

        response = await client.post(
            "/upload",
            files={"video": ("test.mp4", fake_mp4, "video/mp4")},
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error


# ============================================
# Video Validation Tests
# ============================================

class TestVideoValidation:
    """Tests for video file validation."""

    def test_validate_mp4_file(self):
        """Should validate MP4 files."""
        from api.routers.champions import validate_video_file

        # Valid MP4 magic bytes (ftyp at offset 4)
        mp4_bytes = b'\x00\x00\x00\x1cftypisom\x00\x00'

        assert validate_video_file(mp4_bytes) is True

    def test_validate_avi_file(self):
        """Should validate AVI files."""
        from api.routers.champions import validate_video_file

        # Valid AVI magic bytes
        avi_bytes = b'RIFF\x00\x00\x00\x00AVI LIST'

        assert validate_video_file(avi_bytes) is True

    def test_reject_invalid_file(self):
        """Should reject non-video files."""
        from api.routers.champions import validate_video_file

        invalid_bytes = b'not a video file'

        assert validate_video_file(invalid_bytes) is False

    def test_reject_short_file(self):
        """Should reject files too short to validate."""
        from api.routers.champions import validate_video_file

        short_bytes = b'short'

        assert validate_video_file(short_bytes) is False
