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
- **AND** starts the new stream using MPV audio backend
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

#### Scenario: Development Mode Hardware Mocking

- **WHEN** the system runs in development mode (non-Pi environment)
- **THEN** hardware controls are mocked to return simulated responses
- **AND** API endpoints for hardware control remain functional
- **AND** developers can test hardware integration without physical GPIO

### Requirement: Audio Backend Integration

The system must provide reliable audio streaming using MPV with proper error handling and recovery.

#### Scenario: Stream Initialization

- **WHEN** a radio station is selected for playback
- **THEN** the MPV process is initialized with the stream URL
- **AND** stream metadata is captured when available
- **AND** connection failures are handled gracefully with user feedback

#### Scenario: Audio Output Configuration

- **WHEN** the system starts on different hardware platforms
- **THEN** it automatically detects and configures appropriate audio output
- **AND** it handles cases where no audio hardware is available (development)
- **AND** audio output device can be specified in configuration

#### Scenario: Stream Recovery

- **WHEN** an active radio stream fails or disconnects
- **THEN** the system attempts automatic reconnection
- **AND** it provides clear status updates about connection state
- **AND** it falls back to stopped state after reasonable retry attempts

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