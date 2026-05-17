## MODIFIED Requirements

### Requirement: Saved Network Management
The system must allow users to view and manage previously connected WiFi networks stored in NetworkManager, including forgetting the currently active connection.

#### Scenario: Saved Networks Retrieval
- **WHEN** a user requests the list of saved WiFi networks
- **THEN** the system queries NetworkManager's saved connections
- **AND** returns network names, last used dates, and auto-connect settings
- **AND** excludes hotspot and system connections from the user-visible list

#### Scenario: Network Forgetting — non-current network
- **WHEN** a user chooses to forget a saved WiFi network that is not currently active
- **THEN** the system SHALL resolve the NM connection profile name via `list_saved_networks` and pass `connection_name` (not SSID) to `nmcli connection delete`
- **AND** provides confirmation of successful removal
- **AND** the network will require re-entering credentials on next connection

#### Scenario: Network Forgetting — currently connected network
- **WHEN** a user chooses to forget the currently active WiFi network
- **THEN** the system SHALL first run `nmcli device disconnect <interface>` to drop the connection
- **AND** then delete the NM connection profile using `connection_name`
- **AND** return success; the device will be left without a WiFi connection
- **AND** no HTTP 400 or backend guard SHALL prevent this operation

### Requirement: WiFi Network Connection
The system must reliably connect to both new and previously saved networks by resolving the exact NetworkManager connection profile name.

#### Scenario: WiFi Network Connection — new network
- **WHEN** a user attempts to connect to a network with no existing NM profile
- **THEN** the system SHALL use `nmcli device wifi connect <ssid> password <pw>` to create a new profile
- **AND** validates the connection before returning success

#### Scenario: WiFi Network Connection — saved network (existing profile)
- **WHEN** a user attempts to connect to a network that has an existing NM profile
- **THEN** the system SHALL call `list_saved_networks()` to find the exact `connection_name` for that SSID
- **AND** if a match is found, use `nmcli connection up <connection_name>` (NOT `<ssid>`)
- **AND** SHALL NOT use substring matching to detect profile existence
- **AND** validates the connection before returning success

#### Scenario: Connection Status Monitoring
- **WHEN** the system checks WiFi connection status
- **THEN** it queries NetworkManager device status using `nmcli device status`
- **AND** returns current SSID, IP address, signal strength, and connection state
- **AND** differentiates between connected, connecting, disconnected, and hotspot modes
- **AND** updates are provided in real-time via WebSocket when status changes

## ADDED Requirements

### Requirement: Saved Network Forget UI
The WiFi Settings page dialog SHALL expose a Forget Network action for all saved networks, including the currently connected one.

#### Scenario: Forget button for currently-connected network
- **WHEN** a user opens the dialog for the currently connected network
- **THEN** the dialog SHALL show only a "Forget Network" button (no "Close" button)
- **AND** tapping it SHALL trigger a confirmation prompt before proceeding

#### Scenario: Forget button for saved-but-not-current network
- **WHEN** a user opens the dialog for a saved network that is not currently connected
- **THEN** the dialog SHALL show "Cancel", "Connect", and "Forget Network" buttons
- **AND** tapping "Forget Network" SHALL trigger a confirmation prompt before proceeding
