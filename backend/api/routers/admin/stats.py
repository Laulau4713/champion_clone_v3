"""
Admin Statistics Router.

Dashboard & statistics endpoints for admin panel.
"""

from datetime import datetime, timedelta

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.admin.dependencies import require_admin
from database import get_db
from models import AdminAlert, Champion, SubscriptionPlan, TrainingSession, User
from services.activity import ActivityService
from services.email import EmailService
from services.webhooks import WebhookService

logger = structlog.get_logger()

router = APIRouter(tags=["Admin - Stats"])


@router.get("/stats")
async def get_admin_stats(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Get global statistics for admin dashboard."""
    # Total counts
    users_count = await db.scalar(select(func.count(User.id)))
    champions_count = await db.scalar(select(func.count(Champion.id)))
    sessions_count = await db.scalar(select(func.count(TrainingSession.id)))

    # Average score
    avg_score = await db.scalar(
        select(func.avg(TrainingSession.overall_score)).where(TrainingSession.overall_score.isnot(None))
    )

    # Stats for last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = await db.scalar(select(func.count(User.id)).where(User.created_at >= week_ago))
    sessions_week = await db.scalar(
        select(func.count(TrainingSession.id)).where(TrainingSession.started_at >= week_ago)
    )

    # Subscription breakdown
    subscription_stats = {}
    for plan in SubscriptionPlan:
        count = await db.scalar(select(func.count(User.id)).where(User.subscription_plan == plan.value))
        subscription_stats[plan.value] = count or 0

    # Unread alerts
    unread_alerts = await db.scalar(
        select(func.count(AdminAlert.id)).where(AdminAlert.is_read == False)  # noqa: E712
    )

    logger.info("admin_stats_fetched", admin_id=admin.id)

    return {
        "total_users": users_count or 0,
        "total_champions": champions_count or 0,
        "total_sessions": sessions_count or 0,
        "avg_score": round(avg_score or 0, 1),
        "new_users_week": new_users_week or 0,
        "sessions_week": sessions_week or 0,
        "subscriptions": subscription_stats,
        "unread_alerts": unread_alerts or 0,
    }


@router.get("/stats/funnel")
async def get_funnel_stats(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Get user funnel conversion statistics."""
    activity_service = ActivityService(db)
    return await activity_service.get_funnel_stats()


@router.get("/stats/activity")
async def get_activity_stats(
    days: int = Query(30, ge=1, le=365), admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Get activity statistics for the past N days."""
    activity_service = ActivityService(db)
    return await activity_service.get_activity_stats(days)


@router.get("/stats/errors")
async def get_error_stats(
    days: int = Query(7, ge=1, le=365), admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Get error statistics for the past N days."""
    activity_service = ActivityService(db)
    return await activity_service.get_error_stats(days)


@router.get("/stats/emails")
async def get_email_stats(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Get email delivery statistics."""
    email_service = EmailService(db)
    return await email_service.get_email_stats()


@router.get("/stats/webhooks")
async def get_webhook_stats(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Get webhook delivery statistics."""
    webhook_service = WebhookService(db)
    return await webhook_service.get_webhook_stats()
