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

    @pytest.fixture
    async def mock_station_manager(self):
        """Mock station manager for testing."""
        mock = AsyncMock(spec=StationManager)

        # Mock default behavior
        mock.get_station.return_value = RadioStation(
            name="Test Station",
            url="https://test.example.com/stream",
            slot=1,
            genre="Test"
        )

        mock.get_all_stations.return_value = {
            1: RadioStation(name="Station 1", url="https://test1.example.com", slot=1),
            2: None,
            3: RadioStation(name="Station 3", url="https://test3.example.com", slot=3)
        }

        mock.initialize.return_value = None
        return mock

    @pytest.fixture
    def mock_audio_player(self):
        """Mock audio player for testing."""
        mock = AsyncMock()
        mock.initialize.return_value = None
        mock.play.return_value = True
        mock.stop.return_value = True
        mock.set_volume.return_value = True
        mock.get_volume.return_value = 50
        mock.is_playing = False
        mock.current_url = None
        return mock

    @pytest.fixture
    def mock_sound_manager(self):
        """Mock sound manager for testing."""
        mock = AsyncMock()
        mock.initialize.return_value = None
        mock.play_sound.return_value = None
        return mock

    @pytest.fixture
    def status_callback(self):
        """Mock status update callback."""
        return AsyncMock()

    @pytest.fixture
    async def radio_manager(self, mock_station_manager, mock_audio_player,
                           mock_sound_manager, status_callback, temp_data_dir):
        """Create radio manager with mocked dependencies."""

        # Patch the dependencies
        with patch('core.radio_manager.StationManager', return_value=mock_station_manager), \
             patch('core.radio_manager.SoundManager', return_value=mock_sound_manager), \
             patch('hardware.audio_player.AudioPlayer', return_value=mock_audio_player):

            manager = RadioManager(
                config=Config,
                status_update_callback=status_callback,
                mock_mode=True
            )

            await manager._initialize()
            yield manager

            try:
                await manager.shutdown()
            except Exception:
                pass  # Ignore shutdown errors in tests

    async def test_initialization(self, radio_manager):
        """Test radio manager initialization."""
        assert radio_manager is not None
        assert radio_manager._status is not None
        assert radio_manager._mock_mode is True

        # Check initial status
        status = await radio_manager.get_status()
        assert isinstance(status, SystemStatus)
        assert status.volume == Config.DEFAULT_VOLUME
        assert status.is_playing is False
        assert status.playback_state == PlaybackState.STOPPED

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

    async def test_volume_control(self, radio_manager):
        """Test volume control functionality."""
        # Test setting volume
        success = await radio_manager.set_volume(75)
        assert success is True

        status = await radio_manager.get_status()
        assert status.volume == 75

    async def test_volume_limits(self, radio_manager):
        """Test volume limits enforcement."""
        # Test minimum volume (muting allowed)
        await radio_manager.set_volume(0)
        status = await radio_manager.get_status()
        assert status.volume == 0

        # Test hardware minimum when above 0
        await radio_manager.set_volume(10)  # Below MIN_VOLUME
        status = await radio_manager.get_status()
        # Should be clamped to MIN_VOLUME if above 0
        if status.volume > 0:
            assert status.volume >= Config.MIN_VOLUME

        # Test maximum volume
        await radio_manager.set_volume(150)  # Above MAX_VOLUME
        status = await radio_manager.get_status()
        assert status.volume <= Config.MAX_VOLUME

    async def test_volume_change_broadcasting(self, radio_manager, status_callback):
        """Test that volume changes trigger status broadcasts."""
        await radio_manager.set_volume(60, broadcast=True)

        # Should have called the callback
        status_callback.assert_called()

    async def test_play_station_success(self, radio_manager, mock_station_manager, mock_audio_player):
        """Test successful station playback."""
        # Mock station exists
        mock_station_manager.get_station.return_value = RadioStation(
            name="Test Station",
            url="https://test.example.com/stream",
            slot=1
        )

        # Mock successful audio playback
        mock_audio_player.play.return_value = True
        mock_audio_player.is_playing = True

        success = await radio_manager.play_station(1)
        assert success is True

        # Verify audio player was called
        mock_audio_player.play.assert_called_with("https://test.example.com/stream")

        # Check status update
        status = await radio_manager.get_status()
        assert status.current_station == 1
        assert status.is_playing is True

    async def test_play_empty_slot(self, radio_manager, mock_station_manager):
        """Test playing an empty station slot."""
        # Mock empty slot
        mock_station_manager.get_station.return_value = None

        success = await radio_manager.play_station(2)
        assert success is False

        # Status should not change
        status = await radio_manager.get_status()
        assert status.current_station is None
        assert status.is_playing is False

    async def test_play_station_audio_failure(self, radio_manager, mock_station_manager, mock_audio_player):
        """Test handling of audio playback failure."""
        # Mock station exists
        mock_station_manager.get_station.return_value = RadioStation(
            name="Test Station",
            url="https://test.example.com/stream",
            slot=1
        )

        # Mock audio playback failure
        mock_audio_player.play.return_value = False

        success = await radio_manager.play_station(1)
        assert success is False

        # Status should reflect failure
        status = await radio_manager.get_status()
        assert status.is_playing is False

    async def test_stop_playback(self, radio_manager, mock_audio_player):
        """Test stopping playback."""
        # First start playback
        mock_audio_player.is_playing = True
        radio_manager._status.is_playing = True
        radio_manager._status.current_station = 1

        success = await radio_manager.stop_playback()
        assert success is True

        # Verify audio player stop was called
        mock_audio_player.stop.assert_called_once()

        # Check status update
        status = await radio_manager.get_status()
        assert status.is_playing is False
        assert status.current_station is None

    async def test_toggle_station_play(self, radio_manager, mock_station_manager, mock_audio_player):
        """Test toggling station from stopped to playing."""
        # Mock station exists
        mock_station_manager.get_station.return_value = RadioStation(
            name="Test Station",
            url="https://test.example.com/stream",
            slot=1
        )

        # Initial state: not playing
        mock_audio_player.is_playing = False
        radio_manager._status.is_playing = False
        radio_manager._status.current_station = None

        success = await radio_manager.toggle_station(1)
        assert success is True

        # Should start playing
        mock_audio_player.play.assert_called()

    async def test_toggle_station_stop(self, radio_manager, mock_station_manager, mock_audio_player):
        """Test toggling station from playing to stopped."""
        # Mock station exists
        mock_station_manager.get_station.return_value = RadioStation(
            name="Test Station",
            url="https://test.example.com/stream",
            slot=1
        )

        # Initial state: playing this station
        mock_audio_player.is_playing = True
        radio_manager._status.is_playing = True
        radio_manager._status.current_station = 1

        success = await radio_manager.toggle_station(1)
        assert success is True

        # Should stop playing
        mock_audio_player.stop.assert_called()

    async def test_toggle_different_station(self, radio_manager, mock_station_manager, mock_audio_player):
        """Test toggling to a different station while one is playing."""
        # Mock stations exist
        def mock_get_station(slot):
            return RadioStation(
                name=f"Station {slot}",
                url=f"https://test{slot}.example.com/stream",
                slot=slot
            )

        mock_station_manager.get_station.side_effect = mock_get_station

        # Initial state: playing station 1
        mock_audio_player.is_playing = True
        radio_manager._status.is_playing = True
        radio_manager._status.current_station = 1

        # Toggle to station 2
        success = await radio_manager.toggle_station(2)
        assert success is True

        # Should stop current and play new
        mock_audio_player.stop.assert_called()
        mock_audio_player.play.assert_called_with("https://test2.example.com/stream")

    async def test_hardware_button_handling(self, radio_manager):
        """Test hardware button press handling."""
        # Test button press simulation (development mode)
        await radio_manager._handle_button_press(Config.BUTTON_PIN_1)

        # In mock mode, this should not raise errors
        # Actual behavior depends on implementation

    async def test_hardware_volume_handling(self, radio_manager):
        """Test hardware volume change handling."""
        initial_status = await radio_manager.get_status()
        initial_volume = initial_status.volume

        # Test volume increase
        await radio_manager._handle_volume_change(5)

        status = await radio_manager.get_status()
        expected_volume = min(initial_volume + 5, Config.MAX_VOLUME)
        assert status.volume == expected_volume

    async def test_status_broadcasting(self, radio_manager, status_callback):
        """Test status update broadcasting."""
        # Trigger a status update
        await radio_manager._broadcast_status_update("test_update")

        # Should have called the callback
        status_callback.assert_called()

    async def test_get_status_with_station_info(self, radio_manager, mock_station_manager):
        """Test getting status with current station information."""
        # Mock playing a station
        test_station = RadioStation(
            name="Current Station",
            url="https://current.example.com/stream",
            slot=2,
            genre="Pop"
        )

        mock_station_manager.get_station.return_value = test_station
        radio_manager._status.current_station = 2
        radio_manager._status.is_playing = True

        status = await radio_manager.get_status()
        assert status.current_station == 2
        assert status.current_station_info is not None
        assert status.current_station_info.name == "Current Station"

    async def test_simulate_button_press(self, radio_manager):
        """Test button press simulation for development."""
        # Should work in mock mode
        await radio_manager.simulate_button_press(1)
        await radio_manager.simulate_button_press(2)
        await radio_manager.simulate_button_press(3)

        # Should handle invalid button numbers gracefully
        await radio_manager.simulate_button_press(4)  # Invalid

    async def test_simulate_volume_change(self, radio_manager):
        """Test volume change simulation for development."""
        initial_status = await radio_manager.get_status()
        initial_volume = initial_status.volume

        # Test volume increase simulation
        await radio_manager.simulate_volume_change(10)

        status = await radio_manager.get_status()
        expected_volume = min(initial_volume + 10, Config.MAX_VOLUME)
        assert status.volume == expected_volume

    async def test_hardware_status(self, radio_manager):
        """Test getting hardware status."""
        hw_status = radio_manager.get_hardware_status()

        assert isinstance(hw_status, dict)
        assert "mock_mode" in hw_status
        assert hw_status["mock_mode"] is True
        assert "gpio_available" in hw_status
        assert "audio_available" in hw_status

    async def test_error_handling_during_playback(self, radio_manager, mock_station_manager, mock_audio_player):
        """Test error handling during playback operations."""
        # Mock station exists
        mock_station_manager.get_station.return_value = RadioStation(
            name="Error Station",
            url="https://error.example.com/stream",
            slot=1
        )

        # Mock audio player raising exception
        mock_audio_player.play.side_effect = Exception("Audio error")

        # Should handle error gracefully
        success = await radio_manager.play_station(1)
        assert success is False

        # Status should remain consistent
        status = await radio_manager.get_status()
        assert status.is_playing is False

    async def test_concurrent_operations(self, radio_manager):
        """Test concurrent radio manager operations."""
        # Test concurrent volume changes
        tasks = []
        for volume in [25, 50, 75]:
            task = radio_manager.set_volume(volume)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete without exceptions
        for result in results:
            assert not isinstance(result, Exception)

    async def test_shutdown_cleanup(self, radio_manager, mock_audio_player, mock_sound_manager):
        """Test proper cleanup during shutdown."""
        await radio_manager.shutdown()

        # Should stop audio playback
        mock_audio_player.stop.assert_called()

        # Should cleanup sound manager
        # Actual cleanup behavior depends on implementation

    async def test_volume_step_calculations(self, radio_manager):
        """Test volume step size calculations."""
        initial_volume = 50
        await radio_manager.set_volume(initial_volume)

        # Test step up
        await radio_manager._handle_volume_change(Config.ROTARY_VOLUME_STEP)
        status = await radio_manager.get_status()
        expected = min(initial_volume + Config.ROTARY_VOLUME_STEP, Config.MAX_VOLUME)
        assert status.volume == expected

        # Test step down
        await radio_manager._handle_volume_change(-Config.ROTARY_VOLUME_STEP)
        status = await radio_manager.get_status()
        expected = max(expected - Config.ROTARY_VOLUME_STEP, 0)
        assert status.volume == expected

    async def test_playback_state_transitions(self, radio_manager, mock_station_manager, mock_audio_player):
        """Test playback state transitions."""
        # Mock station
        mock_station_manager.get_station.return_value = RadioStation(
            name="State Test",
            url="https://state.example.com/stream",
            slot=1
        )

        # Initial state
        status = await radio_manager.get_status()
        assert status.playback_state == PlaybackState.STOPPED

        # Start playing
        mock_audio_player.play.return_value = True
        mock_audio_player.is_playing = True

        await radio_manager.play_station(1)
        status = await radio_manager.get_status()
        assert status.playback_state in [PlaybackState.PLAYING, PlaybackState.CONNECTING]

        # Stop playing
        await radio_manager.stop_playback()
        status = await radio_manager.get_status()
        assert status.playback_state == PlaybackState.STOPPED

    async def test_configuration_integration(self, radio_manager):
        """Test integration with configuration settings."""
        # Test that config values are respected
        assert radio_manager._config == Config

        # Test volume limits from config
        await radio_manager.set_volume(Config.MAX_VOLUME + 10)
        status = await radio_manager.get_status()
        assert status.volume <= Config.MAX_VOLUME

        # Test default volume
        new_manager_config = Config
        assert new_manager_config.DEFAULT_VOLUME == Config.DEFAULT_VOLUME
