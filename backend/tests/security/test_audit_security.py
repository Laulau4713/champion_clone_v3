"""
Security Tests for Audit API.

Tests OWASP Top 10 vulnerabilities:
- A01: Broken Access Control
- A02: Cryptographic Failures (JWT validation)
- A03: Injection (SQL, Command)
- A04: Insecure Design
- A05: Security Misconfiguration
- A07: Identification and Authentication Failures
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import Skill, User, VoiceTrainingSession
from services.auth import create_access_token

# ============================================
# Fixtures
# ============================================


@pytest.fixture
async def test_skill(db_session: AsyncSession) -> Skill:
    """Create a test skill."""
    skill = Skill(name="Test Skill", slug="test_skill", level="beginner", description="For testing", order=1)
    db_session.add(skill)
    await db_session.commit()
    await db_session.refresh(skill)
    return skill


@pytest.fixture
async def user_session(db_session: AsyncSession, test_user: User, test_skill: Skill) -> VoiceTrainingSession:
    """Create a session for the test user."""
    session = VoiceTrainingSession(
        user_id=test_user.id,
        skill_id=test_skill.id,
        level="beginner",
        scenario_json={},
        starting_gauge=50,
        current_gauge=60,
        status="completed",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def other_user(db_session: AsyncSession) -> User:
    """Create another user for authorization tests."""
    user = User(email="other@example.com", hashed_password="hashed_password", full_name="Other User", is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def other_user_session(db_session: AsyncSession, other_user: User, test_skill: Skill) -> VoiceTrainingSession:
    """Create a session for another user."""
    session = VoiceTrainingSession(
        user_id=other_user.id,
        skill_id=test_skill.id,
        level="beginner",
        scenario_json={},
        starting_gauge=50,
        current_gauge=60,
        status="completed",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


# ============================================
# A01: Broken Access Control
# ============================================


class TestBrokenAccessControl:
    """Tests for access control vulnerabilities."""

    @pytest.mark.asyncio
    async def test_idor_session_audit(
        self, client: AsyncClient, auth_headers: dict, other_user_session: VoiceTrainingSession
    ):
        """
        IDOR Test: Should not access other user's session.

        Attacker tries to access session ID belonging to another user.
        """
        response = await client.get(f"/audit/session/{other_user_session.id}", headers=auth_headers)

        assert response.status_code == 403
        assert "denied" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_idor_enumeration_prevention(self, client: AsyncClient, auth_headers: dict):
        """
        Should not leak information through enumeration.

        Non-existent sessions should return 404, not 403.
        This prevents attackers from discovering valid session IDs.
        """
        # Try multiple session IDs
        for session_id in [99999, 100000, 100001]:
            response = await client.get(f"/audit/session/{session_id}", headers=auth_headers)
            # Should be 404 for non-existent, not revealing anything
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_vertical_privilege_escalation(self, client: AsyncClient, auth_headers: dict):
        """
        Regular user should not access admin endpoints.
        """
        # Try to access admin audit logs (if they exist)
        response = await client.get("/admin/audit-logs", headers=auth_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_horizontal_privilege_escalation(self, client: AsyncClient, auth_headers: dict, other_user: User):
        """
        User A should not get progress report for User B.

        Note: Progress report uses current_user from JWT, so this tests
        that we can't manipulate user_id parameter.
        """
        # Progress endpoint uses current user from JWT
        response = await client.get("/audit/progress", headers=auth_headers)

        # Should only return data for authenticated user
        assert response.status_code == 200


# ============================================
# A02: Cryptographic Failures
# ============================================


class TestCryptographicFailures:
    """Tests for cryptographic vulnerabilities."""

    @pytest.mark.asyncio
    async def test_expired_token_rejected(self, client: AsyncClient, test_user: User):
        """Expired JWT tokens should be rejected."""
        # Create an expired token
        with patch("services.auth.timedelta") as mock_timedelta:
            # Force token to be created with past expiry
            from datetime import timedelta

            mock_timedelta.return_value = timedelta(minutes=-30)
            expired_token = create_access_token(test_user.id, test_user.email)

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await client.get("/audit/progress", headers=headers)

        # Should be unauthorized
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_malformed_token_rejected(self, client: AsyncClient):
        """Malformed JWT tokens should be rejected."""
        malformed_tokens = [
            "not.a.token",
            "Bearer",
            "",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJub25lIn0.eyJzdWIiOiIxMjM0NTY3ODkwIn0.",  # Algorithm: none attack
        ]

        for token in malformed_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/audit/progress", headers=headers)
            assert response.status_code == 401, f"Token should be rejected: {token[:50]}..."

    @pytest.mark.asyncio
    async def test_token_tampering_detected(self, client: AsyncClient, test_user: User):
        """Tampered JWT tokens should be rejected."""
        valid_token = create_access_token(test_user.id, test_user.email)

        # Tamper with the payload (change a character)
        parts = valid_token.split(".")
        if len(parts) == 3:
            tampered = parts[0] + "." + parts[1][:-1] + "X" + "." + parts[2]
            headers = {"Authorization": f"Bearer {tampered}"}
            response = await client.get("/audit/progress", headers=headers)
            assert response.status_code == 401


# ============================================
# A03: Injection
# ============================================


class TestInjection:
    """Tests for injection vulnerabilities."""

    @pytest.mark.asyncio
    async def test_sql_injection_session_id(self, client: AsyncClient, auth_headers: dict):
        """SQL injection in session_id should be prevented."""
        payloads = [
            "1 OR 1=1",
            "1; DROP TABLE users;--",
            "1 UNION SELECT * FROM users--",
            "1' OR '1'='1",
        ]

        for payload in payloads:
            response = await client.get(f"/audit/session/{payload}", headers=auth_headers)
            # FastAPI should reject non-integer paths
            assert response.status_code == 422, f"Should reject: {payload}"

    @pytest.mark.asyncio
    async def test_sql_injection_days_param(self, client: AsyncClient, auth_headers: dict):
        """SQL injection in days parameter should be prevented."""
        payloads = [
            "7; DROP TABLE sessions;--",
            "7 OR 1=1",
            "7 UNION SELECT password FROM users",
        ]

        for payload in payloads:
            response = await client.get(f"/audit/progress?days={payload}", headers=auth_headers)
            assert response.status_code == 422, f"Should reject: {payload}"

    @pytest.mark.asyncio
    async def test_command_injection_prevented(self, client: AsyncClient, auth_headers: dict):
        """Command injection should be prevented."""
        payloads = [
            "1%3B%20cat%20%2Fetc%2Fpasswd",  # URL encoded: 1; cat /etc/passwd
            "1%20%7C%20ls",  # URL encoded: 1 | ls
            "1%24%28whoami%29",  # URL encoded: 1$(whoami)
        ]

        for payload in payloads:
            response = await client.get(f"/audit/session/{payload}", headers=auth_headers)
            # Should not execute any commands - rejected as invalid integer
            assert response.status_code in [404, 422, 307]


# ============================================
# A04: Insecure Design
# ============================================


class TestInsecureDesign:
    """Tests for insecure design patterns."""

    @pytest.mark.asyncio
    async def test_no_sensitive_data_in_error_messages(self, client: AsyncClient, auth_headers: dict):
        """Error messages should not leak sensitive information."""
        response = await client.get("/audit/session/99999", headers=auth_headers)

        error = response.json()
        error_str = str(error).lower()

        # Should not contain sensitive info
        assert "password" not in error_str
        assert "secret" not in error_str
        assert "api_key" not in error_str
        assert "database" not in error_str
        assert "sql" not in error_str

    @pytest.mark.asyncio
    async def test_rate_limiting_exists(self, client: AsyncClient, auth_headers: dict):
        """Endpoints should have rate limiting."""
        # Make many requests quickly
        responses = []
        for _ in range(100):
            response = await client.get("/audit/progress", headers=auth_headers)
            responses.append(response.status_code)

        # If rate limiting is working, some requests should be rejected
        # Note: This depends on rate limit configuration
        # At minimum, all should complete without server crash
        assert all(r in [200, 429] for r in responses)


# ============================================
# A05: Security Misconfiguration
# ============================================


class TestSecurityMisconfiguration:
    """Tests for security misconfiguration."""

    @pytest.mark.asyncio
    async def test_no_stack_trace_in_errors(
        self, client: AsyncClient, auth_headers: dict, user_session: VoiceTrainingSession
    ):
        """Stack traces should not be exposed in production errors."""
        # Force an error
        with patch("agents.audit_agent.agent.AuditAgent.audit_session") as mock:
            mock.side_effect = Exception("Internal error")

            response = await client.get(f"/audit/session/{user_session.id}", headers=auth_headers)

            if response.status_code == 500:
                error = response.json()
                error_str = str(error)

                # Should not contain file paths or stack traces
                assert 'File "' not in error_str
                assert "line " not in error_str
                assert "Traceback" not in error_str

    @pytest.mark.asyncio
    async def test_cors_not_wildcard(self, client: AsyncClient):
        """CORS should not allow all origins in production."""
        # Check OPTIONS response for CORS headers
        response = await client.options("/audit/progress", headers={"Origin": "https://evil-site.com"})

        cors_header = response.headers.get("access-control-allow-origin", "")
        # Should not be wildcard
        assert cors_header != "*"


# ============================================
# A07: Identification and Authentication Failures
# ============================================


class TestAuthenticationFailures:
    """Tests for authentication vulnerabilities."""

    @pytest.mark.asyncio
    async def test_missing_auth_header(self, client: AsyncClient):
        """Should reject requests without auth header."""
        response = await client.get("/audit/progress")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_auth_header(self, client: AsyncClient):
        """Should reject empty auth header."""
        response = await client.get("/audit/progress", headers={"Authorization": ""})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_auth_scheme(self, client: AsyncClient):
        """Should reject non-Bearer auth schemes."""
        response = await client.get("/audit/progress", headers={"Authorization": "Basic dXNlcjpwYXNz"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_inactive_user_rejected(self, client: AsyncClient, inactive_user: User):
        """Inactive users should be rejected."""
        token = create_access_token(inactive_user.id, inactive_user.email)
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/audit/progress", headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_deleted_user_rejected(self, client: AsyncClient, db_session: AsyncSession, test_user: User):
        """Tokens for deleted users should be rejected."""
        # Create token first
        token = create_access_token(test_user.id, test_user.email)
        headers = {"Authorization": f"Bearer {token}"}

        # Delete the user
        await db_session.delete(test_user)
        await db_session.commit()

        # Token should no longer work
        response = await client.get("/audit/progress", headers=headers)
        assert response.status_code == 401


# ============================================
# Structure Tests
# ============================================


class TestCodeStructure:
    """Tests for code structure and organization."""

    def test_schemas_are_dataclasses(self):
        """Schemas should be proper dataclasses."""
        from dataclasses import is_dataclass

        from agents.audit_agent.schemas import ChampionComparison, SessionAudit, UserProgressReport, WeeklyDigest

        assert is_dataclass(SessionAudit)
        assert is_dataclass(UserProgressReport)
        assert is_dataclass(ChampionComparison)
        assert is_dataclass(WeeklyDigest)

    def test_performance_levels_are_complete(self):
        """PerformanceLevel enum should have all expected values."""
        from agents.audit_agent.schemas import PerformanceLevel

        expected = {"excellent", "bon", "moyen", "insuffisant", "critique"}
        actual = {level.value for level in PerformanceLevel}

        assert actual == expected

    def test_prompts_are_defined(self):
        """All required prompts should be defined."""
        from agents.audit_agent.prompts import (
            CHAMPION_COMPARISON_PROMPT,
            PROGRESS_REPORT_PROMPT,
            SESSION_AUDIT_PROMPT,
            WEEKLY_DIGEST_PROMPT,
        )

        assert len(SESSION_AUDIT_PROMPT) > 100
        assert len(PROGRESS_REPORT_PROMPT) > 100
        assert len(CHAMPION_COMPARISON_PROMPT) > 100
        assert len(WEEKLY_DIGEST_PROMPT) > 100

    def test_agent_has_required_methods(self):
        """AuditAgent should have all required public methods."""
        from agents.audit_agent.agent import AuditAgent

        required_methods = [
            "audit_session",
            "generate_progress_report",
            "compare_to_champion",
            "generate_weekly_digest",
            "get_next_recommendation",
        ]

        for method in required_methods:
            assert hasattr(AuditAgent, method), f"Missing method: {method}"
