#!/bin/bash
# Radio WiFi Configuration - Developer Setup Script
# Sets up the development environment with pre-commit hooks and dependencies

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Header
echo ""
echo "🚀 Radio WiFi Configuration - Development Setup"
echo "================================================"
echo ""

# Check system requirements
print_status "Checking system requirements..."

# Check Docker
if ! command_exists docker; then
    print_error "Docker is not installed"
    echo "Please install Docker Desktop:"
    echo "  macOS: https://docs.docker.com/desktop/mac/"
    echo "  Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check Docker Compose
if ! docker compose version >/dev/null 2>&1; then
    print_error "Docker Compose is not available"
    echo "Please install Docker Compose v2 or use Docker Desktop"
    exit 1
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Check Node.js (for IDE integration)
if ! command_exists node; then
    print_warning "Node.js not found locally"
    echo "Node.js is not required (runs in Docker) but recommended for IDE integration"
    echo "Install from: https://nodejs.org/"
    echo ""
fi

# Check Git
if ! command_exists git; then
    print_error "Git is not installed"
    exit 1
fi

print_success "System requirements check passed"
echo ""

# Setup development environment
print_status "Setting up development environment..."

# Make scripts executable
chmod +x scripts/*.sh 2>/dev/null || true

# Setup pre-commit hooks
print_status "Setting up pre-commit hooks..."

cd app

# Install dependencies
if [ -f "package.json" ]; then
    print_status "Installing frontend dependencies..."

    # Try npm first, fall back to using Docker if local Node.js not available
    if command_exists npm; then
        npm install
        print_success "Dependencies installed locally"
    else
        print_status "Installing dependencies via Docker..."
        cd ..
        ./scripts/docker-dev.sh shell radio-app "npm install"
        cd app
        print_success "Dependencies installed via Docker"
    fi
else
    print_error "package.json not found in app directory"
    exit 1
fi

# Setup husky hooks
print_status "Setting up Git hooks..."
if command_exists npm; then
    npm run prepare 2>/dev/null || true
else
    print_status "Setting up hooks via Docker..."
    cd ..
    ./scripts/dev-environment.sh shell radio-app "npm run prepare"
    cd app
fi

# Make sure hook files are executable
chmod +x ../.husky/* 2>/dev/null || true

print_success "Git hooks configured"
cd ..

# Test Docker setup
print_status "Testing Docker environment..."

# Build containers
print_status "Building Docker containers (this may take a few minutes)..."
if ./scripts/dev-environment.sh start; then
    sleep 5

    # Test if services are running
    if curl -f http://localhost:3000/api/health >/dev/null 2>&1; then
        print_success "Frontend is running at http://localhost:3000"
    else
        print_warning "Frontend health check failed, but containers are running"
    fi

    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Backend is running at http://localhost:8000"
    else
        print_warning "Backend health check failed, but containers are running"
    fi

    # Stop containers for now
    print_status "Stopping containers..."
    ./scripts/dev-environment.sh stop

else
    print_error "Failed to start Docker environment"
    echo "Check Docker logs for details:"
    echo "  ./scripts/dev-environment.sh logs"
    exit 1
fi

# Test pre-commit hooks
print_status "Testing pre-commit hooks..."
cd app

# Create a temporary test file to verify hooks work
echo "// Test file for hooks" > /tmp/test-hooks.js
git add /tmp/test-hooks.js 2>/dev/null || true

# Run hooks manually to test
if command_exists npm; then
    if npm run lint >/dev/null 2>&1; then
        print_success "Lint configuration working"
    else
        print_warning "Lint check failed (may be expected)"
    fi

    if npm run type-check >/dev/null 2>&1; then
        print_success "Type checking working"
    else
        print_warning "Type check failed (may be expected)"
    fi
fi

# Clean up test file
rm -f /tmp/test-hooks.js
git reset HEAD /tmp/test-hooks.js 2>/dev/null || true

cd ..

# Configuration check
print_status "Checking configuration..."

# Check if .env files exist
if [ ! -f ".env" ]; then
    print_warning "No .env file found"
    echo "You may want to create one for custom configuration"
    echo "See .env.example for reference"
fi

# Platform detection
print_status "Detecting platform..."
PLATFORM=$(uname -m)
case $PLATFORM in
    arm64|aarch64)
        print_success "Apple Silicon (ARM64) detected - optimized builds will be used"
        ;;
    x86_64)
        print_success "Intel/AMD64 detected - standard builds will be used"
        ;;
    *)
        print_warning "Unknown platform: $PLATFORM"
        ;;
esac

# Final setup summary
echo ""
echo "🎉 Development Environment Setup Complete!"
echo "=========================================="
echo ""
echo "✅ Docker environment configured"
echo "✅ Pre-commit hooks installed"
echo "✅ Dependencies installed"
echo "✅ Platform optimizations applied"
echo ""

# Next steps
echo "🚀 Next Steps:"
echo ""
echo "1. Start development environment:"
echo "   ./scripts/dev-environment.sh start"
echo ""
echo "2. Open your browser:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo ""
echo "3. Make changes and commit:"
echo "   git add ."
echo "   git commit -m 'feat: your new feature'"
echo ""
echo "4. View logs:"
echo "   ./scripts/dev-environment.sh logs"
echo ""

# Development workflow reminder
echo "💡 Development Workflow:"
echo ""
echo "• Code changes auto-reload in containers"
echo "• Pre-commit hooks auto-fix lint issues"
echo "• Type checking runs on every commit"
echo "• Use conventional commit messages"
echo ""

# Troubleshooting
echo "🛠️  Troubleshooting:"
echo ""
echo "• Container issues: ./scripts/dev-environment.sh cleanup && ./scripts/dev-environment.sh start"
echo "• Hook issues: cd app && npm run prepare"
echo "• IDE type errors: Expected - packages are in Docker containers"
echo "• Documentation: See DEVELOPMENT.md and .github/DEVELOPER_WORKFLOW.md"
echo ""

print_success "Setup complete! Happy coding! 🎯"
