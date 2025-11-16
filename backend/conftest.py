"""
Global pytest configuration for Radio Backend tests.

This module provides comprehensive async test support, shared fixtures,
and proper pytest-asyncio configuration to ensure all async tests run correctly.
"""

import os
import sys
import pytest
import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure the backend modules can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import test dependencies
from core.models import RadioStation, StationRequest
from core.radio_manager import RadioManager
from main import Config

# Configure pytest-asyncio
pytest_plugins = ['pytest_asyncio']


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of the default event loop for the test session.

    This fixture ensures all async tests run in the same event loop,
    preventing asyncio warnings and test failures.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    yield loop

    # Clean up
    try:
        # Cancel any pending tasks
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()

        # Wait for tasks to complete cancellation
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

        loop.close()
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configure test environment settings."""
    os.environ['NODE_ENV'] = 'test'
    os.environ['MOCK_HARDWARE'] = 'true'
    os.environ['DEBUG'] = 'false'

    yield

    # Cleanup
    for key in ['NODE_ENV', 'MOCK_HARDWARE', 'DEBUG']:
        os.environ.pop(key, None)


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create required subdirectories
        (temp_path / "data").mkdir(exist_ok=True)
        (temp_path / "logs").mkdir(exist_ok=True)
        (temp_path / "sounds").mkdir(exist_ok=True)

        yield temp_path


@pytest.fixture
def test_config(temp_data_dir):
    """Test configuration with temporary paths."""
    class TestConfig:
        DATA_DIR = temp_data_dir / "data"
        LOGS_DIR = temp_data_dir / "logs"
        SOUNDS_DIR = temp_data_dir / "sounds"
        STATIONS_FILE = DATA_DIR / "stations.json"
        IS_DEVELOPMENT = True
        MOCK_HARDWARE = True
        DEBUG = False

        # Radio Settings - match real Config
        DEFAULT_VOLUME: int = 50
        MIN_VOLUME: int = 30
        MAX_VOLUME: int = 100

        @classmethod
        def ensure_paths(cls):
            cls.DATA_DIR.mkdir(exist_ok=True, parents=True)
            cls.LOGS_DIR.mkdir(exist_ok=True, parents=True)
            cls.SOUNDS_DIR.mkdir(exist_ok=True, parents=True)

    TestConfig.ensure_paths()
    return TestConfig


@pytest.fixture
def test_station():
    """Test radio station data."""
    return RadioStation(
        name="Test Radio Station",
        url="https://test-stream.example.com/radio.mp3",
        slot=1,
        country="Test Country",
        location="Test City",
        genre="Test Genre",
        bitrate="128k",
        language="English"
    )


@pytest.fixture
def test_station_2():
    """Second test radio station data."""
    return RadioStation(
        name="Alternative Test Station",
        url="https://alt-stream.example.com/radio.mp3",
        slot=2,
        country="Alt Country",
        location="Alt City",
        genre="Alternative",
        bitrate="256k",
        language="English"
    )


@pytest.fixture
def test_station_request():
    """Test station request data."""
    return StationRequest(
        name="New Test Station",
        url="https://new-stream.example.com/stream",
        country="New Country",
        location="New City",
        genre="Pop",
        bitrate="192k",
        language="English"
    )


@pytest.fixture
def mock_station_manager():
    """Mock station manager for testing."""
    mock = AsyncMock()

    # Mock default behavior
    mock.get_station.return_value = RadioStation(
        name="Test Station",
        url="https://test.example.com/stream",
        slot=1
    )

    mock.get_all_stations.return_value = {
        1: RadioStation(name="Station 1", url="https://test1.example.com", slot=1),
        2: None,
        3: RadioStation(name="Station 3", url="https://test3.example.com", slot=3)
    }

    mock.initialize.return_value = None
    mock.save_station.return_value = None
    mock.delete_station.return_value = None

    return mock


@pytest.fixture
def mock_audio_player():
    """Mock audio player for testing."""
    mock = AsyncMock()
    mock.initialize.return_value = None
    mock.play.return_value = True
    mock.stop.return_value = True
    mock.set_volume.return_value = True
    mock.get_volume.return_value = 50
    mock.is_playing = False
    mock.current_url = None
    return mock


@pytest.fixture
def mock_gpio_controller():
    """Mock GPIO controller for testing."""
    mock = MagicMock()
    mock.initialize.return_value = None
    mock.cleanup.return_value = None
    mock.get_button_states.return_value = [False, False, False]
    mock.get_volume_position.return_value = 50
    return mock


@pytest.fixture
def mock_sound_manager():
    """Mock sound manager for testing."""
    mock = AsyncMock()
    mock.initialize.return_value = None
    mock.play.return_value = True
    mock.stop.return_value = True
    mock.set_volume.return_value = 50
    mock.get_volume.return_value = 50
    mock.is_playing.return_value = False
    mock.current_station = None
    return mock


@pytest.fixture
def status_callback():
    """Mock status callback for testing."""
    return AsyncMock()


# Removed unused helper function - using direct singleton pattern in tests


@pytest.fixture
def sample_station_request():
    """Sample station request for API testing."""
    return {
        "name": "Test FM Radio",
        "url": "https://stream.example.com/test",
        "country": "United Kingdom",
        "location": "London",
        "genre": "Pop",
        "bitrate": "128k",
        "language": "English"
    }


@pytest.fixture
def websocket_messages():
    """Sample WebSocket messages for testing."""
    return {
        "volume_update": {
            "type": "volume_update",
            "data": {"volume": 75, "change": 5},
            "timestamp": 1703123456.789
        },
        "station_change": {
            "type": "station_change",
            "data": {"slot": 2, "station": "Jazz FM"},
            "timestamp": 1703123456.789
        },
        "playback_status": {
            "type": "playback_status",
            "data": {"is_playing": True, "station": "Rock FM"},
            "timestamp": 1703123456.789
        }
    }


@pytest.fixture
def test_preferences():
    """Test preferences data."""
    return {
        "volume": {
            "last_level": 65,
            "default_level": 50,
            "mute_level": 0,
            "startup_volume": 40
        },
        "playback": {
            "last_station": 2,
            "auto_start": False,
            "fade_in": True,
            "fade_out": True
        },
        "ui": {
            "theme": "dark",
            "show_metadata": True,
            "compact_mode": False
        }
    }


# Async test client fixtures for API testing
@pytest.fixture
async def client():
    """Create async test client for FastAPI."""
    from httpx import AsyncClient
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_hardware():
    """Ensure hardware mocking is enabled for all tests."""
    os.environ['MOCK_HARDWARE'] = 'true'
    return True


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "integration: End-to-end workflow tests")
    config.addinivalue_line("markers", "websocket: WebSocket communication tests")
    config.addinivalue_line("markers", "slow: Performance/long-running tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle async tests properly."""
    for item in items:
        # Mark all async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)

        # Add default markers based on file path
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        elif "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "websocket" in item.nodeid:
            item.add_marker(pytest.mark.websocket)


@pytest.fixture(autouse=True)
async def cleanup_tasks():
    """Clean up any running asyncio tasks after each test."""
    yield

    # Cancel any tasks that might be hanging around
    tasks = [task for task in asyncio.all_tasks() if not task.done()]
    for task in tasks:
        if not task.cancelled():
            task.cancel()

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
