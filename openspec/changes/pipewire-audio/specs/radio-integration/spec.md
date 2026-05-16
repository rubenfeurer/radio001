## MODIFIED Requirements

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
- **AND** starts the new stream using PipeWire (via PulseAudio socket) when available, or direct ALSA as fallback
- **AND** provides real-time playback status updates via WebSocket

#### Scenario: Volume Management

- **WHEN** a user adjusts the volume level (via UI, API, or rotary encoder)
- **THEN** the volume is constrained to safe limits (30-100%)
- **AND** the volume setting persists across station changes
- **AND** volume changes are immediately applied via `pactl set-sink-volume @DEFAULT_SINK@` (PipeWire backend) or `amixer` (ALSA fallback)
- **AND** the OS volume slider reflects the new level when PipeWire backend is active
