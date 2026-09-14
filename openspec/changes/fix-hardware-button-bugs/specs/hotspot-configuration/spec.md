## MODIFIED Requirements

### Requirement: Hardware-Triggered WiFi Mode Toggle

The system SHALL allow toggling between WiFi client mode and hotspot mode via a physical gesture (rotary encoder long press), in addition to the existing web UI trigger. The asynchronous mode-switch coroutines SHALL be awaited so the switch actually executes; a mode switch SHALL NOT be reported or signalled as successful unless the coroutine has run.

#### Scenario: Long press triggers hotspot mode

- **WHEN** the rotary encoder button is held for ≥ 2 seconds and the system is in client mode
- **THEN** `RadioManager._handle_long_press_event` SHALL `await WiFiManager.switch_to_host_mode()` so the coroutine executes
- **AND** `success.wav` plays on successful activation
- **AND** `error.wav` plays if the switch fails

#### Scenario: Long press triggers client mode

- **WHEN** the rotary encoder button is held for ≥ 2 seconds and the system is in hotspot mode
- **THEN** `RadioManager._handle_long_press_event` SHALL `await WiFiManager.switch_to_client_mode()` so the coroutine executes
- **AND** `success.wav` plays on successful switch
- **AND** `error.wav` plays if the switch fails

#### Scenario: Mode switch failure surfaces as an error

- **WHEN** the awaited mode-switch coroutine raises an exception
- **THEN** the error SHALL be logged
- **AND** `error.wav` SHALL play instead of the toggle silently claiming success

#### Scenario: WiFiManager unavailable

- **WHEN** `RadioManager` was initialised without a `wifi_manager` reference
- **THEN** the long-press event is logged as a warning and no mode switch is attempted

## ADDED Requirements

### Requirement: Long-Press Toggle Await Test Coverage
The long-press WiFi mode toggle SHALL be covered by unit tests that assert the mode-switch coroutines are genuinely awaited, not merely called.

#### Scenario: Host-mode switch awaited

- **WHEN** the test suite invokes `_handle_long_press_event` with a WiFi manager whose `switch_to_host_mode` is an `AsyncMock` and status reports connected client mode
- **THEN** the test SHALL assert `switch_to_host_mode` was awaited (e.g. `assert_awaited_once`), which fails if the coroutine is only created but never awaited

#### Scenario: Client-mode switch awaited

- **WHEN** the test suite invokes `_handle_long_press_event` with a WiFi manager whose `switch_to_client_mode` is an `AsyncMock` and status reports hotspot (non-client) mode
- **THEN** the test SHALL assert `switch_to_client_mode` was awaited
