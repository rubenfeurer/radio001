## MODIFIED Requirements

### Requirement: WiFi Network Discovery and Connection

The system must provide reliable WiFi network scanning, connection, and management capabilities using NetworkManager. Connection operations MUST NOT expose credentials via process arguments and MUST pass API-supplied SSIDs to nmcli in a position-safe form.

#### Scenario: WiFi Network Scanning

- **WHEN** a user requests to scan for available WiFi networks
- **THEN** the system uses `nmcli device wifi list` to discover networks
- **AND** returns a list of networks with SSID, signal strength, security type, and frequency
- **AND** filters out hidden networks and duplicates appropriately
- **AND** scanning completes within reasonable time limits (30 seconds max)

#### Scenario: WiFi Network Connection — new network

- **WHEN** a user attempts to connect to a secured network with no existing NM profile
- **THEN** the system SHALL create a profile with `nmcli connection add type wifi ... ssid <ssid>` (SSID passed as the value of the `ssid` property, never as a bare positional argument) and activate it with `nmcli connection up <name> passwd-file <path>`
- **AND** the password SHALL NOT appear anywhere in the argv of any spawned process
- **AND** if activation fails, the just-created profile is deleted so failed attempts do not accumulate
- **AND** provides immediate feedback on connection success or failure
- **AND** allows user-controlled retry rather than automatic retry loops
- **AND** validates the connection before returning success

#### Scenario: WiFi Network Connection — saved network (existing profile)

- **WHEN** a user attempts to connect to a network that has an existing NM profile
- **THEN** the system SHALL call `list_saved_networks()` to find the exact `connection_name` for that SSID
- **AND** if a match is found, use `nmcli connection up <connection_name>` (NOT `<ssid>`)
- **AND** if the user supplied a new password, it SHALL be provided via `passwd-file` on `connection up` (not via `nmcli connection modify ... wifi-sec.psk` in argv)
- **AND** SHALL NOT use substring matching to detect profile existence
- **AND** validates the connection before returning success

#### Scenario: Connection Status Monitoring

- **WHEN** the system checks WiFi connection status
- **THEN** it queries NetworkManager device status using `nmcli device status`
- **AND** returns current SSID, IP address, signal strength, and connection state
- **AND** differentiates between connected, connecting, disconnected, and hotspot modes
- **AND** updates are provided in real-time via WebSocket when status changes

## ADDED Requirements

### Requirement: WiFi Credential and SSID Input Safety

The system MUST keep WiFi credentials out of process argument lists and MUST validate API-supplied SSIDs before they reach any subprocess.

#### Scenario: PSK never in process argv

- **WHEN** the system performs any nmcli operation that requires a WiFi password (new connection or password update)
- **THEN** the password is supplied via a NetworkManager `passwd-file` (or equivalent non-argv channel), never as a command-line argument
- **AND** the passwd-file is created with mode 0600
- **AND** the passwd-file is deleted immediately after the nmcli call completes, including on failure

#### Scenario: SSID validation

- **WHEN** an API request supplies an SSID for connection
- **THEN** the system rejects SSIDs that are empty, longer than 32 bytes, or contain control characters (including `\n` and `\r`) before spawning any subprocess
- **AND** the rejection produces a clear error message to the caller

#### Scenario: Dash-prefixed SSID handled safely

- **WHEN** an API request supplies a syntactically valid SSID beginning with `-` (e.g. `-mynetwork`)
- **THEN** the SSID is passed to nmcli only as the value following the `ssid` property keyword, so it cannot be interpreted as an nmcli option
- **AND** the connection attempt proceeds normally for that SSID
