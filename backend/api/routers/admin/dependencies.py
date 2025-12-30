"""
Admin dependencies.
"""

from fastapi import Depends, HTTPException
import structlog

from models import User
from api.routers.auth import get_current_user

logger = structlog.get_logger()


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that requires admin role."""
    if current_user.role != "admin":
        logger.warning("admin_access_denied", user_id=current_user.id, role=current_user.role)
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
