"""
Payments API Router - LemonSqueezy Integration.

Disabled by default - requires LEMONSQUEEZY_API_KEY in .env
"""

from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from database import get_db
from models import SubscriptionEvent, SubscriptionPlan, SubscriptionStatus, User
from schemas import SuccessResponse
from services.payment_service import payment_service

logger = structlog.get_logger()

router = APIRouter(prefix="/payments", tags=["Payments"])


# =============================================================================
# SCHEMAS
# =============================================================================


from pydantic import BaseModel


class PaymentStatusResponse(BaseModel):
    """Payment system status."""

    enabled: bool
    plan: str
    status: str
    subscription_id: str | None = None
    expires_at: datetime | None = None


class CheckoutRequest(BaseModel):
    """Checkout request."""

    plan: str = "pro"  # starter, pro, enterprise


class CheckoutResponse(BaseModel):
    """Checkout response."""

    checkout_url: str | None = None
    message: str


class SubscriptionResponse(BaseModel):
    """Subscription details."""

    plan: str
    status: str
    subscription_id: str | None = None
    started_at: datetime | None = None
    expires_at: datetime | None = None
    cancel_at_period_end: bool = False


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/status", response_model=PaymentStatusResponse)
async def get_payment_status(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Get current payment/subscription status.

    Returns whether payments are enabled and user's subscription info.
    """
    return PaymentStatusResponse(
        enabled=payment_service.is_enabled(),
        plan=current_user.subscription_plan,
        status=current_user.subscription_status,
        subscription_id=current_user.stripe_customer_id,  # Using existing field for now
        expires_at=current_user.subscription_expires_at,
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CheckoutRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Create a LemonSqueezy checkout session.

    Returns checkout URL to redirect user to payment page.
    Returns message if payments are disabled.
    """
    if not payment_service.is_enabled():
        return CheckoutResponse(
            checkout_url=None, message="Le paiement n'est pas encore configuré. Contactez l'administrateur."
        )

    # Don't allow checkout if already subscribed
    if current_user.subscription_plan != SubscriptionPlan.FREE.value:
        if current_user.subscription_status == SubscriptionStatus.ACTIVE.value:
            return CheckoutResponse(checkout_url=None, message="Vous avez déjà un abonnement actif.")

    result = await payment_service.create_checkout(
        user_id=current_user.id, user_email=current_user.email, plan=request.plan
    )

    if result is None:
        return CheckoutResponse(
            checkout_url=None, message="Erreur lors de la création du checkout. Réessayez plus tard."
        )

    logger.info("checkout_created", user_id=current_user.id, plan=request.plan)

    return CheckoutResponse(checkout_url=result["checkout_url"], message="Redirection vers le paiement...")


@router.post("/webhook")
async def handle_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handle LemonSqueezy webhooks.

    Processes subscription events:
    - subscription_created
    - subscription_updated
    - subscription_cancelled
    - subscription_payment_failed
    """
    if not payment_service.is_enabled():
        raise HTTPException(status_code=503, detail="Payments not configured")

    # Get signature from header
    signature = request.headers.get("X-Signature", "")
    if not signature:
        logger.warning("webhook_missing_signature")
        raise HTTPException(status_code=400, detail="Missing signature")

    # Get raw body
    body = await request.body()

    # Verify signature
    if not payment_service.verify_webhook(body, signature):
        logger.warning("webhook_invalid_signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse payload
    import json

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_name = payload.get("meta", {}).get("event_name")
    data = payload.get("data", {})
    attributes = data.get("attributes", {})

    logger.info("webhook_received", event=event_name)

    # Get user_id from custom data
    custom_data = attributes.get("first_subscription_item", {}).get("custom_data", {})
    if not custom_data:
        custom_data = attributes.get("custom_data", {})

    user_id_str = custom_data.get("user_id")
    if not user_id_str:
        logger.warning("webhook_missing_user_id", payload=payload)
        # Still return 200 to acknowledge receipt
        return {"status": "ok", "message": "No user_id in custom_data"}

    try:
        user_id = int(user_id_str)
    except ValueError:
        logger.warning("webhook_invalid_user_id", user_id=user_id_str)
        return {"status": "ok", "message": "Invalid user_id"}

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("webhook_user_not_found", user_id=user_id)
        return {"status": "ok", "message": "User not found"}

    subscription_id = str(data.get("id", ""))

    # Handle events
    if event_name == "subscription_created":
        # New subscription
        variant_id = str(attributes.get("variant_id", ""))
        plan = _variant_to_plan(variant_id)

        user.subscription_plan = plan
        user.subscription_status = SubscriptionStatus.ACTIVE.value
        user.subscription_started_at = datetime.utcnow()
        user.stripe_customer_id = subscription_id  # Store subscription ID

        # Log event
        event = SubscriptionEvent(
            user_id=user.id,
            event_type="subscription_created",
            from_plan=SubscriptionPlan.FREE.value,
            to_plan=plan,
            extra_data={"subscription_id": subscription_id},
        )
        db.add(event)

        logger.info("subscription_created", user_id=user.id, plan=plan, subscription_id=subscription_id)

    elif event_name == "subscription_updated":
        # Plan change or renewal
        variant_id = str(attributes.get("variant_id", ""))
        new_plan = _variant_to_plan(variant_id)
        status = attributes.get("status", "active")

        old_plan = user.subscription_plan
        user.subscription_plan = new_plan
        user.subscription_status = _map_status(status)

        # Parse ends_at if present
        ends_at = attributes.get("ends_at")
        if ends_at:
            try:
                user.subscription_expires_at = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        # Log event
        event = SubscriptionEvent(
            user_id=user.id,
            event_type="subscription_updated",
            from_plan=old_plan,
            to_plan=new_plan,
            extra_data={"subscription_id": subscription_id, "status": status},
        )
        db.add(event)

        logger.info("subscription_updated", user_id=user.id, old_plan=old_plan, new_plan=new_plan, status=status)

    elif event_name == "subscription_cancelled":
        # Subscription cancelled (may still be active until period end)
        user.subscription_status = SubscriptionStatus.CANCELLED.value

        ends_at = attributes.get("ends_at")
        if ends_at:
            try:
                user.subscription_expires_at = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        # Log event
        event = SubscriptionEvent(
            user_id=user.id,
            event_type="subscription_cancelled",
            from_plan=user.subscription_plan,
            to_plan=user.subscription_plan,  # Plan stays until expiry
            extra_data={"subscription_id": subscription_id},
        )
        db.add(event)

        logger.info("subscription_cancelled", user_id=user.id, plan=user.subscription_plan)

    elif event_name in ("subscription_payment_failed", "subscription_expired"):
        # Payment failed or expired
        user.subscription_status = (
            SubscriptionStatus.PAST_DUE.value
            if event_name == "subscription_payment_failed"
            else SubscriptionStatus.EXPIRED.value
        )

        if event_name == "subscription_expired":
            # Downgrade to free
            old_plan = user.subscription_plan
            user.subscription_plan = SubscriptionPlan.FREE.value

            event = SubscriptionEvent(
                user_id=user.id,
                event_type="subscription_expired",
                from_plan=old_plan,
                to_plan=SubscriptionPlan.FREE.value,
                extra_data={"subscription_id": subscription_id},
            )
            db.add(event)

        logger.info(event_name, user_id=user.id, plan=user.subscription_plan)

    await db.commit()

    return {"status": "ok"}


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Get detailed subscription information.
    """
    cancel_at_period_end = current_user.subscription_status == SubscriptionStatus.CANCELLED.value

    return SubscriptionResponse(
        plan=current_user.subscription_plan,
        status=current_user.subscription_status,
        subscription_id=current_user.stripe_customer_id,
        started_at=current_user.subscription_started_at,
        expires_at=current_user.subscription_expires_at,
        cancel_at_period_end=cancel_at_period_end,
    )


@router.post("/cancel", response_model=SuccessResponse)
async def cancel_subscription(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Cancel current subscription.

    Subscription remains active until the end of the billing period.
    """
    if not payment_service.is_enabled():
        raise HTTPException(status_code=503, detail="Le paiement n'est pas configuré")

    if current_user.subscription_plan == SubscriptionPlan.FREE.value:
        raise HTTPException(status_code=400, detail="Vous n'avez pas d'abonnement actif")

    subscription_id = current_user.stripe_customer_id
    if not subscription_id:
        raise HTTPException(status_code=400, detail="Aucun abonnement trouvé")

    success = await payment_service.cancel_subscription(subscription_id)

    if not success:
        raise HTTPException(status_code=500, detail="Erreur lors de l'annulation. Contactez le support.")

    # Update local status (webhook will also update, but this is immediate feedback)
    current_user.subscription_status = SubscriptionStatus.CANCELLED.value
    await db.commit()

    logger.info("subscription_cancel_requested", user_id=current_user.id, subscription_id=subscription_id)

    return SuccessResponse(success=True, message="Votre abonnement sera annulé à la fin de la période de facturation.")


# =============================================================================
# HELPERS
# =============================================================================


def _variant_to_plan(variant_id: str) -> str:
    """Map LemonSqueezy variant ID to plan name."""
    from config import get_settings

    settings = get_settings()

    if variant_id == settings.LEMONSQUEEZY_VARIANT_STARTER:
        return SubscriptionPlan.STARTER.value
    elif variant_id == settings.LEMONSQUEEZY_VARIANT_PRO:
        return SubscriptionPlan.PRO.value
    elif variant_id == settings.LEMONSQUEEZY_VARIANT_ENTERPRISE:
        return SubscriptionPlan.ENTERPRISE.value
    else:
        return SubscriptionPlan.PRO.value  # Default


def _map_status(ls_status: str) -> str:
    """Map LemonSqueezy status to our status."""
    mapping = {
        "active": SubscriptionStatus.ACTIVE.value,
        "cancelled": SubscriptionStatus.CANCELLED.value,
        "past_due": SubscriptionStatus.PAST_DUE.value,
        "expired": SubscriptionStatus.EXPIRED.value,
        "on_trial": SubscriptionStatus.TRIAL.value,
        "paused": SubscriptionStatus.CANCELLED.value,  # Treat paused as cancelled
    }
    return mapping.get(ls_status, SubscriptionStatus.ACTIVE.value)
