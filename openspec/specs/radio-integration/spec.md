## ADDED Requirements

### Requirement: Radio Station Management

The system must provide a 3-slot radio station management system with persistent storage and real-time audio streaming capabilities.

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

The system must provide live updates of radio playback status to connected clients without polling.

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

### Requirement: Hardware Controls Integration

The system must support physical hardware controls for radio operation without requiring the web interface.

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

The system must provide reliable audio streaming using mpg123 (subprocess) with amixer for ALSA volume control.

#### Scenario: Stream Initialization

- **WHEN** a radio station is selected for playback
- **THEN** a mpg123 subprocess is spawned with the stream URL
- **AND** connection failures are handled gracefully with user feedback
- **AND** the process is monitored for unexpected exits

#### Scenario: Audio Output Configuration

- **WHEN** the system starts on different hardware platforms
- **THEN** it automatically detects and configures appropriate ALSA audio output
- **AND** it handles cases where no audio hardware is available (mock mode)
- **AND** volume is controlled system-wide via amixer (PCM or Master control)

#### Scenario: Stream Recovery

- **WHEN** an active radio stream fails or the mpg123 process exits unexpectedly
- **THEN** the system updates playback state to reflect the failure
- **AND** it provides clear status updates about connection state
- **AND** it falls back to stopped state

### Requirement: Station Persistence

The system must reliably store and retrieve radio station configurations across system restarts.

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