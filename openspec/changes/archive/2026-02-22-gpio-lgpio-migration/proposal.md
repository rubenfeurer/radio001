## Why

The GPIO controller uses `pigpio`, which requires a background daemon (`pigpiod`) that is not packaged for Raspberry Pi OS Trixie (64-bit). On boot the container falls back to mock mode silently, making all physical buttons and the rotary encoder non-functional. `lgpio` is already installed on the Pi OS, uses the kernel's `/dev/gpiochip0` interface directly with no daemon, and is the recommended GPIO library for modern Pi OS.

## What Changes

### New file: none

### Modified: `backend/hardware/gpio_controller.py`
- Replace `_initialize_hardware()` pigpio implementation with lgpio equivalent
- `lgpio.gpiochip_open(0)` replaces `pigpio.pi()` daemon connection
- `lgpio.gpio_claim_input(handle, pin, SET_PULL_UP)` replaces `set_mode` + `set_pull_up_down`
- `lgpio.gpio_set_alert_func(handle, pin, callback)` replaces `pi.callback()` — same edge-triggered callback model
- `_handle_button_event` and `_handle_rotary_event` callback signatures updated: lgpio passes `(chip, gpio, level, timestamp)` vs pigpio's `(gpio, level, tick)`
- `_handle_rotary_event` reads DT pin via `lgpio.gpio_read(handle, pin)` instead of `pi.read()`
- `cleanup()` calls `lgpio.gpiochip_close(handle)` instead of `pi.stop()`
- `get_hardware_info()` updated to reflect lgpio (remove pigpio_available/pigpio_version fields)

### Modified: `backend/requirements.txt`
- Remove `pigpio==1.78`
- Add `lgpio` (version unconstrained — use whatever Pi OS ships)

### Modified: `compose/docker-compose.prod.yml`
- Add `/dev/gpiochip0` device mount so the container can access the GPIO chip

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `gpio-control`: implementation backend changes from pigpio+daemon to lgpio+gpiochip; external behavior (button press toggles slot, rotary changes volume) is unchanged

## Impact

- `backend/hardware/gpio_controller.py`: hardware init and callback methods rewritten; mock mode and public API unchanged
- `backend/requirements.txt`: pigpio removed, lgpio added
- `compose/docker-compose.prod.yml`: add `/dev/gpiochip0:/dev/gpiochip0` device
- No frontend changes
- No API changes
- Docker rebuild required (new dependency)
