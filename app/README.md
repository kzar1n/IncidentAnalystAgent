# Incident Analyzer App

Spring Boot application with OpenTelemetry observability for the AI-Assisted Incident Resolution Platform.

## Overview

This is a sample Spring Boot application that demonstrates:
- REST API endpoints for incident simulation
- OpenTelemetry integration for tracing, metrics, and logs
- SigNoz observability platform integration
- Structured logging with correlation IDs

## Features

- **Health Check**: `/health` - Returns application status
- **Error Simulation**: `/error` - Throws intentional exception
- **Timeout Simulation**: `/timeout` - Simulates 15 second delay
- **Payment Service**: `/payment/{id}` - Sample business logic endpoint
- **OpenTelemetry**: Automatic tracing and metrics export
- **Structured Logging**: JSON logs with trace context

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

Traces and metrics are automatically exported to:
- OpenTelemetry Collector (OTLP)
- SigNoz Dashboard (http://localhost:3301)

## Requirements

- Java 21
- Maven 3.9+
- Docker & Docker Compose (for full stack)
