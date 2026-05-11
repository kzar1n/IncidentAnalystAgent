# Getting Started Guide

This guide will walk you through setting up and running the AI-Assisted Incident Resolution Platform locally using Docker.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Service Overview](#service-overview)
4. [Configure SigNoz alerts for the orchestrator](#configure-signoz-alerts-for-the-orchestrator)
5. [Testing the Platform](#testing-the-platform)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required

- **Docker**: Version 20.10 or higher
  - Download: https://www.docker.com/products/docker-desktop
  
- **Docker Compose**: Version 2.0 or higher
  - Usually included with Docker Desktop
  - Verify: `docker-compose --version`

- **OpenAI API Key**
  - Required for CrewAI agents
  - Get from: https://platform.openai.com/account/api-keys
  - Keep it safe and never commit to Git!

### Optional

- **Git**: For cloning the repository
- **cURL**: For testing API endpoints (usually pre-installed)
- **PostgreSQL Client**: For direct database access (pgAdmin or psql)

## Quick Start

### 1. Clone/Navigate to Project

```bash
cd IncidentAnalystAgent
```

### 2. Configure Environment

Create or edit the `.env` file:

```bash
# Linux/Mac
nano .env

# Windows
notepad .env
```

Add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. Start All Services

#### Option A: Using Docker Compose (Recommended)

```bash
docker-compose up -d
```

#### Option B: Using Setup Script (Linux/Mac)

```bash
chmod +x setup.sh
./setup.sh start
```

#### Option C: Using Setup Script (Windows)

```bash
setup.bat start
```

### 4. Wait for Services to Be Ready

Monitor service startup (Compose V2):

```bash
docker compose ps
# or legacy: docker-compose ps
```

**One-shot containers** (`incident-init-clickhouse`, `incident-signoz-telemetrystore-migrator`) normally finish and show **Exited (0)** after the first successful run. That is expected.

Typical steady-state `docker compose ps` (example):

```
NAME                              STATUS                         PORTS
incident-postgres                 Up … (healthy)                 0.0.0.0:5432->5432/tcp
incident-clickhouse               Up … (healthy)                 8123/tcp, 9000/tcp (published)
incident-zookeeper-1              Up … (healthy)                 (internal ZooKeeper ports)
incident-signoz                   Up … (healthy)                 0.0.0.0:3301->8080/tcp
incident-signoz-otel-collector    Up …                          0.0.0.0:4317-4318->4317-4318/tcp
incident-otel-collector           Up …                          0.0.0.0:8888->8888/tcp
incident-spring-app               Up … (healthy)                 0.0.0.0:8080->8080/tcp
incident-orchestrator             Up … (healthy)                 0.0.0.0:8000->8000/tcp
```

Docker only shows `(healthy)` when the service defines a **`HEALTHCHECK`**. Gateways **`incident-otel-collector`** and **`incident-signoz-otel-collector`** may stay **Up** without that label—they are still required for telemetry.

Optional: inspect Compose health explicitly:

```bash
docker compose ps --format "table {{.Name}}\t{{.Status}}"
```

Optional: Docker health field for a named container:

```bash
docker inspect -f "{{.State.Health.Status}}" incident-orchestrator
```

### 4a. Essential services vs supporting services

Everything below must be **running** for the **full pipeline** (app → OTLP → SigNoz UI → webhook → orchestrator):

| Role | Compose service name | Container (typical) | Why it matters |
|------|----------------------|---------------------|----------------|
| App + traces | `spring-app` | `incident-spring-app` | Generates telemetry and simulated errors |
| OTLP gateway | `otel-collector` | `incident-otel-collector` | Relays OTLP from the app toward SigNoz |
| OTLP ingestion (SigNoz) | `signoz-otel-collector` | `incident-signoz-otel-collector` | Receives OTLP and writes to ClickHouse |
| Storage | `clickhouse` | `incident-clickhouse` | Telemetry store |
| Coordination | `zookeeper-1` | `incident-zookeeper-1` | Required by ClickHouse SigNoz setup |
| UI + alerts API | `signoz` | `incident-signoz` | Dashboard and **configured** alert notifications |
| Incidents DB + AI | `orchestrator` | `incident-orchestrator` | Receives webhook `POST /incidents`, persists to Postgres |
| Incidents persistence | `postgres` | `incident-postgres` | Stores incidents and analyses |

Supporting / bootstrap (often **not** long-running):

| Compose service | Typical status | Purpose |
|-----------------|----------------|---------|
| `init-clickhouse` | Exited (0) | Downloads helper into ClickHouse user scripts |
| `signoz-telemetrystore-migrator` | Exited (0) | Runs DB migrations once |

### 5. Verify HTTP endpoints

```bash
# Spring Boot
curl -s http://localhost:8080/health

# Orchestrator (returns JSON with UP)
curl -s http://localhost:8000/health

# SigNoz UI/API (expects HTML or redirect; OK if connection succeeds)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3301/
```

Telemetry path (conceptual):

`spring-app` → **`otel-collector:4317`** (internal) → **`signoz-otel-collector:4317`** → **ClickHouse** → **SigNoz UI** (`localhost:3301`).

**Important:** Simply calling `GET /error` on the app **does not** notify the orchestrator. SigNoz ingests traces; the orchestrator is called only when **you configure an alert** (or **notification channel**) in SigNoz that sends a webhook to the orchestrator. See [Configure SigNoz alerts for the orchestrator](#configure-signoz-alerts-for-the-orchestrator) below.

## Service Overview

### 1. Spring Boot Application (Port 8080)

Sample application that generates observability data.

**Endpoints:**
- `GET /health` - Health check
- `GET /error` - Simulate error
- `GET /timeout` - Simulate timeout
- `GET /payment/{id}` - Test payment endpoint

**Usage:**
```bash
# Health check
curl http://localhost:8080/health

# Trigger an error (will be captured by SigNoz)
curl http://localhost:8080/error

# Simulate slowness
curl http://localhost:8080/timeout

# Test payment
curl http://localhost:8080/payment/123
curl http://localhost:8080/payment/999  # Will error
```

### 2. FastAPI Orchestrator (Port 8000)

AI-powered incident orchestration service.

**Endpoints:**
- `GET /health` - Health check
- `POST /incidents` - Receive SigNoz webhook
- `GET /incidents` - List incidents
- `GET /incidents/{id}` - Get specific incident
- `POST /incidents/analyze` - Manual analysis

**Usage:**
```bash
# List incidents
curl http://localhost:8000/incidents

# Manual incident analysis
curl -X POST "http://localhost:8000/incidents/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "payment-service",
    "error_type": "NullPointerException",
    "error_message": "Cannot invoke method",
    "stacktrace": "at PaymentService.java:42",
    "severity": "high"
  }'
```

### 3. SigNoz (Port 3301)

Observability platform for viewing traces, metrics, and logs.

**Access:**
- URL: http://localhost:3301
- Username: admin
- Password: (default)

**Features:**
- View real-time traces
- Monitor metrics
- View structured logs
- Set up alert rules

### 4. PostgreSQL (Port 5432)

Database for persisting incidents and analysis results.

**Credentials:**
- Host: localhost
- Port: 5432
- User: incident_user
- Password: incident_pass
- Database: incident_db

**Access via psql:**
```bash
docker exec -it incident-postgres psql -U incident_user -d incident_db

# View incidents
SELECT id, service_name, error_type, root_cause, status FROM incidents;
```

## Configure SigNoz alerts for the orchestrator

The platform **does not** automatically forward exceptions from Spring Boot to the orchestrator. Flow:

1. The app sends **OpenTelemetry** data to **`otel-collector`**, which forwards to **`signoz-otel-collector`** and into **ClickHouse**.
2. SigNoz shows traces in the UI (**http://localhost:3301**).
3. The orchestrator is notified only when a **SigNoz alert fires** and that alert delivers a webhook to **`POST /incidents`**.

Configure once in SigNoz (menus vary slightly by version; look under **Alerts** or **Settings**):

1. Open **http://localhost:3301** (often `admin` / `admin` on first install—change credentials if prompted).
2. Create a **notification channel** (or webhook **integration**) of type **Webhook** pointing to **`http://orchestrator:8000/incidents`**. Use the Compose hostname **`orchestrator`**, not `localhost`, because the request originates from SigNoz inside Docker.
3. Create an **alert rule** tied to telemetry you care about (for example thresholds on errors, spans, logs, or derived metrics—depending on availability in your SigNoz build).
4. Route that rule through the webhook channel and **enable** it.

Smoke-test the webhook from the host (bypasses SigNoz):

```bash
curl -s -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -d '{"alerts":[{"severity":"error","message":"manual webhook test"}]}'
```

You should see `{"status":"received",...}` and orchestrator logs with `docker compose logs -f orchestrator`.

Until steps 2–4 are done, **`GET http://localhost:8000/incidents` can stay empty** even when **`/error`** traces appear in SigNoz.

To exercise CrewAI without SigNoz, use **manual analysis** (`POST /incidents/analyze`) in Test 5 below.

## Testing the Platform

### Test 1: Health Checks

Verify HTTP responders and Postgres health:

```bash
curl -s http://localhost:8080/health
curl -s http://localhost:8000/health
docker compose ps postgres
docker compose logs --tail=50 otel-collector signoz-otel-collector
```

### Test 2: Trigger error — traces vs orchestrator incidents

**Path A (traces):** confirms OTLP ingestion.

```bash
curl -s http://localhost:8080/error
```

In **Services** or **Traces** at http://localhost:3301, find spans from your application (see `SPRING_APPLICATION_NAME`). If traces are missing, inspect logs for **`otel-collector`** and **`signoz-otel-collector`**.

**Path B (orchestrator):** runs only after [Configure SigNoz alerts](#configure-signoz-alerts-for-the-orchestrator). When your alert fires:

```bash
curl -s http://localhost:8000/incidents
```

Without webhook alerts, `/incidents` may stay empty—that is normal.

### Test 3: Payment Endpoint

Test business logic endpoint:

```bash
# Valid payment
curl http://localhost:8080/payment/123

# Invalid payment (ID 999 triggers error)
curl http://localhost:8080/payment/999
```

### Test 4: Manual Incident Analysis

Create and analyze an incident without SigNoz webhook:

```bash
curl -X POST "http://localhost:8000/incidents/analyze" \
  -d "service_name=auth-service" \
  -d "error_type=InvalidCredentialException" \
  -d "error_message=User credentials invalid" \
  -d "stacktrace=at com.auth.AuthService.validate(AuthService.java:127)" \
  -d "severity=high"
```

### Test 5: View Results in Database

```bash
# Connect to database
docker exec -it incident-postgres psql -U incident_user -d incident_db

# List all incidents
SELECT id, service_name, error_type, root_cause, status 
FROM incidents 
ORDER BY created_at DESC 
LIMIT 10;

# View specific incident
SELECT * FROM incidents WHERE id = 'your-incident-id';

# Exit
\q
```

### Test 6: View in SigNoz Dashboard

1. Open http://localhost:3301
2. Use **Services** or **Traces** to find your workload (often `SPRING_APPLICATION_NAME`, e.g. `incident-analyzer-app`).
3. Open a trace tied to **`/error`** (or trigger again and refresh).
4. Under **Alerts**, confirm rules are enabled and webhook delivery appears when you expect incidents in the orchestrator.

## Troubleshooting

### Services Won't Start

**Problem:** `docker-compose up` fails

**Solution:**
```bash
# Check Docker is running
docker ps

# Check for port conflicts
netstat -tuln | grep -E '8000|8080|5432|3301|4317'

# Check logs
docker-compose logs

# Full restart
docker-compose down
docker-compose up -d
```

### Can't Connect to Services

**Problem:** `curl: Failed to connect`

**Solution:**
```bash
# Check service status
docker-compose ps

# If not healthy, restart
docker-compose restart incident-spring-app
docker-compose restart incident-orchestrator

# Check logs
docker-compose logs incident-orchestrator
```

### Database Connection Issues

**Problem:** Orchestrator can't connect to PostgreSQL

**Solution:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker exec incident-postgres pg_isready

# Reset database
docker-compose down
docker volume rm incidentanalystagent_postgres_data
docker-compose up -d postgres
```

### CrewAI/OpenAI Errors

**Problem:** "Authentication error" or "Invalid API key"

**Solution:**
1. Verify API key in `.env`
2. Check key has API access enabled at https://platform.openai.com
3. Check API quota/usage limits
4. View logs: `docker-compose logs orchestrator`

### Webhook Not Triggering

**Problem:** SigNoz alerts don't trigger webhook

**Solution:**
1. Verify orchestrator is running: `curl http://localhost:8000/health`
2. Check SigNoz alerts configured correctly
3. View orchestrator logs: `docker-compose logs orchestrator`
4. Manually test: Use `/incidents/analyze` endpoint

### Timeout Issues

**Problem:** Requests timeout or hang

**Solution:**
```bash
# Increase Docker resource limits
# Edit docker-compose.yml and add:
#   deploy:
#     resources:
#       limits:
#         cpus: '2'
#         memory: 4G

docker-compose restart
```

## Next Steps

### 1. Configure SigNoz Alerts

1. Open http://localhost:3301
2. Go to Alerts → Alert Rules → New Alert
3. Create rule for HTTP 500 or exceptions
4. Set webhook URL: `http://orchestrator:8000/incidents`
5. Enable alert

### 2. Customize Agents

Edit `/orchestrator/agents/incident_analyst.py` to customize AI behavior:
- Modify agent roles and goals
- Adjust analysis prompts
- Add custom logic

### 3. Monitor Incidents

```bash
# Watch for new incidents
watch 'curl -s http://localhost:8000/incidents | jq .'

# Or check database
docker exec -it incident-postgres psql -U incident_user -d incident_db \
  -c "SELECT id, service_name, error_type, status FROM incidents ORDER BY created_at DESC LIMIT 5;"
```

### 4. View Application Logs

```bash
# Spring Boot logs
docker-compose logs -f spring-app

# Orchestrator logs
docker-compose logs -f orchestrator

# All logs
docker-compose logs -f
```

## Useful Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose stop

# Remove all (careful!)
docker-compose down

# View logs
docker-compose logs -f <service>

# Restart service
docker-compose restart <service>

# Execute command in container
docker exec -it <container> <command>

# Check service status
docker-compose ps

# View resource usage
docker stats

# Clean up unused Docker resources
docker system prune
```

## Performance Tips

1. **Allocate Resources**: Docker Desktop → Settings → Resources
   - Recommended: 4+ CPUs, 4GB+ memory

2. **Volume Optimization**:
   - Use named volumes instead of bind mounts
   - Already configured in docker-compose.yml

3. **Caching**:
   - Dependencies are cached in Docker layers
   - Rebuild images only when needed: `docker-compose build --no-cache`

## Security Notes (for POC)

This is a proof-of-concept. For production deployment, implement:

- ✅ API authentication and authorization
- ✅ Input validation and sanitization
- ✅ Rate limiting
- ✅ TLS/SSL encryption
- ✅ Secret management (not in .env)
- ✅ Network policies
- ✅ RBAC and audit logging

## Getting Help

1. Check logs: `docker-compose logs -f`
2. Review README files in each service directory
3. Check `.env` configuration
4. Verify OpenAI API key
5. Ensure ports are not in use

## Summary

You now have a fully functional AI-Assisted Incident Resolution Platform running locally!

**Key Services:**
- Spring Boot App → http://localhost:8080
- Orchestrator API → http://localhost:8000
- SigNoz UI → http://localhost:3301
- PostgreSQL → localhost:5432

**Next:** Trigger an error at http://localhost:8080/error and watch the incident flow through the system!
