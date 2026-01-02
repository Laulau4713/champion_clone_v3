"""
Admin Notes Router.

Admin notes management endpoints for admin panel.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.admin.dependencies import require_admin
from api.routers.admin.schemas import AdminNoteRequest
from config import get_settings
from database import get_db
from models import AdminActionType, AdminNote, User
from services.audit import AuditService

logger = structlog.get_logger()
settings = get_settings()

# Rate limiter for admin endpoints
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Admin - Notes"])


@router.get("/users/{user_id}/notes")
async def list_user_notes(user_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """List all admin notes for a user."""
    result = await db.execute(
        select(AdminNote)
        .where(AdminNote.user_id == user_id)
        .order_by(AdminNote.is_pinned.desc(), AdminNote.created_at.desc())
    )
    notes = result.scalars().all()

    return {
        "items": [
            {
                "id": n.id,
                "content": n.content,
                "is_pinned": n.is_pinned,
                "admin_id": n.admin_id,
                "created_at": n.created_at.isoformat() if n.created_at else None,
                "updated_at": n.updated_at.isoformat() if n.updated_at else None,
            }
            for n in notes
        ]
    }


@router.post("/users/{user_id}/notes")
@limiter.limit(settings.RATE_LIMIT_ADMIN_WRITE)
async def create_user_note(
    request: Request,
    user_id: int,
    body: AdminNoteRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add a note to a user."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    note = AdminNote(user_id=user_id, admin_id=admin.id, content=body.content, is_pinned=body.is_pinned)
    db.add(note)
    await db.commit()
    await db.refresh(note)

    logger.info("admin_note_created", admin_id=admin.id, user_id=user_id, note_id=note.id)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_action(
        admin=admin,
        action=AdminActionType.NOTE_CREATE.value,
        resource_type="admin_note",
        resource_id=note.id,
        old_value=None,
        new_value={
            "user_id": user_id,
            "content": note.content[:100] + "..." if len(note.content) > 100 else note.content,
            "is_pinned": note.is_pinned,
        },
        request=request,
    )

    return {"status": "created", "note_id": note.id}


@router.patch("/notes/{note_id}")
@limiter.limit(settings.RATE_LIMIT_ADMIN_WRITE)
async def update_note(
    request: Request,
    note_id: int,
    body: AdminNoteRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update an admin note."""
    result = await db.execute(select(AdminNote).where(AdminNote.id == note_id))
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Capture old values for audit
    old_values = {
        "content": note.content[:100] + "..." if len(note.content) > 100 else note.content,
        "is_pinned": note.is_pinned,
    }

    note.content = body.content
    note.is_pinned = body.is_pinned
    await db.commit()

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_action(
        admin=admin,
        action=AdminActionType.NOTE_UPDATE.value,
        resource_type="admin_note",
        resource_id=note_id,
        old_value=old_values,
        new_value={
            "content": body.content[:100] + "..." if len(body.content) > 100 else body.content,
            "is_pinned": body.is_pinned,
        },
        request=request,
    )

    return {"status": "updated", "note_id": note_id}


@router.delete("/notes/{note_id}")
@limiter.limit(settings.RATE_LIMIT_ADMIN_DELETE)
async def delete_note(
    request: Request, note_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Delete an admin note."""
    result = await db.execute(select(AdminNote).where(AdminNote.id == note_id))
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Capture old values for audit before deletion
    old_values = {
        "user_id": note.user_id,
        "content": note.content[:100] + "..." if len(note.content) > 100 else note.content,
        "is_pinned": note.is_pinned,
    }

    await db.delete(note)
    await db.commit()

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_action(
        admin=admin,
        action=AdminActionType.NOTE_DELETE.value,
        resource_type="admin_note",
        resource_id=note_id,
        old_value=old_values,
        new_value=None,
        request=request,
    )

    return {"status": "deleted", "note_id": note_id}
