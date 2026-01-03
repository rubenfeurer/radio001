#!/bin/bash
# Test Status Summary Script
# Provides overview of testing infrastructure and current status

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Icons
CHECK="✅"
CROSS="❌"
WARNING="⚠️ "
INFO="ℹ️ "
ROCKET="🚀"
TEST="🧪"
COG="⚙️"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check file exists
file_exists() {
    [ -f "$1" ]
}

# Function to check directory exists
dir_exists() {
    [ -d "$1" ]
}

# Function to get test count from directory
count_test_files() {
    local dir="$1"
    if [ -d "$dir" ]; then
        find "$dir" -name "test_*.py" | wc -l
    else
        echo "0"
    fi
}

# Function to check pytest markers
check_pytest_markers() {
    if file_exists "backend/pytest.ini"; then
        echo -e "${GREEN}${INFO} Pytest markers configured:${NC}"
        grep -A 10 "markers =" backend/pytest.ini | grep -E "^\s*(unit|api|integration|websocket|slow):" | sed 's/^/    /'
    else
        echo -e "${RED}${CROSS} No pytest.ini found${NC}"
    fi
}

# Function to check coverage configuration
check_coverage_config() {
    if file_exists "backend/pytest.ini"; then
        local cov_modules=$(grep -E "^\s*--cov=" backend/pytest.ini | wc -l)
        if [ "$cov_modules" -gt 0 ]; then
            echo -e "${GREEN}${CHECK} Coverage configured for modules:${NC}"
            grep -E "^\s*--cov=" backend/pytest.ini | sed 's/.*--cov=/    /' | sed 's/^\s*/    /'
        else
            echo -e "${YELLOW}${WARNING} No coverage modules configured${NC}"
        fi
    fi
}

# Function to check GitHub workflows
check_github_workflows() {
    local workflow_count=0

    if file_exists ".github/workflows/ci-cd.yml"; then
        workflow_count=$((workflow_count + 1))
        echo -e "    ${GREEN}${CHECK} Main CI/CD Pipeline${NC} (.github/workflows/ci-cd.yml)"
    fi

    if file_exists ".github/workflows/develop-ci.yml"; then
        workflow_count=$((workflow_count + 1))
        echo -e "    ${GREEN}${CHECK} Development CI${NC} (.github/workflows/develop-ci.yml)"
    fi

    if file_exists ".github/workflows/test-backend.yml"; then
        workflow_count=$((workflow_count + 1))
        echo -e "    ${GREEN}${CHECK} Comprehensive Backend Tests${NC} (.github/workflows/test-backend.yml)"
    fi

    if [ "$workflow_count" -eq 0 ]; then
        echo -e "    ${RED}${CROSS} No GitHub workflows found${NC}"
    fi

    return $workflow_count
}

# Function to check docker configuration
check_docker_config() {
    if file_exists "compose/docker-compose.ci.yml"; then
        echo -e "    ${GREEN}${CHECK} CI Docker Compose${NC} (compose/docker-compose.ci.yml)"

        # Check if it has test dependencies arg
        if grep -q "INSTALL_TEST_DEPS" compose/docker-compose.ci.yml 2>/dev/null; then
            echo -e "    ${GREEN}${CHECK} Test dependencies configured in Docker${NC}"
        else
            echo -e "    ${YELLOW}${WARNING} Test dependencies not configured in Docker${NC}"
        fi
    else
        echo -e "    ${RED}${CROSS} No CI Docker configuration found${NC}"
    fi

    if file_exists "backend/Dockerfile"; then
        echo -e "    ${GREEN}${CHECK} Backend Dockerfile exists${NC}"

        # Check if it supports test dependencies
        if grep -q "requirements-test.txt" backend/Dockerfile; then
            echo -e "    ${GREEN}${CHECK} Test dependencies supported in Dockerfile${NC}"
        else
            echo -e "    ${YELLOW}${WARNING} Test dependencies not in Dockerfile${NC}"
        fi
    else
        echo -e "    ${RED}${CROSS} No backend Dockerfile found${NC}"
    fi
}

# Function to check test dependencies
check_test_dependencies() {
    if file_exists "backend/requirements-test.txt"; then
        echo -e "${GREEN}${CHECK} Test dependencies file exists${NC}"
        local dep_count=$(grep -c "^[^#]" backend/requirements-test.txt 2>/dev/null || echo "0")
        echo -e "    ${INFO} $dep_count test dependencies configured"

        # Show key dependencies
        echo -e "${CYAN}    Key test dependencies:${NC}"
        for dep in pytest pytest-asyncio httpx pytest-cov websockets; do
            if grep -q "^$dep" backend/requirements-test.txt; then
                echo -e "      ${GREEN}${CHECK} $dep${NC}"
            else
                echo -e "      ${RED}${CROSS} $dep${NC}"
            fi
        done
    else
        echo -e "${RED}${CROSS} No test dependencies file found${NC}"
    fi
}

