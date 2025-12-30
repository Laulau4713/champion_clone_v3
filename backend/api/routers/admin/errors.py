"""
Admin Errors Router.

Error log management endpoints for admin panel.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import User, ErrorLog
from api.routers.admin.dependencies import require_admin
from api.routers.admin.schemas import ErrorResolveRequest
from services.activity import ActivityService

router = APIRouter(tags=["Admin - Errors"])


@router.get("/errors")
async def list_errors(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    per_page: int = 50,
    resolved: Optional[bool] = None,
    error_type: Optional[str] = None
):
    """List error logs with filtering."""
    activity_service = ActivityService(db)
    errors, total = await activity_service.get_errors(
        resolved=resolved,
        error_type=error_type,
        limit=per_page,
        offset=(page - 1) * per_page
    )

    return {
        "items": [
            {
                "id": e.id,
                "user_id": e.user_id,
                "error_type": e.error_type,
                "error_message": e.error_message,
                "endpoint": e.endpoint,
                "is_resolved": e.is_resolved,
                "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
                "resolution_notes": e.resolution_notes,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in errors
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }


@router.get("/errors/{error_id}")
async def get_error_detail(
    error_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get full error details including stack trace."""
    result = await db.execute(select(ErrorLog).where(ErrorLog.id == error_id))
    error = result.scalar_one_or_none()

    if not error:
        raise HTTPException(status_code=404, detail="Error not found")

    return {
        "id": error.id,
        "user_id": error.user_id,
        "error_type": error.error_type,
        "error_message": error.error_message,
        "stack_trace": error.stack_trace,
        "endpoint": error.endpoint,
        "request_data": error.request_data,
        "is_resolved": error.is_resolved,
        "resolved_at": error.resolved_at.isoformat() if error.resolved_at else None,
        "resolved_by": error.resolved_by,
        "resolution_notes": error.resolution_notes,
        "created_at": error.created_at.isoformat() if error.created_at else None
    }


@router.post("/errors/{error_id}/resolve")
async def resolve_error(
    error_id: int,
    body: ErrorResolveRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Mark an error as resolved."""
    activity_service = ActivityService(db)
    error = await activity_service.resolve_error(error_id, admin.id, body.resolution_notes)

    if not error:
        raise HTTPException(status_code=404, detail="Error not found")

    return {"status": "resolved", "error_id": error_id}
