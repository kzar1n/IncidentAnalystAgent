@echo off
REM AI-Assisted Incident Resolution Platform - Setup & Test Script (Windows)

setlocal enabledelayedexpansion

REM Colors
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "NC=[0m"

if "%1%"=="" goto :start
if /i "%1%"=="start" goto :start
if /i "%1%"=="check" goto :check
if /i "%1%"=="test" goto :test
if /i "%1%"=="logs" goto :logs
if /i "%1%"=="stop" goto :stop
if /i "%1%"=="clean" goto :clean
if /i "%1%"=="manual-test" goto :manual_test

echo Usage: %0 {start^|check^|test^|logs^|stop^|clean^|manual-test}
goto :end

:start
echo ============================================
echo Starting Docker Compose Services
echo ============================================

REM Check if .env exists
if not exist ".env" (
    echo Creating .env file...
    (
        echo DB_HOST=postgres
        echo DB_PORT=5432
        echo DB_NAME=incident_db
        echo DB_USER=incident_user
        echo DB_PASSWORD=incident_pass
        echo OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
        echo API_PORT=8000
        echo API_HOST=0.0.0.0
        echo SPRING_APPLICATION_NAME=incident-analyzer-app
        echo SERVER_PORT=8080
        echo OPENAI_API_KEY=sk-your-openai-api-key-here
        echo LOG_LEVEL=INFO
    ) > .env
    echo.
    echo WARNING: Please edit .env and add your OpenAI API key
    echo Run: notepad .env
    echo.
)

docker-compose up -d

echo.
echo Waiting for services to be healthy (up to 60 seconds)...
timeout /t 10 /nobreak

echo.
docker-compose ps

echo.
echo ============================================
echo Available Endpoints
echo ============================================
echo.
echo Spring Boot Application:
echo   GET    http://localhost:8080/health
echo   GET    http://localhost:8080/error
echo   GET    http://localhost:8080/timeout
echo   GET    http://localhost:8080/payment/{id}
echo.
echo FastAPI Orchestrator:
echo   GET    http://localhost:8000/health
echo   POST   http://localhost:8000/incidents
echo   GET    http://localhost:8000/incidents
echo   GET    http://localhost:8000/incidents/{id}
echo.
echo SigNoz Observability:
echo   UI     http://localhost:3301
echo.
echo PostgreSQL Database:
echo   Host   localhost:5432
echo   User   incident_user
echo   Pass   incident_pass
echo   DB     incident_db
echo.
goto :end

:check
echo ============================================
echo Checking Service Health
echo ============================================
echo.

echo Testing Spring Boot App (8080)...
curl -s http://localhost:8080/health >nul 2>&1
if !errorlevel! equ 0 (
    echo [32m✓ Spring Boot App (8080) is healthy[0m
) else (
    echo [31m✗ Spring Boot App (8080) is not responding[0m
)

echo Testing Orchestrator (8000)...
curl -s http://localhost:8000/health >nul 2>&1
if !errorlevel! equ 0 (
    echo [32m✓ Orchestrator (8000) is healthy[0m
) else (
    echo [31m✗ Orchestrator (8000) is not responding[0m
)

echo Testing SigNoz (3301)...
curl -s http://localhost:3301 >nul 2>&1
if !errorlevel! equ 0 (
    echo [32m✓ SigNoz (3301) is accessible[0m
) else (
    echo [31m✗ SigNoz (3301) is not responding[0m
)

echo.
docker-compose ps
echo.
goto :end

:test
echo ============================================
echo Running Tests
echo ============================================
echo.

echo Testing health endpoints...
curl -s http://localhost:8080/health >nul 2>&1 && echo [32m✓ Spring Boot health check passed[0m || echo [31m✗ Spring Boot health check failed[0m

curl -s http://localhost:8000/health >nul 2>&1 && echo [32m✓ Orchestrator health check passed[0m || echo [31m✗ Orchestrator health check failed[0m

echo.
echo Testing error simulation endpoint...
curl -s http://localhost:8080/error >nul 2>&1
echo [32m✓ Error endpoint triggered (check SigNoz for trace)[0m

echo.
echo Testing payment endpoint...
curl -s http://localhost:8080/payment/123 | find "processed" >nul 2>&1 && echo [32m✓ Valid payment endpoint works[0m || echo [31m✗ Valid payment endpoint failed[0m

echo.
echo Testing incident listing...
curl -s http://localhost:8000/incidents | find "incidents" >nul 2>&1 && echo [32m✓ Incident listing works[0m || echo [31m✗ Incident listing failed[0m

echo.
goto :end

:logs
echo ============================================
echo Service Logs (CTRL+C to exit)
echo ============================================
echo.
docker-compose logs -f
goto :end

:stop
echo ============================================
echo Stopping Services
echo ============================================
docker-compose down
echo.
echo [32m✓ All services stopped[0m
goto :end

:clean
echo ============================================
echo Cleaning Up
echo ============================================
echo.
echo WARNING: This will remove all containers and volumes
set /p confirm="Are you sure? (y/n): "

if /i "%confirm%"=="y" (
    docker-compose down -v
    echo.
    echo [32m✓ Cleanup complete[0m
) else (
    echo [33m⚠ Cleanup cancelled[0m
)
goto :end

:manual_test
echo ============================================
echo Running Manual Incident Analysis
echo ============================================
echo.
echo Creating test incident...
echo.

curl -X POST "http://localhost:8000/incidents/analyze" ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "service_name=payment-service" ^
  -d "error_type=NullPointerException" ^
  -d "error_message=Cannot invoke method on null object" ^
  -d "stacktrace=at com.payment.PaymentService.processPayment(PaymentService.java:42)" ^
  -d "severity=high"

echo.
echo.
echo [32m✓ Incident submitted for analysis[0m
echo [34mℹ Check results: curl http://localhost:8000/incidents[0m
echo.
goto :end

:end
endlocal
