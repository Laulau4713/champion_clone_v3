# Champion Clone - Multi-Agent Architecture

Sales training platform powered by an orchestrated multi-agent system.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                                │
│                    "Upload video champion.mp4"                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FASTAPI ENDPOINTS                               │
│                  /upload, /analyze, /training/*                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                    ORCHESTRATOR (Claude Opus)                       │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    DECISION ENGINE                          │  │
│   │  • Analyzes task intent                                     │  │
│   │  • Creates execution workflow                               │  │
│   │  • Routes to appropriate agents                             │  │
│   │  • Manages parallel execution                               │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                    │               │               │
                    ▼               ▼               ▼
        ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
        │  AUDIO AGENT  │ │ PATTERN AGENT │ │TRAINING AGENT │
        │   (Sonnet)    │ │    (Opus)     │ │   (Sonnet)    │
        ├───────────────┤ ├───────────────┤ ├───────────────┤
        │ Tools:        │ │ Tools:        │ │ Tools:        │
        │ • FFmpeg      │ │ • Claude API  │ │ • Session mgmt│
        │ • Whisper     │ │ • Embeddings  │ │ • Scoring     │
        │ • ElevenLabs  │ │ • Qdrant      │ │ • Feedback    │
        ├───────────────┤ ├───────────────┤ ├───────────────┤
        │ Memory:       │ │ Memory:       │ │ Memory:       │
        │ Voice profiles│ │ Vector store  │ │ Redis sessions│
        └───────────────┘ └───────────────┘ └───────────────┘
                │               │               │
                ▼               ▼               ▼
        ┌───────────────────────────────────────────────────┐
        │                  MEMORY LAYER                      │
        ├─────────────┬─────────────┬───────────────────────┤
        │   Qdrant    │    Redis    │     PostgreSQL        │
        │  (Vectors)  │ (Sessions)  │   (Persistence)       │
        └─────────────┴─────────────┴───────────────────────┘
```

## Project Structure

```
backend/
├── main.py                    # Original FastAPI (MVP)
├── main_orchestrated.py       # Orchestrated FastAPI
│
├── orchestrator/
│   ├── __init__.py
│   ├── main.py               # ChampionCloneOrchestrator
│   └── decision_engine.py    # Routing & workflow planning
│
├── agents/
│   ├── base_agent.py         # Abstract BaseAgent class
│   ├── audio_agent/
│   │   ├── agent.py          # AudioAgent
│   │   ├── tools.py          # FFmpeg, Whisper, ElevenLabs
│   │   └── memory.py         # Voice profiles
│   ├── pattern_agent/
│   │   ├── agent.py          # PatternAgent
│   │   ├── tools.py          # Claude API analysis
│   │   └── memory.py         # Vector store wrapper
│   └── training_agent/
│       ├── agent.py          # TrainingAgent
│       ├── tools.py          # Session & feedback
│       └── memory.py         # Redis session wrapper
│
├── mcp_servers/
│   ├── package.json
│   ├── audio_server.js       # MCP for Audio Agent
│   ├── pattern_server.js     # MCP for Pattern Agent
│   └── training_server.js    # MCP for Training Agent
│
├── memory/
│   ├── __init__.py
│   ├── vector_store.py       # Qdrant integration
│   ├── session_store.py      # Redis integration
│   └── schemas.py            # Data structures
│
├── tools/
│   ├── registry.py           # Tool discovery
│   └── definitions/          # JSON tool schemas
│
├── tests/
│   ├── test_agents.py
│   └── test_mcp.py
│
└── requirements.txt
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend

# Python dependencies
pip install -r requirements.txt

# MCP server dependencies
cd mcp_servers && npm install && cd ..
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Required
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Optional (for full features)
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
ELEVENLABS_API_KEY=...

# Models
CLAUDE_OPUS_MODEL=claude-opus-4-20250514
CLAUDE_SONNET_MODEL=claude-sonnet-4-20250514
```

### 3. Start Services (Optional)

```bash
# Start Qdrant (for vector search)
docker run -p 6333:6333 qdrant/qdrant

# Start Redis (for sessions)
docker run -p 6379:6379 redis:alpine
```

### 4. Run the Server

```bash
# MVP mode (simpler)
python main.py

# Orchestrated mode (multi-agent)
python main_orchestrated.py
```

## API Endpoints

### Health & Status

```http
GET /health
GET /agents/status
GET /tools
```

### Orchestration

```http
POST /orchestrate
Content-Type: multipart/form-data

task: "Upload and analyze video champion.mp4"
context: {"champion_name": "Marie"}
```

### Champions

```http
POST /upload
POST /analyze/{champion_id}
GET /champions
GET /champions/{id}
DELETE /champions/{id}
```

### Training

```http
GET /scenarios/{champion_id}
POST /training/start
POST /training/respond
POST /training/end
GET /training/sessions
```

### Learning (Pedagogical Path)

**Public endpoints:**
```http
GET /learning/skills                    # List all skills (13)
GET /learning/skills/{slug}             # Skill details
GET /learning/sectors                   # List sectors (6)
GET /learning/sectors/{slug}            # Sector details
GET /learning/courses                   # List courses (15 days)
GET /learning/courses/day/{day}         # Course for specific day
GET /learning/difficulty-levels         # Easy, Medium, Expert
GET /learning/quiz/{skill_slug}         # Quiz questions (no answers)
```

**Protected endpoints (require auth):**
```http
GET  /learning/progress                 # User progression
GET  /learning/progress/skills          # Progress per skill
POST /learning/progress/select-sector   # Select sector (expert level)
POST /learning/session/start            # Start daily session
POST /learning/session/{id}/complete-course  # Mark course as read
POST /learning/session/{id}/listen-script    # Listen to script
GET  /learning/session/today            # Today's session
POST /learning/quiz/{slug}/submit       # Submit quiz answers
```

## Agent Details

### AudioAgent

**Purpose:** Process video/audio files

**Tools:**
- `extract_audio` - FFmpeg extraction
- `transcribe` - Whisper transcription
- `clone_voice` - ElevenLabs voice cloning
- `text_to_speech` - Generate audio
- `analyze_audio` - Audio characteristics

**Memory:** Voice profiles (JSON file storage)

### PatternAgent

**Purpose:** Extract and analyze sales patterns

**Tools:**
- `extract_patterns` - Claude Opus analysis
- `generate_scenarios` - Create training scenarios
- `store_patterns` - Save to Qdrant
- `find_patterns` - Semantic search
- `analyze_response` - Evaluate user responses

**Memory:** Qdrant vector store

### TrainingAgent

**Purpose:** Manage training sessions

**Tools:**
- `start_session` - Initialize session
- `process_response` - Handle user input
- `end_session` - Generate summary
- `get_session` - Retrieve state
- `generate_tips` - Contextual hints

**Memory:** Redis session store

### ContentAgent

**Purpose:** Generate and adapt pedagogical content

**Tools:**
- `generate_scenario` - Create training scenarios from skills
- `adapt_to_sector` - Adapt scenario to business sector
- `generate_example_script` - Create good/bad example scripts
- `personalize_difficulty` - Adjust difficulty based on performance
- `get_scenario_variants` - Generate multiple scenario variants

**Memory:** Cached scenarios (PostgreSQL)

## Services

### InterruptionService

Manages prospect interruptions based on difficulty level:

| Level | Interruption | Patience | Triggers |
|-------|-------------|----------|----------|
| Easy | Never | - | - |
| Medium | Occasional | 20s | Long speech |
| Expert | Frequent | 8s | Hesitations, low confidence, errors |

**Phrases types:** impatient, skeptical, disagreement

### AudioAnalyzer

Analyzes speech patterns and emotions:

- **Hesitation detection:** euh, donc, voila, en fait, peut-etre...
- **Prosody analysis:** pitch, tempo, volume (requires librosa)
- **Emotion scores:** confidence, hesitation, stress, enthusiasm
- **Feedback generation:** Automatic coaching tips

## Pedagogical Content

The platform includes a 15-day learning path with:

| Content | Count | Description |
|---------|-------|-------------|
| Skills | 13 | Sales competencies (easy/medium/expert) |
| Sectors | 6 | Business domains with vocabulary |
| Courses | 15 | Daily theory lessons |
| Quizzes | 13 | 5 questions per skill (65 total) |
| Difficulty Levels | 3 | Easy, Medium, Expert |

### Importing Content

```bash
python scripts/import_content.py content/
```

## MCP Integration

### Configure Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "champion-clone-audio": {
      "command": "node",
      "args": ["/path/to/backend/mcp_servers/audio_server.js"],
      "env": {
        "API_URL": "http://localhost:8000"
      }
    },
    "champion-clone-pattern": {
      "command": "node",
      "args": ["/path/to/backend/mcp_servers/pattern_server.js"],
      "env": {
        "API_URL": "http://localhost:8000"
      }
    },
    "champion-clone-training": {
      "command": "node",
      "args": ["/path/to/backend/mcp_servers/training_server.js"],
      "env": {
        "API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Example Flows

### Video Processing Flow

```
User: "Process video champion_marie.mp4"
     │
     ▼
Orchestrator: Analyzes task → Routes to AudioAgent
     │
     ▼
AudioAgent:
  1. extract_audio(video_path) → audio.mp3
  2. transcribe(audio_path) → transcript
  3. remember(voice_profile)
     │
     ▼
Orchestrator: Audio done → Routes to PatternAgent
     │
     ▼
PatternAgent:
  1. extract_patterns(transcript) → patterns
  2. store_patterns(champion_id, patterns)
  3. generate_scenarios(patterns) → scenarios
     │
     ▼
Orchestrator: Returns aggregated results
```

### Training Session Flow

```
User: "Start training with champion 1"
     │
     ▼
Orchestrator → TrainingAgent:
  1. start_session(champion_id, scenario)
  2. Returns first_message, tips
     │
     ▼
User: "Hello, I'd like to discuss your needs"
     │
     ▼
TrainingAgent:
  1. process_response(session_id, response)
  2. evaluate_response() → score, feedback
  3. generate_prospect_response()
  4. update_session()
     │
     ▼
Returns: prospect_response, score, suggestions
```

## Security

The application implements several security measures (see `SECURITY_AUDIT_2025-12-29.md` for full details):

### Authentication
- JWT-based authentication with Bearer tokens
- Bcrypt password hashing
- Protected endpoints require valid token

```bash
# Register
curl -X POST /auth/register -d '{"email":"user@example.com","password":"SecureP@ss123"}'

# Login
curl -X POST /auth/login -d '{"email":"user@example.com","password":"SecureP@ss123"}'
# Returns: {"access_token": "eyJ..."}

# Access protected endpoint
curl -H "Authorization: Bearer eyJ..." /champions
```

### Rate Limiting
| Endpoint | Limit |
|----------|-------|
| `/upload` | 10/hour |
| `/analyze/{id}` | 20/hour |
| `/training/*` | 60/minute |
| `/auth/login` | 10/minute |

### File Upload Security
- Max file size: 500 MB
- Allowed extensions: `.mp4`, `.mov`, `.avi`
- Magic bytes validation (prevents disguised files)

### CORS Configuration
```bash
# In .env
CORS_ORIGINS=https://app.example.com,https://admin.example.com
```

### Required Environment Variables (Production)
```bash
JWT_SECRET=<openssl rand -hex 32>  # REQUIRED - Generate with: openssl rand -hex 32
CORS_ORIGINS=https://your-domain.com
```

## Testing

```bash
# Run all tests (375 tests, 85% coverage)
pytest tests/ -v

# Run specific test file
pytest tests/test_agents.py -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

### Test Coverage Summary

| Module | Coverage |
|--------|----------|
| `services/interruption_service.py` | 100% |
| `services/audio_analyzer.py` | 69% |
| `agents/content_agent/agent.py` | 95% |
| `api/routers/learning.py` | 59% |
| `models.py` | 100% |
| **Total** | **85%** |

### Test Structure

```
tests/
├── unit/
│   ├── test_interruption_service.py   # 16 tests
│   ├── test_audio_analyzer.py         # 17 tests
│   ├── test_content_agent.py          # 23 tests
│   ├── test_services.py
│   ├── test_repositories.py
│   └── ...
├── integration/
│   ├── test_learning_endpoints.py     # 35 tests
│   ├── test_api.py
│   ├── test_champions.py
│   └── ...
└── conftest.py
```

## Development

### Adding a New Agent

1. Create directory: `agents/new_agent/`
2. Implement `agent.py` extending `BaseAgent`
3. Define tools in `tools.py`
4. Add memory handler in `memory.py`
5. Register in `orchestrator/decision_engine.py`
6. Create MCP server in `mcp_servers/`

### Adding a New Tool

1. Define in agent's `get_tools()` method
2. Implement in `execute_tool()` method
3. Add to `tools/definitions/<agent>_tools.json`
4. Update MCP server if needed

## License

MIT
