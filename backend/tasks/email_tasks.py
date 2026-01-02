"""
Email Tasks - Celery tasks for email notifications
===================================================

Handles:
- Transactional emails (welcome, password reset)
- Marketing emails (inactive reminders)
- Notification emails (session completed, achievement unlocked)
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog
from celery import shared_task

logger = structlog.get_logger()

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@champion-clone.com")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"


# =============================================================================
# BASE EMAIL SENDING
# =============================================================================


@shared_task(
    bind=True,
    autoretry_for=(smtplib.SMTPException,),
    max_retries=3,
    retry_backoff=True,
    rate_limit="60/m",  # 60 emails per minute max
)
def send_email(self, to: str, subject: str, html_body: str, text_body: str = None):
    """
    Send email via SMTP.

    Args:
        to: Recipient email address
        subject: Email subject
        html_body: HTML content
        text_body: Plain text content (optional)

    Returns:
        dict: {"success": bool, "message_id": str}
    """
    if not SMTP_USER:
        logger.warning("smtp_not_configured", to=to)
        return {"success": False, "error": "SMTP not configured"}

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to

        # Add text version
        if text_body:
            msg.attach(MIMEText(text_body, "plain"))

        # Add HTML version
        msg.attach(MIMEText(html_body, "html"))

        # Send
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            if SMTP_USE_TLS:
                server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to], msg.as_string())

        logger.info("email_sent", to=to, subject=subject)

        return {"success": True, "to": to}

    except smtplib.SMTPException as e:
        logger.error("email_failed", to=to, error=str(e))
        raise


# =============================================================================
# WELCOME EMAIL
# =============================================================================


@shared_task(bind=True)
def send_welcome_email(self, user_email: str, user_name: str):
    """Send welcome email to new user."""
    subject = "Bienvenue sur Champion Clone !"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #3b82f6;">Bienvenue, {user_name} !</h1>

            <p>Merci de rejoindre Champion Clone, la plateforme d'entraînement commercial propulsée par l'IA.</p>

            <h2>Pour commencer :</h2>
            <ol>
                <li><strong>Uploadez une vidéo</strong> d'un de vos meilleurs commerciaux</li>
                <li><strong>Laissez l'IA analyser</strong> les techniques de vente</li>
                <li><strong>Entraînez-vous</strong> avec des scénarios personnalisés</li>
            </ol>

            <a href="https://champion-clone.com/dashboard"
               style="display: inline-block; padding: 12px 24px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px;">
                Accéder à mon dashboard
            </a>

            <p style="margin-top: 30px; color: #666; font-size: 14px;">
                Des questions ? Répondez à cet email ou contactez-nous à support@champion-clone.com
            </p>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    Bienvenue, {user_name} !

    Merci de rejoindre Champion Clone.

    Pour commencer :
    1. Uploadez une vidéo d'un de vos meilleurs commerciaux
    2. Laissez l'IA analyser les techniques de vente
    3. Entraînez-vous avec des scénarios personnalisés

    Accédez à votre dashboard : https://champion-clone.com/dashboard
    """

    return send_email.delay(user_email, subject, html_body, text_body)


# =============================================================================
# INACTIVE USER REMINDERS
# =============================================================================


@shared_task(bind=True)
def send_inactive_user_reminders(self, days_inactive: int = 7):
    """
    Send reminder emails to inactive users.
    Called daily by Celery Beat.
    """
    # This would query the database for inactive users
    # For now, just log
    logger.info("inactive_reminders_check", days=days_inactive)

    # TODO: Implement database query
    # async with AsyncSessionLocal() as db:
    #     cutoff = datetime.utcnow() - timedelta(days=days_inactive)
    #     users = await db.execute(
    #         select(User).where(User.last_login < cutoff)
    #     )
    #     for user in users.scalars():
    #         send_inactive_reminder.delay(user.email, user.first_name)

    return {"status": "checked", "days": days_inactive}


@shared_task(bind=True)
def send_inactive_reminder(self, user_email: str, user_name: str, days: int = 7):
    """Send individual inactive reminder."""
    subject = f"Vous nous manquez, {user_name} !"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #3b82f6;">Bonjour {user_name},</h1>

            <p>Cela fait {days} jours que vous n'avez pas utilisé Champion Clone.</p>

            <p>Vos compétences commerciales n'attendent que vous !</p>

            <h2>Cette semaine sur Champion Clone :</h2>
            <ul>
                <li>Nouveaux scénarios d'entraînement</li>
                <li>Améliorations de l'IA coach</li>
                <li>Nouveaux badges à débloquer</li>
            </ul>

            <a href="https://champion-clone.com/training"
               style="display: inline-block; padding: 12px 24px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px;">
                Reprendre mon entraînement
            </a>

            <p style="margin-top: 30px; color: #666; font-size: 14px;">
                <a href="https://champion-clone.com/unsubscribe">Se désabonner</a>
            </p>
        </div>
    </body>
    </html>
    """

    return send_email.delay(user_email, subject, html_body)


# =============================================================================
# ACHIEVEMENT UNLOCKED
# =============================================================================


@shared_task(bind=True)
def send_achievement_email(self, user_email: str, user_name: str, achievement_name: str, xp_earned: int):
    """Send email when user unlocks achievement."""
    subject = f"Nouveau badge débloqué : {achievement_name} !"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; text-align: center;">
            <h1 style="color: #f59e0b;">Félicitations {user_name} !</h1>

            <div style="font-size: 64px; margin: 20px 0;">🏆</div>

            <h2>Vous avez débloqué :</h2>
            <p style="font-size: 24px; font-weight: bold; color: #3b82f6;">{achievement_name}</p>

            <p style="font-size: 18px;">+{xp_earned} XP</p>

            <a href="https://champion-clone.com/achievements"
               style="display: inline-block; padding: 12px 24px; background: #f59e0b; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px;">
                Voir mes trophées
            </a>
        </div>
    </body>
    </html>
    """

    return send_email.delay(user_email, subject, html_body)
