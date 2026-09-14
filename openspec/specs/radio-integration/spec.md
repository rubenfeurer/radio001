## ADDED Requirements

## Purpose
Defines requirements for radio playback integration: audio backend, stream lifecycle, status updates, and recovery.
## Requirements
### Requirement: Radio Station Management

The system MUST provide a 3-slot radio station management system with persistent storage and real-time audio streaming capabilities.

#### Scenario: Station Storage and Retrieval

- **WHEN** a user configures a radio station in slot 1, 2, or 3
- **THEN** the station URL, name, and metadata are persisted to disk
- **AND** the station configuration survives system restarts
- **AND** stations can be retrieved via API endpoints

#### Scenario: Audio Streaming Control

- **WHEN** a user selects a radio station to play
- **THEN** the system stops any currently playing stream
- **AND** starts the new stream using mpg123 audio backend
- **AND** provides real-time playback status updates via WebSocket

#### Scenario: Volume Management

- **WHEN** a user adjusts the volume level
- **THEN** the volume is constrained to safe limits (30-100%)
- **AND** the volume setting persists across station changes
- **AND** volume changes are immediately applied to the audio output

### Requirement: Real-time Radio Status

The system must provide live updates of radio playback status to connected clients without polling, and delivery to any one client MUST NOT be blocked by another client's connection.

#### Scenario: WebSocket Status Broadcasting

- **WHEN** radio playback status changes (play/pause/stop/volume/station)
- **THEN** all connected WebSocket clients receive immediate updates
- **AND** the update includes current station, volume, and playback state
- **AND** clients can subscribe to specific update types

#### Scenario: Initial Status Sync

- **WHEN** a client connects to the WebSocket endpoint
- **THEN** they immediately receive the current radio status
- **AND** they receive the current station configuration
- **AND** they are synchronized with the actual audio output state

#### Scenario: Stalled Client Isolation

- **WHEN** one connected WebSocket client stops reading (stalled TCP buffer) or errors during a broadcast
- **THEN** each individual send SHALL be bounded by a per-send timeout
- **AND** the stalled or failed connection SHALL be removed from the active connection set
- **AND** all other connected clients SHALL still receive the broadcast message
- **AND** subsequent broadcasts SHALL proceed without the removed connection

#### Scenario: Consistent Connection-Set Access

- **WHEN** broadcasts, connects, and disconnects occur concurrently
- **THEN** all reads and mutations of the active connection set SHALL be serialized under the connection manager's lock (snapshots may be taken under the lock and sends performed outside it)
- **AND** the lock SHALL NOT be held while awaiting a network send

### Requirement: Hardware Controls Integration

The system MUST support physical hardware controls for radio operation without requiring the web interface.

#### Scenario: Hardware Button Control

- **WHEN** physical buttons are pressed (3 station buttons + rotary encoder)
- **THEN** the corresponding radio actions are triggered
- **AND** the web interface reflects the hardware-initiated changes
- **AND** button presses work even when no clients are connected

#### Scenario: Rotary Encoder Volume Control

- **WHEN** the rotary encoder is turned
- **THEN** volume adjusts in appropriate increments
- **AND** volume changes respect the 30-100% safety limits
- **AND** the web interface shows the updated volume level

#### Scenario: Rotary Encoder Long Press — WiFi Mode Toggle

- **WHEN** the rotary encoder button is held for ≥ 2 seconds
- **THEN** the system SHALL stop any active radio playback first
- **AND** play a confirmation sound (`success.wav` or `error.wav`) before executing the mode switch
- **AND** toggle the WiFi mode between client and hotspot
- **AND** if the triggering GPIO pin is not the rotary encoder switch (`ROTARY_SW`), the event SHALL be ignored and a warning logged

#### Scenario: Long Press on Station Buttons — No Action

- **WHEN** a station button (slots 1–3) is held for ≥ 2 seconds
- **THEN** no long-press action is triggered
- **AND** the button release is handled as a normal short press

#### Scenario: Development Mode Hardware Mocking

- **WHEN** the system runs in development mode (non-Pi environment)
- **THEN** hardware controls are mocked to return simulated responses
- **AND** API endpoints for hardware control remain functional
- **AND** developers can test hardware integration without physical GPIO

### Requirement: Audio Backend Integration

The system must provide reliable audio streaming using mpg123 (subprocess) with amixer for ALSA volume control. The mpg123 subprocess SHALL be spawned with both stdout and stderr redirected to `DEVNULL` (or actively drained) so that unread pipe buffers can never stall playback. Unexpected subprocess exits SHALL be reported to `RadioManager` via the `AudioPlayer` status callback.

#### Scenario: Stream Initialization

- **WHEN** a radio station is selected for playback
- **THEN** a mpg123 subprocess is spawned with the stream URL
- **AND** the subprocess's stdout and stderr are redirected to `DEVNULL` (no unread `PIPE` is left attached)
- **AND** connection failures are handled gracefully with user feedback
- **AND** the process is monitored for unexpected exits

#### Scenario: Audio Output Configuration

- **WHEN** the system starts on different hardware platforms
- **THEN** it automatically detects and configures appropriate ALSA audio output
- **AND** it handles cases where no audio hardware is available (mock mode)
- **AND** volume is controlled system-wide via amixer (PCM or Master control)

#### Scenario: Stream Recovery

- **WHEN** an active radio stream fails or the mpg123 process exits unexpectedly
- **THEN** the `AudioPlayer` process monitor invokes the status callback wired into `RadioManager`, marking the exit as unexpected
- **AND** `RadioManager` updates its playback state to `connecting` (keeping the current station) and broadcasts the change over WebSocket
- **AND** automatic reconnection is attempted per the Stream Auto-Reconnect requirement
- **AND** if reconnection ultimately fails, the system enters `error` state rather than silently claiming to be playing

#### Scenario: Exit during user-initiated stop is not a failure

- **WHEN** the mpg123 process exits because `stop()` (or a station switch) terminated it
- **THEN** no unexpected-exit event is raised
- **AND** no reconnection is attempted

### Requirement: Station Persistence

The system MUST reliably store and retrieve radio station configurations across system restarts.

#### Scenario: Station Data Storage

- **WHEN** a user saves a station to any slot (1-3)
- **THEN** the station data is written to persistent storage immediately
- **AND** the storage format is human-readable JSON
- **AND** invalid station data is rejected with clear error messages

#### Scenario: Data Migration and Recovery

- **WHEN** the system starts with existing station data
- **THEN** it validates and loads saved stations into memory
- **AND** it handles corrupted data files gracefully
- **AND** it provides mechanisms to recover or reset station data if needed

#### Scenario: Concurrent Access Safety

- **WHEN** multiple API requests modify station data simultaneously
- **THEN** the system prevents data corruption through proper locking
- **AND** each request receives appropriate success/failure responses
- **AND** the persistent storage remains consistent

### Requirement: Stream URL Pre-Caching

The system SHALL resolve stream redirect URLs in the background at startup and cache them so that `play()` can start mpg123 immediately without a blocking curl resolution.

#### Scenario: URLs pre-cached at startup

- **WHEN** `RadioManager._initialize()` completes
- **THEN** a background task calls `AudioPlayer.precache_urls()` with all configured station URLs
- **AND** each URL is resolved via curl with a browser User-Agent and stored in `_url_cache`
- **AND** pre-caching runs concurrently and does not delay application startup

#### Scenario: Cache hit on play

- **WHEN** `AudioPlayer.play(url)` is called and `url` is present in `_url_cache`
- **THEN** mpg123 is spawned immediately with the cached resolved URL
- **AND** no curl subprocess is launched

#### Scenario: Cache miss on play

- **WHEN** `AudioPlayer.play(url)` is called and `url` is not in `_url_cache`
- **THEN** the system resolves the URL live via curl (existing behaviour)
- **AND** the resolved URL is stored in `_url_cache` for subsequent calls

### Requirement: Rotary Long-Press Hardware Event

The system SHALL forward rotary encoder long-press events from `GPIOController` to `RadioManager` via a registered callback, enabling application-level responses to the gesture.

#### Scenario: Long-press callback registered

- **WHEN** `RadioManager._initialize_hardware()` creates a `GPIOController` instance
- **THEN** it passes `long_press_callback=self._handle_long_press_event` to the constructor
- **AND** `GPIOController` calls this callback when a long press is detected on `ROTARY_SW`

#### Scenario: Long-press fires after threshold

- **WHEN** the rotary encoder button is held for ≥ `LONG_PRESS_DURATION` seconds (default 2.0s)
- **THEN** `GPIOController._handle_long_press()` calls `long_press_callback(gpio_pin)`
- **AND** the callback executes on the asyncio event loop (via `call_soon_threadsafe`)

### Requirement: Last-Played State Persistence

The system SHALL persist the active station slot and volume to a JSON state file on every successful play and volume change, enabling session restore on reboot.

#### Scenario: State written on play

- **WHEN** `RadioManager.play_station(slot)` succeeds
- **THEN** `{"slot": slot, "volume": current_volume}` is atomically written to `RADIO_STATE_FILE`

#### Scenario: State written on volume change

- **WHEN** `RadioManager.set_volume(volume)` is called while a station is active
- **THEN** the state file is updated with the new volume and current slot

