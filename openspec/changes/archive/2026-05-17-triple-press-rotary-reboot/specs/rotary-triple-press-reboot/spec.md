## ADDED Requirements

### Requirement: Triple Press Triggers Pi Reboot
When the rotary knob switch is pressed three times in quick succession, the system SHALL initiate a host Pi reboot.

#### Scenario: Triple press detected in production mode
- **WHEN** the user presses the rotary knob three times within `TRIPLE_PRESS_INTERVAL` seconds
- **THEN** `GPIOController` SHALL invoke `triple_press_callback` with the GPIO pin number
- **AND** `RadioManager._handle_triple_press_event` SHALL log a warning and execute `subprocess.run(["reboot"])`
- **AND** the Pi SHALL reboot within a few seconds

#### Scenario: Triple press detected in mock/development mode
- **WHEN** the user (or test) triggers a triple press event and `mock_mode` is `True`
- **THEN** the system SHALL log a warning that a reboot was requested
- **AND** the system SHALL NOT execute any reboot command
- **AND** normal operation SHALL continue uninterrupted

#### Scenario: No triple_press_callback registered
- **WHEN** `GPIOController` is instantiated without a `triple_press_callback`
- **THEN** a triple press on the rotary knob SHALL log a warning and take no further action
- **AND** the system SHALL NOT raise an exception

### Requirement: Reboot API Endpoint
The system SHALL expose a `POST /api/system/reboot` endpoint that reboots the Pi host.

#### Scenario: Reboot endpoint called in production
- **WHEN** a client sends `POST /api/system/reboot`
- **THEN** the server SHALL respond with HTTP 200 and `{"success": true, "message": "Rebooting…"}`
- **AND** the Pi SHALL reboot within a few seconds after the response is sent

#### Scenario: Reboot endpoint called in mock/development mode
- **WHEN** a client sends `POST /api/system/reboot` and `NODE_ENV=development`
- **THEN** the server SHALL respond with HTTP 200 and `{"success": true, "message": "Reboot skipped in development mode"}`
- **AND** no actual reboot SHALL occur

### Requirement: GPIOController Triple Press Callback
`GPIOController` SHALL accept an optional `triple_press_callback` parameter and invoke it on triple press detection.

#### Scenario: Callback wired at construction time
- **WHEN** `GPIOController` is constructed with a `triple_press_callback`
- **THEN** it SHALL store the callback and invoke it (awaiting if coroutine) when `_handle_triple_press` is called for `ROTARY_SW`

#### Scenario: simulate_triple_press in mock mode
- **WHEN** `simulate_triple_press()` is called in mock mode
- **THEN** `GPIOController` SHALL simulate three button presses on `ROTARY_SW` within `TRIPLE_PRESS_INTERVAL`
- **AND** the `triple_press_callback` SHALL be invoked if registered
