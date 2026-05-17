## ADDED Requirements

### Requirement: GPIO Package Available in Production Image

The arm64 Docker image SHALL include the `lgpio` Python package (built from Joan's `lg` C library source, since `python3-lgpio` and `liblgpio-dev` are absent from Debian trixie) so hardware GPIO access is available without any runtime package installation.

#### Scenario: lgpio importable in container

- **WHEN** the production container starts on Pi (arm64)
- **THEN** `python3 -c "import lgpio"` exits with code 0
- **AND** no `ModuleNotFoundError` appears in container logs

#### Scenario: amd64 image unaffected

- **WHEN** the amd64 image is built (CI / dev)
- **THEN** the lgpio install step is skipped without build failure
- **AND** the amd64 container starts normally in mock mode

### Requirement: Container User Has GPIO Device Access

The `radio` container user SHALL be a member of the `gpio` group (or equivalent) so it can open `/dev/gpiochip0` without elevated privileges.

#### Scenario: gpiochip0 accessible by radio user

- **WHEN** the production container runs on Pi
- **THEN** `docker exec radio-backend-prod python3 -c "import lgpio; h = lgpio.gpiochip_open(0); lgpio.gpiochip_close(h)"` succeeds without permission errors

### Requirement: GPIO Controller Initialises in Hardware Mode

The `GPIOController` SHALL successfully initialise in hardware mode (not mock) when lgpio is available and `/dev/gpiochip0` is accessible.

#### Scenario: Startup log confirms hardware mode

- **WHEN** the container starts in production (NODE_ENV=production)
- **THEN** container logs contain `GPIO hardware initialized successfully via lgpio`
- **AND** logs do NOT contain `GPIO mock interface initialized`

#### Scenario: Fallback logged explicitly on failure

- **WHEN** GPIO hardware initialisation fails for any reason
- **THEN** the container logs include the specific error message (e.g. `ModuleNotFoundError` or `Permission denied`)
- **AND** the system falls back to mock mode and continues operating

### Requirement: Station Buttons Trigger Playback

The three physical station buttons (GPIO pins defined in config) SHALL trigger the corresponding station playback when pressed.

#### Scenario: Short press plays station

- **WHEN** a physical station button is pressed and released (< LONG_PRESS_DURATION)
- **THEN** the radio starts playing the station assigned to that slot
- **AND** the WebSocket broadcasts an updated playback status to all connected clients

### Requirement: Rotary Encoder Controls Volume

The rotary encoder SHALL adjust audio volume in real-time when turned, using ALSA to apply the change to the running mpg123 process.

#### Scenario: Clockwise rotation increases volume

- **WHEN** the rotary encoder is turned clockwise
- **THEN** the volume increases by ROTARY_VOLUME_STEP
- **AND** the new volume is constrained to the configured maximum (100%)
- **AND** `amixer -c 2 sset PCM <volume>%` reports the new level (e.g. `[70%]`)
- **AND** the audible output level changes perceptibly

#### Scenario: Counter-clockwise rotation decreases volume

- **WHEN** the rotary encoder is turned counter-clockwise
- **THEN** the volume decreases by ROTARY_VOLUME_STEP
- **AND** the new volume is constrained to the configured minimum (30%)
- **AND** the audible output level changes perceptibly

### Requirement: ALSA Volume Control Targets Correct Card

The `amixer` invocation SHALL target card 2 (`bcm2835 Headphones`) using the simple mixer interface (`sset`) with control name `PCM`. Card 0 (`vc4-hdmi-0`) has no PCM simple control and targeting it silently fails.

#### Scenario: amixer targets correct card

- **WHEN** `set_volume` is called with any value 0–100
- **THEN** `amixer -c 2 sset PCM <value>%` exits 0
- **AND** the output confirms the new level (e.g. `Playback [70%]`)
