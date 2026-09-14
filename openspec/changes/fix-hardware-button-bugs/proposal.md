# Fix Hardware Button Bugs

## Why

Two critical bugs from the September 2026 project review (`docs/project-review-2026-09.md`, Critical items 2 and 3) break the rotary switch gestures:

1. **Two knob clicks reboot the Pi.** `backend/hardware/gpio_controller.py:275-288` — triple-press detection compares the release time against the press *start* time (always less than the 0.5 s `TRIPLE_PRESS_INTERVAL`, since it equals the press duration), press counts never decay over time, and the reboot fires at count >= 2. Any two short presses of the rotary switch — even minutes apart — reboot the Pi.
2. **Long-press hotspot toggle is a no-op.** `backend/core/radio_manager.py:401,404` call the async `WiFiManager.switch_to_host_mode()` / `switch_to_client_mode()` without `await`, so the coroutines are never executed: the success chime plays, the log claims a switch, nothing happens.

The hardware layer has zero unit tests (`gpio_controller` is untested), which is exactly why both bugs shipped.

## What Changes

- Fix `_check_triple_press` in `backend/hardware/gpio_controller.py` so a reboot requires **three** presses, each occurring within `TRIPLE_PRESS_INTERVAL` of the previous press's *release*, and press counts reset once the interval is exceeded. Two presses — at any spacing — never trigger the reboot.
- Add the missing `await` on `switch_to_host_mode()` / `switch_to_client_mode()` in `RadioManager._handle_long_press_event` (`backend/core/radio_manager.py:401,404`) so the long-press WiFi mode toggle actually executes.
- Add unit tests for `GPIOController` press handling: short press, long press, triple-press timing (three fast presses fire, two presses never fire, presses spaced beyond the interval reset the count), and a test that `_handle_long_press_event` genuinely awaits the WiFi manager coroutine (via `AsyncMock` awaited assertions).

## Capabilities

### New Capabilities

None — this change corrects and hardens existing capabilities.

### Modified Capabilities

- `rotary-triple-press-reboot`: The "Triple Press Triggers Pi Reboot" requirement is corrected to demand three presses each within `TRIPLE_PRESS_INTERVAL` of the previous release, with count reset on timeout, and an explicit guarantee that two presses never reboot. Test-coverage requirements for press detection are added.
- `hotspot-configuration`: The "Hardware-Triggered WiFi Mode Toggle" requirement is tightened: the mode-switch coroutines SHALL be awaited so the switch actually executes (not merely "called"). A test-coverage requirement asserting the coroutine is awaited is added.

## Impact

- **Code**: `backend/hardware/gpio_controller.py` (`_check_triple_press`, press-count state), `backend/core/radio_manager.py` (`_handle_long_press_event`).
- **Tests**: new `backend/tests` module for `GPIOController` press handling; new/extended tests for `RadioManager._handle_long_press_event` awaiting the WiFi manager.
- **Behavior on device**: rotary switch double-click no longer reboots the Pi; long press actually toggles client/hotspot mode.
- **No API, dependency, or deployment changes.** No changes to `WiFiManager` itself (the HTTP path already awaits correctly).
