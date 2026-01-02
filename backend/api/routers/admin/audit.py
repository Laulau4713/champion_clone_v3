"""
Admin Audit Router.

Audit log viewing endpoints for admin panel.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.admin.dependencies import require_admin
from database import get_db
from models import AdminActionType, User
from services.audit import AuditService

logger = structlog.get_logger()

router = APIRouter(tags=["Admin - Audit"])


@router.get("/audit-logs")
async def list_audit_logs(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    admin_id: int | None = None,
    action: str | None = None,
    resource_type: str | None = None,
):
    """
    List all admin audit logs.

    Supports filtering by:
    - admin_id: Filter by specific admin
    - action: Filter by action type (e.g., 'user_update', 'webhook_create')
    - resource_type: Filter by resource type (e.g., 'user', 'webhook')
    """
    audit_service = AuditService(db)
    logs, total = await audit_service.get_logs(
        admin_id=admin_id, action=action, resource_type=resource_type, page=page, per_page=per_page
    )

    logger.info("admin_audit_logs_listed", admin_id=admin.id, count=len(logs))

    return {
        "items": [
            {
                "id": log.id,
                "admin_id": log.admin_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "available_actions": [a.value for a in AdminActionType],
    }


@router.get("/audit-logs/{log_id}")
async def get_audit_log(log_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Get detailed information about a specific audit log entry."""
    audit_service = AuditService(db)
    log = await audit_service.get_log(log_id)

    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    return {
        "id": log.id,
        "admin_id": log.admin_id,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "old_value": log.old_value,
        "new_value": log.new_value,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }
