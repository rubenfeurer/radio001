# Fix Hardware Button Bugs — Design

## Context

Two confirmed bugs in the rotary-switch gesture pipeline (verified against source, matching `docs/project-review-2026-09.md` Critical items 2 and 3):

1. **Triple-press detection** (`backend/hardware/gpio_controller.py:275-291`). `_check_triple_press(gpio_pin, release_time)` compares `release_time` against `self._last_press_times[gpio_pin]`, which at that moment still holds the *start* time of the very press being released (it is only overwritten with the release time afterwards, at line 254). The difference is therefore the press *duration* — always under the 0.5 s `TRIPLE_PRESS_INTERVAL` for any short click — so the `< TRIPLE_PRESS_INTERVAL` branch is taken on every short press regardless of spacing. The counter increments unboundedly, never decays, and the reboot fires at `count >= 2`. Net effect: **any two short clicks of the rotary switch, even minutes apart, reboot the Pi.**
2. **Long-press WiFi toggle no-op** (`backend/core/radio_manager.py:401,404`). `_handle_long_press_event` calls `self._wifi_manager.switch_to_host_mode()` / `switch_to_client_mode()` without `await`. Both are `async def` (`backend/core/wifi_manager.py:686,720`), so the calls create coroutine objects that are never scheduled: the success chime plays and "Switched to …" is logged, but no mode switch happens. The HTTP path awaits correctly, which masked the bug.

There are currently **zero** tests for `GPIOController` (`backend/tests/` has `core/`, `unit/`, `api/`, `integration/` — no hardware tests), and the existing `RadioManager` tests do not cover `_handle_long_press_event`'s awaiting behavior.

## Goals / Non-Goals

**Goals:**
- A reboot requires exactly three presses, each within `TRIPLE_PRESS_INTERVAL` of the previous press's **release**; the count resets when the interval is exceeded. Two presses never reboot, at any spacing.
- The long-press client ↔ hotspot toggle actually executes the mode switch (coroutines awaited).
- Unit tests that would have caught both bugs: short press, long press, triple-press timing (fire / no-fire / reset), and an `AsyncMock`-based awaited assertion on the WiFi manager coroutines.

**Non-Goals:**
- No changes to `WiFiManager` itself, the HTTP mode-switch path, debounce logic, rotary-rotation handling, sound playback, or the reboot mechanism (`subprocess.run(["reboot"])` and its mock-mode guard stay as-is).
- No new gestures, no configurability changes to `TRIPLE_PRESS_INTERVAL` / `LONG_PRESS_DURATION`.
- No hardware-in-the-loop testing; tests drive the async press/release handlers directly.

## Decisions

### 1. Track last *release* time in a dedicated dict

Add `self._last_release_times: Dict[int, float]` rather than reusing `_last_press_times`. `_last_press_times` is dual-purpose today (press start for duration math at line 233-238, then overwritten with the release time at line 254 for debounce) — overloading it a third way is what caused the bug. `_check_triple_press(gpio_pin, release_time)` compares `release_time` against `self._last_release_times.get(gpio_pin)` **before** updating it, then stores `release_time`.

*Alternative considered:* reorder the existing dict updates so `_last_press_times` holds the previous release at comparison time. Rejected — keeps the fragile aliasing that produced the bug and breaks the duration/debounce uses.

### 2. Counter semantics: count presses in the chain, fire at 3, reset on gap

- First tracked release (no prior release, or gap ≥ `TRIPLE_PRESS_INTERVAL`): `count = 1`.
- Release within the interval of the previous release: `count += 1`.
- When `count >= 3`: invoke `_handle_triple_press` and reset `count = 0`.

This makes the counter mean "presses in the current fast chain" (the old code's `1` seed plus `>= 2` threshold mixed zero- and one-based conventions). The reset-on-gap in the `else` branch is the decay the old code lacked in practice, since its condition was always true.

### 3. Fix the no-op calls with `await`, nothing more

`radio_manager.py:401,404` become `await self._wifi_manager.switch_to_host_mode()` / `await self._wifi_manager.switch_to_client_mode()`. The surrounding `try/except` already routes failures to `play_error_sound()`; once awaited, a raising mode switch correctly produces the error chime instead of a false success. The success chime intentionally still plays *before* the switch (existing design: audio device is freed and feedback is immediate); changing that ordering is out of scope.

### 4. Test approach: drive the async handlers directly with controlled timestamps

New `backend/tests/hardware/test_gpio_controller.py` (with `__init__.py`), following the existing test layout. Construct `GPIOController` in mock mode with a lightweight config (real `ROTARY_SW`, `TRIPLE_PRESS_INTERVAL`, `LONG_PRESS_DURATION` values) and `AsyncMock` callbacks, then call `_handle_button_press(pin, t)` / `_handle_button_release(pin, t)` with explicit synthetic timestamps — no sleeping, no clock patching, deterministic timing. Cases:

- short press → `button_callback` awaited once; no long/triple callback
- long press (duration ≥ `LONG_PRESS_DURATION`) → no short-press callback (long-press monitor path is timer-driven; assert the release path suppresses the short-press callback, and cover `_handle_long_press` invoking `long_press_callback`)
- three presses with inter-release gaps < `TRIPLE_PRESS_INTERVAL` → `triple_press_callback` fires exactly once
- **two presses only — any spacing (both fast and minutes apart) → callback never fires** (the regression test for this bug)
- presses spaced ≥ `TRIPLE_PRESS_INTERVAL` reset the chain: e.g. 2 fast + gap + 2 fast → never fires; a fresh 3-chain after a gap → fires

For the long-press toggle: in `backend/tests/unit/test_radio_manager.py` (or a focused addition), give `RadioManager` a mock WiFi manager whose `switch_to_host_mode` / `switch_to_client_mode` / `get_status` are `AsyncMock`s and assert `switch_to_host_mode.assert_awaited_once()` (and the client-mode counterpart). `assert_awaited_once` — not `assert_called_once` — is the assertion that fails on the current bug.

## Risks / Trade-offs

- [Real-hardware timing differs from synthetic timestamps] → thresholds are compared, not slept on, so unit determinism is representative; keep manual verification on the Pi (three fast clicks reboot, two do not) in the task list.
- [`_last_press_times[pin] = release_time` at line 254 also feeds press debounce] → the new release dict is additive; the existing line is untouched, so debounce behavior is unchanged.
- [Long press also produces a release event that enters `_check_triple_press`] → a long press's release still counts toward the chain exactly as today; behavior unchanged and covered implicitly by the two-press guarantee (a long press plus a click is two presses — no reboot).
- [Awaiting the mode switch makes `_handle_long_press_event` slower/failable] → intended; failures now surface as the error chime via the existing exception handler instead of silent false success.

## Open Questions

None — both fixes are mechanical once the semantics above are agreed, and the review's proposed behavior matches the original intent of the spec (`openspec/specs/rotary-triple-press-reboot/spec.md`).
