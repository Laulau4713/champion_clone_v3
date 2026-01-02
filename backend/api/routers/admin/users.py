"""
Admin Users Router.

User management endpoints for admin panel.
"""

from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.admin.dependencies import require_admin
from api.routers.admin.schemas import UserUpdateRequest
from config import get_settings
from database import get_db
from models import (
    ActivityLog,
    AdminActionType,
    AdminNote,
    Champion,
    SubscriptionEvent,
    SubscriptionPlan,
    SubscriptionStatus,
    TrainingSession,
    User,
)
from services.activity import ActivityService
from services.audit import AuditService

logger = structlog.get_logger()
settings = get_settings()

# Rate limiter for admin endpoints
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Admin - Users"])


@router.get("/users")
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    per_page: int = 10,
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    subscription_plan: str | None = None,
    journey_stage: str | None = None,
):
    """List all users with pagination and filtering."""
    per_page = min(per_page, 100)
    skip = (page - 1) * per_page

    query = select(User)
    count_query = select(func.count(User.id))

    # Apply filters
    if search:
        search_filter = User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)

    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    if subscription_plan:
        query = query.where(User.subscription_plan == subscription_plan)
        count_query = count_query.where(User.subscription_plan == subscription_plan)

    if journey_stage:
        query = query.where(User.journey_stage == journey_stage)
        count_query = count_query.where(User.journey_stage == journey_stage)

    total = await db.scalar(count_query)

    result = await db.execute(query.order_by(User.created_at.desc()).offset(skip).limit(per_page))
    users = result.scalars().all()

    logger.info("admin_users_listed", admin_id=admin.id, count=len(users), page=page)

    return {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "subscription_plan": u.subscription_plan,
                "subscription_status": u.subscription_status,
                "journey_stage": u.journey_stage,
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                "last_activity_at": u.last_activity_at.isoformat() if u.last_activity_at else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total or 0,
        "page": page,
        "per_page": per_page,
        "total_pages": ((total or 0) + per_page - 1) // per_page,
    }


@router.get("/users/churn-risk")
async def get_churn_risk_users(
    days: int = Query(14, ge=1, le=90), admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """Get users at risk of churning (inactive for X days)."""
    activity_service = ActivityService(db)
    users = await activity_service.get_churn_risk_users(days)

    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "subscription_plan": u.subscription_plan,
                "journey_stage": u.journey_stage,
                "last_activity_at": u.last_activity_at.isoformat() if u.last_activity_at else None,
                "days_inactive": (datetime.utcnow() - u.last_activity_at).days if u.last_activity_at else None,
            }
            for u in users
        ],
        "count": len(users),
        "threshold_days": days,
    }


@router.get("/users/{user_id}")
async def get_user_detail(user_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Get detailed information about a specific user."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user's champions
    champions_result = await db.execute(select(Champion).where(Champion.user_id == user_id))
    champions = champions_result.scalars().all()

    # Get user's sessions
    sessions_result = await db.execute(
        select(TrainingSession)
        .where(TrainingSession.user_id == str(user_id))
        .order_by(TrainingSession.started_at.desc())
        .limit(20)
    )
    sessions = sessions_result.scalars().all()

    # Get recent activities
    activities_result = await db.execute(
        select(ActivityLog).where(ActivityLog.user_id == user_id).order_by(ActivityLog.created_at.desc()).limit(20)
    )
    activities = activities_result.scalars().all()

    # Get admin notes
    notes_result = await db.execute(
        select(AdminNote)
        .where(AdminNote.user_id == user_id)
        .order_by(AdminNote.is_pinned.desc(), AdminNote.created_at.desc())
    )
    notes = notes_result.scalars().all()

    # Calculate stats
    session_scores = [s.overall_score for s in sessions if s.overall_score is not None]
    avg_score = sum(session_scores) / len(session_scores) if session_scores else 0

    logger.info("admin_user_detail_fetched", admin_id=admin.id, target_user_id=user_id)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "subscription_plan": user.subscription_plan,
            "subscription_status": user.subscription_status,
            "subscription_started_at": user.subscription_started_at.isoformat()
            if user.subscription_started_at
            else None,
            "subscription_expires_at": user.subscription_expires_at.isoformat()
            if user.subscription_expires_at
            else None,
            "journey_stage": user.journey_stage,
            "login_count": user.login_count,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "last_activity_at": user.last_activity_at.isoformat() if user.last_activity_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "champions": [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in champions
        ],
        "sessions": [
            {
                "id": s.id,
                "champion_id": s.champion_id,
                "score": s.overall_score,
                "status": s.status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
            }
            for s in sessions
        ],
        "activities": [
            {
                "id": a.id,
                "action": a.action,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in activities
        ],
        "notes": [
            {
                "id": n.id,
                "content": n.content,
                "is_pinned": n.is_pinned,
                "admin_id": n.admin_id,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notes
        ],
        "stats": {"total_champions": len(champions), "total_sessions": len(sessions), "avg_score": round(avg_score, 1)},
    }


@router.patch("/users/{user_id}")
@limiter.limit(settings.RATE_LIMIT_ADMIN_WRITE)
async def update_user(
    request: Request,
    user_id: int,
    body: UserUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's status, role, or subscription."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from demoting/deactivating themselves
    if user.id == admin.id:
        if body.role and body.role != "admin":
            raise HTTPException(status_code=400, detail="Cannot demote yourself")
        if body.is_active is False:
            raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    # Capture old values for audit log
    old_values = {
        "is_active": user.is_active,
        "role": user.role,
        "subscription_plan": user.subscription_plan,
        "subscription_status": user.subscription_status,
    }
    new_values = {}

    # Apply updates
    if body.is_active is not None:
        new_values["is_active"] = body.is_active
        user.is_active = body.is_active
        logger.info("admin_user_status_changed", admin_id=admin.id, target_user_id=user_id, is_active=body.is_active)

    if body.role is not None:
        if body.role not in ["user", "admin"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        new_values["role"] = body.role
        user.role = body.role
        logger.info("admin_user_role_changed", admin_id=admin.id, target_user_id=user_id, role=body.role)

    if body.subscription_plan is not None:
        valid_plans = [p.value for p in SubscriptionPlan]
        if body.subscription_plan not in valid_plans:
            raise HTTPException(status_code=400, detail=f"Invalid plan. Must be one of: {valid_plans}")
        new_values["subscription_plan"] = body.subscription_plan
        old_plan = user.subscription_plan
        user.subscription_plan = body.subscription_plan

        # Log subscription event
        event = SubscriptionEvent(
            user_id=user_id,
            event_type="admin_change",
            from_plan=old_plan,
            to_plan=body.subscription_plan,
            extra_data={"admin_id": admin.id},
        )
        db.add(event)
        logger.info(
            "admin_subscription_changed", admin_id=admin.id, target_user_id=user_id, plan=body.subscription_plan
        )

    if body.subscription_status is not None:
        valid_statuses = [s.value for s in SubscriptionStatus]
        if body.subscription_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        new_values["subscription_status"] = body.subscription_status
        user.subscription_status = body.subscription_status

    await db.commit()

    # Log to audit trail
    if new_values:
        audit_service = AuditService(db)
        await audit_service.log_action(
            admin=admin,
            action=AdminActionType.USER_UPDATE.value,
            resource_type="user",
            resource_id=user_id,
            old_value={k: old_values[k] for k in new_values},
            new_value=new_values,
            request=request,
        )

    return {"status": "updated", "user_id": user_id}
