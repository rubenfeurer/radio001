# Homepage Radio Controls

## Purpose
Defines requirements for the homepage station controls and the frontend's live-update (WebSocket) behaviour. (The former freeform description was stale — old store filenames, a removed volume slider, wrong WS message names — and was replaced by the requirements below at archive time of `fix-frontend-robustness` and `cleanup-dead-code-and-docs`.)
## Requirements
### Requirement: WebSocket reconnection survives the full SPA session
The WebSocket client SHALL re-enable automatic reconnection every time `connect()` is called. A prior call to `disconnect()` MUST NOT permanently disable reconnection: `connect()` SHALL reset the internal reconnect flag so that a later connection loss schedules a reconnect.

#### Scenario: Reconnect works after a disconnect/connect cycle
- **WHEN** `disconnect()` has been called at some point in the session, `connect()` is called again, and the resulting connection later drops
- **THEN** the client SHALL schedule a reconnect attempt automatically

#### Scenario: Explicit disconnect stops reconnection
- **WHEN** `disconnect()` is called
- **THEN** the client SHALL close the socket, cancel any pending reconnect timer, and SHALL NOT attempt to reconnect until `connect()` is called again

### Requirement: connect() never orphans an in-flight socket
The WebSocket client SHALL NOT create a new socket while an existing socket is in the `CONNECTING` or `OPEN` state. Calling `connect()` in those states SHALL be a no-op, so no socket is ever replaced while its event handlers are still live.

#### Scenario: connect() during CONNECTING is a no-op
- **WHEN** `connect()` is called while a previous socket is still in the `CONNECTING` state
- **THEN** no new WebSocket SHALL be created and the in-flight connection attempt SHALL be allowed to complete

#### Scenario: connect() during OPEN is a no-op
- **WHEN** `connect()` is called while the socket is `OPEN`
- **THEN** no new WebSocket SHALL be created and the existing connection SHALL remain in use

### Requirement: Reconnect attempts use bounded exponential backoff
The WebSocket client SHALL space reconnect attempts using exponential backoff with an upper cap, and SHALL reset the backoff delay to its base value after a connection opens successfully.

#### Scenario: Repeated failures back off
- **WHEN** consecutive reconnect attempts fail
- **THEN** the delay before each subsequent attempt SHALL increase up to a fixed maximum instead of retrying at a constant short interval

#### Scenario: Successful connection resets backoff
- **WHEN** a connection opens successfully after failed attempts
- **THEN** the next connection loss SHALL start reconnecting from the base delay again

### Requirement: Half-open connections are detected via liveness checks
While connected, the WebSocket client SHALL periodically verify the connection is alive (ping/liveness mechanism). If liveness cannot be confirmed within a timeout, the client SHALL close the socket so the standard reconnect path runs. All liveness timers SHALL be cancelled when the socket closes or `disconnect()` is called.

#### Scenario: Stale connection is recycled
- **WHEN** the connection stops delivering messages and a liveness check receives no response within the timeout
- **THEN** the client SHALL close the socket and reconnect via the normal reconnect path

#### Scenario: Timers cleaned up on disconnect
- **WHEN** the socket closes or `disconnect()` is called
- **THEN** any pending liveness or ping timers SHALL be cancelled

### Requirement: Playback and volume API failures are surfaced to the user
The radio store SHALL treat a non-OK HTTP response from the playback and volume endpoints (`toggle`, `stop`, `volume`) as a failure: it SHALL check `response.ok`, expose a user-readable error state, and the UI SHALL display that error. Network errors (rejected fetch) SHALL be surfaced the same way. The error state SHALL be cleared when a subsequent action succeeds.

#### Scenario: Backend error on toggle is visible
- **WHEN** the user taps a station slot and the toggle request returns a non-OK status (e.g. 500)
- **THEN** the store SHALL set an error state and the page SHALL show a user-visible error message

#### Scenario: Successful action clears the error
- **WHEN** a playback or volume request succeeds after a previous failure
- **THEN** the error state SHALL be cleared and the error message removed from the UI

### Requirement: Station selection validates the slot and does not fake success
The station picker SHALL validate the `?slot=` query parameter as an integer within the valid slot range before using it; an invalid or out-of-range value SHALL be treated as if no slot was provided, and no API request SHALL ever be issued with a non-numeric slot (e.g. `NaN`) in the URL. When assigning a station to a slot fails, the picker SHALL show an error and remain on the page instead of navigating home.

#### Scenario: Malformed slot parameter is rejected
- **WHEN** the stations page is opened with a non-integer or out-of-range `?slot=` value
- **THEN** the page SHALL behave as browse-only (no slot selected) and SHALL NOT send any request containing `NaN` or an invalid slot

#### Scenario: Failed assignment keeps the user on the picker
- **WHEN** the user selects a station and the assignment request fails or returns a non-OK status
- **THEN** the page SHALL display an error, re-enable selection, and SHALL NOT navigate to the homepage

#### Scenario: Successful assignment navigates home
- **WHEN** the assignment request succeeds
- **THEN** the page SHALL navigate to the homepage; a failure of the follow-up play request SHALL be surfaced but SHALL NOT undo the assignment

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

