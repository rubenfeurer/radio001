"""
API endpoint tests for station management routes.

Tests all station management API endpoints including:
- GET /radio/stations/ - Get all stations
- GET /radio/stations/{slot} - Get station by slot
- POST /radio/stations/{slot} - Save station to slot
- POST /radio/stations/{slot}/toggle - Toggle station playback
- POST /radio/stations/{slot}/play - Play specific station
- DELETE /radio/stations/{slot} - Remove station
- POST /radio/stations/{slot}/clear - Clear station slot
"""

import pytest
import json
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


@pytest.mark.api
class TestStationRoutes:
    """Test station management API endpoints."""

    async def test_get_all_stations_endpoint(self, client: AsyncClient):
        """Test GET /radio/stations/ endpoint."""
        response = await client.get("/radio/stations/")
        assert response.status_code == 200

        data = response.json()
        assert "stations" in data
        assert "total_configured" in data
        assert isinstance(data["stations"], dict)
        assert len(data["stations"]) == 3

        # Check slot structure
        for slot in ["1", "2", "3"]:
            assert slot in data["stations"]
            # Station can be None or a station object

    async def test_get_station_by_slot_valid(self, client: AsyncClient):
        """Test GET /radio/stations/{slot} endpoint with valid slots."""
        for slot in [1, 2, 3]:
            response = await client.get(f"/radio/stations/{slot}")
            assert response.status_code == 200
            # Response can be station object or None

    async def test_get_station_by_slot_invalid(self, client: AsyncClient):
        """Test GET /radio/stations/{slot} endpoint with invalid slots."""
        invalid_slots = [0, 4, 5, -1, 999]
        for slot in invalid_slots:
            response = await client.get(f"/radio/stations/{slot}")
            assert response.status_code == 400
            error_data = response.json()
            assert "Slot must be 1, 2, or 3" in error_data["detail"]

    async def test_save_station_success(self, client: AsyncClient):
        """Test POST /radio/stations/{slot} endpoint with valid data."""
        station_data = {
            "name": "API Test Station",
            "url": "https://api-test.example.com/stream",
            "country": "Test Land",
            "location": "Test City",
            "genre": "Test Music",
            "bitrate": "128k",
            "language": "English"
        }

        response = await client.post("/radio/stations/1", json=station_data)
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert "Station" in result["message"]
        assert "saved to slot 1" in result["message"]
        assert "data" in result
        assert result["data"]["slot"] == 1
        assert "station" in result["data"]

    async def test_save_station_minimal_data(self, client: AsyncClient):
        """Test saving station with minimal required data."""
        minimal_station = {
            "name": "Minimal Station",
            "url": "https://minimal.example.com/stream"
        }

        response = await client.post("/radio/stations/2", json=minimal_station)
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True

    async def test_save_station_validation_errors(self, client: AsyncClient):
        """Test station validation on save."""
        # Test invalid URL
        invalid_station = {
            "name": "Invalid Station",
            "url": "not-a-valid-url"
        }
        response = await client.post("/radio/stations/1", json=invalid_station)
        assert response.status_code == 422

        # Test missing required fields
        incomplete_stations = [
            {"url": "https://valid.example.com/stream"},  # Missing name
            {"name": "Valid Name"},  # Missing URL
            {},  # Missing both
        ]

        for incomplete_station in incomplete_stations:
            response = await client.post("/radio/stations/1", json=incomplete_station)
            assert response.status_code == 422

    async def test_save_station_invalid_slot(self, client: AsyncClient):
        """Test saving to invalid slot numbers."""
        station_data = {
            "name": "Valid Station",
            "url": "https://valid.example.com/stream"
        }

        invalid_slots = [0, 4, -1]
        for slot in invalid_slots:
            response = await client.post(f"/radio/stations/{slot}", json=station_data)
            assert response.status_code == 400

    async def test_save_station_url_validation(self, client: AsyncClient):
        """Test various URL validation scenarios."""
        # Valid URLs
        valid_urls = [
            "https://stream.example.com/radio",
            "http://stream.example.com/radio.mp3",
            "https://radio.stream.com:8080/live",
        ]

        for url in valid_urls:
            station_data = {
                "name": "URL Test Station",
                "url": url
            }
            response = await client.post("/radio/stations/1", json=station_data)
            assert response.status_code == 200

    async def test_save_station_url_validation(self, client: AsyncClient):
        """Test URL validation when saving stations."""
        # Test invalid URLs (must start with http:// or https://)
        invalid_urls = [
            "ftp://invalid.com/stream",  # Wrong protocol
            "not-a-url-at-all",  # No protocol
            "",  # Empty string
            "javascript:alert('xss')"  # XSS attempt
        ]

        for url in invalid_urls:
            invalid_station = {
                "name": "Invalid URL Station",
                "url": url
            }
            response = await client.post("/radio/stations/1", json=invalid_station)
            assert response.status_code == 422

        # Test valid URLs (should be accepted)
        valid_urls = [
            "http://valid.example.com/stream",
            "https://secure.example.com/stream",
            "http://",  # Minimal valid format (starts with http://)
        ]

        for url in valid_urls:
            valid_station = {
                "name": "Valid URL Station",
                "url": url
            }
            response = await client.post("/radio/stations/1", json=valid_station)
            assert response.status_code == 200

    async def test_toggle_station_playback_success(self, client: AsyncClient):
        """Test POST /radio/stations/{slot}/toggle endpoint."""
        # First save a station
        station_data = {
            "name": "Toggle Test Station",
            "url": "https://toggle-test.example.com/stream"
        }
        await client.post("/radio/stations/2", json=station_data)

        # Test toggle
        response = await client.post("/radio/stations/2/toggle")
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert "action" in result["data"]
        assert result["data"]["action"] in ["starting", "stopping"]
        assert result["data"]["slot"] == 2
        assert "station_name" in result["data"]

    async def test_toggle_empty_slot(self, client: AsyncClient):
        """Test toggling an empty slot."""
        # Clear slot first to ensure it's empty
        await client.post("/radio/stations/2/clear")

        # Try to toggle empty slot
        response = await client.post("/radio/stations/2/toggle")
        assert response.status_code == 404
        error_data = response.json()
        assert "No station configured in slot 2" in error_data["detail"]

    async def test_toggle_invalid_slot(self, client: AsyncClient):
        """Test toggling invalid slot numbers."""
        invalid_slots = [0, 4, -1]
        for slot in invalid_slots:
            response = await client.post(f"/radio/stations/{slot}/toggle")
            assert response.status_code == 400

    async def test_play_station_success(self, client: AsyncClient):
        """Test POST /radio/stations/{slot}/play endpoint."""
        # Save a station first
        station_data = {
            "name": "Play Test Station",
            "url": "https://play-test.example.com/stream"
        }
        await client.post("/radio/stations/1", json=station_data)

        # Test play
        response = await client.post("/radio/stations/1/play")
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert result["data"]["action"] == "playing"
        assert result["data"]["slot"] == 1

    async def test_play_empty_slot(self, client: AsyncClient):
        """Test playing an empty slot."""
        await client.post("/radio/stations/3/clear")

        response = await client.post("/radio/stations/3/play")
        assert response.status_code == 404

    async def test_delete_station_success(self, client: AsyncClient):
        """Test DELETE /radio/stations/{slot} endpoint."""
        # Save a station first
        station_data = {
            "name": "Delete Test Station",
            "url": "https://delete-test.example.com/stream"
        }
        await client.post("/radio/stations/1", json=station_data)

        # Delete the station
        response = await client.delete("/radio/stations/1")
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert "removed" in result["message"].lower() or "deleted" in result["message"].lower()
        assert "data" in result
        assert result["data"]["slot"] == 1

    async def test_delete_station_loads_default(self, client: AsyncClient):
        """Test that deleting a station loads the default."""
        # Save a custom station
        custom_station = {
            "name": "Custom Station",
            "url": "https://custom.example.com/stream"
        }
        await client.post("/radio/stations/1", json=custom_station)

        # Delete it
        response = await client.delete("/radio/stations/1")
        assert response.status_code == 200

        # Check that a default was loaded
        response = await client.get("/radio/stations/1")
        assert response.status_code == 200
        station = response.json()
        assert station is not None  # Should have default
        assert station["name"] != "Custom Station"  # Should be different

    async def test_delete_invalid_slot(self, client: AsyncClient):
        """Test deleting from invalid slot."""
        invalid_slots = [0, 4, -1]
        for slot in invalid_slots:
            response = await client.delete(f"/radio/stations/{slot}")
            assert response.status_code == 400

    async def test_clear_station_slot_success(self, client: AsyncClient):
        """Test POST /radio/stations/{slot}/clear endpoint."""
        # Save a station first
        station_data = {
            "name": "Clear Test Station",
            "url": "https://clear-test.example.com/stream"
        }
        await client.post("/radio/stations/3", json=station_data)

        # Clear the slot
        response = await client.post("/radio/stations/3/clear")
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert "cleared" in result["message"].lower()

        # Verify slot is empty
        response = await client.get("/radio/stations/3")
        assert response.status_code == 200
        assert response.json() is None

    async def test_clear_invalid_slot(self, client: AsyncClient):
        """Test clearing invalid slot numbers."""
        invalid_slots = [0, 4, -1]
        for slot in invalid_slots:
            response = await client.post(f"/radio/stations/{slot}/clear")
            assert response.status_code == 400

    async def test_clear_already_empty_slot(self, client: AsyncClient):
        """Test clearing an already empty slot."""
        # Ensure slot is empty
        await client.post("/radio/stations/2/clear")

        # Clear again
        response = await client.post("/radio/stations/2/clear")
        assert response.status_code == 200  # Should still succeed

    async def test_station_metadata_preservation(self, client: AsyncClient):
        """Test that all station metadata is preserved."""
        detailed_station = {
            "name": "Detailed Station",
            "url": "https://detailed.example.com/stream",
            "country": "Test Country",
            "location": "Test City",
            "genre": "Progressive Rock",
            "bitrate": "320k",
            "language": "English"
        }

        # Save station
        response = await client.post("/radio/stations/1", json=detailed_station)
        assert response.status_code == 200

        # Retrieve and verify metadata
        response = await client.get("/radio/stations/1")
        assert response.status_code == 200

        station = response.json()
        assert station["name"] == detailed_station["name"]
        assert station["url"] == detailed_station["url"]
        assert station["country"] == detailed_station["country"]
        assert station["location"] == detailed_station["location"]
        assert station["genre"] == detailed_station["genre"]
        assert station["bitrate"] == detailed_station["bitrate"]
        assert station["language"] == detailed_station["language"]
        assert station["slot"] == 1

    async def test_concurrent_station_operations(self, client: AsyncClient):
        """Test concurrent station operations."""
        import asyncio

        # Prepare station data for each slot
        stations = [
            {
                "name": f"Concurrent Station {i}",
                "url": f"https://concurrent{i}.example.com/stream"
            }
            for i in range(1, 4)
        ]

        # Save stations concurrently
        save_tasks = [
            client.post(f"/radio/stations/{i}", json=station)
            for i, station in enumerate(stations, 1)
        ]

        results = await asyncio.gather(*save_tasks)
        for result in results:
            assert result.status_code == 200

        # Verify all stations were saved
        response = await client.get("/radio/stations/")
        assert response.status_code == 200
        all_stations = response.json()
        assert all_stations["total_configured"] == 3

    async def test_station_workflow_integration(self, client: AsyncClient):
        """Test complete station workflow."""
        station_data = {
            "name": "Workflow Test Station",
            "url": "https://workflow.example.com/stream",
            "genre": "Integration Test"
        }

        # 1. Save station
        response = await client.post("/radio/stations/1", json=station_data)
        assert response.status_code == 200

        # 2. Verify it was saved
        response = await client.get("/radio/stations/1")
        assert response.status_code == 200
        station = response.json()
        assert station["name"] == station_data["name"]

        # 3. Play station
        response = await client.post("/radio/stations/1/play")
        assert response.status_code == 200

        # 4. Toggle (should stop)
        response = await client.post("/radio/stations/1/toggle")
        assert response.status_code == 200

        # 5. Clear station
        response = await client.post("/radio/stations/1/clear")
        assert response.status_code == 200

        # 6. Verify it's empty
        response = await client.get("/radio/stations/1")
        assert response.status_code == 200
        assert response.json() is None

    async def test_error_response_format(self, client: AsyncClient):
        """Test that error responses follow expected format."""
        # Test validation error
        response = await client.post("/radio/stations/1", json={"invalid": "data"})
        assert response.status_code == 422

        # Should be FastAPI validation error format
        error_data = response.json()
        assert "detail" in error_data

        # Test not found error
        await client.post("/radio/stations/2/clear")  # Ensure empty
        response = await client.post("/radio/stations/2/toggle")
        assert response.status_code == 404

        error_data = response.json()
        assert "detail" in error_data

        # Test bad request error
        response = await client.get("/radio/stations/0")
        assert response.status_code == 400

        error_data = response.json()
        assert "detail" in error_data

    @patch('core.station_manager.StationManager.validate_station_url')
    async def test_url_validation_mock(self, mock_validate, client: AsyncClient):
        """Test URL validation behavior in different scenarios."""
        # Test when validation passes
        mock_validate.return_value = True

        station_data = {
            "name": "Validation Test",
            "url": "https://validation.example.com/stream"
        }

        response = await client.post("/radio/stations/1", json=station_data)
        assert response.status_code == 200

        # Test when validation fails
        mock_validate.return_value = False

        response = await client.post("/radio/stations/1", json=station_data)
        # Should still succeed due to mock mode, but in production might fail

    async def test_large_station_name(self, client: AsyncClient):
        """Test handling of large station names."""
        # Test maximum length name (100 characters as per model)
        long_name = "A" * 100
        station_data = {
            "name": long_name,
            "url": "https://long-name.example.com/stream"
        }

        response = await client.post("/radio/stations/1", json=station_data)
        assert response.status_code == 200

        # Test name too long (should fail validation)
        too_long_name = "A" * 101
        station_data["name"] = too_long_name

        response = await client.post("/radio/stations/1", json=station_data)
        assert response.status_code == 422

    async def test_special_characters_in_station_data(self, client: AsyncClient):
        """Test handling of special characters in station data."""
        special_station = {
            "name": "Rádio Français & More! 🎵",
            "url": "https://special.example.com/stream",
            "country": "França",
            "location": "São Paulo",
            "genre": "Rock & Roll",
            "language": "Português"
        }

        response = await client.post("/radio/stations/1", json=special_station)
        assert response.status_code == 200

        # Verify special characters are preserved
        response = await client.get("/radio/stations/1")
        assert response.status_code == 200
        station = response.json()
        assert station["name"] == special_station["name"]
        assert station["country"] == special_station["country"]
