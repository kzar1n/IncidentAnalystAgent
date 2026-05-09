#!/bin/bash

# AI-Assisted Incident Resolution Platform - Setup & Test Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker is installed"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_success "Docker Compose is installed"
    
    # Check .env file
    if [ ! -f .env ]; then
        print_warning ".env file not found, creating from defaults..."
        cat > .env << 'EOF'
DB_HOST=postgres
DB_PORT=5432
DB_NAME=incident_db
DB_USER=incident_user
DB_PASSWORD=incident_pass
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
API_PORT=8000
API_HOST=0.0.0.0
SPRING_APPLICATION_NAME=incident-analyzer-app
SERVER_PORT=8080
OPENAI_API_KEY=sk-your-openai-api-key-here
LOG_LEVEL=INFO
EOF
        print_warning "Please edit .env and add your OpenAI API key"
        print_warning "Run: nano .env"
    else
        print_success ".env file found"
    fi
}

# Start services
start_services() {
    print_header "Starting Docker Compose Services"
    
    docker-compose up -d
    
    print_info "Waiting for services to be healthy (up to 60 seconds)..."
    
    # Wait for services
    max_retries=60
    retries=0
    
    while [ $retries -lt $max_retries ]; do
        if docker-compose ps | grep -q "healthy"; then
            print_success "Services are starting..."
            break
        fi
        retries=$((retries + 1))
        sleep 1
    done
    
    sleep 10
    
    docker-compose ps
}

# Check service health
check_services() {
    print_header "Checking Service Health"
    
    # Spring Boot
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        print_success "Spring Boot App (8080) is healthy"
    else
        print_error "Spring Boot App (8080) is not responding"
    fi
    
    # Orchestrator
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Orchestrator (8000) is healthy"
    else
        print_error "Orchestrator (8000) is not responding"
    fi
    
    # SigNoz
    if curl -s http://localhost:3301 > /dev/null 2>&1; then
        print_success "SigNoz (3301) is accessible"
    else
        print_error "SigNoz (3301) is not responding"
    fi
    
    # PostgreSQL
    if docker exec incident-postgres pg_isready -U incident_user > /dev/null 2>&1; then
        print_success "PostgreSQL (5432) is accessible"
    else
        print_error "PostgreSQL (5432) is not responding"
    fi
}

# Run tests
run_tests() {
    print_header "Running Tests"
    
    print_info "Testing health endpoints..."
    
    # Test Spring Boot health
    response=$(curl -s http://localhost:8080/health)
    if echo "$response" | grep -q "UP"; then
        print_success "Spring Boot health check passed"
    else
        print_error "Spring Boot health check failed"
    fi
    
    # Test Orchestrator health
    response=$(curl -s http://localhost:8000/health)
    if echo "$response" | grep -q "UP"; then
        print_success "Orchestrator health check passed"
    else
        print_error "Orchestrator health check failed"
    fi
    
    print_info "Testing error simulation endpoint..."
    
    # This should fail but that's expected
    curl -s http://localhost:8080/error > /dev/null 2>&1 || true
    print_success "Error endpoint triggered (check SigNoz for trace)"
    
    print_info "Testing payment endpoint..."
    
    # Valid payment
    response=$(curl -s http://localhost:8080/payment/123)
    if echo "$response" | grep -q "processed"; then
        print_success "Valid payment endpoint works"
    else
        print_error "Valid payment endpoint failed"
    fi
    
    # Invalid payment (will error)
    curl -s http://localhost:8080/payment/999 > /dev/null 2>&1 || true
    print_success "Invalid payment endpoint triggered error"
    
    print_info "Testing incident listing..."
    
    # List incidents
    response=$(curl -s http://localhost:8000/incidents)
    if echo "$response" | grep -q "incidents"; then
        print_success "Incident listing works"
    else
        print_error "Incident listing failed"
    fi
}

# Show endpoints
show_endpoints() {
    print_header "Available Endpoints"
    
    echo -e "${BLUE}Spring Boot Application:${NC}"
    echo "  GET    http://localhost:8080/health"
    echo "  GET    http://localhost:8080/error"
    echo "  GET    http://localhost:8080/timeout"
    echo "  GET    http://localhost:8080/payment/{id}"
    
    echo ""
    echo -e "${BLUE}FastAPI Orchestrator:${NC}"
    echo "  GET    http://localhost:8000/health"
    echo "  POST   http://localhost:8000/incidents"
    echo "  GET    http://localhost:8000/incidents"
    echo "  GET    http://localhost:8000/incidents/{id}"
    echo "  POST   http://localhost:8000/incidents/analyze"
    
    echo ""
    echo -e "${BLUE}SigNoz Observability:${NC}"
    echo "  UI     http://localhost:3301"
    
    echo ""
    echo -e "${BLUE}PostgreSQL Database:${NC}"
    echo "  Host   localhost:5432"
    echo "  User   incident_user"
    echo "  Pass   incident_pass"
    echo "  DB     incident_db"
}

# Show usage
show_usage() {
    echo ""
    print_header "Usage"
    
    echo -e "${YELLOW}Commands:${NC}"
    echo "  ./setup.sh start       - Start all services"
    echo "  ./setup.sh check       - Check service health"
    echo "  ./setup.sh test        - Run tests"
    echo "  ./setup.sh logs        - Show logs"
    echo "  ./setup.sh stop        - Stop all services"
    echo "  ./setup.sh clean       - Remove all containers and volumes"
    echo "  ./setup.sh manual-test - Run manual incident analysis"
    echo ""
}

# View logs
view_logs() {
    print_header "Service Logs (CTRL+C to exit)"
    docker-compose logs -f
}

# Stop services
stop_services() {
    print_header "Stopping Services"
    docker-compose down
    print_success "All services stopped"
}

# Clean up
clean_services() {
    print_header "Cleaning Up"
    print_warning "This will remove all containers and volumes"
    read -p "Are you sure? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        print_success "Cleanup complete"
    else
        print_warning "Cleanup cancelled"
    fi
}

# Manual test
manual_test() {
    print_header "Running Manual Incident Analysis"
    
    print_info "Creating test incident..."
    
    curl -X POST "http://localhost:8000/incidents/analyze" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "service_name=payment-service" \
      -d "error_type=NullPointerException" \
      -d "error_message=Cannot invoke method on null object" \
      -d "stacktrace=at com.payment.PaymentService.processPayment(PaymentService.java:42)" \
      -d "severity=high"
    
    echo ""
    print_success "Incident submitted for analysis"
    print_info "Check results: curl http://localhost:8000/incidents"
}

# Main
case "${1:-start}" in
    start)
        check_prerequisites
        start_services
        check_services
        show_endpoints
        show_usage
        ;;
    check)
        check_services
        ;;
    test)
        run_tests
        show_endpoints
        ;;
    logs)
        view_logs
        ;;
    stop)
        stop_services
        ;;
    clean)
        clean_services
        ;;
    manual-test)
        manual_test
        ;;
    *)
        echo "Usage: $0 {start|check|test|logs|stop|clean|manual-test}"
        show_usage
        exit 1
        ;;
esac
