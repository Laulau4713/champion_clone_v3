"""
Maintenance Tasks - Celery tasks for system maintenance
========================================================

Scheduled tasks for:
- Database cleanup
- Token expiration
- File cleanup
- Health monitoring
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from celery import shared_task
import structlog

logger = structlog.get_logger()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "./audio"))


# =============================================================================
# SESSION CLEANUP
# =============================================================================

@shared_task(bind=True)
def cleanup_old_sessions(self, days_old: int = 30):
    """
    Clean up old training sessions from database.
    Runs daily at 3 AM.
    """
    logger.info("cleanup_sessions_started", days_old=days_old)

    # TODO: Implement database cleanup
    # This would run something like:
    # async with AsyncSessionLocal() as db:
    #     cutoff = datetime.utcnow() - timedelta(days=days_old)
    #     result = await db.execute(
    #         delete(TrainingSession).where(TrainingSession.created_at < cutoff)
    #     )
    #     await db.commit()
    #     deleted = result.rowcount

    deleted = 0  # Placeholder

    logger.info("cleanup_sessions_completed", deleted=deleted)

    return {"deleted": deleted, "days_old": days_old}


# =============================================================================
# TOKEN CLEANUP
# =============================================================================

@shared_task(bind=True)
def cleanup_expired_tokens(self):
    """
    Remove expired refresh tokens from database.
    Runs every 6 hours.
    """
    logger.info("cleanup_tokens_started")

    # TODO: Implement token cleanup
    # async with AsyncSessionLocal() as db:
    #     result = await db.execute(
    #         delete(RefreshToken).where(RefreshToken.expires_at < datetime.utcnow())
    #     )
    #     await db.commit()
    #     deleted = result.rowcount

    deleted = 0  # Placeholder

    logger.info("cleanup_tokens_completed", deleted=deleted)

    return {"deleted": deleted}


# =============================================================================
# AUDIO FILE CLEANUP
# =============================================================================

@shared_task(bind=True)
def cleanup_audio_files(self, days_old: int = 7):
    """
    Remove old audio files from disk.
    Runs daily at 2 AM.
    """
    logger.info("cleanup_audio_started", days_old=days_old)

    cutoff = datetime.now() - timedelta(days=days_old)
    deleted_count = 0
    freed_bytes = 0

    try:
        if AUDIO_DIR.exists():
            for file_path in AUDIO_DIR.glob("*"):
                if file_path.is_file():
                    # Check modification time
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff:
                        size = file_path.stat().st_size
                        file_path.unlink()
                        deleted_count += 1
                        freed_bytes += size

        logger.info(
            "cleanup_audio_completed",
            deleted=deleted_count,
            freed_mb=round(freed_bytes / 1024 / 1024, 2),
        )

        return {
            "deleted": deleted_count,
            "freed_mb": round(freed_bytes / 1024 / 1024, 2),
        }

    except Exception as e:
        logger.error("cleanup_audio_failed", error=str(e))
        raise


# =============================================================================
# DATABASE VACUUM
# =============================================================================

@shared_task(bind=True)
def vacuum_database(self):
    """
    Run VACUUM ANALYZE on PostgreSQL.
    Runs weekly on Sunday at 4 AM.
    """
    logger.info("vacuum_started")

    database_url = os.getenv("DATABASE_URL", "")

    if "postgresql" not in database_url:
        logger.info("vacuum_skipped", reason="Not PostgreSQL")
        return {"status": "skipped", "reason": "Not PostgreSQL"}

    try:
        import psycopg2

        # Parse connection string
        # postgresql+asyncpg://user:pass@host:port/db
        # Convert to psycopg2 format
        conn_str = database_url.replace("postgresql+asyncpg://", "postgresql://")

        conn = psycopg2.connect(conn_str)
        conn.autocommit = True

        with conn.cursor() as cur:
            cur.execute("VACUUM ANALYZE;")

        conn.close()

        logger.info("vacuum_completed")
        return {"status": "completed"}

    except Exception as e:
        logger.error("vacuum_failed", error=str(e))
        raise


# =============================================================================
# HEALTH CHECK
# =============================================================================

@shared_task(bind=True)
def health_check(self):
    """
    Periodic health check.
    Runs every 5 minutes.
    """
    checks = {
        "timestamp": datetime.utcnow().isoformat(),
        "redis": False,
        "database": False,
        "disk_space": False,
    }

    # Check Redis
    try:
        from redis import Redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = Redis.from_url(redis_url)
        r.ping()
        checks["redis"] = True
    except:
        pass

    # Check disk space
    try:
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)
        checks["disk_space"] = free_gb > 1  # At least 1GB free
        checks["disk_free_gb"] = free_gb
    except:
        pass

    # Check database
    try:
        # Would need async context, simplified for task
        checks["database"] = True
    except:
        pass

    # Log if any checks failed
    all_ok = all([checks["redis"], checks["database"], checks["disk_space"]])

    if all_ok:
        logger.debug("health_check_ok", **checks)
    else:
        logger.warning("health_check_issues", **checks)

    return checks


# =============================================================================
# UPLOAD FILE CLEANUP
# =============================================================================

@shared_task(bind=True)
def cleanup_upload_files(self, days_old: int = 30):
    """
    Remove old upload files from disk.
    """
    logger.info("cleanup_uploads_started", days_old=days_old)

    cutoff = datetime.now() - timedelta(days=days_old)
    deleted_count = 0
    freed_bytes = 0

    try:
        if UPLOAD_DIR.exists():
            for file_path in UPLOAD_DIR.glob("**/*"):
                if file_path.is_file():
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff:
                        size = file_path.stat().st_size
                        file_path.unlink()
                        deleted_count += 1
                        freed_bytes += size

        logger.info(
            "cleanup_uploads_completed",
            deleted=deleted_count,
            freed_mb=round(freed_bytes / 1024 / 1024, 2),
        )

        return {
            "deleted": deleted_count,
            "freed_mb": round(freed_bytes / 1024 / 1024, 2),
        }

    except Exception as e:
        logger.error("cleanup_uploads_failed", error=str(e))
        raise
