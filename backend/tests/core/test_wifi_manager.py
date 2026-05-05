"""
Unit tests for WiFi Manager (nmcli-based).

Tests WiFi management functionality using NetworkManager:
- Network scanning
- Connection management
- Status checking
- Saved networks management
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.wifi_manager import WiFiManager, WiFiNetwork, WiFiStatus


class TestWiFiManagerScanning:
    """Test WiFi network scanning functionality"""

    @pytest.mark.asyncio
    async def test_scan_networks_development_mode(self):
        """Test network scanning in development mode returns mock data"""
        manager = WiFiManager(development_mode=True)

        networks = await manager.scan_networks()

        assert len(networks) == 3
        assert networks[0].ssid == "HomeWiFi"
        assert networks[0].signal == 75
        assert networks[0].encryption == "WPA2"

    @pytest.mark.asyncio
    async def test_scan_networks_with_nmcli(self):
        """Test network scanning with nmcli subprocess"""
        manager = WiFiManager(development_mode=False)

        # Mock nmcli output
        nmcli_output = """HomeWiFi:75:WPA2:2412 MHz
GuestNetwork:60::5180 MHz
NeighborWiFi:45:WPA3:2437 MHz"""

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock rescan command
            mock_rescan = AsyncMock()
            mock_rescan.returncode = 0
            mock_rescan.communicate = AsyncMock(return_value=(b"", b""))

            # Mock list command
            mock_list = AsyncMock()
            mock_list.returncode = 0
            mock_list.communicate = AsyncMock(return_value=(nmcli_output.encode(), b""))

            # Return rescan then list
            mock_subprocess.side_effect = [mock_rescan, mock_list]

            networks = await manager.scan_networks()

            assert len(networks) == 3
            assert networks[0].ssid == "HomeWiFi"
            assert networks[0].signal == 75
            assert networks[0].encryption == "WPA2"
            assert networks[1].encryption == "Open"  # Empty security
            assert networks[2].encryption == "WPA3"

    @pytest.mark.asyncio
    async def test_scan_networks_handles_duplicates(self):
        """Test that duplicate SSIDs are filtered"""
        manager = WiFiManager(development_mode=False)

        # Mock nmcli output with duplicate SSIDs
        nmcli_output = """HomeWiFi:75:WPA2:2412 MHz
