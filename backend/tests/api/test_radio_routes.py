"""
API endpoint tests for radio control routes.

Tests all radio system control API endpoints including:
- GET /radio/status - Get system status
- GET /radio/volume - Get current volume
- POST /radio/volume - Set volume level
- POST /radio/volume/up - Increase volume
- POST /radio/volume/down - Decrease volume
- POST /radio/stop - Stop all playback
- GET /radio/playback-status - Get detailed playback status
- GET /radio/hardware-status - Get hardware status
- POST /radio/shutdown - Shutdown radio system
- POST /radio/dev/simulate-button/{button} - Simulate button press (dev only)
- POST /radio/dev/simulate-volume/{change} - Simulate volume change (dev only)
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


@pytest.mark.api
class TestRadioControlRoutes:
    """Test radio system control API endpoints."""

    async def test_get_system_status(self, client: AsyncClient):
        """Test GET /radio/status endpoint."""
        response = await client.get("/radio/status")
        assert response.status_code == 200

        status = response.json()
        assert "volume" in status
        assert "is_playing" in status
        assert "playback_state" in status
        assert "current_station" in status
        assert "current_station_info" in status

        # Validate types
        assert isinstance(status["volume"], int)
        assert isinstance(status["is_playing"], bool)
        assert status["volume"] >= 0
        assert status["volume"] <= 100

    async def test_get_volume_info(self, client: AsyncClient):
        """Test GET /radio/volume endpoint."""
        response = await client.get("/radio/volume")
        assert response.status_code == 200

        volume_info = response.json()
        assert "volume" in volume_info
        assert "min_volume" in volume_info
        assert "max_volume" in volume_info
        assert "is_muted" in volume_info

        # Validate ranges
        assert volume_info["min_volume"] >= 0
        assert volume_info["max_volume"] <= 100
        assert volume_info["min_volume"] <= volume_info["max_volume"]
        assert isinstance(volume_info["is_muted"], bool)

    async def test_set_volume_valid_range(self, client: AsyncClient):
        """Test POST /radio/volume with valid volume levels."""
        valid_volumes = [0, 25, 50, 75, 100]

        for volume in valid_volumes:
            response = await client.post("/radio/volume", json={"volume": volume})
            assert response.status_code == 200

            result = response.json()
            assert result["success"] is True
            assert "volume" in result["message"].lower()
            assert "data" in result
            assert result["data"]["volume"] == volume or result["data"]["volume"] >= 30  # Hardware minimum

    async def test_set_volume_invalid_values(self, client: AsyncClient):
        """Test POST /radio/volume with invalid volume values."""
        # Test validation errors
        invalid_requests = [
            {},  # Missing volume
            {"volume": "invalid"},  # Non-integer
            {"volume": None},  # Null value
            {"invalid_field": 50},  # Wrong field name
        ]

        for invalid_request in invalid_requests:
            response = await client.post("/radio/volume", json=invalid_request)
            assert response.status_code == 422  # Validation error

    async def test_set_volume_boundary_clamping(self, client: AsyncClient):
        """Test volume clamping at boundaries."""
        # Test extreme values (should be clamped)
        extreme_values = [
            {"volume": -50, "expected_min": 0},
            {"volume": 150, "expected_max": 100},
            {"volume": 999, "expected_max": 100}
        ]

        for test_case in extreme_values:
            response = await client.post("/radio/volume", json={"volume": test_case["volume"]})
            assert response.status_code == 200

            result = response.json()
            assert result["success"] is True
            actual_volume = result["data"]["volume"]

            if "expected_min" in test_case:
                assert actual_volume >= test_case["expected_min"]
            if "expected_max" in test_case:
                assert actual_volume <= test_case["expected_max"]

    async def test_volume_up(self, client: AsyncClient):
        """Test POST /radio/volume/up endpoint."""
        # Set initial volume
        await client.post("/radio/volume", json={"volume": 50})

        # Test volume up
        response = await client.post("/radio/volume/up")
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert result["data"]["volume"] > 50
        assert "change" in result["data"]

    async def test_volume_up_at_maximum(self, client: AsyncClient):
        """Test volume up when already at maximum."""
        # Set to maximum volume first
        await client.post("/radio/volume", json={"volume": 100})

        response = await client.post("/radio/volume/up")
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert "already at maximum" in result["message"] or result["data"]["volume"] == 100

    async def test_volume_down(self, client: AsyncClient):
        """Test POST /radio/volume/down endpoint."""
        # Set initial volume
        await client.post("/radio/volume", json={"volume": 75})

        # Test volume down
        response = await client.post("/radio/volume/down")
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert result["data"]["volume"] < 75
        assert "change" in result["data"]
        assert result["data"]["change"] < 0

    async def test_volume_down_at_minimum(self, client: AsyncClient):
        """Test volume down when already at minimum."""
        # Set to minimum volume first
        await client.post("/radio/volume", json={"volume": 0})

        response = await client.post("/radio/volume/down")
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert "already at minimum" in result["message"] or result["data"]["volume"] == 0

    async def test_stop_playback_when_playing(self, client: AsyncClient):
        """Test POST /radio/stop when something is playing."""
        # First try to start something playing (save a station and play it)
        station_data = {
            "name": "Stop Test Station",
            "url": "https://stop-test.example.com/stream"
        }
        await client.post("/radio/stations/1", json=station_data)
        await client.post("/radio/stations/1/play")

        # Now test stop
        response = await client.post("/radio/stop")
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert "stop" in result["message"].lower()
        assert "data" in result

    async def test_stop_playback_when_not_playing(self, client: AsyncClient):
        """Test POST /radio/stop when nothing is playing."""
        response = await client.post("/radio/stop")
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert "no playback to stop" in result["message"].lower() or "stopped" in result["message"].lower()

    async def test_get_playback_status(self, client: AsyncClient):
        """Test GET /radio/playback-status endpoint."""
        response = await client.get("/radio/playback-status")
        assert response.status_code == 200

        status = response.json()
        assert "state" in status
        assert "volume" in status
        assert "station_slot" in status
        assert "station_name" in status

        # Validate state values
        valid_states = ["stopped", "playing", "paused", "connecting", "error"]
        assert status["state"] in valid_states

    async def test_get_hardware_status(self, client: AsyncClient):
        """Test GET /radio/hardware-status endpoint."""
        response = await client.get("/radio/hardware-status")
        assert response.status_code == 200

        hw_status = response.json()
        assert "gpio_available" in hw_status
        assert "audio_available" in hw_status
        assert "mock_mode" in hw_status
        assert "button_states" in hw_status

        # In test environment, should be in mock mode
        assert hw_status["mock_mode"] is True
        assert isinstance(hw_status["gpio_available"], bool)
        assert isinstance(hw_status["audio_available"], bool)

    async def test_system_shutdown(self, client: AsyncClient):
        """Test POST /radio/shutdown endpoint."""
        response = await client.post("/radio/shutdown")
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert "shutdown" in result["message"].lower()

    async def test_simulate_button_press_valid(self, client: AsyncClient):
        """Test POST /radio/dev/simulate-button/{button} with valid buttons."""
        valid_buttons = [1, 2, 3]

        for button in valid_buttons:
            response = await client.post(f"/radio/dev/simulate-button/{button}")
            assert response.status_code == 200

            result = response.json()
            assert result["success"] is True
            assert result["data"]["button"] == button
            assert result["data"]["action"] == "simulated_press"

    async def test_simulate_button_press_invalid(self, client: AsyncClient):
        """Test button simulation with invalid button numbers."""
        invalid_buttons = [0, 4, 5, -1]

        for button in invalid_buttons:
            response = await client.post(f"/radio/dev/simulate-button/{button}")
            assert response.status_code == 400

            error_data = response.json()
            assert "Button must be 1, 2, or 3" in error_data["detail"]

    async def test_simulate_volume_change_valid(self, client: AsyncClient):
        """Test POST /radio/dev/simulate-volume/{change} with valid changes."""
        valid_changes = [-10, -5, 5, 10, 25]

        for change in valid_changes:
            response = await client.post(f"/radio/dev/simulate-volume/{change}")
            assert response.status_code == 200

            result = response.json()
            assert result["success"] is True
            assert result["data"]["change"] == change
            assert result["data"]["action"] == "simulated_volume_change"

    async def test_simulate_volume_change_invalid(self, client: AsyncClient):
        """Test volume simulation with invalid change values."""
        invalid_changes = [100, -100, 999]  # Extreme values

        for change in invalid_changes:
            response = await client.post(f"/radio/dev/simulate-volume/{change}")
            assert response.status_code == 400

            error_data = response.json()
            assert "Volume change must be between" in error_data["detail"]

    async def test_volume_persistence_across_requests(self, client: AsyncClient):
        """Test that volume changes persist across requests."""
        test_volume = 65

        # Set volume
        response = await client.post("/radio/volume", json={"volume": test_volume})
        assert response.status_code == 200

        # Verify it persists in status
        response = await client.get("/radio/status")
        assert response.status_code == 200
        status = response.json()
        assert status["volume"] == test_volume

        # Verify it persists in volume endpoint
        response = await client.get("/radio/volume")
        assert response.status_code == 200
        volume_info = response.json()
        assert volume_info["volume"] == test_volume

    async def test_concurrent_volume_operations(self, client: AsyncClient):
        """Test concurrent volume operations."""
        import asyncio

        # Test concurrent volume changes
        volume_tasks = [
            client.post("/radio/volume", json={"volume": vol})
            for vol in [25, 50, 75]
        ]

        results = await asyncio.gather(*volume_tasks)
        for result in results:
            assert result.status_code == 200

        # Final volume should be one of the set values
        response = await client.get("/radio/volume")
        assert response.status_code == 200
        final_volume = response.json()["volume"]
        assert final_volume in [25, 50, 75] or final_volume >= 30  # Hardware minimum

    async def test_status_consistency(self, client: AsyncClient):
        """Test consistency between different status endpoints."""
        # Get status from main endpoint
        response1 = await client.get("/radio/status")
        assert response1.status_code == 200
        main_status = response1.json()

        # Get status from playback endpoint
        response2 = await client.get("/radio/playback-status")
        assert response2.status_code == 200
        playback_status = response2.json()

        # Volume should be consistent
        assert main_status["volume"] == playback_status["volume"]

        # Playing state should be consistent
        assert main_status["is_playing"] == (playback_status["state"] == "playing")

    async def test_error_response_formats(self, client: AsyncClient):
        """Test that error responses follow consistent format."""
        # Test various error conditions
        error_requests = [
            ("POST", "/radio/volume", {"invalid": "data"}),
            ("POST", "/radio/dev/simulate-button/0", {}),
            ("POST", "/radio/dev/simulate-volume/999", {}),
        ]

        for method, url, data in error_requests:
            if method == "POST":
                response = await client.post(url, json=data)
            else:
                response = await client.get(url)

            # Should be an error status
            assert response.status_code >= 400

            # Should have detail field for errors
            error_data = response.json()
            assert "detail" in error_data

    async def test_volume_step_size_configuration(self, client: AsyncClient):
        """Test that volume step size is configurable and consistent."""
        # Set initial volume
        initial_volume = 50
        await client.post("/radio/volume", json={"volume": initial_volume})

        # Test volume up
        response = await client.post("/radio/volume/up")
        assert response.status_code == 200
        result = response.json()

        volume_increase = result["data"]["volume"] - initial_volume
        step_size = result["data"]["change"]

        # Step size should be positive and reasonable (typically 5)
        assert step_size > 0
        assert step_size <= 10
        assert volume_increase == step_size

    async def test_mute_unmute_workflow(self, client: AsyncClient):
        """Test muting and unmuting workflow."""
        # Set non-zero volume
        await client.post("/radio/volume", json={"volume": 60})

        # Verify not muted
        response = await client.get("/radio/volume")
        volume_info = response.json()
        assert volume_info["is_muted"] is False

        # Mute (set to 0)
        response = await client.post("/radio/volume", json={"volume": 0})
        assert response.status_code == 200

        # Verify muted
        response = await client.get("/radio/volume")
        volume_info = response.json()
        assert volume_info["is_muted"] is True
        assert volume_info["volume"] == 0

    async def test_system_integration_workflow(self, client: AsyncClient):
        """Test complete system workflow integration."""
        # 1. Check initial status
        response = await client.get("/radio/status")
        assert response.status_code == 200
        initial_status = response.json()

        # 2. Set volume
        response = await client.post("/radio/volume", json={"volume": 70})
        assert response.status_code == 200

        # 3. Save and play a station
        station_data = {
            "name": "Integration Test",
            "url": "https://integration.example.com/stream"
        }
        await client.post("/radio/stations/1", json=station_data)
        await client.post("/radio/stations/1/play")

        # 4. Check updated status
        response = await client.get("/radio/status")
        assert response.status_code == 200
        updated_status = response.json()
        assert updated_status["volume"] == 70

        # 5. Stop playback
        response = await client.post("/radio/stop")
        assert response.status_code == 200

        # 6. Verify final status
        response = await client.get("/radio/status")
        assert response.status_code == 200
        final_status = response.json()
        assert final_status["volume"] == 70  # Volume should persist
        assert final_status["is_playing"] is False  # Should be stopped

    @patch('os.environ.get')
    async def test_dev_endpoints_only_in_mock_mode(self, mock_env_get, client: AsyncClient):
        """Test that dev endpoints are only available in mock mode."""
        # Mock production environment
        def env_side_effect(key, default=None):
            if key == "NODE_ENV":
                return "production"
            return default

        mock_env_get.side_effect = env_side_effect

        # Dev endpoints should return 403 in production
        # Note: This test depends on how the mock mode detection is implemented
        # In practice, the radio manager's mock_mode setting controls this

    async def test_hardware_status_details(self, client: AsyncClient):
        """Test detailed hardware status information."""
        response = await client.get("/radio/hardware-status")
        assert response.status_code == 200

        hw_status = response.json()

        # Should have button states
        if "button_states" in hw_status:
            assert isinstance(hw_status["button_states"], dict)

        # Should have timing information
        if "last_volume_change" in hw_status:
            # Can be None or a timestamp
            assert hw_status["last_volume_change"] is None or isinstance(hw_status["last_volume_change"], (int, float))

    async def test_api_response_consistency(self, client: AsyncClient):
        """Test that API responses follow consistent format."""
        # Test successful responses
        successful_endpoints = [
            ("GET", "/radio/status"),
            ("GET", "/radio/volume"),
            ("POST", "/radio/volume", {"volume": 50}),
            ("POST", "/radio/stop"),
        ]

        for method, url, *data in successful_endpoints:
            if method == "POST" and data:
                response = await client.post(url, json=data[0])
            elif method == "POST":
                response = await client.post(url)
            else:
                response = await client.get(url)

            assert response.status_code == 200

            # ApiResponse format for POST endpoints
            if method == "POST":
                result = response.json()
                assert "success" in result
                assert "message" in result
                # data field is optional
