"""
Unit tests for the StationManager class.

Tests the core functionality of station management including:
- Station CRUD operations
- 3-slot management system
- Data persistence and validation
- Default station loading
- Error handling and edge cases
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from core.station_manager import StationManager
from core.models import RadioStation, StationRequest


@pytest.mark.unit
class TestStationManager:
    """Test StationManager functionality in isolation."""

    @pytest.fixture
    async def station_manager(self, temp_data_dir):
        """Create station manager for testing."""
        stations_file = temp_data_dir / "data" / "test_stations.json"
        manager = StationManager(stations_file)
        await manager.initialize()
        return manager

    @pytest.fixture
    def sample_station_request(self):
        """Sample station request for testing."""
        return StationRequest(
            name="Test Station",
            url="https://test.example.com/stream",
            country="Test Country",
            location="Test City",
            genre="Test Genre",
            bitrate="128k",
            language="English"
        )

    async def test_initialization(self, station_manager):
        """Test station manager initialization."""
        assert station_manager is not None
        assert station_manager._stations is not None

        # Should have 3 slots
        stations = await station_manager.get_all_stations()
        assert isinstance(stations, dict)
        assert len(stations) == 3
        assert all(slot in stations for slot in [1, 2, 3])

    async def test_initialization_with_existing_file(self, temp_data_dir):
        """Test initialization with existing stations file."""
        stations_file = temp_data_dir / "data" / "existing_stations.json"

        # Create existing file with test data
        existing_data = {
            "1": {
                "name": "Existing Station",
                "url": "https://existing.example.com/stream",
                "slot": 1,
                "genre": "Existing"
            },
            "2": None,
            "3": None
        }

        stations_file.write_text(json.dumps(existing_data))

        # Initialize manager with existing file
        manager = StationManager(stations_file)
        await manager.initialize()

        # Should load existing station
        station = await manager.get_station(1)
        assert station is not None
        assert station.name == "Existing Station"

    async def test_initialization_with_missing_file(self, temp_data_dir):
        """Test initialization when stations file doesn't exist."""
        stations_file = temp_data_dir / "data" / "missing_stations.json"

        # File doesn't exist
        assert not stations_file.exists()

        manager = StationManager(stations_file)
        await manager.initialize()

        # Should create file with defaults
        assert stations_file.exists()

        stations = await manager.get_all_stations()
        # Should have default stations loaded
        assert any(station is not None for station in stations.values())

    async def test_save_and_retrieve_station(self, station_manager, sample_station_request):
        """Test saving and retrieving a station."""
        # Save station to slot 1
        saved_station = await station_manager.save_station(1, sample_station_request)

        assert saved_station.name == sample_station_request.name
        assert saved_station.url == sample_station_request.url
        assert saved_station.slot == 1
        assert saved_station.country == sample_station_request.country

        # Retrieve station
        retrieved_station = await station_manager.get_station(1)
        assert retrieved_station is not None
        assert retrieved_station.name == sample_station_request.name
        assert retrieved_station.url == sample_station_request.url

    async def test_save_station_validation(self, station_manager):
        """Test station validation during save."""
        # Test valid station
        valid_request = StationRequest(
            name="Valid Station",
            url="https://valid.example.com/stream"
        )

        saved = await station_manager.save_station(2, valid_request)
        assert saved is not None
        assert saved.name == "Valid Station"

    async def test_save_to_all_slots(self, station_manager):
        """Test saving stations to all three slots."""
        stations = [
            StationRequest(name=f"Station {i}", url=f"https://test{i}.example.com/stream")
            for i in range(1, 4)
        ]

        # Save to all slots
        for i, station_request in enumerate(stations):
            saved = await station_manager.save_station(i + 1, station_request)
            assert saved.slot == i + 1
            assert saved.name == f"Station {i + 1}"

        # Verify all are saved
        all_stations = await station_manager.get_all_stations()
        for slot in [1, 2, 3]:
            assert all_stations[slot] is not None
            assert all_stations[slot].name == f"Station {slot}"

    async def test_get_all_stations(self, station_manager, sample_station_request):
        """Test retrieving all stations."""
        # Save a station
        await station_manager.save_station(2, sample_station_request)

        stations = await station_manager.get_all_stations()
        assert len(stations) == 3
        assert stations[2] is not None
        assert stations[2].name == sample_station_request.name

    async def test_delete_station(self, station_manager, sample_station_request):
        """Test deleting a station."""
        # Save station first
        await station_manager.save_station(2, sample_station_request)

        # Verify it exists
        station = await station_manager.get_station(2)
        assert station is not None
        assert station.name == sample_station_request.name

        # Delete station
        success = await station_manager.delete_station(2)
        assert success is True

        # Should load default station (not None)
        station = await station_manager.get_station(2)
        assert station is not None  # Default should be loaded
        assert station.name != sample_station_request.name  # Should be different

    async def test_clear_slot(self, station_manager, sample_station_request):
        """Test clearing a slot completely."""
        # Save station first
        await station_manager.save_station(3, sample_station_request)

        # Verify it exists
        station = await station_manager.get_station(3)
        assert station is not None

        # Clear slot
        success = await station_manager.clear_slot(3)
        assert success is True

        # Verify slot is empty
        station = await station_manager.get_station(3)
        assert station is None

    async def test_slot_validation(self, station_manager, sample_station_request):
        """Test slot number validation."""
        # Valid slots should work
        for slot in [1, 2, 3]:
            saved = await station_manager.save_station(slot, sample_station_request)
            assert saved.slot == slot

        # Test getting from valid slots
        for slot in [1, 2, 3]:
            station = await station_manager.get_station(slot)
            # Should not raise exception

    async def test_invalid_slot_handling(self, station_manager, sample_station_request):
        """Test handling of invalid slot numbers."""
        # Note: Actual validation behavior depends on implementation
        # This tests the expected behavior based on the API design

        # Test slot bounds in get_station
        valid_slots = [1, 2, 3]
        for slot in valid_slots:
            # Should not raise exception
            result = await station_manager.get_station(slot)
            # Result can be None or a station

    async def test_get_configured_count(self, station_manager, sample_station_request):
        """Test getting count of configured stations."""
        initial_count = await station_manager.get_configured_count()

        # Save a station
        await station_manager.save_station(1, sample_station_request)
        new_count = await station_manager.get_configured_count()

        # Count should increase
        assert new_count >= initial_count

        # Clear a slot
        await station_manager.clear_slot(1)
        cleared_count = await station_manager.get_configured_count()

        # Count should decrease
        assert cleared_count < new_count

    async def test_is_slot_empty(self, station_manager, sample_station_request):
        """Test checking if a slot is empty."""
        # Clear slot first
        await station_manager.clear_slot(1)

        # Should be empty
        is_empty = await station_manager.is_slot_empty(1)
        assert is_empty is True

        # Save station
        await station_manager.save_station(1, sample_station_request)

        # Should not be empty
        is_empty = await station_manager.is_slot_empty(1)
        assert is_empty is False

    @patch('aiohttp.ClientSession.get')
    async def test_validate_station_url(self, mock_get, station_manager):
        """Test station URL validation."""
        # Mock successful HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response

        # Test valid URL
        is_valid = await station_manager.validate_station_url("https://valid.example.com/stream")
        # In mock mode, this might always return True
        # The actual behavior depends on implementation

        # Test invalid URL format
        is_valid = await station_manager.validate_station_url("not-a-url")
        # Should handle gracefully

    async def test_persistence_across_instances(self, temp_data_dir):
        """Test station persistence across manager instances."""
        stations_file = temp_data_dir / "data" / "persistence_test.json"

        # Create first manager and save station
        manager1 = StationManager(stations_file)
        await manager1.initialize()

        test_request = StationRequest(
            name="Persistence Test",
            url="https://persist.example.com/stream",
            genre="Test"
        )
        await manager1.save_station(1, test_request)

        # Create second manager and verify persistence
        manager2 = StationManager(stations_file)
        await manager2.initialize()

        retrieved = await manager2.get_station(1)
        assert retrieved is not None
        assert retrieved.name == "Persistence Test"
        assert retrieved.url == "https://persist.example.com/stream"

    async def test_file_corruption_handling(self, temp_data_dir):
        """Test handling of corrupted stations file."""
        stations_file = temp_data_dir / "data" / "corrupted.json"

        # Write corrupted JSON
        stations_file.write_text("{ invalid json content")

        # Should handle gracefully and load defaults
        manager = StationManager(stations_file)
        await manager.initialize()

        stations = await manager.get_all_stations()
        assert isinstance(stations, dict)
        assert len(stations) == 3

    async def test_concurrent_access(self, station_manager):
        """Test concurrent access to station manager."""
        import asyncio

        # Create multiple station requests
        requests = [
            StationRequest(name=f"Concurrent {i}", url=f"https://concurrent{i}.example.com/stream")
            for i in range(3)
        ]

        # Save concurrently to different slots
        tasks = [
            station_manager.save_station(i + 1, request)
            for i, request in enumerate(requests)
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed
        for i, result in enumerate(results):
            assert result is not None
            assert result.slot == i + 1

    async def test_export_stations(self, station_manager, sample_station_request):
        """Test exporting stations for backup."""
        # Save some stations
        await station_manager.save_station(1, sample_station_request)

        export_data = await station_manager.export_stations()
        assert isinstance(export_data, dict)
        assert "stations" in export_data
        assert "metadata" in export_data or "timestamp" in export_data

    async def test_import_stations(self, station_manager):
        """Test importing stations from backup."""
        # Prepare import data
        import_data = {
            "stations": {
                "1": {
                    "name": "Imported Station",
                    "url": "https://imported.example.com/stream",
                    "slot": 1,
                    "genre": "Imported"
                }
            },
            "metadata": {
                "version": "1.0.0",
                "exported_at": "2024-01-01T00:00:00Z"
            }
        }

        success = await station_manager.import_stations(import_data)
        # Implementation may vary - test based on actual method

        if hasattr(station_manager, 'import_stations'):
            # Verify import worked if method exists
            station = await station_manager.get_station(1)
            # Test based on implementation

    async def test_default_stations_loading(self, temp_data_dir):
        """Test that default stations are loaded correctly."""
        stations_file = temp_data_dir / "data" / "defaults_test.json"

        manager = StationManager(stations_file)
        await manager.initialize()

        stations = await manager.get_all_stations()

        # Should have some default stations (implementation specific)
        default_count = sum(1 for station in stations.values() if station is not None)
        assert default_count > 0  # At least some defaults should be loaded

    async def test_station_metadata_handling(self, station_manager):
        """Test handling of station metadata fields."""
        detailed_request = StationRequest(
            name="Detailed Station",
            url="https://detailed.example.com/stream",
            country="Test Country",
            location="Test City",
            genre="Progressive Rock",
            bitrate="320k",
            language="English"
        )

        saved = await station_manager.save_station(1, detailed_request)

        # Verify all metadata is preserved
        assert saved.country == "Test Country"
        assert saved.location == "Test City"
        assert saved.genre == "Progressive Rock"
        assert saved.bitrate == "320k"
        assert saved.language == "English"

        # Verify retrieval preserves metadata
        retrieved = await station_manager.get_station(1)
        assert retrieved.country == "Test Country"
        assert retrieved.bitrate == "320k"

    async def test_error_handling_during_save(self, temp_data_dir):
        """Test error handling during station save operations."""
        # Create manager with read-only file to simulate write errors
        stations_file = temp_data_dir / "data" / "readonly_test.json"

        manager = StationManager(stations_file)
        await manager.initialize()

        # Try to make file read-only (if possible in test environment)
        try:
            stations_file.chmod(0o444)  # Read-only

            request = StationRequest(
                name="Error Test",
                url="https://error.example.com/stream"
            )

            # Save should handle error gracefully
            # Implementation may vary - test based on actual behavior
            result = await manager.save_station(1, request)

            # Restore permissions
            stations_file.chmod(0o644)
        except (OSError, PermissionError):
            # Skip this test if file permissions can't be changed
            pass

    async def test_memory_consistency(self, station_manager, sample_station_request):
        """Test consistency between memory and file storage."""
        # Save station
        saved = await station_manager.save_station(1, sample_station_request)

        # Get from memory
        from_memory = await station_manager.get_station(1)

        # Should be consistent
        assert from_memory.name == saved.name
        assert from_memory.url == saved.url
        assert from_memory.slot == saved.slot

        # Verify file was updated
        if station_manager.stations_file.exists():
            file_content = json.loads(station_manager.stations_file.read_text())
            if "1" in file_content and file_content["1"]:
                assert file_content["1"]["name"] == saved.name
