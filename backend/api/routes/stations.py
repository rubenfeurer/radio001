"""
Station Management API Routes.

This module provides FastAPI routes for managing the 3-slot radio station system:
- GET /stations - Get all stations
- GET /stations/{slot} - Get specific station
- POST /stations/{slot} - Save station to slot
- POST /stations/{slot}/toggle - Play/stop station
- DELETE /stations/{slot} - Remove station
"""

import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse

from core.models import (
    RadioStation, StationRequest, StationsResponse,
    ApiResponse, SystemStatus
)
from core.radio_manager import RadioManager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=StationsResponse, summary="Get all stations")
async def get_all_stations():
    """
    Get all configured stations from all slots (1-3).

    Returns:
        StationsResponse: Dictionary mapping slot numbers to station objects or None
    """
    try:
        radio_manager = RadioManager.get_instance()
        stations = await radio_manager._station_manager.get_all_stations()

        configured_count = sum(1 for station in stations.values() if station is not None)

        return StationsResponse(
            stations=stations,
            total_configured=configured_count
        )
    except Exception as e:
        logger.error(f"Error getting stations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve stations"
        )


@router.get("/{slot}", response_model=Optional[RadioStation], summary="Get station by slot")
async def get_station(slot: int):
    """
    Get station from specific slot.

    Args:
        slot: Station slot number (1-3)

    Returns:
        RadioStation or None: Station object if configured, None if empty
    """
    if slot not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot must be 1, 2, or 3"
        )

    try:
        radio_manager = RadioManager.get_instance()
        station = await radio_manager._station_manager.get_station(slot)
        return station
    except Exception as e:
        logger.error(f"Error getting station {slot}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve station {slot}"
        )


@router.post("/{slot}", response_model=ApiResponse, summary="Save station to slot")
async def save_station(slot: int, station_request: StationRequest):
    """
    Save or update a station in the specified slot.

    Args:
        slot: Station slot number (1-3)
        station_request: Station details to save

    Returns:
        ApiResponse: Success/failure status with saved station info
    """
    if slot not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot must be 1, 2, or 3"
        )

    try:
        radio_manager = RadioManager.get_instance()

        # Validate URL if not in mock mode
        if not radio_manager._mock_mode:
            is_valid = await radio_manager._station_manager.validate_station_url(station_request.url)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Station URL is not reachable"
                )

        # Save the station
        saved_station = await radio_manager._station_manager.save_station(slot, station_request)

        logger.info(f"Station saved to slot {slot}: {saved_station.name}")

        return ApiResponse(
            success=True,
            message=f"Station '{saved_station.name}' saved to slot {slot}",
            data={
                "slot": slot,
                "station": saved_station.model_dump()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving station to slot {slot}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save station"
        )


@router.post("/{slot}/toggle", response_model=ApiResponse, summary="Toggle station playback")
async def toggle_station(slot: int):
    """
    Toggle playback for a station slot (play if stopped, stop if playing).

    Args:
        slot: Station slot number (1-3)

    Returns:
        ApiResponse: Success/failure status with playback action taken
    """
    if slot not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot must be 1, 2, or 3"
        )

    try:
        radio_manager = RadioManager.get_instance()

        # Check if slot has a station
        station = await radio_manager._station_manager.get_station(slot)
        if station is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No station configured in slot {slot}"
            )

        # Await the toggle so the response reports the actual outcome
        # (a background task plus post-scheduling status read could describe
        # the opposite action, or claim success for a dead stream URL)
        pre_status = await radio_manager.get_status()
        intended_stop = pre_status.current_station == slot and pre_status.is_playing

        is_playing = await radio_manager.toggle_station(slot)

        if not intended_stop and not is_playing:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start playback for '{station.name}'"
            )

        action = "started" if is_playing else "stopped"
        logger.info(f"Toggled station {slot}: {action} playback")

        return ApiResponse(
            success=True,
            message=f"Station '{station.name}' playback {action}",
            data={
                "slot": slot,
                "station_name": station.name,
                "action": action,
                "is_playing": is_playing
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling station {slot}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle station playback"
        )


@router.post("/{slot}/play", response_model=ApiResponse, summary="Play specific station")
async def play_station(slot: int):
    """
    Play a specific station slot.

    Args:
        slot: Station slot number (1-3)

    Returns:
        ApiResponse: Success/failure status
    """
    if slot not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot must be 1, 2, or 3"
        )

    try:
        radio_manager = RadioManager.get_instance()

        # Check if slot has a station
        station = await radio_manager._station_manager.get_station(slot)
        if station is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No station configured in slot {slot}"
            )

        # Await playback start so the response reports the actual outcome
        ok = await radio_manager.play_station(slot)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start playback for '{station.name}'"
            )

        logger.info(f"Started playback for station {slot}: {station.name}")

        return ApiResponse(
            success=True,
            message=f"Playing '{station.name}'",
            data={
                "slot": slot,
                "station_name": station.name,
                "action": "playing"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error playing station {slot}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to play station"
        )


@router.delete("/{slot}", response_model=ApiResponse, summary="Remove station from slot")
async def delete_station(slot: int):
    """
    Remove station from slot and load default station.

    Args:
        slot: Station slot number (1-3)

    Returns:
        ApiResponse: Success/failure status
    """
    if slot not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot must be 1, 2, or 3"
        )

    try:
        radio_manager = RadioManager.get_instance()

        # Get station name before deleting (for response message)
        station = await radio_manager._station_manager.get_station(slot)
        station_name = station.name if station else "Empty slot"

        # Delete the station (this will load default)
        success = await radio_manager._station_manager.delete_station(slot)

        if success:
            # Get the default station that was loaded
            new_station = await radio_manager._station_manager.get_station(slot)
            new_name = new_station.name if new_station else "None"

            logger.info(f"Deleted station from slot {slot}, loaded default: {new_name}")

            return ApiResponse(
                success=True,
                message=f"Removed '{station_name}' from slot {slot}, loaded default: '{new_name}'",
                data={
                    "slot": slot,
                    "removed_station": station_name,
                    "new_station": new_name
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete station"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting station {slot}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete station"
        )


@router.post("/{slot}/clear", response_model=ApiResponse, summary="Clear station slot")
async def clear_station_slot(slot: int):
    """
    Clear a station slot completely (set to None) without loading default.

    Args:
        slot: Station slot number (1-3)

    Returns:
        ApiResponse: Success/failure status
    """
    if slot not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot must be 1, 2, or 3"
        )

    try:
        radio_manager = RadioManager.get_instance()

        # Get station name before clearing (for response message)
        station = await radio_manager._station_manager.get_station(slot)
        station_name = station.name if station else "Empty slot"

        # Clear the slot
        success = await radio_manager._station_manager.clear_slot(slot)

        if success:
            logger.info(f"Cleared slot {slot}")

            return ApiResponse(
                success=True,
                message=f"Cleared slot {slot} (was '{station_name}')",
                data={
                    "slot": slot,
                    "cleared_station": station_name
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear slot"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing slot {slot}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear slot"
        )
