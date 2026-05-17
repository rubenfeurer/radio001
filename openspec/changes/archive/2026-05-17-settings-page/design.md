## Context

`radio.conf` is read once at startup by `_load_radio_conf()` in `main.py` and merged into `os.environ`. The `Config` class reads from env vars — there is no live reload mechanism. The config mount is currently `:ro`, so the container cannot write back. The `/settings` route exists but shows a "Coming Soon" stub.

## Goals / Non-Goals

**Goals:**
- Expose a focused set of user-relevant config fields (hotspot, volume, encoder) in a web UI
- Backend reads and writes `radio.conf` file, preserving comments and unedited fields
- Fields that need restart to take effect are clearly labelled; a restart action is available on the page
- Config mount changed to `:rw` in compose and install.sh

**Non-Goals:**
- Exposing all ~40 config fields (GPIO pins, file paths, dev flags — kept internal)
- Live hot-reload of settings without restart (out of scope; most fields affect hardware init)
- Auth / access control (device is single-user, owner-operated)
- Station management (handled by the existing `/stations` page)

## Decisions

**D1: Partial file write (preserve comments and structure)**
Write back only the changed key-value pairs in-place, leaving comments, blank lines, and section headers untouched. Parse line-by-line: if a line matches `KEY=value`, replace value for keys in the known editable set; leave all other lines as-is. This preserves the conf file as a readable document.
> Alternative considered: rewrite the entire file from a template. Rejected — destroys user-added comments and customisations.

**D2: Restart-required banner, not auto-restart**
After a successful PUT, return which changed fields require restart. Frontend shows a persistent banner: "Settings saved. Restart required for some changes to take effect." with a Restart button that calls `POST /api/system/restart`. User controls when music stops.
> Alternative: auto-restart immediately on save. Rejected — interrupts playback unexpectedly.

**D3: Editable field allowlist**
Backend maintains an explicit allowlist of fields that may be written via the API. Any key not in the allowlist is silently ignored on PUT. This prevents accidental or malicious writes to GPIO pins, file paths, or internal flags.

Editable fields:
```
HOTSPOT_SSID, HOTSPOT_PASSWORD
DEFAULT_VOLUME, MIN_VOLUME, MAX_VOLUME, NOTIFICATION_VOLUME
ROTARY_CLOCKWISE_INCREASES, ROTARY_VOLUME_STEP, ROTARY_DEBOUNCE
LONG_PRESS_DURATION, TRIPLE_PRESS_INTERVAL
```

**D4: GET returns only editable fields**
`GET /api/system/settings` returns only the allowlisted fields as a JSON object. This keeps the API surface small and avoids leaking internal config.

**D5: New settings router, minimal changes to existing code**
Add `backend/api/routes/settings.py`. Register it in `main.py` at `/api/system`. No changes to the `Config` class — the settings endpoint reads the file directly rather than from env vars (since env vars reflect startup state, not current file state).

**D6: Validation in the API layer**
- `HOTSPOT_PASSWORD`: minimum 8 characters (WPA2 requirement)
- `DEFAULT_VOLUME`, `MIN_VOLUME`, `MAX_VOLUME`, `NOTIFICATION_VOLUME`: integer 0–100; MIN ≤ DEFAULT ≤ MAX
- `ROTARY_VOLUME_STEP`: integer 1–20
- `ROTARY_DEBOUNCE`: float 0.01–1.0
- `LONG_PRESS_DURATION`: float 0.5–10.0
- `TRIPLE_PRESS_INTERVAL`: float 0.1–2.0
- `ROTARY_CLOCKWISE_INCREASES`: boolean

## Risks / Trade-offs

- **`:rw` mount** — The container can now modify its own config. Acceptable: the device is owner-operated and there is no multi-user scenario. → No mitigation needed beyond the allowlist.
- **Race condition on file write** — Multiple simultaneous PUT requests could corrupt the file. → Use a file lock (`fcntl.flock`) around the write operation.
- **Restart endpoint abuse** — `POST /api/system/restart` causes the container to exit (systemd restarts it). On a shared network this is a DoS vector. → Acceptable given owner-operated context; no mitigation for now.
- **env vars not updated after write** — The running process still has the old values in `os.environ`. Hardware (GPIO, audio) will behave per startup config until restart. The UI makes this clear with the "restart required" label. → By design (D2).

## Migration Plan

1. Change config mount to `:rw` in `compose.prod.yml` and `scripts/install.sh` inline block
2. Deploy new image (includes settings router)
3. Update `/opt/radio/docker-compose.yml` on Pi with `:rw` mount (scp + alpine trick)
4. Restart container — no data migration needed

Rollback: revert mount to `:ro`, redeploy. Settings page returns to stub.
