#!/bin/bash

# Development startup script for Radio WiFi Configuration
# Starts both frontend (Nuxt) and backend (FastAPI) services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APP_DIR="$PROJECT_DIR/app"
BACKEND_DIR="$PROJECT_DIR/backend"

# Default ports
FRONTEND_PORT=3000
BACKEND_PORT=8000

# PID files for process management
FRONTEND_PID_FILE="/tmp/radio-frontend.pid"
BACKEND_PID_FILE="/tmp/radio-backend.pid"

# Log files
LOG_DIR="$PROJECT_DIR/logs"
FRONTEND_LOG="$LOG_DIR/frontend.log"
BACKEND_LOG="$LOG_DIR/backend.log"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0 # Port is in use
    else
        return 1 # Port is free
    fi
}

# Function to kill process by PID file
kill_by_pid_file() {
    local pid_file=$1
    local service_name=$2

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            print_info "Stopping $service_name (PID: $pid)..."
            kill "$pid"
            rm -f "$pid_file"
            print_success "$service_name stopped"
        else
            print_warning "$service_name PID file exists but process not running"
            rm -f "$pid_file"
        fi
    fi
}

# Function to cleanup on exit
cleanup() {
    print_info "Shutting down services..."
    kill_by_pid_file "$FRONTEND_PID_FILE" "Frontend"
    kill_by_pid_file "$BACKEND_PID_FILE" "Backend"
    exit 0
}

# Setup signal handlers
trap cleanup SIGINT SIGTERM

# Function to check dependencies
check_dependencies() {
    print_info "Checking dependencies..."

    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed"
        exit 1
    fi

    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed"
        exit 1
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi

    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        exit 1
    fi

    print_success "All dependencies found"
}

# Function to setup log directory
setup_logs() {
    mkdir -p "$LOG_DIR"

    # Rotate logs if they're too large (>10MB)
    for log_file in "$FRONTEND_LOG" "$BACKEND_LOG"; do
        if [ -f "$log_file" ] && [ $(stat -c%s "$log_file" 2>/dev/null || echo 0) -gt 10485760 ]; then
            mv "$log_file" "${log_file}.old"
        fi
    done
}

# Function to install frontend dependencies
install_frontend_deps() {
    print_info "Installing frontend dependencies..."
    cd "$APP_DIR"

    if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules/.package-lock.json" ]; then
        npm install
        print_success "Frontend dependencies installed"
    else
        print_info "Frontend dependencies are up to date"
    fi
}

# Function to install backend dependencies
install_backend_deps() {
    print_info "Installing backend dependencies..."
    cd "$BACKEND_DIR"

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install/upgrade pip
    pip install --upgrade pip

    # Install dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Backend dependencies installed"
    else
        print_warning "No requirements.txt found, installing minimal dependencies..."
        pip install fastapi uvicorn python-multipart
    fi
}

# Function to start the backend
start_backend() {
    print_info "Starting backend service..."
    cd "$BACKEND_DIR"

    # Check if port is already in use
    if check_port $BACKEND_PORT; then
        print_error "Backend port $BACKEND_PORT is already in use"
        exit 1
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Start backend in background
    nohup python main.py --host 0.0.0.0 --port $BACKEND_PORT > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$BACKEND_PID_FILE"

    # Wait a moment and check if it started successfully
    sleep 2
    if kill -0 $BACKEND_PID 2>/dev/null; then
        print_success "Backend started (PID: $BACKEND_PID) on port $BACKEND_PORT"
    else
        print_error "Backend failed to start. Check logs: $BACKEND_LOG"
        exit 1
    fi
}

# Function to start the frontend
start_frontend() {
    print_info "Starting frontend service..."
    cd "$APP_DIR"

    # Check if port is already in use
    if check_port $FRONTEND_PORT; then
        print_error "Frontend port $FRONTEND_PORT is already in use"
        exit 1
    fi

    # Set environment variables
    export NODE_ENV=development
    export NUXT_HOST=0.0.0.0
    export NUXT_PORT=$FRONTEND_PORT
    export API_HOST=localhost
    export API_PORT=$BACKEND_PORT

    # Start frontend in background
    nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$FRONTEND_PID_FILE"

    # Wait a moment and check if it started successfully
    sleep 3
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        print_success "Frontend started (PID: $FRONTEND_PID) on port $FRONTEND_PORT"
    else
        print_error "Frontend failed to start. Check logs: $FRONTEND_LOG"
        exit 1
    fi
}

