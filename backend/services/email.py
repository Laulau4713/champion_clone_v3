"""
Email automation service.
Handles email template management and sending.
"""

import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from models import User, EmailTemplate, EmailLog, EmailTrigger
from config import get_settings

logger = structlog.get_logger(__name__)


class EmailService:
    """Service for email automation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    # =========================================================================
    # TEMPLATE MANAGEMENT
    # =========================================================================

    async def get_templates(self) -> list[EmailTemplate]:
        """Get all email templates."""
        result = await self.db.execute(
            select(EmailTemplate).order_by(EmailTemplate.trigger)
        )
        return list(result.scalars().all())

    async def get_template(self, template_id: int) -> Optional[EmailTemplate]:
        """Get a template by ID."""
        result = await self.db.execute(
            select(EmailTemplate).where(EmailTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_template_by_trigger(self, trigger: str) -> Optional[EmailTemplate]:
        """Get a template by trigger type."""
        result = await self.db.execute(
            select(EmailTemplate).where(EmailTemplate.trigger == trigger)
        )
        return result.scalar_one_or_none()

    async def create_template(
        self,
        trigger: str,
        subject: str,
        body_html: str,
        body_text: str,
        variables: Optional[list[str]] = None,
        is_active: bool = True
    ) -> EmailTemplate:
        """Create a new email template."""
        template = EmailTemplate(
            trigger=trigger,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            variables=variables,
            is_active=is_active
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update_template(
        self,
        template_id: int,
        subject: Optional[str] = None,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        variables: Optional[list[str]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[EmailTemplate]:
        """Update an email template."""
        template = await self.get_template(template_id)
        if not template:
            return None

        if subject is not None:
            template.subject = subject
        if body_html is not None:
            template.body_html = body_html
        if body_text is not None:
            template.body_text = body_text
        if variables is not None:
            template.variables = variables
        if is_active is not None:
            template.is_active = is_active

        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete_template(self, template_id: int) -> bool:
        """Delete an email template."""
        template = await self.get_template(template_id)
        if not template:
            return False

        await self.db.delete(template)
        await self.db.commit()
        return True

    # =========================================================================
    # EMAIL SENDING
    # =========================================================================

    def _render_template(
        self,
        content: str,
        variables: dict
    ) -> str:
        """Render template with variables."""
        rendered = content
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        return rendered

    async def send_email(
        self,
        user_id: int,
        trigger: str,
        variables: Optional[dict] = None
    ) -> Optional[EmailLog]:
        """Send an email using a template."""
        # Get user
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            logger.warning("user_not_found", user_id=user_id)
            return None

        # Get template
        template = await self.get_template_by_trigger(trigger)
        if not template or not template.is_active:
            logger.warning("template_not_found_or_inactive", trigger=trigger)
            return None

        # Prepare variables
        all_vars = {
            "user_name": user.full_name or user.email.split("@")[0],
            "user_email": user.email,
            "app_name": "Champion Clone",
            "app_url": self.settings.cors_origins.split(",")[0] if self.settings.cors_origins else "http://localhost:3000"
        }
        if variables:
            all_vars.update(variables)

        # Render content
        subject = self._render_template(template.subject, all_vars)
        body_html = self._render_template(template.body_html, all_vars)
        body_text = self._render_template(template.body_text, all_vars)

        # Create log entry
        email_log = EmailLog(
            user_id=user_id,
            template_id=template.id,
            trigger=trigger,
            to_email=user.email,
            subject=subject,
            status="pending"
        )
        self.db.add(email_log)
        await self.db.commit()
        await self.db.refresh(email_log)

        # Send email
        try:
            if self.settings.smtp_host:
                await self._send_smtp(user.email, subject, body_html, body_text)
                email_log.status = "sent"
            else:
                # No SMTP configured, just log
                logger.info(
                    "email_simulated",
                    to=user.email,
                    subject=subject,
                    trigger=trigger
                )
                email_log.status = "sent"
                email_log.extra_data = {"simulated": True}

        except Exception as e:
            email_log.status = "failed"
            email_log.error_message = str(e)
            logger.error("email_send_failed", error=str(e), user_id=user_id)

        await self.db.commit()
        await self.db.refresh(email_log)
        return email_log

    async def _send_smtp(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str
    ):
        """Send email via SMTP."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.settings.smtp_from or f"noreply@{self.settings.smtp_host}"
        msg["To"] = to_email

        part1 = MIMEText(body_text, "plain")
        part2 = MIMEText(body_html, "html")

        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port or 587) as server:
            if self.settings.smtp_tls:
                server.starttls()
            if self.settings.smtp_user and self.settings.smtp_password:
                server.login(self.settings.smtp_user, self.settings.smtp_password)
            server.sendmail(msg["From"], to_email, msg.as_string())

    # =========================================================================
    # TRIGGER AUTOMATION
    # =========================================================================

    async def trigger_email(
        self,
        trigger: EmailTrigger,
        user_id: int,
        variables: Optional[dict] = None
    ) -> Optional[EmailLog]:
        """Trigger an automated email."""
        return await self.send_email(user_id, trigger.value, variables)

    async def send_welcome_email(self, user_id: int) -> Optional[EmailLog]:
        """Send welcome email to new user."""
        return await self.trigger_email(EmailTrigger.WELCOME, user_id)

    async def send_first_champion_email(self, user_id: int, champion_name: str) -> Optional[EmailLog]:
        """Send email when user creates first champion."""
        return await self.trigger_email(
            EmailTrigger.FIRST_CHAMPION,
            user_id,
            {"champion_name": champion_name}
        )

    async def send_first_session_email(self, user_id: int, score: float) -> Optional[EmailLog]:
        """Send email when user completes first training session."""
        return await self.trigger_email(
            EmailTrigger.FIRST_SESSION,
            user_id,
            {"score": f"{score:.1f}"}
        )

    async def send_inactive_reminder(self, user_id: int, days_inactive: int) -> Optional[EmailLog]:
        """Send reminder email to inactive user."""
        if days_inactive >= 30:
            trigger = EmailTrigger.INACTIVE_30_DAYS
        elif days_inactive >= 7:
            trigger = EmailTrigger.INACTIVE_7_DAYS
        else:
            trigger = EmailTrigger.INACTIVE_3_DAYS

        return await self.trigger_email(trigger, user_id, {"days_inactive": days_inactive})

    # =========================================================================
    # EMAIL LOGS
    # =========================================================================

    async def get_email_logs(
        self,
        user_id: Optional[int] = None,
        trigger: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[EmailLog], int]:
        """Get email logs with optional filtering."""
        query = select(EmailLog)
        count_query = select(func.count(EmailLog.id))

        if user_id:
            query = query.where(EmailLog.user_id == user_id)
            count_query = count_query.where(EmailLog.user_id == user_id)

        if trigger:
            query = query.where(EmailLog.trigger == trigger)
            count_query = count_query.where(EmailLog.trigger == trigger)

        if status:
            query = query.where(EmailLog.status == status)
            count_query = count_query.where(EmailLog.status == status)

        query = query.order_by(EmailLog.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return logs, total

    async def get_email_stats(self) -> dict:
        """Get email delivery statistics."""
        # Total sent
        sent_result = await self.db.execute(
            select(func.count(EmailLog.id)).where(EmailLog.status == "sent")
        )
        sent = sent_result.scalar() or 0

        # Failed
        failed_result = await self.db.execute(
            select(func.count(EmailLog.id)).where(EmailLog.status == "failed")
        )
        failed = failed_result.scalar() or 0

        # Opened
        opened_result = await self.db.execute(
            select(func.count(EmailLog.id)).where(EmailLog.opened_at.isnot(None))
        )
        opened = opened_result.scalar() or 0

        # Clicked
        clicked_result = await self.db.execute(
            select(func.count(EmailLog.id)).where(EmailLog.clicked_at.isnot(None))
        )
        clicked = clicked_result.scalar() or 0

        # By trigger
        trigger_result = await self.db.execute(
            select(EmailLog.trigger, func.count(EmailLog.id))
            .group_by(EmailLog.trigger)
            .order_by(func.count(EmailLog.id).desc())
        )
        by_trigger = {row[0]: row[1] for row in trigger_result.all()}

        total = sent + failed
        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "opened": opened,
            "clicked": clicked,
            "open_rate": round((opened / sent * 100) if sent > 0 else 0, 1),
            "click_rate": round((clicked / sent * 100) if sent > 0 else 0, 1),
            "delivery_rate": round((sent / total * 100) if total > 0 else 0, 1),
            "by_trigger": by_trigger
        }

    async def mark_opened(self, email_id: int) -> bool:
        """Mark an email as opened (for tracking pixel)."""
        result = await self.db.execute(
            select(EmailLog).where(EmailLog.id == email_id)
        )
        email = result.scalar_one_or_none()
        if not email:
            return False

        if not email.opened_at:
            email.opened_at = datetime.utcnow()
            email.status = "opened"
            await self.db.commit()

        return True

    async def mark_clicked(self, email_id: int) -> bool:
        """Mark an email as clicked."""
        result = await self.db.execute(
            select(EmailLog).where(EmailLog.id == email_id)
        )
        email = result.scalar_one_or_none()
        if not email:
            return False

        if not email.clicked_at:
            email.clicked_at = datetime.utcnow()
            email.status = "clicked"
            if not email.opened_at:
                email.opened_at = datetime.utcnow()
            await self.db.commit()

        return True
