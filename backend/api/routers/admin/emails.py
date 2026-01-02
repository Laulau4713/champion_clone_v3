"""
Admin Email Router.

Email template and log management endpoints for admin panel.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.admin.dependencies import require_admin
from api.routers.admin.schemas import EmailTemplateRequest, EmailTemplateUpdateRequest
from config import get_settings
from database import get_db
from models import AdminActionType, User
from services.audit import AuditService
from services.email import EmailService

logger = structlog.get_logger()
settings = get_settings()

# Rate limiter for admin endpoints
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Admin - Emails"])


@router.get("/email-templates")
async def list_email_templates(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """List all email templates."""
    email_service = EmailService(db)
    templates = await email_service.get_templates()

    return {
        "items": [
            {
                "id": t.id,
                "trigger": t.trigger,
                "subject": t.subject,
                "is_active": t.is_active,
                "variables": t.variables,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in templates
        ]
    }


@router.get("/email-templates/{template_id}")
async def get_email_template(
    template_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Get full email template details."""
    email_service = EmailService(db)
    template = await email_service.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "id": template.id,
        "trigger": template.trigger,
        "subject": template.subject,
        "body_html": template.body_html,
        "body_text": template.body_text,
        "is_active": template.is_active,
        "variables": template.variables,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }


@router.post("/email-templates")
@limiter.limit(settings.RATE_LIMIT_ADMIN_WRITE)
async def create_email_template(
    request: Request,
    body: EmailTemplateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new email template."""
    email_service = EmailService(db)

    # Check if trigger already exists
    existing = await email_service.get_template_by_trigger(body.trigger)
    if existing:
        raise HTTPException(status_code=400, detail="Template for this trigger already exists")

    template = await email_service.create_template(
        trigger=body.trigger,
        subject=body.subject,
        body_html=body.body_html,
        body_text=body.body_text,
        variables=body.variables,
        is_active=body.is_active,
    )

    logger.info("email_template_created", admin_id=admin.id, template_id=template.id)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_action(
        admin=admin,
        action=AdminActionType.EMAIL_TEMPLATE_CREATE.value,
        resource_type="email_template",
        resource_id=template.id,
        old_value=None,
        new_value={
            "trigger": template.trigger,
            "subject": template.subject,
            "is_active": template.is_active,
            "variables": template.variables,
        },
        request=request,
    )

    return {"status": "created", "template_id": template.id}


@router.patch("/email-templates/{template_id}")
@limiter.limit(settings.RATE_LIMIT_ADMIN_WRITE)
async def update_email_template(
    request: Request,
    template_id: int,
    body: EmailTemplateUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update an email template."""
    email_service = EmailService(db)

    # Get old values for audit
    old_template = await email_service.get_template(template_id)
    if not old_template:
        raise HTTPException(status_code=404, detail="Template not found")

    old_values = {
        "subject": old_template.subject,
        "is_active": old_template.is_active,
        "variables": old_template.variables,
    }

    template = await email_service.update_template(
        template_id=template_id,
        subject=body.subject,
        body_html=body.body_html,
        body_text=body.body_text,
        variables=body.variables,
        is_active=body.is_active,
    )

    logger.info("email_template_updated", admin_id=admin.id, template_id=template_id)

    # Build new values from what was actually changed
    new_values = {}
    if body.subject is not None:
        new_values["subject"] = body.subject
    if body.is_active is not None:
        new_values["is_active"] = body.is_active
    if body.variables is not None:
        new_values["variables"] = body.variables
    if body.body_html is not None:
        new_values["body_html_changed"] = True
    if body.body_text is not None:
        new_values["body_text_changed"] = True

    # Audit log
    if new_values:
        audit_service = AuditService(db)
        await audit_service.log_action(
            admin=admin,
            action=AdminActionType.EMAIL_TEMPLATE_UPDATE.value,
            resource_type="email_template",
            resource_id=template_id,
            old_value={k: old_values.get(k) for k in new_values if k in old_values},
            new_value=new_values,
            request=request,
        )

    return {"status": "updated", "template_id": template_id}


@router.delete("/email-templates/{template_id}")
@limiter.limit(settings.RATE_LIMIT_ADMIN_DELETE)
async def delete_email_template(
    request: Request, template_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Delete an email template."""
    email_service = EmailService(db)

    # Get old values for audit before deletion
    old_template = await email_service.get_template(template_id)
    if not old_template:
        raise HTTPException(status_code=404, detail="Template not found")

    old_values = {"trigger": old_template.trigger, "subject": old_template.subject, "is_active": old_template.is_active}

    success = await email_service.delete_template(template_id)

    logger.info("email_template_deleted", admin_id=admin.id, template_id=template_id)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_action(
        admin=admin,
        action=AdminActionType.EMAIL_TEMPLATE_DELETE.value,
        resource_type="email_template",
        resource_id=template_id,
        old_value=old_values,
        new_value=None,
        request=request,
    )

    return {"status": "deleted", "template_id": template_id}


@router.post("/email-templates/{template_id}/send-test")
async def send_test_email(template_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Send a test email to the admin."""
    email_service = EmailService(db)
    template = await email_service.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    log = await email_service.send_email(admin.id, template.trigger)

    if not log:
        raise HTTPException(status_code=500, detail="Failed to send test email")

    return {"status": "sent", "email_log_id": log.id, "to": admin.email}


@router.get("/email-logs")
async def list_email_logs(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    per_page: int = 50,
    user_id: int | None = None,
    trigger: str | None = None,
    status: str | None = None,
):
    """List email logs with filtering."""
    email_service = EmailService(db)
    logs, total = await email_service.get_email_logs(
        user_id=user_id, trigger=trigger, status=status, limit=per_page, offset=(page - 1) * per_page
    )

    return {
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "trigger": log.trigger,
                "to_email": log.to_email,
                "subject": log.subject,
                "status": log.status,
                "opened_at": log.opened_at.isoformat() if log.opened_at else None,
                "clicked_at": log.clicked_at.isoformat() if log.clicked_at else None,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }
