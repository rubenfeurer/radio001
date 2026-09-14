# homepage-radio-controls Delta — cleanup-dead-code-and-docs

The existing main spec is freeform prose (no `### Requirement:` blocks) and badly stale: it references removed store filenames (`radio.ts`/`websocket.ts` instead of `radio.svelte.ts`/`websocket.svelte.ts`), a homepage volume slider that no longer exists, and the WS message name `stations_list` instead of the actual `stations_update`. This delta defines the correct requirement set; at sync/archive time the freeform legacy body is replaced by these requirements.

## ADDED Requirements

### Requirement: Homepage station slots
The homepage SHALL display three station slot rows (slots 1-3). Each row SHALL show the configured station name, or `(empty)` when unconfigured, and empty slots SHALL be disabled for playback.

#### Scenario: Slot rendering
- **WHEN** the homepage mounts and station data is loaded via `fetchStations()` and `fetchStatus()` from `frontend/src/lib/stores/radio.svelte.ts`
- **THEN** three slot rows SHALL render with the station name or `(empty)`
- **AND** the playback button of an empty slot SHALL be disabled

#### Scenario: Tap-to-toggle playback
- **WHEN** the user taps a configured slot
- **THEN** the frontend SHALL call `toggleStation(slot)`, which issues `POST /api/radio/stations/{slot}/toggle` to start playback or stop it if that slot is already playing
- **AND** the currently playing slot SHALL be visually highlighted with a spinning record indicator

#### Scenario: Per-slot settings navigation
- **WHEN** the user taps a slot's chevron button
- **THEN** the app SHALL navigate to `/stations?slot={slot}` without toggling playback

### Requirement: Homepage has no volume control
The homepage SHALL NOT display a volume slider or any volume control. Volume is controlled from the Settings page and the hardware rotary encoder.

#### Scenario: No volume UI on homepage
- **WHEN** the homepage renders
- **THEN** no volume slider, volume number, or volume control element SHALL be present

### Requirement: Real-time updates via WebSocket
The homepage SHALL receive live updates through the WebSocket client in `frontend/src/lib/stores/websocket.svelte.ts`, using the actual backend message types.

#### Scenario: Handled message types
- **WHEN** a WebSocket message arrives
- **THEN** the client SHALL handle `system_status`, `volume_update`, `playback_status`, `station_change`, `stations_update`, and `pong`
- **AND** `stations_update` (not `stations_list`) SHALL refresh the station slots

#### Scenario: Disconnected indicator
- **WHEN** the WebSocket is not connected
- **THEN** the homepage SHALL show a "live updates offline" indicator above the station slots
- **AND** slot interactions SHALL continue to work via plain HTTP API calls
