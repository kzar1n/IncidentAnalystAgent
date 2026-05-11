# Incident Analyzer App

Spring Boot application with OpenTelemetry observability for the AI-Assisted Incident Resolution Platform.

## Overview

This is a sample Spring Boot application that demonstrates:

- REST API endpoints for incident simulation
- OpenTelemetry **traces**, **metrics**, and **logs** export over OTLP to the Compose `otel-collector` (seen in SigNoz after the Signoz ingestion pipeline processes them)
- SigNoz integration

Traces alone do **not** populate the Logs view in SigNoz. Logs are bridged separately via **`SdkLoggerProvider`** + **`io.opentelemetry.instrumentation:opentelemetry-logback-appender-1.0`** (see `logback-spring.xml` and `OpenTelemetryLoggingConfiguration`).

## Features

- **Health Check**: `/health` - Returns application status
- **Error Simulation**: `/error` - Throws intentional exception
- **Timeout Simulation**: `/timeout` - Simulates 15 second delay
- **Payment Service**: `/payment/{id}` - Sample business logic endpoint
- **OpenTelemetry**: Tracing, metrics (Micrometer OTLP), and **Logback logs** via OTLP Log Records

## Quick Start

### Local Development

```bash
# Build the application
mvn clean package

# Run locally
mvn spring-boot:run
```

### Docker

```bash
# Build Docker image
docker build -t incident-analyzer-app:latest .

# Run in Docker
docker run -p 8080:8080 \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
  incident-analyzer-app:latest
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8080/health
```

### Simulate Error
```bash
curl http://localhost:8080/error
```

### Simulate Timeout
```bash
curl http://localhost:8080/timeout
```

### Get Payment
```bash
# Valid payment
curl http://localhost:8080/payment/123

# Invalid payment (will error)
curl http://localhost:8080/payment/999
```

## Configuration

Configure via environment variables:

- `SERVER_PORT` - Port number (default: 8080)
- `OTEL_EXPORTER_OTLP_ENDPOINT` - OpenTelemetry collector endpoint
- `SPRING_APPLICATION_NAME` - Application name for tracing

## Monitoring

Traces, metrics, and Logback **`INFO+`** logs are exported as OTLP to the Collector (`4317`), then forwarded to SigNoz’s OTel Collector and written to ClickHouse.

In SigNoz, confirm under **Logs** (filter by **`service.name`**, aligned with **`spring.application.name`**). If Logs is empty, verify `docker compose logs otel-collector` / `signoz-otel-collector` for ingestion errors—not just Traces working.

## Requirements

- Java 21
- Maven 3.9+
- Docker & Docker Compose (for full stack)
