"""
WiFi Manager using NetworkManager (nmcli)

This module handles all WiFi operations using nmcli instead of wpa_supplicant.
It provides a clean interface for scanning, connecting, and managing WiFi networks.
"""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class WiFiNetwork:
    """WiFi network information"""

    def __init__(
        self,
        ssid: str,
        signal: Optional[int] = None,
        encryption: str = "Unknown",
        frequency: Optional[str] = None,
    ):
        self.ssid = ssid
        self.signal = signal
        self.encryption = encryption
        self.frequency = frequency

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "ssid": self.ssid,
            "signal": self.signal,
            "encryption": self.encryption,
            "frequency": self.frequency,
        }


class WiFiStatus:
    """WiFi connection status"""

    def __init__(
        self,
        mode: str,
        connected: bool,
        ssid: Optional[str] = None,
        ip_address: Optional[str] = None,
        signal_strength: Optional[int] = None,
    ):
        self.mode = mode  # "client" or "host"
        self.connected = connected
        self.ssid = ssid
        self.ip_address = ip_address
        self.signal_strength = signal_strength

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "mode": self.mode,
            "connected": self.connected,
            "ssid": self.ssid,
            "ip_address": self.ip_address,
            "signal_strength": self.signal_strength,
        }


class WiFiManager:
    """WiFi management using NetworkManager (nmcli)"""

    def __init__(
        self,
        interface: str = "wlan0",
        host_mode_file: Optional[Path] = None,
        development_mode: bool = False,
        hotspot_ssid: str = "Radio-Setup",
        hotspot_password: str = "radio123",
        hotspot_ip: str = "192.168.4.1",
    ):
        self.interface = interface
        self.host_mode_file = host_mode_file or Path("/etc/raspiwifi/host_mode")
        self.development_mode = development_mode
        self.hotspot_ssid = hotspot_ssid
        self.hotspot_password = hotspot_password
        self.hotspot_ip = hotspot_ip
        logger.info(
            f"WiFiManager initialized (interface={interface}, dev_mode={development_mode})"
        )

    async def _run_cmd(self, *args: str, check: bool = True) -> tuple[int, str, str]:
        """Run a subprocess command and return (returncode, stdout, stderr)"""
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()
        if check and process.returncode != 0:
            logger.warning(
                f"Command {args} failed ({process.returncode}): {stderr_str}"
            )
        return process.returncode, stdout_str, stderr_str

    def _parse_nmcli_scan(self, output: str) -> List[WiFiNetwork]:
        """Parse nmcli scan output into WiFiNetwork objects"""
        networks_dict = {}  # Use dict to track best signal per SSID

        lines = output.strip().split("\n")
        for line in lines:
            if not line.strip():
                continue

            # nmcli output format: SSID:SIGNAL:SECURITY:FREQ
            parts = line.split(":")
            if len(parts) < 4:
                continue

            ssid = parts[0].strip()
            if not ssid:
                continue

            try:
                signal = int(parts[1].strip()) if parts[1].strip() else 0
                security = parts[2].strip() if parts[2].strip() else "Open"
                freq = parts[3].strip() if parts[3].strip() else None

                # Simplify security display
                if security == "--":
                    encryption = "Open"
                elif "WPA3" in security:
                    encryption = "WPA3"
                elif "WPA2" in security:
                    encryption = "WPA2"
                elif "WPA" in security:
                    encryption = "WPA"
                else:
                    encryption = security if security else "Unknown"

                # Convert frequency to GHz band
                frequency = None
                if freq:
                    try:
                        freq_val = int(freq.split()[0]) if freq.split() else 0
                        if 2400 <= freq_val <= 2500:
                            frequency = "2.4GHz"
                        elif 5000 <= freq_val <= 6000:
                            frequency = "5GHz"
                    except (ValueError, IndexError):
                        pass

                # Keep the network with the best signal for each SSID
                if ssid not in networks_dict or signal > networks_dict[ssid].signal:
                    networks_dict[ssid] = WiFiNetwork(
                        ssid=ssid,
                        signal=signal,
                        encryption=encryption,
                        frequency=frequency,
                    )
            except (ValueError, IndexError) as e:
                logger.debug(f"Skipping malformed line: {line} ({e})")
                continue

        # Convert dict to list and sort by signal strength
        networks = sorted(
            networks_dict.values(), key=lambda n: n.signal or 0, reverse=True
        )
        return networks

    async def scan_networks(self) -> List[WiFiNetwork]:
        """Scan for available WiFi networks using nmcli"""

        if self.development_mode:
            # Return mock data for development
            return [
                WiFiNetwork(
                    ssid="HomeWiFi", signal=75, encryption="WPA2", frequency="2.4GHz"
                ),
                WiFiNetwork(
                    ssid="GuestNetwork", signal=60, encryption="Open", frequency="5GHz"
                ),
                WiFiNetwork(
                    ssid="NeighborWiFi",
                    signal=45,
                    encryption="WPA3",
                    frequency="2.4GHz",
                ),
            ]

        try:
            # Request fresh scan first (requires sudo for permission)
            rescan_process = await asyncio.create_subprocess_exec(
                "sudo",
                "nmcli",
                "device",
                "wifi",
                "rescan",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            rescan_stdout, rescan_stderr = await rescan_process.communicate()

            if rescan_process.returncode != 0:
                logger.warning(
                    f"WiFi rescan returned non-zero: {rescan_stderr.decode()}"
                )
            else:
                logger.info("WiFi rescan completed successfully")

            # Wait longer for scan to complete (networks take time to be discovered)
            # Increased to 5 seconds to ensure all networks are found
            await asyncio.sleep(5)

            # Get scan results with custom format (--rescan ensures fresh data)
            process = await asyncio.create_subprocess_exec(
                "nmcli",
                "-t",
                "-f",
                "SSID,SIGNAL,SECURITY,FREQ",
                "device",
                "wifi",
                "list",
                "--rescan",
                "no",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"nmcli scan failed: {stderr.decode()}")

            return self._parse_nmcli_scan(stdout.decode())

        except Exception as e:
            raise Exception(f"WiFi scan failed: {str(e)}")

    async def get_status(self) -> WiFiStatus:
        """Get current WiFi status using nmcli"""

        if self.development_mode:
            return WiFiStatus(
                mode="host",
                connected=False,
                ssid="Radio-Setup",
                ip_address="192.168.4.1",
            )

        try:
            # Check if in host mode marker exists
            is_host_mode = self.host_mode_file.exists()

            if is_host_mode:
                return WiFiStatus(
                    mode="host",
                    connected=True,
                    ssid="Radio-Setup",
                    ip_address="192.168.4.1",
                )

            # Get WiFi connection status from NetworkManager
            process = await asyncio.create_subprocess_exec(
                "nmcli",
                "-t",
                "-f",
                "TYPE,STATE,CONNECTION",
                "device",
                "status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return WiFiStatus(mode="client", connected=False)

            output = stdout.decode()

            # Look for WiFi connection
            connected = False
            connection_name = None

            for line in output.split("\n"):
                if not line.strip():
                    continue
                parts = line.split(":")
                if len(parts) >= 3 and parts[0] == "wifi":
                    if parts[1] == "connected":
                        connected = True
                        connection_name = parts[2].strip() if parts[2].strip() else None
                        break

            # Get actual SSID from the active WiFi connection (not the connection name)
            ssid = None
            if connected:
                wifi_list_process = await asyncio.create_subprocess_exec(
                    "nmcli",
                    "-t",
                    "-f",
                    "IN-USE,SSID",
                    "device",
                    "wifi",
                    "list",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                wifi_stdout, _ = await wifi_list_process.communicate()
                if wifi_list_process.returncode == 0:
                    # Find the active connection (marked with *)
                    for line in wifi_stdout.decode().split("\n"):
                        if line.startswith("*"):
                            parts = line.split(":")
                            if len(parts) >= 2:
                                ssid = parts[1].strip()
                                break

            # Get IP address and signal strength if connected
            ip_address = None
            signal_strength = None

            if connected and connection_name:
                # Get IP address using connection name
                ip_process = await asyncio.create_subprocess_exec(
                    "nmcli",
                    "-t",
                    "-f",
                    "IP4.ADDRESS",
                    "connection",
                    "show",
                    connection_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                ip_stdout, _ = await ip_process.communicate()
                if ip_process.returncode == 0:
                    ip_output = ip_stdout.decode().strip()
                    if ip_output:
                        # Extract IP (format: IP4.ADDRESS[1]:192.168.1.100/24)
                        for line in ip_output.split("\n"):
                            if line.startswith("IP4.ADDRESS"):
                                ip_address = (
                                    line.split(":")[1].split("/")[0]
                                    if ":" in line
                                    else None
                                )
                                break

                # Get signal strength
                sig_process = await asyncio.create_subprocess_exec(
                    "nmcli",
                    "-t",
                    "-f",
                    "IN-USE,SIGNAL,SSID",
                    "device",
                    "wifi",
                    "list",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                sig_stdout, _ = await sig_process.communicate()
                if sig_process.returncode == 0:
                    for line in sig_stdout.decode().split("\n"):
                        if line.startswith("*"):  # Active connection
                            parts = line.split(":")
                            if len(parts) >= 2:
                                try:
                                    signal_strength = int(parts[1].strip())
                                except ValueError:
                                    pass
                                break

            return WiFiStatus(
                mode="client",
                connected=connected,
                ssid=ssid,
                ip_address=ip_address,
                signal_strength=signal_strength,
            )

        except Exception as e:
            logger.error(f"Error getting WiFi status: {e}")
            return WiFiStatus(mode="client", connected=False)

    @staticmethod
    def _validate_ssid(ssid: str) -> Optional[str]:
        """Return an error message for an invalid SSID, or None if OK."""
        if not ssid:
            return "SSID must not be empty"
        if len(ssid.encode("utf-8")) > 32:
            return "SSID must be at most 32 bytes (802.11)"
        if any(ord(c) < 0x20 or ord(c) == 0x7F for c in ssid):
            return "SSID must not contain control characters"
        return None

    @staticmethod
    def _write_psk_file(password: str) -> str:
        """Write the PSK to a private 0600 temp file for nmcli's passwd-file.

        Keeps the password out of process argv (/proc/<pid>/cmdline is
        world-readable for the lifetime of the nmcli call). Caller must
        delete the file in a finally block.
        """
        fd, path = tempfile.mkstemp(prefix="nm-psk-")
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(f"802-11-wireless-security.psk:{password}\n")
        except BaseException:
            os.unlink(path)
            raise
        return path

    async def _nmcli(self, *args: str) -> tuple[int, str, str]:
        """Run sudo nmcli with args; return (returncode, stdout, stderr)."""
        process = await asyncio.create_subprocess_exec(
            "sudo",
            "nmcli",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode().strip(), stderr.decode().strip()

    async def connect_network(self, ssid: str, password: str = "") -> tuple[bool, str]:
        """
        Connect to WiFi network using nmcli (single attempt).

        User can manually retry if connection fails.
        Validates connection BEFORE returning success.

        The PSK is passed via a private passwd-file, never argv; the SSID is
        only ever the value after the `ssid` property keyword, so names
        starting with `-` cannot be parsed as nmcli options.

        Returns:
            tuple[bool, str]: (success, error_message)
        """
        last_error = ""

        ssid_error = self._validate_ssid(ssid)
        if ssid_error:
            logger.warning(f"Rejected invalid SSID: {ssid_error}")
            return False, ssid_error

        logger.info(f"Attempting to connect to {ssid}")

        try:
            # Resolve exact NM connection name for this SSID (avoids substring-match false positives)
            saved = await self.list_saved_networks()
            existing = next((n for n in saved if n["ssid"] == ssid), None)

            if existing:
                connection_name = existing["connection_name"]
                logger.info(f"Existing NM profile found for {ssid!r}: {connection_name!r}")
                # Bring up the profile; a supplied password goes via passwd-file
                # (NM persists it on the profile under default psk-flags)
                if password:
                    psk_path = self._write_psk_file(password)
                    try:
                        returncode, _, stderr = await self._nmcli(
                            "connection", "up", connection_name, "passwd-file", psk_path
                        )
                    finally:
                        try:
                            os.unlink(psk_path)
                        except OSError:
                            pass
                else:
                    returncode, _, stderr = await self._nmcli(
                        "connection", "up", connection_name
                    )

                if returncode != 0:
                    last_error = stderr
                    logger.error(f"nmcli connection up failed: {last_error}")
                    return False, last_error
            else:
                logger.info(f"Creating new connection for {ssid}...")
                connection_name = ssid
                add_args = [
                    "connection", "add",
                    "type", "wifi",
                    "con-name", connection_name,
                    "ifname", self.interface,
                    "ssid", ssid,
                ]
                if password:
                    add_args += ["wifi-sec.key-mgmt", "wpa-psk"]

                returncode, _, stderr = await self._nmcli(*add_args)
                if returncode != 0:
                    last_error = stderr
                    logger.error(f"nmcli connection add failed: {last_error}")
                    return False, last_error

                if password:
                    psk_path = self._write_psk_file(password)
                    try:
                        returncode, _, stderr = await self._nmcli(
                            "connection", "up", connection_name, "passwd-file", psk_path
                        )
                    finally:
                        try:
                            os.unlink(psk_path)
                        except OSError:
                            pass
                else:
                    returncode, _, stderr = await self._nmcli(
                        "connection", "up", connection_name
                    )

                if returncode != 0:
                    last_error = stderr
                    logger.error(f"nmcli connection up failed: {last_error}")
                    # Don't accumulate half-configured profiles from failed attempts
                    await self._nmcli("connection", "delete", connection_name)
                    return False, last_error

            # Wait for connection with 40s timeout
            if await self.wait_for_connection(ssid, timeout=40):
                logger.info(f"Successfully connected to {ssid}")
                return True, ""

            last_error = (
                "Connection timeout - network may be out of range or password incorrect"
            )
            logger.warning(f"Connection failed: Connection timeout")
            return False, last_error

        except Exception as e:
            last_error = str(e)
            logger.error(f"Connection failed with exception: {e}")
            return False, last_error

    async def wait_for_connection(self, ssid: str, timeout: int = 40) -> bool:
        """
        Wait for WiFi connection to complete (pre-switch validation).

        Uses nmcli to poll connection status every 2 seconds.

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
                # Check connection status using nmcli
                process = await asyncio.create_subprocess_exec(
                    "nmcli",
                    "-t",
                    "-f",
                    "DEVICE,STATE,CONNECTION",
                    "device",
                    "status",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()
                output = stdout.decode().strip()

                # Check if connected to target SSID
                for line in output.split("\n"):
                    parts = line.split(":")
                    if len(parts) >= 3 and parts[1] == "connected":
                        current_ssid = parts[2].strip()
                        if current_ssid == ssid:
                            logger.info(f"Successfully connected to {ssid}")
                            # Give a moment for DHCP to complete
                            await asyncio.sleep(2)
                            return True

            except Exception as e:
                logger.error(f"Error checking connection status: {e}")

            await asyncio.sleep(poll_interval)

        logger.error(f"Connection timeout after {timeout}s")
        return False

    async def list_saved_networks(self) -> List[dict]:
        """
        List all saved WiFi networks using nmcli.

        Returns:
            List of saved networks with id, ssid, and current connection status
        """
        try:
            # Get current connection status
            current_status = await self.get_status()
            current_ssid = current_status.ssid if current_status.connected else None

            # Get list of saved WiFi connections with their actual SSIDs
            process = await asyncio.create_subprocess_exec(
                "nmcli",
                "-t",
                "-f",
                "NAME,TYPE",
                "connection",
                "show",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Failed to list connections: {stderr.decode()}")
                return []

            networks = []
            network_id = 0

            for line in stdout.decode().split("\n"):
                if not line.strip():
                    continue

                parts = line.split(":")
                if len(parts) >= 2 and parts[1] == "802-11-wireless":
                    connection_name = parts[0].strip()

                    # Get the actual SSID from connection details
                    detail_process = await asyncio.create_subprocess_exec(
                        "nmcli",
                        "-t",
                        "-f",
                        "802-11-wireless.ssid",
                        "connection",
                        "show",
                        connection_name,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    detail_stdout, _ = await detail_process.communicate()

                    # Extract SSID from output (format: "802-11-wireless.ssid:NetworkName")
                    actual_ssid = connection_name  # Default to connection name
                    if detail_process.returncode == 0:
                        detail_output = detail_stdout.decode().strip()
                        if ":" in detail_output:
                            actual_ssid = detail_output.split(":", 1)[1].strip()

                    networks.append(
                        {
                            "id": network_id,
                            "ssid": actual_ssid,
                            "connection_name": connection_name,
                            "current": current_ssid is not None
                            and actual_ssid == current_ssid,
                            "disabled": False,
                        }
                    )
                    network_id += 1

            logger.info(
                f"Found {len(networks)} saved networks (current: {current_ssid})"
            )
            return networks

        except Exception as e:
            logger.error(f"Failed to list saved networks: {e}")
            return []

    async def forget_network(self, connection_name: str) -> bool:
        """
        Remove a saved WiFi network using nmcli.

        Keyed by the stable NetworkManager connection name — a positional
        index would resolve to the wrong profile whenever the connection
        list changes between enumeration and deletion.

        Args:
            connection_name: NM connection name from list_saved_networks

        Returns:
            True if successfully removed; False if the name is unknown
        """
        try:
            # Single enumeration: verify existence and read the current flag
            saved_networks = await self.list_saved_networks()
            target_network = next(
                (n for n in saved_networks if n["connection_name"] == connection_name),
                None,
            )
            if target_network is None:
                logger.error(f"No saved network named {connection_name!r}")
                return False

            ssid = target_network["ssid"]

            # Disconnect first if this is the currently active connection
            if target_network.get("current", False):
                logger.info(f"Disconnecting from active network {ssid!r} before deleting profile")
                disc_process = await asyncio.create_subprocess_exec(
                    "sudo",
                    "nmcli",
                    "device",
                    "disconnect",
                    self.interface,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await disc_process.communicate()

            # Delete the connection profile using the exact NM connection name
            process = await asyncio.create_subprocess_exec(
                "sudo",
                "nmcli",
                "connection",
                "delete",
                connection_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Failed to delete connection: {stderr.decode()}")
                return False

            logger.info(f"Successfully removed network: {ssid} (profile: {connection_name!r})")
            return True

        except Exception as e:
            logger.error(f"Failed to remove network {connection_name!r}: {e}")
            return False

    async def switch_to_client_mode(self):
        """Switch from host mode to client mode using nmcli"""

        if self.development_mode:
            logger.info("Development mode: Skipping mode switch")
            return

        try:
            # Stop the nmcli hotspot connection
            await self._run_cmd(
                "sudo", "nmcli", "connection", "down", "Hotspot", check=False
            )
            logger.info("Stopped hotspot connection")

            # Remove host mode marker
            if self.host_mode_file.exists():
                await self._run_cmd("sudo", "rm", "-f", str(self.host_mode_file))
                logger.info(f"Removed host mode marker: {self.host_mode_file}")

            # Re-enable NetworkManager management of the interface
            await self._run_cmd(
                "sudo", "nmcli", "device", "set", self.interface, "managed", "yes"
            )
            logger.info("Mode switch to client complete")

        except Exception as e:
            logger.error(f"Failed to switch mode: {e}", exc_info=True)
            raise

    async def switch_to_host_mode(self):
        """Switch from client mode to host mode (hotspot) using nmcli"""

        if self.development_mode:
            logger.info("Development mode: Skipping mode switch to host")
            return

        try:
            # 1. Create host mode marker
            await self._run_cmd("sudo", "mkdir", "-p", str(self.host_mode_file.parent))
            rc, _, stderr = await self._run_cmd(
                "sudo", "touch", str(self.host_mode_file)
            )
            if rc != 0:
                raise Exception(f"Failed to create host mode file: {stderr}")
            logger.info(f"Created host mode marker: {self.host_mode_file}")

            # 2. Disconnect any active WiFi connection
            await self._run_cmd(
                "sudo", "nmcli", "device", "disconnect", self.interface, check=False
            )
            logger.info(f"Disconnected WiFi interface {self.interface}")

            # 3. Start hotspot using nmcli (handles AP, DHCP, IP all in one)
            rc, stdout, stderr = await self._run_cmd(
                "sudo",
                "nmcli",
                "device",
                "wifi",
                "hotspot",
                "ifname",
                self.interface,
                "ssid",
                self.hotspot_ssid,
                "password",
                self.hotspot_password,
            )
            if rc != 0:
                raise Exception(f"nmcli hotspot failed: {stderr}")

            # nmcli's built-in DHCP hands clients the gateway IP; the UI is
            # reachable at http://<hotspot_ip>:8000 (radio.local does not
            # resolve in hotspot mode — mDNS is a client-mode feature)
            logger.info(
                f"Hotspot mode active: SSID={self.hotspot_ssid}, "
                f"UI at http://{self.hotspot_ip}:8000"
            )

        except Exception as e:
            logger.error(f"Failed to switch to host mode: {e}", exc_info=True)
            raise
