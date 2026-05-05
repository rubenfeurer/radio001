## Context

The rotary encoder button long-press is intended to toggle WiFi mode (client ↔ hotspot). The current implementation in `RadioManager._handle_long_press_event` calls `switch_to_host_mode()` / `switch_to_client_mode()` first, then plays the sound. Because the WiFi switch may reconfigure the network interface synchronously (blocking briefly) and the radio audio stream is still running when the sound is triggered, the sound either doesn't play audibly or is lost entirely. The user hears nothing and the device silently switches to hotspot mode.

A secondary concern: the `long_press_callback` registered with `GPIOController` does not verify which GPIO pin fired. Although `GPIOController._handle_button_press` currently only starts long-press monitoring for `ROTARY_SW`, the handler in `RadioManager` should be defensive and guard against unexpected invocations.

## Goals / Non-Goals

**Goals:**
- Ensure the user hears a confirmation sound on every long-press WiFi toggle.
- Stop radio playback before the sound and mode switch so the audio device is uncontested.
- Add a pin guard in `_handle_long_press_event` so only `ROTARY_SW` triggers WiFi toggling.
- No user-facing behaviour changes beyond the sound now being audible.

**Non-Goals:**
- Adding long-press actions to the 3 station buttons (undefined; out of scope).
- Changing the long-press detection threshold or GPIO wiring.
- Modifying the WiFi switch logic itself.

## Decisions

### 1. Operation order: stop → sound → switch

**Decision**: Execute `stop_playback()` → `play_success_sound()` (or `play_error_sound()`) → `switch_to_*_mode()`.

**Rationale**: The audio device must be free for the sound to play. The WiFi switch is the most disruptive operation; placing it last means the sound is always attempted in a clean state. Playing the sound *before* switching also gives the user immediate tactile feedback that the gesture was recognised.

**Alternative considered**: Play sound *after* switch (current code). Rejected because the WiFi switch can momentarily disrupt the system audio path and the sound is inaudible.

**Alternative considered**: Play sound concurrently with switch (`asyncio.gather`). Rejected because concurrency makes ordering unpredictable and the switch may kill network-dependent audio.

### 2. Pin guard via early return

**Decision**: At the top of `_handle_long_press_event`, check `gpio_pin != config.ROTARY_SW` and log a warning + return early.

**Rationale**: Defensive programming. `GPIOController` already limits long-press monitoring to `ROTARY_SW`, but the callback contract should be explicit. Costs nothing at runtime.

### 3. No change to `GPIOController`

**Decision**: `GPIOController._handle_button_press` already restricts long-press monitoring to `ROTARY_SW` (line 222). No change needed there.

**Rationale**: The GPIO layer is correct; the bug is purely in `RadioManager`'s handler ordering.

## Risks / Trade-offs

- **Sound adds ~200–500 ms latency before WiFi switch** → Acceptable; user feedback is the goal and the delay is imperceptible.
- **`stop_playback()` under `_playback_lock` could deadlock if called from within the lock** → `_handle_long_press_event` is called from a GPIO callback, never from within `_playback_lock`. No deadlock risk.
- **WiFi switch fails after sound has played** → `play_error_sound()` is called in the `except` branch, so the user gets an error tone. The stop-first ordering means playback has already stopped; the caller will need to manually restart it. This is acceptable — mode switch failure is an edge case.

## Migration Plan

- Single-file change to `backend/core/radio_manager.py`.
- No database, API, or config changes.
- Rollback: revert the file; no state migration needed.
- Deploy by rebuilding the Docker image and restarting the container.
