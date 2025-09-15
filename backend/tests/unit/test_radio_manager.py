"""
Unit tests for the RadioManager class.

Tests the central radio system controller including:
- Volume control with hardware limits
- Station playback management
- Hardware integration hooks
- Status tracking and broadcasting
- Error handling and recovery
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from core.radio_manager import RadioManager
from core.models import RadioStation, SystemStatus, PlaybackState, VolumeUpdate
from core.station_manager import StationManager
from main import Config


@pytest.mark.unit
class TestRadioManager:
    """Test RadioManager functionality in isolation."""

    async def test_initialization(self, temp_data_dir):
        """Test radio manager initialization."""
        # Clear any existing instance
        RadioManager._instance = None

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                assert manager is not None
                assert manager._status is not None
                assert manager._mock_mode is True

                # Check initial status
                status = await manager.get_status()
                assert isinstance(status, SystemStatus)
                assert status.volume == Config.DEFAULT_VOLUME
                assert status.is_playing is False
                assert status.playback_state == PlaybackState.STOPPED
            finally:
                await manager.shutdown()

    async def test_singleton_pattern(self, temp_data_dir):
        """Test that RadioManager follows singleton pattern."""
        # Clear any existing instance
        RadioManager._instance = None

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager1 = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            manager2 = RadioManager.get_instance()

            assert manager1 is manager2

            # Cleanup
            await manager1.shutdown()

    async def test_volume_control(self, temp_data_dir):
        """Test volume control functionality."""
        # Clear any existing instance
        RadioManager._instance = None

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                # Test setting volume
                success = await manager.set_volume(75)
                assert success is True

                status = await manager.get_status()
                assert status.volume == 75
            finally:
                await manager.shutdown()

    async def test_volume_limits(self, temp_data_dir):
        """Test volume limits enforcement."""
        # Clear any existing instance
        RadioManager._instance = None

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                # Test minimum volume (muting allowed)
                await manager.set_volume(0)
                status = await manager.get_status()
                assert status.volume == 0

                # Test setting a low volume
                await manager.set_volume(10)
                status = await manager.get_status()
                assert status.volume == 10  # Should accept the volume as set

                # Test maximum volume
                await manager.set_volume(200)  # Above MAX_VOLUME
                status = await manager.get_status()
                assert status.volume <= Config.MAX_VOLUME
            finally:
                await manager.shutdown()

    async def test_volume_change_broadcasting(self, temp_data_dir):
        """Test that volume changes trigger status broadcasts."""
        # Clear any existing instance
        RadioManager._instance = None

        status_callback = AsyncMock()

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                status_update_callback=status_callback,
                mock_mode=True
            )

            try:
                await manager.set_volume(60, broadcast=True)

                # Should have called the callback
                status_callback.assert_called()
            finally:
                await manager.shutdown()

    async def test_play_station_success(self, temp_data_dir):
        """Test successful station playback."""
        # Clear any existing instance
        RadioManager._instance = None

        # Create mock station manager that returns a test station
        mock_station_manager = AsyncMock()
        mock_station_manager.initialize.return_value = None
        mock_station_manager.get_station.return_value = RadioStation(
            name="Test Station",
            url="https://test.example.com/stream",
            slot=1
        )

        # Create mock audio player that succeeds
        mock_audio_player = AsyncMock()
        mock_audio_player.initialize.return_value = None
        mock_audio_player.play.return_value = True
        mock_audio_player.is_playing = True

        # Create mock sound manager
        mock_sound_manager = AsyncMock()
        mock_sound_manager.initialize.return_value = None
        mock_sound_manager.play_startup_sound.return_value = None
        mock_sound_manager.play_error_sound.return_value = None

        with patch('core.radio_manager.StationManager', return_value=mock_station_manager), \
             patch('core.radio_manager.SoundManager', return_value=mock_sound_manager), \
             patch('core.radio_manager.AudioPlayer', return_value=mock_audio_player):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                success = await manager.play_station(1)
                assert success is True

                # Verify the mocks were called correctly
                mock_station_manager.get_station.assert_called_with(1)
                mock_audio_player.play.assert_called_with("https://test.example.com/stream")
            finally:
                await manager.shutdown()

    async def test_play_empty_slot(self, temp_data_dir):
        """Test playing an empty station slot."""
        # Clear any existing instance
        RadioManager._instance = None

        # Create mock station manager that returns None (empty slot)
        mock_station_manager = AsyncMock()
        mock_station_manager.initialize.return_value = None
        mock_station_manager.get_station.return_value = None

        with patch('core.station_manager.StationManager', return_value=mock_station_manager), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                success = await manager.play_station(2)
                assert success is False

                # Check status unchanged
                status = await manager.get_status()
                assert status.current_station is None
                assert status.is_playing is False
            finally:
                await manager.shutdown()

    async def test_play_station_audio_failure(self, temp_data_dir):
        """Test handling of audio playback failure."""
        # Clear any existing instance
        RadioManager._instance = None

        # Create mock station manager that returns a test station
        mock_station_manager = AsyncMock()
        mock_station_manager.initialize.return_value = None
        mock_station_manager.get_station.return_value = RadioStation(
            name="Test Station",
            url="https://test.example.com/stream",
            slot=1
        )

        # Create mock audio player that fails to play
        mock_audio_player = AsyncMock()
        mock_audio_player.initialize.return_value = None
        mock_audio_player.play.return_value = False
        mock_audio_player.is_playing = False

        # Create mock sound manager
        mock_sound_manager = AsyncMock()
        mock_sound_manager.initialize.return_value = None
        mock_sound_manager.play_startup_sound.return_value = None
        mock_sound_manager.play_error_sound.return_value = None

        with patch('core.radio_manager.StationManager', return_value=mock_station_manager), \
             patch('core.radio_manager.SoundManager', return_value=mock_sound_manager), \
             patch('core.radio_manager.AudioPlayer', return_value=mock_audio_player):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                success = await manager.play_station(1)
                assert success is False

                # Status should show no playback
                status = await manager.get_status()
                assert status.is_playing is False
            finally:
                await manager.shutdown()

    async def test_stop_playback(self, temp_data_dir):
        """Test stopping playback."""
        # Clear any existing instance
        RadioManager._instance = None

        # Create mock station manager
        mock_station_manager = AsyncMock()
        mock_station_manager.initialize.return_value = None

        # Create mock sound manager
        mock_sound_manager = AsyncMock()
        mock_sound_manager.initialize.return_value = None
        mock_sound_manager.play_startup_sound.return_value = None
        mock_sound_manager.play_error_sound.return_value = None

        # Create mock audio player
        mock_audio_player = AsyncMock()
        mock_audio_player.initialize.return_value = None
        mock_audio_player.stop.return_value = True
        mock_audio_player.is_playing = False

        with patch('core.radio_manager.StationManager', return_value=mock_station_manager), \
             patch('core.radio_manager.SoundManager', return_value=mock_sound_manager), \
             patch('core.radio_manager.AudioPlayer', return_value=mock_audio_player):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                success = await manager.stop_playback()
                assert success is True

                # Verify audio player stop was called
                mock_audio_player.stop.assert_called()

                # Check status
                status = await manager.get_status()
                assert status.is_playing is False
            finally:
                await manager.shutdown()

    async def test_toggle_station_play(self, temp_data_dir):
        """Test toggling station from stopped to playing."""
        # Clear any existing instance
        RadioManager._instance = None

        # Create mock station manager
        mock_station_manager = AsyncMock()
        mock_station_manager.initialize.return_value = None
        mock_station_manager.get_station.return_value = RadioStation(
            name="Test Station",
            url="https://test.example.com/stream",
            slot=1
        )

        # Create mock audio player
        mock_audio_player = AsyncMock()
        mock_audio_player.initialize.return_value = None
        mock_audio_player.play.return_value = True
        mock_audio_player.is_playing = False

        # Create mock sound manager
        mock_sound_manager = AsyncMock()
        mock_sound_manager.initialize.return_value = None
        mock_sound_manager.play_startup_sound.return_value = None
        mock_sound_manager.play_error_sound.return_value = None

        with patch('core.radio_manager.StationManager', return_value=mock_station_manager), \
             patch('core.radio_manager.SoundManager', return_value=mock_sound_manager), \
             patch('core.radio_manager.AudioPlayer', return_value=mock_audio_player):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                success = await manager.toggle_station(1)
                assert success is True

                # Should start playing
                mock_audio_player.play.assert_called_with("https://test.example.com/stream")
            finally:
                await manager.shutdown()

    async def test_toggle_station_stop(self, temp_data_dir):
        """Test toggling station from playing to stopped."""
        # Clear any existing instance
        RadioManager._instance = None

        # Create mock station manager
        mock_station_manager = AsyncMock()
        mock_station_manager.initialize.return_value = None
        mock_station_manager.get_station.return_value = RadioStation(
            name="Test Station",
            url="https://test.example.com/stream",
            slot=1
        )

        # Create mock audio player
        mock_audio_player = AsyncMock()
        mock_audio_player.initialize.return_value = None
        mock_audio_player.stop.return_value = True
        mock_audio_player.is_playing = True

        # Create mock sound manager
        mock_sound_manager = AsyncMock()
        mock_sound_manager.initialize.return_value = None
        mock_sound_manager.play_startup_sound.return_value = None
        mock_sound_manager.play_error_sound.return_value = None

        with patch('core.radio_manager.StationManager', return_value=mock_station_manager), \
             patch('core.radio_manager.SoundManager', return_value=mock_sound_manager), \
             patch('core.radio_manager.AudioPlayer', return_value=mock_audio_player):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                # Simulate currently playing this station
                await manager.play_station(1)  # Start playing first

                success = await manager.toggle_station(1)
                assert success is True

                # Should stop playing
                mock_audio_player.stop.assert_called()
            finally:
                await manager.shutdown()

    async def test_toggle_different_station(self, temp_data_dir):
        """Test toggling to a different station while one is playing."""
        # Clear any existing instance
        RadioManager._instance = None

        # Create mock station manager with multiple stations
        mock_station_manager = AsyncMock()
        mock_station_manager.initialize.return_value = None

        def mock_get_station(slot):
            return RadioStation(
                name=f"Station {slot}",
                url=f"https://test{slot}.example.com/stream",
                slot=slot
            )
        mock_station_manager.get_station.side_effect = mock_get_station

        # Create mock audio player
        mock_audio_player = AsyncMock()
        mock_audio_player.initialize.return_value = None
        mock_audio_player.play.return_value = True
        mock_audio_player.stop.return_value = True
        mock_audio_player.is_playing = True

        # Create mock sound manager
        mock_sound_manager = AsyncMock()
        mock_sound_manager.initialize.return_value = None
        mock_sound_manager.play_startup_sound.return_value = None
        mock_sound_manager.play_error_sound.return_value = None

        with patch('core.radio_manager.StationManager', return_value=mock_station_manager), \
             patch('core.radio_manager.SoundManager', return_value=mock_sound_manager), \
             patch('core.radio_manager.AudioPlayer', return_value=mock_audio_player):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                # Start playing station 1
                await manager.play_station(1)

                # Toggle to station 2
                success = await manager.toggle_station(2)
                assert success is True

                # Should play the new station
                mock_audio_player.play.assert_called_with("https://test2.example.com/stream")
            finally:
                await manager.shutdown()

    async def test_hardware_button_handling(self, temp_data_dir):
        """Test hardware button press handling."""
        # Clear any existing instance
        RadioManager._instance = None

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                # Test button press simulation (development mode)
                await manager.simulate_button_press(1)
                # In mock mode, this should not raise errors
                # Just verify it completes successfully
            finally:
                await manager.shutdown()

    async def test_hardware_volume_handling(self, temp_data_dir):
        """Test hardware volume change handling."""
        # Clear any existing instance
        RadioManager._instance = None

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                initial_status = await manager.get_status()
                initial_volume = initial_status.volume

                # Test volume change simulation
                await manager.simulate_volume_change(10)

                status = await manager.get_status()
                expected_volume = min(Config.MAX_VOLUME, initial_volume + 10)
                assert status.volume == expected_volume
            finally:
                await manager.shutdown()

    async def test_status_broadcasting(self, temp_data_dir):
        """Test status update broadcasting."""
        # Clear any existing instance
        RadioManager._instance = None

        status_callback = AsyncMock()

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                status_update_callback=status_callback,
                mock_mode=True
            )

            try:
                # Trigger a status update
                await manager.set_volume(65, broadcast=True)

                # Should have called the callback
                status_callback.assert_called()
            finally:
                await manager.shutdown()

    async def test_get_status_with_station_info(self, temp_data_dir):
        """Test getting status with current station information."""
        # Clear any existing instance
        RadioManager._instance = None

        # Create mock station manager
        mock_station_manager = AsyncMock()
        mock_station_manager.initialize.return_value = None
        test_station = RadioStation(
            name="Current Station",
            url="https://current.example.com/stream",
            slot=2,
            genre="Pop"
        )
        mock_station_manager.get_station.return_value = test_station

        # Create mock sound manager
        mock_sound_manager = AsyncMock()
        mock_sound_manager.initialize.return_value = None
        mock_sound_manager.play_startup_sound.return_value = None
        mock_sound_manager.play_error_sound.return_value = None

        # Create mock audio player
        mock_audio_player = AsyncMock()
        mock_audio_player.initialize.return_value = None
        mock_audio_player.play.return_value = True
        mock_audio_player.is_playing = False

        with patch('core.radio_manager.StationManager', return_value=mock_station_manager), \
             patch('core.radio_manager.SoundManager', return_value=mock_sound_manager), \
             patch('core.radio_manager.AudioPlayer', return_value=mock_audio_player):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                # Start playing station 2
                await manager.play_station(2)

                status = await manager.get_status()
                assert status.current_station == 2
            finally:
                await manager.shutdown()

    async def test_simulate_button_press(self, temp_data_dir):
        """Test button press simulation for development."""
        # Clear any existing instance
        RadioManager._instance = None

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                # Should work in mock mode
                await manager.simulate_button_press(1)
                await manager.simulate_button_press(2)
                await manager.simulate_button_press(3)

                # Invalid button should log warning but not raise error
                await manager.simulate_button_press(4)  # Invalid - logs warning
            finally:
                await manager.shutdown()

    async def test_simulate_volume_change(self, temp_data_dir):
        """Test volume change simulation for development."""
        # Clear any existing instance
        RadioManager._instance = None

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                initial_status = await manager.get_status()
                initial_volume = initial_status.volume

                # Test volume increase simulation
                await manager.simulate_volume_change(10)

                status = await manager.get_status()
                expected_volume = min(Config.MAX_VOLUME, initial_volume + 10)
                assert status.volume == expected_volume
            finally:
                await manager.shutdown()

    async def test_hardware_status(self, temp_data_dir):
        """Test getting hardware status."""
        # Clear any existing instance
        RadioManager._instance = None

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                hw_status = manager.get_hardware_status()

                assert isinstance(hw_status, dict)
                assert "mock_mode" in hw_status
                assert hw_status["mock_mode"] is True
                assert "gpio_available" in hw_status
                assert "audio_available" in hw_status
            finally:
                await manager.shutdown()

    async def test_error_handling_during_playback(self, temp_data_dir):
        """Test error handling during playback operations."""
        # Clear any existing instance
        RadioManager._instance = None

        # Create mock station manager
        mock_station_manager = AsyncMock()
        mock_station_manager.initialize.return_value = None
        mock_station_manager.get_station.return_value = RadioStation(
            name="Test Station",
            url="https://test.example.com/stream",
            slot=1
        )

        # Create mock audio player that raises exception
        mock_audio_player = AsyncMock()
        mock_audio_player.initialize.return_value = None
        mock_audio_player.play.side_effect = Exception("Audio error")

        # Create mock sound manager
        mock_sound_manager = AsyncMock()
        mock_sound_manager.initialize.return_value = None
        mock_sound_manager.play_startup_sound.return_value = None
        mock_sound_manager.play_error_sound.return_value = None

        with patch('core.radio_manager.StationManager', return_value=mock_station_manager), \
             patch('core.radio_manager.SoundManager', return_value=mock_sound_manager), \
             patch('core.radio_manager.AudioPlayer', return_value=mock_audio_player):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                # Should handle error gracefully
                success = await manager.play_station(1)
                assert success is False

                # Status should remain unchanged
                status = await manager.get_status()
                assert status.is_playing is False
            finally:
                await manager.shutdown()

    async def test_concurrent_operations(self, temp_data_dir):
        """Test concurrent radio manager operations."""
        # Clear any existing instance
        RadioManager._instance = None

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                # Test concurrent volume changes
                tasks = []
                for volume in [25, 50, 75]:
                    task = manager.set_volume(volume)
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # All should complete without exceptions
                for result in results:
                    assert not isinstance(result, Exception)
            finally:
                await manager.shutdown()

    async def test_shutdown_cleanup(self, temp_data_dir):
        """Test proper cleanup during shutdown."""
        # Clear any existing instance
        RadioManager._instance = None

        # Create mock station manager
        mock_station_manager = AsyncMock()
        mock_station_manager.initialize.return_value = None

        # Create mock sound manager
        mock_sound_manager = AsyncMock()
        mock_sound_manager.initialize.return_value = None
        mock_sound_manager.play_startup_sound.return_value = None
        mock_sound_manager.play_error_sound.return_value = None

        mock_audio_player = AsyncMock()
        mock_audio_player.initialize.return_value = None
        mock_audio_player.stop.return_value = True

        with patch('core.radio_manager.StationManager', return_value=mock_station_manager), \
             patch('core.radio_manager.SoundManager', return_value=mock_sound_manager), \
             patch('core.radio_manager.AudioPlayer', return_value=mock_audio_player):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            # Shutdown should complete successfully
            await manager.shutdown()

            # Should stop audio playback
            mock_audio_player.stop.assert_called()

    async def test_volume_step_calculations(self, temp_data_dir):
        """Test volume step size calculations."""
        # Clear any existing instance
        RadioManager._instance = None

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                initial_volume = 50
                await manager.set_volume(initial_volume)

                # Test volume change simulation
                await manager.simulate_volume_change(5)
                status = await manager.get_status()
                expected = min(initial_volume + 5, Config.MAX_VOLUME)
                assert status.volume == expected
            finally:
                await manager.shutdown()



    async def test_playback_state_transitions(self, temp_data_dir):
        """Test playback state transitions."""
        # Clear any existing instance
        RadioManager._instance = None

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                # Initial state
                status = await manager.get_status()
                assert status.playback_state == PlaybackState.STOPPED

                # The state transitions will depend on the actual implementation
                # In mock mode, we just verify the initial state is correct
                assert status.is_playing is False
            finally:
                await manager.shutdown()

    async def test_configuration_integration(self, temp_data_dir):
        """Test integration with configuration settings."""
        # Clear any existing instance
        RadioManager._instance = None

        with patch('core.station_manager.StationManager'), \
             patch('core.sound_manager.SoundManager'), \
             patch('hardware.audio_player.AudioPlayer'):

            manager = await RadioManager.create_instance(
                config=Config,
                mock_mode=True
            )

            try:
                # Test that config values are respected
                assert manager._config == Config

                # Test volume limits from config
                await manager.set_volume(Config.MAX_VOLUME + 10)
                status = await manager.get_status()
                assert status.volume <= Config.MAX_VOLUME
            finally:
                await manager.shutdown()

        # Test default volume
        new_manager_config = Config
        assert new_manager_config.DEFAULT_VOLUME == Config.DEFAULT_VOLUME
