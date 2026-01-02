"""
Admin Alerts Router.

Admin alerts management endpoints for admin panel.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.admin.dependencies import require_admin
from database import get_db
from models import AdminAlert, User

router = APIRouter(tags=["Admin - Alerts"])


@router.get("/alerts")
async def list_alerts(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    per_page: int = 20,
    unread_only: bool = False,
):
    """List admin alerts."""
    per_page = min(per_page, 100)
    skip = (page - 1) * per_page

    query = select(AdminAlert)
    count_query = select(func.count(AdminAlert.id))

    if unread_only:
        query = query.where(AdminAlert.is_read == False)  # noqa: E712
        count_query = count_query.where(AdminAlert.is_read == False)  # noqa: E712

    total = await db.scalar(count_query)

    result = await db.execute(query.order_by(AdminAlert.created_at.desc()).offset(skip).limit(per_page))
    alerts = result.scalars().all()

    return {
        "items": [
            {
                "id": a.id,
                "type": a.type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "extra_data": a.extra_data,
                "is_read": a.is_read,
                "is_dismissed": a.is_dismissed,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ],
        "total": total or 0,
        "page": page,
        "per_page": per_page,
        "total_pages": ((total or 0) + per_page - 1) // per_page,
    }


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Mark an alert as read."""
    result = await db.execute(select(AdminAlert).where(AdminAlert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    await db.commit()

    return {"status": "read", "alert_id": alert_id}


@router.post("/alerts/{alert_id}/dismiss")
async def dismiss_alert(alert_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Dismiss an alert."""
    result = await db.execute(select(AdminAlert).where(AdminAlert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_dismissed = True
    alert.dismissed_by = admin.id
    alert.dismissed_at = datetime.utcnow()
    await db.commit()

    return {"status": "dismissed", "alert_id": alert_id}


@router.post("/alerts/read-all")
async def mark_all_alerts_read(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Mark all alerts as read."""
    result = await db.execute(
        select(AdminAlert).where(AdminAlert.is_read == False)  # noqa: E712
    )
    alerts = result.scalars().all()

    for alert in alerts:
        alert.is_read = True

    await db.commit()

    return {"status": "all_read", "count": len(alerts)}
