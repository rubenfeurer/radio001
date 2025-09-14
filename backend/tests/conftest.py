"""
Shared test fixtures and configuration for radio backend tests.

This module provides common fixtures, mock objects, and test utilities
used across all test modules in the radio backend test suite.
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from typing import Dict, Any, Optional

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app, Config
from api.routes.websocket import setup_radio_manager_with_websocket
from core.models import RadioStation, StationRequest


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data and configure paths."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Override config paths for testing
        original_data_dir = Config.DATA_DIR
        original_sounds_dir = Config.SOUNDS_DIR
        original_stations_file = Config.STATIONS_FILE
        original_preferences_file = Config.PREFERENCES_FILE

        Config.DATA_DIR = temp_path / "data"
        Config.SOUNDS_DIR = temp_path / "sounds"
        Config.STATIONS_FILE = Config.DATA_DIR / "stations.json"
        Config.PREFERENCES_FILE = Config.DATA_DIR / "preferences.json"

        # Create directories
        Config.DATA_DIR.mkdir(exist_ok=True)
        Config.SOUNDS_DIR.mkdir(exist_ok=True)

        # Create default stations file
        default_stations = {
            "1": {
                "name": "Test Station 1",
                "url": "https://test1.example.com/stream",
                "slot": 1,
                "country": "Test Country",
                "genre": "Test Genre"
            },
            "2": None,
            "3": {
                "name": "Test Station 3",
                "url": "https://test3.example.com/stream",
                "slot": 3,
                "country": "Test Country",
                "genre": "Classical"
            }
        }

        Config.STATIONS_FILE.write_text(json.dumps(default_stations, indent=2))

        yield temp_path

        # Restore original paths
        Config.DATA_DIR = original_data_dir
        Config.SOUNDS_DIR = original_sounds_dir
        Config.STATIONS_FILE = original_stations_file
        Config.PREFERENCES_FILE = original_preferences_file


@pytest.fixture
async def radio_manager(temp_data_dir):
    """Create a radio manager instance for testing."""
    # Ensure we're in development mode for testing
    original_env = os.environ.get("NODE_ENV")
    os.environ["NODE_ENV"] = "development"

    try:
        manager = await setup_radio_manager_with_websocket(
            config=Config,
            mock_mode=True
        )
        yield manager
        await manager.shutdown()
    finally:
        if original_env:
            os.environ["NODE_ENV"] = original_env
        elif "NODE_ENV" in os.environ:
            del os.environ["NODE_ENV"]


@pytest.fixture
async def client(temp_data_dir):
    """Create HTTP client for API testing."""
    # Set test environment
    os.environ["NODE_ENV"] = "development"

    # Initialize radio manager for integration tests
    manager = await setup_radio_manager_with_websocket(
        config=Config,
        mock_mode=True
    )

    try:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    finally:
        await manager.shutdown()


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
def invalid_station_request():
    """Invalid station request for testing validation."""
    return {
        "name": "Invalid Station",
        "url": "not-a-valid-url",  # Invalid URL format
        "country": "Test"
    }


@pytest.fixture
def mock_stations_data():
    """Mock stations data for testing."""
    return {
        "1": {
            "name": "Mock Station 1",
            "url": "https://mock1.example.com/stream",
            "slot": 1,
            "genre": "Pop",
            "country": "Mock Country"
        },
        "2": None,
        "3": {
            "name": "Mock Station 3",
            "url": "https://mock3.example.com/stream",
            "slot": 3,
            "genre": "Jazz",
            "country": "Mock Country"
        }
    }


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection for testing."""
    mock_ws = MagicMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.receive_text = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


@pytest.fixture
def mock_audio_player():
    """Mock audio player for testing without actual audio."""
    with patch('hardware.audio_player.AudioPlayer') as mock:
        instance = mock.return_value
        instance.initialize = AsyncMock()
        instance.play = AsyncMock(return_value=True)
        instance.stop = AsyncMock(return_value=True)
        instance.set_volume = AsyncMock(return_value=True)
        instance.get_volume = AsyncMock(return_value=50)
        instance.is_playing = False
        instance.current_url = None
        yield instance


