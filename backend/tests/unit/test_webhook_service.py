"""
Unit tests for WebhookService.
Tests endpoint management, webhook delivery, and logging.
"""

import hashlib
import hmac
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models import WebhookEndpoint, WebhookLog
from services.webhooks import WebhookService


class TestEndpointManagement:
    """Tests for webhook endpoint management."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        db.delete = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create WebhookService with mock db."""
        return WebhookService(mock_db)

    @pytest.mark.asyncio
    async def test_get_endpoints(self, service, mock_db):
        """Test getting all endpoints."""
        mock_endpoints = [
            MagicMock(spec=WebhookEndpoint, name="CRM"),
            MagicMock(spec=WebhookEndpoint, name="Analytics"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_endpoints
        mock_db.execute.return_value = mock_result

        endpoints = await service.get_endpoints()

        assert len(endpoints) == 2

    @pytest.mark.asyncio
    async def test_get_endpoints_active_only(self, service, mock_db):
        """Test getting only active endpoints."""
        mock_endpoints = [MagicMock(spec=WebhookEndpoint, is_active=True)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_endpoints
        mock_db.execute.return_value = mock_result

        endpoints = await service.get_endpoints(active_only=True)

        assert len(endpoints) == 1

    @pytest.mark.asyncio
    async def test_get_endpoint(self, service, mock_db):
        """Test getting endpoint by ID."""
        mock_endpoint = MagicMock(spec=WebhookEndpoint)
        mock_endpoint.id = 1
        mock_endpoint.name = "Test Endpoint"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_endpoint
        mock_db.execute.return_value = mock_result

        endpoint = await service.get_endpoint(1)

        assert endpoint.name == "Test Endpoint"

    @pytest.mark.asyncio
    async def test_get_endpoint_not_found(self, service, mock_db):
        """Test getting non-existent endpoint."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        endpoint = await service.get_endpoint(999)

        assert endpoint is None

    @pytest.mark.asyncio
    async def test_create_endpoint(self, service, mock_db):
        """Test creating a new endpoint."""
        result = await service.create_endpoint(
            name="New Webhook",
            url="https://example.com/webhook",
            events=["user.registered", "user.login"],
            is_active=True,
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_endpoint_generates_secret(self, service, mock_db):
        """Test that creating endpoint generates a secret."""
        captured_endpoint = None

        def capture_add(obj):
            nonlocal captured_endpoint
            captured_endpoint = obj

        mock_db.add.side_effect = capture_add

        await service.create_endpoint(name="New Webhook", url="https://example.com/webhook", events=["user.registered"])

        # Secret should be 64 chars (hex of 32 bytes)
        assert captured_endpoint is not None
        assert len(captured_endpoint.secret) == 64

    @pytest.mark.asyncio
    async def test_update_endpoint(self, service, mock_db):
        """Test updating an endpoint."""
        mock_endpoint = MagicMock(spec=WebhookEndpoint)
        mock_endpoint.id = 1
        mock_endpoint.name = "Old Name"
        mock_endpoint.url = "https://old.com/webhook"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_endpoint
        mock_db.execute.return_value = mock_result

        result = await service.update_endpoint(endpoint_id=1, name="New Name", url="https://new.com/webhook")

        assert mock_endpoint.name == "New Name"
        assert mock_endpoint.url == "https://new.com/webhook"

    @pytest.mark.asyncio
    async def test_update_endpoint_not_found(self, service, mock_db):
        """Test updating non-existent endpoint."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.update_endpoint(endpoint_id=999, name="New")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_endpoint(self, service, mock_db):
        """Test deleting an endpoint."""
        mock_endpoint = MagicMock(spec=WebhookEndpoint)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_endpoint
        mock_db.execute.return_value = mock_result

        result = await service.delete_endpoint(1)

        assert result is True
        assert mock_db.delete.called

    @pytest.mark.asyncio
    async def test_delete_endpoint_not_found(self, service, mock_db):
        """Test deleting non-existent endpoint."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.delete_endpoint(999)

        assert result is False

    @pytest.mark.asyncio
    async def test_regenerate_secret(self, service, mock_db):
        """Test regenerating endpoint secret."""
        mock_endpoint = MagicMock(spec=WebhookEndpoint)
        mock_endpoint.id = 1
        mock_endpoint.secret = "old_secret"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_endpoint
        mock_db.execute.return_value = mock_result

        new_secret = await service.regenerate_secret(1)

        assert new_secret is not None
        assert len(new_secret) == 64
        assert new_secret != "old_secret"

    @pytest.mark.asyncio
    async def test_regenerate_secret_not_found(self, service, mock_db):
        """Test regenerating secret for non-existent endpoint."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.regenerate_secret(999)

        assert result is None


class TestSignature:
    """Tests for HMAC signature functionality."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return WebhookService(mock_db)

    def test_sign_payload(self, service):
        """Test payload signing with HMAC-SHA256."""
        payload = '{"event": "test", "data": {}}'
        secret = "test_secret_key"

        signature = service._sign_payload(payload, secret)

        # Verify signature format
        assert len(signature) == 64  # SHA256 hex digest

        # Verify correct signature
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        assert signature == expected

    def test_sign_payload_different_payloads(self, service):
        """Test that different payloads produce different signatures."""
        secret = "test_secret"

        sig1 = service._sign_payload('{"a": 1}', secret)
        sig2 = service._sign_payload('{"a": 2}', secret)

        assert sig1 != sig2

    def test_sign_payload_different_secrets(self, service):
        """Test that different secrets produce different signatures."""
        payload = '{"test": "data"}'

        sig1 = service._sign_payload(payload, "secret1")
        sig2 = service._sign_payload(payload, "secret2")

        assert sig1 != sig2


class TestWebhookDelivery:
    """Tests for webhook delivery functionality."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        return WebhookService(mock_db)

    @pytest.mark.asyncio
    async def test_send_event_to_subscribed_endpoints(self, service, mock_db):
        """Test sending event to subscribed endpoints."""
        mock_endpoint = MagicMock(spec=WebhookEndpoint)
        mock_endpoint.id = 1
        mock_endpoint.name = "Test"
        mock_endpoint.url = "https://example.com/webhook"
        mock_endpoint.secret = "test_secret"
        mock_endpoint.events = ["user.registered"]
        mock_endpoint.is_active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_endpoint]
        mock_db.execute.return_value = mock_result

        with patch("httpx.AsyncClient") as mock_client, patch("services.webhooks.logger"):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            logs = await service.send_event(
                event="user.registered", payload={"user_id": 1, "email": "test@example.com"}
            )

            assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_send_event_no_subscribers(self, service, mock_db):
        """Test sending event with no subscribers."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        logs = await service.send_event(event="user.deleted", payload={"user_id": 1})

        assert len(logs) == 0

    @pytest.mark.asyncio
    async def test_retry_webhook(self, service, mock_db):
        """Test retrying a failed webhook."""
        mock_log = MagicMock(spec=WebhookLog)
        mock_log.id = 1
        mock_log.endpoint_id = 1
        mock_log.event = "user.registered"
        mock_log.payload = {"event": "user.registered", "data": {"user_id": 1}}
        mock_log.status = "failed"
        mock_log.attempts = 1

        mock_endpoint = MagicMock(spec=WebhookEndpoint)
        mock_endpoint.id = 1
        mock_endpoint.is_active = True
        mock_endpoint.url = "https://example.com/webhook"
        mock_endpoint.secret = "secret"

        mock_log_result = MagicMock()
        mock_log_result.scalar_one_or_none.return_value = mock_log

        mock_endpoint_result = MagicMock()
        mock_endpoint_result.scalar_one_or_none.return_value = mock_endpoint

        mock_db.execute.side_effect = [mock_log_result, mock_endpoint_result]

        with patch("httpx.AsyncClient") as mock_client, patch("services.webhooks.logger"):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await service.retry_webhook(1)

            assert mock_log.attempts == 2

    @pytest.mark.asyncio
    async def test_retry_webhook_already_success(self, service, mock_db):
        """Test retrying already successful webhook."""
        mock_log = MagicMock(spec=WebhookLog)
        mock_log.status = "success"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_db.execute.return_value = mock_result

        result = await service.retry_webhook(1)

        assert result is None

    @pytest.mark.asyncio
    async def test_retry_webhook_not_found(self, service, mock_db):
        """Test retrying non-existent webhook."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.retry_webhook(999)

        assert result is None


class TestWebhookLogs:
    """Tests for webhook log functionality."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        return WebhookService(mock_db)

    @pytest.mark.asyncio
    async def test_get_logs(self, service, mock_db):
        """Test getting webhook logs."""
        mock_logs = [MagicMock(spec=WebhookLog) for _ in range(5)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 20

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        logs, total = await service.get_logs(limit=5)

        assert len(logs) == 5
        assert total == 20

    @pytest.mark.asyncio
    async def test_get_logs_filtered(self, service, mock_db):
        """Test getting filtered webhook logs."""
        mock_logs = [MagicMock(spec=WebhookLog)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        logs, total = await service.get_logs(endpoint_id=1, event="user.registered", status="success")

        assert len(logs) == 1

    @pytest.mark.asyncio
    async def test_get_webhook_stats(self, service, mock_db):
        """Test getting webhook statistics."""
        mock_total = MagicMock()
        mock_total.scalar.return_value = 100

        mock_success = MagicMock()
        mock_success.scalar.return_value = 90

        mock_failed = MagicMock()
        mock_failed.scalar.return_value = 10

        mock_pending = MagicMock()
        mock_pending.scalar.return_value = 5

        mock_by_event = MagicMock()
        mock_by_event.all.return_value = [("user.registered", 40), ("user.login", 30), ("training.completed", 30)]

        mock_active = MagicMock()
        mock_active.scalar.return_value = 3

        mock_db.execute.side_effect = [mock_total, mock_success, mock_failed, mock_pending, mock_by_event, mock_active]

        stats = await service.get_webhook_stats()

        assert stats["total_deliveries"] == 100
        assert stats["success"] == 90
        assert stats["failed"] == 10
        assert stats["success_rate"] == 90.0
        assert stats["active_endpoints"] == 3
        assert "available_events" in stats


class TestConvenienceMethods:
    """Tests for convenience event emission methods."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return WebhookService(mock_db)

    @pytest.mark.asyncio
    async def test_emit_user_registered(self, service):
        """Test emitting user.registered event."""
        with patch.object(service, "send_event", new_callable=AsyncMock) as mock_send:
            await service.emit_user_registered(user_id=1, email="test@example.com", name="Test User")

            mock_send.assert_called_once_with(
                "user.registered", {"user_id": 1, "email": "test@example.com", "name": "Test User"}
            )

    @pytest.mark.asyncio
    async def test_emit_user_login(self, service):
        """Test emitting user.login event."""
        with patch.object(service, "send_event", new_callable=AsyncMock) as mock_send:
            await service.emit_user_login(user_id=1, email="test@example.com")

            mock_send.assert_called_once_with("user.login", {"user_id": 1, "email": "test@example.com"})

    @pytest.mark.asyncio
    async def test_emit_champion_created(self, service):
        """Test emitting champion.created event."""
        with patch.object(service, "send_event", new_callable=AsyncMock) as mock_send:
            await service.emit_champion_created(user_id=1, champion_id=10, name="Sales Pro")

            mock_send.assert_called_once_with(
                "champion.created", {"user_id": 1, "champion_id": 10, "name": "Sales Pro"}
            )

    @pytest.mark.asyncio
    async def test_emit_champion_analyzed(self, service):
        """Test emitting champion.analyzed event."""
        with patch.object(service, "send_event", new_callable=AsyncMock) as mock_send:
            await service.emit_champion_analyzed(user_id=1, champion_id=10, name="Sales Pro")

            mock_send.assert_called_once_with(
                "champion.analyzed", {"user_id": 1, "champion_id": 10, "name": "Sales Pro"}
            )

    @pytest.mark.asyncio
    async def test_emit_training_completed(self, service):
        """Test emitting training.completed event."""
        with patch.object(service, "send_event", new_callable=AsyncMock) as mock_send:
            await service.emit_training_completed(user_id=1, session_id=5, champion_id=10, score=85.5)

            mock_send.assert_called_once_with(
                "training.completed", {"user_id": 1, "session_id": 5, "champion_id": 10, "score": 85.5}
            )

    @pytest.mark.asyncio
    async def test_emit_subscription_changed(self, service):
        """Test emitting subscription.changed event."""
        with patch.object(service, "send_event", new_callable=AsyncMock) as mock_send:
            await service.emit_subscription_changed(user_id=1, from_plan="free", to_plan="pro", event_type="upgrade")

            mock_send.assert_called_once_with(
                "subscription.changed", {"user_id": 1, "from_plan": "free", "to_plan": "pro", "type": "upgrade"}
            )


class TestAvailableEvents:
    """Tests for available events constant."""

    def test_events_list_exists(self):
        """Test that EVENTS list is defined."""
        assert hasattr(WebhookService, "EVENTS")
        assert isinstance(WebhookService.EVENTS, list)

    def test_events_list_contains_user_events(self):
        """Test user-related events are present."""
        assert "user.registered" in WebhookService.EVENTS
        assert "user.login" in WebhookService.EVENTS
        assert "user.updated" in WebhookService.EVENTS
        assert "user.deleted" in WebhookService.EVENTS

    def test_events_list_contains_champion_events(self):
        """Test champion-related events are present."""
        assert "champion.created" in WebhookService.EVENTS
        assert "champion.analyzed" in WebhookService.EVENTS
        assert "champion.deleted" in WebhookService.EVENTS

    def test_events_list_contains_training_events(self):
        """Test training-related events are present."""
        assert "training.started" in WebhookService.EVENTS
        assert "training.completed" in WebhookService.EVENTS

    def test_events_list_contains_subscription_events(self):
        """Test subscription-related events are present."""
        assert "subscription.changed" in WebhookService.EVENTS
        assert "subscription.expired" in WebhookService.EVENTS
