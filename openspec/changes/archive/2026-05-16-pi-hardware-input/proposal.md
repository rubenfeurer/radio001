## Why

Physical station buttons and the rotary encoder volume knob are completely unresponsive on the Pi because the GPIO subsystem always falls back to mock mode. Root cause: the `lgpio` Python package is not installed in the Docker image — the `pip install lgpio` step in `Dockerfile.backend` silently fails (wrapped in `|| true`), and lgpio is absent from `requirements.lock`. Without lgpio, `GPIOController` catches the `ImportError` and sets `_gpio_controller = None`, so no hardware events are ever processed.

## What Changes

- Fix `Dockerfile.backend` to reliably install lgpio (and its C runtime `liblgpio1`) for the arm64/Pi build — remove the silent-fail `|| true` pattern and ensure installation is architecture-aware
- Add `radio` user to the `gpio` group in the Dockerfile so the container process can open `/dev/gpiochip0` (currently only `audio` and `netdev` groups are assigned)
- Add `gpio` group to the container user in `compose.prod.yml` via `group_add` as a belt-and-suspenders runtime guard
- Improve startup diagnostics: log clearly when lgpio fails to load and why, rather than silently entering mock mode

## Capabilities

### New Capabilities

- `hardware-gpio-input`: Physical hardware input — station buttons and rotary encoder volume control working in production on Pi

### Modified Capabilities

_(none — the radio-integration spec already describes the intended behavior; this change makes the implementation match it)_

## Impact

- `docker/Dockerfile.backend` — lgpio installation fix; `gpio` group assignment
- `docker/compose.prod.yml` — `group_add` for gpio
- `backend/hardware/gpio_controller.py` — improved error diagnostics on init failure
- No API changes, no frontend changes, no schema changes
