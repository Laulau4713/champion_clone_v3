"""
Service de paiement LemonSqueezy.
DÉSACTIVÉ PAR DÉFAUT - Activer en ajoutant les clés API dans .env
"""

import hashlib
import hmac

import httpx
import structlog

from config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class PaymentService:
    """Gestion des paiements via LemonSqueezy."""

    BASE_URL = "https://api.lemonsqueezy.com/v1"

    def __init__(self):
        self._api_key = None
        self._webhook_secret = None
        self._store_id = None
        self._variants = {}
        self._initialized = False

    def _init_settings(self):
        """Initialize settings lazily to avoid import issues."""
        if self._initialized:
            return

        self._api_key = getattr(settings, "lemonsqueezy_api_key", "") or ""
        self._webhook_secret = getattr(settings, "lemonsqueezy_webhook_secret", "") or ""
        self._store_id = getattr(settings, "lemonsqueezy_store_id", "") or ""
        self._variants = {
            "starter": getattr(settings, "lemonsqueezy_variant_starter", "") or "",
            "pro": getattr(settings, "lemonsqueezy_variant_pro", "") or "",
            "enterprise": getattr(settings, "lemonsqueezy_variant_enterprise", "") or "",
        }
        self._initialized = True

    @property
    def api_key(self) -> str:
        self._init_settings()
        return self._api_key

    @property
    def webhook_secret(self) -> str:
        self._init_settings()
        return self._webhook_secret

    @property
    def store_id(self) -> str:
        self._init_settings()
        return self._store_id

    @property
    def variants(self) -> dict:
        self._init_settings()
        return self._variants

    def is_enabled(self) -> bool:
        """Vérifie si le paiement est configuré."""
        return bool(self.api_key)

    async def create_checkout(self, user_id: int, user_email: str, plan: str = "pro") -> dict | None:
        """
        Crée une session de checkout LemonSqueezy.

        Returns:
            {"checkout_url": "https://..."} ou None si désactivé
        """
        if not self.is_enabled():
            logger.info("payment_disabled", action="create_checkout")
            return None

        variant_id = self.variants.get(plan)
        if not variant_id:
            logger.error("unknown_plan", plan=plan)
            raise ValueError(f"Unknown plan: {plan}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/checkouts",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/vnd.api+json",
                        "Accept": "application/vnd.api+json",
                    },
                    json={
                        "data": {
                            "type": "checkouts",
                            "attributes": {"checkout_data": {"email": user_email, "custom": {"user_id": str(user_id)}}},
                            "relationships": {
                                "store": {"data": {"type": "stores", "id": self.store_id}},
                                "variant": {"data": {"type": "variants", "id": variant_id}},
                            },
                        }
                    },
                    timeout=30.0,
                )

                if response.status_code != 201:
                    logger.error("lemonsqueezy_checkout_error", status=response.status_code, response=response.text)
                    return None

                data = response.json()
                checkout_url = data["data"]["attributes"]["url"]

                logger.info("checkout_created", user_id=user_id, plan=plan)

                return {"checkout_url": checkout_url}

        except Exception as e:
            logger.error("checkout_error", error=str(e))
            return None

    async def get_subscription(self, subscription_id: str) -> dict | None:
        """Récupère les infos d'un abonnement."""
        if not self.is_enabled():
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/subscriptions/{subscription_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Accept": "application/vnd.api+json",
                    },
                    timeout=30.0,
                )

                if response.status_code != 200:
                    logger.error("get_subscription_error", subscription_id=subscription_id, status=response.status_code)
                    return None

                return response.json()["data"]

        except Exception as e:
            logger.error("get_subscription_error", error=str(e))
            return None

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Annule un abonnement."""
        if not self.is_enabled():
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.BASE_URL}/subscriptions/{subscription_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Accept": "application/vnd.api+json",
                    },
                    timeout=30.0,
                )

                success = response.status_code == 200

                if success:
                    logger.info("subscription_cancelled", subscription_id=subscription_id)
                else:
                    logger.error(
                        "cancel_subscription_error", subscription_id=subscription_id, status=response.status_code
                    )

                return success

        except Exception as e:
            logger.error("cancel_subscription_error", error=str(e))
            return False

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Vérifie la signature du webhook LemonSqueezy."""
        if not self.webhook_secret:
            logger.warning("webhook_secret_not_configured")
            return False

        try:
            expected = hmac.new(self.webhook_secret.encode(), payload, hashlib.sha256).hexdigest()

            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.error("webhook_verify_error", error=str(e))
            return False


# Singleton instance
payment_service = PaymentService()
