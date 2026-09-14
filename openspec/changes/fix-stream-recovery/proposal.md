## Why

When mpg123 dies mid-stream (WiFi blip, stream server restart), the radio silently stops but the system keeps claiming it is playing: `radio_manager.py:73` constructs `AudioPlayer` without a status callback, so the existing process monitor's exit detection never reaches `RadioManager`. State stays "playing" forever, the UI lies, and pressing the same station button *stops* the dead session instead of restarting it. Two related audio-path bugs compound this: mpg123 is spawned with `stderr=PIPE` that is never drained (`audio_player.py:141-145`) so a chatty/flaky stream fills the 64 KB pipe buffer and wedges playback after hours, and notification chimes are WAV files played through mpg123 (`sound_manager.py:218-224`), an MPEG-only decoder, with errors silenced — chimes likely never play on the Pi.

## What Changes

- Wire `AudioPlayer`'s process monitor into `RadioManager` via the existing (currently unused) `status_callback` parameter, so an unexpected mpg123 exit updates `RadioManager` status and broadcasts over WebSocket.
- Add automatic stream reconnect on unexpected exit: bounded retries with backoff; after N failed attempts, give up, set `ERROR` status, broadcast, and play the error chime.
- Stop leaking the mpg123 stderr pipe: spawn with `stderr=DEVNULL` (or drain it in the monitor) so playback cannot wedge on a full pipe buffer.
- Fix notification chime playback: play WAV files with a WAV-capable player (`paplay` for the PipeWire backend, `aplay` for direct ALSA — both are in the image via `pulseaudio-utils` and `alsa-utils` in `docker/Dockerfile.backend`), and honor or remove the currently ignored `volume` parameter of `SoundManager.play_sound`.
- Add tests covering: monitor-detected exit updates `RadioManager` status; reconnect retry/backoff behavior; give-up behavior (ERROR status + error chime). `audio_player.py` and `sound_manager.py` currently have zero tests.

## Capabilities

### New Capabilities

<!-- none — all changes fall under the existing radio-integration capability -->

### Modified Capabilities

- `radio-integration`: The Stream Recovery behavior under "Audio Backend Integration" changes from "detect exit and fall back to stopped" to "detect exit, broadcast the state change, and automatically reconnect with bounded retries/backoff, entering ERROR state with an audible chime after giving up." New requirements are added for stream auto-reconnect and for reliable notification-sound playback (WAV played by a WAV-capable player, volume honored).

## Impact

- **Code**: `backend/core/radio_manager.py` (pass status callback, handle unexpected-exit events, reconnect state machine), `backend/hardware/audio_player.py` (stderr handling, monitor/callback semantics), `backend/core/sound_manager.py` (playback command, volume handling, availability probe).
- **Tests**: new test modules for `audio_player` and `sound_manager`, plus `RadioManager` recovery tests (`backend/tests/`).
- **Runtime deps**: no new packages — `aplay` (alsa-utils) and `paplay` (pulseaudio-utils) already installed by `docker/Dockerfile.backend`.
- **API/WebSocket**: no new endpoints; existing `playback_status` WebSocket broadcasts now also fire on stream failure, reconnect attempts, and give-up.
