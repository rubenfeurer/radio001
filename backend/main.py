"""
FastAPI Backend for Radio WiFi Configuration
Inspired by RaspiWiFi with minimal dependencies and clean architecture
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, List, Optional

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
from api.routes.websocket import router as websocket_router
from api.routes.websocket import (
    setup_radio_manager_with_websocket,
    start_metrics_broadcast,
    stop_metrics_broadcast,
)
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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
    WPA_SUPPLICANT_FILE = Path(
        "/tmp/wpa_supplicant.conf"
        if os.getenv("NODE_ENV") == "development"
        else "/etc/wpa_supplicant/wpa_supplicant.conf"
    )

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


# =============================================================================
# Data Models
# =============================================================================


class WiFiNetwork(BaseModel):
    """WiFi network model"""

    ssid: str
    signal: Optional[int] = None
    encryption: str = "Unknown"
    frequency: Optional[str] = None


class WiFiCredentials(BaseModel):
    """WiFi connection credentials"""

    ssid: str = Field(..., min_length=1, max_length=32)
    password: str = Field(default="", max_length=63)


class SystemStatus(BaseModel):
    """System status model"""

    mode: str  # "client" or "host"
    connected: bool
    ssid: Optional[str] = None
    ip_address: Optional[str] = None
    signal_strength: Optional[int] = None


class ApiResponse(BaseModel):
    """Standard API response"""

    success: bool
    message: str
    data: Optional[Any] = None


# =============================================================================
# WiFi Management (RaspiWiFi inspired)
# =============================================================================


class WiFiManager:
    """WiFi management class inspired by RaspiWiFi's approach"""

    @staticmethod
    def _parse_signal_strength(line: str) -> Optional[int]:
        """Parse signal strength from iwlist output line"""
        try:
            signal_part = line.split("Signal level=")[1].split()[0]
            if "dBm" in signal_part:
                signal = int(signal_part.replace("dBm", ""))
                # Convert dBm to percentage (rough approximation)
                return max(0, min(100, 2 * (signal + 100)))
        except (ValueError, IndexError):
            pass
        return None

    @staticmethod
    def _parse_encryption(line: str) -> str:
        """Parse encryption type from iwlist output line"""
        if "off" in line:
            return "Open"
        return "WPA"

    @staticmethod
    def _parse_frequency(line: str) -> Optional[str]:
        """Parse frequency from iwlist output line"""
        try:
            return line.split("Frequency:")[1].split()[0]
        except IndexError:
            return None

    @staticmethod
    def _parse_ssid(line: str) -> Optional[str]:
        """Parse SSID from iwlist output line"""
        ssid = line.split("ESSID:")[1].strip('"')
        if ssid and ssid != "":
            return ssid
        return None

    @staticmethod
    def _parse_iwlist_output(output: str) -> List[WiFiNetwork]:
        """Parse iwlist output into WiFiNetwork objects"""
        networks = []
        current_network = {}

        for line in output.split("\n"):
            line = line.strip()

            if "ESSID:" in line:
                ssid = WiFiManager._parse_ssid(line)
                if ssid:
                    current_network["ssid"] = ssid

            elif "Signal level=" in line:
                signal = WiFiManager._parse_signal_strength(line)
                if signal is not None:
                    current_network["signal"] = signal

            elif "Encryption key:" in line:
                current_network["encryption"] = WiFiManager._parse_encryption(line)

            elif "Frequency:" in line:
                freq = WiFiManager._parse_frequency(line)
                if freq:
                    current_network["frequency"] = freq

            # If we have a complete network, add it
            elif "ssid" in current_network and line.startswith("Cell"):
                if len(current_network) > 1:  # Has more than just SSID
                    networks.append(WiFiNetwork(**current_network))
                current_network = {}

        # Don't forget the last network
        if "ssid" in current_network and len(current_network) > 1:
            networks.append(WiFiNetwork(**current_network))

        return networks

    @staticmethod
    async def scan_networks() -> List[WiFiNetwork]:
        """Scan for available WiFi networks using iwlist (RaspiWiFi method)"""

        if Config.IS_DEVELOPMENT:
            # Return mock data for development
            return [
                WiFiNetwork(
                    ssid="HomeWiFi", signal=-45, encryption="WPA2", frequency="2.4GHz"
                ),
                WiFiNetwork(
                    ssid="GuestNetwork", signal=-60, encryption="Open", frequency="5GHz"
                ),
                WiFiNetwork(
                    ssid="NeighborWiFi",
                    signal=-75,
                    encryption="WPA3",
                    frequency="2.4GHz",
                ),
            ]

        try:
            # Use iwlist scan (same as RaspiWiFi)
            process = await asyncio.create_subprocess_exec(
                "iwlist",
                Config.WIFI_INTERFACE,
                "scan",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"iwlist scan failed: {stderr.decode()}")

            return WiFiManager._parse_iwlist_output(stdout.decode())

        except Exception as e:
            raise Exception(f"WiFi scan failed: {str(e)}")

    @staticmethod
    async def get_status() -> SystemStatus:
        """Get current WiFi status"""

        if Config.IS_DEVELOPMENT:
            return SystemStatus(
                mode="host",
                connected=False,
                ssid="Radio-Setup",
                ip_address="192.168.4.1",
            )

        try:
            # Check if in host mode (RaspiWiFi method)
            is_host_mode = Config.HOST_MODE_FILE.exists()

            if is_host_mode:
                return SystemStatus(
                    mode="host",
                    connected=True,
                    ssid="Radio-Setup",
                    ip_address="192.168.4.1",
                )

            # Check client connection using iwconfig (RaspiWiFi method)
            process = await asyncio.create_subprocess_exec(
                "iwconfig",
                Config.WIFI_INTERFACE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return SystemStatus(mode="client", connected=False)

            output = stdout.decode()

            # Parse iwconfig output
            connected = "Access Point: Not-Associated" not in output
            ssid = None

            if connected:
                for line in output.split("\n"):
                    if "ESSID:" in line:
                        ssid = line.split("ESSID:")[1].strip('"')
                        break

            return SystemStatus(mode="client", connected=connected, ssid=ssid)

        except Exception:
            return SystemStatus(mode="client", connected=False)

    @staticmethod
    async def connect_network(credentials: WiFiCredentials) -> bool:
        """Connect to WiFi network (RaspiWiFi method)"""

        if Config.IS_DEVELOPMENT:
            # Simulate connection in development
            logger.info(
                f"Development mode: Simulating WiFi connection to {credentials.ssid}"
            )
            await asyncio.sleep(1)
            return True

        try:
            logger.info(f"Creating wpa_supplicant.conf for {credentials.ssid}")

            # Create wpa_supplicant.conf (same as RaspiWiFi)
            wpa_config = [
                "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev",
                "update_config=1",
                "",
                "network={",
                f'    ssid="{credentials.ssid}"',
            ]

            if credentials.password:
                wpa_config.append(f'    psk="{credentials.password}"')
            else:
                wpa_config.append("    key_mgmt=NONE")

            wpa_config.append("}")

            # Write wpa_supplicant.conf
            temp_file = Path("/tmp/wpa_supplicant.conf.tmp")
            temp_file.write_text("\n".join(wpa_config))
            logger.debug(f"Wrote temporary config to {temp_file}")

            # Move to final location (requires root)
            process = await asyncio.create_subprocess_exec(
                "sudo",
                "mv",
                str(temp_file),
                str(Config.WPA_SUPPLICANT_FILE),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"Successfully wrote {Config.WPA_SUPPLICANT_FILE}")
                return True
            else:
                logger.error(f"Failed to move config file: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error writing WiFi credentials: {e}", exc_info=True)
            return False

    @staticmethod
    async def switch_to_client_mode():
        """Switch from host mode to client mode (RaspiWiFi-inspired method)"""

        if Config.IS_DEVELOPMENT:
            logger.info("Development mode: Skipping mode switch")
            return

        try:
            # Remove host mode marker (RaspiWiFi method)
            if Config.HOST_MODE_FILE.exists():
                Config.HOST_MODE_FILE.unlink()
                logger.info(f"Removed host mode marker: {Config.HOST_MODE_FILE}")

            # Restore original configurations if they exist (RaspiWiFi backup pattern)
            restore_commands = []

            dnsmasq_original = Path("/etc/dnsmasq.conf.original")
            if dnsmasq_original.exists():
                restore_commands.append(
                    (
                        "sudo mv /etc/dnsmasq.conf.original /etc/dnsmasq.conf",
                        "dnsmasq.conf",
                    )
                )

            dhcpcd_original = Path("/etc/dhcpcd.conf.original")
            if dhcpcd_original.exists():
                restore_commands.append(
                    (
                        "sudo mv /etc/dhcpcd.conf.original /etc/dhcpcd.conf",
                        "dhcpcd.conf",
                    )
                )

            # Execute restore commands with error checking
            for cmd, desc in restore_commands:
                try:
                    process = await asyncio.create_subprocess_shell(
                        cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await process.communicate()

                    if process.returncode == 0:
                        logger.info(f"Restored {desc}")
                    else:
                        logger.warning(f"Failed to restore {desc}: {stderr.decode()}")
                except Exception as e:
                    logger.warning(f"Error restoring {desc}: {e}")

            logger.info("Mode switch to client complete, initiating reboot...")

            # Reboot to apply changes
            await asyncio.create_subprocess_shell("sudo reboot")

        except Exception as e:
            logger.error(f"Failed to switch mode: {e}", exc_info=True)
            raise


# =============================================================================
# FastAPI Application
# =============================================================================

# Global radio manager instance
radio_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with radio system initialization"""
    global radio_manager

    # Startup
    print("Radio WiFi Backend starting...")
    Config.ensure_paths()
    if Config.IS_DEVELOPMENT:
        print("Running in development mode")

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


# =============================================================================
# API Routes
# =============================================================================


@app.get("/", response_model=ApiResponse)
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


@app.get("/health", response_model=ApiResponse)
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


@app.get("/wifi/status", response_model=ApiResponse)
async def get_wifi_status():
    """Get current WiFi status"""
    try:
        status = await WiFiManager.get_status()
        return ApiResponse(
            success=True, message="WiFi status retrieved", data=status.model_dump()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/wifi/scan", response_model=ApiResponse)
async def scan_wifi_networks():
    """Scan for available WiFi networks"""
    try:
        networks = await WiFiManager.scan_networks()
        return ApiResponse(
            success=True,
            message=f"Found {len(networks)} networks",
            data=[network.model_dump() for network in networks],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/wifi/connect", response_model=ApiResponse)
async def connect_wifi(credentials: WiFiCredentials, background_tasks: BackgroundTasks):
    """Connect to WiFi network (RaspiWiFi-style)"""
    try:
        # Validate credentials
        if not credentials.ssid.strip():
            raise HTTPException(status_code=400, detail="SSID cannot be empty")

        logger.info(f"Attempting to connect to WiFi: {credentials.ssid}")

        # Write wpa_supplicant.conf with credentials
        success = await WiFiManager.connect_network(credentials)

        if not success:
            logger.error(f"Failed to write WiFi credentials for {credentials.ssid}")
            return ApiResponse(
                success=False,
                message="Failed to save WiFi credentials. Check system permissions.",
            )

        logger.info(f"WiFi credentials saved for {credentials.ssid}")

        # Execute mode switch (not in background so we can catch errors)
        # Note: If in hotspot mode, this will remove host_mode marker and reboot
        try:
            await WiFiManager.switch_to_client_mode()
            # If we reach here, reboot is starting
            return ApiResponse(
                success=True,
                message=f"WiFi configured. System rebooting to connect to '{credentials.ssid}'...",
                data={
                    "ssid": credentials.ssid,
                    "instructions": "System will reboot. Connect your device to the new WiFi network and navigate to http://radio.local",
                },
            )
        except Exception as e:
            logger.error(f"Mode switch failed: {e}", exc_info=True)
            return ApiResponse(
                success=False,
                message=f"Failed to switch mode: {str(e)}. System remains in current mode.",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Connect WiFi error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/system/reset", response_model=ApiResponse)
async def reset_to_host_mode():
    """Reset system to host mode (RaspiWiFi reset functionality)"""
    if Config.IS_DEVELOPMENT:
        return ApiResponse(success=True, message="Reset simulated in development mode")

    try:
        # Create host mode marker
        Config.RASPIWIFI_DIR.mkdir(exist_ok=True)
        Config.HOST_MODE_FILE.touch()

        # Schedule reboot
        await asyncio.create_subprocess_shell("sudo reboot")

        return ApiResponse(success=True, message="System resetting to host mode...")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
