## MODIFIED Requirements

### Requirement: Triple Press Triggers Pi Reboot
When the rotary knob switch is pressed three times in quick succession, the system SHALL initiate a host Pi reboot. A press sequence counts as a triple press only when each press occurs within `TRIPLE_PRESS_INTERVAL` seconds of the previous press's **release**. The press count SHALL reset whenever the interval between consecutive releases exceeds `TRIPLE_PRESS_INTERVAL`. Fewer than three qualifying presses SHALL NEVER trigger a reboot.

#### Scenario: Triple press detected in production mode
- **WHEN** the user presses the rotary knob three times, each press within `TRIPLE_PRESS_INTERVAL` seconds of the previous press's release
- **THEN** `GPIOController` SHALL invoke `triple_press_callback` with the GPIO pin number exactly once
- **AND** `RadioManager._handle_triple_press_event` SHALL log a warning and execute `subprocess.run(["reboot"])`
- **AND** the Pi SHALL reboot within a few seconds

#### Scenario: Two presses never trigger a reboot
- **WHEN** the user presses the rotary knob exactly twice — whether in rapid succession or separated by any longer interval
- **THEN** `triple_press_callback` SHALL NOT be invoked
- **AND** no reboot SHALL occur

#### Scenario: Press count resets after the interval elapses
- **WHEN** one or two presses occur and then more than `TRIPLE_PRESS_INTERVAL` seconds pass before the next press
- **THEN** the press count SHALL reset, with the next press counting as the first of a new sequence
- **AND** a subsequent pair of presses SHALL NOT trigger a reboot
- **AND** only a fresh sequence of three presses, each within `TRIPLE_PRESS_INTERVAL` of the previous release, SHALL trigger the reboot

#### Scenario: Triple press detected in mock/development mode
- **WHEN** the user (or test) triggers a triple press event and `mock_mode` is `True`
- **THEN** the system SHALL log a warning that a reboot was requested
- **AND** the system SHALL NOT execute any reboot command
- **AND** normal operation SHALL continue uninterrupted

#### Scenario: No triple_press_callback registered
- **WHEN** `GPIOController` is instantiated without a `triple_press_callback`
- **THEN** a triple press on the rotary knob SHALL log a warning and take no further action
- **AND** the system SHALL NOT raise an exception

## ADDED Requirements

### Requirement: GPIO Press Handling Test Coverage
The `GPIOController` press-handling logic SHALL be covered by unit tests that exercise short press, long press, and triple-press timing without requiring GPIO hardware.

#### Scenario: Short press unit test
- **WHEN** the test suite simulates a press and release shorter than `LONG_PRESS_DURATION`
- **THEN** the test SHALL assert that `button_callback` is awaited for the pin
- **AND** the test SHALL assert that neither `long_press_callback` nor `triple_press_callback` is invoked

#### Scenario: Long press unit test
- **WHEN** the test suite simulates a press held for at least `LONG_PRESS_DURATION`
- **THEN** the test SHALL assert that the short-press callback is not invoked for that press
- **AND** the test SHALL assert that `long_press_callback` is awaited when the long-press handler fires

#### Scenario: Triple press timing unit tests
- **WHEN** the test suite simulates press sequences with controlled timestamps
- **THEN** three presses each within `TRIPLE_PRESS_INTERVAL` of the previous release SHALL be asserted to invoke `triple_press_callback` exactly once
- **AND** two presses at any spacing SHALL be asserted to never invoke `triple_press_callback`
- **AND** presses separated by more than `TRIPLE_PRESS_INTERVAL` SHALL be asserted to reset the press count
