"""
Unit tests for AudioPlayer stream-death reporting and stderr handling.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from hardware.audio_player import AudioPlayer

pytestmark = pytest.mark.asyncio


class FakeProcess:
    """Stands in for an mpg123 asyncio subprocess."""

    def __init__(self):
        self._exit_event = asyncio.Event()
        self.returncode = None
        self.terminated = False

    async def wait(self):
        await self._exit_event.wait()
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.exit(0)

    def kill(self):
        self.exit(-9)

    def exit(self, code=1):
        self.returncode = code
        self._exit_event.set()


@pytest.fixture
def statuses():
    return []


@pytest.fixture
def player(statuses):
    async def record(status):
        statuses.append(status)

    p = AudioPlayer(mock_mode=False, status_callback=record)
    p._is_initialized = True
    p._audio_backend = "pulse"
    return p


async def start_playing(player, fake_process, url="http://stream.example/radio"):
    with patch.object(player, "_resolve_url", AsyncMock(return_value=url)), \
         patch("hardware.audio_player.asyncio.create_subprocess_exec",
               AsyncMock(return_value=fake_process)) as spawn:
        assert await player.play(url) is True
    return spawn


@pytest.mark.unit
class TestAudioPlayerExitReporting:
    async def test_spawn_uses_devnull_stderr(self, player):
        proc = FakeProcess()
        spawn = await start_playing(player, proc)
        kwargs = spawn.call_args.kwargs
        assert kwargs["stderr"] == asyncio.subprocess.DEVNULL
        assert kwargs["stdout"] == asyncio.subprocess.DEVNULL
        proc.exit(0)

    async def test_unexpected_exit_fires_callback_with_marker(self, player, statuses):
        proc = FakeProcess()
        await start_playing(player, proc)
        statuses.clear()

        proc.exit(1)  # mpg123 dies on its own
        await asyncio.sleep(0.05)  # let the monitor task run

        assert len(statuses) == 1
        assert statuses[0]["unexpected_exit"] is True
        assert statuses[0]["is_playing"] is False
        assert player._is_playing is False

    async def test_user_stop_does_not_report_unexpected_exit(self, player, statuses):
        proc = FakeProcess()
        await start_playing(player, proc)
        statuses.clear()

        await player.stop()
        await asyncio.sleep(0.05)

        assert statuses, "stop() should emit a normal status update"
        assert all(not s["unexpected_exit"] for s in statuses)

    async def test_refresh_cache_re_resolves_url(self, player):
        url = "http://stream.example/radio"
        player._url_cache[url] = "http://stale.example/old"
        proc = FakeProcess()

        with patch.object(player, "_resolve_url",
                          AsyncMock(return_value="http://fresh.example/new")) as resolve, \
             patch("hardware.audio_player.asyncio.create_subprocess_exec",
                   AsyncMock(return_value=proc)) as spawn:
            assert await player.play(url, refresh_cache=True) is True

        resolve.assert_awaited_once_with(url)
        assert "http://fresh.example/new" in spawn.call_args.args
        assert player._url_cache[url] == "http://fresh.example/new"
        proc.exit(0)

    async def test_default_play_uses_cache(self, player):
        url = "http://stream.example/radio"
        player._url_cache[url] = "http://cached.example/live"
        proc = FakeProcess()

        with patch.object(player, "_resolve_url", AsyncMock()) as resolve, \
             patch("hardware.audio_player.asyncio.create_subprocess_exec",
                   AsyncMock(return_value=proc)) as spawn:
            assert await player.play(url) is True

        resolve.assert_not_awaited()
        assert "http://cached.example/live" in spawn.call_args.args
        proc.exit(0)
