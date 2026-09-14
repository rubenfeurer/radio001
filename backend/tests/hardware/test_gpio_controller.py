"""
Unit tests for GPIOController press handling.

Drives the async press/release handlers directly with synthetic timestamps —
no sleeping on real thresholds, fully deterministic. Covers the triple-press
regression where any two short presses rebooted the Pi (press counts compared
against press start time instead of the previous release, and fired at 2).
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

from hardware.gpio_controller import GPIOController
from main import Config

pytestmark = pytest.mark.asyncio

SW = Config.ROTARY_SW
INTERVAL = Config.TRIPLE_PRESS_INTERVAL
LONG = Config.LONG_PRESS_DURATION


@pytest_asyncio.fixture
async def controller():
    ctrl = GPIOController(
        config=Config,
        button_callback=AsyncMock(),
        volume_callback=AsyncMock(),
        long_press_callback=AsyncMock(),
        triple_press_callback=AsyncMock(),
        mock_mode=True,
    )
    await ctrl.initialize()
    yield ctrl
    await ctrl.cleanup()


async def click(ctrl, t, duration=0.1, pin=SW):
    """Simulate one press+release with explicit timestamps; returns release time."""
    await ctrl._handle_button_press(pin, t)
    release = t + duration
    await ctrl._handle_button_release(pin, release)
    return release


@pytest.mark.unit
class TestShortAndLongPress:
    async def test_short_press_invokes_button_callback(self, controller):
        await click(controller, 100.0, duration=0.1)
        controller.button_callback.assert_awaited_once_with(SW)
        controller.long_press_callback.assert_not_awaited()
        controller.triple_press_callback.assert_not_awaited()

    async def test_long_press_release_suppresses_short_press_callback(self, controller):
        await click(controller, 100.0, duration=LONG + 0.5)
        controller.button_callback.assert_not_awaited()

    async def test_handle_long_press_awaits_callback(self, controller):
        await controller._handle_long_press(SW)
        controller.long_press_callback.assert_awaited_once_with(SW)


@pytest.mark.unit
class TestTriplePress:
    async def test_three_fast_presses_fire_exactly_once(self, controller):
        t = 100.0
        for _ in range(3):
            release = await click(controller, t, duration=0.1)
            t = release + INTERVAL * 0.5  # inter-release gap < INTERVAL
        controller.triple_press_callback.assert_awaited_once_with(SW)
        # Chain resets after firing
        assert controller._press_counts[SW] == 0

    async def test_two_fast_presses_never_fire(self, controller):
        t = 100.0
        for _ in range(2):
            release = await click(controller, t, duration=0.1)
            t = release + INTERVAL * 0.5
        controller.triple_press_callback.assert_not_awaited()

    async def test_two_presses_minutes_apart_never_fire(self, controller):
        # The original bug: press duration (always < INTERVAL) was compared
        # instead of the gap between presses, so this rebooted the Pi.
        await click(controller, 100.0, duration=0.1)
        await click(controller, 300.0, duration=0.1)
        controller.triple_press_callback.assert_not_awaited()

    async def test_many_spaced_presses_never_fire(self, controller):
        t = 100.0
        for _ in range(6):
            release = await click(controller, t, duration=0.1)
            t = release + INTERVAL * 3  # every gap exceeds the interval
        controller.triple_press_callback.assert_not_awaited()

    async def test_gap_resets_chain(self, controller):
        # 2 fast + gap + 2 fast → never fires
        t = 100.0
        for _ in range(2):
            release = await click(controller, t, duration=0.1)
            t = release + INTERVAL * 0.5
        t = release + INTERVAL * 4
        for _ in range(2):
            release = await click(controller, t, duration=0.1)
            t = release + INTERVAL * 0.5
        controller.triple_press_callback.assert_not_awaited()

        # Fresh 3-chain after the gap does fire
        t = release + INTERVAL * 4
        for _ in range(3):
            release = await click(controller, t, duration=0.1)
            t = release + INTERVAL * 0.5
        controller.triple_press_callback.assert_awaited_once_with(SW)

    async def test_simulate_triple_press_helper_fires(self, controller):
        await controller.simulate_triple_press()
        controller.triple_press_callback.assert_awaited_once_with(SW)
