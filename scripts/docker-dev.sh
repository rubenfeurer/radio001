#!/bin/bash

# Docker-based development script for Radio WiFi Configuration
# Manages Docker Compose services for frontend and backend development

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
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
COMPOSE_PROD_FILE="$PROJECT_DIR/docker-compose.prod.yml"

# Detect platform for Apple Silicon optimization
PLATFORM=$(uname -m)
COMPOSE_OVERRIDE=""
if [[ "$PLATFORM" == "arm64" || "$PLATFORM" == "aarch64" ]]; then
    COMPOSE_OVERRIDE="-f $PROJECT_DIR/docker-compose.override.yml"
    print_info "Detected Apple Silicon (arm64) - using optimized configuration"
fi

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

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    if ! command -v docker-compose >/dev/null 2>&1; then
        print_error "docker-compose is not installed. Please install Docker Compose."
        exit 1
    fi

    print_info "Docker platform: $PLATFORM"
}

# Function to check if services are running
check_services() {
    local running_services
    running_services=$(docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE ps --services --filter "status=running" 2>/dev/null || echo "")

    if [[ -n "$running_services" ]]; then
        return 0  # Services are running
    else
        return 1  # No services running
    fi
}

# Function to start development environment
start_dev() {
    print_info "Starting Radio WiFi development environment..."

    cd "$PROJECT_DIR"

    # Build and start services
    print_info "Building Docker images..."
    if [[ "$PLATFORM" == "arm64" || "$PLATFORM" == "aarch64" ]]; then
        print_info "Using Apple Silicon optimized build..."
        docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE build --no-cache
    else
        docker-compose -f "$COMPOSE_FILE" build
    fi

    print_info "Starting services..."
    docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE up -d

    # Wait for services to be healthy
    print_info "Waiting for services to be ready..."

    local max_attempts=60
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE ps | grep -q "Up (healthy)"; then
            break
        fi

        if [ $((attempt % 10)) -eq 0 ]; then
            print_info "Still waiting for services... (${attempt}/${max_attempts})"
        fi

        sleep 3
        attempt=$((attempt + 1))
    done

    # Check final status
    if check_services; then
        print_success "🚀 Radio WiFi Development Environment is running!"
        echo
        echo "📱 Frontend: http://localhost:3000"
        echo "🔧 Backend:  http://localhost:8000"
        echo "📋 API Docs: http://localhost:8000/docs"
        echo "🐳 Traefik:  http://localhost:8080 (run with --traefik)"
        echo
        echo "📊 Useful commands:"
        echo "   $0 logs       - View logs"
        echo "   $0 status     - Check service status"
        echo "   $0 stop       - Stop all services"
        echo "   $0 restart    - Restart services"
        echo
        return 0
    else
        print_error "Failed to start services properly"
        show_status
        return 1
    fi
}

# Function to stop development environment
stop_dev() {
    print_info "Stopping Radio WiFi development environment..."

    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE down

    print_success "Services stopped"
}

# Function to restart development environment
restart_dev() {
    print_info "Restarting Radio WiFi development environment..."

    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE restart

    print_success "Services restarted"
}

# Function to show service status
show_status() {
    print_info "Service status:"

    cd "$PROJECT_DIR"

    if check_services; then
        echo
        docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE ps
        echo
        print_info "Service health:"
        docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
    else
        print_warning "No services are currently running"
        echo
        print_info "Run '$0 start' to start the development environment"
    fi
}

# Function to show logs
show_logs() {
    local service="$1"

    cd "$PROJECT_DIR"

    if [[ -n "$service" ]]; then
        print_info "Showing logs for service: $service"
        docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE logs -f "$service"
    else
        print_info "Showing logs for all services (Ctrl+C to exit)"
        docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE logs -f
    fi
}

