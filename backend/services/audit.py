"""
Admin Audit Log Service.

Provides audit logging for all admin actions to track who did what, when.
"""

from typing import Any

import structlog
from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import AdminAuditLog, User

logger = structlog.get_logger()


class AuditService:
    """Service for logging admin actions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        admin: User,
        action: str,
        resource_type: str,
        resource_id: int | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        request: Request | None = None,
    ) -> AdminAuditLog:
        """
        Log an admin action.

        Args:
            admin: The admin user performing the action
            action: The action type (e.g., 'user_update', 'webhook_create')
            resource_type: Type of resource affected (e.g., 'user', 'webhook')
            resource_id: ID of the affected resource
            old_value: Previous state (for updates/deletes)
            new_value: New state (for creates/updates)
            request: Optional request object for IP/user-agent

        Returns:
            The created audit log entry
        """
        ip_address = None
        user_agent = None

        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("User-Agent", "")[:500]

        audit_log = AdminAuditLog(
            admin_id=admin.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        logger.info(
            "admin_audit_logged", admin_id=admin.id, action=action, resource_type=resource_type, resource_id=resource_id
        )

        return audit_log

    async def get_logs(
        self,
        admin_id: int | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[AdminAuditLog], int]:
        """
        Get audit logs with optional filtering.

        Returns:
            Tuple of (logs, total_count)
        """
        per_page = min(per_page, 100)
        skip = (page - 1) * per_page

        query = select(AdminAuditLog)
        count_query = select(func.count(AdminAuditLog.id))

        if admin_id:
            query = query.where(AdminAuditLog.admin_id == admin_id)
            count_query = count_query.where(AdminAuditLog.admin_id == admin_id)

        if action:
            query = query.where(AdminAuditLog.action == action)
            count_query = count_query.where(AdminAuditLog.action == action)

        if resource_type:
            query = query.where(AdminAuditLog.resource_type == resource_type)
            count_query = count_query.where(AdminAuditLog.resource_type == resource_type)

        total = await self.db.scalar(count_query)

        result = await self.db.execute(query.order_by(AdminAuditLog.created_at.desc()).offset(skip).limit(per_page))
        logs = result.scalars().all()

        return list(logs), total or 0

    async def get_log(self, log_id: int) -> AdminAuditLog | None:
        """Get a specific audit log entry."""
        return await self.db.get(AdminAuditLog, log_id)


def serialize_for_audit(obj: Any) -> dict:
    """
    Serialize an object for audit logging.

    Only includes relevant fields, excluding sensitive data.
    """
    if obj is None:
        return None

    if hasattr(obj, "__dict__"):
        # SQLAlchemy model
        result = {}
        for key, value in vars(obj).items():
            if key.startswith("_"):
                continue
            # Skip sensitive fields
            if key in ("hashed_password", "password"):
                continue
            # Convert datetime to ISO string
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            # Skip relationships
            if hasattr(value, "__tablename__"):
                continue
            result[key] = value
        return result

    return obj
