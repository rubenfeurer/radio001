"""
FastAPI Backend for Radio WiFi Configuration
Inspired by RaspiWiFi with minimal dependencies and clean architecture
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
from api.routes.radio import router as radio_router

# Radio system imports
from api.routes.stations import router as stations_router
from api.routes.system import router as system_router
from api.routes.system import set_system_wifi_manager
from api.routes.websocket import router as websocket_router
from api.routes.websocket import (
    setup_radio_manager_with_websocket,
    start_metrics_broadcast,
    stop_metrics_broadcast,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# =============================================================================
# Configuration
# =============================================================================


class Config:
    """Application configuration - inspired by RaspiWiFi's simple approach"""

    # Paths (following RaspiWiFi convention)
    RASPIWIFI_DIR = (
        Path("/tmp/radio")
        if os.getenv("NODE_ENV") == "development"
        else Path("/etc/raspiwifi")
    )
    config_file = RASPIWIFI_DIR / "raspiwifi.conf"
    HOST_MODE_FILE = RASPIWIFI_DIR / "host_mode"
    # Network interfaces
    WIFI_INTERFACE = os.getenv("WIFI_INTERFACE", "wlan0")

    # Development mode
    IS_DEVELOPMENT = os.getenv("NODE_ENV", "production") == "development"

    # Server settings
    HOST = "0.0.0.0"
    PORT = int(os.getenv("API_PORT", "8000"))

    # Radio Settings
    DEFAULT_VOLUME: int = 50
    MIN_VOLUME: int = 30
    MAX_VOLUME: int = 100
    NOTIFICATION_VOLUME: int = 40

    # Hardware Settings (GPIO pins)
    BUTTON_PIN_1: int = 17  # GPIO17 (Pin 11) - Station 1
    BUTTON_PIN_2: int = 16  # GPIO16 (Pin 36) - Station 2
    BUTTON_PIN_3: int = 26  # GPIO26 (Pin 37) - Station 3

    # Rotary Encoder Settings
    ROTARY_CLK: int = 11  # GPIO11 (Pin 23) - Clock
    ROTARY_DT: int = 9  # GPIO9  (Pin 21) - Data
    ROTARY_SW: int = 10  # GPIO10 (Pin 19) - Switch/Button
    ROTARY_CLOCKWISE_INCREASES: bool = True  # Volume direction
    ROTARY_VOLUME_STEP: int = 5  # Volume change per step

    # Button Press Settings (in seconds)
    LONG_PRESS_DURATION: float = 3.0
    TRIPLE_PRESS_INTERVAL: float = 0.5

    # Audio & Data Paths
    DATA_DIR = Path("data")
    SOUNDS_DIR = Path("assets/sounds")
    STATIONS_FILE = DATA_DIR / "stations.json"
    PREFERENCES_FILE = DATA_DIR / "preferences.json"

    # Ensure paths exist
    @classmethod
    def ensure_paths(cls):
        """Create necessary directories for the application"""
        cls.RASPIWIFI_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
        # Additional path creation for logs, etc.


# WiFi module imports
from api.routes.wifi import router as wifi_router
from api.routes.wifi import set_wifi_manager
from core import WiFiManager


# Standard API response model
class ApiResponse(BaseModel):
    """Standard API response"""

    success: bool
    message: str
    data: Any = None


# =============================================================================
# FastAPI Application
# =============================================================================

