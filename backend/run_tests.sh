#!/bin/bash
# Backend Test Runner Script
# Provides easy local testing with various options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
COVERAGE_THRESHOLD=70
VERBOSE=false
WATCH=false
CLEAN=false
DOCKER=false

# Function to display usage
usage() {
    echo -e "${BLUE}Backend Test Runner${NC}"
    echo "===================="
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE        Test type (all, unit, api, websocket, integration)"
    echo "  -c, --coverage NUM     Coverage threshold (default: 70)"
    echo "  -v, --verbose          Verbose output"
    echo "  -w, --watch            Watch for changes and re-run tests"
    echo "  -d, --docker           Run tests in Docker container"
    echo "  --clean               Clean previous test artifacts"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                     # Run all tests"
    echo "  $0 -t unit             # Run only unit tests"
    echo "  $0 -t api -v           # Run API tests with verbose output"
    echo "  $0 --clean --coverage 80  # Clean and run with 80% coverage"
    echo "  $0 -d                  # Run in Docker"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -c|--coverage)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -w|--watch)
            WATCH=true
            shift
            ;;
        -d|--docker)
            DOCKER=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Validate test type
case $TEST_TYPE in
    all|unit|api|websocket|integration)
        ;;
    *)
        echo -e "${RED}Error: Invalid test type '$TEST_TYPE'${NC}"
        echo "Valid types: all, unit, api, websocket, integration"
        exit 1
        ;;
esac

# Check if we're in the backend directory
if [[ ! -f "requirements.txt" || ! -f "main.py" ]]; then
    echo -e "${RED}Error: Please run this script from the backend directory${NC}"
    exit 1
fi

# Function to clean previous artifacts
clean_artifacts() {
    echo -e "${YELLOW}🧹 Cleaning test artifacts...${NC}"
    rm -rf htmlcov/
    rm -rf .coverage
    rm -rf coverage.xml
    rm -rf test-results.xml
    rm -rf .pytest_cache/
    rm -rf __pycache__/
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Function to setup test environment
setup_environment() {
    echo -e "${BLUE}🔧 Setting up test environment...${NC}"

    export NODE_ENV=development
    export MOCK_HARDWARE=true
    export PYTHONPATH=${PWD}:${PYTHONPATH}

    # Check if virtual environment exists
    if [[ ! -d "venv" ]]; then
        echo -e "${YELLOW}⚠️  No virtual environment found. Creating one...${NC}"
        python3 -m venv venv
    fi

    # Activate virtual environment
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    fi

    # Install dependencies
    echo -e "${BLUE}📦 Installing dependencies...${NC}"
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    pip install -r requirements-test.txt --quiet

    echo -e "${GREEN}✅ Dependencies installed${NC}"
}

# Function to build pytest command
build_pytest_command() {
    local cmd="python -m pytest"

    # Add verbosity
    if [[ "$VERBOSE" == "true" ]]; then
        cmd="$cmd --verbose"
    else
        cmd="$cmd -q"
    fi

    # Add coverage
    cmd="$cmd --cov=core --cov=hardware --cov=api"
    cmd="$cmd --cov-report=term-missing"
    cmd="$cmd --cov-report=html:htmlcov"
    cmd="$cmd --cov-report=xml:coverage.xml"
    cmd="$cmd --cov-fail-under=$COVERAGE_THRESHOLD"

    # Add test markers based on type
    case $TEST_TYPE in
        unit)
            cmd="$cmd -m 'unit'"
            ;;
        api)
            cmd="$cmd -m 'api'"
            ;;
        websocket)
            cmd="$cmd -m 'websocket'"
            ;;
        integration)
            cmd="$cmd -m 'integration'"
            ;;
        all)
            # Run all tests
            ;;
    esac

    # Add other options
    cmd="$cmd --junitxml=test-results.xml"
    cmd="$cmd --tb=short"
    cmd="$cmd --maxfail=10"
    cmd="$cmd --durations=20"
    cmd="$cmd tests/"

    echo "$cmd"
}

# Function to run tests locally
run_local_tests() {
    echo -e "${BLUE}🧪 Running ${TEST_TYPE} tests locally...${NC}"

    local cmd=$(build_pytest_command)
    echo -e "${YELLOW}Command: $cmd${NC}"
    echo ""

    if eval "$cmd"; then
        echo ""
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        return 0
    else
        echo ""
        echo -e "${RED}❌ Some tests failed${NC}"
        return 1
    fi
}

