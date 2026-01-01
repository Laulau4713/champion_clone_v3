# =============================================================================
# BACKEND DOCKERFILE - Multi-stage build for dev and production
# =============================================================================
#
# Stages:
#   - base: Common dependencies
#   - development: Hot reload with uvicorn
#   - production: Gunicorn multi-worker with optimizations
#
# Usage:
#   Dev:  docker build --target development -t champion-backend:dev .
#   Prod: docker build --target production -t champion-backend:prod .
# =============================================================================

# =============================================================================
# BASE STAGE - Common dependencies
# =============================================================================
FROM python:3.11-slim AS base

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r champion && useradd -r -g champion champion

# Create directories
RUN mkdir -p /app/uploads /app/audio /app/data /app/logs \
    && chown -R champion:champion /app

# Python settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# DEVELOPMENT STAGE - Hot reload with uvicorn
# =============================================================================
FROM base AS development

# Install dev dependencies
RUN pip install --no-cache-dir \
    watchfiles \
    debugpy

# Copy source (will be overridden by volume mount in docker-compose)
COPY --chown=champion:champion . .

# Switch to non-root user
USER champion

# Port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Development command with hot reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =============================================================================
# PRODUCTION STAGE - Gunicorn multi-worker
# =============================================================================
FROM base AS production

# Install production dependencies
RUN pip install --no-cache-dir \
    gunicorn \
    prometheus-client

# Copy source code
COPY --chown=champion:champion . .

# Remove unnecessary files
RUN rm -rf tests/ .pytest_cache/ __pycache__/ *.pyc .env.* venv/

# Switch to non-root user
USER champion

# Port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Environment variables for Gunicorn
ENV GUNICORN_WORKERS=4 \
    GUNICORN_THREADS=2 \
    GUNICORN_TIMEOUT=120 \
    GUNICORN_KEEPALIVE=5 \
    GUNICORN_MAX_REQUESTS=1000 \
    GUNICORN_MAX_REQUESTS_JITTER=100

# Production command with Gunicorn
# - Workers: CPU cores * 2 + 1 (configurable via env)
# - UvicornWorker: async support for FastAPI
# - Graceful timeout: 30s for clean shutdown
# - Access log: stdout for Docker logging
CMD ["sh", "-c", "gunicorn main:app \
    --workers ${GUNICORN_WORKERS} \
    --threads ${GUNICORN_THREADS} \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout ${GUNICORN_TIMEOUT} \
    --keep-alive ${GUNICORN_KEEPALIVE} \
    --max-requests ${GUNICORN_MAX_REQUESTS} \
    --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER} \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance"]
