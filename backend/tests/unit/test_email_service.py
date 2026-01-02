"""
Unit tests for EmailService.
Tests template management, email sending, and email logs.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models import EmailLog, EmailTemplate, EmailTrigger, User
from services.email import EmailService


class TestTemplateManagement:
    """Tests for email template management."""

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
        """Create EmailService with mock db."""
        with patch("services.email.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                smtp_host="",
                smtp_port=587,
                smtp_tls=True,
                smtp_user="",
                smtp_password="",
                smtp_from="test@example.com",
                cors_origins="http://localhost:3000",
            )
            return EmailService(mock_db)

    @pytest.mark.asyncio
    async def test_get_templates(self, service, mock_db):
        """Test getting all templates."""
        mock_templates = [
            MagicMock(spec=EmailTemplate, trigger="welcome"),
            MagicMock(spec=EmailTemplate, trigger="inactive_3_days"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_templates
        mock_db.execute.return_value = mock_result

        templates = await service.get_templates()

        assert len(templates) == 2

    @pytest.mark.asyncio
    async def test_get_template(self, service, mock_db):
        """Test getting a template by ID."""
        mock_template = MagicMock(spec=EmailTemplate)
        mock_template.id = 1
        mock_template.trigger = "welcome"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_db.execute.return_value = mock_result

        template = await service.get_template(1)

        assert template.trigger == "welcome"

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, service, mock_db):
        """Test getting non-existent template."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        template = await service.get_template(999)

        assert template is None

    @pytest.mark.asyncio
    async def test_get_template_by_trigger(self, service, mock_db):
        """Test getting template by trigger."""
        mock_template = MagicMock(spec=EmailTemplate)
        mock_template.trigger = "welcome"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_db.execute.return_value = mock_result

        template = await service.get_template_by_trigger("welcome")

        assert template.trigger == "welcome"

    @pytest.mark.asyncio
    async def test_create_template(self, service, mock_db):
        """Test creating a new template."""
        result = await service.create_template(
            trigger="test_trigger",
            subject="Test Subject",
            body_html="<h1>Test</h1>",
            body_text="Test",
            variables=["user_name"],
            is_active=True,
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_template(self, service, mock_db):
        """Test updating a template."""
        mock_template = MagicMock(spec=EmailTemplate)
        mock_template.id = 1
        mock_template.subject = "Old Subject"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_db.execute.return_value = mock_result

        result = await service.update_template(template_id=1, subject="New Subject")

        assert mock_template.subject == "New Subject"
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_template_not_found(self, service, mock_db):
        """Test updating non-existent template."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.update_template(template_id=999, subject="New")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_template(self, service, mock_db):
        """Test deleting a template."""
        mock_template = MagicMock(spec=EmailTemplate)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_db.execute.return_value = mock_result

        result = await service.delete_template(1)

        assert result is True
        assert mock_db.delete.called

    @pytest.mark.asyncio
    async def test_delete_template_not_found(self, service, mock_db):
        """Test deleting non-existent template."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.delete_template(999)

        assert result is False


class TestEmailRendering:
    """Tests for template rendering."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        with patch("services.email.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(smtp_host="", cors_origins="http://localhost:3000")
            return EmailService(mock_db)

    def test_render_template_simple(self, service):
        """Test rendering template with variables."""
        content = "Hello {{user_name}}, welcome to {{app_name}}!"
        variables = {"user_name": "John", "app_name": "TestApp"}

        rendered = service._render_template(content, variables)

        assert rendered == "Hello John, welcome to TestApp!"

    def test_render_template_multiple_occurrences(self, service):
        """Test rendering with multiple occurrences of same variable."""
        content = "Hi {{user_name}}, your name is {{user_name}}."
        variables = {"user_name": "Alice"}

        rendered = service._render_template(content, variables)

        assert rendered == "Hi Alice, your name is Alice."

    def test_render_template_no_variables(self, service):
        """Test rendering template without variables."""
        content = "This is a static message."
        variables = {}

        rendered = service._render_template(content, variables)

        assert rendered == "This is a static message."


class TestEmailSending:
    """Tests for email sending functionality."""

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
        with patch("services.email.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                smtp_host="",
                smtp_port=587,
                smtp_tls=True,
                smtp_user="",
                smtp_password="",
                smtp_from="test@example.com",
                cors_origins="http://localhost:3000",
            )
            return EmailService(mock_db)

    @pytest.mark.asyncio
    async def test_send_email_user_not_found(self, service, mock_db):
        """Test sending email when user not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.send_email(user_id=999, trigger="welcome")

        assert result is None

    @pytest.mark.asyncio
    async def test_send_email_template_not_found(self, service, mock_db):
        """Test sending email when template not found."""
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.email = "test@example.com"

        # First call returns user, second returns None (no template)
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user

        mock_template_result = MagicMock()
        mock_template_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_user_result, mock_template_result]

        result = await service.send_email(user_id=1, trigger="nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_send_email_simulated(self, service, mock_db):
        """Test sending email without SMTP (simulated)."""
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"

        mock_template = MagicMock(spec=EmailTemplate)
        mock_template.id = 1
        mock_template.trigger = "welcome"
        mock_template.is_active = True
        mock_template.subject = "Welcome {{user_name}}"
        mock_template.body_html = "<h1>Hello {{user_name}}</h1>"
        mock_template.body_text = "Hello {{user_name}}"

        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user

        mock_template_result = MagicMock()
        mock_template_result.scalar_one_or_none.return_value = mock_template

        mock_db.execute.side_effect = [mock_user_result, mock_template_result]

        result = await service.send_email(user_id=1, trigger="welcome")

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_send_email_inactive_template(self, service, mock_db):
        """Test that inactive templates don't send."""
        mock_user = MagicMock(spec=User)
        mock_user.id = 1

        mock_template = MagicMock(spec=EmailTemplate)
        mock_template.is_active = False

        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user

        mock_template_result = MagicMock()
        mock_template_result.scalar_one_or_none.return_value = mock_template

        mock_db.execute.side_effect = [mock_user_result, mock_template_result]

        result = await service.send_email(user_id=1, trigger="welcome")

        assert result is None


class TestTriggerAutomation:
    """Tests for trigger automation methods."""

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
        with patch("services.email.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(smtp_host="", cors_origins="http://localhost:3000")
            return EmailService(mock_db)

    @pytest.mark.asyncio
    async def test_send_welcome_email(self, service):
        """Test sending welcome email."""
        with patch.object(service, "trigger_email", new_callable=AsyncMock) as mock_trigger:
            await service.send_welcome_email(user_id=1)
            mock_trigger.assert_called_once_with(EmailTrigger.WELCOME, 1)

    @pytest.mark.asyncio
    async def test_send_first_champion_email(self, service):
        """Test sending first champion email."""
        with patch.object(service, "trigger_email", new_callable=AsyncMock) as mock_trigger:
            await service.send_first_champion_email(user_id=1, champion_name="Sales Pro")
            mock_trigger.assert_called_once()
            args = mock_trigger.call_args
            assert args[0][0] == EmailTrigger.FIRST_CHAMPION
            assert args[0][2]["champion_name"] == "Sales Pro"

    @pytest.mark.asyncio
    async def test_send_inactive_reminder_3_days(self, service):
        """Test sending 3-day inactive reminder."""
        with patch.object(service, "trigger_email", new_callable=AsyncMock) as mock_trigger:
            await service.send_inactive_reminder(user_id=1, days_inactive=3)
            args = mock_trigger.call_args
            assert args[0][0] == EmailTrigger.INACTIVE_3_DAYS

    @pytest.mark.asyncio
    async def test_send_inactive_reminder_7_days(self, service):
        """Test sending 7-day inactive reminder."""
        with patch.object(service, "trigger_email", new_callable=AsyncMock) as mock_trigger:
            await service.send_inactive_reminder(user_id=1, days_inactive=7)
            args = mock_trigger.call_args
            assert args[0][0] == EmailTrigger.INACTIVE_7_DAYS

    @pytest.mark.asyncio
    async def test_send_inactive_reminder_30_days(self, service):
        """Test sending 30-day inactive reminder."""
        with patch.object(service, "trigger_email", new_callable=AsyncMock) as mock_trigger:
            await service.send_inactive_reminder(user_id=1, days_inactive=30)
            args = mock_trigger.call_args
            assert args[0][0] == EmailTrigger.INACTIVE_30_DAYS


class TestEmailLogs:
    """Tests for email log functionality."""

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
        with patch("services.email.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(smtp_host="")
            return EmailService(mock_db)

    @pytest.mark.asyncio
    async def test_get_email_logs(self, service, mock_db):
        """Test getting email logs."""
        mock_logs = [MagicMock(spec=EmailLog) for _ in range(5)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 20

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        logs, total = await service.get_email_logs(limit=5)

        assert len(logs) == 5
        assert total == 20

    @pytest.mark.asyncio
    async def test_get_email_logs_filtered(self, service, mock_db):
        """Test getting filtered email logs."""
        mock_logs = [MagicMock(spec=EmailLog)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        logs, total = await service.get_email_logs(user_id=1, trigger="welcome", status="sent")

        assert len(logs) == 1

    @pytest.mark.asyncio
    async def test_get_email_stats(self, service, mock_db):
        """Test getting email statistics."""
        mock_sent = MagicMock()
        mock_sent.scalar.return_value = 100

        mock_failed = MagicMock()
        mock_failed.scalar.return_value = 5

        mock_opened = MagicMock()
        mock_opened.scalar.return_value = 60

        mock_clicked = MagicMock()
        mock_clicked.scalar.return_value = 20

        mock_by_trigger = MagicMock()
        mock_by_trigger.all.return_value = [("welcome", 50), ("inactive_3_days", 30), ("first_champion", 25)]

        mock_db.execute.side_effect = [mock_sent, mock_failed, mock_opened, mock_clicked, mock_by_trigger]

        stats = await service.get_email_stats()

        assert stats["sent"] == 100
        assert stats["failed"] == 5
        assert stats["opened"] == 60
        assert stats["clicked"] == 20
        assert stats["open_rate"] == 60.0
        assert stats["click_rate"] == 20.0

    @pytest.mark.asyncio
    async def test_mark_opened(self, service, mock_db):
        """Test marking email as opened."""
        mock_email = MagicMock(spec=EmailLog)
        mock_email.id = 1
        mock_email.opened_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_email
        mock_db.execute.return_value = mock_result

        result = await service.mark_opened(1)

        assert result is True
        assert mock_email.opened_at is not None
        assert mock_email.status == "opened"

    @pytest.mark.asyncio
    async def test_mark_opened_already_opened(self, service, mock_db):
        """Test marking already opened email."""
        mock_email = MagicMock(spec=EmailLog)
        mock_email.id = 1
        mock_email.opened_at = datetime.utcnow()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_email
        mock_db.execute.return_value = mock_result

        result = await service.mark_opened(1)

        assert result is True
        # commit should not be called since already opened
        assert not mock_db.commit.called

    @pytest.mark.asyncio
    async def test_mark_clicked(self, service, mock_db):
        """Test marking email as clicked."""
        mock_email = MagicMock(spec=EmailLog)
        mock_email.id = 1
        mock_email.clicked_at = None
        mock_email.opened_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_email
        mock_db.execute.return_value = mock_result

        result = await service.mark_clicked(1)

        assert result is True
        assert mock_email.clicked_at is not None
        assert mock_email.opened_at is not None  # Also marks as opened
        assert mock_email.status == "clicked"

    @pytest.mark.asyncio
    async def test_mark_clicked_not_found(self, service, mock_db):
        """Test marking non-existent email as clicked."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.mark_clicked(999)

        assert result is False
