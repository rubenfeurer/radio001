"""
Audio Player - Handles internet radio streaming and audio playback control.

This module provides the AudioPlayer class which manages:
- MPV-based audio streaming for internet radio
- Volume control and audio output management
- Stream connection and error handling
- Mock mode for development without audio hardware
"""

import asyncio
import logging
from typing import Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioPlayer:
    """
    Audio player for internet radio streaming.

    Provides high-level audio playback control using MPV as the backend.
    Supports mock mode for development on systems without audio hardware.
    """

    def __init__(self, mock_mode: bool = True, status_callback: Optional[Callable] = None):
        """
        Initialize the AudioPlayer.

        Args:
            mock_mode: Whether to run in mock mode (no actual audio)
            status_callback: Optional callback for playback status updates
        """
        self.mock_mode = mock_mode
        self.status_callback = status_callback
        self._player = None
        self._current_url: Optional[str] = None
        self._volume: int = 50
        self._is_playing: bool = False
        self._is_initialized: bool = False

        logger.info(f"AudioPlayer initialized (mock_mode={mock_mode})")

    async def initialize(self):
        """Initialize the audio player and MPV backend."""
        try:
            if not self.mock_mode:
                # Try to initialize MPV for actual audio playback
                try:
                    import mpv

                    self._player = mpv.MPV(
                        input_default_bindings=True,
                        input_vo_keyboard=True,
                        video=False,
                        volume_max=100,
                        volume=self._volume
                    )

                    # Set up event handlers
                    @self._player.event_callback('playback-restart')
                    def on_playback_start(_):
                        asyncio.create_task(self._on_playback_started())

                    @self._player.event_callback('end-file')
                    def on_playback_end(_):
                        asyncio.create_task(self._on_playback_stopped())

                    logger.info("MPV audio player initialized successfully")

                except ImportError:
                    logger.warning("MPV not available, falling back to mock mode")
                    self.mock_mode = True
                except Exception as e:
                    logger.error(f"Failed to initialize MPV: {e}")
                    self.mock_mode = True

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

            if not self._is_initialized or not self._player:
                logger.error("AudioPlayer not initialized")
                return False

            # Stop current playback if any
            if self._is_playing:
                await self.stop()

            logger.info(f"Starting playback: {url}")

            # Start playback
            self._player.play(url)
            self._current_url = url

            # Wait a moment for playback to start
            await asyncio.sleep(0.5)

            # Check if playback actually started
            if hasattr(self._player, 'pause') and not self._player.pause:
                self._is_playing = True
                logger.info(f"Playback started successfully: {url}")
                await self._notify_status_change()
                return True
            else:
                logger.error(f"Playback failed to start: {url}")
                self._current_url = None
                return False

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

            if not self._is_initialized or not self._player:
                logger.error("AudioPlayer not initialized")
                return False

            if self._is_playing:
                logger.info("Stopping playback")
                self._player.stop()

            self._current_url = None
            self._is_playing = False

            await self._notify_status_change()
            logger.info("Playback stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping playback: {e}", exc_info=True)
            # Reset state even on error
            self._current_url = None
            self._is_playing = False
            await self._notify_status_change()
            return False

    async def pause(self) -> bool:
        """
        Pause current playback.

        Returns:
            True if paused successfully
        """
        try:
            if self.mock_mode:
                logger.info("[MOCK] Pausing playback")
                # In mock mode, pause is same as stop
                return await self.stop()

            if not self._is_initialized or not self._player or not self._is_playing:
                logger.warning("Cannot pause: not playing or not initialized")
                return False

            self._player.pause = True
            logger.info("Playback paused")
            await self._notify_status_change()
            return True

        except Exception as e:
            logger.error(f"Error pausing playback: {e}", exc_info=True)
            return False

    async def resume(self) -> bool:
        """
        Resume paused playback.

        Returns:
            True if resumed successfully
        """
        try:
            if self.mock_mode:
                logger.info("[MOCK] Resuming playback")
                return True

            if not self._is_initialized or not self._player:
                logger.warning("Cannot resume: not initialized")
                return False

            self._player.pause = False
            logger.info("Playback resumed")
            await self._notify_status_change()
            return True

        except Exception as e:
            logger.error(f"Error resuming playback: {e}", exc_info=True)
            return False

    async def set_volume(self, volume: int) -> bool:
        """
        Set audio volume level.

        Args:
            volume: Volume level (0-100)

        Returns:
            True if volume was set successfully
        """
        try:
            # Clamp volume to valid range
            volume = max(0, min(100, volume))

            if self.mock_mode:
                logger.info(f"[MOCK] Setting volume to {volume}%")
                self._volume = volume
                await self._notify_status_change()
                return True

            if not self._is_initialized or not self._player:
                logger.warning("Cannot set volume: not initialized")
                return False

            self._player.volume = volume
            self._volume = volume

            logger.debug(f"Volume set to {volume}%")
            await self._notify_status_change()
            return True

        except Exception as e:
            logger.error(f"Error setting volume to {volume}: {e}", exc_info=True)
            return False

    async def get_volume(self) -> int:
        """
        Get current volume level.

        Returns:
            Current volume level (0-100)
        """
        return self._volume

    def is_playing(self) -> bool:
        """
        Check if audio is currently playing.

        Returns:
            True if audio is playing
        """
        return self._is_playing

    def get_current_url(self) -> Optional[str]:
        """
        Get currently playing stream URL.

        Returns:
            Current stream URL or None if nothing is playing
        """
        return self._current_url

    async def get_playback_info(self) -> dict:
        """
        Get detailed playback information.

        Returns:
            Dictionary with playback status information
        """
        try:
            info = {
                "is_playing": self._is_playing,
                "current_url": self._current_url,
                "volume": self._volume,
                "mock_mode": self.mock_mode,
                "initialized": self._is_initialized
            }

            if not self.mock_mode and self._player and self._is_playing:
                try:
                    # Try to get additional info from MPV
                    info.update({
                        "duration": getattr(self._player, 'duration', None),
                        "position": getattr(self._player, 'time_pos', None),
                        "bitrate": getattr(self._player, 'audio_bitrate', None),
                        "format": getattr(self._player, 'audio_codec', None)
                    })
                except:
                    pass  # Ignore errors getting detailed info

            return info

        except Exception as e:
            logger.error(f"Error getting playback info: {e}", exc_info=True)
            return {
                "is_playing": False,
                "current_url": None,
                "volume": self._volume,
                "mock_mode": self.mock_mode,
                "initialized": False,
                "error": str(e)
            }

    # =============================================================================
    # Internal Event Handlers
    # =============================================================================

    async def _on_playback_started(self):
        """Handle playback started event."""
        self._is_playing = True
        logger.debug("Playback started event received")
        await self._notify_status_change()

    async def _on_playback_stopped(self):
        """Handle playback stopped event."""
        self._is_playing = False
        self._current_url = None
        logger.debug("Playback stopped event received")
        await self._notify_status_change()

    async def _notify_status_change(self):
        """Notify status callback of playback changes."""
        if self.status_callback:
            try:
                status = {
                    "is_playing": self._is_playing,
                    "current_url": self._current_url,
                    "volume": self._volume
                }
                await self.status_callback(status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}", exc_info=True)

    # =============================================================================
    # System Methods
    # =============================================================================

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
            # Try to play for a few seconds
            success = await self.play(test_url)
            if success:
                await asyncio.sleep(2)  # Play for 2 seconds
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
            # Stop any current playback
            await self.stop()

            # Cleanup MPV player
            if self._player and not self.mock_mode:
                try:
                    self._player.terminate()
                except:
                    pass  # Ignore cleanup errors

            self._player = None
            self._is_initialized = False

            logger.info("AudioPlayer cleanup complete")

        except Exception as e:
            logger.error(f"Error during AudioPlayer cleanup: {e}", exc_info=True)

    def get_hardware_info(self) -> dict:
        """Get hardware and capability information."""
        info = {
            "mock_mode": self.mock_mode,
            "initialized": self._is_initialized,
            "mpv_available": False,
            "audio_backend": "mock" if self.mock_mode else "mpv"
        }

        if not self.mock_mode:
            try:
                import mpv
                info["mpv_available"] = True
                info["mpv_version"] = getattr(mpv, '__version__', 'unknown')
            except ImportError:
                info["mpv_available"] = False

        return info
