"""
Admin Webhooks Router.

Webhook endpoint and log management for admin panel.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.admin.dependencies import require_admin
from api.routers.admin.schemas import WebhookEndpointRequest, WebhookEndpointUpdateRequest
from config import get_settings
from database import get_db
from models import AdminActionType, User
from services.audit import AuditService
from services.webhooks import WebhookService

logger = structlog.get_logger()
settings = get_settings()

# Rate limiter for admin endpoints
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Admin - Webhooks"])


@router.get("/webhooks")
async def list_webhook_endpoints(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """List all webhook endpoints."""
    webhook_service = WebhookService(db)
    endpoints = await webhook_service.get_endpoints()

    return {
        "items": [
            {
                "id": e.id,
                "name": e.name,
                "url": e.url,
                "events": e.events,
                "is_active": e.is_active,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in endpoints
        ],
        "available_events": WebhookService.EVENTS,
    }


@router.get("/webhooks/{endpoint_id}")
async def get_webhook_endpoint(
    endpoint_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Get webhook endpoint details (includes secret)."""
    webhook_service = WebhookService(db)
    endpoint = await webhook_service.get_endpoint(endpoint_id)

    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    return {
        "id": endpoint.id,
        "name": endpoint.name,
        "url": endpoint.url,
        "secret": endpoint.secret,
        "events": endpoint.events,
        "is_active": endpoint.is_active,
        "created_at": endpoint.created_at.isoformat() if endpoint.created_at else None,
        "updated_at": endpoint.updated_at.isoformat() if endpoint.updated_at else None,
    }


