"""
Radio System Control API Routes.

This module provides FastAPI routes for global radio system control:
- GET /status - Get current system status
- POST /volume - Set volume level
- GET /volume - Get current volume
- POST /stop - Stop all playback
- POST /shutdown - Shutdown radio system
- GET /hardware-status - Get hardware component status
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse

from core.models import (
    SystemStatus, VolumeUpdate, ApiResponse,
    PlaybackStatus, HardwareStatus
)
from core.radio_manager import RadioManager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status", response_model=SystemStatus, summary="Get system status")
async def get_system_status():
    """
    Get current radio system status including playback state, volume, and current station.

    Returns:
        SystemStatus: Complete system status information
    """
    try:
        radio_manager = RadioManager.get_instance()
        status = await radio_manager.get_status()
        return status
    except Exception as e:
        logger.error(f"Error getting system status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )


@router.get("/volume", summary="Get current volume")
async def get_volume():
    """
    Get current system volume level.

    Returns:
        Dict: Volume level and related info
    """
    try:
        radio_manager = RadioManager.get_instance()
        current_status = await radio_manager.get_status()

        return {
            "volume": current_status.volume,
            "min_volume": radio_manager._config.MIN_VOLUME,
            "max_volume": radio_manager._config.MAX_VOLUME,
            "is_muted": current_status.volume == 0
        }
    except Exception as e:
        logger.error(f"Error getting volume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve volume"
        )


@router.post("/volume", response_model=ApiResponse, summary="Set volume level")
async def set_volume(volume_update: VolumeUpdate, background_tasks: BackgroundTasks):
    """
    Set system volume level.

    Args:
        volume_update: Volume update request with new volume level
        background_tasks: FastAPI background tasks for async operations

    Returns:
        ApiResponse: Success/failure status with new volume level
    """
    try:
        radio_manager = RadioManager.get_instance()

        # Validate volume range
        if volume_update.volume < 0 or volume_update.volume > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Volume must be between 0 and 100"
            )

        # Apply hardware limits
        min_vol = radio_manager._config.MIN_VOLUME
        max_vol = radio_manager._config.MAX_VOLUME

        if volume_update.volume > 0 and volume_update.volume < min_vol:
            actual_volume = min_vol
            logger.info(f"Volume {volume_update.volume} below minimum, setting to {min_vol}")
        elif volume_update.volume > max_vol:
            actual_volume = max_vol
            logger.info(f"Volume {volume_update.volume} above maximum, setting to {max_vol}")
        else:
            actual_volume = volume_update.volume

        # Set volume in background
        background_tasks.add_task(radio_manager.set_volume, actual_volume)

        logger.info(f"Volume set to {actual_volume}")

        return ApiResponse(
            success=True,
            message=f"Volume set to {actual_volume}",
            data={
                "volume": actual_volume,
                "requested_volume": volume_update.volume,
                "min_volume": min_vol,
                "max_volume": max_vol
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting volume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set volume"
        )


@router.post("/volume/up", response_model=ApiResponse, summary="Increase volume")
async def volume_up(background_tasks: BackgroundTasks):
    """
    Increase volume by one step.

    Args:
        background_tasks: FastAPI background tasks for async operations

    Returns:
        ApiResponse: Success/failure status with new volume level
    """
    try:
        radio_manager = RadioManager.get_instance()
        current_status = await radio_manager.get_status()

        volume_step = radio_manager._config.ROTARY_VOLUME_STEP
        new_volume = min(current_status.volume + volume_step, radio_manager._config.MAX_VOLUME)

        if new_volume != current_status.volume:
            background_tasks.add_task(radio_manager.set_volume, new_volume)
            message = f"Volume increased to {new_volume}"
        else:
            message = f"Volume already at maximum ({new_volume})"

        return ApiResponse(
            success=True,
            message=message,
            data={"volume": new_volume, "change": volume_step}
        )

    except Exception as e:
        logger.error(f"Error increasing volume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to increase volume"
        )


@router.post("/volume/down", response_model=ApiResponse, summary="Decrease volume")
async def volume_down(background_tasks: BackgroundTasks):
    """
    Decrease volume by one step.

    Args:
        background_tasks: FastAPI background tasks for async operations

    Returns:
        ApiResponse: Success/failure status with new volume level
    """
    try:
        radio_manager = RadioManager.get_instance()
        current_status = await radio_manager.get_status()

        volume_step = radio_manager._config.ROTARY_VOLUME_STEP
        min_volume = 0  # Allow muting
        new_volume = max(current_status.volume - volume_step, min_volume)

        if new_volume != current_status.volume:
            background_tasks.add_task(radio_manager.set_volume, new_volume)
            message = f"Volume decreased to {new_volume}"
        else:
            message = f"Volume already at minimum ({new_volume})"

        return ApiResponse(
            success=True,
            message=message,
            data={"volume": new_volume, "change": -volume_step}
        )

    except Exception as e:
        logger.error(f"Error decreasing volume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrease volume"
        )


@router.post("/stop", response_model=ApiResponse, summary="Stop all playback")
async def stop_playback(background_tasks: BackgroundTasks):
    """
    Stop all radio playback.

    Args:
        background_tasks: FastAPI background tasks for async operations

    Returns:
        ApiResponse: Success/failure status
    """
    try:
        radio_manager = RadioManager.get_instance()
        current_status = await radio_manager.get_status()

        if current_status.is_playing:
            background_tasks.add_task(radio_manager.stop_playback)
            message = f"Stopped playback"
            if current_status.current_station_info:
                message += f" of '{current_status.current_station_info.name}'"
        else:
            message = "No playback to stop"

        logger.info(message)

        return ApiResponse(
            success=True,
            message=message,
            data={
                "was_playing": current_status.is_playing,
                "stopped_station": current_status.current_station
            }
        )

    except Exception as e:
        logger.error(f"Error stopping playback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop playback"
        )


@router.get("/playback-status", response_model=PlaybackStatus, summary="Get detailed playback status")
async def get_playback_status():
    """
    Get detailed playback status information.

    Returns:
        PlaybackStatus: Detailed playback state information
    """
    try:
        radio_manager = RadioManager.get_instance()
        system_status = await radio_manager.get_status()

        playback_status = PlaybackStatus(
            state=system_status.playback_state,
            station_slot=system_status.current_station,
            station_name=system_status.current_station_info.name if system_status.current_station_info else None,
            volume=system_status.volume
        )

        return playback_status

    except Exception as e:
        logger.error(f"Error getting playback status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve playback status"
        )


@router.get("/hardware-status", response_model=HardwareStatus, summary="Get hardware status")
async def get_hardware_status():
    """
    Get hardware component status for debugging and monitoring.

    Returns:
        HardwareStatus: Hardware component availability and status
    """
    try:
        radio_manager = RadioManager.get_instance()
        hw_status = radio_manager.get_hardware_status()

        hardware_status = HardwareStatus(
            gpio_available=hw_status.get("gpio_available", False),
            audio_available=hw_status.get("audio_available", False),
            mock_mode=hw_status.get("mock_mode", True),
            button_states=hw_status.get("button_states", {}),
            last_volume_change=hw_status.get("last_volume_change")
        )

        return hardware_status

    except Exception as e:
        logger.error(f"Error getting hardware status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve hardware status"
        )


@router.post("/shutdown", response_model=ApiResponse, summary="Shutdown radio system")
async def shutdown_radio_system(background_tasks: BackgroundTasks):
    """
    Gracefully shutdown the radio system.

    Args:
        background_tasks: FastAPI background tasks for async operations

    Returns:
        ApiResponse: Shutdown confirmation
    """
    try:
        radio_manager = RadioManager.get_instance()

        # Stop playback first
        if (await radio_manager.get_status()).is_playing:
            await radio_manager.stop_playback()

        # Shutdown in background
        background_tasks.add_task(radio_manager.shutdown)

        logger.info("Radio system shutdown initiated")

        return ApiResponse(
            success=True,
            message="Radio system shutdown initiated",
            data={"timestamp": "shutdown_initiated"}
        )

    except Exception as e:
        logger.error(f"Error shutting down radio system: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to shutdown radio system"
        )


# Development/Testing endpoints (only available in mock mode)
@router.post("/dev/simulate-button/{button}", response_model=ApiResponse, summary="Simulate button press (dev only)")
async def simulate_button_press(button: int, background_tasks: BackgroundTasks):
    """
    Simulate a hardware button press for development/testing.
    Only available when running in mock mode.

    Args:
        button: Button number (1, 2, or 3)
        background_tasks: FastAPI background tasks for async operations

    Returns:
        ApiResponse: Simulation result
    """
    try:
        radio_manager = RadioManager.get_instance()

        if not radio_manager._mock_mode:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Simulation endpoints only available in mock mode"
            )

        if button not in [1, 2, 3]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Button must be 1, 2, or 3"
            )

        background_tasks.add_task(radio_manager.simulate_button_press, button)

        logger.info(f"Simulated button {button} press")

        return ApiResponse(
            success=True,
            message=f"Simulated button {button} press",
            data={"button": button, "action": "simulated_press"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error simulating button press: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to simulate button press"
        )


@router.post("/dev/simulate-volume/{change}", response_model=ApiResponse, summary="Simulate volume change (dev only)")
async def simulate_volume_change(change: int, background_tasks: BackgroundTasks):
    """
    Simulate a rotary encoder volume change for development/testing.
    Only available when running in mock mode.

    Args:
        change: Volume change amount (positive for increase, negative for decrease)
        background_tasks: FastAPI background tasks for async operations

    Returns:
        ApiResponse: Simulation result
    """
    try:
        radio_manager = RadioManager.get_instance()

        if not radio_manager._mock_mode:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Simulation endpoints only available in mock mode"
            )

        if abs(change) > 50:  # Reasonable limits for simulation
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Volume change must be between -50 and +50"
            )

        background_tasks.add_task(radio_manager.simulate_volume_change, change)

        logger.info(f"Simulated volume change: {change}")

        return ApiResponse(
            success=True,
            message=f"Simulated volume change: {change}",
            data={"change": change, "action": "simulated_volume_change"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error simulating volume change: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to simulate volume change"
        )
