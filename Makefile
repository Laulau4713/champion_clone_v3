# =============================================================================
# Champion Clone - Makefile
# =============================================================================
# Quick commands for development and production
#
# Usage:
#   make dev          - Start development environment
#   make prod         - Start production environment
#   make logs         - View logs
#   make test         - Run tests
#   make clean        - Clean up
# =============================================================================

# Detect docker-compose command (v1 or v2)
DOCKER_COMPOSE := $(shell which docker-compose 2>/dev/null || echo "docker compose")

.PHONY: help dev dev-up dev-down dev-logs prod prod-up prod-down prod-logs \
        test lint build clean db-migrate db-reset celery-worker celery-flower \
        shell-backend shell-frontend

# Default target
help:
	@echo "Champion Clone - Available Commands"
	@echo "===================================="
	@echo ""
	@echo "Development:"
	@echo "  make dev           Start dev environment (docker-compose)"
	@echo "  make dev-local     Start backend + frontend locally (no docker)"
	@echo "  make dev-down      Stop dev environment"
	@echo "  make dev-logs      View dev logs"
	@echo ""
	@echo "Production:"
	@echo "  make prod          Start production environment"
	@echo "  make prod-down     Stop production environment"
	@echo "  make prod-logs     View production logs"
	@echo "  make prod-scale    Scale backend to 3 instances"
	@echo ""
	@echo "Testing:"
	@echo "  make test          Run all tests"
	@echo "  make test-cov      Run tests with coverage"
	@echo "  make lint          Run linters"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate    Run database migrations"
	@echo "  make db-reset      Reset database (WARNING: deletes data)"
	@echo ""
	@echo "Utilities:"
	@echo "  make build         Build all Docker images"
	@echo "  make clean         Clean up containers and volumes"
	@echo "  make shell-back    Open shell in backend container"
	@echo "  make shell-front   Open shell in frontend container"

# =============================================================================
# DEVELOPMENT
# =============================================================================

dev: dev-up
	@echo "Development environment started!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend:  http://localhost:8000"
	@echo "Redis:    localhost:6379"
	@echo "Mailhog:  http://localhost:8025"

dev-up:
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml ps

dev-down:
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

dev-logs:
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f

dev-logs-backend:
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f backend

dev-logs-frontend:
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f frontend

# Local development (without Docker)
dev-local:
	@echo "Starting local development..."
	@echo "Run these commands in separate terminals:"
	@echo ""
	@echo "Terminal 1 (Backend):"
	@echo "  cd backend && source venv/bin/activate && python main.py"
	@echo ""
	@echo "Terminal 2 (Frontend):"
	@echo "  cd frontend && npm run dev"
	@echo ""
	@echo "Terminal 3 (Redis - optional):"
	@echo "  docker run -p 6379:6379 redis:7-alpine"

# =============================================================================
# PRODUCTION
# =============================================================================

prod: prod-up
	@echo "Production environment started!"
	@echo "Application: https://champion-clone.com"
	@echo "API:         https://api.champion-clone.com"

prod-up:
	@if [ ! -f .env.prod ]; then \
		echo "ERROR: .env.prod file not found!"; \
		echo "Copy .env.prod.example to .env.prod and configure it."; \
		exit 1; \
	fi
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml --env-file .env.prod up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml ps

prod-down:
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml down

prod-logs:
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml logs -f

prod-logs-backend:
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml logs -f backend

prod-logs-celery:
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml logs -f celery_worker

# Scale backend instances
prod-scale:
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml --env-file .env.prod up -d --scale backend=3 --scale celery_worker=4

prod-restart:
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml --env-file .env.prod restart backend celery_worker

# =============================================================================
# TESTING
# =============================================================================

test:
	cd backend && source venv/bin/activate && pytest tests/ -v

test-cov:
	cd backend && source venv/bin/activate && pytest tests/ -v --cov=. --cov-report=html
	@echo "Coverage report: backend/htmlcov/index.html"

test-unit:
	cd backend && source venv/bin/activate && pytest tests/unit/ -v

