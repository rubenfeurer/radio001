## ADDED Requirements

### Requirement: Live volume slider throttles requests and ignores echoes while dragging
The live volume slider on the settings page SHALL NOT send one volume request per `input` event. Volume updates during a drag SHALL be throttled/debounced so the request rate is bounded, and the final slider value at the end of the drag SHALL always be sent. While the user is actively dragging, incoming WebSocket `volume_update` echoes SHALL NOT be applied to the slider's bound value, so the slider never snaps backwards mid-drag. When the user is not dragging, external volume changes (e.g. rotary encoder) SHALL still update the slider.

#### Scenario: Drag produces bounded requests with accurate final value
- **WHEN** the user drags the volume slider across many values
- **THEN** the frontend SHALL send a throttled/debounced stream of volume requests rather than one per input event
- **THEN** the last value the user released the slider at SHALL be sent to the backend

#### Scenario: WS echo does not fight the drag
- **WHEN** a WebSocket `volume_update` message arrives while the user is still dragging the slider
- **THEN** the slider position SHALL continue to follow the user's pointer and SHALL NOT jump to the echoed value

#### Scenario: External volume changes still update an idle slider
- **WHEN** the volume changes from another source (rotary encoder or another client) while the user is not interacting with the slider
- **THEN** the slider SHALL update to reflect the new volume
