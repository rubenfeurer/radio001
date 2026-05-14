"""
FastAPI Backend for Radio WiFi Configuration
Inspired by RaspiWiFi with minimal dependencies and clean architecture
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn

# Load radio.conf before anything reads os.getenv().
# In Docker the file is at /app/config/radio.conf (mounted volume).
# In dev it falls back to ../config/radio.conf relative to this file.
def _load_radio_conf():
    _candidates = [
        Path("/app/config/radio.conf"),
        Path(__file__).parent.parent / "config" / "radio.conf",
    ]
    for _p in _candidates:
        if _p.exists():
            try:
                with open(_p) as _f:
                    for _line in _f:
                        _line = _line.strip()
                        if not _line or _line.startswith("#") or "=" not in _line:
                            continue
                        _key, _, _val = _line.partition("=")
                        _key = _key.strip()
                        _val = _val.split("#")[0].strip()  # strip inline comments
                        if _key and _key not in os.environ:
                            os.environ[_key] = _val
                print(f"Loaded config from {_p}")
            except Exception as _e:
                print(f"WARNING: Could not load {_p}: {_e}")
            return

_load_radio_conf()

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
from fastapi.staticfiles import StaticFiles

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
    DEFAULT_VOLUME: int = int(os.getenv("DEFAULT_VOLUME", "50"))
    MIN_VOLUME: int = int(os.getenv("MIN_VOLUME", "30"))
    MAX_VOLUME: int = int(os.getenv("MAX_VOLUME", "100"))
    NOTIFICATION_VOLUME: int = int(os.getenv("NOTIFICATION_VOLUME", "40"))

    # Hardware Settings (GPIO pins)
    BUTTON_PIN_1: int = int(os.getenv("BUTTON_PIN_1", "17"))
    BUTTON_PIN_2: int = int(os.getenv("BUTTON_PIN_2", "16"))
    BUTTON_PIN_3: int = int(os.getenv("BUTTON_PIN_3", "26"))

    # Rotary Encoder Settings
    ROTARY_CLK: int = int(os.getenv("ROTARY_CLK", "11"))
    ROTARY_DT: int = int(os.getenv("ROTARY_DT", "9"))
    ROTARY_SW: int = int(os.getenv("ROTARY_SW", "10"))
    ROTARY_CLOCKWISE_INCREASES: bool = os.getenv("ROTARY_CLOCKWISE_INCREASES", "true").lower() == "true"
    ROTARY_VOLUME_STEP: int = int(os.getenv("ROTARY_VOLUME_STEP", "5"))
    ROTARY_DEBOUNCE: float = float(os.getenv("ROTARY_DEBOUNCE", "0.05"))

    # Button Press Settings (in seconds)
    LONG_PRESS_DURATION: float = float(os.getenv("LONG_PRESS_DURATION", "2.0"))
    TRIPLE_PRESS_INTERVAL: float = float(os.getenv("TRIPLE_PRESS_INTERVAL", "0.5"))

    # ALSA mixer control
    ALSA_MIXER_CONTROL: str = os.getenv("ALSA_MIXER_CONTROL", "PCM")

    # Default station slots
    DEFAULT_STATION_1_NAME: str = os.getenv("DEFAULT_STATION_1_NAME", "SRF 3")
    DEFAULT_STATION_1_URL: str = os.getenv("DEFAULT_STATION_1_URL", "https://stream.srg-ssr.ch/m/srf3/mp3_128")
    DEFAULT_STATION_2_NAME: str = os.getenv("DEFAULT_STATION_2_NAME", "Radio Swiss Jazz")
    DEFAULT_STATION_2_URL: str = os.getenv("DEFAULT_STATION_2_URL", "https://stream.srg-ssr.ch/m/rsj/mp3_128")
    DEFAULT_STATION_3_NAME: str = os.getenv("DEFAULT_STATION_3_NAME", "Radio Swiss Classic")
    DEFAULT_STATION_3_URL: str = os.getenv("DEFAULT_STATION_3_URL", "https://stream.srg-ssr.ch/m/rsc_de/mp3_128")

    # Audio & Data Paths
    DATA_DIR = Path("data")
    SOUNDS_DIR = Path("assets/sounds")
    STATIONS_FILE = DATA_DIR / "stations.json"
    PREFERENCES_FILE = DATA_DIR / "preferences.json"
    RADIO_STATE_FILE = Path(os.getenv("RADIO_STATE_FILE", "data/radio_state.json"))

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
from core.models import ApiResponse


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
            config=Config, mock_mode=Config.IS_DEVELOPMENT, wifi_manager=wifi_manager
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
app.include_router(system_router, prefix="/api/system", tags=["System"])
app.include_router(stations_router, prefix="/api/radio/stations", tags=["Radio Stations"])
app.include_router(radio_router, prefix="/api/radio", tags=["Radio Control"])
app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])


app.include_router(wifi_router, prefix="/api/wifi", tags=["WiFi"])

# =============================================================================
# API Routes
# =============================================================================


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


# Serve frontend static files — mounted last so API routes take priority
_static_dir = Path("/app/static")
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")


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
