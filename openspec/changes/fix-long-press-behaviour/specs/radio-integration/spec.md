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
