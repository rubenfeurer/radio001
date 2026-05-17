## ADDED Requirements

### Requirement: WiFi Network Discovery and Connection

The system must provide reliable WiFi network scanning, connection, and management capabilities using NetworkManager.

#### Scenario: WiFi Network Scanning

- **WHEN** a user requests to scan for available WiFi networks
- **THEN** the system uses `nmcli device wifi list` to discover networks
- **AND** returns a list of networks with SSID, signal strength, security type, and frequency
- **AND** filters out hidden networks and duplicates appropriately
- **AND** scanning completes within reasonable time limits (30 seconds max)

#### Scenario: WiFi Network Connection — new network

- **WHEN** a user attempts to connect to a network with no existing NM profile
- **THEN** the system SHALL use `nmcli device wifi connect <ssid> password <pw>` to create a new profile
- **AND** provides immediate feedback on connection success or failure
- **AND** allows user-controlled retry rather than automatic retry loops
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

### Requirement: WiFi Interface Management

The system must properly manage WiFi interface states and handle transitions between client and hotspot modes.

#### Scenario: Interface State Control

- **WHEN** switching between WiFi client and hotspot modes
- **THEN** the system properly manages the WiFi interface using `nmcli device set managed`
- **AND** ensures clean disconnection before mode switches
- **AND** handles interface state conflicts gracefully
- **AND** verifies interface readiness before attempting operations

#### Scenario: NetworkManager Integration

- **WHEN** performing any WiFi operation
- **THEN** the system uses NetworkManager CLI (nmcli) exclusively
- **AND** does not directly manipulate wpa_supplicant or low-level WiFi tools
- **AND** respects NetworkManager's connection management and security policies
- **AND** leverages NetworkManager's built-in retry and recovery mechanisms

#### Scenario: WiFi Security Handling

- **WHEN** connecting to secured WiFi networks
- **THEN** the system supports WPA2, WPA3, and enterprise security methods
- **AND** handles password validation and security protocol negotiation
- **AND** stores credentials securely using NetworkManager's keyring integration
- **AND** provides clear error messages for authentication failures

### Requirement: Boot-time WiFi Behavior

The system must automatically establish WiFi connectivity on boot with appropriate fallback to hotspot mode.

#### Scenario: Boot WiFi Check

- **WHEN** the system boots up
- **THEN** it waits for the WiFi interface to become available
- **AND** attempts to connect to saved networks for a configurable timeout period
- **AND** falls back to hotspot mode if no connection is established
- **AND** logs all boot-time WiFi decisions clearly

#### Scenario: Saved Network Auto-Connection

- **WHEN** the system detects saved WiFi networks in range during boot
- **THEN** it automatically attempts connection to the highest priority saved network
- **AND** respects NetworkManager's connection priority settings
- **AND** provides status updates during the connection process
- **AND** handles multiple available saved networks appropriately

#### Scenario: Boot Fallback Configuration

- **WHEN** HOTSPOT_ENABLE_FALLBACK is disabled in configuration
- **THEN** the system skips automatic hotspot fallback on boot
- **AND** continues to attempt WiFi connections indefinitely
- **AND** still allows manual hotspot activation via API
- **AND** logs the disabled fallback status clearly

### Requirement: WiFi Error Handling and Recovery

The system must provide robust error handling for WiFi operations with clear user feedback and automatic recovery where appropriate.

#### Scenario: Connection Failure Handling

- **WHEN** a WiFi connection attempt fails
- **THEN** the system provides specific error information (authentication, signal, timeout, etc.)
- **AND** suggests appropriate remediation steps based on the failure type
- **AND** does not automatically retry without user consent
- **AND** maintains system stability regardless of connection failures

#### Scenario: Interface Recovery

- **WHEN** the WiFi interface enters an error state
- **THEN** the system can reset the interface using NetworkManager commands
- **AND** it attempts graceful recovery before suggesting system restart
- **AND** it logs recovery attempts and their outcomes
- **AND** it provides manual recovery options through the API

#### Scenario: NetworkManager Service Health

- **WHEN** NetworkManager service is not responding or has issues
- **THEN** the system detects the service health problems
- **AND** provides appropriate error messages to users
- **AND** attempts basic service recovery where possible
- **AND** gracefully degrades functionality when NetworkManager is unavailable

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