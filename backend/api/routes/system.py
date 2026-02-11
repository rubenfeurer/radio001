"""
System API Routes for System Metrics and Status.

This module provides endpoints for system-level information including:
- CPU, memory, and disk usage
- System uptime
- WiFi status and network information
- Service health checks
"""

import logging
import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# Global WiFi manager instance (set from main.py)
wifi_manager = None


def set_system_wifi_manager(manager):
    """Set the WiFi manager instance for system routes"""
    global wifi_manager
    wifi_manager = manager
    logger.info("WiFi manager set in system routes")


class SystemMetrics(BaseModel):
    """System metrics including CPU, memory, and uptime"""

    hostname: str = Field(..., description="System hostname")
    uptime: int = Field(..., description="System uptime in seconds")
    memory: Dict[str, int] = Field(..., description="Memory usage in bytes")
    cpu: Dict[str, float] = Field(..., description="CPU metrics")
    network: Dict[str, Any] = Field(..., description="Network status")
    services: Dict[str, bool] = Field(
        default_factory=dict, description="Service status"
    )


async def get_system_metrics() -> Dict[str, Any]:
    """
    Get comprehensive system metrics.

    Returns:
        Dict containing hostname, uptime, memory, CPU, and network info
    """
    metrics = {
        "hostname": "radio",
        "uptime": 0,
        "memory": {"total": 0, "used": 0, "free": 0},
        "cpu": {"load": 0.0, "temperature": None},
        "network": {
            "wifi": {
                "wifiInterface": "wlan0",
                "status": "disconnected",
                "ssid": None,
                "ip": None,
                "signal": None,
                "mode": "client",
            }
        },
        "services": {},
    }

    try:
        # Get hostname
        with open("/etc/hostname", "r") as f:
            metrics["hostname"] = f.read().strip()
    except Exception as e:
        logger.warning(f"Could not read hostname: {e}")

    try:
        # Get uptime
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.read().split()[0])
            metrics["uptime"] = int(uptime_seconds)
    except Exception as e:
        logger.warning(f"Could not read uptime: {e}")

    try:
        # Get memory info
        with open("/proc/meminfo", "r") as f:
            meminfo = {}
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().split()[0]  # Get value in kB
                    meminfo[key] = int(value) * 1024  # Convert to bytes

            metrics["memory"] = {
                "total": meminfo.get("MemTotal", 0),
                "free": meminfo.get("MemAvailable", meminfo.get("MemFree", 0)),
                "used": meminfo.get("MemTotal", 0)
                - meminfo.get("MemAvailable", meminfo.get("MemFree", 0)),
            }
    except Exception as e:
        logger.warning(f"Could not read memory info: {e}")

    try:
        # Get CPU load (1-minute load average)
        with open("/proc/loadavg", "r") as f:
            load_avg = float(f.read().split()[0])
            # Convert to percentage (assuming 4 cores for Pi)
            cpu_count = os.cpu_count() or 4
            metrics["cpu"]["load"] = min(100.0, (load_avg / cpu_count) * 100)
    except Exception as e:
        logger.warning(f"Could not read CPU load: {e}")

    try:
        # Get CPU temperature (Raspberry Pi specific)
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_millidegrees = int(f.read().strip())
            metrics["cpu"]["temperature"] = temp_millidegrees / 1000.0
    except Exception as e:
        logger.debug(f"Could not read CPU temperature: {e}")

    # Get WiFi status (import here to avoid circular dependency)
    try:
        import os
        from pathlib import Path

        from core.wifi_manager import WiFiManager

        # Get the wifi_manager instance from main
        # Since we can't import wifi_manager from main directly, create a temporary instance
        wifi_mgr = WiFiManager(
            interface=os.getenv("WIFI_INTERFACE", "wlan0"),
            host_mode_file=Path("/etc/raspiwifi/host_mode"),
            development_mode=os.getenv("NODE_ENV") == "development",
        )
        wifi_status = await wifi_mgr.get_status()

        metrics["network"]["wifi"] = {
            "wifiInterface": "wlan0",
            "status": "connected" if wifi_status.connected else "disconnected",
            "ssid": wifi_status.ssid,
            "ip": wifi_status.ip_address,
            "signal": wifi_status.signal_strength,
            "mode": wifi_status.mode,
        }
    except Exception as e:
        logger.warning(f"Could not get WiFi status: {e}")

    return metrics


@router.get("/status", response_model=SystemMetrics, summary="Get system status")
async def get_system_status():
    """
    Get comprehensive system status including CPU, memory, network, and uptime.

    Returns:
        SystemMetrics: Complete system metrics
    """
    try:
        metrics = await get_system_metrics()
        return SystemMetrics(**metrics)
    except Exception as e:
        logger.error(f"Error getting system status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get system status: {str(e)}"
        )


@router.get("/health", summary="Health check")
async def health_check():
    """
    Quick health check endpoint.

    Returns:
        Dict: Basic health status
    """
    return {"status": "healthy", "service": "radio-system"}


class ApiResponse(BaseModel):
    """Standard API response"""

    success: bool
    message: str
    data: Any = None


@router.post(
    "/hotspot-mode", response_model=ApiResponse, summary="Switch to hotspot mode"
)
async def activate_hotspot_mode():
    """
    Reset system to hotspot mode for WiFi reconfiguration.

    This will:
    1. Create the host mode marker file
    2. Disconnect from current WiFi network
    3. Start hotspot via nmcli

    Returns:
        ApiResponse: Success status and message
    """
    global wifi_manager

    if wifi_manager is None:
        # Fallback: create temporary instance if not set
        from pathlib import Path

        from core.wifi_manager import WiFiManager

        wifi_manager = WiFiManager(
            interface=os.getenv("WIFI_INTERFACE", "wlan0"),
            host_mode_file=Path("/etc/raspiwifi/host_mode"),
            development_mode=os.getenv("NODE_ENV") == "development",
            hotspot_ssid=os.getenv("HOTSPOT_SSID", "Radio-Setup"),
            hotspot_password=os.getenv("HOTSPOT_PASSWORD", "Configure123!"),
            hotspot_ip=os.getenv("HOTSPOT_IP", "192.168.4.1"),
        )

    try:
        logger.info("Initiating system reset to hotspot mode...")
        await wifi_manager.switch_to_host_mode()

        return ApiResponse(
            success=True,
            message="Hotspot mode activated. Connect to 'Radio-Setup' WiFi network.",
            data={
                "action": "hotspot_activated",
                "mode": "hotspot",
                "instructions": "Connect to 'Radio-Setup' WiFi and navigate to http://192.168.4.1",
            },
        )
    except Exception as e:
        logger.error(f"Failed to reset to hotspot mode: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reset system: {str(e)}")
