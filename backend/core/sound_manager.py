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
import math
import struct
import wave
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
                # Verify mpg123 is available for WAV playback
                import asyncio as _asyncio
                proc = await _asyncio.create_subprocess_exec(
                    "which", "mpg123",
                    stdout=_asyncio.subprocess.DEVNULL,
                    stderr=_asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
                if proc.returncode != 0:
                    logger.warning("mpg123 not found, sound notifications disabled")
                    self.mock_mode = True
                else:
                    logger.info("mpg123 available for sound playback")

            # Verify sound files exist (and generate tones if needed)
            await self._verify_sound_files()

            logger.info("SoundManager initialization complete")

        except Exception as e:
            logger.error(f"SoundManager initialization failed: {e}", exc_info=True)
            # Continue in mock mode if initialization fails
            self.mock_mode = True

    async def _verify_sound_files(self):
        """Verify that required sound files exist and are real audio (not placeholders)."""
        self.sounds_dir.mkdir(parents=True, exist_ok=True)

        # Generate tones for any missing or placeholder generic sound files
        await self._ensure_tone_files()

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
            logger.warning(f"Missing sound files (no fallback): {missing_files}")

    def _generate_tone_wav(self, path: Path, notes: list[tuple[float, float]]):
        """
        Write a WAV file containing a sequence of pure tones using stdlib only.

        Args:
            path: Destination file path.
            notes: List of (frequency_hz, duration_s) pairs played in sequence.
        """
        sample_rate = 44100
        amplitude = 28000  # ~85% of int16 max — audible but not distorted

        frames = []
        for freq, duration in notes:
            n_samples = int(sample_rate * duration)
            for i in range(n_samples):
                # Sine wave with a short linear fade-in/out to avoid clicks
                fade_len = min(int(sample_rate * 0.01), n_samples // 4)
                t = i / sample_rate
                sample = amplitude * math.sin(2 * math.pi * freq * t)
                if i < fade_len:
                    sample *= i / fade_len
                elif i > n_samples - fade_len:
                    sample *= (n_samples - i) / fade_len
                frames.append(struct.pack('<h', int(sample)))

        with wave.open(str(path), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))

    def _is_placeholder(self, path: Path) -> bool:
        """Return True if file is missing or is a placeholder (size < 200 bytes)."""
        if not path.exists():
            return True
        return path.stat().st_size < 200

    async def _ensure_tone_files(self):
        """Generate audible WAV tones for any missing or placeholder generic sound files."""
        tone_specs = {
            # startup.wav and success.wav: two ascending tones (C5 523 Hz → E5 659 Hz)
            "startup.wav": [(523.25, 0.25), (659.25, 0.25)],
            "success.wav": [(523.25, 0.25), (659.25, 0.25)],
            # error.wav: two descending tones (A4 440 Hz → E4 330 Hz)
            "error.wav": [(440.0, 0.25), (329.63, 0.25)],
        }

        for filename, notes in tone_specs.items():
            path = self.sounds_dir / filename
            if self._is_placeholder(path):
                try:
                    self._generate_tone_wav(path, notes)
                    logger.info(f"Generated audible tone file: {filename}")
                except Exception as e:
                    logger.warning(f"Could not generate {filename}: {e}")

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
            if not sound_path.exists():
                logger.warning(f"Sound file missing: {sound_path}")
                return

            logger.debug(f"Playing sound: {sound_file} for event: {event}")

            # Play WAV via mpg123 (non-blocking — fire and forget)
            proc = await asyncio.create_subprocess_exec(
                "mpg123", "--quiet", str(sound_path),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            # Wait briefly so the sound has started before returning
            await asyncio.sleep(0.1)

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
        """Get list of missing or placeholder sound files (no usable fallback)."""
        missing = []
        for event, filename in self.sound_files.items():
            sound_path = self.sounds_dir / filename
            fallback_path = self.sounds_dir / self.fallback_sounds[event]

            if self._is_placeholder(sound_path) and self._is_placeholder(fallback_path):
                missing.append(filename)

        return missing

    async def cleanup(self):
        """Cleanup sound manager resources."""
        try:
            logger.info("SoundManager cleanup complete")

        except Exception as e:
            logger.error(f"Error during SoundManager cleanup: {e}", exc_info=True)
