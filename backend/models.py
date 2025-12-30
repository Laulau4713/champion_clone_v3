"""
SQLAlchemy models for Champion Clone MVP.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import String, Text, DateTime, Integer, Float, ForeignKey, JSON, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database import Base


# =============================================================================
# ENUMS
# =============================================================================

class SubscriptionPlan(str, PyEnum):
    """Subscription plans available."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, PyEnum):
    """Status of a subscription."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    EXPIRED = "expired"
    TRIAL = "trial"


class EmailTrigger(str, PyEnum):
    """Email automation triggers."""
    WELCOME = "welcome"
    FIRST_CHAMPION = "first_champion"
    FIRST_SESSION = "first_session"
    INACTIVE_3_DAYS = "inactive_3_days"
    INACTIVE_7_DAYS = "inactive_7_days"
    INACTIVE_30_DAYS = "inactive_30_days"
    SUBSCRIPTION_REMINDER = "subscription_reminder"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    WEEKLY_SUMMARY = "weekly_summary"
    MILESTONE_10_SESSIONS = "milestone_10_sessions"
    MILESTONE_50_SESSIONS = "milestone_50_sessions"


class ActivityAction(str, PyEnum):
    """Types of user activities."""
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    UPLOAD_VIDEO = "upload_video"
    START_ANALYSIS = "start_analysis"
    COMPLETE_ANALYSIS = "complete_analysis"
    START_TRAINING = "start_training"
    COMPLETE_TRAINING = "complete_training"
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_CHAMPION = "view_champion"
    DELETE_CHAMPION = "delete_champion"
    UPDATE_PROFILE = "update_profile"
    SUBSCRIPTION_CHANGE = "subscription_change"


class JourneyStage(str, PyEnum):
    """User journey stages in the funnel."""
    REGISTERED = "registered"
    FIRST_LOGIN = "first_login"
    FIRST_UPLOAD = "first_upload"
    FIRST_ANALYSIS = "first_analysis"
    FIRST_TRAINING = "first_training"
    ACTIVE_USER = "active_user"       # 3+ sessions
    POWER_USER = "power_user"         # 10+ sessions
    CHURNED = "churned"               # 30+ days inactive


class User(Base):
    """
    User account for authentication.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)  # "user" | "admin"

    # Subscription fields
    subscription_plan: Mapped[str] = mapped_column(
        String(20), default=SubscriptionPlan.FREE.value, nullable=False
    )
    subscription_status: Mapped[str] = mapped_column(
        String(20), default=SubscriptionStatus.ACTIVE.value, nullable=False
    )
    subscription_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Activity tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Journey stage
    journey_stage: Mapped[str] = mapped_column(
        String(30), default=JourneyStage.REGISTERED.value, nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    activities: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="user", cascade="all, delete-orphan"
    )
    journey_events: Mapped[list["UserJourney"]] = relationship(
        "UserJourney", back_populates="user", cascade="all, delete-orphan"
    )
    subscription_events: Mapped[list["SubscriptionEvent"]] = relationship(
        "SubscriptionEvent", back_populates="user", cascade="all, delete-orphan"
    )
    email_logs: Mapped[list["EmailLog"]] = relationship(
        "EmailLog", back_populates="user", cascade="all, delete-orphan"
    )
    admin_notes: Mapped[list["AdminNote"]] = relationship(
        "AdminNote", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"


class Champion(Base):
    """
    Represents a sales champion whose patterns are extracted from videos.
    """
    __tablename__ = "champions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Owner
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # File paths
    video_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Processed content
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Extracted patterns stored as JSON
    patterns_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Generated scenarios stored as JSON
    scenarios_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Processing status
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False
    )  # pending, processing, ready, error

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    sessions: Mapped[list["TrainingSession"]] = relationship(
        "TrainingSession",
        back_populates="champion",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Champion(id={self.id}, name='{self.name}', status='{self.status}')>"


class TrainingSession(Base):
    """
    Represents a training session where a user practices against a champion's patterns.
    """
    __tablename__ = "training_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # User identifier (simplified for MVP - no auth)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, default="anonymous")

    # Champion being trained against
    champion_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("champions.id", ondelete="CASCADE"),
        nullable=False
    )

    # Training scenario
    # Structure: {
    #   "context": "...",
    #   "prospect_type": "...",
    #   "challenge": "...",
    #   "objectives": [...]
    # }
    scenario: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Conversation history
    # Structure: [
    #   {"role": "champion|user", "content": "...", "timestamp": "...", "feedback": "...", "score": 0-10}
    # ]
    messages: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Session scoring
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Session status
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False
    )  # active, completed, abandoned

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    champion: Mapped["Champion"] = relationship(
        "Champion",
        back_populates="sessions"
    )

    def __repr__(self) -> str:
        return f"<TrainingSession(id={self.id}, champion_id={self.champion_id}, status='{self.status}')>"


