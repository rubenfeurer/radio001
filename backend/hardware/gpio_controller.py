"""
GPIO Controller - Handles physical button and rotary encoder control.

This module provides the GPIOController class which manages:
- 3 physical buttons for station control (GPIO pins)
- Rotary encoder for volume control with push button
- Button press detection (short, long, triple press)
- Hardware event callbacks for radio system integration
- Mock mode for development without Raspberry Pi hardware
"""

import asyncio
import logging
import time
from typing import Optional, Callable, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ButtonEvent(str, Enum):
    """Types of button events that can be detected."""
    SHORT_PRESS = "short_press"
    LONG_PRESS = "long_press"
    TRIPLE_PRESS = "triple_press"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"


class GPIOController:
    """
    GPIO controller for physical radio controls.

    Manages physical buttons and rotary encoder, providing event callbacks
    for integration with the radio system. Supports mock mode for development.
    """

    def __init__(self,
                 config: Any,
                 button_callback: Optional[Callable[[int], None]] = None,
                 volume_callback: Optional[Callable[[int], None]] = None,
                 long_press_callback: Optional[Callable[[int], None]] = None,
                 mock_mode: bool = True):
        """
        Initialize the GPIO controller.

        Args:
            config: Application configuration with GPIO pin definitions
            button_callback: Callback for button press events (receives button pin)
            volume_callback: Callback for volume changes (receives change amount)
            long_press_callback: Callback for long press events (receives gpio pin)
            mock_mode: Whether to run in mock mode (no actual GPIO)
        """
        self.config = config
        self.button_callback = button_callback
        self.volume_callback = volume_callback
        self.long_press_callback = long_press_callback
        self.mock_mode = mock_mode

        # GPIO state tracking
        self._button_states: Dict[int, bool] = {}
        self._last_press_times: Dict[int, float] = {}
        self._press_counts: Dict[int, int] = {}
        self._long_press_tasks: Dict[int, asyncio.Task] = {}

        # Rotary encoder state
        self._last_rotation_time: float = 0
        self._rotation_debounce: float = getattr(config, "ROTARY_DEBOUNCE", 0.05)

        # Hardware objects (lgpio)
        self._pi = None       # gpiochip handle
        self._lgpio = None    # lgpio module reference
        self._callbacks: Dict[int, Any] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None  # captured at init for thread-safe scheduling

        # Mock mode simulation
        self._mock_button_states: Dict[int, bool] = {
            config.BUTTON_PIN_1: False,
            config.BUTTON_PIN_2: False,
            config.BUTTON_PIN_3: False,
            config.ROTARY_SW: False
        }

        logger.info(f"GPIOController initialized (mock_mode={mock_mode})")

    async def initialize(self):
        """Initialize GPIO hardware or mock interface."""
        try:
            self._loop = asyncio.get_event_loop()
            if not self.mock_mode:
                await self._initialize_hardware()
            else:
                await self._initialize_mock()

            logger.info("GPIOController initialization complete")

        except Exception as e:
            logger.error(f"GPIOController initialization failed: {e}", exc_info=True)
            # Fall back to mock mode on hardware failure
            self.mock_mode = True
            await self._initialize_mock()

    async def _initialize_hardware(self):
        """Initialize actual GPIO hardware via lgpio (no daemon required)."""
        try:
            import lgpio
            self._lgpio = lgpio

            handle = lgpio.gpiochip_open(0)
            if handle < 0:
                raise RuntimeError(f"Failed to open gpiochip0: error {handle}")
            self._pi = handle

            logger.info("Opened gpiochip0 via lgpio")

            # Setup button pins (alert mode = edge detection with pull-up)
            for pin in [self.config.BUTTON_PIN_1, self.config.BUTTON_PIN_2,
                        self.config.BUTTON_PIN_3, self.config.ROTARY_SW]:
                lgpio.gpio_claim_alert(handle, pin, lgpio.BOTH_EDGES, lgpio.SET_PULL_UP)
                lgpio.gpio_set_debounce_micros(handle, pin, 5000)  # 5ms hardware debounce
                cb = lgpio.callback(handle, pin, lgpio.BOTH_EDGES, self._handle_button_event)
                self._callbacks[pin] = cb
                self._button_states[pin] = False  # pulled-up = not pressed
                self._last_press_times[pin] = 0
                self._press_counts[pin] = 0

            # Setup rotary encoder pins (DT is read-only, CLK triggers alerts)
            lgpio.gpio_claim_input(handle, self.config.ROTARY_DT, lgpio.SET_PULL_UP)
            lgpio.gpio_claim_alert(handle, self.config.ROTARY_CLK, lgpio.BOTH_EDGES, lgpio.SET_PULL_UP)
            clk_cb = lgpio.callback(handle, self.config.ROTARY_CLK, lgpio.BOTH_EDGES, self._handle_rotary_event)
            self._callbacks[self.config.ROTARY_CLK] = clk_cb

            logger.info("GPIO hardware initialized successfully via lgpio")

        except ImportError:
            raise RuntimeError("lgpio library not available")
        except Exception as e:
            logger.error(f"Hardware initialization failed: {e}")
            raise

    async def _initialize_mock(self):
        """Initialize mock GPIO interface for development."""
        logger.info("GPIO mock interface initialized")

        # Initialize mock button states
        for pin in [self.config.BUTTON_PIN_1, self.config.BUTTON_PIN_2, self.config.BUTTON_PIN_3, self.config.ROTARY_SW]:
            self._mock_button_states[pin] = False
            self._button_states[pin] = False
            self._last_press_times[pin] = 0
            self._press_counts[pin] = 0

    def _handle_button_event(self, chip: int, gpio_pin: int, level: int, timestamp: int):
        """Handle GPIO button events (hardware mode). Called by lgpio callback."""
        try:
            current_time = time.time()
            is_pressed = (level == 0)  # Active low (pulled up normally)

            if is_pressed and not self._button_states.get(gpio_pin, False):
                # Button pressed
                self._button_states[gpio_pin] = True
                self._loop.call_soon_threadsafe(
                    asyncio.ensure_future,
                    self._handle_button_press(gpio_pin, current_time),
                )

            elif not is_pressed and self._button_states.get(gpio_pin, False):
                # Button released
                self._button_states[gpio_pin] = False
                self._loop.call_soon_threadsafe(
                    asyncio.ensure_future,
                    self._handle_button_release(gpio_pin, current_time),
                )

        except Exception as e:
            logger.error(f"Error handling button event on pin {gpio_pin}: {e}", exc_info=True)

    def _handle_rotary_event(self, chip: int, gpio_pin: int, level: int, timestamp: int):
        """Handle rotary encoder events (hardware mode). Called by lgpio callback."""
        try:
            current_time = time.time()

            # Debounce rotary events
            if current_time - self._last_rotation_time < self._rotation_debounce:
                return

            if gpio_pin == self.config.ROTARY_CLK and level == 1:  # Rising edge on clock
                # Read data pin to determine direction
                dt_state = self._lgpio.gpio_read(self._pi, self.config.ROTARY_DT)

                if dt_state == 0:
                    # Clockwise rotation
                    direction = 1 if self.config.ROTARY_CLOCKWISE_INCREASES else -1
                else:
                    # Counter-clockwise rotation
                    direction = -1 if self.config.ROTARY_CLOCKWISE_INCREASES else 1

                volume_change = direction * self.config.ROTARY_VOLUME_STEP
                self._loop.call_soon_threadsafe(
                    asyncio.ensure_future,
                    self._handle_volume_change(volume_change),
                )

                self._last_rotation_time = current_time

        except Exception as e:
            logger.error(f"Error handling rotary event: {e}", exc_info=True)

    async def _handle_button_press(self, gpio_pin: int, press_time: float):
        """Handle button press start."""
        try:
            # Debounce: ignore presses within 50ms of last release
            last = self._last_press_times.get(gpio_pin, 0)
            if press_time - last < 0.05:
                return

            logger.debug(f"Button press detected on pin {gpio_pin}")

            # Record press time so release can compute duration
            self._last_press_times[gpio_pin] = press_time

            # Start long press detection for rotary switch
            if gpio_pin == self.config.ROTARY_SW:
                task = asyncio.create_task(self._monitor_long_press(gpio_pin, press_time))
                self._long_press_tasks[gpio_pin] = task

        except Exception as e:
            logger.error(f"Error handling button press on pin {gpio_pin}: {e}", exc_info=True)

    async def _handle_button_release(self, gpio_pin: int, release_time: float):
        """Handle button release."""
        try:
            press_time = self._last_press_times.get(gpio_pin, 0)
            if press_time == 0:
                # No recorded press (debounced away) — ignore release
                return

            press_duration = release_time - press_time

            # Cancel long press monitoring
            if gpio_pin in self._long_press_tasks:
                self._long_press_tasks[gpio_pin].cancel()
                del self._long_press_tasks[gpio_pin]

            # Check for triple press (rotary switch only)
            if gpio_pin == self.config.ROTARY_SW:
                await self._check_triple_press(gpio_pin, release_time)

            # Handle short press if not a long press
            if press_duration < self.config.LONG_PRESS_DURATION:
                await self._handle_short_press(gpio_pin)

            # Record release time so next press debounce works correctly
            self._last_press_times[gpio_pin] = release_time

        except Exception as e:
            logger.error(f"Error handling button release on pin {gpio_pin}: {e}", exc_info=True)

    async def _monitor_long_press(self, gpio_pin: int, press_time: float):
        """Monitor for long press detection."""
        try:
            await asyncio.sleep(self.config.LONG_PRESS_DURATION)

            # If we get here, it's a long press
            if self._button_states.get(gpio_pin, False):
                logger.info(f"Long press detected on pin {gpio_pin}")
                await self._handle_long_press(gpio_pin)

        except asyncio.CancelledError:
            # Normal cancellation when button is released
            pass
        except Exception as e:
            logger.error(f"Error monitoring long press on pin {gpio_pin}: {e}", exc_info=True)

    async def _check_triple_press(self, gpio_pin: int, press_time: float):
        """Check for triple press sequence."""
        try:
            last_press = self._last_press_times.get(gpio_pin, 0)

            if press_time - last_press < self.config.TRIPLE_PRESS_INTERVAL:
                self._press_counts[gpio_pin] += 1

                if self._press_counts[gpio_pin] >= 2:  # Third press
                    logger.info(f"Triple press detected on pin {gpio_pin}")
                    await self._handle_triple_press(gpio_pin)
                    self._press_counts[gpio_pin] = 0
            else:
                self._press_counts[gpio_pin] = 1

        except Exception as e:
            logger.error(f"Error checking triple press on pin {gpio_pin}: {e}", exc_info=True)

    async def _handle_short_press(self, gpio_pin: int):
        """Handle short button press."""
        try:
            if self.button_callback:
                await self.button_callback(gpio_pin)

        except Exception as e:
            logger.error(f"Error in button callback for pin {gpio_pin}: {e}", exc_info=True)

    async def _handle_long_press(self, gpio_pin: int):
        """Handle long button press."""
        try:
            logger.info(f"Long press detected on pin {gpio_pin}")
            if self.long_press_callback:
                await self.long_press_callback(gpio_pin)
            else:
                logger.warning(f"Long press on pin {gpio_pin} but no long_press_callback registered")

        except Exception as e:
            logger.error(f"Error handling long press on pin {gpio_pin}: {e}", exc_info=True)

    async def _handle_triple_press(self, gpio_pin: int):
        """Handle triple button press."""
        try:
            if gpio_pin == self.config.ROTARY_SW:
                logger.warning("Triple press detected - system reset sequence")
                # Could trigger system reset/reboot

        except Exception as e:
            logger.error(f"Error handling triple press on pin {gpio_pin}: {e}", exc_info=True)

    async def _handle_volume_change(self, change: int):
        """Handle volume change from rotary encoder."""
        try:
            if self.volume_callback:
                await self.volume_callback(change)

        except Exception as e:
            logger.error(f"Error in volume callback with change {change}: {e}", exc_info=True)

    # =============================================================================
    # Public Mock Interface (Development)
    # =============================================================================

    async def simulate_button_press(self, button: int, duration: float = 0.1):
        """
        Simulate button press for development/testing.

        Args:
            button: Button number (1, 2, 3) or GPIO pin number
            duration: Press duration in seconds
        """
        if not self.mock_mode:
            logger.warning("simulate_button_press called in non-mock mode")
            return

        # Map button numbers to GPIO pins
        pin_map = {
            1: self.config.BUTTON_PIN_1,
            2: self.config.BUTTON_PIN_2,
            3: self.config.BUTTON_PIN_3,
            4: self.config.ROTARY_SW  # Rotary switch
        }

        gpio_pin = pin_map.get(button, button)

        if gpio_pin not in self._mock_button_states:
            logger.warning(f"Invalid button/pin for simulation: {button}")
            return

        try:
            logger.info(f"Simulating button press: {button} (pin {gpio_pin}) for {duration}s")

            # Simulate press
            current_time = time.time()
            await self._handle_button_press(gpio_pin, current_time)

            # Wait for duration
            await asyncio.sleep(duration)

            # Simulate release
            await self._handle_button_release(gpio_pin, time.time())

        except Exception as e:
            logger.error(f"Error simulating button press: {e}", exc_info=True)

    async def simulate_volume_change(self, direction: int):
        """
        Simulate rotary encoder volume change.

        Args:
            direction: 1 for clockwise, -1 for counter-clockwise
        """
        if not self.mock_mode:
            logger.warning("simulate_volume_change called in non-mock mode")
            return

        try:
            volume_change = direction * self.config.ROTARY_VOLUME_STEP
            logger.info(f"Simulating volume change: {volume_change}")
            await self._handle_volume_change(volume_change)

        except Exception as e:
            logger.error(f"Error simulating volume change: {e}", exc_info=True)

    async def simulate_long_press(self, button: int = 4):
        """
        Simulate long press (typically on rotary switch).

        Args:
            button: Button number (default 4 = rotary switch)
        """
        if not self.mock_mode:
            logger.warning("simulate_long_press called in non-mock mode")
            return

        pin_map = {1: self.config.BUTTON_PIN_1, 2: self.config.BUTTON_PIN_2,
                  3: self.config.BUTTON_PIN_3, 4: self.config.ROTARY_SW}

        gpio_pin = pin_map.get(button, self.config.ROTARY_SW)

        try:
            logger.info(f"Simulating long press on button {button}")
            await self._handle_long_press(gpio_pin)

        except Exception as e:
            logger.error(f"Error simulating long press: {e}", exc_info=True)

    # =============================================================================
    # System Methods
    # =============================================================================

    def get_button_states(self) -> Dict[int, bool]:
        """Get current button states."""
        if self.mock_mode:
            return self._mock_button_states.copy()
        else:
            return self._button_states.copy()

    def get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware status information."""
        return {
            "mock_mode": self.mock_mode,
            "driver": "lgpio" if not self.mock_mode else "mock",
            "connected": not self.mock_mode and self._pi is not None,
            "button_count": 4,
            "rotary_encoder": True,
        }

    async def test_all_buttons(self):
        """Test all buttons (mock mode only)."""
        if not self.mock_mode:
            logger.warning("test_all_buttons only available in mock mode")
            return

        logger.info("Testing all buttons...")

        for button in [1, 2, 3, 4]:
            await self.simulate_button_press(button, 0.2)
            await asyncio.sleep(0.3)

        # Test volume changes
        await self.simulate_volume_change(1)
        await asyncio.sleep(0.2)
        await self.simulate_volume_change(-1)

        logger.info("Button test complete")

    async def cleanup(self):
        """Cleanup GPIO resources."""
        try:
            # Cancel any pending long press tasks
            for task in self._long_press_tasks.values():
                if not task.done():
                    task.cancel()

            self._long_press_tasks.clear()

            # Cleanup hardware
            if not self.mock_mode and self._pi is not None:
                # Cancel callbacks
                for cb in self._callbacks.values():
                    if cb:
                        cb.cancel()
                self._callbacks.clear()

                # Close gpiochip handle
                self._lgpio.gpiochip_close(self._pi)
                self._pi = None
                self._lgpio = None

            logger.info("GPIOController cleanup complete")

        except Exception as e:
            logger.error(f"Error during GPIOController cleanup: {e}", exc_info=True)
