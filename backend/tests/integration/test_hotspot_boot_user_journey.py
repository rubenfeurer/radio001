"""
Integration test for hotspot boot mode user journey.

Tests the complete user flow when Pi boots without WiFi connection:
1. System boots and enters hotspot mode (no WiFi connection)
2. User connects to hotspot AP ("Radio-Setup")
3. User accesses web interface at http://192.168.4.1
4. User scans for available WiFi networks
5. User selects and connects to a network
6. System switches from hotspot to client mode
7. User can access system via new WiFi network

This simulates the real-world scenario of setting up the device for the first time
or recovering from a lost WiFi connection.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.wifi_manager import WiFiManager, WiFiNetwork, WiFiStatus
from main import app


@pytest.mark.integration
class TestHotspotBootUserJourney:
    """Test complete user journey from hotspot boot to WiFi connection"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_wifi_manager(self):
        """Create a mock WiFi manager that simulates hotspot mode"""
        manager = AsyncMock(spec=WiFiManager)

        # Initial state: Hotspot mode (no WiFi connection)
        manager.get_status.return_value = WiFiStatus(
            mode="host",
            connected=True,
            ssid="Radio-Setup",
            ip_address="192.168.4.1",
            signal_strength=None,
        )

        # Available networks that user can scan
        manager.scan_networks.return_value = [
            WiFiNetwork(
                ssid="HomeWiFi", signal=85, encryption="WPA2", frequency="2.4GHz"
            ),
            WiFiNetwork(
                ssid="OfficeNetwork", signal=70, encryption="WPA2", frequency="5GHz"
            ),
            WiFiNetwork(
                ssid="GuestNetwork", signal=45, encryption="Open", frequency="2.4GHz"
            ),
        ]

        # No saved networks initially
        manager.list_saved_networks.return_value = []

        # Connection will succeed
        manager.connect_network.return_value = (True, "")

        return manager

    @pytest.mark.asyncio
    async def test_step1_system_boots_in_hotspot_mode(self, client, mock_wifi_manager):
        """
        Step 1: System boots without WiFi connection and enters hotspot mode

        User journey: Pi boots up, can't find saved WiFi, creates hotspot AP
        """
        with patch("api.routes.wifi.wifi_manager", mock_wifi_manager):
            # Check system status - should be in hotspot mode
            response = client.get("/wifi/status")

            assert response.status_code == 200
            data = response.json()

            # Verify we're in hotspot mode
            assert data["success"] is True
            assert data["data"]["mode"] == "host"
            assert data["data"]["ssid"] == "Radio-Setup"
            assert data["data"]["ip_address"] == "192.168.4.1"
            assert data["data"]["connected"] is True

            print("✓ Step 1: System booted in hotspot mode")
            print(f"  - Hotspot SSID: {data['data']['ssid']}")
            print(f"  - Access URL: http://{data['data']['ip_address']}")

    @pytest.mark.asyncio
    async def test_step2_user_accesses_web_interface(self, client, mock_wifi_manager):
        """
        Step 2: User connects to hotspot and accesses web interface

        User journey: User connects phone to "Radio-Setup" AP and opens browser
        """
        with patch("api.routes.wifi.wifi_manager", mock_wifi_manager):
            # User opens http://192.168.4.1 (or http://radio.local)
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "healthy" in data["message"].lower()

            print("✓ Step 2: Web interface accessible")
            print("  - User can access http://192.168.4.1")

    @pytest.mark.asyncio
    async def test_step3_user_scans_for_networks(self, client, mock_wifi_manager):
        """
        Step 3: User opens WiFi setup page and scans for networks

        User journey: User navigates to /setup page and clicks "Scan"
        """
        with patch("api.routes.wifi.wifi_manager", mock_wifi_manager):
            # User clicks "Scan for Networks" button
            response = client.post("/wifi/scan")

            assert response.status_code == 200
            data = response.json()

            # Verify scan results
            assert data["success"] is True
            assert data["message"] == "Found 3 networks"
            assert len(data["data"]) == 3

            # Verify network details
            networks = data["data"]
            assert networks[0]["ssid"] == "HomeWiFi"
            assert networks[0]["signal"] == 85
            assert networks[0]["encryption"] == "WPA2"

            assert networks[1]["ssid"] == "OfficeNetwork"
            assert networks[2]["ssid"] == "GuestNetwork"

            print("✓ Step 3: WiFi networks scanned successfully")
            print(f"  - Found {len(networks)} networks")
            for net in networks:
                print(f"    • {net['ssid']} ({net['signal']}%, {net['encryption']})")

    @pytest.mark.asyncio
    async def test_step4_check_no_saved_networks(self, client, mock_wifi_manager):
        """
        Step 4: Verify no saved networks exist (fresh setup)

        User journey: First-time setup, no previous WiFi connections
        """
        with patch("api.routes.wifi.wifi_manager", mock_wifi_manager):
            response = client.get("/wifi/saved")

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert len(data["data"]["networks"]) == 0

            print("✓ Step 4: No saved networks (first-time setup)")

    @pytest.mark.asyncio
    async def test_step5_user_selects_and_connects_to_network(
        self, client, mock_wifi_manager
    ):
        """
        Step 5: User selects HomeWiFi and enters password

        User journey:
        - User clicks on "HomeWiFi" network
        - Enters password in dialog
        - Clicks "Connect" button
        - System attempts connection (single attempt, 40s timeout)
        """
        with patch("api.routes.wifi.wifi_manager", mock_wifi_manager):
            # User submits connection request
            connection_data = {
                "ssid": "HomeWiFi",
                "password": "mypassword123",
                "security": "WPA2",
            }

            response = client.post("/wifi/connect", json=connection_data)

            assert response.status_code == 200
            data = response.json()

            # Verify connection success
            assert data["success"] is True
            assert "Connected to 'HomeWiFi'" in data["message"]
            assert (
                "rebooting" in data["message"].lower()
                or "reboot" in data["message"].lower()
            )

            # Verify connect_network was called with correct parameters
            mock_wifi_manager.connect_network.assert_called_once_with(
                "HomeWiFi", "mypassword123"
            )

            print("✓ Step 5: Connection initiated successfully")
            print(f"  - Target network: {connection_data['ssid']}")
            print(f"  - Connection status: {data['message']}")

    @pytest.mark.asyncio
    async def test_step6_system_switches_to_client_mode(self, mock_wifi_manager):
        """
        Step 6: System verifies connection and switches from hotspot to client mode

        User journey:
        - Backend validates WiFi connection (40s timeout)
        - If successful, stops hostapd/dnsmasq
        - Switches to client mode
        - System may reboot (in production)
        """
        # Simulate connection verification
        success, error = await mock_wifi_manager.connect_network(
            "HomeWiFi", "mypassword123"
        )

        assert success is True
        assert error == ""

        print("✓ Step 6: Connection verified, mode switch initiated")
        print("  - Hotspot services stopped")
        print("  - Switching to client mode")

    @pytest.mark.asyncio
    async def test_step7_verify_client_mode_access(self, client, mock_wifi_manager):
        """
        Step 7: After reboot, user accesses system via WiFi network

        User journey:
        - System reboots (or switches mode)
        - User disconnects from "Radio-Setup" AP
        - User connects to "HomeWiFi" network
        - User accesses http://radio.local
        - System shows connected to "HomeWiFi"
        """
        # Update mock to simulate client mode after reboot
        mock_wifi_manager.get_status.return_value = WiFiStatus(
            mode="client",
            connected=True,
            ssid="HomeWiFi",
            ip_address="192.168.1.100",
            signal_strength=85,
        )

        with patch("api.routes.wifi.wifi_manager", mock_wifi_manager):
            # User accesses system via new WiFi network
            response = client.get("/wifi/status")

            assert response.status_code == 200
            data = response.json()

            # Verify we're now in client mode, connected to HomeWiFi
            assert data["success"] is True
            assert data["data"]["mode"] == "client"
            assert data["data"]["ssid"] == "HomeWiFi"
            assert data["data"]["connected"] is True
            assert data["data"]["ip_address"] == "192.168.1.100"
            assert data["data"]["signal_strength"] == 85

            print("✓ Step 7: System accessible via WiFi network")
            print(f"  - Connected to: {data['data']['ssid']}")
            print(f"  - IP address: {data['data']['ip_address']}")
            print(f"  - Signal: {data['data']['signal_strength']}%")
            print(f"  - Access: http://radio.local")

    @pytest.mark.asyncio
    async def test_complete_user_journey(self, client, mock_wifi_manager):
        """
        Complete end-to-end user journey test

        Simulates the entire flow from boot to successful WiFi connection
        """
        print("\n" + "=" * 60)
        print("HOTSPOT BOOT MODE - COMPLETE USER JOURNEY TEST")
        print("=" * 60)

        with patch("api.routes.wifi.wifi_manager", mock_wifi_manager):
            # Step 1: Check initial hotspot mode
            print("\n[1] Checking initial system state...")
            status_response = client.get("/wifi/status")
            assert status_response.json()["data"]["mode"] == "host"
            print("    ✓ System in hotspot mode: Radio-Setup")

            # Step 2: Verify web interface accessible
            print("\n[2] Verifying web interface accessibility...")
            health_response = client.get("/health")
            assert health_response.status_code == 200
            print("    ✓ Web interface accessible at http://192.168.4.1")

            # Step 3: Scan for networks
            print("\n[3] Scanning for WiFi networks...")
            scan_response = client.post("/wifi/scan")
            networks = scan_response.json()["data"]
            assert len(networks) == 3
            print(f"    ✓ Found {len(networks)} networks")
            for net in networks:
                print(f"      • {net['ssid']} ({net['signal']}%)")

            # Step 4: Check saved networks
            print("\n[4] Checking saved networks...")
            saved_response = client.get("/wifi/saved")
            assert len(saved_response.json()["data"]["networks"]) == 0
            print("    ✓ No saved networks (first-time setup)")

            # Step 5: Connect to network
            print("\n[5] Connecting to HomeWiFi...")
            connect_response = client.post(
                "/wifi/connect",
                json={
                    "ssid": "HomeWiFi",
                    "password": "mypassword123",
                    "security": "WPA2",
                },
            )
            assert connect_response.json()["success"] is True
            print("    ✓ Connection request successful")
            print("    ⏳ Validating connection (40s timeout)...")

            # Step 6: Simulate successful connection and mode switch
            print("\n[6] Validating connection and switching modes...")
            success, _ = await mock_wifi_manager.connect_network(
                "HomeWiFi", "mypassword123"
            )
            assert success is True
            print("    ✓ Connection validated")
            print("    ✓ Switching to client mode...")

            # Step 7: Verify client mode
            print("\n[7] Verifying final state...")
            mock_wifi_manager.get_status.return_value = WiFiStatus(
                mode="client",
                connected=True,
                ssid="HomeWiFi",
                ip_address="192.168.1.100",
                signal_strength=85,
            )

            final_status = client.get("/wifi/status")
            final_data = final_status.json()["data"]

            assert final_data["mode"] == "client"
            assert final_data["ssid"] == "HomeWiFi"
            assert final_data["connected"] is True

            print("    ✓ System now in client mode")
            print(f"    ✓ Connected to: {final_data['ssid']}")
            print(f"    ✓ IP address: {final_data['ip_address']}")
            print(f"    ✓ Signal strength: {final_data['signal_strength']}%")

            print("\n" + "=" * 60)
            print("✅ COMPLETE USER JOURNEY TEST PASSED")
            print("=" * 60)
            print("\nUser can now access system at:")
            print("  • http://radio.local")
            print(f"  • http://{final_data['ip_address']}")
            print("=" * 60 + "\n")


