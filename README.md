# AI-Assisted Incident Resolution Platform - POC

A proof-of-concept platform for AI-assisted incident resolution using OpenTelemetry, SigNoz, and CrewAI agents.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (for CrewAI agents)
- Java 21+ (optional, for local Spring Boot development)
- Python 3.12+ (optional, for local orchestrator development)

### Setup

1. **Clone the repository**

```bash
cd IncidentAnalystAgent
```

2. **Configure environment**

```bash
# Edit .env and add your OpenAI API key
nano .env
# Set: OPENAI_API_KEY=sk-your-key-here
```

3. **Start all services**

```bash
docker-compose up -d
```

4. **Wait for containers to stabilize** (first boot can take longer while ClickHouse/ZooKeeper and migrations run):

```bash
docker compose ps
```

Services with **`HEALTHCHECK`** show `(healthy)` in `docker ps`. **`otel-collector`** and **`signoz-otel-collector`** may appear only as **`Up`** with no healthy label—they are still required. Jobs **`init-clickhouse`** and **`signoz-telemetrystore-migrator`** often exit with **`Exited (0)`** after succeeding.

**Telemetry path:**  
`spring-app` → **`otel-collector`** (inside Compose) → **`signoz-otel-collector`** (OTLP ingress; host ports **4317/4318**) → **ClickHouse** → **SigNoz UI** on **http://localhost:3301**.