#### Scenario: Atomic write prevents corruption

- **WHEN** the state file is written
- **THEN** the system writes to a `.tmp` file first and then renames it to the target path
- **AND** a partial write cannot leave the state file in a corrupt state

### Requirement: Stream Auto-Reconnect

The system SHALL automatically attempt to reconnect an interrupted stream after an unexpected mpg123 exit, using a bounded number of retries with increasing backoff delays. After the retry budget is exhausted, the system SHALL give up: set playback state to `error`, broadcast the state over WebSocket, and play the error notification sound once. User commands SHALL always take precedence over an in-flight reconnect.

#### Scenario: Reconnect succeeds within retry budget

- **WHEN** a stream dies unexpectedly and a reconnect attempt succeeds before the retry budget (default 5 attempts with backoff of 1s, 2s, 4s, 8s, 15s) is exhausted
- **THEN** playback resumes on the same station slot
- **AND** playback state returns to `playing` and is broadcast over WebSocket
- **AND** no error sound is played

#### Scenario: Reconnect gives up after bounded retries

- **WHEN** all reconnect attempts for an outage fail
- **THEN** playback state is set to `error` with `is_playing` false, keeping `current_station` so clients can show which station failed
- **AND** the state change is broadcast over WebSocket
- **AND** the error notification sound is played exactly once

#### Scenario: Stale cached URL is re-resolved during reconnect

- **WHEN** a reconnect attempt follows an unexpected exit
- **THEN** the stream URL is re-resolved (bypassing the pre-cached redirect URL) on retry, so an expired redirect cannot make every attempt fail

#### Scenario: User command cancels reconnect

- **WHEN** the user issues stop or selects a station (via button, API, or UI) while a reconnect is in progress
- **THEN** the in-flight reconnect task is cancelled before the command is executed
- **AND** the user's command takes effect normally

#### Scenario: Button press on a dead session restarts instead of stopping

- **WHEN** the station button for the current slot is pressed while that slot is in `connecting` (reconnecting) or `error` state
- **THEN** `toggle_station` treats the slot as not playing and starts fresh playback of that slot
- **AND** it never issues a stop against the dead session

### Requirement: Notification Sound Playback

The system SHALL play notification chimes (WAV files) through a WAV-capable player matching the active audio backend — `paplay` when the PipeWire/PulseAudio socket is available, `aplay` on the direct-ALSA fallback — never through mpg123. The `volume` parameter of `SoundManager.play_sound` SHALL be honored on backends that support per-invocation volume (`paplay`), and documented as best-effort where the backend does not (`aplay`).

#### Scenario: Chime playback via PipeWire backend

- **WHEN** a notification sound is played and the PipeWire/PulseAudio socket is present
- **THEN** the WAV file is played via `paplay`
- **AND** the requested volume (0-100) is mapped to `paplay --volume` (0-65536) and applied

#### Scenario: Chime playback via ALSA fallback

- **WHEN** a notification sound is played and no PipeWire/PulseAudio socket is present
- **THEN** the WAV file is played via `aplay` against the configured ALSA device

#### Scenario: Player availability probe at initialization

- **WHEN** `SoundManager.initialize()` runs outside mock mode
- **THEN** it verifies the WAV-capable player for the detected backend is available (both `aplay` and `paplay` are installed by `docker/Dockerfile.backend`)
- **AND** it falls back to mock mode (logging a warning) if no suitable player is found

### Requirement: Truthful Mutating API Responses

Mutating radio API endpoints (volume set, station play/toggle) SHALL execute the requested action before responding, and the response SHALL reflect the actual outcome. The API SHALL NOT report success for an action that has not yet run or that failed.

#### Scenario: Volume set reflects actual outcome

- **WHEN** a client calls `POST /api/radio/volume`
- **THEN** the server SHALL await the volume change before responding
- **AND** respond with `success=True` and the applied (limit-clamped) volume only if the audio backend accepted the change
- **AND** respond with an error (`success=False` or HTTP 5xx) if the volume change failed

#### Scenario: Station toggle reflects actual resulting state

- **WHEN** a client calls `POST /api/radio/stations/{slot}/play`
- **THEN** the server SHALL await the toggle before responding
- **AND** the response action ("started" or "stopped") SHALL be derived from the state before mutation together with the toggle's actual result, never computed after scheduling a background task
- **AND** the response SHALL report the resulting playback state for the slot
- **AND** a failed stream start SHALL NOT be reported as started

#### Scenario: No fire-and-forget success

- **WHEN** any mutating radio endpoint handles a request
- **THEN** it SHALL NOT schedule the state change as a background task and return success beforehand

