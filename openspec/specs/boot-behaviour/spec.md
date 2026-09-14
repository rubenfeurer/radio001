## ADDED Requirements

## Purpose
Defines requirements for radio behaviour at boot: service start, auto-play restore, and boot feedback sounds.
## Requirements
### Requirement: Auto-Start on Boot
The system SHALL start the Docker radio stack automatically on Pi power-on via a systemd service, without requiring manual intervention. The `radio.service` unit SHALL be valid under current systemd: `Type=oneshot` with `RemainAfterExit=yes`, no `Restart=` directive (invalid for oneshot units), and no `StartLimit*` settings in the `[Service]` section. Container restart supervision is delegated to Docker via `restart: unless-stopped` in the compose file.

#### Scenario: Service starts radio from pre-built image
- **WHEN** the `radio.service` systemd unit starts (on boot or `systemctl start radio`)
- **THEN** it SHALL run `docker compose -f /opt/radio/docker-compose.yml up -d`
- **AND** no `docker build` step SHALL execute
- **AND** no local source tree SHALL be required

#### Scenario: Service does not pull on start
- **WHEN** the `radio.service` starts
- **THEN** it SHALL NOT run `docker compose pull` before starting
- **AND** image updates are delegated entirely to Watchtower on its nightly schedule

#### Scenario: Container restarts are supervised by Docker, not systemd
- **WHEN** the radio container exits unexpectedly
- **THEN** dockerd SHALL restart the container per the compose `restart: unless-stopped` policy
- **AND** the `radio.service` unit SHALL NOT declare `Restart=` or `RestartSec=`

#### Scenario: Unit file is accepted by systemd without warnings
- **WHEN** `systemctl daemon-reload` loads the installed `radio.service`
- **THEN** systemd SHALL report no invalid or ignored directives for the unit
- **AND** the unit SHALL use `Type=oneshot` with `RemainAfterExit=yes`
- **AND** any start-rate limiting, if present, SHALL live in the `[Unit]` section

#### Scenario: Service install via install script
- **WHEN** `sudo bash scripts/install.sh` is executed on the Pi
- **THEN** the script writes `/etc/systemd/system/radio.service`
- **AND** runs `systemctl daemon-reload && systemctl enable --now radio.service`
- **AND** the radio backend becomes reachable within normal container startup time

### Requirement: Boot Sounds (WiFi-Aware)
The system SHALL play an audio tone during startup to indicate whether it is ready to stream (WiFi connected) or in configuration mode (hotspot active).

#### Scenario: Successful WiFi connection at boot
- **WHEN** the radio backend initialises and `WiFiManager.get_status()` returns `connected=true` and `mode="client"`
- **THEN** `startup.wav` is played via the ALSA audio output
- **AND** the sound plays before auto-play begins

#### Scenario: No WiFi — hotspot mode at boot
- **WHEN** the radio backend initialises and `WiFiManager.get_status()` returns `connected=false` or `mode="host"`
- **THEN** `error.wav` is played via the ALSA audio output

#### Scenario: WiFi status check fails at boot
- **WHEN** `WiFiManager.get_status()` raises an exception during startup
- **THEN** the system logs a warning and plays `startup.wav` as a safe fallback
- **AND** initialisation continues normally

### Requirement: Auto-Play Last Session on Boot
The system SHALL restore and begin playing the last-used station slot at the last-used volume level after a successful start.

#### Scenario: Last session state exists
- **WHEN** the radio backend initialises and `data/radio_state.json` contains a valid slot (1–3) and volume
- **THEN** the system sets the volume to the saved value
- **AND** begins playing the saved station slot asynchronously (non-blocking initialisation)

#### Scenario: No saved state
- **WHEN** `data/radio_state.json` does not exist or contains invalid data
- **THEN** the system starts in the stopped state at `DEFAULT_VOLUME`
- **AND** no station plays automatically

#### Scenario: State persisted on play
- **WHEN** a station is successfully started via button press or web UI
- **THEN** the current slot and volume are written atomically to `data/radio_state.json`

#### Scenario: State persisted on volume change
- **WHEN** the volume is changed while a station is active
- **THEN** the updated volume is written atomically to `data/radio_state.json`

### Requirement: Audible WAV Sound Files
The system SHALL generate real audible WAV tone files at startup if the files are missing or are text placeholders (size < 200 bytes).

#### Scenario: Placeholder files replaced at startup
- **WHEN** `SoundManager` initialises and finds `assets/sounds/startup.wav`, `success.wav`, or `error.wav` with size < 200 bytes
- **THEN** it generates audible 16-bit mono WAV tones using Python stdlib only (`wave`, `struct`, `math`)
- **AND** `startup.wav` and `success.wav` use two ascending tones (C5 523 Hz → E5 659 Hz)
- **AND** `error.wav` uses two descending tones (A4 440 Hz → E4 330 Hz)

#### Scenario: Existing real files not overwritten
- **WHEN** a sound file already has size ≥ 200 bytes
- **THEN** the existing file is left unchanged

