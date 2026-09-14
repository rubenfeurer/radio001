## Context

`AudioPlayer` already has an unexpected-exit monitor (`_monitor_process`) and a `status_callback` parameter, but `RadioManager` constructs it without a callback (`backend/core/radio_manager.py:73`), so exit detection never reaches application state. When mpg123 dies (WiFi blip, stream server restart):

- `RadioManager._status` stays `is_playing=True` / `PLAYING` forever; the UI lies.
- `toggle_station(slot)` sees `current_station == slot and is_playing` and *stops* the dead session — the user must press twice to restart.
- No reconnect logic exists anywhere.

Two adjacent bugs compound this:

- mpg123 is spawned with `stderr=asyncio.subprocess.PIPE` that nothing reads (`backend/hardware/audio_player.py:141-145`). A chatty/flaky stream fills the 64 KB pipe buffer and wedges mpg123 mid-playback.
- `SoundManager.play_sound` plays generated **WAV** chimes with `mpg123` (`backend/core/sound_manager.py:218-224`), an MPEG-only decoder, with stdout/stderr silenced — chimes almost certainly never play on the Pi. The `volume` parameter is accepted and ignored.

Constraints: single-process asyncio app; `PlaybackState` enum already has `CONNECTING` and `ERROR`; `docker/Dockerfile.backend` already installs `mpg123`, `alsa-utils` (`aplay`) and `pulseaudio-utils` (`paplay`); mock mode must keep working on macOS dev.

## Goals / Non-Goals

**Goals:**

- Unexpected mpg123 exit is detected, reflected in `RadioManager` status, and broadcast over the existing WebSocket callback.
- Automatic reconnect with bounded retries and backoff; after the retry budget is exhausted: `ERROR` state, broadcast, error chime.
- A user pressing the station button during a dead/reconnecting session gets a (re)start, never a phantom "stop".
- mpg123 stderr can never wedge playback.
- Notification chimes audibly play on the Pi via a WAV-capable player, honoring the `volume` parameter (or the parameter is removed).
- Test coverage for exit detection, retry/backoff, and give-up behavior.

**Non-Goals:**

- No changes to the frontend, API routes, or WebSocket message schema (existing `playback_status` messages carry the new states — `CONNECTING`/`ERROR` already exist in the enum).
- No stream health probing beyond process exit (no silence detection, no HTTP keep-alive checks).
- No fixing of other review findings (WS client reconnect bugs, API truthfulness, etc.) — separate changes.
- No new runtime dependencies or Dockerfile changes.

## Decisions

### 1. Recovery lives in RadioManager, not AudioPlayer

`AudioPlayer` stays a dumb transport: it reports "the process exited and I didn't stop it" via `status_callback`. `RadioManager` owns the reconnect state machine because it owns `SystemStatus`, the WebSocket broadcast, the station→URL mapping, and the chime path. Alternative — retry loop inside `AudioPlayer._monitor_process` — rejected: AudioPlayer has no notion of station slots, broadcast, or chimes, and burying retries there would hide state from the UI.

Wiring: construct `AudioPlayer(mock_mode=mock_mode, status_callback=self._handle_player_status)` in `RadioManager.__init__`. The callback distinguishes *unexpected* exit (player reports `is_playing=False` while manager believes `PLAYING`) from expected transitions (stop/play we initiated). To make this unambiguous, the monitor's status payload includes an `unexpected_exit: True` marker rather than making RadioManager infer it.

### 2. Reconnect state machine: bounded retries with fixed-schedule backoff

On unexpected exit while state is `PLAYING`:

1. Set `playback_state = CONNECTING` (keep `current_station`), broadcast `playback_status`.
2. Retry loop (single `asyncio.Task`, stored as `self._reconnect_task`): attempt `AudioPlayer.play(url)` up to **5** attempts with delays **1 s, 2 s, 4 s, 8 s, 15 s** (capped exponential backoff — cheap to reason about, tunable via config constants `STREAM_RECONNECT_ATTEMPTS` / max delay).
3. Success → `PLAYING`, broadcast, done.
4. All attempts fail → `ERROR` state, `is_playing=False` (keep `current_station` so the UI shows *which* station failed), broadcast, play error chime once.
5. If mpg123 dies again *after* a successful reconnect, the monitor fires again and the retry budget resets (it is a new outage).

Alternatives considered: infinite retry with capped backoff (rejected: a permanently dead URL would chime-loop and hide the failure), immediate single retry (rejected: WiFi blips routinely exceed one attempt window).

