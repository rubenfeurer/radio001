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

pytestmark = pytest.mark.asyncio

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
    """Test WiFi connection functionality.

    The PSK must never appear in nmcli argv (passwd-file mechanism) and
    SSIDs are only passed as the value after the `ssid` property keyword.
    """

    @staticmethod
    def _spawn_recorder(calls, psk_files):
        """Return a create_subprocess_exec side effect that records argv and
        inspects any passwd-file at call time (perms + existence)."""
        import os
        import stat

        async def spawn(*args, **kwargs):
            calls.append(args)
            if "passwd-file" in args:
                path = args[args.index("passwd-file") + 1]
                st = os.stat(path)
                psk_files.append({
                    "path": path,
                    "mode": stat.S_IMODE(st.st_mode),
                    "content": open(path).read(),
                })
            proc = AsyncMock()
            proc.returncode = 0
            proc.communicate = AsyncMock(return_value=(b"", b""))
            return proc

        return spawn

    @pytest.mark.asyncio
    async def test_connect_new_network(self):
        """New secured network: connection add + up with passwd-file; PSK not in argv"""
        manager = WiFiManager(development_mode=False)
        calls, psk_files = [], []

        with (
            patch.object(manager, "list_saved_networks", AsyncMock(return_value=[])),
            patch("asyncio.create_subprocess_exec",
                  side_effect=self._spawn_recorder(calls, psk_files)),
            patch.object(manager, "wait_for_connection", return_value=True) as mock_wait,
        ):
            result = await manager.connect_network("TestNetwork", "testpass123")

        assert result[0] is True
        mock_wait.assert_called_once_with("TestNetwork", timeout=40)

        # PSK never in any argv
        for args in calls:
            assert "testpass123" not in args

        # SSID only appears as the value after the `ssid` property keyword
        add_call = next(a for a in calls if "add" in a)
        assert add_call[add_call.index("ssid") + 1] == "TestNetwork"
        assert "wifi-sec.key-mgmt" in add_call and "wpa-psk" in add_call

        # passwd-file was 0600, contained the PSK, and is deleted afterwards
        import os
        assert len(psk_files) == 1
        assert psk_files[0]["mode"] == 0o600
        assert psk_files[0]["content"] == "802-11-wireless-security.psk:testpass123\n"
        assert not os.path.exists(psk_files[0]["path"])

    @pytest.mark.asyncio
    async def test_connect_existing_network(self):
        """Saved profile: connection up with passwd-file, no wifi-sec.psk argv"""
        manager = WiFiManager(development_mode=False)
        calls, psk_files = [], []

        with (
            patch.object(manager, "list_saved_networks", AsyncMock(return_value=[
                {"id": 0, "ssid": "TestNetwork", "connection_name": "TestNetwork",
                 "current": False},
            ])),
            patch("asyncio.create_subprocess_exec",
                  side_effect=self._spawn_recorder(calls, psk_files)),
            patch.object(manager, "wait_for_connection", return_value=True),
        ):
            result = await manager.connect_network("TestNetwork", "newpass456")

        assert result[0] is True
        for args in calls:
            assert "newpass456" not in args
            assert "wifi-sec.psk" not in args
        up_call = next(a for a in calls if "up" in a)
        assert "passwd-file" in up_call
        assert len(psk_files) == 1

    @pytest.mark.asyncio
    async def test_connect_open_network(self):
        """Open network: connection add without security, up without passwd-file"""
        manager = WiFiManager(development_mode=False)
        calls, psk_files = [], []

        with (
            patch.object(manager, "list_saved_networks", AsyncMock(return_value=[])),
            patch("asyncio.create_subprocess_exec",
                  side_effect=self._spawn_recorder(calls, psk_files)),
            patch.object(manager, "wait_for_connection", return_value=True),
        ):
            result = await manager.connect_network("OpenNetwork", "")

        assert result[0] is True
        add_call = next(a for a in calls if "add" in a)
        assert add_call[add_call.index("ssid") + 1] == "OpenNetwork"
        assert "wifi-sec.key-mgmt" not in add_call
        assert not psk_files

    @pytest.mark.asyncio
    async def test_connect_with_retry(self):
        """A failed wait_for_connection returns a failure tuple"""
        manager = WiFiManager(development_mode=False)
        calls, psk_files = [], []

        with (
            patch.object(manager, "list_saved_networks", AsyncMock(return_value=[])),
            patch("asyncio.create_subprocess_exec",
                  side_effect=self._spawn_recorder(calls, psk_files)),
            patch.object(manager, "wait_for_connection", return_value=False),
        ):
            result = await manager.connect_network("TestNetwork", "testpass")

        assert result[0] is False
        assert "timeout" in result[1].lower() or "incorrect" in result[1].lower()

    @pytest.mark.asyncio
    async def test_dash_prefixed_ssid_is_position_safe(self):
        """An SSID starting with `-` must only appear after the ssid keyword"""
        manager = WiFiManager(development_mode=False)
        calls, psk_files = [], []

        with (
            patch.object(manager, "list_saved_networks", AsyncMock(return_value=[])),
            patch("asyncio.create_subprocess_exec",
                  side_effect=self._spawn_recorder(calls, psk_files)),
            patch.object(manager, "wait_for_connection", return_value=True),
        ):
            result = await manager.connect_network("-evil-ssid", "testpass123")

        assert result[0] is True
        for args in calls:
            for i, tok in enumerate(args):
                if tok == "-evil-ssid":
                    assert args[i - 1] in ("ssid", "con-name", "delete", "up"), \
                        f"SSID appeared positionally in {args}"

    @pytest.mark.asyncio
    async def test_control_character_ssid_rejected_before_subprocess(self):
        manager = WiFiManager(development_mode=False)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            result = await manager.connect_network("bad\nssid", "pw12345678")

        assert result[0] is False
        mock_subprocess.assert_not_called()

    @pytest.mark.asyncio
    async def test_overlong_and_empty_ssid_rejected(self):
        manager = WiFiManager(development_mode=False)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            assert (await manager.connect_network("s" * 33, "pw12345678"))[0] is False
            assert (await manager.connect_network("", "pw12345678"))[0] is False

        mock_subprocess.assert_not_called()

    @pytest.mark.asyncio
    async def test_failed_activation_deletes_new_profile(self):
        """A new profile whose activation fails must not accumulate"""
        manager = WiFiManager(development_mode=False)
        calls = []

        async def spawn(*args, **kwargs):
            calls.append(args)
            proc = AsyncMock()
            # add succeeds, up fails, delete succeeds
            proc.returncode = 1 if "up" in args else 0
            proc.communicate = AsyncMock(return_value=(b"", b"activation failed"))
            return proc

        with (
            patch.object(manager, "list_saved_networks", AsyncMock(return_value=[])),
            patch("asyncio.create_subprocess_exec", side_effect=spawn),
        ):
            result = await manager.connect_network("TestNetwork", "testpass123")

        assert result[0] is False
        assert any("delete" in a for a in calls)


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
    async def test_forget_network_by_name(self):
        """Forget deletes exactly the named profile (never a positional index)"""
        manager = WiFiManager(development_mode=False)
        calls = []

        async def spawn(*args, **kwargs):
            calls.append(args)
            proc = AsyncMock()
            proc.returncode = 0
            proc.communicate = AsyncMock(return_value=(b"Connection deleted", b""))
            return proc

        with (
            patch.object(manager, "list_saved_networks") as mock_list,
            patch("asyncio.create_subprocess_exec", side_effect=spawn),
        ):
            mock_list.return_value = [
                {"id": 0, "ssid": "HomeWiFi", "connection_name": "HomeWiFi", "current": False},
                {"id": 1, "ssid": "GuestWiFi", "connection_name": "Guest WiFi 5GHz", "current": False},
            ]

            result = await manager.forget_network("Guest WiFi 5GHz")

            assert result is True
            delete_call = next(a for a in calls if "delete" in a)
            assert delete_call[-1] == "Guest WiFi 5GHz"
            # Single enumeration only
            mock_list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_forget_unknown_name_fails_without_delete(self):
        """Unknown connection name returns False and spawns no subprocess"""
        manager = WiFiManager(development_mode=False)

        with (
            patch.object(manager, "list_saved_networks") as mock_list,
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
        ):
            mock_list.return_value = [
                {"id": 0, "ssid": "HomeWiFi", "connection_name": "HomeWiFi", "current": False},
            ]

            result = await manager.forget_network("NoSuchProfile")

            assert result is False
            mock_subprocess.assert_not_called()

    @pytest.mark.asyncio
    async def test_forget_current_network_disconnects_first(self):
        """Forgetting the active network disconnects before deleting"""
        manager = WiFiManager(development_mode=False)
        calls = []

        async def spawn(*args, **kwargs):
            calls.append(args)
            proc = AsyncMock()
            proc.returncode = 0
            proc.communicate = AsyncMock(return_value=(b"", b""))
            return proc

        with (
            patch.object(manager, "list_saved_networks") as mock_list,
            patch("asyncio.create_subprocess_exec", side_effect=spawn),
        ):
            mock_list.return_value = [
                {"id": 0, "ssid": "HomeWiFi", "connection_name": "HomeWiFi", "current": True},
            ]

            result = await manager.forget_network("HomeWiFi")

            assert result is True
            assert any("disconnect" in a for a in calls)
            disconnect_idx = next(i for i, a in enumerate(calls) if "disconnect" in a)
            delete_idx = next(i for i, a in enumerate(calls) if "delete" in a)
            assert disconnect_idx < delete_idx


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
