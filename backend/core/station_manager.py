"""
Station Manager - Handles 3-slot radio station storage and management.

This module provides the StationManager class which handles:
- Loading and saving radio stations to/from JSON storage
- Managing the 3-slot station system (slots 1, 2, 3)
- Providing default stations for empty slots
- CRUD operations for station data
- Data validation and persistence
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

from core.models import RadioStation, StationRequest

logger = logging.getLogger(__name__)


class StationManager:
    """
    Manages the 3-slot radio station storage system.

    Provides persistence, validation, and CRUD operations for radio stations.
    Each slot (1, 2, 3) can contain one RadioStation or be empty (None).
    """

    def __init__(self, stations_file: Path):
        """
        Initialize the StationManager.

        Args:
            stations_file: Path to the JSON file for station storage
        """
        self.stations_file = Path(stations_file)
        self._stations: Dict[int, Optional[RadioStation]] = {1: None, 2: None, 3: None}
        self._lock = asyncio.Lock()

        # Default stations for empty slots
        self._default_stations = {
            1: RadioStation(
                name="SRF 3",
                url="https://stream.srg-ssr.ch/m/srf3/mp3_128",
                slot=1,
                country="Switzerland",
                location="Bern",
                genre="Pop/Rock",
                language="German"
            ),
            2: RadioStation(
                name="Radio Swiss Jazz",
                url="https://stream.srg-ssr.ch/m/rsj/mp3_128",
                slot=2,
                country="Switzerland",
                location="Bern",
                genre="Jazz",
                language="Instrumental"
            ),
            3: RadioStation(
                name="Radio Swiss Classic",
                url="https://stream.srg-ssr.ch/m/rsc_de/mp3_128",
                slot=3,
                country="Switzerland",
                location="Bern",
                genre="Classical",
                language="Instrumental"
            )
        }

        logger.info(f"StationManager initialized with storage: {self.stations_file}")

    async def initialize(self):
        """Initialize the station manager and load existing stations."""
        try:
            await self._load_stations()
            logger.info("StationManager initialization complete")

        except Exception as e:
            logger.error(f"StationManager initialization failed: {e}", exc_info=True)
            # Continue with default stations if loading fails
            await self._load_defaults_for_empty_slots()

    async def _load_stations(self):
        """Load stations from JSON file or create with defaults."""
        async with self._lock:
            if self.stations_file.exists():
                try:
                    with open(self.stations_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Convert loaded data to RadioStation objects
                    for slot_str, station_data in data.items():
                        slot = int(slot_str)
                        if slot in [1, 2, 3] and station_data:
                            station = RadioStation(**station_data)
                            station.slot = slot  # Ensure slot is set correctly
                            self._stations[slot] = station

                    logger.info(f"Loaded stations: {[s.name if s else 'Empty' for s in self._stations.values()]}")

                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.error(f"Error loading stations from {self.stations_file}: {e}")
                    # Fall back to defaults on error
                    await self._load_defaults_for_empty_slots()
            else:
                logger.info("No existing stations file found, using defaults")
                await self._load_defaults_for_empty_slots()

    async def _load_defaults_for_empty_slots(self):
        """Load default stations for any empty slots."""
        for slot in [1, 2, 3]:
            if self._stations[slot] is None:
                self._stations[slot] = self._default_stations[slot]
                logger.info(f"Loaded default station for slot {slot}: {self._default_stations[slot].name}")

    async def _save_stations(self):
        """Save current stations to JSON file."""
        async with self._lock:
            try:
                # Ensure directory exists
                self.stations_file.parent.mkdir(parents=True, exist_ok=True)

                # Convert stations to serializable format
                data = {}
                for slot, station in self._stations.items():
                    if station:
                        data[str(slot)] = station.dict()
                    else:
                        data[str(slot)] = None

                # Write to file atomically
                temp_file = self.stations_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                # Atomic replace
                temp_file.replace(self.stations_file)

                logger.info(f"Stations saved to {self.stations_file}")

            except Exception as e:
                logger.error(f"Error saving stations: {e}", exc_info=True)
                raise

    # =============================================================================
    # Public API Methods
    # =============================================================================

    async def get_station(self, slot: int) -> Optional[RadioStation]:
        """
        Get station from specified slot.

        Args:
            slot: Station slot number (1-3)

        Returns:
            RadioStation object or None if slot is empty

        Raises:
            ValueError: If slot number is invalid
        """
        if slot not in [1, 2, 3]:
            raise ValueError(f"Invalid slot number: {slot}. Must be 1, 2, or 3.")

        return self._stations[slot]

    async def get_all_stations(self) -> Dict[int, Optional[RadioStation]]:
        """
        Get all stations.

        Returns:
            Dictionary mapping slot numbers to RadioStation objects or None
        """
        return self._stations.copy()

    async def save_station(self, slot: int, station_request: StationRequest) -> RadioStation:
        """
        Save a station to the specified slot.

        Args:
            slot: Station slot number (1-3)
            station_request: Station data to save

        Returns:
            The saved RadioStation object

        Raises:
            ValueError: If slot number is invalid
        """
        if slot not in [1, 2, 3]:
            raise ValueError(f"Invalid slot number: {slot}. Must be 1, 2, or 3.")

        try:
            # Create RadioStation from request
            station = RadioStation(
                name=station_request.name,
                url=station_request.url,
                slot=slot,
                country=station_request.country,
                location=station_request.location,
                genre=station_request.genre,
                bitrate=station_request.bitrate,
                language=station_request.language
            )

            # Save to memory
            self._stations[slot] = station

            # Persist to file
            await self._save_stations()

            logger.info(f"Station saved to slot {slot}: {station.name}")
            return station

        except Exception as e:
            logger.error(f"Error saving station to slot {slot}: {e}", exc_info=True)
            raise

    async def delete_station(self, slot: int) -> bool:
        """
        Delete station from specified slot and load default.

        Args:
            slot: Station slot number (1-3)

        Returns:
            True if deletion was successful

        Raises:
            ValueError: If slot number is invalid
        """
        if slot not in [1, 2, 3]:
            raise ValueError(f"Invalid slot number: {slot}. Must be 1, 2, or 3.")

        try:
            old_station = self._stations[slot]

            # Replace with default station
            self._stations[slot] = self._default_stations[slot]

            # Persist changes
            await self._save_stations()

            if old_station:
                logger.info(f"Deleted station from slot {slot}: {old_station.name}, restored default")
            else:
                logger.info(f"Slot {slot} was already empty, restored default")

            return True

        except Exception as e:
            logger.error(f"Error deleting station from slot {slot}: {e}", exc_info=True)
            return False

    async def clear_slot(self, slot: int) -> bool:
        """
        Clear a slot (set to None) without loading default.

        Args:
            slot: Station slot number (1-3)

        Returns:
            True if clearing was successful

        Raises:
            ValueError: If slot number is invalid
        """
        if slot not in [1, 2, 3]:
            raise ValueError(f"Invalid slot number: {slot}. Must be 1, 2, or 3.")

        try:
            old_station = self._stations[slot]
            self._stations[slot] = None

            # Persist changes
            await self._save_stations()

            if old_station:
                logger.info(f"Cleared slot {slot}: {old_station.name}")
            else:
                logger.info(f"Slot {slot} was already empty")

            return True

        except Exception as e:
            logger.error(f"Error clearing slot {slot}: {e}", exc_info=True)
            return False

    async def get_configured_count(self) -> int:
        """
        Get number of configured (non-None) stations.

        Returns:
            Number of configured stations (0-3)
        """
        return sum(1 for station in self._stations.values() if station is not None)

    async def is_slot_empty(self, slot: int) -> bool:
        """
        Check if a slot is empty.

        Args:
            slot: Station slot number (1-3)

        Returns:
            True if slot is empty (None)

        Raises:
            ValueError: If slot number is invalid
        """
        if slot not in [1, 2, 3]:
            raise ValueError(f"Invalid slot number: {slot}. Must be 1, 2, or 3.")

        return self._stations[slot] is None

    async def validate_station_url(self, url: str) -> bool:
        """
        Validate if a station URL is reachable (basic check).

        Args:
            url: Stream URL to validate

        Returns:
            True if URL appears valid for streaming
        """
        try:
            # Basic URL validation
            if not url.startswith(('http://', 'https://')):
                return False

            # Additional validation could be added here (e.g., HEAD request)
            # For now, just check basic format
            return len(url.strip()) > 10

        except Exception as e:
            logger.error(f"Error validating URL {url}: {e}")
            return False

    # =============================================================================
    # Utility Methods
    # =============================================================================

    def get_storage_info(self) -> Dict[str, any]:
        """Get information about storage file and status."""
        return {
            "storage_file": str(self.stations_file),
            "file_exists": self.stations_file.exists(),
            "configured_stations": sum(1 for s in self._stations.values() if s),
            "last_modified": self.stations_file.stat().st_mtime if self.stations_file.exists() else None
        }

    async def export_stations(self) -> Dict[str, any]:
        """Export all stations for backup purposes."""
        return {
            "export_timestamp": datetime.now().isoformat(),
            "stations": {str(k): v.dict() if v else None for k, v in self._stations.items()}
        }

    async def import_stations(self, data: Dict[str, any]) -> bool:
        """
        Import stations from backup data.

        Args:
            data: Exported station data

        Returns:
            True if import was successful
        """
        try:
            async with self._lock:
                stations_data = data.get("stations", {})

                for slot_str, station_data in stations_data.items():
                    slot = int(slot_str)
                    if slot in [1, 2, 3]:
                        if station_data:
                            station = RadioStation(**station_data)
                            station.slot = slot
                            self._stations[slot] = station
                        else:
                            self._stations[slot] = None

                await self._save_stations()
                logger.info("Stations imported successfully")
                return True

        except Exception as e:
            logger.error(f"Error importing stations: {e}", exc_info=True)
            return False