HomeWiFi:60:WPA2:2412 MHz
GuestNetwork:50::5180 MHz"""

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_rescan = AsyncMock()
            mock_rescan.returncode = 0
            mock_rescan.communicate = AsyncMock(return_value=(b"", b""))

            mock_list = AsyncMock()
            mock_list.returncode = 0
            mock_list.communicate = AsyncMock(return_value=(nmcli_output.encode(), b""))

            mock_subprocess.side_effect = [mock_rescan, mock_list]

            networks = await manager.scan_networks()

            # Should only have 2 unique SSIDs
            assert len(networks) == 2
            ssids = [n.ssid for n in networks]
            assert "HomeWiFi" in ssids
            assert "GuestNetwork" in ssids


class TestWiFiManagerStatus:
    """Test WiFi status checking functionality"""

    @pytest.mark.asyncio
    async def test_get_status_development_mode(self):
        """Test status in development mode"""
        manager = WiFiManager(development_mode=True)

        status = await manager.get_status()

        assert status.mode == "host"
        assert status.connected is False
        assert status.ssid == "Radio-Setup"
        assert status.ip_address == "192.168.4.1"

    @pytest.mark.asyncio
    async def test_get_status_host_mode(self):
        """Test status when in host mode"""
        host_mode_file = Path("/tmp/test_host_mode")
        manager = WiFiManager(development_mode=False, host_mode_file=host_mode_file)

        try:
            host_mode_file.touch()

            status = await manager.get_status()

            assert status.mode == "host"
            assert status.connected is True
            assert status.ssid == "Radio-Setup"
        finally:
            if host_mode_file.exists():
                host_mode_file.unlink()

    @pytest.mark.asyncio
    async def test_get_status_connected_client(self):
        """Test status when connected as client"""
        manager = WiFiManager(
            development_mode=False, host_mode_file=Path("/tmp/nonexistent")
        )

        # get_status makes multiple nmcli calls:
        # 1. `nmcli -t -f TYPE,STATE,CONNECTION device status`
        # 2. `nmcli -t -f IN-USE,SSID device wifi list` (to resolve SSID)
        # 3. `nmcli -t -f IP4.ADDRESS connection show <name>` (for IP)
        # 4. `nmcli -t -f IN-USE,SIGNAL,SSID device wifi list` (for signal)
        device_status = "wifi:connected:HomeWiFi"
        wifi_list = "*:HomeWiFi"

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_device = AsyncMock()
            mock_device.returncode = 0
            mock_device.communicate = AsyncMock(
                return_value=(device_status.encode(), b"")
            )

            mock_wifi_list = AsyncMock()
            mock_wifi_list.returncode = 0
            mock_wifi_list.communicate = AsyncMock(
                return_value=(wifi_list.encode(), b"")
            )

            mock_ip = AsyncMock()
            mock_ip.returncode = 0
            mock_ip.communicate = AsyncMock(return_value=(b"", b""))

            mock_signal = AsyncMock()
            mock_signal.returncode = 0
            mock_signal.communicate = AsyncMock(return_value=(b"", b""))

            mock_subprocess.side_effect = [mock_device, mock_wifi_list, mock_ip, mock_signal]

            status = await manager.get_status()

            assert status.mode == "client"
            assert status.connected is True
            assert status.ssid == "HomeWiFi"


class TestWiFiManagerConnection:
    """Test WiFi connection functionality"""

    @pytest.mark.asyncio
    async def test_connect_new_network(self):
        """Test connecting to a new WiFi network"""
        manager = WiFiManager(development_mode=False)

        with (
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
            patch.object(
                manager, "wait_for_connection", return_value=True
            ) as mock_wait,
        ):
            # Mock connection list (network doesn't exist)
            mock_list = AsyncMock()
            mock_list.returncode = 0
            mock_list.communicate = AsyncMock(return_value=(b"", b""))

            # Mock connect command
            mock_connect = AsyncMock()
            mock_connect.returncode = 0
            mock_connect.communicate = AsyncMock(
                return_value=(b"Connection successfully activated", b"")
            )

            mock_subprocess.side_effect = [mock_list, mock_connect]

            result = await manager.connect_network("TestNetwork", "testpass123")

            assert result[0] is True
            mock_wait.assert_called_once_with("TestNetwork", timeout=40)

    @pytest.mark.asyncio
    async def test_connect_existing_network(self):
        """Test reconnecting to an existing saved network"""
        manager = WiFiManager(development_mode=False)

        with (
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
            patch.object(
                manager, "wait_for_connection", return_value=True
            ) as mock_wait,
        ):
            # Mock connection list (network exists)
            mock_list = AsyncMock()
            mock_list.returncode = 0
            mock_list.communicate = AsyncMock(
                return_value=(b"TestNetwork\nOtherNetwork", b"")
            )

            # Mock modify command
            mock_modify = AsyncMock()
            mock_modify.returncode = 0
            mock_modify.communicate = AsyncMock(return_value=(b"", b""))

            # Mock connection up command
            mock_up = AsyncMock()
            mock_up.returncode = 0
            mock_up.communicate = AsyncMock(
                return_value=(b"Connection successfully activated", b"")
            )

            mock_subprocess.side_effect = [mock_list, mock_modify, mock_up]

            result = await manager.connect_network("TestNetwork", "newpass456")

            assert result[0] is True

    @pytest.mark.asyncio
    async def test_connect_open_network(self):
        """Test connecting to an open network (no password)"""
        manager = WiFiManager(development_mode=False)

        with (
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
            patch.object(manager, "wait_for_connection", return_value=True),
        ):
            mock_list = AsyncMock()
            mock_list.returncode = 0
            mock_list.communicate = AsyncMock(return_value=(b"", b""))

            mock_connect = AsyncMock()
            mock_connect.returncode = 0
            mock_connect.communicate = AsyncMock(
                return_value=(b"Connection successfully activated", b"")
            )

            mock_subprocess.side_effect = [mock_list, mock_connect]

            result = await manager.connect_network("OpenNetwork", "")

            assert result[0] is True

    @pytest.mark.asyncio
    async def test_connect_with_retry(self):
        """Test that a failed wait_for_connection returns a failure tuple"""
        manager = WiFiManager(development_mode=False)

        with (
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
            patch.object(manager, "wait_for_connection", return_value=False),
        ):
            mock_list = AsyncMock()
            mock_list.returncode = 0
            mock_list.communicate = AsyncMock(return_value=(b"", b""))

            mock_connect = AsyncMock()
            mock_connect.returncode = 0
            mock_connect.communicate = AsyncMock(return_value=(b"", b""))

            mock_subprocess.side_effect = [mock_list, mock_connect]

            result = await manager.connect_network("TestNetwork", "testpass")

            assert result[0] is False
            assert "timeout" in result[1].lower() or "incorrect" in result[1].lower()


class TestWiFiManagerSavedNetworks:
    """Test saved networks management"""

    @pytest.mark.asyncio
    async def test_list_saved_networks(self):
        """Test listing saved WiFi networks"""
        manager = WiFiManager(development_mode=False)

        # Mock current status
        with patch.object(manager, "get_status") as mock_status:
            mock_status.return_value = WiFiStatus(
                mode="client", connected=True, ssid="HomeWiFi"
            )

            # list_saved_networks calls `nmcli -t -f NAME,TYPE connection show`
            # then per WiFi entry calls `nmcli -t -f 802-11-wireless.ssid connection show <name>`
            # Format: NAME:TYPE (only two fields requested)
            connection_list = "HomeWiFi:802-11-wireless\nGuestWiFi:802-11-wireless\nEthernet:802-3-ethernet"

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_list = AsyncMock()
                mock_list.returncode = 0
                mock_list.communicate = AsyncMock(
                    return_value=(connection_list.encode(), b"")
                )

                mock_detail_home = AsyncMock()
                mock_detail_home.returncode = 0
                mock_detail_home.communicate = AsyncMock(
                    return_value=(b"802-11-wireless.ssid:HomeWiFi", b"")
                )

                mock_detail_guest = AsyncMock()
                mock_detail_guest.returncode = 0
                mock_detail_guest.communicate = AsyncMock(
                    return_value=(b"802-11-wireless.ssid:GuestWiFi", b"")
                )

                mock_subprocess.side_effect = [mock_list, mock_detail_home, mock_detail_guest]

                networks = await manager.list_saved_networks()

                assert len(networks) == 2  # Only WiFi connections
                assert networks[0]["ssid"] == "HomeWiFi"
                assert networks[0]["current"] is True
                assert networks[1]["ssid"] == "GuestWiFi"
                assert networks[1]["current"] is False

    @pytest.mark.asyncio
    async def test_forget_network(self):
        """Test forgetting a saved network"""
        manager = WiFiManager(development_mode=False)

        with (
            patch.object(manager, "list_saved_networks") as mock_list,
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
        ):
            # Mock saved networks
            mock_list.return_value = [
                {"id": 0, "ssid": "HomeWiFi", "current": False},
                {"id": 1, "ssid": "GuestWiFi", "current": False},
            ]

            # Mock delete command
            mock_delete = AsyncMock()
            mock_delete.returncode = 0
            mock_delete.communicate = AsyncMock(
                return_value=(b"Connection deleted", b"")
            )
            mock_subprocess.return_value = mock_delete

            result = await manager.forget_network(1)

            assert result is True

    @pytest.mark.asyncio
    async def test_forget_current_network_fails(self):
        """Test that forgetting the current network is prevented"""
        manager = WiFiManager(development_mode=False)

        with patch.object(manager, "list_saved_networks") as mock_list:
            mock_list.return_value = [{"id": 0, "ssid": "HomeWiFi", "current": True}]

            result = await manager.forget_network(0)

            assert result is False


class TestWiFiManagerHelpers:
    """Test helper methods"""

    @pytest.mark.asyncio
    async def test_wait_for_connection_success(self):
        """Test waiting for connection succeeds"""
        manager = WiFiManager(development_mode=False)

        # Mock nmcli showing connected status
        device_status = "wlan0:connected:TestNetwork"

        with (
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
            patch("asyncio.sleep"),
        ):  # Speed up test
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(
                return_value=(device_status.encode(), b"")
            )
            mock_subprocess.return_value = mock_process

            result = await manager.wait_for_connection("TestNetwork", timeout=5)

            assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_connection_timeout(self):
        """Test waiting for connection times out"""
        manager = WiFiManager(development_mode=False)

        # Mock nmcli showing disconnected status
        device_status = "wlan0:disconnected:"

        with (
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
            patch("asyncio.sleep"),
        ):  # Speed up test
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(
                return_value=(device_status.encode(), b"")
            )
            mock_subprocess.return_value = mock_process

            result = await manager.wait_for_connection("TestNetwork", timeout=1)

            assert result is False
