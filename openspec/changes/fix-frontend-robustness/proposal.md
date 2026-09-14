# Fix Frontend Robustness

## Why

The 2026-09 project review found frontend defects that silently degrade the app: visiting `/status` permanently kills WebSocket reconnection for the rest of the SPA session, a `CONNECTING` socket can be orphaned causing connection flapping, playback/volume API failures are invisible to the user (no `response.ok` checks, no error state), and the settings volume slider fires a POST per input event while WS echoes snap it backwards mid-drag.

## What Changes

- **WebSocket client fixes** (`frontend/src/lib/stores/websocket.svelte.ts`):
  - `connect()` resets `shouldReconnect = true` so a prior `disconnect()` (set at line 80, never reset) no longer disables reconnection for the session.
  - `connect()` guards `CONNECTING` as well as `OPEN` (line 18 currently guards only `OPEN`), so an in-flight socket is never orphaned with live handlers.
  - Add reconnect backoff (exponential with cap, reset on successful open) and a ping/liveness check so half-open connections are detected.
- **Delete the dead `/status` route** (`frontend/src/routes/status/+page.svelte`): linked from nowhere, duplicates the settings-page WiFi/System cards, and is the sole caller of `wsClient.disconnect()` — the trigger of the reconnect bug.
- **Delete unused components**: `frontend/src/lib/components/SignalStrength.svelte`, `frontend/src/lib/components/ui/separator/`, and unused card subcomponents (`card-description.svelte`, `card-footer.svelte`; `CardHeader`/`CardTitle` stay — still used by `/setup`).
- **Dedupe helpers**: move the identical `formatUptime`/`formatBytes` copies (status page + `settings/+page.svelte:108-122`) into a shared util module.
- **Surface errors in the radio store** (`frontend/src/lib/stores/radio.svelte.ts`): `toggleStation`, `stopPlayback`, `setVolume` check `response.ok`, set an error state on failure, and the UI shows user-visible feedback instead of swallowing backend 500s.
- **Stations page robustness** (`frontend/src/routes/stations/+page.svelte`): `selectStation` no longer navigates home as if successful when a request fails; `?slot=` is validated (integer in valid slot range) so a malformed value never produces a `POST /api/radio/stations/NaN` request.
- **Volume slider fix** (`frontend/src/routes/settings/+page.svelte:124-127`): debounce/throttle the POST-per-input-event and ignore WS `volume_update` echoes while the user is dragging, so the slider no longer snaps backwards mid-drag.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `homepage-radio-controls`: adds WebSocket reconnect-resilience requirements (reconnect survives a prior disconnect, no orphaned CONNECTING sockets, backoff + liveness) and error-surfacing requirements for playback/volume/station-selection actions (including `?slot=` validation). The existing spec is freeform prose without `### Requirement:` blocks, so the delta uses `## ADDED Requirements` only; the full staleness rewrite of the prose is owned by the separate `cleanup-dead-code-and-docs` change.
- `settings-ui`: adds a requirement for the live volume slider — debounced/throttled volume POSTs and echo suppression while dragging.

No spec references the `/status` route, so no `## REMOVED Requirements` block is needed for its deletion. `frontend-design-system` requirements are unaffected: the removed components (SignalStrength, separator, unused card subcomponents) are not mandated by that spec.

## Impact

- **Frontend only** — no backend, API, or dependency changes.
- Modified: `frontend/src/lib/stores/websocket.svelte.ts`, `frontend/src/lib/stores/radio.svelte.ts`, `frontend/src/routes/settings/+page.svelte`, `frontend/src/routes/stations/+page.svelte`, homepage (error feedback display).
- Deleted: `frontend/src/routes/status/+page.svelte`, `frontend/src/lib/components/SignalStrength.svelte`, `frontend/src/lib/components/ui/separator/`, `frontend/src/lib/components/ui/card/card-description.svelte`, `card-footer.svelte`.
- Added: shared format util module (e.g. `frontend/src/lib/format.ts`).
- Verified by `npm run check` and `npm run build`.