# Function to analyze test structure
analyze_test_structure() {
    echo -e "${BLUE}${TEST} Test Structure Analysis:${NC}"

    if dir_exists "backend/tests"; then
        echo -e "${GREEN}${CHECK} Test directory exists${NC} (backend/tests/)"

        # Count tests by category
        local unit_tests=$(count_test_files "backend/tests/unit")
        local api_tests=$(count_test_files "backend/tests/api")
        local integration_tests=$(count_test_files "backend/tests/test_integration.py" && echo "1" || echo "0")

        echo -e "${CYAN}    Test Categories:${NC}"
        echo -e "      Unit Tests: $unit_tests files"
        echo -e "      API Tests: $api_tests files"
        echo -e "      Integration Tests: $integration_tests files"

        # Check for conftest.py
        if file_exists "backend/tests/conftest.py"; then
            echo -e "    ${GREEN}${CHECK} Test configuration file (conftest.py)${NC}"
        else
            echo -e "    ${YELLOW}${WARNING} No test configuration file (conftest.py)${NC}"
        fi

        # Total test files
        local total_tests=$(find backend/tests -name "test_*.py" | wc -l)
        echo -e "${PURPLE}    Total test files: $total_tests${NC}"

    else
        echo -e "${RED}${CROSS} No test directory found${NC}"
    fi
}

# Function to check local test runner
check_test_runner() {
    if file_exists "backend/run_tests.sh"; then
        echo -e "${GREEN}${CHECK} Local test runner script exists${NC}"

        if [ -x "backend/run_tests.sh" ]; then
            echo -e "    ${GREEN}${CHECK} Script is executable${NC}"
        else
            echo -e "    ${YELLOW}${WARNING} Script is not executable (run: chmod +x backend/run_tests.sh)${NC}"
        fi
    else
        echo -e "${RED}${CROSS} No local test runner script found${NC}"
    fi

    if file_exists "backend/TESTING.md"; then
        echo -e "${GREEN}${CHECK} Testing documentation exists${NC}"
    else
        echo -e "${YELLOW}${WARNING} No testing documentation found${NC}"
    fi
}

# Function to check system tools
check_system_tools() {
    echo -e "${BLUE}${COG} System Tools Check:${NC}"

    # Python
    if command_exists python3; then
        local python_version=$(python3 --version | cut -d' ' -f2)
        echo -e "${GREEN}${CHECK} Python 3 installed${NC} (version: $python_version)"
    else
        echo -e "${RED}${CROSS} Python 3 not found${NC}"
    fi

    # Pip
    if command_exists pip; then
        echo -e "${GREEN}${CHECK} pip installed${NC}"
    else
        echo -e "${RED}${CROSS} pip not found${NC}"
    fi

    # Docker
    if command_exists docker; then
        echo -e "${GREEN}${CHECK} Docker installed${NC}"
    else
        echo -e "${YELLOW}${WARNING} Docker not found (needed for CI simulation)${NC}"
    fi

    # Docker Compose
    if docker compose version >/dev/null 2>&1; then
        echo -e "${GREEN}${CHECK} Docker Compose installed${NC}"
    else
        echo -e "${YELLOW}${WARNING} Docker Compose not found (needed for integration tests)${NC}"
    fi

    # Git
    if command_exists git; then
        echo -e "${GREEN}${CHECK} Git installed${NC}"
    else
        echo -e "${RED}${CROSS} Git not found${NC}"
    fi
}

# Function to run quick test validation
run_quick_validation() {
    echo -e "${BLUE}${TEST} Quick Validation:${NC}"

    if dir_exists "backend" && file_exists "backend/requirements-test.txt"; then
        cd backend 2>/dev/null || return 1

        # Check if virtual environment is recommended
        if ! command_exists pytest; then
            echo -e "${YELLOW}${WARNING} pytest not installed globally${NC}"
            echo -e "    ${INFO} Consider creating virtual environment: python3 -m venv venv && source venv/bin/activate${NC}"
            cd ..
            return 0
        fi

        # Try to run pytest help
        if pytest --version >/dev/null 2>&1; then
            echo -e "${GREEN}${CHECK} pytest is working${NC}"

            # Quick syntax check
            if python3 -m py_compile tests/conftest.py 2>/dev/null; then
                echo -e "${GREEN}${CHECK} Test configuration syntax is valid${NC}"
            else
                echo -e "${YELLOW}${WARNING} Test configuration may have syntax issues${NC}"
            fi
        else
            echo -e "${RED}${CROSS} pytest is not working properly${NC}"
        fi

        cd ..
    else
        echo -e "${YELLOW}${WARNING} Cannot run validation - missing backend or test dependencies${NC}"
    fi
}

