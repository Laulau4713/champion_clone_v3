"""
Admin Router Module.

Combines all admin sub-routers into a single admin router.

Structure:
- stats.py: Dashboard & statistics endpoints (6 endpoints)
- users.py: User management endpoints (5 endpoints)
- sessions.py: Training sessions endpoints (1 endpoint)
- activities.py: Activity log endpoints (1 endpoint)
- errors.py: Error log endpoints (3 endpoints)
- emails.py: Email template & log endpoints (7 endpoints)
- webhooks.py: Webhook endpoints (10 endpoints)
- notes.py: Admin notes endpoints (4 endpoints)
- alerts.py: Admin alerts endpoints (4 endpoints)

Total: 39 endpoints
"""

from fastapi import APIRouter

# Import sub-routers
from api.routers.admin.stats import router as stats_router
from api.routers.admin.users import router as users_router
from api.routers.admin.sessions import router as sessions_router
from api.routers.admin.activities import router as activities_router
from api.routers.admin.errors import router as errors_router
from api.routers.admin.emails import router as emails_router
from api.routers.admin.webhooks import router as webhooks_router
from api.routers.admin.notes import router as notes_router
from api.routers.admin.alerts import router as alerts_router
from api.routers.admin.audit import router as audit_router

# Export schemas and dependencies for external use
from api.routers.admin.schemas import (
    UserUpdateRequest,
    EmailTemplateRequest,
    EmailTemplateUpdateRequest,
    WebhookEndpointRequest,
    WebhookEndpointUpdateRequest,
    AdminNoteRequest,
    ErrorResolveRequest
)
from api.routers.admin.dependencies import require_admin

# Create main router
router = APIRouter(prefix="/admin", tags=["Admin"])

# Include all sub-routers
router.include_router(stats_router)
router.include_router(users_router)
router.include_router(sessions_router)
router.include_router(activities_router)
router.include_router(errors_router)
router.include_router(emails_router)
router.include_router(webhooks_router)
router.include_router(notes_router)
router.include_router(alerts_router)
router.include_router(audit_router)

__all__ = [
    "router",
    "require_admin",
    "UserUpdateRequest",
    "EmailTemplateRequest",
    "EmailTemplateUpdateRequest",
    "WebhookEndpointRequest",
    "WebhookEndpointUpdateRequest",
    "AdminNoteRequest",
    "ErrorResolveRequest"
]
