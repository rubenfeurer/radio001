# radio-integration — delta for fix-backend-reliability

## MODIFIED Requirements

### Requirement: Real-time Radio Status

The system must provide live updates of radio playback status to connected clients without polling, and delivery to any one client MUST NOT be blocked by another client's connection.

#### Scenario: WebSocket Status Broadcasting

- **WHEN** radio playback status changes (play/pause/stop/volume/station)
- **THEN** all connected WebSocket clients receive immediate updates
- **AND** the update includes current station, volume, and playback state
- **AND** clients can subscribe to specific update types

#### Scenario: Initial Status Sync

- **WHEN** a client connects to the WebSocket endpoint
- **THEN** they immediately receive the current radio status
- **AND** they receive the current station configuration
- **AND** they are synchronized with the actual audio output state

#### Scenario: Stalled Client Isolation

- **WHEN** one connected WebSocket client stops reading (stalled TCP buffer) or errors during a broadcast
- **THEN** each individual send SHALL be bounded by a per-send timeout
- **AND** the stalled or failed connection SHALL be removed from the active connection set
- **AND** all other connected clients SHALL still receive the broadcast message
- **AND** subsequent broadcasts SHALL proceed without the removed connection

#### Scenario: Consistent Connection-Set Access

- **WHEN** broadcasts, connects, and disconnects occur concurrently
- **THEN** all reads and mutations of the active connection set SHALL be serialized under the connection manager's lock (snapshots may be taken under the lock and sends performed outside it)
- **AND** the lock SHALL NOT be held while awaiting a network send

## ADDED Requirements

### Requirement: Truthful Mutating API Responses

Mutating radio API endpoints (volume set, station play/toggle) SHALL execute the requested action before responding, and the response SHALL reflect the actual outcome. The API SHALL NOT report success for an action that has not yet run or that failed.

#### Scenario: Volume set reflects actual outcome

- **WHEN** a client calls `POST /api/radio/volume`
- **THEN** the server SHALL await the volume change before responding
- **AND** respond with `success=True` and the applied (limit-clamped) volume only if the audio backend accepted the change
- **AND** respond with an error (`success=False` or HTTP 5xx) if the volume change failed

#### Scenario: Station toggle reflects actual resulting state

- **WHEN** a client calls `POST /api/radio/stations/{slot}/play`
- **THEN** the server SHALL await the toggle before responding
- **AND** the response action ("started" or "stopped") SHALL be derived from the state before mutation together with the toggle's actual result, never computed after scheduling a background task
- **AND** the response SHALL report the resulting playback state for the slot
- **AND** a failed stream start SHALL NOT be reported as started

#### Scenario: No fire-and-forget success

- **WHEN** any mutating radio endpoint handles a request
- **THEN** it SHALL NOT schedule the state change as a background task and return success beforehand
