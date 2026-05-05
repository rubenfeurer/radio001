## Why

Long-pressing the rotary encoder button does not play any audible feedback sound and incorrectly toggles the device to hotspot mode — the sound is intended to confirm the action but fires after the WiFi switch, which may be blocked by the still-running radio stream. Additionally, the long-press detection in `GPIOController` is silently skipped for the 3 station buttons (no long-press task is started), leaving their intended behaviour undefined and potentially noisy.

## What Changes

- **Fix sound ordering in WiFi mode toggle**: play the confirmation sound (`success.wav` / `error.wav`) *before* executing the WiFi switch so the user hears feedback regardless of stream state changes.
- **Stop radio playback before WiFi mode toggle**: call `stop_playback()` before switching mode so the audio device is free when the sound is played.
- **Add pin guard to `_handle_long_press_event`**: the handler must verify the triggering pin is `ROTARY_SW`; long presses on station button pins should be ignored (they have no defined long-press action).
- **Document station-button long-press as not implemented**: make it explicit in `GPIOController._handle_button_press` that long-press monitoring is only started for `ROTARY_SW`, and add a log warning if a long-press callback fires on an unexpected pin.

## Capabilities

### New Capabilities
<!-- None — all changes are bug fixes to existing behaviour -->

### Modified Capabilities
- `radio-integration`: the rotary-encoder long-press scenario gains the requirement that playback is stopped and sound plays *before* the mode switch; the pin guard is a new constraint on `_handle_long_press_event`.

## Impact

- `backend/core/radio_manager.py` — `_handle_long_press_event`: reorder stop → sound → switch; add pin guard.
- `backend/hardware/gpio_controller.py` — `_handle_button_press`: no functional change needed (long-press monitoring already restricted to `ROTARY_SW`); add defensive log if callback fires on wrong pin.
- No API changes, no new dependencies.
