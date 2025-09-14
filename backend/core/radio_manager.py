"""
Radio Manager - Central controller for radio system operations.

This module provides the RadioManager class which serves as the central coordinator
for all radio functionality including station management, audio playback, volume control,
and hardware integration.

The RadioManager follows a singleton pattern and integrates with:
- StationManager: For 3-slot station storage and retrieval
- AudioPlayer: For audio streaming and playback control
- SoundManager: For system notification sounds
- GPIOController: For physical hardware control (when available)
"""

import asyncio
import logging
import time
from typing import Optional, Callable, Dict, Any
from pathlib import Path

from .models import RadioStation, SystemStatus, PlaybackState, VolumeUpdate
from .station_manager import StationManager
from .sound_manager import SoundManager
from ..hardware.audio_player import AudioPlayer
from ..hardware.gpio_controller import GPIOController

logger = logging.getLogger(__name__)


class RadioManager:
    """
    Central radio system controller.

    Manages all radio operations including playback, volume, stations, and hardware integration.
    Designed as a singleton to ensure consistent state across the application.
    """

    _instance: Optional["RadioManager"] = None
    _lock = asyncio.Lock()

    def __init__(self,
                 config: Any,
                 status_update_callback: Optional[Callable] = None,
                 mock_mode: bool = True):
        """
        Initialize the RadioManager.

        Args:
            config: Application configuration object
            status_update_callback: Optional callback for status updates (WebSocket broadcasting)
            mock_mode: Whether to run in mock mode (for development)
        """
        if RadioManager._instance is not None:
            raise RuntimeError("RadioManager is a singleton. Use get_instance() instead.")

        self._config = config
        self._status_update_callback = status_update_callback
        self._mock_mode = mock_mode

        # Initialize core components
        self._station_manager = StationManager(config.STATIONS_FILE)
        self._sound_manager = SoundManager(config.SOUNDS_DIR, mock_mode=mock_mode)
        self._audio_player = AudioPlayer(mock_mode=mock_mode)

        # Initialize system status
        self._status = SystemStatus(
            volume=config.DEFAULT_VOLUME,
            is_playing=False,
            playback_state=PlaybackState.STOPPED
        )

        # Hardware controller (None in mock mode)
        self._gpio_controller: Optional[GPIOController] = None

        # Internal state
        self._playback_lock = asyncio.Lock()
        self._startup_complete = False

        logger.info(f"RadioManager initialized (mock_mode={mock_mode})")

    @classmethod
    async def create_instance(cls,
                            config: Any,
                            status_update_callback: Optional[Callable] = None,
                            mock_mode: bool = True) -> "RadioManager":
        """
        Create and initialize the RadioManager singleton instance.

        Args:
            config: Application configuration
            status_update_callback: Optional WebSocket callback
            mock_mode: Whether to use mock hardware

        Returns:
            RadioManager instance
        """
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls(config, status_update_callback, mock_mode)
                await cls._instance._initialize()
            return cls._instance

    @classmethod
    def get_instance(cls) -> "RadioManager":
        """Get the existing RadioManager instance."""
        if cls._instance is None:
            raise RuntimeError("RadioManager not initialized. Call create_instance() first.")
        return cls._instance

    async def _initialize(self):
        """Initialize the radio manager and all components."""
        try:
            logger.info("Initializing RadioManager components...")

            # Initialize station manager
            await self._station_manager.initialize()

            # Set initial volume
            await self.set_volume(self._config.DEFAULT_VOLUME, broadcast=False)

            # Initialize hardware if not in mock mode
            if not self._mock_mode:
                await self._initialize_hardware()

            # Play startup sound
            await self._sound_manager.play_startup_sound()

            self._startup_complete = True
            logger.info("RadioManager initialization complete")

        except Exception as e:
            logger.error(f"RadioManager initialization failed: {e}", exc_info=True)
            await self._sound_manager.play_error_sound()
            raise

    async def _initialize_hardware(self):
        """Initialize hardware controllers (Pi only)."""
        try:
            self._gpio_controller = GPIOController(
                config=self._config,
                button_callback=self._handle_button_press,
                volume_callback=self._handle_volume_change,
                mock_mode=self._mock_mode
            )
            await self._gpio_controller.initialize()
            logger.info("Hardware controllers initialized")

        except Exception as e:
            logger.error(f"Hardware initialization failed: {e}", exc_info=True)
            # Continue in mock mode if hardware fails
            self._gpio_controller = None

    # =============================================================================
    # Public API Methods
    # =============================================================================

    async def get_status(self) -> SystemStatus:
        """Get current system status."""
        # Update current station info if playing
        if self._status.current_station:
            station = await self._station_manager.get_station(self._status.current_station)
            self._status.current_station_info = station

        return self._status

    async def set_volume(self, volume: int, broadcast: bool = True) -> bool:
        """
        Set system volume level.

        Args:
            volume: Volume level (0-100)
            broadcast: Whether to broadcast the change

        Returns:
            True if successful
        """
        try:
            # Clamp volume to valid range
            volume = max(0, min(100, volume))

            # Set audio player volume
            await self._audio_player.set_volume(volume)

            # Update status
            self._status.volume = volume

            logger.info(f"Volume set to {volume}%")

            if broadcast:
                await self._broadcast_status_update("volume_update")

            return True

        except Exception as e:
            logger.error(f"Error setting volume: {e}", exc_info=True)
            return False

    async def play_station(self, slot: int) -> bool:
        """
        Play a station from the specified slot.

        Args:
            slot: Station slot number (1-3)

        Returns:
            True if playback started successfully
        """
        async with self._playback_lock:
            try:
                # Get station from slot
                station = await self._station_manager.get_station(slot)
                if not station:
                    logger.warning(f"No station configured in slot {slot}")
                    return False

                # Stop current playback if any
                if self._status.is_playing:
                    await self._audio_player.stop()

                # Update status to connecting
                self._status.playback_state = PlaybackState.CONNECTING
                self._status.current_station = slot
                await self._broadcast_status_update("playback_status")

                # Start playback
                success = await self._audio_player.play(station.url)

                if success:
                    self._status.is_playing = True
                    self._status.playback_state = PlaybackState.PLAYING
                    logger.info(f"Started playing {station.name} from slot {slot}")
                else:
                    self._status.is_playing = False
                    self._status.playback_state = PlaybackState.ERROR
                    self._status.current_station = None
                    logger.error(f"Failed to start playback for slot {slot}")

                await self._broadcast_status_update("playback_status")
                return success

            except Exception as e:
                logger.error(f"Error playing station {slot}: {e}", exc_info=True)
                self._status.is_playing = False
                self._status.playback_state = PlaybackState.ERROR
                self._status.current_station = None
                await self._broadcast_status_update("playback_status")
                return False

    async def stop_playback(self) -> bool:
        """
        Stop current playback.

        Returns:
            True if stopped successfully
        """
        async with self._playback_lock:
            try:
                await self._audio_player.stop()

                self._status.is_playing = False
                self._status.playback_state = PlaybackState.STOPPED
                self._status.current_station = None
                self._status.current_station_info = None

                logger.info("Playback stopped")
                await self._broadcast_status_update("playback_status")

                return True

            except Exception as e:
                logger.error(f"Error stopping playback: {e}", exc_info=True)
                return False

    async def toggle_station(self, slot: int) -> bool:
        """
        Toggle playback for a station slot (play if stopped, stop if playing this slot).

        Args:
            slot: Station slot number (1-3)

        Returns:
            True if currently playing the slot after toggle
        """
        if self._status.current_station == slot and self._status.is_playing:
            # Currently playing this slot, so stop
            await self.stop_playback()
            return False
        else:
            # Not playing this slot (or not playing at all), so play it
            success = await self.play_station(slot)
            return success

    # =============================================================================
    # Hardware Event Handlers
    # =============================================================================

    async def _handle_button_press(self, button_pin: int):
        """Handle physical button press events."""
        try:
            # Map GPIO pins to station slots
            pin_to_slot = {
                self._config.BUTTON_PIN_1: 1,
                self._config.BUTTON_PIN_2: 2,
                self._config.BUTTON_PIN_3: 3,
            }

            slot = pin_to_slot.get(button_pin)
            if slot:
                logger.info(f"Button press detected for station {slot}")
                await self.toggle_station(slot)
            else:
                logger.warning(f"Unknown button pin: {button_pin}")

        except Exception as e:
            logger.error(f"Error handling button press: {e}", exc_info=True)

    async def _handle_volume_change(self, change: int):
        """Handle rotary encoder volume changes."""
        try:
            new_volume = self._status.volume + change
            new_volume = max(0, min(100, new_volume))

            if new_volume != self._status.volume:
                await self.set_volume(new_volume)

        except Exception as e:
            logger.error(f"Error handling volume change: {e}", exc_info=True)

    # =============================================================================
    # Internal Methods
    # =============================================================================

    async def _broadcast_status_update(self, update_type: str = "system_status"):
        """Broadcast status update via WebSocket callback."""
        if self._status_update_callback:
            try:
                message = {
                    "type": update_type,
                    "data": self._status.dict(),
                    "timestamp": time.time()
                }
                await self._status_update_callback(message)

            except Exception as e:
                logger.error(f"Error broadcasting status update: {e}", exc_info=True)

    async def shutdown(self):
        """Shutdown the radio manager and cleanup resources."""
        try:
            logger.info("Shutting down RadioManager...")

            # Stop playback
            await self.stop_playback()

            # Cleanup hardware
            if self._gpio_controller:
                await self._gpio_controller.cleanup()

            # Cleanup audio
            await self._audio_player.cleanup()

            logger.info("RadioManager shutdown complete")

        except Exception as e:
            logger.error(f"Error during RadioManager shutdown: {e}", exc_info=True)

    # =============================================================================
    # Development/Debug Methods
    # =============================================================================

    async def simulate_button_press(self, button: int):
        """Simulate button press for development/testing."""
        if not self._mock_mode:
            logger.warning("simulate_button_press called in non-mock mode")
            return

        pin_map = {1: self._config.BUTTON_PIN_1, 2: self._config.BUTTON_PIN_2, 3: self._config.BUTTON_PIN_3}
        pin = pin_map.get(button)

        if pin:
            logger.info(f"Simulating button press for station {button}")
            await self._handle_button_press(pin)
        else:
            logger.warning(f"Invalid button number for simulation: {button}")

    async def simulate_volume_change(self, change: int):
        """Simulate volume change for development/testing."""
        if not self._mock_mode:
            logger.warning("simulate_volume_change called in non-mock mode")
            return

        logger.info(f"Simulating volume change: {change}")
        await self._handle_volume_change(change)

    def get_hardware_status(self) -> Dict[str, Any]:
        """Get hardware status for debugging."""
        return {
            "gpio_available": self._gpio_controller is not None,
            "audio_available": self._audio_player is not None,
            "mock_mode": self._mock_mode,
            "startup_complete": self._startup_complete
        }