# Function to run tests in Docker
run_docker_tests() {
    echo -e "${BLUE}🐳 Running ${TEST_TYPE} tests in Docker...${NC}"

    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Error: docker-compose not found${NC}"
        exit 1
    fi

    # Build and start container
    echo -e "${YELLOW}Building Docker container with test dependencies...${NC}"
    docker-compose -f ../compose/docker-compose.ci.yml build radio-backend --build-arg INSTALL_TEST_DEPS=true

    echo -e "${YELLOW}Starting container...${NC}"
    docker-compose -f ../compose/docker-compose.ci.yml up -d radio-backend

    # Wait for container to be ready
    echo -e "${YELLOW}Waiting for container to be ready...${NC}"
    for i in {1..30}; do
        if docker-compose -f ../compose/docker-compose.ci.yml exec -T radio-backend curl -f http://localhost:8000/health &>/dev/null; then
            echo -e "${GREEN}✅ Container is ready${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""

    # Build Docker pytest command
    local docker_cmd=$(build_pytest_command)

    # Run tests in container
    echo -e "${BLUE}🧪 Executing tests in container...${NC}"
    if docker-compose -f ../compose/docker-compose.ci.yml exec -T radio-backend bash -c "
        export NODE_ENV=development
        export MOCK_HARDWARE=true
        export PYTHONPATH=/app:\$PYTHONPATH
        cd /app
        $docker_cmd
    "; then
        echo ""
        echo -e "${GREEN}🎉 All Docker tests passed!${NC}"

        # Copy results back
        echo -e "${YELLOW}📋 Copying test results...${NC}"
        docker-compose -f ../compose/docker-compose.ci.yml cp radio-backend:/app/coverage.xml ./
        docker-compose -f ../compose/docker-compose.ci.yml cp radio-backend:/app/htmlcov ./
        docker-compose -f ../compose/docker-compose.ci.yml cp radio-backend:/app/test-results.xml ./

        docker_success=true
    else
        echo ""
        echo -e "${RED}❌ Some Docker tests failed${NC}"
        docker_success=false
    fi

    # Cleanup
    echo -e "${YELLOW}🧹 Cleaning up Docker resources...${NC}"
    docker-compose -f ../compose/docker-compose.ci.yml down -v

    return $([[ "$docker_success" == "true" ]] && echo 0 || echo 1)
}

# Function to watch for changes
run_watch_mode() {
    echo -e "${BLUE}👀 Starting watch mode for ${TEST_TYPE} tests...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop watching${NC}"
    echo ""

    # Check if fswatch is available
    if command -v fswatch &> /dev/null; then
        fswatch -o . --exclude="htmlcov|\.coverage|test-results\.xml|__pycache__|\.pytest_cache" | while read num; do
            echo -e "${YELLOW}📁 Changes detected, running tests...${NC}"
            run_local_tests || true
            echo ""
            echo -e "${BLUE}👀 Watching for changes...${NC}"
        done
    else
        echo -e "${YELLOW}⚠️  fswatch not found, using basic polling...${NC}"
        while true; do
            run_local_tests || true
            echo ""
            echo -e "${BLUE}⏱️  Waiting 5 seconds before next run...${NC}"
            sleep 5
        done
    fi
}

# Function to display results summary
display_summary() {
    echo ""
    echo -e "${BLUE}📊 Test Results Summary${NC}"
    echo "======================="

    if [[ -f "test-results.xml" ]]; then
        echo -e "${GREEN}📋 Test Results:${NC}"
        python3 -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('test-results.xml')
    root = tree.getroot()
    tests = root.attrib.get('tests', '0')
    failures = root.attrib.get('failures', '0')
    errors = root.attrib.get('errors', '0')
    time = root.attrib.get('time', '0')
    passed = int(tests) - int(failures) - int(errors)

    print(f'  Total: {tests}')
    print(f'  Passed: {passed} ✅')
    print(f'  Failed: {failures}')
    print(f'  Errors: {errors}')
    print(f'  Duration: {float(time):.2f}s')
except Exception as e:
    print(f'  Could not parse results: {e}')
"
    fi

    if [[ -f "coverage.xml" ]]; then
        echo -e "${GREEN}📈 Coverage:${NC}"
        python3 -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('coverage.xml')
    root = tree.getroot()
    coverage = float(root.attrib.get('line-rate', '0')) * 100
    print(f'  Line Coverage: {coverage:.1f}%')
    if coverage >= $COVERAGE_THRESHOLD:
        print('  ✅ Meets threshold')
    else:
        print(f'  ❌ Below threshold ({$COVERAGE_THRESHOLD}%)')
except Exception as e:
    print(f'  Could not parse coverage: {e}')
"
    fi

    if [[ -d "htmlcov" ]]; then
        echo -e "${GREEN}📄 Coverage Report:${NC} htmlcov/index.html"
    fi

    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}🧪 Backend Test Runner${NC}"
    echo -e "${BLUE}=====================${NC}"
    echo ""
    echo -e "${YELLOW}Configuration:${NC}"
    echo "  Test Type: $TEST_TYPE"
    echo "  Coverage Threshold: $COVERAGE_THRESHOLD%"
    echo "  Verbose: $VERBOSE"
    echo "  Watch Mode: $WATCH"
    echo "  Docker: $DOCKER"
    echo "  Clean: $CLEAN"
    echo ""

    # Clean if requested
    if [[ "$CLEAN" == "true" ]]; then
        clean_artifacts
        echo ""
    fi

    # Run tests based on mode
    if [[ "$DOCKER" == "true" ]]; then
        if run_docker_tests; then
            test_success=true
        else
            test_success=false
        fi
    else
        setup_environment
        echo ""

        if [[ "$WATCH" == "true" ]]; then
            run_watch_mode
        else
            if run_local_tests; then
                test_success=true
            else
                test_success=false
            fi
        fi
    fi

    # Display summary if not in watch mode
    if [[ "$WATCH" != "true" ]]; then
        display_summary

        if [[ "$test_success" == "true" ]]; then
            echo -e "${GREEN}🎉 SUCCESS: All tests completed successfully!${NC}"
            exit 0
        else
            echo -e "${RED}❌ FAILURE: Some tests failed${NC}"
            exit 1
        fi
    fi
}

# Run main function
main "$@"
