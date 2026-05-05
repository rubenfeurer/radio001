## 1. Fix `_handle_long_press_event` in RadioManager

- [ ] 1.1 Add pin guard: if `gpio_pin != config.ROTARY_SW`, log warning and return early
- [ ] 1.2 Call `stop_playback()` before playing any sound or switching WiFi mode
- [ ] 1.3 Play `success.wav` / `error.wav` *before* calling `switch_to_host_mode()` / `switch_to_client_mode()`
- [ ] 1.4 Ensure the success sound plays based on current WiFi state *before* the switch (detect mode, play sound, then switch)

## 2. Verify GPIO controller defensive behaviour

- [ ] 2.1 Confirm `GPIOController._handle_button_press` only starts long-press monitoring for `ROTARY_SW` (read, no change needed)
- [ ] 2.2 Add log warning in `_handle_long_press` if callback fires but `long_press_callback` is not set

## 3. Test

- [ ] 3.1 Rebuild Docker image and restart container
- [ ] 3.2 Tail logs and simulate a long press via API/WebSocket to verify: playback stops → sound plays → WiFi mode changes
- [ ] 3.3 Verify short press on station buttons still works normally after the change
- [ ] 3.4 Verify no sound/WiFi toggle occurs on station button presses
