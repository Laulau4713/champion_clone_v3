"""
Champion Clone MVP - FastAPI Backend

A sales training platform that:
1. Analyzes champion salespeople's techniques from videos
2. Generates training scenarios
3. Provides AI-powered practice sessions with feedback
"""

import os
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from jose import jwt
import structlog

# Configuration
from config import get_settings

settings = get_settings()


def get_rate_limit_key(request: Request) -> str:
    """
    Get the rate limit key for a request.

    Strategy:
    - For authenticated requests: use "user:{user_id}" as key
    - For unauthenticated requests: use IP address as fallback

    This prevents:
    - VPN hopping (authenticated users can't bypass limits)
    - Shared IP issues (different users on same IP get separate limits)
    """
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            if settings.JWT_SECRET:
                payload = jwt.decode(
                    token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
                )
                user_id = payload.get("sub")
                if user_id:
                    return f"user:{user_id}"
        except Exception:
            pass

    return get_remote_address(request)


# Initialize rate limiter with custom key function
limiter = Limiter(key_func=get_rate_limit_key)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# ============================================
# JWT Secret Validation
# ============================================

if not settings.JWT_SECRET:
    if settings.DEBUG:
        logger.warning("jwt_secret_missing", message="JWT_SECRET not set! Using insecure default (DEBUG mode only)")
    else:
        logger.error("jwt_secret_required", message="JWT_SECRET environment variable is required!")
        raise SystemExit("FATAL: JWT_SECRET not set. Generate with: openssl rand -hex 32")

if not settings.REFRESH_TOKEN_SECRET:
    if settings.DEBUG:
        logger.warning("refresh_secret_missing", message="REFRESH_TOKEN_SECRET not set! Using derived secret (DEBUG mode only)")
    else:
        logger.error("refresh_secret_required", message="REFRESH_TOKEN_SECRET environment variable is required!")
        raise SystemExit("FATAL: REFRESH_TOKEN_SECRET not set. Generate with: openssl rand -hex 32")


# ============================================
# Database and Routers Imports
# ============================================

from database import init_db, close_db
from schemas import ErrorResponse

# Import domain exceptions
from domain.exceptions import (
    ChampionCloneError,
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ExternalServiceError,
    SessionError,
    SessionNotFoundError,
    SessionNotActiveError,
    ConfigurationError,
)

# Import routers
from api.routers import auth, champions, training, admin, learning, payments, audit


# ============================================
# Application Lifespan
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("application_starting")
    await init_db()

    # Create upload directories
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.AUDIO_DIR).mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    logger.info("application_shutting_down")
    await close_db()


# ============================================
# FastAPI Application
# ============================================

app = FastAPI(
    title="Champion Clone API",
    description="Sales training platform powered by AI",
    version="0.1.0",
    lifespan=lifespan
)

# Attach rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
# SECURITY: Never use "*" with credentials in production!
# Set CORS_ORIGINS in .env: CORS_ORIGINS=https://myapp.com,https://admin.myapp.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


# ============================================
# Include Routers
# ============================================

app.include_router(auth.router)
app.include_router(champions.router)
app.include_router(training.router)
app.include_router(admin.router)
app.include_router(learning.router)
app.include_router(payments.router)
app.include_router(audit.router)


# ============================================
# Health Check
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ============================================
# Domain Exception Handlers
# ============================================

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    """Handle resource not found errors."""
    return JSONResponse(
        status_code=404,
        content={"error": "NotFound", "detail": str(exc), "resource": exc.resource}
    )


@app.exception_handler(AlreadyExistsError)
async def already_exists_handler(request: Request, exc: AlreadyExistsError):
    """Handle duplicate resource errors."""
    return JSONResponse(
        status_code=409,
        content={"error": "Conflict", "detail": str(exc), "resource": exc.resource}
    )


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    """Handle business validation errors."""
    return JSONResponse(
        status_code=400,
        content={"error": "ValidationError", "detail": str(exc)}
    )


@app.exception_handler(AuthenticationError)
async def auth_handler(request: Request, exc: AuthenticationError):
    """Handle authentication failures."""
    return JSONResponse(
        status_code=401,
        content={"error": "Unauthorized", "detail": str(exc)}
    )


@app.exception_handler(AuthorizationError)
async def authz_handler(request: Request, exc: AuthorizationError):
    """Handle authorization failures."""
    return JSONResponse(
        status_code=403,
        content={"error": "Forbidden", "detail": str(exc)}
    )


@app.exception_handler(ExternalServiceError)
async def external_handler(request: Request, exc: ExternalServiceError):
    """Handle external service errors."""
    logger.error("external_service_error", service=exc.service, error=str(exc))
    return JSONResponse(
        status_code=502,
        content={"error": "ServiceError", "detail": str(exc), "service": exc.service}
    )


@app.exception_handler(SessionNotFoundError)
async def session_not_found_handler(request: Request, exc: SessionNotFoundError):
    """Handle session not found errors."""
    return JSONResponse(
        status_code=404,
        content={"error": "SessionNotFound", "detail": str(exc), "session_id": exc.session_id}
    )


@app.exception_handler(SessionNotActiveError)
async def session_not_active_handler(request: Request, exc: SessionNotActiveError):
    """Handle session not active errors."""
    return JSONResponse(
        status_code=409,
        content={"error": "SessionNotActive", "detail": str(exc), "session_id": exc.session_id, "status": exc.status}
    )


@app.exception_handler(SessionError)
async def session_error_handler(request: Request, exc: SessionError):
    """Handle generic session errors."""
    return JSONResponse(
        status_code=400,
        content={"error": "SessionError", "detail": str(exc)}
    )


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(request: Request, exc: ConfigurationError):
    """Handle configuration errors."""
    logger.error("configuration_error", key=exc.key, error=str(exc))
    return JSONResponse(
        status_code=503,
        content={"error": "ConfigurationError", "detail": str(exc)}
    )


# ============================================
# General Error Handler
# ============================================

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error("unhandled_exception", error=str(exc), type=type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.DEBUG else None,
            code="INTERNAL_ERROR"
        ).model_dump()
    )


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
