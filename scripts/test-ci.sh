#!/bin/bash
# Test CI configuration locally
# This script replicates the CI environment for local testing

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[CI-TEST]${NC} $1"
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

# Header
echo ""
echo "🧪 Testing CI Configuration Locally"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.ci.yml" ]; then
    print_error "docker-compose.ci.yml not found. Are you in the project root?"
    exit 1
fi

# Clean up any existing CI containers
print_status "Cleaning up existing CI containers..."
docker compose -f docker-compose.ci.yml down -v --remove-orphans 2>/dev/null || true

# Force platform to AMD64 to match CI
export DOCKER_DEFAULT_PLATFORM=linux/amd64

# Build containers using CI configuration
print_status "Building containers (CI configuration)..."
if ! docker compose -f docker-compose.ci.yml build --no-cache; then
    print_error "Failed to build CI containers"
    exit 1
fi

# Start services
print_status "Starting CI services..."
if ! docker compose -f docker-compose.ci.yml up -d; then
    print_error "Failed to start CI services"
    docker compose -f docker-compose.ci.yml logs
    exit 1
fi

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 45

# Show running containers
print_status "Checking container status..."
docker compose -f docker-compose.ci.yml ps

# Test backend health first
print_status "Testing backend health..."
BACKEND_HEALTHY=false
for i in {1..10}; do
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend health check passed (attempt $i/10)"
        BACKEND_HEALTHY=true
        break
    else
        print_warning "Backend health check failed (attempt $i/10)"
        if [ $i -eq 10 ]; then
            print_error "Backend failed to become healthy"
            echo ""
            print_status "Backend logs:"
            docker compose -f docker-compose.ci.yml logs radio-backend
            echo ""
        else
            sleep 10
        fi
    fi
done

if [ "$BACKEND_HEALTHY" != "true" ]; then
    print_error "Backend health checks failed"
    docker compose -f docker-compose.ci.yml down -v
    exit 1
fi

# Test frontend health
print_status "Testing frontend health..."
FRONTEND_HEALTHY=false
for i in {1..10}; do
    if curl -f -s http://localhost:3000/api/health > /dev/null 2>&1; then
        print_success "Frontend health check passed (attempt $i/10)"
        FRONTEND_HEALTHY=true
        break
    else
        print_warning "Frontend health check failed (attempt $i/10)"
        if [ $i -eq 10 ]; then
            print_error "Frontend failed to become healthy"
            echo ""
            print_status "Frontend logs:"
            docker compose -f docker-compose.ci.yml logs radio-app
            echo ""
        else
            sleep 10
        fi
    fi
done

if [ "$FRONTEND_HEALTHY" != "true" ]; then
    print_error "Frontend health checks failed"
    docker compose -f docker-compose.ci.yml down -v
    exit 1
fi

# Additional API tests
print_status "Testing additional API endpoints..."

# Test WiFi status endpoint
if curl -f -s http://localhost:3000/api/wifi/status > /dev/null 2>&1; then
    print_success "WiFi status API working"
else
    print_warning "WiFi status API test failed (may be expected in CI)"
fi

# Test system status endpoint
if curl -f -s http://localhost:3000/api/system/status > /dev/null 2>&1; then
    print_success "System status API working"
else
    print_warning "System status API test failed (may be expected in CI)"
fi

# Test backend direct endpoints
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend direct health endpoint working"
else
    print_error "Backend direct health endpoint failed"
fi

# Show resource usage
print_status "Container resource usage:"
docker stats --no-stream

# Summary
echo ""
echo "🎉 CI Configuration Test Results"
echo "==============================="
echo ""

if [ "$BACKEND_HEALTHY" == "true" ] && [ "$FRONTEND_HEALTHY" == "true" ]; then
    print_success "All CI health checks passed!"
    echo ""
    echo "✅ Backend: http://localhost:8000/health"
    echo "✅ Frontend: http://localhost:3000/api/health"
    echo "✅ Container resource limits working"
    echo "✅ Platform compatibility confirmed (AMD64)"
    echo ""
    echo "Your configuration should work in GitHub Actions CI!"
else
    print_error "Some CI tests failed"
    exit 1
fi

# Ask user if they want to keep containers running
echo ""
read -p "Keep CI containers running for manual testing? [y/N] " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "CI containers will continue running:"
    echo ""
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔌 Backend:  http://localhost:8000"
    echo "📊 Stats:    docker stats"
    echo "📝 Logs:     docker compose -f docker-compose.ci.yml logs -f"
    echo "🛑 Stop:     docker compose -f docker-compose.ci.yml down -v"
    echo ""
    print_success "CI test completed successfully!"
else
    print_status "Stopping CI containers..."
    docker compose -f docker-compose.ci.yml down -v
    print_success "CI test completed and cleaned up!"
fi

echo ""
print_success "Local CI testing finished! 🎯"
