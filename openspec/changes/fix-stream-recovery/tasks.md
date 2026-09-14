## 1. AudioPlayer: exit reporting and stderr fix

- [x] 1.1 Change mpg123 spawn in `backend/hardware/audio_player.py` to `stderr=asyncio.subprocess.DEVNULL` (matching stdout) so an undrained pipe can never wedge playback
- [x] 1.2 Extend `_monitor_process` / `_notify_status_change` so the status payload of an unexpected exit carries an explicit `unexpected_exit: True` marker (expected stops and normal status updates must not carry it)
- [x] 1.3 Add a way for reconnect attempts to bypass the stale `_url_cache` entry (e.g. `play(url, refresh_cache=True)` or an explicit cache-invalidate method) so retries re-resolve expired redirects

## 2. RadioManager: status wiring and reconnect state machine

- [x] 2.1 Construct `AudioPlayer` with `status_callback=self._handle_player_status` in `backend/core/radio_manager.py` and implement `_handle_player_status`, ignoring events unless the marker is set and manager state is `PLAYING`
- [x] 2.2 On unexpected exit: set `playback_state = CONNECTING` (keep `current_station`), broadcast `playback_status`, and spawn a single reconnect task stored on the manager
- [x] 2.3 Implement the reconnect loop: up to 5 attempts with 1s/2s/4s/8s/15s backoff (constants, delays injectable for tests), acquiring `_playback_lock` only around each play attempt; on success restore `PLAYING` and broadcast
- [x] 2.4 Implement give-up: after the final failed attempt set `ERROR` with `is_playing=False` (keep `current_station`), broadcast, and play the error chime exactly once
- [x] 2.5 Cancel any in-flight reconnect task at the top of `stop_playback()` and `play_station()`; update `toggle_station` so `CONNECTING`/`ERROR` on the pressed slot triggers a fresh `play_station(slot)` instead of a stop
- [x] 2.6 Cancel the reconnect task in `shutdown()`

## 3. SoundManager: WAV-capable chime playback

- [x] 3.1 Add backend detection to `backend/core/sound_manager.py` (PipeWire socket probe via `PULSE_SERVER`, same logic as `AudioPlayer`) and replace the `which mpg123` probe in `initialize()` with a probe for the selected player, falling back to mock mode if absent
- [x] 3.2 Replace the mpg123 invocation in `play_sound` with `paplay --volume=<volume/100*65536>` on the PipeWire backend and `aplay -q -D <ALSA device>` on the ALSA fallback; document that `volume` is best-effort on aplay
- [x] 3.3 Verify volume mapping bounds (0 → 0, 100 → 65536, clamped) and keep fire-and-forget semantics

## 4. Tests

- [x] 4.1 Add `backend/tests/unit/test_audio_player.py`: monitor detects unexpected exit and fires callback with the marker; user-initiated stop produces no unexpected-exit event; spawn uses DEVNULL for stderr; cache-bypass path re-resolves the URL
- [x] 4.2 Add RadioManager recovery tests: unexpected exit transitions PLAYING→CONNECTING and broadcasts; reconnect succeeds mid-schedule and restores PLAYING; give-up sets ERROR, broadcasts, and plays the error chime once; retry delays follow the configured schedule (patched to ~0)
- [x] 4.3 Add RadioManager cancellation tests: `stop_playback`/`play_station` cancel an in-flight reconnect; button press on a `CONNECTING`/`ERROR` slot restarts playback instead of stopping
- [x] 4.4 Add `backend/tests/unit/test_sound_manager.py`: paplay command + volume mapping on PipeWire backend; aplay command on ALSA fallback; initialize falls back to mock mode when the player binary is missing
- [x] 4.5 Run the backend test suite and lint/type checks; fix regressions

## 5. Verification on hardware

- [ ] 5.1 On the test Pi (`:latest` image): kill mpg123 manually and confirm CONNECTING broadcast + automatic recovery; disable the stream URL and confirm ERROR state in UI plus one audible error chime; confirm boot chime is now audible