class RefreshToken(Base):
    """
    Stored refresh tokens for JWT authentication.
    Storing tokens allows us to:
    - Revoke tokens (logout, security breach)
    - Track active sessions
    - Implement "logout from all devices"
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Token identifier (not the full token - we store a hash for security)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # User who owns this token
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Token metadata
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Device/session info (optional, for "active sessions" feature)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 max length

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship("User", backref="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.is_revoked})>"


class AnalysisLog(Base):
    """
    Logs for tracking pattern analysis jobs.
    Useful for debugging and monitoring.
    """
    __tablename__ = "analysis_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    champion_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("champions.id", ondelete="CASCADE"),
        nullable=False
    )

    # Analysis details
    step: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # started, completed, error
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<AnalysisLog(champion_id={self.champion_id}, step='{self.step}', status='{self.status}')>"


# =============================================================================
# SESSION 6B: ADMIN ANALYTICS MODELS
# =============================================================================

class ActivityLog(Base):
    """
    Tracks all user activities for analytics and debugging.
    """
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # champion, session, etc.
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="activities")

    def __repr__(self) -> str:
        return f"<ActivityLog(user_id={self.user_id}, action='{self.action}')>"


class UserJourney(Base):
    """
    Tracks user progression through the funnel stages.
    """
    __tablename__ = "user_journeys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    stage: Mapped[str] = mapped_column(String(30), nullable=False)
    previous_stage: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="journey_events")

    def __repr__(self) -> str:
        return f"<UserJourney(user_id={self.user_id}, stage='{self.stage}')>"


class ErrorLog(Base):
    """
    Tracks application errors for debugging.
    """
    __tablename__ = "error_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    error_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    endpoint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    request_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(default=False, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    def __repr__(self) -> str:
        return f"<ErrorLog(id={self.id}, type='{self.error_type}')>"


class SubscriptionEvent(Base):
    """
    Tracks subscription changes for billing analytics.
    """
    __tablename__ = "subscription_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # upgrade, downgrade, cancel, renew
    from_plan: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    to_plan: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    stripe_event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="subscription_events")

    def __repr__(self) -> str:
        return f"<SubscriptionEvent(user_id={self.user_id}, type='{self.event_type}')>"


class EmailTemplate(Base):
    """
    Email templates for automation.
    """
    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trigger: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    variables: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of available template variables
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<EmailTemplate(trigger='{self.trigger}')>"


class EmailLog(Base):
    """
    Tracks sent emails for deliverability monitoring.
    """
    __tablename__ = "email_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    template_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("email_templates.id", ondelete="SET NULL"),
        nullable=True
    )
    trigger: Mapped[str] = mapped_column(String(50), nullable=False)
    to_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, sent, failed, opened, clicked
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="email_logs")

    def __repr__(self) -> str:
        return f"<EmailLog(user_id={self.user_id}, trigger='{self.trigger}', status='{self.status}')>"


class WebhookEndpoint(Base):
    """
    Configured webhook endpoints for external integrations.
    """
    __tablename__ = "webhook_endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)  # For HMAC signature
    events: Mapped[list] = mapped_column(JSON, nullable=False)  # List of events to send
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationship
    logs: Mapped[list["WebhookLog"]] = relationship(
        "WebhookLog", back_populates="endpoint", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<WebhookEndpoint(name='{self.name}', url='{self.url}')>"


class WebhookLog(Base):
    """
    Tracks webhook delivery attempts.
    """
    __tablename__ = "webhook_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    endpoint_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("webhook_endpoints.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    event: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, success, failed
    response_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship
    endpoint: Mapped["WebhookEndpoint"] = relationship("WebhookEndpoint", back_populates="logs")

    def __repr__(self) -> str:
        return f"<WebhookLog(endpoint_id={self.endpoint_id}, event='{self.event}', status='{self.status}')>"


class AdminNote(Base):
    """
    Admin notes on users for CRM functionality.
    """
    __tablename__ = "admin_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    admin_id: Mapped[int] = mapped_column(Integer, nullable=False)  # ID of admin who wrote the note
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="admin_notes")

    def __repr__(self) -> str:
        return f"<AdminNote(user_id={self.user_id}, admin_id={self.admin_id})>"


class AdminAlert(Base):
    """
    System alerts for admin attention.
    """
    __tablename__ = "admin_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # error_spike, churn_risk, payment_failed, etc.
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)  # info, warning, critical
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_dismissed: Mapped[bool] = mapped_column(default=False, nullable=False)
    dismissed_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<AdminAlert(type='{self.type}', severity='{self.severity}')>"


class AdminActionType(str, PyEnum):
    """Types of admin actions for audit logging."""
    # User management
    USER_UPDATE = "user_update"
    USER_ROLE_CHANGE = "user_role_change"
    USER_STATUS_CHANGE = "user_status_change"
    USER_SUBSCRIPTION_CHANGE = "user_subscription_change"

    # Content management
    EMAIL_TEMPLATE_CREATE = "email_template_create"
    EMAIL_TEMPLATE_UPDATE = "email_template_update"
    EMAIL_TEMPLATE_DELETE = "email_template_delete"

    # Webhook management
    WEBHOOK_CREATE = "webhook_create"
    WEBHOOK_UPDATE = "webhook_update"
    WEBHOOK_DELETE = "webhook_delete"
    WEBHOOK_SECRET_REGENERATE = "webhook_secret_regenerate"

    # Notes and alerts
    NOTE_CREATE = "note_create"
    NOTE_UPDATE = "note_update"
    NOTE_DELETE = "note_delete"
    ALERT_DISMISS = "alert_dismiss"

    # Error resolution
    ERROR_RESOLVE = "error_resolve"


class AdminAuditLog(Base):
    """
    Audit log for all admin actions.

    Tracks who did what, when, and to whom/what for compliance and debugging.
    """
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,  # Nullable in case admin is deleted
        index=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # user, webhook, email_template, etc.
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    old_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Previous state
    new_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # New state
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # Relationship
    admin: Mapped[Optional["User"]] = relationship("User", foreign_keys=[admin_id])

    def __repr__(self) -> str:
        return f"<AdminAuditLog(admin_id={self.admin_id}, action='{self.action}', resource='{self.resource_type}:{self.resource_id}')>"
