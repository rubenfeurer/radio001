#!/bin/bash

# Backend Docker entrypoint script
# Handles initialization and startup for the FastAPI backend container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[BACKEND]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[BACKEND]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[BACKEND]${NC} $1"
}

print_error() {
    echo -e "${RED}[BACKEND]${NC} $1"
}

# Default values
API_PORT=${API_PORT:-8000}
WIFI_INTERFACE=${WIFI_INTERFACE:-wlan0}
NODE_ENV=${NODE_ENV:-production}

print_info "Starting Radio WiFi Backend..."
print_info "Environment: $NODE_ENV"
print_info "Port: $API_PORT"
print_info "WiFi Interface: $WIFI_INTERFACE"

# Check if running in development mode
if [ "$NODE_ENV" = "development" ]; then
    print_info "Development mode enabled"
    RELOAD_FLAG="--reload"
    LOG_LEVEL="debug"
else
    print_info "Production mode enabled"
    RELOAD_FLAG=""
    LOG_LEVEL="info"
fi

# Wait for any dependencies (if needed)
if [ -n "$WAIT_FOR_SERVICES" ]; then
    print_info "Waiting for dependencies..."
    sleep 5
fi

# Check Python environment
print_info "Python version: $(python --version)"
print_info "FastAPI installation: $(python -c 'import fastapi; print(fastapi.__version__)' 2>/dev/null || echo 'Not found')"

# Create necessary directories
mkdir -p /tmp/radio
mkdir -p /var/log/radio

# Set permissions for development
if [ "$NODE_ENV" = "development" ]; then
    # In development, we might need some additional setup
    print_info "Setting up development environment..."

    # Create mock system files for development
    mkdir -p /tmp/radio/mock
    echo "mock" > /tmp/radio/mock/interface_status
fi

# Health check function
health_check() {
    local max_attempts=30
    local attempt=0

    print_info "Performing health check..."

    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s "http://localhost:$API_PORT/health" >/dev/null 2>&1; then
            print_success "Backend is healthy"
            return 0
        fi

        attempt=$((attempt + 1))
        sleep 1
    done

    print_error "Health check failed after $max_attempts attempts"
    return 1
}

# Start the application
print_info "Starting FastAPI server..."

# Check if main.py exists
if [ ! -f "main.py" ]; then
    print_error "main.py not found in current directory"
    print_error "Current directory: $(pwd)"
    print_error "Directory contents:"
    ls -la
    exit 1
fi

# Export environment variables for the application
export API_PORT
export WIFI_INTERFACE
export NODE_ENV
export PYTHONPATH=/app
export PYTHONUNBUFFERED=1

# Handle different startup scenarios
case "${1:-start}" in
    start)
        # Normal startup
        exec python main.py \
            --host 0.0.0.0 \
            --port "$API_PORT" \
            --log-level "$LOG_LEVEL" \
            $RELOAD_FLAG
        ;;

    dev)
        # Development startup with additional debugging
        print_info "Starting in development mode with debugging..."
        exec python main.py \
            --host 0.0.0.0 \
            --port "$API_PORT" \
            --log-level debug \
            --reload \
            --reload-dir /app
        ;;

    uvicorn)
        # Direct uvicorn startup
        print_info "Starting with uvicorn directly..."
        exec uvicorn main:app \
            --host 0.0.0.0 \
            --port "$API_PORT" \
            --log-level "$LOG_LEVEL" \
            $RELOAD_FLAG
        ;;

    test)
        # Run tests
        print_info "Running tests..."
        if [ -f "requirements-dev.txt" ]; then
            pip install -r requirements-dev.txt
        fi
        exec python -m pytest -v
        ;;

    shell)
        # Interactive shell
        print_info "Starting interactive shell..."
        exec /bin/bash
        ;;

    health)
        # Health check only
        health_check
        exit $?
        ;;

    *)
        # Pass through any other command
        print_info "Executing custom command: $*"
        exec "$@"
        ;;
esac
