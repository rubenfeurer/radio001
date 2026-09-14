# Tasks — fix-hardware-button-bugs

## 1. Fix triple-press detection (gpio_controller)

- [x] 1.1 Add `self._last_release_times: Dict[int, float] = {}` to `GPIOController.__init__` in `backend/hardware/gpio_controller.py`, and clear/initialize it wherever `_press_counts` is reset (init at lines ~126 and cleanup at ~151)
- [x] 1.2 Rewrite `_check_triple_press(gpio_pin, release_time)`: compare `release_time` against `self._last_release_times.get(gpio_pin)` (not `_last_press_times`); if no prior release or gap ≥ `TRIPLE_PRESS_INTERVAL`, set count to 1; else increment; fire `_handle_triple_press` only when count reaches 3, then reset count to 0; always store `release_time` in `_last_release_times`
- [x] 1.3 Verify `simulate_triple_press` (line ~420) still produces a detected triple press with the new semantics (three simulated presses, inter-release gaps under the interval)

## 2. Fix long-press WiFi toggle (radio_manager)

- [x] 2.1 In `backend/core/radio_manager.py` `_handle_long_press_event`, change line 401 to `await self._wifi_manager.switch_to_host_mode()` and line 404 to `await self._wifi_manager.switch_to_client_mode()`

## 3. Unit tests — GPIO press handling

- [x] 3.1 Create `backend/tests/hardware/__init__.py` and `backend/tests/hardware/test_gpio_controller.py` with a fixture building a mock-mode `GPIOController` (lightweight config with `ROTARY_SW`, `LONG_PRESS_DURATION`, `TRIPLE_PRESS_INTERVAL`; `AsyncMock` button/long-press/triple-press callbacks) driven via `_handle_button_press` / `_handle_button_release` with explicit timestamps
- [x] 3.2 Test short press: press+release under `LONG_PRESS_DURATION` awaits `button_callback` once; long-press and triple-press callbacks not invoked
- [x] 3.3 Test long press: release after ≥ `LONG_PRESS_DURATION` does not invoke the short-press callback; `_handle_long_press` awaits `long_press_callback`
- [x] 3.4 Test triple press fires: three presses with inter-release gaps < `TRIPLE_PRESS_INTERVAL` invoke `triple_press_callback` exactly once and reset the count
- [x] 3.5 Regression test: exactly two presses NEVER invoke `triple_press_callback` — cover both rapid succession and widely spaced (e.g. minutes apart) timestamps
- [x] 3.6 Test count reset: two fast presses, a gap > `TRIPLE_PRESS_INTERVAL`, then two more fast presses never fire; a fresh three-press chain after a gap does fire

## 4. Unit tests — long-press WiFi toggle awaits

- [x] 4.1 Add tests for `RadioManager._handle_long_press_event` (in `backend/tests/unit/test_radio_manager.py` or a focused module): with an `AsyncMock` WiFi manager reporting connected client mode, assert `switch_to_host_mode.assert_awaited_once()`; reporting non-client/hotspot mode, assert `switch_to_client_mode.assert_awaited_once()`
- [x] 4.2 Add a failure-path test: awaited mode-switch coroutine raising an exception results in `play_error_sound` being awaited

## 5. Verify

- [x] 5.1 Run the backend test suite (new hardware tests plus existing tests) and confirm all pass
- [x] 5.2 Run lint/type checks per project CI (quick CI on `develop`)
- [ ] 5.3 On the test Pi: confirm three fast clicks of the rotary switch reboot, two clicks (fast and spaced) do not, and a long press actually toggles client ↔ hotspot mode
