"""
Integration tests for Admin API endpoints.

Tests admin endpoints across modules:
- Stats (7 endpoints)
- Users (5 endpoints)
- Sessions (1 endpoint)
- Activities (1 endpoint)
- Errors (3 endpoints)
- Emails (6 endpoints)
- Webhooks (8 endpoints)
- Alerts (4 endpoints)
- Notes (3 endpoints)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    User, Champion, TrainingSession, ActivityLog, ErrorLog,
    EmailTemplate, EmailLog, WebhookEndpoint, WebhookLog,
    AdminAlert, AdminNote, UserJourney
)


# ============================================
# Stats Endpoints Tests
# ============================================

class TestAdminStats:
    """Tests for /admin/stats endpoints."""

    @pytest.mark.asyncio
    async def test_get_stats_as_admin(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can access global stats."""
        response = await client.get("/admin/stats", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_champions" in data
        assert "total_sessions" in data
        assert "subscriptions" in data

    @pytest.mark.asyncio
    async def test_get_stats_as_user_forbidden(self, client: AsyncClient, auth_headers: dict):
        """Regular user cannot access admin stats."""
        response = await client.get("/admin/stats", headers=auth_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_stats_unauthorized(self, client: AsyncClient):
        """Unauthenticated request is rejected."""
        response = await client.get("/admin/stats")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_funnel_stats(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can access funnel stats."""
        response = await client.get("/admin/stats/funnel", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "stages" in data
        assert "conversion_rates" in data

    @pytest.mark.asyncio
    async def test_get_activity_stats(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can access activity stats with period."""
        response = await client.get("/admin/stats/activity?days=7", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_activities" in data
        assert "period_days" in data
        assert data["period_days"] == 7

    @pytest.mark.asyncio
    async def test_get_error_stats(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can access error stats."""
        response = await client.get("/admin/stats/errors?days=7", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "resolved" in data
        assert "unresolved" in data

    @pytest.mark.asyncio
    async def test_get_email_stats(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can access email stats."""
        response = await client.get("/admin/stats/emails", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "open_rate" in data

    @pytest.mark.asyncio
    async def test_get_webhook_stats(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can access webhook stats."""
        response = await client.get("/admin/stats/webhooks", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_deliveries" in data
        assert "success_rate" in data
        assert "available_events" in data


# ============================================
# Users Endpoints Tests
# ============================================

class TestAdminUsers:
    """Tests for /admin/users endpoints."""

    @pytest.mark.asyncio
    async def test_list_users(self, client: AsyncClient, admin_auth_headers: dict, test_user: User):
        """Admin can list all users with pagination."""
        response = await client.get("/admin/users", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    @pytest.mark.asyncio
    async def test_list_users_with_search(self, client: AsyncClient, admin_auth_headers: dict, test_user: User):
        """Admin can search users by email."""
        response = await client.get(f"/admin/users?search={test_user.email}", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_users_filter_by_role(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can filter users by role."""
        response = await client.get("/admin/users?role=admin", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        for user in data["items"]:
            assert user["role"] == "admin"

    @pytest.mark.asyncio
    async def test_get_user_detail(self, client: AsyncClient, admin_auth_headers: dict, test_user: User):
        """Admin can get detailed user info."""
        response = await client.get(f"/admin/users/{test_user.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Response has nested user object
        assert "user" in data
        assert data["user"]["id"] == test_user.id
        assert "champions" in data
        assert "sessions" in data
        assert "activities" in data
        assert "stats" in data

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """Returns 404 for non-existent user."""
        response = await client.get("/admin/users/99999", headers=admin_auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user(self, client: AsyncClient, admin_auth_headers: dict, test_user: User):
        """Admin can update user via PATCH."""
        response = await client.patch(
            f"/admin/users/{test_user.id}",
            headers=admin_auth_headers,
            json={"is_active": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["user_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_update_user_role(self, client: AsyncClient, admin_auth_headers: dict, test_user: User):
        """Admin can update user role."""
        response = await client.patch(
            f"/admin/users/{test_user.id}",
            headers=admin_auth_headers,
            json={"role": "admin"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["user_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_get_churn_risk_users(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can get users at churn risk."""
        response = await client.get("/admin/users/churn-risk", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "count" in data


# ============================================
# Sessions Endpoints Tests
# ============================================

class TestAdminSessions:
    """Tests for /admin/sessions endpoints."""

    @pytest.mark.asyncio
    async def test_list_sessions(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can list all training sessions."""
        response = await client.get("/admin/sessions", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_sessions_with_status_filter(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession, test_user: User
    ):
        """Admin can filter sessions by status."""
        from models import TrainingSession, Champion

        # Create a champion first
        champion = Champion(
            user_id=test_user.id,
            name="Test Champion",
            status="ready"
        )
        db_session.add(champion)
        await db_session.commit()
        await db_session.refresh(champion)

        # Create sessions
        session = TrainingSession(
            user_id=str(test_user.id),
            champion_id=champion.id,
            scenario={"context": "test"},
            status="completed"
        )
        db_session.add(session)
        await db_session.commit()

        response = await client.get(
            "/admin/sessions?status=completed",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "completed"

    @pytest.mark.asyncio
    async def test_list_sessions_with_champion_filter(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession, test_user: User
    ):
        """Admin can filter sessions by champion."""
        from models import TrainingSession, Champion

        champion = Champion(
            user_id=test_user.id,
            name="Filter Test Champion",
            status="ready"
        )
        db_session.add(champion)
        await db_session.commit()
        await db_session.refresh(champion)

        session = TrainingSession(
            user_id=str(test_user.id),
            champion_id=champion.id,
            scenario={"context": "test"},
            status="active"
        )
        db_session.add(session)
        await db_session.commit()

        response = await client.get(
            f"/admin/sessions?champion_id={champion.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["champion_id"] == champion.id


# ============================================
# Activities Endpoints Tests
# ============================================

class TestAdminActivities:
    """Tests for /admin/activities endpoints."""

    @pytest.mark.asyncio
    async def test_list_activities(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can list activity logs."""
        response = await client.get("/admin/activities", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_list_activities_filter_by_action(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession, test_user: User
    ):
        """Admin can filter activities by action."""
        # Create an activity
        activity = ActivityLog(
            user_id=test_user.id,
            action="login",
            ip_address="127.0.0.1"
        )
        db_session.add(activity)
        await db_session.commit()

        response = await client.get("/admin/activities?action=login", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["action"] == "login"


# ============================================
# Errors Endpoints Tests
# ============================================

class TestAdminErrors:
    """Tests for /admin/errors endpoints."""

    @pytest.mark.asyncio
    async def test_list_errors(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can list error logs."""
        response = await client.get("/admin/errors", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_list_errors_filter_resolved(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can filter errors by resolved status."""
        # Create an error
        error = ErrorLog(
            error_type="TestError",
            error_message="Test error message",
            endpoint="/test",
            is_resolved=False
        )
        db_session.add(error)
        await db_session.commit()

        response = await client.get("/admin/errors?resolved=false", headers=admin_auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_error_detail(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can get error details."""
        error = ErrorLog(
            error_type="DetailError",
            error_message="Detail test",
            endpoint="/detail"
        )
        db_session.add(error)
        await db_session.commit()
        await db_session.refresh(error)

        response = await client.get(f"/admin/errors/{error.id}", headers=admin_auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_resolve_error(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can resolve an error."""
        error = ErrorLog(
            error_type="TestError",
            error_message="Test",
            endpoint="/test",
            is_resolved=False
        )
        db_session.add(error)
        await db_session.commit()
        await db_session.refresh(error)

        response = await client.post(
            f"/admin/errors/{error.id}/resolve",
            headers=admin_auth_headers,
            json={"resolution_notes": "Fixed the issue"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
        assert data["error_id"] == error.id


# ============================================
# Email Templates Endpoints Tests
# ============================================

class TestAdminEmails:
    """Tests for /admin/email-templates and /admin/email-logs endpoints."""

    @pytest.mark.asyncio
    async def test_list_email_templates(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can list email templates."""
        response = await client.get("/admin/email-templates", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_create_email_template(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can create an email template."""
        response = await client.post(
            "/admin/email-templates",
            headers=admin_auth_headers,
            json={
                "trigger": "test.event",
                "subject": "Test Subject",
                "body_html": "<h1>Test</h1>",
                "body_text": "Test"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert "template_id" in data

    @pytest.mark.asyncio
    async def test_create_duplicate_template_fails(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Should reject duplicate trigger."""
        template = EmailTemplate(
            trigger="duplicate.trigger",
            subject="Original",
            body_html="<p>Original</p>",
            body_text="Original"
        )
        db_session.add(template)
        await db_session.commit()

        response = await client.post(
            "/admin/email-templates",
            headers=admin_auth_headers,
            json={
                "trigger": "duplicate.trigger",
                "subject": "Duplicate",
                "body_html": "<p>Dup</p>",
                "body_text": "Dup"
            }
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """Should return 404 for non-existent template."""
        response = await client.get("/admin/email-templates/99999", headers=admin_auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_template_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """Should return 404 when updating non-existent template."""
        response = await client.patch(
            "/admin/email-templates/99999",
            headers=admin_auth_headers,
            json={"subject": "Ghost Template"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_template_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """Should return 404 when deleting non-existent template."""
        response = await client.delete("/admin/email-templates/99999", headers=admin_auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_send_test_email_template_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """Should return 404 when testing non-existent template."""
        response = await client.post(
            "/admin/email-templates/99999/send-test",
            headers=admin_auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_email_logs_with_filters(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession, test_user: User
    ):
        """Admin can filter email logs."""
        from models import EmailLog

        log = EmailLog(
            user_id=test_user.id,
            trigger="test.trigger",
            to_email=test_user.email,
            subject="Test",
            status="sent"
        )
        db_session.add(log)
        await db_session.commit()

        response = await client.get(
            f"/admin/email-logs?user_id={test_user.id}&trigger=test.trigger&status=sent",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_email_template(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can get a single email template."""
        template = EmailTemplate(
            trigger="get.test",
            subject="Get Test",
            body_html="<p>Test</p>",
            body_text="Test"
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)

        response = await client.get(
            f"/admin/email-templates/{template.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["trigger"] == "get.test"

    @pytest.mark.asyncio
    async def test_update_email_template(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can update an email template."""
        template = EmailTemplate(
            trigger="update.test",
            subject="Original",
            body_html="<p>Original</p>",
            body_text="Original"
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)

        response = await client.patch(
            f"/admin/email-templates/{template.id}",
            headers=admin_auth_headers,
            json={"subject": "Updated Subject"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["template_id"] == template.id

    @pytest.mark.asyncio
    async def test_delete_email_template(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can delete an email template."""
        template = EmailTemplate(
            trigger="delete.test",
            subject="Delete",
            body_html="<p>Delete</p>",
            body_text="Delete"
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)

        response = await client.delete(
            f"/admin/email-templates/{template.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_email_logs(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can list email logs."""
        response = await client.get("/admin/email-logs", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


# ============================================
# Webhook Endpoints Tests
# ============================================

class TestAdminWebhooks:
    """Tests for /admin/webhooks endpoints."""

    @pytest.mark.asyncio
    async def test_list_webhooks(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can list webhook endpoints."""
        response = await client.get("/admin/webhooks", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "available_events" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_create_webhook(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can create a webhook endpoint."""
        response = await client.post(
            "/admin/webhooks",
            headers=admin_auth_headers,
            json={
                "name": "Test Webhook",
                "url": "https://example.com/webhook",
                "events": ["user.registered"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert "endpoint_id" in data
        assert "secret" in data

    @pytest.mark.asyncio
    async def test_create_webhook_invalid_events(self, client: AsyncClient, admin_auth_headers: dict):
        """Should reject webhook with invalid events."""
        response = await client.post(
            "/admin/webhooks",
            headers=admin_auth_headers,
            json={
                "name": "Invalid Webhook",
                "url": "https://example.com/invalid",
                "events": ["invalid.event"]
            }
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_webhook_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """Should return 404 for non-existent webhook."""
        response = await client.get("/admin/webhooks/99999", headers=admin_auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_webhook_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """Should return 404 when updating non-existent webhook."""
        response = await client.patch(
            "/admin/webhooks/99999",
            headers=admin_auth_headers,
            json={"name": "Ghost Webhook"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_webhook_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """Should return 404 when deleting non-existent webhook."""
        response = await client.delete("/admin/webhooks/99999", headers=admin_auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_regenerate_webhook_secret(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can regenerate webhook secret."""
        webhook = WebhookEndpoint(
            name="Regen Test",
            url="https://example.com/regen",
            secret="old_secret",
            events=["user.registered"]
        )
        db_session.add(webhook)
        await db_session.commit()
        await db_session.refresh(webhook)

        response = await client.post(
            f"/admin/webhooks/{webhook.id}/regenerate-secret",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "regenerated"
        assert "secret" in data

    @pytest.mark.asyncio
    async def test_regenerate_secret_not_found(self, client: AsyncClient, admin_auth_headers: dict):
        """Should return 404 when regenerating secret for non-existent webhook."""
        response = await client.post(
            "/admin/webhooks/99999/regenerate-secret",
            headers=admin_auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_webhook(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can get a single webhook."""
        webhook = WebhookEndpoint(
            name="Get Test",
            url="https://example.com/get",
            secret="secret123",
            events=["user.registered"]
        )
        db_session.add(webhook)
        await db_session.commit()
        await db_session.refresh(webhook)

        response = await client.get(
            f"/admin/webhooks/{webhook.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_webhook(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can update a webhook endpoint."""
        webhook = WebhookEndpoint(
            name="Original",
            url="https://example.com/original",
            secret="secret123",
            events=["user.registered"]
        )
        db_session.add(webhook)
        await db_session.commit()
        await db_session.refresh(webhook)

        response = await client.patch(
            f"/admin/webhooks/{webhook.id}",
            headers=admin_auth_headers,
            json={"name": "Updated Name"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["endpoint_id"] == webhook.id

    @pytest.mark.asyncio
    async def test_delete_webhook(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can delete a webhook endpoint."""
        webhook = WebhookEndpoint(
            name="Delete Test",
            url="https://example.com/delete",
            secret="secret",
            events=["user.registered"]
        )
        db_session.add(webhook)
        await db_session.commit()
        await db_session.refresh(webhook)

        response = await client.delete(
            f"/admin/webhooks/{webhook.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_webhook_logs(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can list webhook delivery logs."""
        response = await client.get("/admin/webhook-logs", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


# ============================================
# Alerts Endpoints Tests
# ============================================

class TestAdminAlerts:
    """Tests for /admin/alerts endpoints."""

    @pytest.mark.asyncio
    async def test_list_alerts(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can list alerts."""
        response = await client.get("/admin/alerts", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_list_alerts_unread_only(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can filter unread alerts only."""
        # Create read and unread alerts
        read_alert = AdminAlert(
            type="test",
            severity="info",
            title="Read Alert",
            message="Already read",
            is_read=True
        )
        unread_alert = AdminAlert(
            type="test",
            severity="warning",
            title="Unread Alert",
            message="Not read yet",
            is_read=False
        )
        db_session.add(read_alert)
        db_session.add(unread_alert)
        await db_session.commit()

        response = await client.get(
            "/admin/alerts?unread_only=true",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["is_read"] == False

    @pytest.mark.asyncio
    async def test_list_alerts_pagination(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can paginate alerts."""
        # Create multiple alerts
        for i in range(5):
            alert = AdminAlert(
                type="test",
                severity="info",
                title=f"Alert {i}",
                message=f"Message {i}"
            )
            db_session.add(alert)
        await db_session.commit()

        response = await client.get(
            "/admin/alerts?page=1&per_page=2",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["per_page"] == 2
        assert len(data["items"]) <= 2

    @pytest.mark.asyncio
    async def test_mark_alert_read(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can mark alert as read."""
        alert = AdminAlert(
            type="test",
            severity="info",
            title="Test",
            message="Test message",
            is_read=False
        )
        db_session.add(alert)
        await db_session.commit()
        await db_session.refresh(alert)

        response = await client.post(
            f"/admin/alerts/{alert.id}/read",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "read"
        assert data["alert_id"] == alert.id

    @pytest.mark.asyncio
    async def test_dismiss_alert(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can dismiss an alert."""
        alert = AdminAlert(
            type="test",
            severity="warning",
            title="Dismiss Test",
            message="Test",
            is_dismissed=False
        )
        db_session.add(alert)
        await db_session.commit()
        await db_session.refresh(alert)

        response = await client.post(
            f"/admin/alerts/{alert.id}/dismiss",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "dismissed"
        assert data["alert_id"] == alert.id

    @pytest.mark.asyncio
    async def test_mark_all_alerts_read(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Admin can mark all alerts as read."""
        # Create multiple unread alerts
        for i in range(3):
            alert = AdminAlert(
                type="test",
                severity="info",
                title=f"Alert {i}",
                message="Test",
                is_read=False
            )
            db_session.add(alert)
        await db_session.commit()

        response = await client.post("/admin/alerts/read-all", headers=admin_auth_headers)
        assert response.status_code == 200


# ============================================
# Notes Endpoints Tests
# ============================================

class TestAdminNotes:
    """Tests for /admin/notes endpoints."""

    @pytest.mark.asyncio
    async def test_list_notes_for_user(
        self, client: AsyncClient, admin_auth_headers: dict,
        test_user: User
    ):
        """Admin can list notes for a user."""
        response = await client.get(
            f"/admin/users/{test_user.id}/notes",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_create_note(
        self, client: AsyncClient, admin_auth_headers: dict,
        test_user: User, admin_user: User
    ):
        """Admin can create a note for a user."""
        response = await client.post(
            f"/admin/users/{test_user.id}/notes",
            headers=admin_auth_headers,
            json={"content": "This is a test note"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert "note_id" in data

    @pytest.mark.asyncio
    async def test_create_pinned_note(
        self, client: AsyncClient, admin_auth_headers: dict,
        test_user: User, admin_user: User
    ):
        """Admin can create a pinned note."""
        response = await client.post(
            f"/admin/users/{test_user.id}/notes",
            headers=admin_auth_headers,
            json={"content": "Important pinned note", "is_pinned": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"

    @pytest.mark.asyncio
    async def test_create_note_for_nonexistent_user(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """Should return 404 for non-existent user."""
        response = await client.post(
            "/admin/users/99999/notes",
            headers=admin_auth_headers,
            json={"content": "Note for ghost user"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_note(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession, test_user: User, admin_user: User
    ):
        """Admin can update a note."""
        note = AdminNote(
            user_id=test_user.id,
            admin_id=admin_user.id,
            content="Original content"
        )
        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)

        response = await client.patch(
            f"/admin/notes/{note.id}",
            headers=admin_auth_headers,
            json={"content": "Updated content", "is_pinned": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"

    @pytest.mark.asyncio
    async def test_update_nonexistent_note(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """Should return 404 for non-existent note."""
        response = await client.patch(
            "/admin/notes/99999",
            headers=admin_auth_headers,
            json={"content": "Ghost note"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_note(
        self, client: AsyncClient, admin_auth_headers: dict,
        db_session: AsyncSession, test_user: User, admin_user: User
    ):
        """Admin can delete a note."""
        note = AdminNote(
            user_id=test_user.id,
            admin_id=admin_user.id,
            content="To delete"
        )
        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)

        response = await client.delete(
            f"/admin/notes/{note.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_nonexistent_note(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """Should return 404 for non-existent note."""
        response = await client.delete(
            "/admin/notes/99999",
            headers=admin_auth_headers
        )
        assert response.status_code == 404


# ============================================
# Audit Log Tests
# ============================================

class TestAdminAuditLogs:
    """Tests for /admin/audit-logs endpoints."""

    @pytest.mark.asyncio
    async def test_list_audit_logs(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can list audit logs."""
        response = await client.get("/admin/audit-logs", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "available_actions" in data

    @pytest.mark.asyncio
    async def test_list_audit_logs_pagination(self, client: AsyncClient, admin_auth_headers: dict):
        """Admin can paginate audit logs."""
        response = await client.get(
            "/admin/audit-logs?page=1&per_page=10",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10

    @pytest.mark.asyncio
    async def test_user_update_creates_audit_log(
        self, client: AsyncClient, admin_auth_headers: dict,
        test_user: User
    ):
        """User update creates an audit log entry."""
        # First, update a user
        await client.patch(
            f"/admin/users/{test_user.id}",
            headers=admin_auth_headers,
            json={"is_active": False}
        )

        # Then check audit logs
        response = await client.get(
            "/admin/audit-logs?resource_type=user",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_audit_log_not_found(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """Should return 404 for non-existent audit log."""
        response = await client.get(
            "/admin/audit-logs/99999",
            headers=admin_auth_headers
        )
        assert response.status_code == 404


# ============================================
# Authorization Tests
# ============================================

class TestAdminAuthorization:
    """Tests for admin authorization across all endpoints."""

    @pytest.mark.asyncio
    async def test_non_admin_cannot_access_users(self, client: AsyncClient, auth_headers: dict):
        """Regular user cannot access admin user endpoints."""
        response = await client.get("/admin/users", headers=auth_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_non_admin_cannot_access_activities(self, client: AsyncClient, auth_headers: dict):
        """Regular user cannot access admin activity endpoints."""
        response = await client.get("/admin/activities", headers=auth_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_non_admin_cannot_access_errors(self, client: AsyncClient, auth_headers: dict):
        """Regular user cannot access admin error endpoints."""
        response = await client.get("/admin/errors", headers=auth_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_non_admin_cannot_access_webhooks(self, client: AsyncClient, auth_headers: dict):
        """Regular user cannot access admin webhook endpoints."""
        response = await client.get("/admin/webhooks", headers=auth_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_non_admin_cannot_access_alerts(self, client: AsyncClient, auth_headers: dict):
        """Regular user cannot access admin alert endpoints."""
        response = await client.get("/admin/alerts", headers=auth_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_non_admin_cannot_update_user(self, client: AsyncClient, auth_headers: dict, test_user: User):
        """Regular user cannot update users via admin endpoint."""
        response = await client.patch(
            f"/admin/users/{test_user.id}",
            headers=auth_headers,
            json={"role": "admin"}
        )
        assert response.status_code == 403