**Incident path:**  
SigNoz **never** pushes to the orchestrator by default. Configure an **alert** with a **webhook** URL **`http://orchestrator:8000/incidents`** (Docker network hostname `orchestrator`). See **[GETTING_STARTED.md](GETTING_STARTED.md#configure-signoz-alerts-for-the-orchestrator)** for step-by-step instructions.

## 📋 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Incident Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Spring Boot App          FastAPI Orchestrator               │
│  (Port 8080)              (Port 8000)                         │
│  ├─ /health              ├─ /health                          │
│  ├─ /error               ├─ /incidents                       │
│  ├─ /timeout             ├─ /incidents/{id}                  │
│  └─ /payment/{id}        └─ /incidents/analyze               │
│        │                         │                            │
│        │ OpenTelemetry           │ CrewAI Agents             │
│        ▼                         ▼                            │
│  ┌──────────────────────────────────────┐                   │
│  │  OpenTelemetry Collector (4317)      │                   │
│  └──────────────────────────────────────┘                   │
│        │                         │                            │
│        └─────────┬───────────────┘                           │
│                  │ OTLP                                         │
│                  ▼                                            │
│  ┌──────────────────────────────────────┐                   │
│  │  SigNoz OTel Collector (4317/4318)    │                   │
│  └──────────────────────────────────────┘                   │
│                  │                                            │
│                  ▼                                            │
│  ┌──────────────────────────────────────┐                   │
│  │   SigNoz UI (localhost:3301)          │                   │
│  │   + ClickHouse + alerts/webhooks       │                   │
│  └──────────────────────────────────────┘                   │
│                  │                                            │
│                  │ Webhook on Alert                          │
│                  ▼                                            │
│  ┌──────────────────────────────────────┐                   │
│  │  FastAPI Orchestrator                │                   │
│  │  - Parse webhook                     │                   │
│  │  - Create incident                   │                   │
│  │  - Analyze with CrewAI               │                   │
│  └──────────────────────────────────────┘                   │
│                  │                                            │
│                  ▼                                            │
│  ┌──────────────────────────────────────┐                   │
│  │   PostgreSQL (Port 5432)             │                   │
│  │   - Incident Storage                 │                   │
│  │   - Analysis Results                 │                   │
│  └──────────────────────────────────────┘                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 🧪 Testing the Platform

### 1. Verify stack health

Containers (run `docker compose ps`):

| Essentials | Purpose |
|------------|---------|
| postgres, zookeeper-1, clickhouse | Persist incidents + telemetry store |
| signoz, **signoz-otel-collector** | UI/API + OTLP intake to ClickHouse |
| **otel-collector**, spring-app, orchestrator | App telemetry gateway + orchestration |

Smoke tests:

```bash
curl -s http://localhost:8080/health
curl -s http://localhost:8000/health
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3301/
docker compose logs --tail=30 signoz-otel-collector otel-collector
```

### 2. Simulate an error (telemetry vs webhook)

```bash
# Exception is traced by OpenTelemetry
curl http://localhost:8080/error
```

Verify the trace under **Services / Traces** at http://localhost:3301.  
**Incident creation in the orchestrator** requires a SigNoz **alert rule** wired to webhook **`http://orchestrator:8000/incidents`** (see GETTING_STARTED). Without that configuration, **`GET /incidents` may stay empty** even when telemetry looks healthy.

### 3. View Incidents

```bash
# List incidents
curl http://localhost:8000/incidents

# Get specific incident
curl http://localhost:8000/incidents/{incident_id}
```

### 4. Manual Incident Analysis (Testing without SigNoz)

```bash
curl -X POST "http://localhost:8000/incidents/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "payment-service",
    "error_type": "NullPointerException",
    "error_message": "Cannot invoke method on null object",
    "stacktrace": "at com.payment.PaymentService.processPayment(PaymentService.java:42)",
    "severity": "high"
  }'
```

### 5. Other Test Endpoints

```bash
# Simulate timeout
curl http://localhost:8080/timeout

# Test payment endpoint with valid ID
curl http://localhost:8080/payment/123

# Test payment endpoint with invalid ID (triggers error)
curl http://localhost:8080/payment/999
```

## 📊 Observability UI

### SigNoz Dashboard

- **URL**: http://localhost:3301
- View real-time traces, metrics, and logs
- Set up alert rules to trigger webhooks

### Configure SigNoz → orchestrator webhook (required for `/incidents` from telemetry)

Follow **[GETTING_STARTED.md — Configure SigNoz alerts](GETTING_STARTED.md#configure-signoz-alerts-for-the-orchestrator)**. Summary:

1. SigNoz UI → create a **webhook notification channel**: `POST` **`http://orchestrator:8000/incidents`** (hostname **`orchestrator`** on the Compose network).
2. **Alerts** → new **rule** for the signal you trigger (thresholds vary by datasource).
3. Attach the webhook channel and **enable** the rule.

## 🗄️ Database

### PostgreSQL Access

```bash
# Connect to database
docker exec -it incident-postgres psql -U incident_user -d incident_db

# View incidents table
SELECT * FROM incidents;

# Query example
SELECT id, service_name, error_type, root_cause, status 
FROM incidents 
ORDER BY created_at DESC;
```

## 📁 Project Structure

```
IncidentAnalystAgent/
├── app/                          # Spring Boot Application
│   ├── src/main/java/           # Java source code
│   ├── pom.xml                  # Maven dependencies
│   ├── Dockerfile               # Container configuration
│   └── README.md                # App documentation
│
├── orchestrator/                # FastAPI Orchestrator
│   ├── agents/                  # CrewAI agents
│   ├── services/                # Business logic
│   ├── api/                     # FastAPI routes
│   ├── models/                  # Data models
│   ├── main.py                  # FastAPI app
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Container configuration
│   └── README.md                # Orchestrator documentation
│
├── infrastructure/              # Infrastructure config
│   └── otel-collector-config.yml # OpenTelemetry setup
│
├── docker-compose.yml           # Docker Compose orchestration
├── .env                         # Environment variables
├── README.md                    # This file
└── spec.md                      # Technical specification
```

## 🔧 Development

### Local Spring Boot Development

```bash
cd app
mvn clean package
mvn spring-boot:run
```

### Local Orchestrator Development

```bash
cd orchestrator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs -f

# Restart services
docker-compose restart

# Full restart
docker-compose down
docker-compose up -d
```

### Database Connection Issues

```bash
# Check PostgreSQL
docker exec incident-postgres pg_isready

# Reinitialize database
docker-compose down
docker volume rm incidentanalystagent_postgres_data
docker-compose up -d postgres
```

### Webhook Not Triggering

1. Ensure SigNoz is running and healthy
2. Check alert rules in SigNoz UI
3. Verify orchestrator is accessible at `http://orchestrator:8000/incidents`
4. Check logs: `docker-compose logs -f orchestrator`

### CrewAI Issues

1. Verify OPENAI_API_KEY is set correctly in .env
2. Check orchestrator logs for API errors
3. Ensure you have API quota in OpenAI account

## 📈 Performance & Scalability

### Current Limitations (POC)

- Single-threaded incident processing
- No distributed queue system
- In-memory CrewAI execution
- Basic webhook retry logic

### Future Improvements

- Message queue (Redis, RabbitMQ)
- Horizontal scaling with load balancer
- Advanced caching strategies
- Enhanced error recovery
- Kubernetes deployment

## 🔐 Security Notes

### For Production Deployment

⚠️ **This is a POC. Do NOT deploy to production without:**

1. ✅ Authentication/Authorization
2. ✅ API rate limiting
3. ✅ Request validation
4. ✅ TLS/SSL encryption
5. ✅ Secret management (Vault)
6. ✅ Network isolation
7. ✅ RBAC policies
8. ✅ Audit logging

## 📚 API Documentation

### Complete API Reference

#### Health Check
```http
GET /health
```

#### Receive SigNoz Webhook
```http
POST /incidents
Content-Type: application/json

{
  "alerts": [...],
  "error_message": "string",
  "error_type": "string",
  "stacktrace": "string",
  "service_name": "string",
  "severity": "string",
  "timestamp": "string"
}
```

#### List Incidents
```http
GET /incidents?limit=50&offset=0
```

#### Get Incident
```http
GET /incidents/{incident_id}
```

#### Manual Analysis
```http
POST /incidents/analyze?service_name=string&error_type=string&error_message=string&stacktrace=string
```

## 🎯 Success Criteria (from Specification)

- ✅ All containers start successfully
- ✅ Spring Boot app exposes REST endpoints
- ✅ OpenTelemetry exports traces to SigNoz
- ✅ SigNoz detects errors and displays them
- ✅ Orchestrator receives webhook events
- ✅ CrewAI analyzes incidents
- ✅ Results persist to PostgreSQL
- ✅ Root cause analysis is generated
- ✅ Fix suggestions are provided

## 🚦 Next Steps

1. **Configure SigNoz Alerts**: Set up webhook triggers in SigNoz
2. **Test Full Flow**: Generate errors and verify analysis
3. **Review Results**: Check database for stored incidents
4. **Customize Agents**: Modify CrewAI agent prompts
5. **Integrate Systems**: Connect to your actual services

## 📞 Support

For issues or questions:

1. Check logs: `docker-compose logs -f <service-name>`
2. Review specification: `spec.md`
3. Check service README files
4. Verify environment configuration in `.env`

## 📝 License

This project is provided as a proof-of-concept for AI-assisted incident resolution.

## 🙏 Acknowledgments

- OpenTelemetry for observability standards
- SigNoz for open-source observability platform
- CrewAI for AI agent framework
- Spring Boot for robust backend framework
- FastAPI for high-performance API framework