@pytest.fixture
def mock_gpio_controller():
    """Mock GPIO controller for testing without hardware."""
    with patch('hardware.gpio_controller.GPIOController') as mock:
        instance = mock.return_value
        instance.initialize = AsyncMock()
        instance.cleanup = AsyncMock()
        instance.read_button = MagicMock(return_value=False)
        instance.set_callback = MagicMock()
        yield instance


@pytest.fixture
def sample_volume_levels():
    """Sample volume levels for testing."""
    return {
        "min": 0,
        "low": 25,
        "medium": 50,
        "high": 75,
        "max": 100,
        "over_max": 150,  # Should be clamped
        "negative": -10   # Should be clamped
    }


@pytest.fixture
async def populated_station_manager(temp_data_dir):
    """Station manager with pre-populated test stations."""
    from core.station_manager import StationManager

    stations_file = temp_data_dir / "data" / "populated_stations.json"
    manager = StationManager(stations_file)

    # Add test stations
    test_stations = [
        StationRequest(name="Pop Station", url="https://pop.example.com/stream", genre="Pop"),
        StationRequest(name="Jazz Station", url="https://jazz.example.com/stream", genre="Jazz"),
        StationRequest(name="Rock Station", url="https://rock.example.com/stream", genre="Rock")
    ]

    await manager.initialize()
    for i, station in enumerate(test_stations, 1):
        await manager.save_station(i, station)

    return manager


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
            "auto_resume": True,
            "fade_in_duration": 1.5,
            "fade_out_duration": 0.8
        },
        "ui": {
            "theme": "dark",
            "language": "en",
            "show_station_info": True,
            "show_volume_percentage": True
        },
        "hardware": {
            "button_feedback": True,
            "volume_step_size": 5,
            "long_press_duration": 2.5
        }
    }


@pytest.fixture
def websocket_messages():
    """Sample WebSocket messages for testing."""
    return {
        "volume_update": {
            "type": "volume_update",
            "data": {"volume": 75, "station_slot": 1}
        },
        "station_change": {
            "type": "station_change",
            "data": {"slot": 2, "station_name": "Jazz FM", "action": "playing"}
        },
        "system_status": {
            "type": "system_status",
            "data": {
                "volume": 50,
                "is_playing": True,
                "current_station": 1,
                "playback_state": "playing"
            }
        },
        "error": {
            "type": "error",
            "data": {"message": "Connection failed", "code": "STREAM_ERROR"}
        }
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment for all tests."""
    # Ensure we're in development mode
    original_env = os.environ.get("NODE_ENV")
    os.environ["NODE_ENV"] = "development"

    yield

    # Restore original environment
    if original_env:
        os.environ["NODE_ENV"] = original_env
    elif "NODE_ENV" in os.environ:
        del os.environ["NODE_ENV"]


# Helper functions for tests
def assert_station_equal(station1: RadioStation, station2: RadioStation):
    """Assert two stations are equal (ignoring timestamps)."""
    assert station1.name == station2.name
    assert station1.url == station2.url
    assert station1.slot == station2.slot
    assert station1.country == station2.country
    assert station1.genre == station2.genre


def create_test_station(slot: int = 1, name_suffix: str = "") -> StationRequest:
    """Helper to create test station requests."""
    return StationRequest(
        name=f"Test Station {slot}{name_suffix}",
        url=f"https://test{slot}.example.com/stream",
        country="Test Country",
        genre=f"Test Genre {slot}"
    )


async def wait_for_async_tasks(timeout: float = 1.0):
    """Wait for pending async tasks to complete."""
    await asyncio.sleep(0.1)  # Allow tasks to start
    pending = [task for task in asyncio.all_tasks() if not task.done()]
    if pending:
        await asyncio.wait(pending, timeout=timeout, return_when=asyncio.ALL_COMPLETED)
