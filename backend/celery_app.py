"""
Celery Application Configuration
================================

Handles async tasks for heavy processing:
- Claude API calls (pattern analysis, training responses)
- ElevenLabs TTS generation
- Audio transcription (Whisper)
- Email notifications
- Periodic cleanup tasks

Usage:
    Worker: celery -A celery_app worker --loglevel=info
    Beat:   celery -A celery_app beat --loglevel=info
    Flower: celery -A celery_app flower (monitoring UI)
"""

import os
from celery import Celery
from celery.schedules import crontab
from kombu import Queue

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

# Broker and Backend URLs
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

# Create Celery app
celery_app = Celery(
    "champion_clone",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "tasks.ai_tasks",
        "tasks.audio_tasks",
        "tasks.email_tasks",
        "tasks.maintenance_tasks",
    ],
)

# =============================================================================
# CELERY SETTINGS
# =============================================================================

celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,

    # Task execution
    task_acks_late=True,  # Acknowledge after task completes (safer)
    task_reject_on_worker_lost=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # Soft limit 9 minutes (allows cleanup)

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_concurrency=4,  # 4 concurrent tasks per worker
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (memory leak prevention)

    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,  # Store task state (PENDING, STARTED, etc.)

    # Retry settings
    task_default_retry_delay=60,  # 1 minute between retries
    task_max_retries=3,

    # Rate limiting for external APIs
    task_annotations={
        "tasks.ai_tasks.call_claude_api": {
            "rate_limit": "30/m",  # 30 calls per minute max
        },
        "tasks.audio_tasks.generate_tts": {
            "rate_limit": "10/m",  # 10 TTS calls per minute
        },
        "tasks.audio_tasks.transcribe_audio": {
            "rate_limit": "20/m",  # 20 transcriptions per minute
        },
    },

    # Task routing - different queues for different priorities
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("ai", routing_key="ai.#"),  # AI tasks (Claude, etc.)
        Queue("audio", routing_key="audio.#"),  # Audio processing
        Queue("email", routing_key="email.#"),  # Email sending
        Queue("maintenance", routing_key="maintenance.#"),  # Cleanup tasks
    ),

    task_default_queue="default",
    task_default_routing_key="default",

    task_routes={
        "tasks.ai_tasks.*": {"queue": "ai", "routing_key": "ai.task"},
        "tasks.audio_tasks.*": {"queue": "audio", "routing_key": "audio.task"},
        "tasks.email_tasks.*": {"queue": "email", "routing_key": "email.task"},
        "tasks.maintenance_tasks.*": {"queue": "maintenance", "routing_key": "maintenance.task"},
    },
)

# =============================================================================
# CELERY BEAT SCHEDULE (Periodic Tasks)
# =============================================================================

celery_app.conf.beat_schedule = {
    # Cleanup old sessions every day at 3 AM
    "cleanup-old-sessions": {
        "task": "tasks.maintenance_tasks.cleanup_old_sessions",
        "schedule": crontab(hour=3, minute=0),
        "kwargs": {"days_old": 30},
    },

    # Cleanup expired tokens every 6 hours
    "cleanup-expired-tokens": {
        "task": "tasks.maintenance_tasks.cleanup_expired_tokens",
        "schedule": crontab(hour="*/6", minute=0),
    },

    # Send inactive user reminders (users inactive for 7 days)
    "send-inactive-reminders": {
        "task": "tasks.email_tasks.send_inactive_user_reminders",
        "schedule": crontab(hour=10, minute=0),  # 10 AM daily
        "kwargs": {"days_inactive": 7},
    },

    # Database vacuum (PostgreSQL maintenance)
    "database-vacuum": {
        "task": "tasks.maintenance_tasks.vacuum_database",
        "schedule": crontab(hour=4, minute=0, day_of_week="sunday"),  # Sunday 4 AM
    },

    # Clear old audio files (keep 7 days)
    "cleanup-audio-files": {
        "task": "tasks.maintenance_tasks.cleanup_audio_files",
        "schedule": crontab(hour=2, minute=0),
        "kwargs": {"days_old": 7},
    },

    # Health check (every 5 minutes)
    "health-check": {
        "task": "tasks.maintenance_tasks.health_check",
        "schedule": 300.0,  # Every 5 minutes
    },
}

# =============================================================================
# CELERY SIGNALS (Logging, Monitoring)
# =============================================================================

from celery.signals import task_prerun, task_postrun, task_failure
import structlog

logger = structlog.get_logger()


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    """Log when task starts."""
    logger.info(
        "task_started",
        task_id=task_id,
        task_name=task.name if task else None,
    )


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, state=None, **kw):
    """Log when task completes."""
    logger.info(
        "task_completed",
        task_id=task_id,
        task_name=task.name if task else None,
        state=state,
    )


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, **kw):
    """Log task failures."""
    logger.error(
        "task_failed",
        task_id=task_id,
        exception=str(exception),
    )
