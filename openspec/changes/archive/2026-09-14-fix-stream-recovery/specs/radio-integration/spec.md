## MODIFIED Requirements

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

## ADDED Requirements

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
