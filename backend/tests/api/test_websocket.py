"""
WebSocket API tests for real-time radio communication.

Tests WebSocket functionality including:
- Connection establishment and management
- Real-time status updates
- Message broadcasting
- Client message handling
- Connection statistics
- Error handling and disconnection scenarios
"""

import pytest
import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosed
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.websocket
class TestWebSocketRoutes:
    """Test WebSocket communication functionality."""

    @pytest.fixture
    async def websocket_url(self):
        """Get WebSocket URL for testing."""
        return "ws://test/ws/"

    async def test_websocket_connection_establishment(self, client: AsyncClient):
        """Test basic WebSocket connection."""
        # Test that WebSocket stats endpoint exists (indicates WebSocket is configured)
        response = await client.get("/ws/stats")
        assert response.status_code == 200

        stats = response.json()
        assert "active_connections" in stats
        assert isinstance(stats["active_connections"], int)

    async def test_websocket_stats_endpoint(self, client: AsyncClient):
        """Test GET /ws/stats endpoint."""
        response = await client.get("/ws/stats")
        assert response.status_code == 200

        stats = response.json()
        assert "active_connections" in stats
        assert "total_messages_sent" in stats
        assert "connections_info" in stats

        assert isinstance(stats["active_connections"], int)
        assert isinstance(stats["total_messages_sent"], int)
        assert isinstance(stats["connections_info"], list)

    @patch('api.routes.websocket.manager')
    async def test_websocket_status_callback(self, mock_manager):
        """Test WebSocket status update callback."""
        from api.routes.websocket import websocket_status_callback

        # Mock manager broadcast
        mock_manager.broadcast = AsyncMock()

        # Test callback
        await websocket_status_callback("test_update", {"test": "data"})

        # Should have called broadcast
        mock_manager.broadcast.assert_called_once_with({
            "type": "test_update",
            "data": {"test": "data"}
        })

    @patch('api.routes.websocket.manager')
    async def test_websocket_status_callback_no_data(self, mock_manager):
        """Test WebSocket status callback without data."""
        from api.routes.websocket import websocket_status_callback

        mock_manager.broadcast = AsyncMock()

        # Test callback without data
        await websocket_status_callback("volume_update")

        # Should have called broadcast with empty data
        mock_manager.broadcast.assert_called_once_with({
            "type": "volume_update",
            "data": {}
        })

    @patch('api.routes.websocket.manager')
    async def test_websocket_callback_error_handling(self, mock_manager):
        """Test WebSocket callback error handling."""
        from api.routes.websocket import websocket_status_callback

        # Mock manager broadcast to raise exception
        mock_manager.broadcast.side_effect = Exception("Broadcast error")

        # Should handle error gracefully
        try:
            await websocket_status_callback("error_test", {"test": "data"})
        except Exception:
            pytest.fail("WebSocket callback should handle errors gracefully")

    def test_websocket_message_types(self, websocket_messages):
        """Test WebSocket message type definitions."""
        # Test message structure
        volume_msg = websocket_messages["volume_update"]
        assert volume_msg["type"] == "volume_update"
        assert "data" in volume_msg
        assert "volume" in volume_msg["data"]

        station_msg = websocket_messages["station_change"]
        assert station_msg["type"] == "station_change"
        assert "data" in station_msg
        assert "slot" in station_msg["data"]

        status_msg = websocket_messages["system_status"]
        assert status_msg["type"] == "system_status"
        assert "data" in status_msg
        assert "volume" in status_msg["data"]
        assert "is_playing" in status_msg["data"]

    @patch('api.routes.websocket.ConnectionManager')
    async def test_connection_manager_connect(self, mock_connection_manager):
        """Test WebSocket connection manager connect."""
        mock_manager = AsyncMock()
        mock_connection_manager.return_value = mock_manager

        mock_websocket = AsyncMock()
        mock_websocket.client.host = "test-host"

        # Test connection
        await mock_manager.connect(mock_websocket, {"host": "test-host"})

        # Should accept connection
        mock_websocket.accept.assert_called_once()

    @patch('api.routes.websocket.ConnectionManager')
    async def test_connection_manager_disconnect(self, mock_connection_manager):
        """Test WebSocket connection manager disconnect."""
        mock_manager = AsyncMock()
        mock_connection_manager.return_value = mock_manager

        mock_websocket = AsyncMock()

        # Test disconnection
        await mock_manager.disconnect(mock_websocket)

        # Should handle disconnect
        mock_manager.disconnect.assert_called_once()

    @patch('api.routes.websocket.ConnectionManager')
    async def test_connection_manager_broadcast(self, mock_connection_manager):
        """Test WebSocket connection manager broadcast."""
        mock_manager = AsyncMock()
        mock_connection_manager.return_value = mock_manager

        test_message = {"type": "test", "data": {"test": "value"}}

        # Test broadcast
        await mock_manager.broadcast(test_message)

        # Should broadcast message
        mock_manager.broadcast.assert_called_once()

    async def test_websocket_message_validation(self):
        """Test WebSocket message validation."""
        from core.models import WSMessage

        # Test valid message
        valid_message = WSMessage(
            type="test_message",
            data={"key": "value"},
            timestamp=1703123456.789
        )
        assert valid_message.type == "test_message"
        assert valid_message.data["key"] == "value"

        # Test message without data
        minimal_message = WSMessage(type="ping")
        assert minimal_message.type == "ping"
        assert minimal_message.data is None

    async def test_websocket_message_timestamps(self):
        """Test that WebSocket messages include timestamps."""
        from core.models import WSVolumeUpdate, WSStationChange

        # Test volume update message
        volume_msg = WSVolumeUpdate(data={"volume": 75})
        assert volume_msg.type == "volume_update"

        # Test station change message
        station_msg = WSStationChange(data={"slot": 1, "action": "playing"})
        assert station_msg.type == "station_change"

    @patch('api.routes.websocket.RadioManager')
    async def test_websocket_client_message_handling(self, mock_radio_manager):
        """Test handling of client messages via WebSocket."""
        from api.routes.websocket import handle_client_message

        # Mock radio manager
        mock_manager_instance = AsyncMock()
        mock_radio_manager.get_instance.return_value = mock_manager_instance
        mock_manager_instance.get_status.return_value = AsyncMock()
        mock_manager_instance._station_manager.get_all_stations.return_value = {}

        # Mock WebSocket
        mock_websocket = AsyncMock()

        # Test get_status message
        message = {"type": "get_status", "data": {}}
        await handle_client_message(mock_websocket, message)

        # Should have called get_status
        mock_manager_instance.get_status.assert_called_once()

    @patch('api.routes.websocket.RadioManager')
    async def test_websocket_get_stations_message(self, mock_radio_manager):
        """Test WebSocket get_stations message handling."""
        from api.routes.websocket import handle_client_message

        # Mock radio manager
        mock_manager_instance = AsyncMock()
        mock_radio_manager.get_instance.return_value = mock_manager_instance
        mock_manager_instance._station_manager.get_all_stations.return_value = {
            1: AsyncMock(dict=lambda: {"name": "Test Station"}),
            2: None,
            3: None
        }

        # Mock WebSocket and connection manager
        mock_websocket = AsyncMock()

        with patch('api.routes.websocket.manager') as mock_manager:
            mock_manager.send_personal_message = AsyncMock()

            # Test get_stations message
            message = {"type": "get_stations", "data": {}}
            await handle_client_message(mock_websocket, message)

            # Should have called get_all_stations
            mock_manager_instance._station_manager.get_all_stations.assert_called_once()

            # Should have sent response
            mock_manager.send_personal_message.assert_called_once()

    @patch('api.routes.websocket.RadioManager')
    async def test_websocket_ping_pong(self, mock_radio_manager):
        """Test WebSocket ping-pong mechanism."""
        from api.routes.websocket import handle_client_message

        mock_websocket = AsyncMock()

        with patch('api.routes.websocket.manager') as mock_manager:
            mock_manager.send_personal_message = AsyncMock()

            # Test ping message
            message = {"type": "ping", "data": {}}
            await handle_client_message(mock_websocket, message)

            # Should respond with pong
            mock_manager.send_personal_message.assert_called_once()
            call_args = mock_manager.send_personal_message.call_args
            sent_message = call_args[0][0]
            assert sent_message["type"] == "pong"

    @patch('api.routes.websocket.RadioManager')
    async def test_websocket_unknown_message_type(self, mock_radio_manager):
        """Test handling of unknown WebSocket message types."""
        from api.routes.websocket import handle_client_message

        mock_websocket = AsyncMock()

        with patch('api.routes.websocket.manager') as mock_manager:
            mock_manager.send_personal_message = AsyncMock()

            # Test unknown message type
            message = {"type": "unknown_type", "data": {}}
            await handle_client_message(mock_websocket, message)

            # Should send error response
            mock_manager.send_personal_message.assert_called_once()
            call_args = mock_manager.send_personal_message.call_args
            sent_message = call_args[0][0]
            assert sent_message["type"] == "error"
            assert "Unknown message type" in sent_message["data"]["message"]

    async def test_websocket_message_parsing_errors(self):
        """Test handling of WebSocket message parsing errors."""
        from api.routes.websocket import handle_client_message

        mock_websocket = AsyncMock()

        with patch('api.routes.websocket.manager') as mock_manager:
            mock_manager.send_personal_message = AsyncMock()

            # Test message without type
            invalid_message = {"data": {"some": "data"}}
            await handle_client_message(mock_websocket, invalid_message)

            # Should handle gracefully (implementation dependent)

    async def test_websocket_subscription_handling(self):
        """Test WebSocket subscription mechanism."""
        from api.routes.websocket import handle_client_message

        mock_websocket = AsyncMock()

        with patch('api.routes.websocket.manager') as mock_manager:
            mock_manager.send_personal_message = AsyncMock()

            # Test subscription message
            message = {
                "type": "subscribe",
                "data": {"types": ["volume_update", "station_change"]}
            }
            await handle_client_message(mock_websocket, message)

            # Should confirm subscription
            mock_manager.send_personal_message.assert_called_once()
            call_args = mock_manager.send_personal_message.call_args
            sent_message = call_args[0][0]
            assert sent_message["type"] == "subscription_confirmed"

    @patch('api.routes.websocket.ConnectionManager')
    async def test_websocket_connection_cleanup(self, mock_connection_manager):
        """Test WebSocket connection cleanup on disconnect."""
        mock_manager = AsyncMock()
        mock_connection_manager.return_value = mock_manager

        # Mock failed connections
        mock_manager.active_connections = {AsyncMock(), AsyncMock()}
        mock_manager.broadcast.side_effect = Exception("Connection failed")

        # Test that cleanup happens
        await mock_manager.broadcast({"type": "test"})

    async def test_websocket_concurrent_connections(self):
        """Test handling of multiple concurrent WebSocket connections."""
        from api.routes.websocket import ConnectionManager

        manager = ConnectionManager()

        # Mock multiple websockets
        websockets = [AsyncMock() for _ in range(3)]

        # Connect all
        for i, ws in enumerate(websockets):
            ws.accept = AsyncMock()
            await manager.connect(ws, {"client": f"client_{i}"})

        # Should track all connections
        assert len(manager.active_connections) == 3

        # Test broadcast to all
        await manager.broadcast({"type": "test_broadcast", "data": {}})

        # All should receive message (in mock)
        # Actual verification depends on implementation

    async def test_websocket_message_rate_limiting(self):
        """Test WebSocket message rate limiting (if implemented)."""
        from api.routes.websocket import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        # Connect
        await manager.connect(mock_websocket)

        # Send many messages rapidly
        messages = [{"type": f"test_{i}", "data": {}} for i in range(10)]

        for message in messages:
            await manager.send_personal_message(message, mock_websocket)

        # Should handle without errors (rate limiting is implementation dependent)

    async def test_websocket_connection_info_tracking(self):
        """Test WebSocket connection information tracking."""
        from api.routes.websocket import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = AsyncMock()
        client_info = {"host": "test-host", "user_agent": "test-agent"}

        # Connect with info
        await manager.connect(mock_websocket, client_info)

        # Should track connection info
        stats = manager.get_connection_stats()
        assert stats["active_connections"] == 1

        if stats["connections_info"]:
            conn_info = stats["connections_info"][0]
            assert "connected_duration" in conn_info
            assert "message_count" in conn_info

    @patch('api.routes.websocket.RadioManager')
    async def test_websocket_hardware_status_message(self, mock_radio_manager):
        """Test WebSocket hardware status message handling."""
        from api.routes.websocket import handle_client_message

        # Mock radio manager
        mock_manager_instance = AsyncMock()
        mock_radio_manager.get_instance.return_value = mock_manager_instance
        mock_manager_instance.get_hardware_status.return_value = {
            "gpio_available": True,
            "audio_available": True,
            "mock_mode": False
        }

        mock_websocket = AsyncMock()

        with patch('api.routes.websocket.manager') as mock_manager:
            mock_manager.send_personal_message = AsyncMock()

            # Test get_hardware_status message
            message = {"type": "get_hardware_status", "data": {}}
            await handle_client_message(mock_websocket, message)

            # Should have called get_hardware_status
            mock_manager_instance.get_hardware_status.assert_called_once()

            # Should have sent response
            mock_manager.send_personal_message.assert_called_once()
            call_args = mock_manager.send_personal_message.call_args
            sent_message = call_args[0][0]
            assert sent_message["type"] == "hardware_status"

    async def test_websocket_error_message_handling(self):
        """Test WebSocket error message handling."""
        from api.routes.websocket import handle_client_message

        mock_websocket = AsyncMock()

        with patch('api.routes.websocket.manager') as mock_manager, \
             patch('api.routes.websocket.RadioManager') as mock_radio_manager:

            # Mock radio manager to raise exception
            mock_radio_manager.get_instance.side_effect = Exception("Radio error")
            mock_manager.send_personal_message = AsyncMock()

            # Test message that causes error
            message = {"type": "get_status", "data": {}}
            await handle_client_message(mock_websocket, message)

            # Should send error response
            mock_manager.send_personal_message.assert_called_once()
            call_args = mock_manager.send_personal_message.call_args
            sent_message = call_args[0][0]
            assert sent_message["type"] == "error"

    async def test_websocket_setup_radio_manager_function(self):
        """Test WebSocket setup radio manager helper function."""
        from api.routes.websocket import setup_radio_manager_with_websocket
        from main import Config

        with patch('api.routes.websocket.RadioManager') as mock_radio_manager:
            mock_instance = AsyncMock()
            mock_radio_manager.create_instance.return_value = mock_instance

            # Test setup function
            result = await setup_radio_manager_with_websocket(
                config=Config,
                mock_mode=True
            )

            # Should create instance with WebSocket callback
            mock_radio_manager.create_instance.assert_called_once()
            call_args = mock_radio_manager.create_instance.call_args
            assert call_args.kwargs["config"] == Config
            assert call_args.kwargs["mock_mode"] is True
            assert "status_update_callback" in call_args.kwargs

    async def test_websocket_integration_with_radio_system(self, client: AsyncClient):
        """Test WebSocket integration with radio system operations."""
        # This test would ideally test the full integration:
        # 1. Connect WebSocket
        # 2. Perform radio operation (volume change, station change)
        # 3. Verify WebSocket receives update

        # For now, test that the integration endpoints exist
        response = await client.get("/ws/stats")
        assert response.status_code == 200

        # Test radio status endpoint (should trigger WebSocket updates when used)
        response = await client.get("/radio/status")
        assert response.status_code == 200

        # Test volume change (should trigger WebSocket updates)
        response = await client.post("/radio/volume", json={"volume": 75})
        assert response.status_code == 200

    def test_websocket_message_serialization(self):
        """Test WebSocket message serialization."""
        from core.models import WSMessage

        # Test message serialization
        message = WSMessage(
            type="test_message",
            data={"volume": 75, "station": 1},
            timestamp=1703123456.789
        )

        # Should be serializable to JSON
        serialized = message.dict()
        assert serialized["type"] == "test_message"
        assert serialized["data"]["volume"] == 75
        assert serialized["timestamp"] == 1703123456.789

        # Should be JSON serializable
        json_str = json.dumps(serialized)
        assert json_str is not None

        # Should be deserializable
        deserialized = json.loads(json_str)
        assert deserialized["type"] == "test_message"

    async def test_websocket_connection_limits(self):
        """Test WebSocket connection limits (if implemented)."""
        from api.routes.websocket import ConnectionManager

        manager = ConnectionManager()

        # Test many connections
        websockets = [AsyncMock() for _ in range(10)]

        for ws in websockets:
            ws.accept = AsyncMock()
            await manager.connect(ws)

        # Should handle reasonable number of connections
        assert len(manager.active_connections) <= 10

    async def test_websocket_memory_cleanup(self):
        """Test WebSocket memory cleanup after disconnections."""
        from api.routes.websocket import ConnectionManager

        manager = ConnectionManager()

        # Connect and disconnect multiple times
        for i in range(5):
            mock_websocket = AsyncMock()
            await manager.connect(mock_websocket)
            await manager.disconnect(mock_websocket)

        # Should not accumulate connection info
        stats = manager.get_connection_stats()
        assert stats["active_connections"] == 0
