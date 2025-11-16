"""
Sound Manager - Handles system notification sounds and audio feedback.

This module provides the SoundManager class which handles:
- System notification sounds (startup, success, error)
- Sound file management and playback
- Mock mode for development without audio hardware
- Integration with MPV for sound playback
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class SystemEvent(str, Enum):
    """System events that trigger notification sounds."""
    STARTUP_SUCCESS = "startup_success"
    STARTUP_ERROR = "startup_error"
    CONNECTION_SUCCESS = "connection_success"
    CONNECTION_ERROR = "connection_error"
    VOLUME_CHANGE = "volume_change"
    STATION_CHANGE = "station_change"
    BUTTON_PRESS = "button_press"
    ERROR = "error"


class SoundManager:
    """
    Manages system notification sounds and audio feedback.

    Provides audio feedback for system events while supporting mock mode
    for development environments without audio hardware.
    """

    def __init__(self, sounds_dir: Path, mock_mode: bool = True):
        """
        Initialize the SoundManager.

        Args:
            sounds_dir: Directory containing sound files
            mock_mode: Whether to run in mock mode (no actual audio)
        """
        self.sounds_dir = Path(sounds_dir)
        self.mock_mode = mock_mode
        self._sound_player = None

        # Sound file mappings
        self.sound_files = {
            SystemEvent.STARTUP_SUCCESS: "startup_success.wav",
            SystemEvent.STARTUP_ERROR: "startup_error.wav",
            SystemEvent.CONNECTION_SUCCESS: "connection_success.wav",
            SystemEvent.CONNECTION_ERROR: "connection_error.wav",
            SystemEvent.VOLUME_CHANGE: "volume_change.wav",
            SystemEvent.STATION_CHANGE: "station_change.wav",
            SystemEvent.BUTTON_PRESS: "button_press.wav",
            SystemEvent.ERROR: "error.wav"
        }

        # Fallback to generic sounds if specific ones don't exist
        self.fallback_sounds = {
            SystemEvent.STARTUP_SUCCESS: "success.wav",
            SystemEvent.STARTUP_ERROR: "error.wav",
            SystemEvent.CONNECTION_SUCCESS: "success.wav",
            SystemEvent.CONNECTION_ERROR: "error.wav",
            SystemEvent.VOLUME_CHANGE: "success.wav",
            SystemEvent.STATION_CHANGE: "success.wav",
            SystemEvent.BUTTON_PRESS: "success.wav",
            SystemEvent.ERROR: "error.wav"
        }

        logger.info(f"SoundManager initialized (mock_mode={mock_mode}, sounds_dir={sounds_dir})")

    async def initialize(self):
        """Initialize the sound manager and verify sound files."""
        try:
            if not self.mock_mode:
                # Try to import MPV for actual sound playback
                try:
                    import mpv
                    self._sound_player = mpv.MPV(video=False, volume=40)
                    logger.info("MPV sound player initialized")
                except ImportError:
                    logger.warning("MPV not available, falling back to mock mode")
                    self.mock_mode = True

            # Verify sound files exist
            await self._verify_sound_files()

            logger.info("SoundManager initialization complete")

        except Exception as e:
            logger.error(f"SoundManager initialization failed: {e}", exc_info=True)
            # Continue in mock mode if initialization fails
            self.mock_mode = True

    async def _verify_sound_files(self):
        """Verify that required sound files exist."""
        self.sounds_dir.mkdir(parents=True, exist_ok=True)

        missing_files = []
        available_files = []

        for event, filename in self.sound_files.items():
            sound_path = self.sounds_dir / filename
            fallback_path = self.sounds_dir / self.fallback_sounds[event]

            if sound_path.exists():
                available_files.append(filename)
            elif fallback_path.exists():
                available_files.append(f"{self.fallback_sounds[event]} (fallback)")
            else:
                missing_files.append(filename)

        if available_files:
            logger.info(f"Available sound files: {available_files}")

        if missing_files:
            logger.warning(f"Missing sound files: {missing_files}")
            await self._create_default_sound_files()

    async def _create_default_sound_files(self):
        """Create placeholder sound files for development."""
        try:
            # Create minimal WAV file headers for silence (placeholder files)
            # This is just for development - real sound files should be provided

            # Basic WAV header for 1 second of silence at 44.1kHz, 16-bit, mono
            wav_header = bytes([
                0x52, 0x49, 0x46, 0x46,  # "RIFF"
                0x2C, 0x00, 0x00, 0x00,  # File size - 8
                0x57, 0x41, 0x56, 0x45,  # "WAVE"
                0x66, 0x6D, 0x74, 0x20,  # "fmt "
                0x10, 0x00, 0x00, 0x00,  # PCM header size
                0x01, 0x00,              # PCM format
                0x01, 0x00,              # Mono
                0x44, 0xAC, 0x00, 0x00,  # Sample rate (44100)
                0x88, 0x58, 0x01, 0x00,  # Byte rate
                0x02, 0x00,              # Block align
                0x10, 0x00,              # Bits per sample
                0x64, 0x61, 0x74, 0x61,  # "data"
                0x00, 0x00, 0x00, 0x00   # Data size (0 = silence)
            ])

            # Create basic sound files
            for sound_file in ["success.wav", "error.wav"]:
                sound_path = self.sounds_dir / sound_file
                if not sound_path.exists():
                    with open(sound_path, 'wb') as f:
                        f.write(wav_header)
                    logger.info(f"Created placeholder sound file: {sound_file}")

        except Exception as e:
            logger.error(f"Error creating default sound files: {e}")

    async def play_sound(self, event: SystemEvent, volume: int = 40):
        """
        Play a notification sound for the specified event.

        Args:
            event: System event to play sound for
            volume: Volume level (0-100)
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Playing sound for event: {event}")
            return

        try:
            # Find sound file (prefer specific, fall back to generic)
            sound_file = self._get_sound_file(event)
            if not sound_file:
                logger.warning(f"No sound file available for event: {event}")
                return

            sound_path = self.sounds_dir / sound_file

            if self._sound_player and sound_path.exists():
                # Set volume and play
                self._sound_player.volume = max(0, min(100, volume))
                self._sound_player.play(str(sound_path))

                logger.debug(f"Playing sound: {sound_file} for event: {event}")

                # Wait for sound to start playing
                await asyncio.sleep(0.1)

            else:
                logger.warning(f"Sound player not available or file missing: {sound_path}")

        except Exception as e:
            logger.error(f"Error playing sound for event {event}: {e}", exc_info=True)

    def _get_sound_file(self, event: SystemEvent) -> Optional[str]:
        """Get the appropriate sound file for an event."""
        # Try specific sound file first
        specific_file = self.sound_files.get(event)
        if specific_file and (self.sounds_dir / specific_file).exists():
            return specific_file

        # Fall back to generic sound
        fallback_file = self.fallback_sounds.get(event)
        if fallback_file and (self.sounds_dir / fallback_file).exists():
            return fallback_file

        return None

    # =============================================================================
    # Convenience Methods for Common Events
    # =============================================================================

    async def play_startup_sound(self):
        """Play startup success sound."""
        await self.play_sound(SystemEvent.STARTUP_SUCCESS)

    async def play_error_sound(self):
        """Play error sound."""
        await self.play_sound(SystemEvent.ERROR)

    async def play_success_sound(self):
        """Play generic success sound."""
        await self.play_sound(SystemEvent.CONNECTION_SUCCESS)

    async def play_station_change_sound(self):
        """Play station change sound."""
        await self.play_sound(SystemEvent.STATION_CHANGE)

    async def play_button_press_sound(self):
        """Play button press feedback sound."""
        await self.play_sound(SystemEvent.BUTTON_PRESS, volume=20)

    async def play_volume_change_sound(self):
        """Play volume change feedback sound."""
        await self.play_sound(SystemEvent.VOLUME_CHANGE, volume=30)

    # =============================================================================
    # System Methods
    # =============================================================================

    async def test_all_sounds(self):
        """Test all available sound files."""
        logger.info("Testing all available sounds...")

        for event in SystemEvent:
            sound_file = self._get_sound_file(event)
            if sound_file:
                logger.info(f"Testing {event}: {sound_file}")
                await self.play_sound(event)
                await asyncio.sleep(0.5)  # Small delay between sounds
            else:
                logger.warning(f"No sound available for {event}")

    def get_available_sounds(self) -> Dict[str, str]:
        """Get list of available sound files."""
        available = {}
        for event in SystemEvent:
            sound_file = self._get_sound_file(event)
            if sound_file:
                available[event] = sound_file
        return available

    def get_missing_sounds(self) -> list[str]:
        """Get list of missing sound files."""
        missing = []
        for event, filename in self.sound_files.items():
            sound_path = self.sounds_dir / filename
            fallback_path = self.sounds_dir / self.fallback_sounds[event]

            if not sound_path.exists() and not fallback_path.exists():
                missing.append(filename)

        return missing

    async def cleanup(self):
        """Cleanup sound manager resources."""
        try:
            if self._sound_player and not self.mock_mode:
                self._sound_player.terminate()
                self._sound_player = None

            logger.info("SoundManager cleanup complete")

        except Exception as e:
            logger.error(f"Error during SoundManager cleanup: {e}", exc_info=True)
