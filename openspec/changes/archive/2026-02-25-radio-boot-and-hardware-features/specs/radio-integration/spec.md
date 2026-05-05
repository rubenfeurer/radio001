## ADDED Requirements

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

## MODIFIED Requirements

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
- **THEN** the system toggles between WiFi client mode and hotspot mode
- **AND** `success.wav` is played on successful toggle
- **AND** `error.wav` is played if the toggle fails

#### Scenario: Development Mode Hardware Mocking
- **WHEN** the system runs in development mode (non-Pi environment)
- **THEN** hardware controls are mocked to return simulated responses
- **AND** API endpoints for hardware control remain functional
- **AND** developers can test hardware integration without physical GPIO
