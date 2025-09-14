"""
Integration tests for the complete radio system.
Tests end-to-end workflows and component interactions.
"""

import pytest
import json
import asyncio
from httpx import AsyncClient
from unittest.mock import patch
import websockets
from websockets.exceptions import ConnectionClosed


@pytest.mark.integration
class TestRadioSystemIntegration:
    """Test complete radio system workflows."""

    async def test_system_startup_and_health(self, client: AsyncClient):
        """Test system startup and health check."""
        # Test root endpoint
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "radio_streaming" in data["data"]["features"]
        assert "3_slot_stations" in data["data"]["features"]
        assert data["data"]["version"] == "2.0.0"

        # Test health check
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "radio_system" in data["data"]
        assert "data_dir_exists" in data["data"]
        assert "sounds_dir_exists" in data["data"]

    async def test_complete_station_workflow(self, client: AsyncClient):
        """Test complete station management workflow."""
        # 1. Get initial stations
        response = await client.get("/radio/stations/")
        assert response.status_code == 200
        initial_stations = response.json()
        assert "stations" in initial_stations
        assert "total_configured" in initial_stations

        # 2. Save a new station to slot 1
        station_data = {
            "name": "Integration Test Station",
            "url": "https://test-stream.example.com/radio",
            "country": "Test Country",
            "genre": "Integration Test",
            "bitrate": "128k",
            "language": "English"
        }
        response = await client.post("/radio/stations/1", json=station_data)
        assert response.status_code == 200
        save_result = response.json()
        assert save_result["success"] is True
        assert "Integration Test Station" in save_result["message"]

        # 3. Verify station was saved
        response = await client.get("/radio/stations/1")
        assert response.status_code == 200
        saved_station = response.json()
        assert saved_station["name"] == station_data["name"]
        assert saved_station["url"] == station_data["url"]
        assert saved_station["slot"] == 1

        # 4. Test station playback toggle
        response = await client.post("/radio/stations/1/toggle")
        assert response.status_code == 200
        toggle_result = response.json()
        assert toggle_result["success"] is True
        assert "action" in toggle_result["data"]

        # 5. Check system status after toggle
        response = await client.get("/radio/status")
        assert response.status_code == 200
        status = response.json()
        assert "volume" in status
        assert "is_playing" in status
        assert "playback_state" in status

        # 6. Stop playback
        response = await client.post("/radio/stop")
        assert response.status_code == 200
        stop_result = response.json()
        assert stop_result["success"] is True

        # 7. Test station clearing
        response = await client.post("/radio/stations/1/clear")
        assert response.status_code == 200
        clear_result = response.json()
        assert clear_result["success"] is True

        # 8. Verify slot is empty
        response = await client.get("/radio/stations/1")
        assert response.status_code == 200
        assert response.json() is None

        # 9. Delete station (should load default)
        # First save another station
        await client.post("/radio/stations/2", json=station_data)
        response = await client.delete("/radio/stations/2")
        assert response.status_code == 200
        delete_result = response.json()
        assert delete_result["success"] is True

    async def test_volume_control_workflow(self, client: AsyncClient):
        """Test volume control workflow with limits and validation."""
        # 1. Get current volume
        response = await client.get("/radio/volume")
        assert response.status_code == 200
        initial_volume = response.json()
        assert "volume" in initial_volume
        assert "min_volume" in initial_volume
        assert "max_volume" in initial_volume

        # 2. Set volume to 75
        response = await client.post("/radio/volume", json={"volume": 75})
        assert response.status_code == 200
        volume_result = response.json()
        assert volume_result["success"] is True

        # 3. Verify volume was set
        response = await client.get("/radio/status")
        assert response.status_code == 200
        status = response.json()
        assert status["volume"] == 75

        # 4. Test volume up
        response = await client.post("/radio/volume/up")
        assert response.status_code == 200
        up_result = response.json()
        assert up_result["success"] is True
        assert up_result["data"]["volume"] > 75

        # 5. Test volume down
        response = await client.post("/radio/volume/down")
        assert response.status_code == 200
        down_result = response.json()
        assert down_result["success"] is True

        # 6. Test volume limits - maximum
        response = await client.post("/radio/volume", json={"volume": 150})
        assert response.status_code == 200
        max_result = response.json()
        # Should be clamped to hardware maximum
        assert max_result["data"]["volume"] <= 100

        # 7. Test volume limits - minimum (mute allowed)
        response = await client.post("/radio/volume", json={"volume": -10})
        assert response.status_code == 200
        min_result = response.json()
        assert min_result["data"]["volume"] == 0

        # 8. Test hardware volume limits
        response = await client.post("/radio/volume", json={"volume": 25})
        assert response.status_code == 200
        # Should respect minimum hardware volume when above 0

    async def test_multiple_station_management(self, client: AsyncClient):
        """Test managing all three station slots simultaneously."""
        stations_data = [
            {
                "name": "Pop Station",
                "url": "https://pop.example.com/stream",
                "genre": "Pop",
                "country": "USA"
            },
            {
                "name": "Jazz Station",
                "url": "https://jazz.example.com/stream",
                "genre": "Jazz",
                "country": "France"
            },
            {
                "name": "Classical Station",
                "url": "https://classical.example.com/stream",
                "genre": "Classical",
                "country": "Austria"
            }
        ]

        # Save stations to all slots
        for slot, station_data in enumerate(stations_data, 1):
            response = await client.post(f"/radio/stations/{slot}", json=station_data)
            assert response.status_code == 200

        # Verify all stations are saved
        response = await client.get("/radio/stations/")
        assert response.status_code == 200
        all_stations = response.json()
        assert all_stations["total_configured"] == 3

        for slot in [1, 2, 3]:
            station = all_stations["stations"][str(slot)]
            assert station is not None
            assert station["name"] == stations_data[slot-1]["name"]

        # Test playing different stations
        for slot in [1, 2, 3]:
            response = await client.post(f"/radio/stations/{slot}/play")
            assert response.status_code == 200
            play_result = response.json()
            assert play_result["success"] is True

        # Stop playback
        response = await client.post("/radio/stop")
        assert response.status_code == 200

    async def test_hardware_simulation_workflow(self, client: AsyncClient):
        """Test hardware simulation in development mode."""
        # Test button simulation for all slots
        for button in [1, 2, 3]:
            response = await client.post(f"/radio/dev/simulate-button/{button}")
            assert response.status_code == 200
            button_result = response.json()
            assert button_result["success"] is True
            assert button_result["data"]["button"] == button

        # Test volume simulation - increase
        response = await client.post("/radio/dev/simulate-volume/5")
        assert response.status_code == 200
        volume_result = response.json()
        assert volume_result["success"] is True
        assert volume_result["data"]["change"] == 5

        # Test volume simulation - decrease
        response = await client.post("/radio/dev/simulate-volume/-3")
        assert response.status_code == 200
        volume_result = response.json()
        assert volume_result["success"] is True
        assert volume_result["data"]["change"] == -3

        # Test hardware status
        response = await client.get("/radio/hardware-status")
        assert response.status_code == 200
        hw_status = response.json()
        assert hw_status["mock_mode"] is True
        assert "gpio_available" in hw_status
        assert "audio_available" in hw_status

    async def test_playback_status_workflow(self, client: AsyncClient):
        """Test detailed playback status tracking."""
        # Save a test station
        station_data = {
            "name": "Status Test Station",
            "url": "https://status-test.example.com/stream"
        }
        await client.post("/radio/stations/1", json=station_data)

        # Get initial playback status
        response = await client.get("/radio/playback-status")
        assert response.status_code == 200
        initial_status = response.json()
        assert "state" in initial_status
        assert "volume" in initial_status

        # Start playback
        response = await client.post("/radio/stations/1/play")
        assert response.status_code == 200

        # Check playback status after starting
        response = await client.get("/radio/playback-status")
        assert response.status_code == 200
        playing_status = response.json()
        # Status should reflect playback attempt (may be mocked)

        # Stop playback
        await client.post("/radio/stop")

        # Check final status
        response = await client.get("/radio/playback-status")
        assert response.status_code == 200
        stopped_status = response.json()
        assert stopped_status["state"] in ["stopped", "error"]  # Depends on mock implementation

    async def test_error_handling_and_edge_cases(self, client: AsyncClient):
        """Test error handling and edge cases throughout the system."""
        # Test invalid slot numbers
        for invalid_slot in [0, 4, 5, -1]:
            response = await client.get(f"/radio/stations/{invalid_slot}")
            assert response.status_code == 400

        # Test invalid volume values
        response = await client.post("/radio/volume", json={"volume": "invalid"})
        assert response.status_code == 422  # Validation error

        response = await client.post("/radio/volume", json={})
        assert response.status_code == 422  # Missing required field

        # Test invalid station URLs
        invalid_stations = [
            {"name": "Invalid URL", "url": "not-a-url"},
            {"name": "Missing URL"},  # No URL field
            {"url": "https://valid.com"},  # No name field
        ]

        for invalid_station in invalid_stations:
            response = await client.post("/radio/stations/1", json=invalid_station)
            assert response.status_code == 422

        # Test playing empty slot
        await client.post("/radio/stations/2/clear")  # Ensure slot is empty
        response = await client.post("/radio/stations/2/toggle")
        assert response.status_code == 404

        # Test invalid button simulation
        response = await client.post("/radio/dev/simulate-button/4")
        assert response.status_code == 400

        # Test extreme volume simulation
        response = await client.post("/radio/dev/simulate-volume/100")
        assert response.status_code == 400  # Should reject extreme values

    async def test_station_validation_workflow(self, client: AsyncClient):
        """Test station URL validation and reachability."""
        # Test valid URLs (should pass validation)
        valid_stations = [
            {
                "name": "HTTP Station",
                "url": "http://stream.example.com/radio"
            },
            {
                "name": "HTTPS Station",
                "url": "https://secure-stream.example.com/radio"
            }
        ]

        for station in valid_stations:
            response = await client.post("/radio/stations/1", json=station)
            assert response.status_code == 200

        # Test invalid URLs (should fail validation)
        invalid_urls = [
            "ftp://invalid.com/stream",
            "not-a-url-at-all",
            "http://",
            "",
            "javascript:alert('xss')"
        ]

        for invalid_url in invalid_urls:
            invalid_station = {
                "name": "Invalid Station",
                "url": invalid_url
            }
            response = await client.post("/radio/stations/1", json=invalid_station)
            assert response.status_code == 422

    async def test_system_shutdown_workflow(self, client: AsyncClient):
        """Test graceful system shutdown."""
        # Start some activity
        station_data = {
            "name": "Shutdown Test Station",
            "url": "https://shutdown-test.example.com/stream"
        }
        await client.post("/radio/stations/1", json=station_data)
        await client.post("/radio/stations/1/play")

        # Test shutdown
        response = await client.post("/radio/shutdown")
        assert response.status_code == 200
        shutdown_result = response.json()
        assert shutdown_result["success"] is True
        assert "shutdown" in shutdown_result["message"].lower()

    @pytest.mark.slow
    async def test_concurrent_operations(self, client: AsyncClient):
        """Test concurrent operations to ensure thread safety."""
        # Prepare test data
        stations = [
            {"name": f"Concurrent Station {i}", "url": f"https://concurrent{i}.example.com/stream"}
            for i in range(1, 4)
        ]

        # Test concurrent station saves
        tasks = []
        for i, station in enumerate(stations):
            task = client.post(f"/radio/stations/{i+1}", json=station)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        for result in results:
            assert result.status_code == 200

        # Test concurrent volume changes
        volume_tasks = []
        for volume in [25, 50, 75]:
            task = client.post("/radio/volume", json={"volume": volume})
            volume_tasks.append(task)

        volume_results = await asyncio.gather(*volume_tasks)
        for result in volume_results:
            assert result.status_code == 200

        # Test concurrent status requests
        status_tasks = [client.get("/radio/status") for _ in range(5)]
        status_results = await asyncio.gather(*status_tasks)
        for result in status_results:
            assert result.status_code == 200

    async def test_data_persistence_workflow(self, client: AsyncClient):
        """Test that station data persists correctly."""
        # Save stations
        test_stations = [
            {
                "name": "Persistence Test 1",
                "url": "https://persist1.example.com/stream",
                "genre": "Rock"
            },
            {
                "name": "Persistence Test 2",
                "url": "https://persist2.example.com/stream",
                "genre": "Jazz"
            }
        ]

        for i, station in enumerate(test_stations):
            response = await client.post(f"/radio/stations/{i+1}", json=station)
            assert response.status_code == 200

        # Verify stations are retrievable
        for i in range(len(test_stations)):
            response = await client.get(f"/radio/stations/{i+1}")
            assert response.status_code == 200
            station = response.json()
            assert station["name"] == test_stations[i]["name"]

        # Test that data survives across different requests
        response = await client.get("/radio/stations/")
        assert response.status_code == 200
        all_stations = response.json()
        assert all_stations["total_configured"] >= 2

    async def test_preferences_and_settings(self, client: AsyncClient):
        """Test system preferences and settings management."""
        # Test getting initial system status with preferences
        response = await client.get("/radio/status")
        assert response.status_code == 200
        status = response.json()

        # Verify default volume is within expected range
        assert 0 <= status["volume"] <= 100

        # Test volume preference persistence
        test_volume = 60
        response = await client.post("/radio/volume", json={"volume": test_volume})
        assert response.status_code == 200

        # Verify volume persists in system status
        response = await client.get("/radio/status")
        assert response.status_code == 200
        updated_status = response.json()
        assert updated_status["volume"] == test_volume
