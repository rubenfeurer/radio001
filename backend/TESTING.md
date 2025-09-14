# Backend Testing Guide

Comprehensive testing documentation for the Radio WiFi Backend system. This guide covers all testing approaches, from local development to CI/CD integration.

## 🎯 Testing Overview

The backend test suite includes **142+ comprehensive tests** covering:

- ✅ **Unit Tests** - Core functionality (RadioManager, StationManager, etc.)
- ✅ **API Tests** - All REST endpoints (stations, radio control, WebSocket)
- ✅ **Integration Tests** - Complete system workflows
- ✅ **WebSocket Tests** - Real-time communication
- ✅ **Mock Hardware** - GPIO and audio simulation for development

## 📊 Test Categories & Coverage

### Unit Tests (`tests/unit/`)
- **RadioManager** - Volume control, station playback, hardware integration
- **StationManager** - 3-slot management, CRUD operations, persistence
- **Core Models** - Data validation, WebSocket messages

### API Tests (`tests/api/`)
- **Station Routes** - GET/POST/DELETE for 3 station slots
- **Radio Routes** - Volume, playback, system control
- **WebSocket Routes** - Connection management, real-time updates

### Integration Tests (`tests/test_integration.py`)
- **System Workflows** - End-to-end station management
- **Volume Control** - Hardware limits and validation
- **Hardware Simulation** - Development mode button/volume simulation
- **Error Handling** - Edge cases and error recovery

### Test Configuration
```ini
[tool:pytest]
minversion = 6.0
testpaths = tests
asyncio_mode = auto
markers =
    unit: Unit tests for individual components
    api: API endpoint tests
    integration: End-to-end workflow tests
    websocket: WebSocket communication tests
    slow: Performance/long-running tests
```

## 🚀 Quick Start

### Local Testing

```bash
# Basic test run
cd backend
./run_tests.sh

# Run specific test types
./run_tests.sh -t unit          # Unit tests only
./run_tests.sh -t api           # API tests only
./run_tests.sh -t integration   # Integration tests
./run_tests.sh -t websocket     # WebSocket tests

# With coverage threshold
./run_tests.sh -c 80            # Require 80% coverage

# Verbose output
./run_tests.sh -v               # Detailed test output

# Clean run
./run_tests.sh --clean          # Remove previous artifacts
```

### Docker Testing

```bash
# Run in Docker (CI environment simulation)
./run_tests.sh -d

# Clean Docker run
./run_tests.sh -d --clean
```

### Watch Mode (Development)

```bash
# Auto-run tests on file changes
./run_tests.sh -w

# Watch specific test type
./run_tests.sh -t unit -w
```

## 🛠️ Manual Testing

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Set environment variables
export NODE_ENV=development
export MOCK_HARDWARE=true
export PYTHONPATH=$PWD:$PYTHONPATH
```

### Run Tests Manually

```bash
# All tests
python -m pytest tests/

# Unit tests with coverage
python -m pytest -m "unit" --cov=core --cov=hardware --cov-report=html

# API tests
python -m pytest -m "api" --verbose

# Integration tests
python -m pytest -m "integration" --tb=short

# WebSocket tests
python -m pytest -m "websocket"

# Specific test file
python -m pytest tests/unit/test_radio_manager.py -v

# Specific test method
python -m pytest tests/api/test_station_routes.py::TestStationRoutes::test_save_station_success -v
```

## 🔧 Test Configuration

### Environment Variables

```bash
# Required for testing
NODE_ENV=development          # Enable development features
MOCK_HARDWARE=true           # Use mock hardware (no Pi required)
PYTHONPATH=/app             # Python module path

# Optional
DEBUG=true                  # Enable debug logging
COVERAGE_THRESHOLD=23       # Minimum coverage percentage (pragmatic threshold)
```

### Mock Configuration

The test suite uses comprehensive mocking:

```python
# Hardware mocking (automatic)
- GPIO buttons and rotary encoder
- Audio playback (MPV player)
- System volume controls
- Hardware status indicators

# API mocking
- HTTP requests to external services
- WebSocket connections
- File system operations
- Network interfaces
```

## 📈 Coverage Reports

### Viewing Coverage

```bash
# Generate HTML report
python -m pytest --cov=core --cov=hardware --cov=api --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Targets

```
Current Coverage Targets:
- Core modules: >80%
- Hardware modules: >70%  
- API routes: >90%
- Overall: >75%
```

### Coverage Analysis

```bash
# Terminal coverage report
coverage report --show-missing

# XML report for CI/CD
coverage xml

# JSON report for analysis
coverage json
```

## 🧪 Writing New Tests

### Unit Test Template

```python
"""
Unit tests for NewComponent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.new_component import NewComponent

@pytest.mark.unit
class TestNewComponent:
    """Test NewComponent functionality."""

    @pytest.fixture
    async def component(self):
        """Create component instance for testing."""
        return NewComponent()

    async def test_basic_functionality(self, component):
        """Test basic component functionality."""
        result = await component.do_something()
        assert result is not None

    async def test_error_handling(self, component):
        """Test error handling."""
        with pytest.raises(ValueError):
            await component.invalid_operation()
```

### API Test Template

