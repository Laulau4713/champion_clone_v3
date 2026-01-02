"""
Admin Sessions Router.

Training session management endpoints for admin panel.
"""

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.admin.dependencies import require_admin
from database import get_db
from models import Champion, TrainingSession, User

logger = structlog.get_logger()

router = APIRouter(tags=["Admin - Sessions"])


@router.get("/sessions")
async def list_all_sessions(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    per_page: int = 10,
    status: str | None = None,
    champion_id: int | None = None,
):
    """List all training sessions with filtering."""
    per_page = min(per_page, 100)
    skip = (page - 1) * per_page

    query = select(TrainingSession, Champion.name).outerjoin(Champion, TrainingSession.champion_id == Champion.id)
    count_query = select(func.count(TrainingSession.id))

    if status:
        query = query.where(TrainingSession.status == status)
        count_query = count_query.where(TrainingSession.status == status)

    if champion_id:
        query = query.where(TrainingSession.champion_id == champion_id)
        count_query = count_query.where(TrainingSession.champion_id == champion_id)

    total = await db.scalar(count_query)

    result = await db.execute(query.order_by(TrainingSession.started_at.desc()).offset(skip).limit(per_page))
    rows = result.all()

    # Get user emails
    user_ids = set()
    for session, _ in rows:
        try:
            user_ids.add(int(session.user_id))
        except (ValueError, TypeError):
            pass

    users_map = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(list(user_ids))))
        for user in users_result.scalars().all():
            users_map[str(user.id)] = user.email

    logger.info("admin_sessions_listed", admin_id=admin.id, count=len(rows), page=page)

    return {
        "items": [
            {
                "id": session.id,
                "user_id": session.user_id,
                "user_email": users_map.get(session.user_id, session.user_id),
                "champion_id": session.champion_id,
                "champion_name": champion_name or f"Champion #{session.champion_id}",
                "score": session.overall_score,
                "status": session.status,
                "started_at": session.started_at.isoformat() if session.started_at else None,
            }
            for session, champion_name in rows
        ],
        "total": total or 0,
        "page": page,
        "per_page": per_page,
        "total_pages": ((total or 0) + per_page - 1) // per_page,
    }
