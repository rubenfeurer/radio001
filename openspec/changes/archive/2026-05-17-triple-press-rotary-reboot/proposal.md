## Why

Triple press detection on the rotary knob already exists in `GPIOController._handle_triple_press` but the method only logs a warning — no callback is wired and no action is taken. This change completes the implementation by connecting the triple press to a host Pi reboot, giving users a hands-on way to restart the device without SSH.

## What Changes

- Add `triple_press_callback` parameter to `GPIOController.__init__` (mirrors existing `long_press_callback` pattern)
- Wire `_handle_triple_press` to invoke the callback instead of only logging
- Add `POST /api/system/reboot` endpoint that reboots the Pi host via `subprocess`
- Wire `RadioManager._initialize_hardware` to pass a `_handle_triple_press_event` callback that calls the reboot endpoint internally
- Add `simulate_triple_press` mock method to `GPIOController` (mirrors `simulate_long_press`)

## Capabilities

### New Capabilities
- `rotary-triple-press-reboot`: Triple press on rotary knob triggers a host Pi reboot. Covers detection wiring, reboot execution, and the API endpoint.

### Modified Capabilities

(none — no existing spec-level requirements change)

## Impact

- `backend/hardware/gpio_controller.py` — add `triple_press_callback`, wire `_handle_triple_press`, add `simulate_triple_press`
- `backend/core/radio_manager.py` — add `_handle_triple_press_event`, pass it to `GPIOController`
- `backend/api/routes/system.py` — add `POST /reboot` endpoint
- Container runs `privileged: true` so `subprocess.run(["reboot"])` reaches the host kernel
