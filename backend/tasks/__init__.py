"""
Celery Tasks Package
====================

Task modules:
- ai_tasks: Claude API, pattern analysis, training responses
- audio_tasks: Transcription, TTS generation
- email_tasks: Email notifications
- maintenance_tasks: Cleanup, health checks
"""

from tasks.ai_tasks import (
    call_claude_api,
    analyze_patterns_async,
    generate_training_response_async,
    evaluate_session_async,
)

from tasks.audio_tasks import (
    transcribe_audio,
    generate_tts,
    extract_audio_from_video,
)

from tasks.email_tasks import (
    send_email,
    send_welcome_email,
    send_inactive_user_reminders,
)

from tasks.maintenance_tasks import (
    cleanup_old_sessions,
    cleanup_expired_tokens,
    cleanup_audio_files,
    vacuum_database,
    health_check,
)

__all__ = [
    # AI
    "call_claude_api",
    "analyze_patterns_async",
    "generate_training_response_async",
    "evaluate_session_async",
    # Audio
    "transcribe_audio",
    "generate_tts",
    "extract_audio_from_video",
    # Email
    "send_email",
    "send_welcome_email",
    "send_inactive_user_reminders",
    # Maintenance
    "cleanup_old_sessions",
    "cleanup_expired_tokens",
    "cleanup_audio_files",
    "vacuum_database",
    "health_check",
]
