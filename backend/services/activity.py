"""
Activity tracking service for user analytics.
Tracks user actions, journey progression, and error logging.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    User, ActivityLog, UserJourney, ErrorLog, TrainingSession,
    ActivityAction, JourneyStage
)


class ActivityService:
    """Service for tracking and analyzing user activities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # ACTIVITY LOGGING
    # =========================================================================

    async def log_activity(
        self,
        user_id: int,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        extra_data: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Log a user activity."""
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            extra_data=extra_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(activity)

        # Update user's last_activity_at
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.last_activity_at = datetime.utcnow()

            # Handle login tracking
            if action == ActivityAction.LOGIN.value:
                user.last_login_at = datetime.utcnow()
                user.login_count = (user.login_count or 0) + 1

        await self.db.commit()
        await self.db.refresh(activity)

        # Check for journey progression
        await self._check_journey_progression(user_id, action, resource_type)

        return activity

    async def get_user_activities(
        self,
        user_id: int,
        action: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[ActivityLog], int]:
        """Get activities for a user with optional filtering."""
        query = select(ActivityLog).where(ActivityLog.user_id == user_id)
        count_query = select(func.count(ActivityLog.id)).where(ActivityLog.user_id == user_id)

        if action:
            query = query.where(ActivityLog.action == action)
            count_query = count_query.where(ActivityLog.action == action)

        query = query.order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        activities = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return activities, total

    # =========================================================================
    # JOURNEY TRACKING
    # =========================================================================

    async def _check_journey_progression(
        self,
        user_id: int,
        action: str,
        resource_type: Optional[str] = None
    ):
        """Check if user should progress to next journey stage."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return

        current_stage = user.journey_stage
        new_stage = None

        # Determine if stage should progress
        if current_stage == JourneyStage.REGISTERED.value:
            if action == ActivityAction.LOGIN.value:
                new_stage = JourneyStage.FIRST_LOGIN.value

        elif current_stage == JourneyStage.FIRST_LOGIN.value:
            if action == ActivityAction.UPLOAD_VIDEO.value:
                new_stage = JourneyStage.FIRST_UPLOAD.value

        elif current_stage == JourneyStage.FIRST_UPLOAD.value:
            if action == ActivityAction.COMPLETE_ANALYSIS.value:
                new_stage = JourneyStage.FIRST_ANALYSIS.value

        elif current_stage == JourneyStage.FIRST_ANALYSIS.value:
            if action == ActivityAction.COMPLETE_TRAINING.value:
                new_stage = JourneyStage.FIRST_TRAINING.value

        elif current_stage == JourneyStage.FIRST_TRAINING.value:
            # Check if user has 3+ completed sessions
            sessions_count = await self._count_completed_sessions(user_id)
            if sessions_count >= 3:
                new_stage = JourneyStage.ACTIVE_USER.value

        elif current_stage == JourneyStage.ACTIVE_USER.value:
            # Check if user has 10+ completed sessions
            sessions_count = await self._count_completed_sessions(user_id)
            if sessions_count >= 10:
                new_stage = JourneyStage.POWER_USER.value

        if new_stage and new_stage != current_stage:
            await self.update_journey_stage(user_id, new_stage)

    async def _count_completed_sessions(self, user_id: int) -> int:
        """Count completed training sessions for a user."""
        result = await self.db.execute(
            select(func.count(TrainingSession.id)).where(
                and_(
                    TrainingSession.user_id == str(user_id),
                    TrainingSession.status == "completed"
                )
            )
        )
        return result.scalar() or 0

    async def update_journey_stage(
        self,
        user_id: int,
        new_stage: str,
        extra_data: Optional[dict] = None
    ) -> Optional[UserJourney]:
        """Update user's journey stage and log the transition."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None

        previous_stage = user.journey_stage
        if previous_stage == new_stage:
            return None

        # Update user
        user.journey_stage = new_stage

        # Log the transition
        journey_event = UserJourney(
            user_id=user_id,
            stage=new_stage,
            previous_stage=previous_stage,
            extra_data=extra_data
        )
        self.db.add(journey_event)
        await self.db.commit()
        await self.db.refresh(journey_event)

        return journey_event

    async def get_funnel_stats(self) -> dict:
        """Get funnel conversion statistics."""
        stages = [stage.value for stage in JourneyStage]
        stats = {}

        for stage in stages:
            result = await self.db.execute(
                select(func.count(User.id)).where(User.journey_stage == stage)
            )
            stats[stage] = result.scalar() or 0

        # Calculate total and conversion rates
        total_users = sum(stats.values())
        if total_users == 0:
            return {
                "stages": stats,
                "total_users": 0,
                "conversion_rates": {}
            }

        conversion_rates = {}
        prev_count = total_users
        for stage in stages:
            if prev_count > 0:
                rate = (stats[stage] / prev_count) * 100
            else:
                rate = 0
            conversion_rates[stage] = round(rate, 1)
            prev_count = stats[stage] if stats[stage] > 0 else prev_count

        return {
            "stages": stats,
            "total_users": total_users,
            "conversion_rates": conversion_rates
        }

    # =========================================================================
    # ERROR LOGGING
    # =========================================================================

    async def log_error(
        self,
        error_type: str,
        error_message: str,
        user_id: Optional[int] = None,
        stack_trace: Optional[str] = None,
        endpoint: Optional[str] = None,
        request_data: Optional[dict] = None
    ) -> ErrorLog:
        """Log an application error."""
        error = ErrorLog(
            user_id=user_id,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            endpoint=endpoint,
            request_data=request_data
        )
        self.db.add(error)
        await self.db.commit()
        await self.db.refresh(error)
        return error

    async def get_errors(
        self,
        resolved: Optional[bool] = None,
        error_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[ErrorLog], int]:
        """Get error logs with optional filtering."""
        query = select(ErrorLog)
        count_query = select(func.count(ErrorLog.id))

        if resolved is not None:
            query = query.where(ErrorLog.is_resolved == resolved)
            count_query = count_query.where(ErrorLog.is_resolved == resolved)

        if error_type:
            query = query.where(ErrorLog.error_type == error_type)
            count_query = count_query.where(ErrorLog.error_type == error_type)

        query = query.order_by(ErrorLog.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        errors = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return errors, total

    async def resolve_error(
        self,
        error_id: int,
        admin_id: int,
        resolution_notes: Optional[str] = None
    ) -> Optional[ErrorLog]:
        """Mark an error as resolved."""
        result = await self.db.execute(select(ErrorLog).where(ErrorLog.id == error_id))
        error = result.scalar_one_or_none()
        if not error:
            return None

        error.is_resolved = True
        error.resolved_at = datetime.utcnow()
        error.resolved_by = admin_id
        error.resolution_notes = resolution_notes

        await self.db.commit()
        await self.db.refresh(error)
        return error

    async def get_error_stats(self, days: int = 7) -> dict:
        """Get error statistics for the past N days."""
        since = datetime.utcnow() - timedelta(days=days)

        # Total errors
        total_result = await self.db.execute(
            select(func.count(ErrorLog.id)).where(ErrorLog.created_at >= since)
        )
        total = total_result.scalar() or 0

        # Unresolved errors
        unresolved_result = await self.db.execute(
            select(func.count(ErrorLog.id)).where(
                and_(
                    ErrorLog.created_at >= since,
                    ErrorLog.is_resolved == False  # noqa: E712
                )
            )
        )
        unresolved = unresolved_result.scalar() or 0

        # Errors by type
        type_result = await self.db.execute(
            select(ErrorLog.error_type, func.count(ErrorLog.id))
            .where(ErrorLog.created_at >= since)
            .group_by(ErrorLog.error_type)
            .order_by(func.count(ErrorLog.id).desc())
            .limit(10)
        )
        by_type = {row[0]: row[1] for row in type_result.all()}

        return {
            "total": total,
            "unresolved": unresolved,
            "resolved": total - unresolved,
            "by_type": by_type,
            "period_days": days
        }

    # =========================================================================
    # ANALYTICS
    # =========================================================================

    async def get_activity_stats(self, days: int = 30) -> dict:
        """Get activity statistics for the past N days."""
        since = datetime.utcnow() - timedelta(days=days)

        # Total activities
        total_result = await self.db.execute(
            select(func.count(ActivityLog.id)).where(ActivityLog.created_at >= since)
        )
        total = total_result.scalar() or 0

        # Activities by action
        action_result = await self.db.execute(
            select(ActivityLog.action, func.count(ActivityLog.id))
            .where(ActivityLog.created_at >= since)
            .group_by(ActivityLog.action)
            .order_by(func.count(ActivityLog.id).desc())
        )
        by_action = {row[0]: row[1] for row in action_result.all()}

        # Daily activity counts
        # Note: SQLite doesn't have DATE() function, use date() from func
        daily_result = await self.db.execute(
            select(
                func.date(ActivityLog.created_at).label("date"),
                func.count(ActivityLog.id)
            )
            .where(ActivityLog.created_at >= since)
            .group_by(func.date(ActivityLog.created_at))
            .order_by(func.date(ActivityLog.created_at))
        )
        daily = {str(row[0]): row[1] for row in daily_result.all()}

        # Active users (unique users with activities)
        active_users_result = await self.db.execute(
            select(func.count(func.distinct(ActivityLog.user_id)))
            .where(ActivityLog.created_at >= since)
        )
        active_users = active_users_result.scalar() or 0

        return {
            "total_activities": total,
            "by_action": by_action,
            "daily": daily,
            "active_users": active_users,
            "period_days": days
        }

    async def get_churn_risk_users(self, inactive_days: int = 14) -> list[User]:
        """Get users at risk of churning (inactive for X days)."""
        threshold = datetime.utcnow() - timedelta(days=inactive_days)

        result = await self.db.execute(
            select(User).where(
                and_(
                    User.is_active == True,  # noqa: E712
                    User.last_activity_at < threshold,
                    User.journey_stage != JourneyStage.CHURNED.value
                )
            ).order_by(User.last_activity_at.asc())
        )
        return list(result.scalars().all())

    async def mark_churned_users(self, inactive_days: int = 30) -> int:
        """Mark users as churned if inactive for X days."""
        threshold = datetime.utcnow() - timedelta(days=inactive_days)

        result = await self.db.execute(
            select(User).where(
                and_(
                    User.is_active == True,  # noqa: E712
                    User.last_activity_at < threshold,
                    User.journey_stage != JourneyStage.CHURNED.value
                )
            )
        )
        users = result.scalars().all()

        count = 0
        for user in users:
            await self.update_journey_stage(user.id, JourneyStage.CHURNED.value)
            count += 1

        return count