Cancellation rules: any explicit `stop_playback()` or `play_station()` cancels an in-flight reconnect task first. `toggle_station` treats `CONNECTING`/`ERROR` on the same slot as "not successfully playing" → pressing the button during recovery cancels the reconnect and issues a fresh `play_station(slot)` (never a stop of a dead session). Reconnect attempts must bypass the stale `_url_cache` entry on later attempts (re-resolve the URL), since an expired redirect is a plausible cause of the exit.

### 3. stderr → DEVNULL

Spawn mpg123 with `stderr=asyncio.subprocess.DEVNULL` (matching stdout). Alternative — drain the pipe in `_monitor_process` and log — rejected: the diagnostics value is marginal (`--quiet` already suppresses most output) and a drain task adds lifecycle complexity for no behavioral gain. Exit *detection* is what matters, and `process.wait()` provides it.

### 4. Chime playback: backend-matched WAV player

`SoundManager.play_sound` selects the player by audio backend, mirroring `AudioPlayer`:

- PipeWire socket present → `paplay --volume=<0..65536> <file.wav>` (`volume/100 * 65536`).
- Otherwise → `aplay -q -D <ALSA device> <file.wav>`; `aplay` has no per-invocation volume, so on the ALSA path `volume` is best-effort (device volume governs) — the parameter is honored where the backend supports it and documented as such.

Both binaries are already in the image (`pulseaudio-utils`, `alsa-utils` — verified in `docker/Dockerfile.backend:39-41`). `initialize()` probes for the chosen player (instead of today's `which mpg123`) and falls back to mock mode if absent. Alternative — generate MP3 chimes so mpg123 keeps working — rejected: stdlib can write WAV (`wave` module, already used) but not MP3; adding an encoder dependency to keep the wrong player is backwards.

Backend detection reuses the same `PULSE_SERVER` socket probe as `AudioPlayer` (small duplicated helper or shared util — implementer's choice; no behavioral coupling required).

### 5. Testing approach

Pure-asyncio unit tests in `backend/tests/` with fake processes / patched `asyncio.create_subprocess_exec`; backoff delays patched to ~0 (delays injectable or monkeypatched) so the suite stays fast. Coverage: monitor detects exit → callback fires with `unexpected_exit`; RadioManager transitions PLAYING→CONNECTING and broadcasts; retries follow the schedule and succeed mid-way; give-up sets ERROR + broadcasts + plays error chime; explicit stop cancels reconnect; button press during CONNECTING/ERROR restarts instead of stopping; SoundManager builds the right paplay/aplay command with the right volume mapping.

## Risks / Trade-offs

- **[Callback distinguishes expected vs unexpected exits]** A race (user stops exactly as mpg123 dies) could trigger a spurious reconnect. → Mitigation: `AudioPlayer.stop()` clears `_process`/`_is_playing` before terminating (already does), monitor only reports when `self._process is process` and `_is_playing` was still true; RadioManager additionally ignores unexpected-exit events unless its own state is `PLAYING`, and all state transitions happen under `_playback_lock`-aware sequencing.
- **[Retry loop vs playback lock]** Holding `_playback_lock` for the whole retry loop would block button presses for up to ~30 s. → Mitigation: the reconnect task acquires the lock only around each individual play attempt; button/API commands cancel the task first.
- **[ERROR keeps `current_station`]** Existing code nulls `current_station` on error; keeping it changes what some clients render. → Accepted: the message payload shape is unchanged and knowing which station failed is strictly more useful; verify frontend renders `error` state sanely.
- **[aplay path ignores volume]** On non-PipeWire fallback, chime volume is whatever the device is set to. → Accepted and documented; the Pi production path is PipeWire, where volume is honored.
- **[Chimes were previously silent — now audible]** Boot/error chimes will start actually playing on Pis for the first time. → Accepted: that is the specified behavior; volumes are modest (default 40%).

## Migration Plan

No data or config migration. Ships as a normal `develop` → `main` → `:latest` → tagged `:stable` release. Rollback = previous image tag. Manual Pi verification after deploy: pull WiFi mid-stream → radio recovers within the backoff window; kill mpg123 by hand → same; break the stream URL → ERROR state in UI + audible error chime; reboot → boot chime audible.

## Open Questions

- None blocking. Retry count/backoff schedule (5 attempts, 1/2/4/8/15 s) are defaults expressed as constants; tune after field experience if needed.
