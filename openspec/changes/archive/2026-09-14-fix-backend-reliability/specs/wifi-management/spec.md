# wifi-management — delta for fix-backend-reliability

## MODIFIED Requirements

### Requirement: Saved Network Management

The system must allow users to view and manage previously connected WiFi networks stored in NetworkManager, including forgetting the currently active connection. Forget operations SHALL be keyed by the NetworkManager connection name (a stable identifier), never by a positional index into an enumeration.

#### Scenario: Saved Networks Retrieval

- **WHEN** a user requests the list of saved WiFi networks
- **THEN** the system queries NetworkManager's saved connections
- **AND** returns network names, last used dates, and auto-connect settings
- **AND** each entry SHALL include its NetworkManager `connection_name` for use as the stable key in subsequent operations
- **AND** excludes hotspot and system connections from the user-visible list

#### Scenario: Network Forgetting — non-current network

- **WHEN** a user chooses to forget a saved WiFi network that is not currently active
- **THEN** the client SHALL identify the network by its `connection_name` (URL-encoded in `DELETE /api/wifi/saved/{connection_name}`)
- **AND** the system SHALL pass that `connection_name` (not an SSID and not a positional index) to `nmcli connection delete`
- **AND** the system SHALL NOT re-enumerate saved networks to resolve a positional index between request validation and deletion
- **AND** provides confirmation of successful removal
- **AND** the network will require re-entering credentials on next connection

#### Scenario: Network Forgetting — currently connected network

- **WHEN** a user chooses to forget the currently active WiFi network, identified by `connection_name`
- **THEN** the system SHALL first run `nmcli device disconnect <interface>` to drop the connection
- **AND** then delete the NM connection profile using `connection_name`
- **AND** return success; the device will be left without a WiFi connection
- **AND** no HTTP 400 or backend guard SHALL prevent this operation

#### Scenario: Network Forgetting — unknown connection name

- **WHEN** a forget request names a `connection_name` that does not match any saved NetworkManager WiFi profile
- **THEN** the API SHALL respond 404 without deleting anything
- **AND** no other saved profile SHALL be affected
