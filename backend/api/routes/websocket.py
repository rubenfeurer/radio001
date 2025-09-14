"""
WebSocket API Routes for Real-time Radio Communication.

This module provides WebSocket endpoints for real-time communication between
the radio system backend and frontend clients. It handles:
- Real-time status updates (volume, playback state, station changes)
- Hardware event broadcasting (button presses, volume changes)
- System notifications and error messages
- Connection management for multiple clients
"""

import asyncio
import json
import logging
import time
from typing import Dict, Set, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi.websockets import WebSocketState

from ...core.models import WSMessage, SystemStatus, PlaybackStatus
from ...core.radio_manager import RadioManager

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.

    Handles multiple client connections and provides methods for broadcasting
    messages to all connected clients or specific connection groups.
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Set[WebSocket] = set()
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_info: Optional[Dict[str, Any]] = None):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            client_info: Optional client information (user agent, IP, etc.)
        """
        await websocket.accept()

        async with self._lock:
            self.active_connections.add(websocket)
            self.connection_info[websocket] = {
                "connected_at": time.time(),
                "client_info": client_info or {},
                "message_count": 0
            }

        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """
        Remove and cleanup a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
        """
        async with self._lock:
            self.active_connections.discard(websocket)
            self.connection_info.pop(websocket, None)

        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        Send a message to a specific WebSocket connection.

        Args:
            message: Message data to send
            websocket: Target WebSocket connection
        """
        if websocket in self.active_connections:
            try:
                message_with_timestamp = {
                    **message,
                    "timestamp": time.time()
                }
                await websocket.send_text(json.dumps(message_with_timestamp))

                # Update message count
                if websocket in self.connection_info:
                    self.connection_info[websocket]["message_count"] += 1

            except Exception as e:
                logger.error(f"Error sending personal message: {e}")
                await self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected WebSocket clients.

        Args:
            message: Message data to broadcast
        """
        if not self.active_connections:
            return

        message_with_timestamp = {
            **message,
            "timestamp": time.time()
        }

        message_text = json.dumps(message_with_timestamp)
        disconnected_connections = set()

        # Send to all connections
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message_text)

                # Update message count
                if connection in self.connection_info:
                    self.connection_info[connection]["message_count"] += 1

            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected_connections.add(connection)

        # Clean up failed connections
        async with self._lock:
            for connection in disconnected_connections:
                self.active_connections.discard(connection)
                self.connection_info.pop(connection, None)

        if disconnected_connections:
            logger.info(f"Removed {len(disconnected_connections)} failed connections")

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics for monitoring."""
        total_messages = sum(
            info.get("message_count", 0)
            for info in self.connection_info.values()
        )

        return {
            "active_connections": len(self.active_connections),
            "total_messages_sent": total_messages,
            "connections_info": [
                {
                    "connected_duration": time.time() - info.get("connected_at", 0),
                    "message_count": info.get("message_count", 0),
                    "client_info": info.get("client_info", {})
                }
                for info in self.connection_info.values()
            ]
        }


# Global connection manager instance
manager = ConnectionManager()


# WebSocket status update callback for RadioManager
async def websocket_status_callback(update_type: str, data: Optional[Dict[str, Any]] = None):
    """
    Callback function for RadioManager to broadcast status updates via WebSocket.

    Args:
        update_type: Type of update (volume_update, station_change, etc.)
        data: Optional data payload for the update
    """
    try:
        message = {
            "type": update_type,
            "data": data or {}
        }
        await manager.broadcast(message)
        logger.debug(f"Broadcasted WebSocket update: {update_type}")
    except Exception as e:
        logger.error(f"Error in WebSocket status callback: {e}", exc_info=True)


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for radio system communication.

    Handles:
    - Initial connection and authentication
    - Real-time message exchange
    - Status updates and notifications
    - Connection cleanup on disconnect
    """
    client_host = websocket.client.host if websocket.client else "unknown"
    logger.info(f"WebSocket connection attempt from {client_host}")

    try:
        # Accept connection
        await manager.connect(websocket, {"host": client_host})

        # Send initial system status
        try:
            radio_manager = RadioManager.get_instance()
            initial_status = await radio_manager.get_status()

            await manager.send_personal_message({
                "type": "system_status",
                "data": initial_status.dict()
            }, websocket)
        except Exception as e:
            logger.error(f"Error sending initial status: {e}")

        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()

                try:
                    message = json.loads(data)
                    await handle_client_message(websocket, message)
                except json.JSONDecodeError:
                    await manager.send_personal_message({
                        "type": "error",
                        "data": {"message": "Invalid JSON format"}
                    }, websocket)
                except Exception as e:
                    logger.error(f"Error handling client message: {e}")
                    await manager.send_personal_message({
                        "type": "error",
                        "data": {"message": "Error processing message"}
                    }, websocket)

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket communication error: {e}")
                break

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        await manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, message: Dict[str, Any]):
    """
    Handle incoming messages from WebSocket clients.

    Args:
        websocket: The WebSocket connection
        message: Parsed message data from client
    """
    message_type = message.get("type")
    message_data = message.get("data", {})

    logger.debug(f"Received WebSocket message: {message_type}")

    try:
        radio_manager = RadioManager.get_instance()

        if message_type == "get_status":
            # Send current system status
            status = await radio_manager.get_status()
            await manager.send_personal_message({
                "type": "system_status",
                "data": status.dict()
            }, websocket)

        elif message_type == "get_stations":
            # Send all stations
            stations = await radio_manager._station_manager.get_all_stations()
            await manager.send_personal_message({
                "type": "stations_update",
                "data": {"stations": {k: v.dict() if v else None for k, v in stations.items()}}
            }, websocket)

        elif message_type == "get_hardware_status":
            # Send hardware status
            hw_status = radio_manager.get_hardware_status()
            await manager.send_personal_message({
                "type": "hardware_status",
                "data": hw_status
            }, websocket)

        elif message_type == "ping":
            # Respond to ping with pong
            await manager.send_personal_message({
                "type": "pong",
                "data": {"timestamp": time.time()}
            }, websocket)

        elif message_type == "subscribe":
            # Handle subscription requests (for future use)
            subscription_types = message_data.get("types", [])
            await manager.send_personal_message({
                "type": "subscription_confirmed",
                "data": {"subscribed_to": subscription_types}
            }, websocket)

        else:
            # Unknown message type
            await manager.send_personal_message({
                "type": "error",
                "data": {"message": f"Unknown message type: {message_type}"}
            }, websocket)

    except Exception as e:
        logger.error(f"Error handling message type '{message_type}': {e}")
        await manager.send_personal_message({
            "type": "error",
            "data": {"message": f"Error processing {message_type} request"}
        }, websocket)


@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.

    Returns:
        Dict: Connection statistics and info
    """
    return manager.get_connection_stats()


# Helper function to set up RadioManager with WebSocket callback
async def setup_radio_manager_with_websocket(config, mock_mode: bool = True):
    """
    Create RadioManager instance with WebSocket status callback.

    Args:
        config: Application configuration
        mock_mode: Whether to run in mock mode

    Returns:
        RadioManager: Configured radio manager instance
    """
    return await RadioManager.create_instance(
        config=config,
        status_update_callback=websocket_status_callback,
        mock_mode=mock_mode
    )


# Export the callback for use in main application
__all__ = ["router", "websocket_status_callback", "manager", "setup_radio_manager_with_websocket"]
