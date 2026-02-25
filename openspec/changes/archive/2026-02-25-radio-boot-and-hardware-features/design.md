## Context

The radio runs FastAPI in Docker on a Pi, with lgpio GPIO callbacks firing in a C thread and all business logic in asyncio. Currently: stream URLs are resolved on every play call (up to 5s delay); the rotary long-press does nothing; boot sounds play unconditionally regardless of WiFi state; the last-played station is not remembered; and the Docker stack must be started manually after reboot.

Existing seams used by this change:
- `GPIOController` already has `button_callback` and `volume_callback` constructor params — same pattern for `long_press_callback`
- `RadioManager` already holds `_playback_lock`, `_status`, `_station_manager`, `_audio_player`, `_sound_manager`
- `SoundManager` already has `play_startup_sound()` / `play_error_sound()` / `play_success_sound()` — just needs real WAV files
- `WiFiManager.get_status()`, `switch_to_host_mode()`, `switch_to_client_mode()` all exist

## Goals / Non-Goals

**Goals:**
- Stream play starts in <100ms after button press (vs up to 5s today) for pre-cached URLs
- Rotary SW held 2s toggles hotspot ↔ client mode; audible confirmation
- Boot plays correct sound based on WiFi outcome
- Last station+volume is restored automatically on power-on
- Pi starts the radio stack on boot without manual `docker compose up`

**Non-Goals:**
- Cache persistence across restarts (per-process in-memory cache is sufficient; URLs rarely change and are re-resolved on first play after restart anyway)
- Cache invalidation / TTL (streams that go stale will be caught when mpg123 fails to connect; next play call re-resolves)
- Multi-user or concurrent boot-sound scenarios
- Changing frontend behaviour

## Decisions

**1. URL cache is in-memory dict, not persisted**
Rationale: redirect targets for most radio streams are stable within a session but can change between restarts (CDN load balancing). A per-process dict is safe and trivial. Persisting it across restarts adds complexity for marginal gain.

**2. `wifi_manager` injected into `RadioManager` as constructor param (not global/singleton)**
Rationale: keeps the dependency explicit and avoids circular imports. `RadioManager.create_instance()` already takes config; adding `wifi_manager=None` is backward-compatible.

**3. Long-press threshold changed to 2.0s (from 3.0s)**
Rationale: 3s is too long for a simple toggle gesture. 2s is sufficient to distinguish from accidental holds while still being deliberate. Configurable via `LONG_PRESS_DURATION` in `radio.conf`.

**4. Playback state persisted to `data/radio_state.json` via atomic write (write tmp → rename)**
Rationale: prevents corruption if process is killed mid-write. File is small (~30 bytes). Written on every `play_station()` success and `set_volume()` change. Path configurable via `RADIO_STATE_FILE`.

**5. Auto-play on boot uses `asyncio.create_task()` inside `_initialize()`**
Rationale: prevents `_initialize()` from blocking for the full stream connection time. FastAPI startup completes immediately; playback begins concurrently.

**6. Boot sound decision made by checking `WiFiManager.get_status()` at end of `_initialize()`**
Rationale: WiFiManager is already fully initialised before RadioManager starts. `get_status()` reads live NetworkManager state — no race condition.

**7. WAV tone files generated via Python stdlib (`wave`/`struct`/`math`) at SoundManager init if missing or placeholder**
Rationale: zero new dependencies. Placeholder detection: check `st_size < 200`. Generated tones: success = two ascending notes (C5→E5), error = two descending notes (A4→E4), startup = same as success.

**8. Systemd service installed by a standalone shell script (`scripts/install-service.sh`)**
Rationale: service installation requires root and is a one-time Pi setup step. Keeping it separate from the Docker build avoids privilege escalation inside the container.

## Risks / Trade-offs

- **Pre-cache race**: if a station URL is updated in the database between cache population and play, the cached URL is stale → Mitigation: `play()` catches mpg123 failure and falls back to re-resolving the URL (existing error path)
- **Long-press during active stream**: toggling hotspot mode will disconnect WiFi, killing the stream → Mitigation: this is expected and correct; the stream stops naturally when network drops
- **Auto-play before WiFi is stable**: `_initialize()` runs quickly; WiFi may not be ready yet on first boot → Mitigation: mpg123 will retry on error; the auto-play task fails gracefully and logs a warning; no crash
- **WAV generation failure**: if `assets/sounds/` is not writable (read-only Docker layer) → Mitigation: SoundManager catches exceptions from file generation and continues; sounds are non-critical

## Migration Plan

1. Update `config/radio.conf`: set `LONG_PRESS_DURATION=2.0`, add `RADIO_STATE_FILE=/app/data/radio_state.json`
2. Rebuild Docker image (`docker compose build radio-backend`)
3. Restart container (`docker compose up -d radio-backend`)
4. On Pi: run `sudo bash scripts/install-service.sh` once to install systemd service
5. Rollback: `systemctl disable radio-wifi.service` + revert `radio.conf` changes + rebuild

## Open Questions

- None — all decisions made above.
