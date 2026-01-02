"""
Unit tests for WiFi management functionality.

Tests WiFi connection scenarios including:
- Successful WiFi network switching with correct credentials
- Failed WiFi network switching with wrong credentials
- WiFi connection loss scenarios
- Network scanning
- Host/client mode switching
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import Config, SystemStatus, WiFiCredentials, WiFiManager, app


class TestWiFiManager:
    """Test WiFiManager class methods with mocked system calls"""

    @pytest.mark.asyncio
    async def test_connect_network_success_with_password(self):
        """Test successful WiFi connection with correct credentials"""
        credentials = WiFiCredentials(ssid="HomeNetwork", password="correct_password")

        # Mock file operations and subprocess
        with (
            patch("pathlib.Path.write_text") as mock_write,
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
        ):
            # Mock successful sudo mv command
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_subprocess.return_value = mock_process

            # Temporarily disable development mode
            original_dev = Config.IS_DEVELOPMENT
            Config.IS_DEVELOPMENT = False

            try:
                result = await WiFiManager.connect_network(credentials)

                # Verify success
                assert result is True

                # Verify wpa_supplicant.conf was written
                mock_write.assert_called_once()
                written_config = mock_write.call_args[0][0]
                assert 'ssid="HomeNetwork"' in written_config
                assert 'psk="correct_password"' in written_config

                # Verify sudo mv was called
                mock_subprocess.assert_called_once()
                call_args = mock_subprocess.call_args[0]
                assert "sudo" in call_args
                assert "mv" in call_args

            finally:
                Config.IS_DEVELOPMENT = original_dev

    @pytest.mark.asyncio
    async def test_connect_network_success_open_network(self):
        """Test successful WiFi connection to open network (no password)"""
        credentials = WiFiCredentials(ssid="OpenNetwork", password="")

        with (
            patch("pathlib.Path.write_text") as mock_write,
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
        ):
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_subprocess.return_value = mock_process

            original_dev = Config.IS_DEVELOPMENT
            Config.IS_DEVELOPMENT = False

            try:
                result = await WiFiManager.connect_network(credentials)

                assert result is True

                # Verify open network config
                written_config = mock_write.call_args[0][0]
                assert 'ssid="OpenNetwork"' in written_config
                assert "key_mgmt=NONE" in written_config
                assert "psk=" not in written_config

            finally:
                Config.IS_DEVELOPMENT = original_dev

    @pytest.mark.asyncio
    async def test_connect_network_failure_permission_denied(self):
        """Test WiFi connection failure due to permission issues (wrong credentials scenario)"""
        credentials = WiFiCredentials(ssid="SecureNetwork", password="wrong_password")

        with (
            patch("pathlib.Path.write_text") as mock_write,
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
        ):
            # Mock failed sudo mv command (permission denied)
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(
                return_value=(b"", b"Permission denied")
            )
            mock_subprocess.return_value = mock_process

            original_dev = Config.IS_DEVELOPMENT
            Config.IS_DEVELOPMENT = False

            try:
                result = await WiFiManager.connect_network(credentials)

                # Verify failure
                assert result is False

            finally:
                Config.IS_DEVELOPMENT = original_dev

    @pytest.mark.asyncio
    async def test_connect_network_failure_exception(self):
        """Test WiFi connection failure due to system exception"""
        credentials = WiFiCredentials(ssid="Network", password="password")

        with patch("pathlib.Path.write_text", side_effect=Exception("Disk full")):
            original_dev = Config.IS_DEVELOPMENT
            Config.IS_DEVELOPMENT = False

            try:
                result = await WiFiManager.connect_network(credentials)
                assert result is False

            finally:
                Config.IS_DEVELOPMENT = original_dev

    @pytest.mark.asyncio
    async def test_get_status_host_mode(self):
        """Test WiFi status when in host mode (AP mode)"""

        with patch.object(Path, "exists", return_value=True):
            original_dev = Config.IS_DEVELOPMENT
            Config.IS_DEVELOPMENT = False

            try:
                status = await WiFiManager.get_status()

                assert status.mode == "host"
                assert status.connected is True
                assert status.ssid == "Radio-Setup"
                assert status.ip_address == "192.168.4.1"

            finally:
                Config.IS_DEVELOPMENT = original_dev

    @pytest.mark.asyncio
    async def test_get_status_client_mode_connected(self):
        """Test WiFi status when connected to network in client mode"""

        # Mock iwconfig output for connected state
        iwconfig_output = b"""wlan0     IEEE 802.11  ESSID:"HomeNetwork"
                  Mode:Managed  Frequency:2.437 GHz  Access Point: AA:BB:CC:DD:EE:FF
                  Bit Rate=72.2 Mb/s   Tx-Power=31 dBm
                  Retry short limit:7   RTS thr:off   Fragment thr:off"""

        with (
            patch.object(Path, "exists", return_value=False),
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
        ):
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(iwconfig_output, b""))
            mock_subprocess.return_value = mock_process

            original_dev = Config.IS_DEVELOPMENT
            Config.IS_DEVELOPMENT = False

            try:
                status = await WiFiManager.get_status()

                assert status.mode == "client"
                assert status.connected is True
                assert status.ssid == "HomeNetwork"

            finally:
                Config.IS_DEVELOPMENT = original_dev

    @pytest.mark.asyncio
    async def test_get_status_client_mode_disconnected(self):
        """Test WiFi status when disconnected (simulates lost connection)"""

        # Mock iwconfig output for disconnected state
        iwconfig_output = b"""wlan0     IEEE 802.11  ESSID:off/any
                  Mode:Managed  Access Point: Not-Associated
                  Retry short limit:7   RTS thr:off   Fragment thr:off"""

        with (
            patch.object(Path, "exists", return_value=False),
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
        ):
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(iwconfig_output, b""))
            mock_subprocess.return_value = mock_process

            original_dev = Config.IS_DEVELOPMENT
            Config.IS_DEVELOPMENT = False

            try:
                status = await WiFiManager.get_status()

                assert status.mode == "client"
                assert status.connected is False
                assert status.ssid is None

            finally:
                Config.IS_DEVELOPMENT = original_dev

    @pytest.mark.asyncio
    async def test_get_status_iwconfig_failure(self):
        """Test WiFi status when iwconfig command fails"""

        with (
            patch.object(Path, "exists", return_value=False),
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
        ):
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b"", b"Error"))
            mock_subprocess.return_value = mock_process

            original_dev = Config.IS_DEVELOPMENT
            Config.IS_DEVELOPMENT = False

            try:
                status = await WiFiManager.get_status()

                assert status.mode == "client"
                assert status.connected is False

            finally:
                Config.IS_DEVELOPMENT = original_dev

    @pytest.mark.asyncio
    async def test_switch_to_client_mode_success(self):
        """Test successful switch from host mode to client mode"""

        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "unlink") as mock_unlink,
            patch("asyncio.create_subprocess_shell") as mock_subprocess,
        ):
            # Mock successful restore commands
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_subprocess.return_value = mock_process

            original_dev = Config.IS_DEVELOPMENT
            Config.IS_DEVELOPMENT = False

            try:
                await WiFiManager.switch_to_client_mode()

                # Verify host mode marker was removed
                mock_unlink.assert_called()

                # Verify reboot was called (last subprocess call)
                reboot_call = mock_subprocess.call_args_list[-1]
                assert "reboot" in reboot_call[0][0]

            finally:
                Config.IS_DEVELOPMENT = original_dev

    @pytest.mark.asyncio
    async def test_switch_to_client_mode_restore_configs(self):
        """Test mode switch restores original configs if they exist"""

        def path_exists(self):
            """Mock exists() to return True for backup configs"""
            if "original" in str(self):
                return True
            if str(self).endswith("host_mode"):
                return True
            return False

        with (
            patch.object(Path, "exists", path_exists),
            patch.object(Path, "unlink"),
            patch("asyncio.create_subprocess_shell") as mock_subprocess,
        ):
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_subprocess.return_value = mock_process

            original_dev = Config.IS_DEVELOPMENT
            Config.IS_DEVELOPMENT = False

            try:
                await WiFiManager.switch_to_client_mode()

                # Verify restore commands were called
                calls = [str(call[0][0]) for call in mock_subprocess.call_args_list]

                # Should have dnsmasq and dhcpcd restore commands plus reboot
                restore_commands = [c for c in calls if "original" in c]
                assert len(restore_commands) >= 2  # dnsmasq and dhcpcd

                # Check for reboot
                assert any("reboot" in c for c in calls)

            finally:
                Config.IS_DEVELOPMENT = original_dev

    @pytest.mark.asyncio
    async def test_scan_networks_success(self):
        """Test successful WiFi network scanning"""

        # Mock iwlist scan output
        iwlist_output = b"""wlan0     Scan completed :
          Cell 01 - Address: AA:BB:CC:DD:EE:FF
                    ESSID:"HomeNetwork"
                    Mode:Master
                    Frequency:2.437 GHz (Channel 6)
                    Quality=70/70  Signal level=-40 dBm
                    Encryption key:on
          Cell 02 - Address: 11:22:33:44:55:66
                    ESSID:"GuestNetwork"
                    Mode:Master
                    Frequency:5.180 GHz (Channel 36)
                    Quality=50/70  Signal level=-60 dBm
                    Encryption key:off"""

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(iwlist_output, b""))
            mock_subprocess.return_value = mock_process

            original_dev = Config.IS_DEVELOPMENT
            Config.IS_DEVELOPMENT = False

            try:
                networks = await WiFiManager.scan_networks()

                # Should find 2 networks
                assert len(networks) >= 2

                # Check network details (networks are WiFiNetwork Pydantic models)
                network_names = [n.ssid for n in networks]
                assert "HomeNetwork" in network_names
                assert "GuestNetwork" in network_names

            finally:
                Config.IS_DEVELOPMENT = original_dev

    @pytest.mark.asyncio
    async def test_scan_networks_failure(self):
        """Test WiFi scanning failure"""

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(
                return_value=(b"", b"Operation not permitted")
            )
            mock_subprocess.return_value = mock_process

            original_dev = Config.IS_DEVELOPMENT
            Config.IS_DEVELOPMENT = False

            try:
                with pytest.raises(Exception) as exc_info:
                    await WiFiManager.scan_networks()

                assert "WiFi scan failed" in str(exc_info.value)

            finally:
                Config.IS_DEVELOPMENT = original_dev


class TestWiFiRoutes:
    """Test WiFi API endpoints"""

    @pytest_asyncio.fixture
    async def client(self):
        """Create test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_connect_wifi_endpoint_success(self, client):
        """Test /wifi/connect endpoint with valid credentials"""

        with (
            patch.object(WiFiManager, "connect_network", return_value=True),
            patch.object(WiFiManager, "switch_to_client_mode", new_callable=AsyncMock),
        ):
            response = await client.post(
                "/wifi/connect", json={"ssid": "TestNetwork", "password": "testpass123"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "configured" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_connect_wifi_endpoint_failure(self, client):
        """Test /wifi/connect endpoint with connection failure"""

        with patch.object(WiFiManager, "connect_network", return_value=False):
            response = await client.post(
                "/wifi/connect",
                json={"ssid": "TestNetwork", "password": "wrongpassword"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "failed" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_connect_wifi_endpoint_mode_switch_failure(self, client):
        """Test /wifi/connect endpoint when mode switch fails"""

        async def mock_switch_failure():
            raise Exception("Failed to switch mode")

        with (
            patch.object(WiFiManager, "connect_network", return_value=True),
            patch.object(
                WiFiManager, "switch_to_client_mode", side_effect=mock_switch_failure
            ),
        ):
            response = await client.post(
                "/wifi/connect", json={"ssid": "TestNetwork", "password": "password"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "switch mode" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_get_wifi_status_endpoint(self, client):
        """Test /wifi/status endpoint"""

        mock_status = SystemStatus(
            mode="client",
            connected=True,
            ssid="HomeNetwork",
            ip_address="192.168.1.100",
        )

        with patch.object(WiFiManager, "get_status", return_value=mock_status):
            response = await client.get("/wifi/status")

            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            data = result["data"]
            assert data["mode"] == "client"
            assert data["connected"] is True
            assert data["ssid"] == "HomeNetwork"

    @pytest.mark.asyncio
    async def test_scan_wifi_endpoint(self, client):
        """Test /wifi/scan endpoint"""

        from main import WiFiNetwork

        mock_networks = [
            WiFiNetwork(ssid="Network1", signal=-50, encryption="WPA2"),
            WiFiNetwork(ssid="Network2", signal=-70, encryption="Open"),
        ]

        with patch.object(WiFiManager, "scan_networks", return_value=mock_networks):
            response = await client.post("/wifi/scan")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2

    @pytest.mark.asyncio
    async def test_scan_wifi_endpoint_failure(self, client):
        """Test /wifi/scan endpoint failure"""

        async def mock_scan_failure():
            raise Exception("Scan failed")

        with patch.object(WiFiManager, "scan_networks", side_effect=mock_scan_failure):
            response = await client.post("/wifi/scan")

            # Endpoint raises HTTPException with 500 status on error
            assert response.status_code == 500


class TestWiFiConnectionLoss:
    """Test scenarios when WiFi connection is lost"""

    @pytest.mark.asyncio
    async def test_detect_connection_loss(self):
        """Test detection of lost WiFi connection"""

        # Simulate connected then disconnected
        connected_output = b'wlan0     IEEE 802.11  ESSID:"HomeNetwork"\n                  Access Point: AA:BB:CC:DD:EE:FF'
        disconnected_output = b"wlan0     IEEE 802.11  ESSID:off/any\n                  Access Point: Not-Associated"

        with (
            patch.object(Path, "exists", return_value=False),
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
        ):
            original_dev = Config.IS_DEVELOPMENT
            Config.IS_DEVELOPMENT = False

            try:
                # First check - connected
                mock_process = AsyncMock()
                mock_process.returncode = 0
                mock_process.communicate = AsyncMock(
                    return_value=(connected_output, b"")
                )
                mock_subprocess.return_value = mock_process

                status1 = await WiFiManager.get_status()
                assert status1.connected is True
                assert status1.ssid == "HomeNetwork"

                # Second check - disconnected (connection lost)
                mock_process2 = AsyncMock()
                mock_process2.returncode = 0
                mock_process2.communicate = AsyncMock(
                    return_value=(disconnected_output, b"")
                )
                mock_subprocess.return_value = mock_process2

                status2 = await WiFiManager.get_status()
                assert status2.connected is False
                assert status2.ssid is None

            finally:
                Config.IS_DEVELOPMENT = original_dev

    @pytest.mark.asyncio
    async def test_reconnect_after_connection_loss(self):
        """Test reconnection attempt after losing WiFi"""

        credentials = WiFiCredentials(ssid="HomeNetwork", password="password123")

        with (
            patch("pathlib.Path.write_text"),
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
        ):
            # Simulate successful reconnection
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_subprocess.return_value = mock_process

            original_dev = Config.IS_DEVELOPMENT
            Config.IS_DEVELOPMENT = False

            try:
                # Attempt reconnection
                result = await WiFiManager.connect_network(credentials)
                assert result is True

            finally:
                Config.IS_DEVELOPMENT = original_dev


class TestWiFiCredentialsValidation:
    """Test WiFi credentials validation"""

    @pytest_asyncio.fixture
    async def client(self):
        """Create test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_connect_missing_ssid(self, client):
        """Test connection attempt with missing SSID"""

        response = await client.post("/wifi/connect", json={"password": "password123"})

        # Should return validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_connect_empty_ssid(self, client):
        """Test connection attempt with empty SSID"""

        response = await client.post(
            "/wifi/connect", json={"ssid": "", "password": "password123"}
        )

        # Should return validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_connect_with_special_characters(self, client):
        """Test connection with special characters in credentials"""

        with (
            patch.object(WiFiManager, "connect_network", return_value=True),
            patch.object(WiFiManager, "switch_to_client_mode", new_callable=AsyncMock),
        ):
            response = await client.post(
                "/wifi/connect",
                json={"ssid": "Network-2.4GHz_5G", "password": "p@ssw0rd!#$"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
