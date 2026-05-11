# AI Incident Orchestrator

FastAPI-based orchestration service for AI-assisted incident resolution platform. Integrates with SigNoz webhooks and uses CrewAI agents for intelligent incident analysis.

## Overview

The orchestrator receives incident alerts from SigNoz, analyzes them using specialized AI agents, and persists the results to PostgreSQL.

## Features

- **Webhook Reception**: Receives alerts from SigNoz
- **Incident Management**: Creates and tracks incidents in PostgreSQL
- **AI Analysis**: Uses CrewAI agents for intelligent incident analysis
- **Root Cause Analysis**: Generates root cause hypotheses and fix suggestions
- **REST API**: Full-featured API for incident management

## Architecture

```
SigNoz Webhook
    ↓
FastAPI Orchestrator
    ├── Parse webhook
    ├── Create incident
    ├── Trigger CrewAI analysis
    ├── Persist results
    └── Return response
    ↓
PostgreSQL
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Receive Webhook
```bash
POST /incidents
Content-Type: application/json

{
  "alerts": [...],
  "error_message": "...",
  "error_type": "...",
  "stacktrace": "...",
  "service_name": "..."
}
```

### List Incidents
```bash
GET /incidents?limit=50&offset=0
```

### Get Incident
```bash
GET /incidents/{incident_id}
```

### Manual Analysis
```bash
POST /incidents/analyze?service_name=...&error_type=...&error_message=...&stacktrace=...
```

## Configuration

Environment variables:

- `DB_HOST` - PostgreSQL host (default: postgres)
- `DB_PORT` - PostgreSQL port (default: 5432)
- `DB_NAME` - Database name (default: incident_db)
- `DB_USER` - Database user (default: incident_user)
- `DB_PASSWORD` - Database password (default: incident_pass)
- `PORT` - API port (default: 8000)
- `HOST` - API host (default: 0.0.0.0)
- `LLM_PROVIDER` - LLM provider selector (default: `gemini`)
- `LLM_MODEL` - CrewAI/LiteLLM model name (default: `gemini/gemini-1.5-flash`)
- `GEMINI_API_KEY` - Gemini API key (recommended)
- `GOOGLE_API_KEY` - Gemini API key fallback
- `OPENAI_API_KEY` - Optional fallback key if using OpenAI models

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# NOTE (Gemini):
# requirements.txt already includes crewai[google-genai]
# If you still see "Google Gen AI native provider not available",
# rebuild the container/image to reinstall dependencies.

# Set environment variables
export DB_HOST=localhost
export LLM_PROVIDER=gemini
export LLM_MODEL=gemini/gemini-1.5-flash
export GEMINI_API_KEY=your-gemini-key-here
export GOOGLE_API_KEY=your-gemini-key-here

# Run application
python main.py
```

### Docker

```bash
# Build image
docker build -t orchestrator:latest .

# Run with docker-compose (recommended)
cd .. && docker-compose up orchestrator
```

## Project Structure

```
orchestrator/
├── agents/
│   └── incident_analyst.py    # CrewAI agents for analysis
├── services/
│   ├── database.py            # Database operations
│   ├── signoz_parser.py       # SigNoz webhook parser
│   └── incident_service.py    # Business logic
├── models/
│   └── incident.py            # Pydantic models
├── api/
│   └── routes.py              # API endpoints
├── main.py                    # FastAPI application
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
└── README.md
```

## Development

### Database Schema

Automatically initialized on startup. Creates `incidents` table with:
- UUID primary key
- Timestamp fields
- Error information (stacktrace, message, type)
- Analysis results (root_cause, suggested_fix, risk_level)
- Status tracking

### CrewAI Agents

Two specialized agents work together:

1. **Incident Analyst Agent**
   - Interprets stacktraces
   - Identifies error patterns
   - Summarizes incidents
   - Classifies severity

2. **Root Cause Agent**
   - Generates root cause hypotheses
   - Identifies impacted files
   - Suggests fix strategies
   - Assesses risk levels

## Requirements

- Python 3.12+
- PostgreSQL 12+
- Docker & Docker Compose
- OpenAI API key (for CrewAI)

## Monitoring

- API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Logs are output in JSON format for easy parsing

## Notes

- Incidents are processed asynchronously in background tasks
- Database schema is auto-initialized on first run
- Failed analyses fall back to heuristic-based results
- All errors are logged for debugging
