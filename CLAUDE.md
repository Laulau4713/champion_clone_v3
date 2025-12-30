# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

Champion Clone is a sales training platform powered by an orchestrated multi-agent system. It consists of:
- **Backend**: Python FastAPI with multi-agent architecture using Claude AI
- **Frontend**: Next.js 14 with React 18, TypeScript, and Tailwind CSS

## Development Commands

### Frontend (in `frontend/` directory)
- `npm run dev` - Start Next.js development server (port 3000)
- `npm run build` - Build production bundle
- `npm run lint` - Run ESLint

### Backend (in `backend/` directory)
- `source venv/bin/activate` - Activate Python virtual environment
- `python main.py` - Run FastAPI server
- `pytest tests/ -v` - Run all tests
- `pip install -r requirements.txt` - Install dependencies

### MCP Servers (in `backend/mcp_servers/`)
- `npm run audio` - Start audio MCP server
- `npm run pattern` - Start pattern MCP server
- `npm run training` - Start training MCP server

## Architecture

### Backend Structure (Modular)

```
backend/
├── main.py                    # Entry point (minimal, ~200 lines)
├── config.py                  # Centralized configuration (pydantic-settings)
├── database.py                # SQLAlchemy async setup
├── models.py                  # SQLAlchemy models
├── schemas.py                 # Pydantic request/response schemas
│
├── api/
│   └── routers/
│       ├── auth.py            # Auth endpoints (/auth/*)
│       ├── champions.py       # Champion endpoints (/upload, /analyze, /champions)
│       └── training.py        # Training endpoints (/scenarios, /training/*)
│
├── services/
│   └── auth.py                # Auth utilities (JWT, password hashing)
│
├── agents/
│   ├── base_agent.py          # Abstract BaseAgent class
│   ├── audio_agent/           # AudioAgent (FFmpeg, Whisper, ElevenLabs)
│   ├── pattern_agent/         # PatternAgent (Claude API, embeddings)
│   └── training_agent/        # TrainingAgent (session management)
│
├── memory/                    # Agent memory systems
│   └── vector_store.py        # Qdrant vector store
│
└── orchestrator/              # Multi-agent orchestration
    ├── main.py                # ChampionCloneOrchestrator
    └── decision_engine.py     # Routing & workflow planning
```

### Multi-Agent System
```
FastAPI Endpoints → Orchestrator (Claude Opus) → Decision Engine → Agents
```

**Agents** (each with tools and memory):
- **AudioAgent** (Sonnet): FFmpeg, Whisper, ElevenLabs - Voice profiles in JSON
- **PatternAgent** (Opus): Claude API analysis, embeddings - Qdrant vector store
- **TrainingAgent** (Sonnet): Session management, scoring - Redis sessions

### Frontend Structure
- `app/` - Next.js App Router pages
- `components/` - React components (analytics, champion, dashboard, layout, training, ui, upload)
- `lib/` - Utilities including `cn()` for Tailwind class merging
- `store/` - Zustand state management
- `types/` - TypeScript type definitions

## Code Style & Conventions

### Frontend
- **Imports**: Use `@/*` path alias for root imports (e.g., `@/lib/utils`)
- **Styling**: Use `cn()` utility from `@/lib/utils` for conditional Tailwind classes
- **Components**: Use Radix UI primitives with custom styling
- **State**: Use Zustand for global state, React Query for server state
- **Icons**: Use Lucide React
- **Animations**: Use Framer Motion
- **Date formatting**: Locale is French (`fr-FR`)

### Backend
- **API Framework**: FastAPI with APIRouter pattern (modular)
- **Configuration**: Centralized in `config.py` using pydantic-settings
- **Database**: SQLAlchemy async with SQLite (dev) / PostgreSQL (prod)
- **Logging**: Use structlog (JSON format)
- **Async**: Use async/await patterns for I/O operations
- **Environment**: All config via `.env` file, never commit secrets

## Environment Variables

### Backend (`backend/.env`)
```bash
# Required
JWT_SECRET=           # Generate with: openssl rand -hex 32
REFRESH_TOKEN_SECRET= # Generate with: openssl rand -hex 32
ANTHROPIC_API_KEY=    # For Claude AI
OPENAI_API_KEY=       # For Whisper transcription

# Optional
DATABASE_URL=sqlite+aiosqlite:///./champion_clone.db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Rate Limits
RATE_LIMIT_UPLOAD=10/hour
RATE_LIMIT_ANALYZE=20/hour
RATE_LIMIT_TRAINING=60/minute
RATE_LIMIT_LOGIN=10/minute
RATE_LIMIT_REGISTER=5/hour

# External Services (optional)
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
ELEVENLABS_API_KEY=
```

### Frontend (`frontend/.env.local`)
- `NEXT_PUBLIC_API_URL` - Backend API URL

## API Endpoints

### Health & Status
- `GET /health` - Health check

### Authentication (`api/routers/auth.py`)
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT tokens (access + refresh)
- `GET /auth/me` - Get current user (requires auth)
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout (revoke refresh token)
- `POST /auth/logout-all` - Logout from all devices

### Champions (`api/routers/champions.py`)
- `POST /upload` - Upload video
- `POST /analyze/{champion_id}` - Analyze champion
- `GET /champions` - List all
- `GET /champions/{id}` - Get one
- `DELETE /champions/{id}` - Delete

### Training (`api/routers/training.py`)
- `GET /scenarios/{champion_id}` - Generate scenarios
- `POST /training/start` - Start session
- `POST /training/respond` - User response
- `POST /training/end` - End session
- `GET /training/sessions` - List sessions
- `GET /training/sessions/{id}` - Get session details

## Adding New Features

### New Router
1. Create `backend/api/routers/new_router.py`
2. Define router: `router = APIRouter(prefix="/new", tags=["New"])`
3. Add endpoints with proper dependencies
4. Include in `main.py`: `app.include_router(new_router.router)`

### New Agent
1. Create directory: `backend/agents/new_agent/`
2. Implement `agent.py` extending `BaseAgent`
3. Define tools in `tools.py`
4. Add memory handler in `memory.py`
5. Register in `backend/orchestrator/decision_engine.py`

### New Service
1. Create `backend/services/new_service.py`
2. Add utility functions
3. Import in routers as needed

## Testing

- **ALWAYS run tests before committing**: `pytest tests/ -v`
- **Backend tests**: `backend/tests/`
- **Coverage**: `pytest tests/ --cov=. --cov-report=html`

## Security

See `backend/SECURITY_AUDIT_2025-12-29.md` for full security audit.

### Authentication
- JWT-based with access tokens (15 min) and refresh tokens (7 days)
- Bcrypt password hashing
- Password policy: 8+ chars, uppercase, lowercase, digit, special char
- Refresh token revocation on logout

### Rate Limiting (per user when authenticated, per IP otherwise)
- Upload: 10/hour
- Analyze: 20/hour
- Training: 60/minute
- Login: 10/minute
- Register: 5/hour

### File Upload
- Max size: 500 MB
- Allowed: `.mp4`, `.mov`, `.avi`
- Magic bytes validation

### CORS
- Configurable via `CORS_ORIGINS` env variable
- Defaults to localhost:3000 in development

## Important Notes

- **NEVER commit `.env` files** - Use `.env.example` as template
- **JWT secrets must be set in production** - App will not start without them
- **Virtual environments**: Backend uses `backend/venv/`
- **Database**: SQLite at `backend/champion_clone.db` (dev only)
- **Uploads**: Stored in `backend/uploads/`
- **Audio files**: Stored in `backend/audio/`