@router.post("/webhooks")
@limiter.limit(settings.RATE_LIMIT_ADMIN_WRITE)
async def create_webhook_endpoint(
    request: Request,
    body: WebhookEndpointRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new webhook endpoint."""
    webhook_service = WebhookService(db)

    # Validate events
    invalid_events = set(body.events) - set(WebhookService.EVENTS)
    if invalid_events:
        raise HTTPException(
            status_code=400, detail=f"Invalid events: {invalid_events}. Valid events: {WebhookService.EVENTS}"
        )

    endpoint = await webhook_service.create_endpoint(
        name=body.name, url=body.url, events=body.events, is_active=body.is_active
    )

    logger.info("webhook_endpoint_created", admin_id=admin.id, endpoint_id=endpoint.id)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_action(
        admin=admin,
        action=AdminActionType.WEBHOOK_CREATE.value,
        resource_type="webhook_endpoint",
        resource_id=endpoint.id,
        old_value=None,
        new_value={
            "name": endpoint.name,
            "url": endpoint.url,
            "events": endpoint.events,
            "is_active": endpoint.is_active,
        },
        request=request,
    )

    return {"status": "created", "endpoint_id": endpoint.id, "secret": endpoint.secret}


@router.patch("/webhooks/{endpoint_id}")
@limiter.limit(settings.RATE_LIMIT_ADMIN_WRITE)
async def update_webhook_endpoint(
    request: Request,
    endpoint_id: int,
    body: WebhookEndpointUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a webhook endpoint."""
    webhook_service = WebhookService(db)

    # Get old values for audit
    old_endpoint = await webhook_service.get_endpoint(endpoint_id)
    if not old_endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    old_values = {
        "name": old_endpoint.name,
        "url": old_endpoint.url,
        "events": old_endpoint.events,
        "is_active": old_endpoint.is_active,
    }

    # Validate events if provided
    if body.events:
        invalid_events = set(body.events) - set(WebhookService.EVENTS)
        if invalid_events:
            raise HTTPException(status_code=400, detail=f"Invalid events: {invalid_events}")

    endpoint = await webhook_service.update_endpoint(
        endpoint_id=endpoint_id, name=body.name, url=body.url, events=body.events, is_active=body.is_active
    )

    logger.info("webhook_endpoint_updated", admin_id=admin.id, endpoint_id=endpoint_id)

    # Build new values from what was actually changed
    new_values = {}
    if body.name is not None:
        new_values["name"] = body.name
    if body.url is not None:
        new_values["url"] = body.url
    if body.events is not None:
        new_values["events"] = body.events
    if body.is_active is not None:
        new_values["is_active"] = body.is_active

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_action(
        admin=admin,
        action=AdminActionType.WEBHOOK_UPDATE.value,
        resource_type="webhook_endpoint",
        resource_id=endpoint_id,
        old_value={k: old_values[k] for k in new_values},
        new_value=new_values,
        request=request,
    )

    return {"status": "updated", "endpoint_id": endpoint_id}


@router.delete("/webhooks/{endpoint_id}")
@limiter.limit(settings.RATE_LIMIT_ADMIN_DELETE)
async def delete_webhook_endpoint(
    request: Request, endpoint_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Delete a webhook endpoint."""
    webhook_service = WebhookService(db)

    # Get old values for audit before deletion
    old_endpoint = await webhook_service.get_endpoint(endpoint_id)
    if not old_endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    old_values = {
        "name": old_endpoint.name,
        "url": old_endpoint.url,
        "events": old_endpoint.events,
        "is_active": old_endpoint.is_active,
    }

    success = await webhook_service.delete_endpoint(endpoint_id)

    logger.info("webhook_endpoint_deleted", admin_id=admin.id, endpoint_id=endpoint_id)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_action(
        admin=admin,
        action=AdminActionType.WEBHOOK_DELETE.value,
        resource_type="webhook_endpoint",
        resource_id=endpoint_id,
        old_value=old_values,
        new_value=None,
        request=request,
    )

    return {"status": "deleted", "endpoint_id": endpoint_id}


@router.post("/webhooks/{endpoint_id}/regenerate-secret")
@limiter.limit(settings.RATE_LIMIT_ADMIN_WRITE)
async def regenerate_webhook_secret(
    request: Request, endpoint_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Regenerate the secret for a webhook endpoint."""
    webhook_service = WebhookService(db)

    # Get endpoint info for audit
    endpoint = await webhook_service.get_endpoint(endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    new_secret = await webhook_service.regenerate_secret(endpoint_id)

    logger.info("webhook_secret_regenerated", admin_id=admin.id, endpoint_id=endpoint_id)

    # Audit log (don't log actual secrets for security)
    audit_service = AuditService(db)
    await audit_service.log_action(
        admin=admin,
        action=AdminActionType.WEBHOOK_SECRET_REGENERATE.value,
        resource_type="webhook_endpoint",
        resource_id=endpoint_id,
        old_value={"name": endpoint.name, "secret": "[REDACTED]"},
        new_value={"name": endpoint.name, "secret": "[REGENERATED]"},
        request=request,
    )

    return {"status": "regenerated", "secret": new_secret}


@router.post("/webhooks/{endpoint_id}/test")
async def test_webhook_endpoint(
    endpoint_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Send a test event to a webhook endpoint."""
    webhook_service = WebhookService(db)
    endpoint = await webhook_service.get_endpoint(endpoint_id)

    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    logs = await webhook_service.send_event(
        "test.ping", {"message": "Test webhook from Champion Clone", "admin_id": admin.id}, endpoint_id=endpoint_id
    )

    if not logs:
        raise HTTPException(status_code=500, detail="Failed to send test webhook")

    log = logs[0]
    return {"status": log.status, "response_code": log.response_code, "error_message": log.error_message}


@router.get("/webhook-logs")
async def list_webhook_logs(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    per_page: int = 50,
    endpoint_id: int | None = None,
    event: str | None = None,
    status: str | None = None,
):
    """List webhook logs with filtering."""
    webhook_service = WebhookService(db)
    logs, total = await webhook_service.get_logs(
        endpoint_id=endpoint_id, event=event, status=status, limit=per_page, offset=(page - 1) * per_page
    )

    return {
        "items": [
            {
                "id": log.id,
                "endpoint_id": log.endpoint_id,
                "event": log.event,
                "status": log.status,
                "response_code": log.response_code,
                "error_message": log.error_message,
                "attempts": log.attempts,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.post("/webhook-logs/{log_id}/retry")
async def retry_webhook(log_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Retry a failed webhook delivery."""
    webhook_service = WebhookService(db)
    log = await webhook_service.retry_webhook(log_id)

    if not log:
        raise HTTPException(status_code=404, detail="Log not found or already succeeded")

    return {"status": log.status, "response_code": log.response_code, "attempts": log.attempts}
