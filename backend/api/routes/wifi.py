"""
WiFi Management API Routes

Handles all WiFi-related endpoints using the WiFiManager module.
"""

import logging
from typing import Any

from core import WiFiCredentials, WiFiManager
from core.models import ApiResponse
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Global WiFi manager instance (initialized in main.py)
wifi_manager: WiFiManager = None


def set_wifi_manager(manager: WiFiManager):
    """Set the global WiFi manager instance"""
    global wifi_manager
    wifi_manager = manager
    logger.info("WiFi manager set in routes")



@router.get("/status", response_model=ApiResponse, tags=["WiFi"])
async def get_wifi_status():
    """Get current WiFi connection status"""
    try:
        status = await wifi_manager.get_status()
        return ApiResponse(
            success=True, message="WiFi status retrieved", data=status.to_dict()
        )
    except Exception as e:
        logger.error(f"Error getting WiFi status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan", response_model=ApiResponse, tags=["WiFi"])
async def scan_wifi_networks():
    """Scan for available WiFi networks"""
    try:
        networks = await wifi_manager.scan_networks()
        return ApiResponse(
            success=True,
            message=f"Found {len(networks)} networks",
            data=[network.to_dict() for network in networks],
        )
    except Exception as e:
        logger.error(f"Error scanning WiFi networks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect", response_model=ApiResponse, tags=["WiFi"])
async def connect_wifi(credentials: WiFiCredentials):
    """
    Connect to WiFi network (single attempt - user can manually retry).

    Validates connection before switching from hotspot to client mode.
    Returns success only if connection verified.
    """
    logger.info(f"Attempting to connect to WiFi: {credentials.ssid}")
    logger.debug(
        f"Password provided: {'Yes' if credentials.password else 'No (empty)'}"
    )

    # Attempt connection (validates before mode switch)
    success, error_message = await wifi_manager.connect_network(
        credentials.ssid, credentials.password
    )

    if not success:
        logger.error(f"Failed to connect to {credentials.ssid}: {error_message}")
        return ApiResponse(
            success=False,
            message=f"Failed to connect to '{credentials.ssid}': {error_message}",
            data={
                "ssid": credentials.ssid,
                "timeout": 40,
                "error": error_message,
            },
        )

    # Connection successful - switch to client mode (stops hotspot if active)
    try:
        logger.info(f"Connection verified. Switching to client mode...")
        await wifi_manager.switch_to_client_mode()

        return ApiResponse(
            success=True,
            message=f"Connected to '{credentials.ssid}' successfully.",
            data={
                "ssid": credentials.ssid,
                "instructions": "Connected to WiFi. Access via http://radio.local:8000",
            },
        )
    except Exception as e:
        logger.error(f"Mode switch failed: {e}", exc_info=True)
        return ApiResponse(
            success=False,
            message=f"Connected to WiFi but mode switch failed: {str(e)}",
            data={"ssid": credentials.ssid},
        )


@router.get("/saved", response_model=ApiResponse, tags=["WiFi"])
async def get_saved_networks():
    """Get list of saved WiFi networks from NetworkManager"""
    try:
        networks = await wifi_manager.list_saved_networks()
        return ApiResponse(
            success=True,
            message=f"Found {len(networks)} saved networks",
            data={"networks": networks},
        )
    except Exception as e:
        logger.error(f"Failed to get saved networks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/saved/{connection_name:path}", response_model=ApiResponse, tags=["WiFi"])
async def forget_saved_network(connection_name: str):
    """
    Forget/remove a saved WiFi network.

    Keyed by the stable NetworkManager connection name (URL-encoded by the
    client) — a positional id resolves to the wrong profile if the list
    changes between enumeration and deletion.

    Args:
        connection_name: NM connection name from the saved networks list
    """
    try:
        # Check if network exists (single enumeration in the manager would
        # suffice, but a 404 needs distinguishing from a delete failure)
        saved_networks = await wifi_manager.list_saved_networks()
        network = next(
            (n for n in saved_networks if n["connection_name"] == connection_name),
            None,
        )

        if not network:
            raise HTTPException(
                status_code=404, detail=f"No saved network named {connection_name!r}"
            )

        # Remove network
        success = await wifi_manager.forget_network(connection_name)

        if success:
            return ApiResponse(
                success=True, message=f"Successfully forgot network: {network['ssid']}"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to remove network")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forgetting network {connection_name!r}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