test-integration:
	cd backend && source venv/bin/activate && pytest tests/integration/ -v

# =============================================================================
# LINTING
# =============================================================================

lint:
	@echo "Running backend linters..."
	cd backend && source venv/bin/activate && python -m flake8 . --max-line-length=120 --exclude=venv,__pycache__
	@echo "Running frontend linters..."
	cd frontend && npm run lint

lint-fix:
	cd frontend && npm run lint -- --fix

# =============================================================================
# BUILD
# =============================================================================

build:
	docker-compose -f docker-compose.dev.yml build
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml build

build-prod:
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml build --no-cache

build-backend:
	docker build -t champion-backend:latest --target production ./backend

build-frontend:
	docker build -t champion-frontend:latest --target production ./frontend

# =============================================================================
# DATABASE
# =============================================================================

db-migrate:
	cd backend && source venv/bin/activate && alembic upgrade head

db-migrate-create:
	@read -p "Migration message: " msg; \
	cd backend && source venv/bin/activate && alembic revision --autogenerate -m "$$msg"

db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ]; then \
		cd backend && rm -f champion_clone.db && python main.py; \
	fi

db-shell:
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml exec db psql -U champion -d champion_clone

# =============================================================================
# CELERY
# =============================================================================

celery-worker:
	cd backend && source venv/bin/activate && celery -A celery_app worker --loglevel=info

celery-beat:
	cd backend && source venv/bin/activate && celery -A celery_app beat --loglevel=info

celery-flower:
	cd backend && source venv/bin/activate && celery -A celery_app flower --port=5555
	@echo "Flower UI: http://localhost:5555"

# =============================================================================
# UTILITIES
# =============================================================================

shell-backend:
	docker-compose -f docker-compose.dev.yml exec backend /bin/sh

shell-frontend:
	docker-compose -f docker-compose.dev.yml exec frontend /bin/sh

shell-db:
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml exec db psql -U champion -d champion_clone

shell-redis:
	docker-compose -f docker-compose.dev.yml exec redis redis-cli

# =============================================================================
# CLEANUP
# =============================================================================

clean:
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml down -v --remove-orphans
	docker system prune -f
	@echo "Cleaned up containers and volumes"

clean-images:
	docker rmi $(docker images -q champion-*) 2>/dev/null || true
	@echo "Cleaned up Docker images"

clean-all: clean clean-images
	@echo "Full cleanup complete"

# =============================================================================
# DEPLOYMENT
# =============================================================================

deploy-check:
	@echo "Pre-deployment checklist:"
	@echo "========================="
	@test -f .env.prod && echo "✓ .env.prod exists" || echo "✗ .env.prod missing"
	@test -f nginx/ssl/fullchain.pem && echo "✓ SSL certificate exists" || echo "✗ SSL certificate missing"
	@docker --version > /dev/null && echo "✓ Docker installed" || echo "✗ Docker not installed"
	@docker-compose --version > /dev/null && echo "✓ Docker Compose installed" || echo "✗ Docker Compose not installed"

deploy:
	@make deploy-check
	@echo ""
	@read -p "Deploy to production? [y/N] " confirm; \
	if [ "$$confirm" = "y" ]; then \
		make build-prod && make prod-up; \
	fi

# =============================================================================
# SSL CERTIFICATES
# =============================================================================

ssl-init:
	@echo "Initializing SSL certificates with Let's Encrypt..."
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml run --rm certbot certonly \
		--webroot \
		--webroot-path=/var/www/certbot \
		--email admin@champion-clone.com \
		--agree-tos \
		--no-eff-email \
		-d champion-clone.com \
		-d www.champion-clone.com \
		-d api.champion-clone.com

ssl-renew:
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml run --rm certbot renew
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml exec nginx nginx -s reload

# =============================================================================
# MONITORING
# =============================================================================

monitoring-up:
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml up -d prometheus grafana
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana:    http://localhost:3000 (admin/admin)"

monitoring-down:
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml stop prometheus grafana
