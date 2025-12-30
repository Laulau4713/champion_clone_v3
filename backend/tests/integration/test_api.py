"""
Integration Tests for API Endpoints.

Tests full request/response cycle:
- Auth endpoints (register, login, me, refresh, logout)
- Champion endpoints (list, upload without auth)
"""

import pytest
from httpx import AsyncClient

from models import User


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self, client: AsyncClient):
        """Health endpoint should return healthy status."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestAuthRegister:
    """Tests for /auth/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, valid_user_data: dict):
        """Should register a new user successfully."""
        response = await client.post("/auth/register", json=valid_user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == valid_user_data["email"]
        assert data["full_name"] == valid_user_data["full_name"]
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_weak_password_fails(
        self, client: AsyncClient, weak_password_data: dict
    ):
        """Should reject weak password."""
        response = await client.post("/auth/register", json=weak_password_data)

        assert response.status_code == 400
        data = response.json()
        assert "ValidationError" in str(data)

    @pytest.mark.asyncio
    async def test_register_duplicate_email_fails(
        self, client: AsyncClient, test_user: User
    ):
        """Should reject duplicate email."""
        response = await client.post("/auth/register", json={
            "email": test_user.email,
            "password": "ValidPass123$",
            "full_name": "Duplicate"
        })

        assert response.status_code == 409
        data = response.json()
        assert "Conflict" in str(data)


class TestAuthLogin:
    """Tests for /auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Should login successfully with correct credentials."""
        response = await client.post("/auth/login", json={
            "email": test_user.email,
            "password": "TestPass123$"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_login_wrong_password_fails(
        self, client: AsyncClient, test_user: User
    ):
        """Should reject incorrect password."""
        response = await client.post("/auth/login", json={
            "email": test_user.email,
            "password": "WrongPassword123$"
        })

        assert response.status_code == 401
        data = response.json()
        assert "Unauthorized" in str(data)

    @pytest.mark.asyncio
    async def test_login_nonexistent_email_fails(self, client: AsyncClient):
        """Should reject non-existent email."""
        response = await client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "TestPass123$"
        })

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_user_fails(
        self, client: AsyncClient, inactive_user: User
    ):
        """Should reject inactive user."""
        response = await client.post("/auth/login", json={
            "email": inactive_user.email,
            "password": "TestPass123$"
        })

        assert response.status_code == 401
        data = response.json()
        assert "inactive" in str(data).lower()


class TestAuthMe:
    """Tests for /auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_me_with_valid_token(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """Should return current user with valid token."""
        response = await client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id

    @pytest.mark.asyncio
    async def test_me_without_token_fails(self, client: AsyncClient):
        """Should reject request without token."""
        response = await client.get("/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_invalid_token_fails(self, client: AsyncClient):
        """Should reject invalid token."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401


class TestAuthRefresh:
    """Tests for /auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_with_valid_token(
        self, client: AsyncClient, test_user: User
    ):
        """Should refresh access token with valid refresh token."""
        # First login to get refresh token
        login_response = await client.post("/auth/login", json={
            "email": test_user.email,
            "password": "TestPass123$"
        })
        refresh_token = login_response.json()["refresh_token"]

        # Then refresh
        response = await client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token_fails(self, client: AsyncClient):
        """Should reject invalid refresh token."""
        response = await client.post("/auth/refresh", json={
            "refresh_token": "invalid.refresh.token"
        })

        assert response.status_code == 401


class TestAuthLogout:
    """Tests for /auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient, test_user: User):
        """Should successfully logout and revoke refresh token."""
        # First login
        login_response = await client.post("/auth/login", json={
            "email": test_user.email,
            "password": "TestPass123$"
        })
        tokens = login_response.json()

        # Then logout
        response = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
            json={"refresh_token": tokens["refresh_token"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"

        # Verify refresh token is revoked
        refresh_response = await client.post("/auth/refresh", json={
            "refresh_token": tokens["refresh_token"]
        })
        assert refresh_response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_without_auth_fails(self, client: AsyncClient):
        """Should reject logout without authentication."""
        response = await client.post("/auth/logout", json={
            "refresh_token": "some.token.here"
        })
        assert response.status_code == 401


class TestAuthLogoutAll:
    """Tests for /auth/logout-all endpoint."""

    @pytest.mark.asyncio
    async def test_logout_all_success(self, client: AsyncClient, test_user: User):
        """Should logout from all devices."""
        # Login twice to create multiple tokens
        login1 = await client.post("/auth/login", json={
            "email": test_user.email,
            "password": "TestPass123$"
        })
        tokens1 = login1.json()

        login2 = await client.post("/auth/login", json={
            "email": test_user.email,
            "password": "TestPass123$"
        })
        tokens2 = login2.json()

        # Logout all using first token
        response = await client.post(
            "/auth/logout-all",
            headers={"Authorization": f"Bearer {tokens1['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "Successfully logged out from all devices" in data["message"]

        # Verify both refresh tokens are revoked
        refresh1 = await client.post("/auth/refresh", json={
            "refresh_token": tokens1["refresh_token"]
        })
        assert refresh1.status_code == 401

        refresh2 = await client.post("/auth/refresh", json={
            "refresh_token": tokens2["refresh_token"]
        })
        assert refresh2.status_code == 401


class TestChampionEndpoints:
    """Tests for champion endpoints."""

    @pytest.mark.asyncio
    async def test_list_champions_empty(self, client: AsyncClient):
        """Should return empty list when no champions exist."""
        response = await client.get("/champions")

        assert response.status_code == 200
        assert response.json() == []

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
    async def test_get_champion_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent champion."""
        response = await client.get("/champions/99999")

        assert response.status_code == 404
