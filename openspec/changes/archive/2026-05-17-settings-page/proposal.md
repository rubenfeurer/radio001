## Why

The radio device has no UI for editing its own configuration. Users who want to change the hotspot SSID/password, adjust volume range, or tune the rotary encoder must SSH into the Pi and edit `/opt/radio/config/radio.conf` manually — an unreasonable expectation for a standalone device. A settings page turns post-install configuration into a first-class experience.

## What Changes

- New `/settings` route (stub currently shows "Coming Soon") becomes a functional settings editor
- New backend API endpoints: `GET /api/system/settings` and `PUT /api/system/settings`
- Config volume mount changed from `:ro` to `:rw` in `compose.prod.yml` and `install.sh`
- Backend writes changed values back to `/app/config/radio.conf`, preserving comments and structure
- Settings that require restart display a "restart required" banner; the page offers a restart action

## Capabilities

### New Capabilities

- `settings-api`: Backend endpoints to read and write radio.conf fields via JSON. Validates values before writing. Returns current config on GET, applies changes on PUT.
- `settings-ui`: SvelteKit settings page with grouped form fields for hotspot, volume, and encoder settings. Shows which fields require restart. Calls settings API.

### Modified Capabilities

- none

## Impact

- **Backend**: New router `backend/api/routes/settings.py`; `Config` class may need a reload helper
- **Frontend**: `frontend/src/routes/settings/+page.svelte` (replace stub)
- **Compose**: `docker/compose.prod.yml` — config mount `:ro` → `:rw`
- **Install**: `scripts/install.sh` — inline compose block, same `:ro` → `:rw` change
- **Security**: Relaxing read-only mount is intentional; the device is single-user and owner-operated
