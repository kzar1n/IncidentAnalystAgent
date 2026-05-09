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

4. **Wait for services to be ready** (approximately 30-60 seconds)

```bash
docker-compose ps
```

All services should show "healthy" status.

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
│                  │                                            │
│                  ▼                                            │
│  ┌──────────────────────────────────────┐                   │
│  │   SigNoz (Port 3301)                 │                   │
│  │   Observability Platform             │                   │
│  │   - Traces, Metrics, Logs            │                   │
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

### 1. Verify Services

```bash
# Check all services are running
curl http://localhost:8080/health
curl http://localhost:8000/health
curl http://localhost:3301
```

### 2. Simulate an Error (Trigger Incident Analysis)

```bash
# This will trigger an exception
curl http://localhost:8080/error

# Check SigNoz UI for the error (http://localhost:3301)
# Wait a moment for the webhook to trigger
```

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

### Steps to Setup SigNoz Alert (Optional)

1. Open SigNoz UI: http://localhost:3301
2. Go to Alerts → Alert Rules
3. Create alert for HTTP 500 or exceptions
4. Set webhook to: `http://orchestrator:8000/incidents`
5. Enable the alert

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
