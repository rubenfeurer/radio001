"""
Radio API routes package.

This package contains all FastAPI route definitions for radio functionality:
- stations.py: Station management (CRUD, playback control)
- radio.py: System control (volume, status, global controls)
- websocket.py: Real-time communication and event broadcasting

Routes are designed to integrate with existing WiFi API endpoints.
"""

__all__ = [
    "stations",
    "radio",
    "websocket"
]