```python
"""
API endpoint tests for new routes.
"""

import pytest
from httpx import AsyncClient

@pytest.mark.api
class TestNewRoutes:
    """Test new API endpoints."""

    async def test_get_endpoint(self, client: AsyncClient):
        """Test GET endpoint."""
        response = await client.get("/new/endpoint")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data

    async def test_post_endpoint(self, client: AsyncClient):
        """Test POST endpoint with validation."""
        payload = {"key": "value"}
        response = await client.post("/new/endpoint", json=payload)
        assert response.status_code == 200

    async def test_validation_error(self, client: AsyncClient):
        """Test validation error handling."""
        response = await client.post("/new/endpoint", json={})
        assert response.status_code == 422
```

### Integration Test Template

```python
"""
Integration tests for complete workflows.
"""

import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestNewWorkflow:
    """Test complete workflow integration."""

    async def test_complete_workflow(self, client: AsyncClient):
        """Test end-to-end workflow."""
        # Step 1: Setup
        response = await client.post("/setup", json={"config": "test"})
        assert response.status_code == 200

        # Step 2: Operation
        response = await client.get("/status")
        assert response.status_code == 200

        # Step 3: Cleanup
        response = await client.post("/cleanup")
        assert response.status_code == 200
```

## 🔄 CI/CD Integration

### GitHub Actions Workflows

The backend tests are integrated into multiple workflows:

#### 1. Main CI/CD (`ci-cd.yml`)
- **Triggers**: Push to main, PRs to main
- **Tests**: Full test suite with coverage
- **Coverage**: Upload to Codecov
- **Artifacts**: Test results, coverage reports

#### 2. Develop CI (`develop-ci.yml`)
- **Triggers**: Push/PR to develop
- **Tests**: Quick validation (unit + API)
- **Focus**: Fast feedback for development

#### 3. Backend Test Suite (`test-backend.yml`)
- **Triggers**: Backend changes, manual dispatch
- **Tests**: Comprehensive testing by category
- **Reports**: Detailed analysis and PR comments

### Workflow Status

```yaml
# Example workflow integration
- name: Run backend tests
  run: |
    cd backend
    python -m pytest \
      --verbose \
      --cov=core \
      --cov=hardware \
      --cov=api \
      --cov-report=xml:coverage.xml \
      --junitxml=test-results.xml \
      tests/

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: backend/coverage.xml
```

## 🚨 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Fix: Set Python path
export PYTHONPATH=$PWD:$PYTHONPATH

# Or run from backend directory
cd backend && python -m pytest tests/
```

#### Mock Hardware Issues
```bash
# Ensure mock mode is enabled
export MOCK_HARDWARE=true
export NODE_ENV=development

# Check mock dependencies
pip install -r requirements-test.txt
```

#### Coverage Issues
```bash
# Install coverage tools
pip install coverage[toml]

# Clear previous coverage data
coverage erase

# Regenerate coverage
python -m pytest --cov=core tests/
```

#### Docker Test Issues
```bash
# Rebuild with test dependencies
docker-compose -f ../compose/docker-compose.ci.yml build radio-backend \
  --build-arg INSTALL_TEST_DEPS=true

# Check container health
docker-compose -f ../compose/docker-compose.ci.yml exec radio-backend curl -f http://localhost:8000/health
```

### Debug Mode

```bash
# Run tests with debug output
python -m pytest -v -s --tb=long tests/

# Run specific failing test
python -m pytest tests/unit/test_radio_manager.py::TestRadioManager::test_volume_control -v -s

# Use pdb debugger
python -m pytest --pdb tests/
```

### Log Analysis

```bash
# Enable debug logging
export DEBUG=true

# View test logs
python -m pytest -s --capture=no tests/

# Check application logs
tail -f logs/radio.log  # If logging to file
```

## 📋 Test Checklists

### Pre-commit Checklist
- [ ] All tests pass locally
- [ ] Coverage meets threshold (>23%)
- [ ] No linting errors
- [ ] New tests for new functionality
- [ ] Mock hardware enabled

### Release Checklist
- [ ] Full test suite passes in CI
- [ ] Integration tests validate workflows  
- [ ] Performance tests complete (if applicable)
- [ ] Coverage reports generated
- [ ] Test artifacts archived

### New Feature Checklist
- [ ] Unit tests for core logic
- [ ] API tests for endpoints
- [ ] Integration tests for workflows
- [ ] WebSocket tests for real-time features
- [ ] Error handling tests
- [ ] Documentation updated

## 🔗 References

### Dependencies
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **httpx** - HTTP client for API testing
- **pytest-cov** - Coverage reporting
- **websockets** - WebSocket testing

### Configuration Files
- `pytest.ini` - Test configuration
- `requirements-test.txt` - Test dependencies
- `conftest.py` - Shared fixtures and utilities
- `run_tests.sh` - Local test runner script

### CI/CD Files
- `.github/workflows/ci-cd.yml` - Main CI/CD pipeline
- `.github/workflows/develop-ci.yml` - Development validation
- `.github/workflows/test-backend.yml` - Comprehensive testing
- `compose/docker-compose.ci.yml` - CI Docker configuration

## 🎯 Best Practices

1. **Test Structure**: Follow AAA pattern (Arrange, Act, Assert)
2. **Mock Usage**: Mock external dependencies, test business logic
3. **Coverage**: Aim for >23% overall (pragmatic threshold), >50% for critical paths
4. **Speed**: Keep unit tests fast (<1s), mark slow tests
5. **Isolation**: Each test should be independent
6. **Documentation**: Include docstrings for complex tests
7. **Error Cases**: Test both success and failure scenarios
8. **Real Scenarios**: Integration tests should mirror actual usage

---

**Happy Testing! 🧪✨**

*For questions or issues, check the main project documentation or open an issue.*