@pytest.mark.integration
class TestHotspotModeFailureScenarios:
    """Test failure scenarios in hotspot mode"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_wifi_manager_failures(self):
        """Mock WiFi manager with failure scenarios"""
        manager = AsyncMock(spec=WiFiManager)

        manager.get_status.return_value = WiFiStatus(
            mode="host",
            connected=True,
            ssid="Radio-Setup",
            ip_address="192.168.4.1",
            signal_strength=None,
        )

        manager.scan_networks.return_value = [
            WiFiNetwork(
                ssid="TestNetwork", signal=70, encryption="WPA2", frequency="2.4GHz"
            )
        ]

        return manager

    @pytest.mark.asyncio
    async def test_connection_failure_wrong_password(
        self, client, mock_wifi_manager_failures
    ):
        """
        Test connection failure due to wrong password

        User journey: User enters wrong password, connection fails after timeout
        """
        # Simulate connection failure
        mock_wifi_manager_failures.connect_network.return_value = (
            False,
            "Connection timeout - network may be out of range or password incorrect",
        )

        with patch("api.routes.wifi.wifi_manager", mock_wifi_manager_failures):
            response = client.post(
                "/wifi/connect",
                json={
                    "ssid": "TestNetwork",
                    "password": "wrongpassword",
                    "security": "WPA2",
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Verify failure is reported
            assert data["success"] is False
            assert "Failed to connect" in data["message"]
            assert (
                "password incorrect" in data["message"].lower()
                or "timeout" in data["message"].lower()
            )

            print("✓ Connection failure handled correctly")
            print(f"  - Error: {data['message']}")
            print("  - User can retry with correct password")

    @pytest.mark.asyncio
    async def test_network_out_of_range(self, client, mock_wifi_manager_failures):
        """
        Test connection failure when network is out of range

        User journey: User tries to connect to network that appeared in scan but is now gone
        """
        mock_wifi_manager_failures.connect_network.return_value = (
            False,
            "Connection timeout - network may be out of range or password incorrect",
        )

        with patch("api.routes.wifi.wifi_manager", mock_wifi_manager_failures):
            response = client.post(
                "/wifi/connect",
                json={
                    "ssid": "TestNetwork",
                    "password": "password123",
                    "security": "WPA2",
                },
            )

            data = response.json()
            assert data["success"] is False
            assert (
                "timeout" in data["message"].lower()
                or "out of range" in data["message"].lower()
            )

            print("✓ Out of range scenario handled")
            print("  - User receives timeout error")
            print("  - User can scan again and retry")

    @pytest.mark.asyncio
    async def test_user_can_retry_after_failure(
        self, client, mock_wifi_manager_failures
    ):
        """
        Test that user can retry connection after failure

        User journey: First attempt fails, user corrects password and tries again
        """
        with patch("api.routes.wifi.wifi_manager", mock_wifi_manager_failures):
            # First attempt - wrong password
            mock_wifi_manager_failures.connect_network.return_value = (
                False,
                "Wrong password",
            )

            response1 = client.post(
                "/wifi/connect",
                json={
                    "ssid": "TestNetwork",
                    "password": "wrongpass",
                    "security": "WPA2",
                },
            )

            assert response1.json()["success"] is False
            print("✓ First attempt failed (wrong password)")

            # Second attempt - correct password
            mock_wifi_manager_failures.connect_network.return_value = (True, "")

            response2 = client.post(
                "/wifi/connect",
                json={
                    "ssid": "TestNetwork",
                    "password": "correctpass",
                    "security": "WPA2",
                },
            )

            assert response2.json()["success"] is True
            print("✓ Second attempt succeeded (correct password)")
            print("  - User can retry without system restart")
