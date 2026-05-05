## ADDED Requirements

### Requirement: Hardware-Triggered WiFi Mode Toggle
The system SHALL allow toggling between WiFi client mode and hotspot mode via a physical gesture (rotary encoder long press), in addition to the existing web UI trigger.

#### Scenario: Long press triggers hotspot mode
- **WHEN** the rotary encoder button is held for ≥ 2 seconds and the system is in client mode
- **THEN** `WiFiManager.switch_to_host_mode()` is called
- **AND** `success.wav` plays on successful activation
- **AND** `error.wav` plays if the switch fails

#### Scenario: Long press triggers client mode
- **WHEN** the rotary encoder button is held for ≥ 2 seconds and the system is in hotspot mode
- **THEN** `WiFiManager.switch_to_client_mode()` is called
- **AND** `success.wav` plays on successful switch
- **AND** `error.wav` plays if the switch fails

#### Scenario: WiFiManager unavailable
- **WHEN** `RadioManager` was initialised without a `wifi_manager` reference
- **THEN** the long-press event is logged as a warning and no mode switch is attempted