# Function to wait for services to be ready
wait_for_services() {
    print_info "Waiting for services to be ready..."

    # Wait for backend
    local backend_ready=false
    for i in {1..30}; do
        if curl -s "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1; then
            backend_ready=true
            break
        fi
        sleep 1
    done

    if [ "$backend_ready" = true ]; then
        print_success "Backend is ready"
    else
        print_error "Backend health check failed"
        return 1
    fi

    # Wait for frontend
    local frontend_ready=false
    for i in {1..60}; do
        if curl -s "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
            frontend_ready=true
            break
        fi
        sleep 1
    done

    if [ "$frontend_ready" = true ]; then
        print_success "Frontend is ready"
    else
        print_error "Frontend health check failed"
        return 1
    fi
}

# Function to show status
show_status() {
    echo
    print_success "🚀 Radio WiFi Development Environment is running!"
    echo
    echo "📱 Frontend: http://localhost:$FRONTEND_PORT"
    echo "🔧 Backend:  http://localhost:$BACKEND_PORT"
    echo "📋 Health:   http://localhost:$BACKEND_PORT/health"
    echo
    echo "📊 Logs:"
    echo "   Frontend: $FRONTEND_LOG"
    echo "   Backend:  $BACKEND_LOG"
    echo
    echo "💡 Tips:"
    echo "   - Press Ctrl+C to stop all services"
    echo "   - Frontend will auto-reload on file changes"
    echo "   - Backend will restart automatically with --reload"
    echo "   - Use 'tail -f $LOG_DIR/*.log' to monitor logs"
    echo
}

# Function to monitor services
monitor_services() {
    while true; do
        # Check if processes are still running
        if [ -f "$FRONTEND_PID_FILE" ]; then
            local frontend_pid=$(cat "$FRONTEND_PID_FILE")
            if ! kill -0 "$frontend_pid" 2>/dev/null; then
                print_error "Frontend process died unexpectedly"
                cleanup
                exit 1
            fi
        fi

        if [ -f "$BACKEND_PID_FILE" ]; then
            local backend_pid=$(cat "$BACKEND_PID_FILE")
            if ! kill -0 "$backend_pid" 2>/dev/null; then
                print_error "Backend process died unexpectedly"
                cleanup
                exit 1
            fi
        fi

        sleep 5
    done
}

# Main execution
main() {
    print_info "Starting Radio WiFi Development Environment..."

    # Check dependencies
    check_dependencies

    # Setup logs
    setup_logs

    # Stop any existing services
    kill_by_pid_file "$FRONTEND_PID_FILE" "Frontend"
    kill_by_pid_file "$BACKEND_PID_FILE" "Backend"

    # Install dependencies
    install_backend_deps
    install_frontend_deps

    # Start services
    start_backend
    start_frontend

    # Wait for services to be ready
    if wait_for_services; then
        show_status

        # Monitor services
        monitor_services
    else
        print_error "Failed to start services properly"
        cleanup
        exit 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --frontend-port)
            FRONTEND_PORT="$2"
            shift 2
            ;;
        --backend-port)
            BACKEND_PORT="$2"
            shift 2
            ;;
        --stop)
            print_info "Stopping all services..."
            kill_by_pid_file "$FRONTEND_PID_FILE" "Frontend"
            kill_by_pid_file "$BACKEND_PID_FILE" "Backend"
            exit 0
            ;;
        --status)
            if [ -f "$FRONTEND_PID_FILE" ] && [ -f "$BACKEND_PID_FILE" ]; then
                frontend_pid=$(cat "$FRONTEND_PID_FILE")
                backend_pid=$(cat "$BACKEND_PID_FILE")

                if kill -0 "$frontend_pid" 2>/dev/null && kill -0 "$backend_pid" 2>/dev/null; then
                    print_success "Both services are running"
                    echo "Frontend PID: $frontend_pid"
                    echo "Backend PID: $backend_pid"
                    exit 0
                else
                    print_error "Some services are not running"
                    exit 1
                fi
            else
                print_error "Services are not running"
                exit 1
            fi
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  --frontend-port PORT  Set frontend port (default: 3000)"
            echo "  --backend-port PORT   Set backend port (default: 8000)"
            echo "  --stop               Stop all running services"
            echo "  --status             Check service status"
            echo "  --help, -h           Show this help message"
            echo
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main
