# Getting Started Guide

This guide will walk you through setting up and running the AI-Assisted Incident Resolution Platform locally using Docker.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Service Overview](#service-overview)
4. [Testing the Platform](#testing-the-platform)
5. [Troubleshooting](#troubleshooting)

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

Monitor service startup:

```bash
docker-compose ps
```

Wait until all services show "healthy" status:

```
NAME                    STATUS              PORTS
incident-postgres       Up 2 minutes        0.0.0.0:5432->5432/tcp
incident-otel-collector Up 2 minutes        0.0.0.0:4317->4317/tcp, 0.0.0.0:4318->4318/tcp
incident-clickhouse     Up 2 minutes        0.0.0.0:8123->8123/tcp, 9000/tcp
incident-signoz         Up 1 minute         0.0.0.0:3301->3301/tcp
incident-spring-app     Up 45 seconds       0.0.0.0:8080->8080/tcp
incident-orchestrator   Up 30 seconds       0.0.0.0:8000->8000/tcp
```

### 5. Verify Services Are Running

```bash
# Test Spring Boot App
curl http://localhost:8080/health

# Test Orchestrator
curl http://localhost:8000/health

# Expected response:
# {"status":"UP"}
```

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

## Testing the Platform

### Test 1: Health Checks

Verify all services are running:

```bash
# Spring Boot
curl http://localhost:8080/health

# Orchestrator
curl http://localhost:8000/health

# Both should return: {"status":"UP"}
```

### Test 2: Trigger Error (Incident Generation)

Generate an error to test the incident pipeline:

```bash
# Trigger error
curl http://localhost:8080/error

# Wait a moment for processing
sleep 2

# Check for incident
curl http://localhost:8000/incidents
```

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
2. Navigate to "Services" section
3. Look for "incident-analyzer-app"
4. Click to view traces and metrics
5. Check "Alerts" for triggered alerts

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
