"""
Unit tests for SoundManager WAV chime playback.

Regression: chimes are WAV files but were played with mpg123 (an MPEG-only
decoder) with errors silenced — they never played on the Pi.
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from core.sound_manager import SoundManager, SystemEvent

pytestmark = pytest.mark.asyncio


@pytest.fixture
def sounds_dir(tmp_path):
    d = tmp_path / "sounds"
    d.mkdir()
    # Real-looking (>200 byte) WAV placeholders so play_sound finds them
    for name in ("success.wav", "error.wav"):
        (d / name).write_bytes(b"RIFF" + b"\x00" * 300)
    return d


@pytest.fixture
def manager(sounds_dir):
    sm = SoundManager(sounds_dir, mock_mode=False)
    return sm


def spawn_mock():
    proc = AsyncMock()
    proc.returncode = 0
    return AsyncMock(return_value=proc)


@pytest.mark.unit
class TestChimePlayback:
    async def test_pulse_backend_uses_paplay_with_volume(self, manager, sounds_dir):
        manager._audio_backend = "pulse"
        with patch("core.sound_manager.asyncio.create_subprocess_exec", spawn_mock()) as spawn:
            await manager.play_sound(SystemEvent.CONNECTION_SUCCESS, volume=40)

        args = spawn.call_args.args
        assert args[0] == "paplay"
        assert args[1] == f"--volume={int(40 / 100 * 65536)}"
        assert args[2] == str(sounds_dir / "success.wav")

    async def test_volume_mapping_bounds(self, manager):
        manager._audio_backend = "pulse"
        for volume, expected in [(0, 0), (100, 65536), (150, 65536), (-5, 0)]:
            with patch("core.sound_manager.asyncio.create_subprocess_exec", spawn_mock()) as spawn:
                await manager.play_sound(SystemEvent.ERROR, volume=volume)
            assert spawn.call_args.args[1] == f"--volume={expected}", f"volume={volume}"

    async def test_alsa_backend_uses_aplay(self, manager, sounds_dir, monkeypatch):
        manager._audio_backend = "alsa"
        monkeypatch.setenv("ALSA_DEVICE", "hw:Test")
        with patch("core.sound_manager.asyncio.create_subprocess_exec", spawn_mock()) as spawn:
            await manager.play_sound(SystemEvent.ERROR, volume=40)

        args = spawn.call_args.args
        assert args[0] == "aplay"
        assert "-q" in args and "-D" in args and "hw:Test" in args
        assert args[-1] == str(sounds_dir / "error.wav")

    async def test_mpg123_never_used_for_chimes(self, manager):
        for backend in ("pulse", "alsa"):
            manager._audio_backend = backend
            with patch("core.sound_manager.asyncio.create_subprocess_exec", spawn_mock()) as spawn:
                await manager.play_sound(SystemEvent.ERROR)
            assert spawn.call_args.args[0] != "mpg123"


@pytest.mark.unit
class TestInitialization:
    async def test_missing_player_falls_back_to_mock(self, sounds_dir):
        sm = SoundManager(sounds_dir, mock_mode=False)
        missing = AsyncMock()
        missing.returncode = 1
        missing.wait = AsyncMock(return_value=1)
        with patch("core.sound_manager.asyncio.create_subprocess_exec",
                   AsyncMock(return_value=missing)):
            await sm.initialize()
        assert sm.mock_mode is True

    async def test_pulse_socket_selects_paplay(self, sounds_dir, tmp_path, monkeypatch):
        socket = tmp_path / "pulse.sock"
        socket.touch()
        monkeypatch.setenv("PULSE_SERVER", f"unix:{socket}")

        sm = SoundManager(sounds_dir, mock_mode=False)
        found = AsyncMock()
        found.returncode = 0
        found.wait = AsyncMock(return_value=0)
        with patch("core.sound_manager.asyncio.create_subprocess_exec",
                   AsyncMock(return_value=found)) as spawn:
            await sm.initialize()

        assert sm._audio_backend == "pulse"
        assert sm._player_cmd == "paplay"
        assert spawn.call_args_list[0].args[:2] == ("which", "paplay")
        assert sm.mock_mode is False
