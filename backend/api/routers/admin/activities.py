"""
Admin Activities Router.

Activity log endpoints for admin panel.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.admin.dependencies import require_admin
from database import get_db
from models import ActivityLog, User

router = APIRouter(tags=["Admin - Activities"])


@router.get("/activities")
async def list_activities(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    per_page: int = 50,
    user_id: int | None = None,
    action: str | None = None,
):
    """List activity logs with filtering."""
    per_page = min(per_page, 100)
    skip = (page - 1) * per_page

    query = select(ActivityLog)
    count_query = select(func.count(ActivityLog.id))

    if user_id:
        query = query.where(ActivityLog.user_id == user_id)
        count_query = count_query.where(ActivityLog.user_id == user_id)

    if action:
        query = query.where(ActivityLog.action == action)
        count_query = count_query.where(ActivityLog.action == action)

    total = await db.scalar(count_query)

    result = await db.execute(query.order_by(ActivityLog.created_at.desc()).offset(skip).limit(per_page))
    activities = result.scalars().all()

    return {
        "items": [
            {
                "id": a.id,
                "user_id": a.user_id,
                "action": a.action,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "extra_data": a.extra_data,
                "ip_address": a.ip_address,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in activities
        ],
        "total": total or 0,
        "page": page,
        "per_page": per_page,
        "total_pages": ((total or 0) + per_page - 1) // per_page,
    }
