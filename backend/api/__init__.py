"""
API routes package for radio functionality.

This package contains FastAPI route definitions for:
- stations.py: Station management endpoints (CRUD operations)
- radio.py: System control endpoints (volume, playback, status)
- websocket.py: Real-time communication for radio events

All routes are designed to integrate seamlessly with the existing WiFi API.
"""

from .stations import router as stations_router
from .radio import router as radio_router
from .websocket import router as websocket_router

__all__ = [
    "stations_router",
    "radio_router",
    "websocket_router"
]
