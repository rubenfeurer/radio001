"""
Audio Player - Handles internet radio streaming and audio playback control.

This module provides the AudioPlayer class which manages:
- mpg123-based audio streaming for internet radio
- Volume control via amixer (ALSA)
- Stream connection and error handling
- Mock mode for development without audio hardware
"""

import asyncio
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class AudioPlayer:
    """
    Audio player for internet radio streaming.

    Provides high-level audio playback control using mpg123 as the backend
    and amixer for ALSA volume control.
    Supports mock mode for development on systems without audio hardware.
    """

    def __init__(
        self, mock_mode: bool = True, status_callback: Optional[Callable] = None
    ):
        """
        Initialize the AudioPlayer.

        Args:
            mock_mode: Whether to run in mock mode (no actual audio)
            status_callback: Optional callback for playback status updates
        """
        self.mock_mode = mock_mode
        self.status_callback = status_callback
        self._process: Optional[asyncio.subprocess.Process] = None
        self._current_url: Optional[str] = None
        self._volume: int = 50
        self._is_playing: bool = False
        self._is_initialized: bool = False

        logger.info(f"AudioPlayer initialized (mock_mode={mock_mode})")

    async def initialize(self):
        """Initialize the audio player."""
        try:
            if not self.mock_mode:
                # Verify mpg123 is available
                proc = await asyncio.create_subprocess_exec(
                    "which",
                    "mpg123",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
                if proc.returncode != 0:
                    logger.warning("mpg123 not found, falling back to mock mode")
                    self.mock_mode = True
                else:
                    logger.info("mpg123 audio player available")
                    # Set initial volume
                    await self._set_alsa_volume(self._volume)

            self._is_initialized = True
            logger.info("AudioPlayer initialization complete")

        except Exception as e:
            logger.error(f"AudioPlayer initialization failed: {e}", exc_info=True)
            self.mock_mode = True
            self._is_initialized = True

    async def play(self, url: str) -> bool:
        """
        Start playing an audio stream.

        Args:
            url: Stream URL to play

        Returns:
            True if playback started successfully
        """
        try:
            if self.mock_mode:
                logger.info(f"[MOCK] Starting playback: {url}")
                self._current_url = url
                self._is_playing = True
                await self._notify_status_change()
                return True

            if not self._is_initialized:
                logger.error("AudioPlayer not initialized")
                return False

            # Stop current playback if any
            if self._is_playing:
                await self.stop()

            logger.info(f"Starting playback: {url}")

            # Spawn mpg123 subprocess
            self._process = await asyncio.create_subprocess_exec(
                "mpg123",
                "--quiet",
                url,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            self._current_url = url
            self._is_playing = True

            # Monitor process in background for unexpected exits
            asyncio.create_task(self._monitor_process(self._process))

            logger.info(f"Playback started successfully: {url}")
            await self._notify_status_change()
            return True

        except Exception as e:
            logger.error(f"Error starting playback for {url}: {e}", exc_info=True)
            self._current_url = None
            self._is_playing = False
            await self._notify_status_change()
            return False

    async def stop(self) -> bool:
        """
        Stop current audio playback.

        Returns:
            True if stopped successfully
        """
        try:
            if self.mock_mode:
                logger.info("[MOCK] Stopping playback")
                self._current_url = None
                self._is_playing = False
                await self._notify_status_change()
                return True

            if self._process:
                logger.info("Stopping playback")
                try:
                    self._process.terminate()
                    try:
                        await asyncio.wait_for(self._process.wait(), timeout=3.0)
                    except asyncio.TimeoutError:
                        self._process.kill()
                        await self._process.wait()
                except ProcessLookupError:
                    pass  # Process already exited
                self._process = None

            self._current_url = None
            self._is_playing = False

            await self._notify_status_change()
            logger.info("Playback stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping playback: {e}", exc_info=True)
            self._current_url = None
            self._is_playing = False
            self._process = None
            await self._notify_status_change()
            return False

    async def pause(self) -> bool:
        """
        Pause current playback. For streaming audio, pause is equivalent to stop.

        Returns:
            True if paused successfully
        """
        return await self.stop()

    async def resume(self) -> bool:
        """
        Resume paused playback. Re-starts the stream from the current URL.

        Returns:
            True if resumed successfully
        """
        if self._current_url:
            return await self.play(self._current_url)
        logger.warning("Cannot resume: no URL to resume")
        return False

    async def set_volume(self, volume: int) -> bool:
        """
        Set audio volume level via amixer.

        Args:
            volume: Volume level (0-100)

        Returns:
            True if volume was set successfully
        """
        try:
            volume = max(0, min(100, volume))

            if self.mock_mode:
                logger.info(f"[MOCK] Setting volume to {volume}%")
                self._volume = volume
                await self._notify_status_change()
                return True

            success = await self._set_alsa_volume(volume)
            if success:
                self._volume = volume
                logger.debug(f"Volume set to {volume}%")
                await self._notify_status_change()
            return success

        except Exception as e:
            logger.error(f"Error setting volume to {volume}: {e}", exc_info=True)
            return False

    async def _set_alsa_volume(self, volume: int) -> bool:
        """Set ALSA volume using amixer."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "amixer",
                "set",
                "PCM",
                f"{volume}%",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                # PCM control might not exist, try Master
                proc = await asyncio.create_subprocess_exec(
                    "amixer",
                    "set",
                    "Master",
                    f"{volume}%",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    logger.warning(f"amixer failed: {stderr.decode().strip()}")
                    return False
            return True
        except FileNotFoundError:
            logger.warning("amixer not found")
            return False

    async def get_volume(self) -> int:
        """Get current volume level."""
        return self._volume

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self._is_playing

    def get_current_url(self) -> Optional[str]:
        """Get currently playing stream URL."""
        return self._current_url

    async def get_playback_info(self) -> dict:
        """Get detailed playback information."""
        return {
            "is_playing": self._is_playing,
            "current_url": self._current_url,
            "volume": self._volume,
            "mock_mode": self.mock_mode,
            "initialized": self._is_initialized,
        }

    async def _monitor_process(self, process: asyncio.subprocess.Process):
        """Monitor the mpg123 process and update state if it exits unexpectedly."""
        try:
            await process.wait()
        except asyncio.CancelledError:
            return
        # Only update state if this is still the active process
        if self._process is process:
            if self._is_playing:
                logger.warning("mpg123 process exited unexpectedly")
                self._is_playing = False
                self._current_url = None
                self._process = None
                await self._notify_status_change()

    async def _notify_status_change(self):
        """Notify status callback of playback changes."""
        if self.status_callback:
            try:
                status = {
                    "is_playing": self._is_playing,
                    "current_url": self._current_url,
                    "volume": self._volume,
                }
                await self.status_callback(status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}", exc_info=True)

    async def test_playback(self, url: str = None) -> bool:
        """
        Test audio playback with a test stream.

        Args:
            url: Optional test URL (uses default if None)

        Returns:
            True if test was successful
        """
        test_url = url or "https://stream.srg-ssr.ch/m/rsj/mp3_128"
        logger.info(f"Testing audio playback with: {test_url}")
        try:
            success = await self.play(test_url)
            if success:
                await asyncio.sleep(2)
                await self.stop()
                logger.info("Audio playback test successful")
                return True
            else:
                logger.error("Audio playback test failed")
                return False
        except Exception as e:
            logger.error(f"Audio playback test error: {e}", exc_info=True)
            return False

    async def cleanup(self):
        """Cleanup audio player resources."""
        try:
            await self.stop()
            self._is_initialized = False
            logger.info("AudioPlayer cleanup complete")
        except Exception as e:
            logger.error(f"Error during AudioPlayer cleanup: {e}", exc_info=True)

    def get_hardware_info(self) -> dict:
        """Get hardware and capability information."""
        return {
            "mock_mode": self.mock_mode,
            "initialized": self._is_initialized,
            "audio_backend": "mock" if self.mock_mode else "mpg123",
        }
