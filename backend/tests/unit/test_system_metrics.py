"""
Unit tests for system metrics WiFi manager reuse.

Regression: get_system_metrics constructed a throwaway WiFiManager
(~4 nmcli subprocesses) on every 5 s metrics tick instead of using the
instance injected via set_system_wifi_manager().
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.routes import system as system_routes

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def restore_injection():
    original = system_routes.wifi_manager
    yield
    system_routes.wifi_manager = original


@pytest.mark.unit
class TestMetricsWifiManagerReuse:
    async def test_injected_manager_is_used(self):
        injected = MagicMock()
        injected.interface = "wlan0"
        injected.get_status = AsyncMock(return_value=MagicMock(
            connected=True, ssid="HomeWiFi", ip_address="192.168.1.10",
            signal_strength=70, mode="client",
        ))
        system_routes.set_system_wifi_manager(injected)

        with patch("core.wifi_manager.WiFiManager") as ctor:
            metrics = await system_routes.get_system_metrics()

        injected.get_status.assert_awaited_once()
        ctor.assert_not_called()
        assert metrics["network"]["wifi"]["ssid"] == "HomeWiFi"
        assert metrics["network"]["wifi"]["status"] == "connected"

    async def test_metrics_without_injected_manager(self):
        system_routes.wifi_manager = None

        with patch("core.wifi_manager.WiFiManager") as ctor:
            metrics = await system_routes.get_system_metrics()

        ctor.assert_not_called()
        # The template's default wifi block remains untouched
        assert metrics["network"]["wifi"]["status"] == "disconnected"
        assert metrics["network"]["wifi"]["ssid"] is None
