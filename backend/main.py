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
                        # Extract SSID and clean up quotes and whitespace
                        ssid_part = line.split("ESSID:")[1]
                        # Remove quotes, backslashes, and whitespace
                        ssid = (
                            ssid_part.strip()
                            .strip('"')
                            .strip()
                            .replace('\\"', "")
                            .strip()
                        )
                        break

            return SystemStatus(mode="client", connected=connected, ssid=ssid)

        except Exception:
            return SystemStatus(mode="client", connected=False)

    @staticmethod
    async def connect_network(credentials: WiFiCredentials) -> bool:
        """
        Connect to WiFi network with automatic retry (RaspiWiFi method with validation).

        Attempts connection up to 3 times with exponential backoff:
        - Attempt 1: Immediate (0s delay)
        - Attempt 2: 5s delay
        - Attempt 3: 10s delay

        Validates connection BEFORE rebooting system.
        """
        max_attempts = 3
        retry_delays = [0, 5, 10]  # Exponential backoff

        # Backup current config in case we need to rollback
        backup_path = Path("/tmp/wpa_supplicant.conf.backup")
        try:
            if Config.WPA_SUPPLICANT_FILE.exists() and not Config.IS_DEVELOPMENT:
                import shutil

                shutil.copy(Config.WPA_SUPPLICANT_FILE, backup_path)
                logger.info(f"Backed up current config to {backup_path}")
        except Exception as e:
            logger.warning(f"Could not backup config: {e}")

        for attempt in range(1, max_attempts + 1):
            logger.info(
                f"Connection attempt {attempt}/{max_attempts} to {credentials.ssid}"
            )

            # Add delay before retry (skip for first attempt)
            if attempt > 1:
                delay = retry_delays[attempt - 1]
                logger.info(f"Waiting {delay}s before retry...")
                await asyncio.sleep(delay)

            try:
                # Write wpa_supplicant.conf
                if not await WiFiManager._write_wpa_config(credentials):
                    logger.error(f"Attempt {attempt}: Failed to write config")
                    continue

                # Reconfigure wpa_supplicant to apply new config
                if not Config.IS_DEVELOPMENT:
                    try:
                        await WiFiManager.run_wpa_cli(["reconfigure"])
                        logger.info("Reconfigured wpa_supplicant with new credentials")
                    except Exception as e:
                        logger.error(f"Failed to reconfigure wpa_supplicant: {e}")
                        continue

                # Wait for connection with 40s timeout
                if await WiFiManager.wait_for_connection(credentials.ssid, timeout=40):
                    logger.info(f"Successfully connected on attempt {attempt}")
                    return True

                logger.warning(f"Attempt {attempt} failed: Connection timeout")

            except Exception as e:
                logger.error(f"Attempt {attempt} failed with exception: {e}")

        # All attempts failed - restore backup if exists
        logger.error(f"All {max_attempts} connection attempts failed")

        if backup_path.exists() and not Config.IS_DEVELOPMENT:
            try:
                import shutil

                shutil.copy(backup_path, Config.WPA_SUPPLICANT_FILE)
                await WiFiManager.run_wpa_cli(["reconfigure"])
                logger.info("Restored original WiFi configuration")
            except Exception as e:
                logger.error(f"Failed to restore backup: {e}")

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

    @staticmethod
    async def run_wpa_cli(command: List[str]) -> str:
        """
        Execute wpa_cli command and return output.

        Args:
            command: List of wpa_cli command arguments (e.g., ['list_networks'])

        Returns:
            stdout output as string
        """
        if Config.IS_DEVELOPMENT:
            # Mock data for development
            if command == ["list_networks"]:
                return "network id / ssid / bssid / flags\n0\tTestNetwork\tany\t[DISABLED]\n"
            elif command == ["status"]:
                return "wpa_state=DISCONNECTED\n"
            return ""

        try:
            logger.debug(f"Running wpa_cli command: {' '.join(command)}")

            # Use timeout wrapper to prevent hanging
            process = await asyncio.create_subprocess_exec(
                "timeout",
                "5",
                "wpa_cli",
                "-i",
                Config.WIFI_INTERFACE,
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            stdout_text = stdout.decode().strip()
            stderr_text = stderr.decode().strip()

            logger.debug(f"wpa_cli returncode: {process.returncode}")
            logger.debug(f"wpa_cli stdout: {stdout_text}")
            logger.debug(f"wpa_cli stderr: {stderr_text}")

            if process.returncode != 0:
                # timeout command returns 124 on timeout
                if process.returncode == 124:
                    raise Exception(f"wpa_cli command timed out after 5 seconds")
                logger.error(
                    f"wpa_cli command failed with code {process.returncode}: {stderr_text}"
                )
                raise Exception(f"wpa_cli error: {stderr_text or 'Unknown error'}")

            return stdout_text
        except Exception as e:
            logger.error(f"Failed to execute wpa_cli: {e}")
            raise

    @staticmethod
    async def wait_for_connection(ssid: str, timeout: int = 40) -> bool:
        """
        Wait for WiFi connection to complete (pre-reboot validation).

        Uses wpa_cli to poll connection status every 2 seconds.

        Args:
            ssid: Expected SSID to connect to
            timeout: Maximum wait time in seconds (default: 40)

        Returns:
            True if connected successfully, False if timeout/failed
        """
        logger.info(f"Waiting for connection to {ssid} (timeout: {timeout}s)")

        start_time = asyncio.get_event_loop().time()
        poll_interval = 2  # Check every 2 seconds

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                # Get wpa_supplicant state
                status_output = await WiFiManager.run_wpa_cli(["status"])

                # Parse status output
                status_dict = {}
                for line in status_output.split("\n"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        status_dict[key] = value

                wpa_state = status_dict.get("wpa_state", "")
                current_ssid = status_dict.get("ssid", "")

                logger.debug(
                    f"Connection status: state={wpa_state}, ssid={current_ssid}"
                )

                # Check if connected
                if wpa_state == "COMPLETED" and current_ssid == ssid:
                    ip_address = status_dict.get("ip_address", "N/A")
                    logger.info(f"Successfully connected to {ssid} (IP: {ip_address})")
                    return True

                # Check for failure states
                if wpa_state in ["DISCONNECTED", "INACTIVE"]:
                    logger.warning(f"Connection failed: wpa_state={wpa_state}")
                    # Don't return immediately, give it more time

            except Exception as e:
                logger.error(f"Error checking connection status: {e}")

            await asyncio.sleep(poll_interval)

        logger.error(f"Connection timeout after {timeout}s")
        return False

    @staticmethod
    async def _write_wpa_config(credentials: WiFiCredentials) -> bool:
        """Helper method to write wpa_supplicant.conf (extracted from connect_network)"""
        if Config.IS_DEVELOPMENT:
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

            # Write to temp file
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
    async def list_saved_networks() -> List[dict]:
        """
        List all saved WiFi networks by parsing wpa_supplicant.conf.

        Returns:
            List of saved networks with id, ssid, and current connection status
        """
        try:
            # Get current connection status
            current_status = await WiFiManager.get_status()
            current_ssid = current_status.ssid if current_status.connected else None

            # Parse wpa_supplicant.conf file
            if not Config.WPA_SUPPLICANT_FILE.exists():
                logger.warning("wpa_supplicant.conf not found")
                return []

            config_content = Config.WPA_SUPPLICANT_FILE.read_text()
            networks = []
            network_id = 0

            # Parse network blocks
            in_network = False
            current_network = {}

            for line in config_content.split("\n"):
                line = line.strip()

                if line.startswith("network={"):
                    in_network = True
                    current_network = {"id": network_id}
                elif line == "}" and in_network:
                    # End of network block
                    if "ssid" in current_network:
                        # Check if this is the currently connected network
                        current_network["current"] = (
                            current_ssid is not None
                            and current_network["ssid"] == current_ssid
                        )
                        current_network["disabled"] = (
                            False  # Not tracking disabled state from file
                        )
                        networks.append(current_network)
                        network_id += 1
                    in_network = False
                    current_network = {}
                elif in_network and "=" in line:
                    # Parse network property
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"')

                    if key == "ssid":
                        current_network["ssid"] = value

            logger.info(
                f"Found {len(networks)} saved networks (current: {current_ssid})"
            )
            return networks

        except Exception as e:
            logger.error(f"Failed to list saved networks: {e}")
            return []

    @staticmethod
    async def forget_network(network_id: int) -> bool:
        """
        Remove a saved WiFi network by rewriting wpa_supplicant.conf.

        Args:
            network_id: Network ID (index) from list_saved_networks

        Returns:
            True if successfully removed
        """
        try:
            if not Config.WPA_SUPPLICANT_FILE.exists():
                logger.error("wpa_supplicant.conf not found")
                return False

            config_content = Config.WPA_SUPPLICANT_FILE.read_text()
            lines = config_content.split("\n")

            # Parse and rebuild config, skipping the network at network_id
            new_lines = []
            in_network = False
            current_network_id = 0
            skip_network = False

            for line in lines:
                stripped = line.strip()

                if stripped.startswith("network={"):
                    in_network = True
                    skip_network = current_network_id == network_id
                    if not skip_network:
                        new_lines.append(line)
                elif stripped == "}" and in_network:
                    if not skip_network:
                        new_lines.append(line)
                    in_network = False
                    current_network_id += 1
                    skip_network = False
                elif not skip_network:
                    new_lines.append(line)

            # Write updated config to temp file
            temp_file = Path("/tmp/wpa_supplicant.conf.tmp")
            temp_file.write_text("\n".join(new_lines))

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

            if process.returncode != 0:
                logger.error(f"Failed to update wpa_supplicant.conf: {stderr.decode()}")
                return False

            logger.info(f"Successfully removed network ID {network_id}")

            # Reconfigure wpa_supplicant to reload config
            try:
                await WiFiManager.run_wpa_cli(["reconfigure"])
            except Exception as e:
                logger.warning(f"Could not reconfigure wpa_supplicant: {e}")
                # Not critical - config will reload on next reboot

            return True

        except Exception as e:
            logger.error(f"Failed to remove network {network_id}: {e}")
            return False


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


@app.get("/wifi/status", response_model=ApiResponse, tags=["WiFi Management"])
async def get_wifi_status():
    """Get current WiFi status"""
    try:
        status = await WiFiManager.get_status()
        return ApiResponse(
            success=True, message="WiFi status retrieved", data=status.model_dump()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/wifi/scan", response_model=ApiResponse, tags=["WiFi Management"])
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


@app.post("/wifi/connect", response_model=ApiResponse, tags=["WiFi Management"])
async def connect_wifi(credentials: WiFiCredentials, background_tasks: BackgroundTasks):
    """
    Connect to WiFi network with retry logic and validation.

    Now validates connection BEFORE rebooting system.
    Returns success only if connection verified.
    """
    logger.info(f"Attempting to connect to WiFi: {credentials.ssid}")

    # Attempt connection with retry (validates before reboot)
    success = await WiFiManager.connect_network(credentials)

    if not success:
        logger.error(f"Failed to connect to {credentials.ssid} after retries")
        return ApiResponse(
            success=False,
            message=f"Failed to connect to '{credentials.ssid}'. Check password and try again.",
            data={"ssid": credentials.ssid, "attempts": 3, "timeout": 40},
        )

    # Connection successful - now switch to client mode and reboot
    try:
        logger.info(f"Connection verified. Switching to client mode and rebooting...")
        await WiFiManager.switch_to_client_mode()

        return ApiResponse(
            success=True,
            message=f"Connected to '{credentials.ssid}'. System rebooting to apply changes...",
            data={
                "ssid": credentials.ssid,
                "instructions": "System will reboot. Reconnect to the new WiFi network and navigate to http://radio.local",
            },
        )
    except Exception as e:
        logger.error(f"Mode switch failed: {e}", exc_info=True)
        return ApiResponse(
            success=False,
            message=f"Connected to WiFi but mode switch failed: {str(e)}",
            data={"ssid": credentials.ssid},
        )


@app.get("/wifi/saved", response_model=ApiResponse, tags=["WiFi Management"])
async def get_saved_networks():
    """Get list of saved WiFi networks from wpa_supplicant.conf"""
    try:
        networks = await WiFiManager.list_saved_networks()
        return ApiResponse(
            success=True,
            message=f"Found {len(networks)} saved networks",
            data={"networks": networks},
        )
    except Exception as e:
        logger.error(f"Failed to get saved networks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete(
    "/wifi/saved/{network_id}", response_model=ApiResponse, tags=["WiFi Management"]
)
async def forget_saved_network(network_id: int):
    """
    Forget/remove a saved WiFi network.

    Args:
        network_id: Network ID from saved networks list
    """
    try:
        # Check if network exists
        saved_networks = await WiFiManager.list_saved_networks()
        network = next((n for n in saved_networks if n["id"] == network_id), None)

        if not network:
            raise HTTPException(
                status_code=404, detail=f"Network ID {network_id} not found"
            )

        # Don't allow forgetting currently connected network
        if network.get("current", False):
            raise HTTPException(
                status_code=400,
                detail="Cannot forget currently connected network. Connect to another network first.",
            )

        # Remove network
        success = await WiFiManager.forget_network(network_id)

        if success:
            return ApiResponse(
                success=True, message=f"Successfully forgot network: {network['ssid']}"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to remove network")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forgetting network {network_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/system/reset", response_model=ApiResponse, tags=["WiFi Management"])
async def reset_to_host_mode():
    """Reset system to hotspot mode (creates Radio-Setup AP for reconfiguration)"""
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
