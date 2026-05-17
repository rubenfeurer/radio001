## Context

`GPIOController._handle_triple_press` (line 312 in `backend/hardware/gpio_controller.py`) already detects triple press on `ROTARY_SW` but only logs a warning. No callback parameter exists for triple press, so the `RadioManager` has no way to act on it. The container runs `privileged: true` with `network_mode: host`, which means a `reboot` subprocess call reaches the Pi's host kernel directly.

## Goals / Non-Goals

**Goals:**
- Wire the existing triple press detection to a real Pi reboot
- Add `triple_press_callback` to `GPIOController` (same pattern as `long_press_callback`)
- Add `POST /api/system/reboot` so the reboot action is also reachable from the API
- Keep mock mode safe: log the event, do not actually reboot in development

**Non-Goals:**
- Audio/visual confirmation before reboot (can be added later via `SoundManager`)
- Configurable triple press action (always reboots)
- Shutdown vs. reboot distinction

## Decisions

**D1: Callback pattern, not direct coupling**
`GPIOController` gains a `triple_press_callback: Optional[Callable]` parameter, mirroring `long_press_callback`. The controller stays generic; reboot logic lives in `RadioManager._handle_triple_press_event`. Alternative — hard-code reboot inside the controller — was rejected because it breaks the separation between hardware detection and application action.

**D2: `subprocess.run(["reboot"])` for host reboot**
The container is `privileged: true` and uses `network_mode: host`, so `reboot` reaches the host kernel. Alternative was `systemctl reboot` via `/run/dbus` (also available); `reboot` is simpler and has no D-Bus dependency. A delayed async call (1 s) gives the API response time to return before the system goes down.

**D3: Reboot logic in `RadioManager`, exposed via system API**
`RadioManager._handle_triple_press_event` performs the reboot. The same logic is reachable via `POST /api/system/reboot` for future UI use. Both paths share the same subprocess call. Alternative — API-only, no direct GPIO → reboot path — would add latency and a network round-trip on the local machine unnecessarily.

**D4: Mock mode guard**
In `mock_mode=True`, `_handle_triple_press_event` logs at WARNING level and returns without executing the subprocess. This prevents accidental host reboots during development on macOS.

## Risks / Trade-offs

- **Accidental triple press**: Three quick presses reboots immediately with no undo. Mitigation: `TRIPLE_PRESS_INTERVAL` (default 0.5 s) already limits window; physical accidental triples are unlikely with the existing debounce.
- **Privileged reboot in container**: Correct for production Pi, but means any code path that reaches `reboot` will kill the host. Mitigation: mock guard is explicit and tested.
- **No graceful audio stop before reboot**: mpg123 is killed abruptly. Mitigation: acceptable for a manual reboot; can add `SoundManager` play + delay later.
