"""
Unit tests for ActivityService.
Tests activity logging, journey tracking, error logging, and analytics.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from models import ActivityAction, ActivityLog, ErrorLog, JourneyStage, User
from services.activity import ActivityService


class TestActivityLogging:
    """Tests for activity logging functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create ActivityService with mock db."""
        return ActivityService(mock_db)

    @pytest.mark.asyncio
    async def test_log_activity_creates_log(self, service, mock_db):
        """Test that log_activity creates an activity log."""
        # Setup mock user
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.last_activity_at = None
        mock_user.login_count = 0
        mock_user.journey_stage = JourneyStage.REGISTERED.value

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Execute
        result = await service.log_activity(
            user_id=1,
            action="test_action",
            resource_type="test",
            resource_id=123,
            extra_data={"key": "value"},
            ip_address="127.0.0.1",
            user_agent="TestAgent",
        )

        # Verify
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_log_activity_updates_last_activity(self, service, mock_db):
        """Test that logging activity updates user's last_activity_at."""
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.last_activity_at = None
        mock_user.login_count = 0
        mock_user.journey_stage = JourneyStage.FIRST_LOGIN.value

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        await service.log_activity(user_id=1, action="some_action")

        # User's last_activity_at should be updated
        assert mock_user.last_activity_at is not None

    @pytest.mark.asyncio
    async def test_log_login_updates_login_count(self, service, mock_db):
        """Test that login action updates login count."""
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.last_activity_at = None
        mock_user.last_login_at = None
        mock_user.login_count = 5
        mock_user.journey_stage = JourneyStage.POWER_USER.value  # Use POWER_USER to skip progression check

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        await service.log_activity(user_id=1, action=ActivityAction.LOGIN.value)

        assert mock_user.login_count == 6
        assert mock_user.last_login_at is not None

    @pytest.mark.asyncio
    async def test_get_user_activities(self, service, mock_db):
        """Test getting user activities with pagination."""
        mock_activities = [MagicMock(spec=ActivityLog) for _ in range(3)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_activities

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 10

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        activities, total = await service.get_user_activities(user_id=1, limit=3, offset=0)

        assert len(activities) == 3
        assert total == 10

    @pytest.mark.asyncio
    async def test_get_user_activities_with_action_filter(self, service, mock_db):
        """Test getting user activities filtered by action."""
        mock_activities = [MagicMock(spec=ActivityLog)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_activities

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        activities, total = await service.get_user_activities(user_id=1, action="login")

        assert len(activities) == 1


class TestJourneyTracking:
    """Tests for user journey tracking."""

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
        return ActivityService(mock_db)

    @pytest.mark.asyncio
    async def test_update_journey_stage(self, service, mock_db):
        """Test updating user journey stage."""
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.journey_stage = JourneyStage.REGISTERED.value

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        result = await service.update_journey_stage(user_id=1, new_stage=JourneyStage.FIRST_LOGIN.value)

        assert mock_user.journey_stage == JourneyStage.FIRST_LOGIN.value
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_journey_stage_no_change(self, service, mock_db):
        """Test that same stage returns None."""
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.journey_stage = JourneyStage.FIRST_LOGIN.value

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        result = await service.update_journey_stage(user_id=1, new_stage=JourneyStage.FIRST_LOGIN.value)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_journey_stage_user_not_found(self, service, mock_db):
        """Test updating journey for non-existent user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.update_journey_stage(user_id=999, new_stage=JourneyStage.FIRST_LOGIN.value)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_funnel_stats(self, service, mock_db):
        """Test getting funnel statistics."""
        # Mock count results for each stage
        mock_results = []
        for i, stage in enumerate(JourneyStage):
            mock_result = MagicMock()
            mock_result.scalar.return_value = 10 - i  # Decreasing counts
            mock_results.append(mock_result)

        mock_db.execute.side_effect = mock_results

        stats = await service.get_funnel_stats()

        assert "stages" in stats
        assert "total_users" in stats
        assert "conversion_rates" in stats

    @pytest.mark.asyncio
    async def test_get_funnel_stats_empty(self, service, mock_db):
        """Test funnel stats with no users."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result

        stats = await service.get_funnel_stats()

        assert stats["total_users"] == 0
        assert stats["conversion_rates"] == {}


class TestErrorLogging:
    """Tests for error logging functionality."""

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
        return ActivityService(mock_db)

    @pytest.mark.asyncio
    async def test_log_error(self, service, mock_db):
        """Test logging an error."""
        result = await service.log_error(
            error_type="ValidationError",
            error_message="Invalid input",
            user_id=1,
            stack_trace="Traceback...",
            endpoint="/api/test",
            request_data={"key": "value"},
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_errors(self, service, mock_db):
        """Test getting error logs."""
        mock_errors = [MagicMock(spec=ErrorLog) for _ in range(5)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_errors

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 20

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        errors, total = await service.get_errors(limit=5)

        assert len(errors) == 5
        assert total == 20

    @pytest.mark.asyncio
    async def test_get_errors_filtered(self, service, mock_db):
        """Test getting filtered error logs."""
        mock_errors = [MagicMock(spec=ErrorLog)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_errors

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        errors, total = await service.get_errors(resolved=False, error_type="ValidationError")

        assert len(errors) == 1

    @pytest.mark.asyncio
    async def test_resolve_error(self, service, mock_db):
        """Test resolving an error."""
        mock_error = MagicMock(spec=ErrorLog)
        mock_error.id = 1
        mock_error.is_resolved = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_error
        mock_db.execute.return_value = mock_result

        result = await service.resolve_error(error_id=1, admin_id=1, resolution_notes="Fixed the issue")

        assert mock_error.is_resolved is True
        assert mock_error.resolved_by == 1
        assert mock_error.resolution_notes == "Fixed the issue"

    @pytest.mark.asyncio
    async def test_resolve_error_not_found(self, service, mock_db):
        """Test resolving non-existent error."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.resolve_error(error_id=999, admin_id=1)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_error_stats(self, service, mock_db):
        """Test getting error statistics."""
        mock_total = MagicMock()
        mock_total.scalar.return_value = 100

        mock_unresolved = MagicMock()
        mock_unresolved.scalar.return_value = 30

        mock_by_type = MagicMock()
        mock_by_type.all.return_value = [("ValidationError", 50), ("DatabaseError", 30), ("AuthError", 20)]

        mock_db.execute.side_effect = [mock_total, mock_unresolved, mock_by_type]

        stats = await service.get_error_stats(days=7)

        assert stats["total"] == 100
        assert stats["unresolved"] == 30
        assert stats["resolved"] == 70
        assert "ValidationError" in stats["by_type"]


class TestAnalytics:
    """Tests for analytics functionality."""

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
        return ActivityService(mock_db)

    @pytest.mark.asyncio
    async def test_get_activity_stats(self, service, mock_db):
        """Test getting activity statistics."""
        mock_total = MagicMock()
        mock_total.scalar.return_value = 500

        mock_by_action = MagicMock()
        mock_by_action.all.return_value = [("login", 200), ("upload_video", 100), ("complete_training", 200)]

        mock_daily = MagicMock()
        mock_daily.all.return_value = [("2025-12-28", 150), ("2025-12-29", 175), ("2025-12-30", 175)]

        mock_active_users = MagicMock()
        mock_active_users.scalar.return_value = 50

        mock_db.execute.side_effect = [mock_total, mock_by_action, mock_daily, mock_active_users]

        stats = await service.get_activity_stats(days=30)

        assert stats["total_activities"] == 500
        assert stats["active_users"] == 50
        assert "login" in stats["by_action"]

    @pytest.mark.asyncio
    async def test_get_churn_risk_users(self, service, mock_db):
        """Test getting users at risk of churning."""
        mock_users = [MagicMock(spec=User) for _ in range(3)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_db.execute.return_value = mock_result

        users = await service.get_churn_risk_users(inactive_days=14)

        assert len(users) == 3

    @pytest.mark.asyncio
    async def test_mark_churned_users(self, service, mock_db):
        """Test marking inactive users as churned."""
        mock_user1 = MagicMock(spec=User)
        mock_user1.id = 1
        mock_user1.journey_stage = JourneyStage.ACTIVE_USER.value

        mock_user2 = MagicMock(spec=User)
        mock_user2.id = 2
        mock_user2.journey_stage = JourneyStage.FIRST_TRAINING.value

        # First call returns users to mark
        mock_result1 = MagicMock()
        mock_result1.scalars.return_value.all.return_value = [mock_user1, mock_user2]

        # Subsequent calls for update_journey_stage
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = mock_user1

        mock_result3 = MagicMock()
        mock_result3.scalar_one_or_none.return_value = mock_user2

        mock_db.execute.side_effect = [mock_result1, mock_result2, mock_result3]

        count = await service.mark_churned_users(inactive_days=30)

        assert count == 2