# Global radio manager instance
radio_manager = None
wifi_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with radio and WiFi system initialization"""
    global radio_manager, wifi_manager

    # Startup
    print("Radio WiFi Backend starting...")
    Config.ensure_paths()
    if Config.IS_DEVELOPMENT:
        print("Running in development mode")

    # Initialize WiFi manager
    try:
        print("Initializing WiFi manager...")
        wifi_manager = WiFiManager(
            interface=Config.WIFI_INTERFACE,
            host_mode_file=Config.HOST_MODE_FILE,
            development_mode=Config.IS_DEVELOPMENT,
            hotspot_ssid=os.getenv("HOTSPOT_SSID", "Radio-Setup"),
            hotspot_password=os.getenv("HOTSPOT_PASSWORD", "Configure123!"),
            hotspot_ip=os.getenv("HOTSPOT_IP", "192.168.4.1"),
        )
        set_wifi_manager(wifi_manager)
        set_system_wifi_manager(wifi_manager)
        print("WiFi manager initialized successfully")
    except Exception as e:
        print(f"ERROR: Error initializing WiFi manager: {e}")
        print("WARNING: Continuing without WiFi functionality")

    # Initialize radio system
    try:
        print("Initializing radio system...")
        radio_manager = await setup_radio_manager_with_websocket(
            config=Config, mock_mode=Config.IS_DEVELOPMENT
        )
        print("Radio system initialized successfully")
    except Exception as e:
        print(f"ERROR: Error initializing radio system: {e}")
        print("WARNING: Continuing without radio functionality")

    # Start system metrics broadcast
    try:
        await start_metrics_broadcast()
        print("System metrics broadcast started")
    except Exception as e:
        print(f"ERROR: Failed to start metrics broadcast: {e}")

    yield

    # Shutdown
    print("Radio WiFi Backend shutting down...")

    # Stop system metrics broadcast
    try:
        await stop_metrics_broadcast()
        print("System metrics broadcast stopped")
    except Exception as e:
        print(f"Error stopping metrics broadcast: {e}")

    if radio_manager:
        try:
            await radio_manager.shutdown()
            print("Radio system shutdown complete")
        except Exception as e:
            print(f"Error shutting down radio system: {e}")


app = FastAPI(
    title="Radio WiFi Configuration API",
    description="Unified WiFi configuration and internet radio system with 3-slot station management",
    version="2.0.0",
    lifespan=lifespan,
)

# Startup configuration moved to lifespan context manager above

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"]
    if Config.IS_DEVELOPMENT
    else ["http://radio.local", "http://radio.local:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(system_router, prefix="/system", tags=["System"])
app.include_router(stations_router, prefix="/radio/stations", tags=["Radio Stations"])
app.include_router(radio_router, prefix="/radio", tags=["Radio Control"])
app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])


app.include_router(wifi_router, prefix="/wifi", tags=["WiFi"])

# =============================================================================
# API Routes
# =============================================================================


@app.get("/", response_model=ApiResponse, tags=["General"])
async def root():
    """Root endpoint"""
    return ApiResponse(
        success=True,
        message="Radio WiFi Configuration API",
        data={
            "version": "2.0.0",
            "status": "running",
            "features": [
                "wifi_management",
                "radio_streaming",
                "3_slot_stations",
                "hardware_controls",
            ],
        },
    )


@app.get("/health", response_model=ApiResponse, tags=["General"])
async def health_check():
    """Health check endpoint with additional diagnostic information"""
    try:
        # Add some basic system checks for development
        system_info = {
            "mode": "development" if Config.IS_DEVELOPMENT else "production",
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "config_dir_exists": Config.RASPIWIFI_DIR.exists(),
            "wifi_interface": Config.WIFI_INTERFACE,
            "data_dir_exists": Config.DATA_DIR.exists(),
            "sounds_dir_exists": Config.SOUNDS_DIR.exists(),
        }

        # Add radio system status if available
        if radio_manager:
            try:
                radio_status = await radio_manager.get_status()
                system_info["radio_system"] = {
                    "initialized": True,
                    "volume": radio_status.volume,
                    "is_playing": radio_status.is_playing,
                    "current_station": radio_status.current_station,
                }
            except Exception as e:
                system_info["radio_system"] = {"initialized": False, "error": str(e)}
        else:
            system_info["radio_system"] = {"initialized": False}

        return ApiResponse(success=True, message="Service healthy", data=system_info)
    except Exception as e:
        return ApiResponse(
            success=False, message=f"Health check failed: {str(e)}", data=None
        )


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    # Check if running in development

    reload = "--reload" in sys.argv or Config.IS_DEVELOPMENT

    print(f"Starting Radio WiFi Backend on {Config.HOST}:{Config.PORT}")
    print(f"WiFi Interface: {Config.WIFI_INTERFACE}")
    print(f"Development Mode: {Config.IS_DEVELOPMENT}")
    print(f"Radio Features: Volume Control, 3-Slot Stations, Hardware Integration")

    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=reload,
        log_level="info" if not Config.IS_DEVELOPMENT else "debug",
    )
