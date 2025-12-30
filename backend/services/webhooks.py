"""
Webhook service for external integrations.
Sends events to configured endpoints with HMAC signatures.
"""

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta
from typing import Optional
import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from models import WebhookEndpoint, WebhookLog

logger = structlog.get_logger(__name__)


class WebhookService:
    """Service for managing webhooks and sending events."""

    # Available webhook events
    EVENTS = [
        "user.registered",
        "user.login",
        "user.updated",
        "user.deleted",
        "champion.created",
        "champion.analyzed",
        "champion.deleted",
        "training.started",
        "training.completed",
        "subscription.changed",
        "subscription.expired"
    ]

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # ENDPOINT MANAGEMENT
    # =========================================================================

    async def get_endpoints(self, active_only: bool = False) -> list[WebhookEndpoint]:
        """Get all webhook endpoints."""
        query = select(WebhookEndpoint)
        if active_only:
            query = query.where(WebhookEndpoint.is_active == True)  # noqa: E712
        query = query.order_by(WebhookEndpoint.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_endpoint(self, endpoint_id: int) -> Optional[WebhookEndpoint]:
        """Get a webhook endpoint by ID."""
        result = await self.db.execute(
            select(WebhookEndpoint).where(WebhookEndpoint.id == endpoint_id)
        )
        return result.scalar_one_or_none()

    async def create_endpoint(
        self,
        name: str,
        url: str,
        events: list[str],
        is_active: bool = True
    ) -> WebhookEndpoint:
        """Create a new webhook endpoint."""
        # Generate secret for HMAC
        secret = secrets.token_hex(32)

        endpoint = WebhookEndpoint(
            name=name,
            url=url,
            secret=secret,
            events=events,
            is_active=is_active
        )
        self.db.add(endpoint)
        await self.db.commit()
        await self.db.refresh(endpoint)
        return endpoint

    async def update_endpoint(
        self,
        endpoint_id: int,
        name: Optional[str] = None,
        url: Optional[str] = None,
        events: Optional[list[str]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[WebhookEndpoint]:
        """Update a webhook endpoint."""
        endpoint = await self.get_endpoint(endpoint_id)
        if not endpoint:
            return None

        if name is not None:
            endpoint.name = name
        if url is not None:
            endpoint.url = url
        if events is not None:
            endpoint.events = events
        if is_active is not None:
            endpoint.is_active = is_active

        await self.db.commit()
        await self.db.refresh(endpoint)
        return endpoint

    async def delete_endpoint(self, endpoint_id: int) -> bool:
        """Delete a webhook endpoint."""
        endpoint = await self.get_endpoint(endpoint_id)
        if not endpoint:
            return False

        await self.db.delete(endpoint)
        await self.db.commit()
        return True

    async def regenerate_secret(self, endpoint_id: int) -> Optional[str]:
        """Regenerate the secret for an endpoint."""
        endpoint = await self.get_endpoint(endpoint_id)
        if not endpoint:
            return None

        new_secret = secrets.token_hex(32)
        endpoint.secret = new_secret

        await self.db.commit()
        return new_secret

    # =========================================================================
    # WEBHOOK DELIVERY
    # =========================================================================

    def _sign_payload(self, payload: str, secret: str) -> str:
        """Create HMAC signature for payload."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    async def send_event(
        self,
        event: str,
        payload: dict,
        endpoint_id: Optional[int] = None
    ) -> list[WebhookLog]:
        """Send an event to all subscribed endpoints."""
        logs = []

        # Get endpoints subscribed to this event
        if endpoint_id:
            endpoints = [await self.get_endpoint(endpoint_id)]
            endpoints = [e for e in endpoints if e and e.is_active]
        else:
            all_endpoints = await self.get_endpoints(active_only=True)
            endpoints = [e for e in all_endpoints if event in e.events]

        for endpoint in endpoints:
            log = await self._deliver_webhook(endpoint, event, payload)
            logs.append(log)

        return logs

    async def _deliver_webhook(
        self,
        endpoint: WebhookEndpoint,
        event: str,
        payload: dict
    ) -> WebhookLog:
        """Deliver a webhook to a single endpoint."""
        # Prepare payload
        full_payload = {
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload
        }
        payload_json = json.dumps(full_payload, default=str)

        # Create signature
        signature = self._sign_payload(payload_json, endpoint.secret)

        # Create log entry
        log = WebhookLog(
            endpoint_id=endpoint.id,
            event=event,
            payload=full_payload,
            status="pending"
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)

        # Send request
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    endpoint.url,
                    content=payload_json,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": f"sha256={signature}",
                        "X-Webhook-Event": event,
                        "X-Webhook-Timestamp": full_payload["timestamp"]
                    }
                )

                log.response_code = response.status_code
                log.response_body = response.text[:1000] if response.text else None

                if 200 <= response.status_code < 300:
                    log.status = "success"
                    logger.info(
                        "webhook_delivered",
                        endpoint=endpoint.name,
                        event=event,
                        status_code=response.status_code
                    )
                else:
                    log.status = "failed"
                    log.error_message = f"HTTP {response.status_code}"
                    log.next_retry_at = datetime.utcnow() + timedelta(minutes=5)
                    logger.warning(
                        "webhook_failed",
                        endpoint=endpoint.name,
                        event=event,
                        status_code=response.status_code
                    )

        except httpx.TimeoutException:
            log.status = "failed"
            log.error_message = "Request timeout"
            log.next_retry_at = datetime.utcnow() + timedelta(minutes=5)
            logger.error("webhook_timeout", endpoint=endpoint.name, event=event)

        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)[:500]
            log.next_retry_at = datetime.utcnow() + timedelta(minutes=5)
            logger.error("webhook_error", endpoint=endpoint.name, event=event, error=str(e))

        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def retry_webhook(self, log_id: int) -> Optional[WebhookLog]:
        """Retry a failed webhook."""
        result = await self.db.execute(
            select(WebhookLog).where(WebhookLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        if not log or log.status == "success":
            return None

        endpoint = await self.get_endpoint(log.endpoint_id)
        if not endpoint or not endpoint.is_active:
            return None

        # Increment attempts
        log.attempts += 1

        # Retry delivery
        return await self._deliver_webhook(endpoint, log.event, log.payload.get("data", {}))

    async def retry_pending_webhooks(self) -> int:
        """Retry all pending webhooks that are due."""
        result = await self.db.execute(
            select(WebhookLog).where(
                WebhookLog.status == "failed",
                WebhookLog.next_retry_at <= datetime.utcnow(),
                WebhookLog.attempts < 5  # Max 5 attempts
            )
        )
        logs = result.scalars().all()

        count = 0
        for log in logs:
            await self.retry_webhook(log.id)
            count += 1

        return count

    # =========================================================================
    # WEBHOOK LOGS
    # =========================================================================

    async def get_logs(
        self,
        endpoint_id: Optional[int] = None,
        event: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[WebhookLog], int]:
        """Get webhook logs with optional filtering."""
        query = select(WebhookLog)
        count_query = select(func.count(WebhookLog.id))

        if endpoint_id:
            query = query.where(WebhookLog.endpoint_id == endpoint_id)
            count_query = count_query.where(WebhookLog.endpoint_id == endpoint_id)

        if event:
            query = query.where(WebhookLog.event == event)
            count_query = count_query.where(WebhookLog.event == event)

        if status:
            query = query.where(WebhookLog.status == status)
            count_query = count_query.where(WebhookLog.status == status)

        query = query.order_by(WebhookLog.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return logs, total

    async def get_webhook_stats(self) -> dict:
        """Get webhook delivery statistics."""
        # Total deliveries
        total_result = await self.db.execute(select(func.count(WebhookLog.id)))
        total = total_result.scalar() or 0

        # Success
        success_result = await self.db.execute(
            select(func.count(WebhookLog.id)).where(WebhookLog.status == "success")
        )
        success = success_result.scalar() or 0

        # Failed
        failed_result = await self.db.execute(
            select(func.count(WebhookLog.id)).where(WebhookLog.status == "failed")
        )
        failed = failed_result.scalar() or 0

        # Pending retries
        pending_result = await self.db.execute(
            select(func.count(WebhookLog.id)).where(
                WebhookLog.status == "failed",
                WebhookLog.next_retry_at.isnot(None)
            )
        )
        pending_retries = pending_result.scalar() or 0

        # By event
        event_result = await self.db.execute(
            select(WebhookLog.event, func.count(WebhookLog.id))
            .group_by(WebhookLog.event)
            .order_by(func.count(WebhookLog.id).desc())
        )
        by_event = {row[0]: row[1] for row in event_result.all()}

        # Active endpoints
        active_result = await self.db.execute(
            select(func.count(WebhookEndpoint.id)).where(
                WebhookEndpoint.is_active == True  # noqa: E712
            )
        )
        active_endpoints = active_result.scalar() or 0

        return {
            "total_deliveries": total,
            "success": success,
            "failed": failed,
            "pending_retries": pending_retries,
            "success_rate": round((success / total * 100) if total > 0 else 0, 1),
            "by_event": by_event,
            "active_endpoints": active_endpoints,
            "available_events": self.EVENTS
        }

    # =========================================================================
    # CONVENIENCE METHODS FOR COMMON EVENTS
    # =========================================================================

    async def emit_user_registered(self, user_id: int, email: str, name: Optional[str] = None):
        """Emit user.registered event."""
        await self.send_event("user.registered", {
            "user_id": user_id,
            "email": email,
            "name": name
        })

    async def emit_user_login(self, user_id: int, email: str):
        """Emit user.login event."""
        await self.send_event("user.login", {
            "user_id": user_id,
            "email": email
        })

    async def emit_champion_created(self, user_id: int, champion_id: int, name: str):
        """Emit champion.created event."""
        await self.send_event("champion.created", {
            "user_id": user_id,
            "champion_id": champion_id,
            "name": name
        })

    async def emit_champion_analyzed(self, user_id: int, champion_id: int, name: str):
        """Emit champion.analyzed event."""
        await self.send_event("champion.analyzed", {
            "user_id": user_id,
            "champion_id": champion_id,
            "name": name
        })

    async def emit_training_completed(
        self,
        user_id: int,
        session_id: int,
        champion_id: int,
        score: float
    ):
        """Emit training.completed event."""
        await self.send_event("training.completed", {
            "user_id": user_id,
            "session_id": session_id,
            "champion_id": champion_id,
            "score": score
        })

    async def emit_subscription_changed(
        self,
        user_id: int,
        from_plan: str,
        to_plan: str,
        event_type: str
    ):
        """Emit subscription.changed event."""
        await self.send_event("subscription.changed", {
            "user_id": user_id,
            "from_plan": from_plan,
            "to_plan": to_plan,
            "type": event_type
        })