# Function to show recommendations
show_recommendations() {
    echo -e "${PURPLE}${ROCKET} Recommendations:${NC}"

    # Check for common improvements
    local recommendations=()

    if ! file_exists "backend/run_tests.sh" || [ ! -x "backend/run_tests.sh" ]; then
        recommendations+=("Set up local test runner: chmod +x backend/run_tests.sh")
    fi

    if ! file_exists "backend/TESTING.md"; then
        recommendations+=("Add comprehensive testing documentation")
    fi

    if ! grep -q "INSTALL_TEST_DEPS" compose/docker-compose.ci.yml 2>/dev/null; then
        recommendations+=("Configure test dependencies in Docker Compose")
    fi

    if ! command_exists docker; then
        recommendations+=("Install Docker for CI simulation and integration testing")
    fi

    if [ ${#recommendations[@]} -eq 0 ]; then
        echo -e "${GREEN}${CHECK} Testing infrastructure is well configured!${NC}"
        echo -e "${CYAN}    Next steps:${NC}"
        echo -e "      1. Run tests locally: cd backend && ./run_tests.sh"
        echo -e "      2. Run in Docker: ./run_tests.sh -d"
        echo -e "      3. Set up watch mode: ./run_tests.sh -w"
        echo -e "      4. Check CI integration on next commit"
    else
        for rec in "${recommendations[@]}"; do
            echo -e "    ${YELLOW}•${NC} $rec"
        done
    fi
}

# Function to show quick start
show_quick_start() {
    echo -e "${BLUE}${ROCKET} Quick Start Commands:${NC}"
    echo ""
    echo -e "${CYAN}Local Testing:${NC}"
    echo -e "  cd backend && ./run_tests.sh                 # Run all tests"
    echo -e "  ./run_tests.sh -t unit                       # Unit tests only"
    echo -e "  ./run_tests.sh -t api -v                     # API tests (verbose)"
    echo -e "  ./run_tests.sh --clean -c 80                 # Clean run, 80% coverage"
    echo ""
    echo -e "${CYAN}Docker Testing:${NC}"
    echo -e "  ./run_tests.sh -d                            # Run in Docker"
    echo -e "  ./run_tests.sh -d --clean                    # Clean Docker run"
    echo ""
    echo -e "${CYAN}Development:${NC}"
    echo -e "  ./run_tests.sh -w                            # Watch mode"
    echo -e "  ./run_tests.sh -t unit -w                    # Watch unit tests"
    echo ""
    echo -e "${CYAN}Manual Testing:${NC}"
    echo -e "  python -m pytest tests/                      # All tests"
    echo -e "  python -m pytest -m 'unit' --cov=core        # Unit tests with coverage"
    echo -e "  python -m pytest tests/api/ -v               # API tests verbose"
}

# Main function
main() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          ${YELLOW}Backend Test Status Summary${BLUE}          ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
    echo ""

    # Check if we're in the right directory
    if ! file_exists "backend/main.py"; then
        echo -e "${RED}${CROSS} Error: Please run this script from the project root directory${NC}"
        echo -e "${INFO} Expected: backend/main.py should exist${NC}"
        exit 1
    fi

    echo -e "${GREEN}${CHECK} Running from correct directory${NC}"
    echo ""

    # System tools check
    check_system_tools
    echo ""

    # Test structure analysis
    analyze_test_structure
    echo ""

    # Test dependencies check
    echo -e "${BLUE}${COG} Test Dependencies:${NC}"
    check_test_dependencies
    echo ""

    # Configuration checks
    echo -e "${BLUE}${COG} Test Configuration:${NC}"
    check_pytest_markers
    echo ""
    check_coverage_config
    echo ""

    # CI/CD integration
    echo -e "${BLUE}${COG} CI/CD Integration:${NC}"
    check_github_workflows
    echo ""
    check_docker_config
    echo ""

    # Local tools
    echo -e "${BLUE}${COG} Local Testing Tools:${NC}"
    check_test_runner
    echo ""

    # Quick validation
    run_quick_validation
    echo ""

    # Recommendations
    show_recommendations
    echo ""

    # Quick start guide
    show_quick_start
    echo ""

    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${CHECK} Test status summary complete!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
}

# Run main function
main "$@"