# Function to open shell in service
open_shell() {
    local service="$1"

    if [[ -z "$service" ]]; then
        print_error "Service name required. Available services: radio-app, radio-backend"
        return 1
    fi

    cd "$PROJECT_DIR"

    print_info "Opening shell in $service..."
    docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE exec "$service" /bin/bash 2>/dev/null || \
    docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE exec "$service" /bin/sh
}

# Function to rebuild services
rebuild() {
    local service="$1"

    cd "$PROJECT_DIR"

    if [[ -n "$service" ]]; then
        print_info "Rebuilding service: $service"
        docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE build --no-cache "$service"
        docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE up -d "$service"
    else
        print_info "Rebuilding all services..."
        docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE build --no-cache
        docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE up -d
    fi

    print_success "Rebuild complete"
}

# Function to clean up Docker resources
cleanup() {
    print_info "Cleaning up Docker resources..."

    cd "$PROJECT_DIR"

    # Stop and remove containers
    docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE down -v

    # Remove unused images
    docker image prune -f

    # Remove unused volumes
    docker volume prune -f

    print_success "Cleanup complete"
}

# Function to start with additional services
start_with_services() {
    local profiles="$1"

    print_info "Starting with additional services: $profiles"

    cd "$PROJECT_DIR"

    if [[ "$profiles" == "traefik" ]]; then
        COMPOSE_PROFILES=traefik docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE up -d
        print_success "Started with Traefik reverse proxy"
        echo "🌐 Access via: http://radio.local"
        echo "🐳 Traefik dashboard: http://localhost:8080"
    elif [[ "$profiles" == "mdns" ]]; then
        COMPOSE_PROFILES=mdns docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE up -d
        print_success "Started with mDNS support"
        echo "🌐 Access via: http://radio.local"
    elif [[ "$profiles" == "all" ]]; then
        COMPOSE_PROFILES=traefik,mdns docker-compose -f "$COMPOSE_FILE" $COMPOSE_OVERRIDE up -d
        print_success "Started with all optional services"
        echo "🌐 Access via: http://radio.local"
        echo "🐳 Traefik dashboard: http://localhost:8080"
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  start              Start development environment"
    echo "  stop               Stop development environment"
    echo "  restart            Restart development environment"
    echo "  status             Show service status"
    echo "  logs [service]     Show logs (all services or specific service)"
    echo "  shell <service>    Open shell in service container"
    echo "  rebuild [service]  Rebuild Docker images"
    echo "  cleanup            Clean up Docker resources"
    echo "  --traefik          Start with Traefik reverse proxy"
    echo "  --mdns             Start with mDNS support"
    echo "  --all              Start with all optional services"
    echo
    echo "Examples:"
    echo "  $0 start                    # Start basic development environment"
    echo "  $0 start --traefik          # Start with Traefik for radio.local access"
    echo "  $0 logs radio-backend       # Show backend logs"
    echo "  $0 shell radio-app          # Open shell in frontend container"
    echo "  $0 rebuild radio-backend    # Rebuild only backend service"
    echo
    echo "Services:"
    echo "  radio-app       Frontend (Nuxt 3) on port 3000"
    echo "  radio-backend   Backend (FastAPI) on port 8000"
    echo
}

# Main execution
main() {
    # Check Docker
    check_docker

    # Parse command line arguments
    case "${1:-start}" in
        start)
            case "${2:-}" in
                --traefik)
                    start_with_services "traefik"
                    ;;
                --mdns)
                    start_with_services "mdns"
                    ;;
                --all)
                    start_with_services "all"
                    ;;
                "")
                    start_dev
                    ;;
                *)
                    print_error "Unknown option: $2"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        stop)
            stop_dev
            ;;
        restart)
            restart_dev
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        shell)
            open_shell "$2"
            ;;
        rebuild)
            rebuild "$2"
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Handle Ctrl+C gracefully
trap 'echo; print_info "Use \"$0 stop\" to stop services"; exit 0' INT

# Run main function
main "$@"
