## ADDED Requirements

### Requirement: NetworkManager-Based Hotspot Mode

The system must provide instant hotspot mode switching using NetworkManager without requiring system reboots or complex configuration files.

#### Scenario: Hotspot Mode Activation

- **WHEN** the system needs to switch to hotspot mode (via API or boot fallback)
- **THEN** it creates a host mode marker file at `/etc/raspiwifi/host_mode`
- **AND** it disconnects any active WiFi connections using `nmcli device disconnect`
- **AND** it starts hotspot using `nmcli device wifi hotspot` with configured SSID and password
- **AND** the hotspot provides immediate connectivity without reboot

#### Scenario: Automatic DHCP and IP Configuration

- **WHEN** hotspot mode is activated via nmcli
- **THEN** NetworkManager automatically configures AP mode, DHCP server, and IP assignment
- **AND** clients can connect and receive IP addresses in the configured range
- **AND** no separate hostapd or dnsmasq configuration files are required

#### Scenario: Hotspot Deactivation

- **WHEN** a successful WiFi connection is established
- **THEN** the system stops the hotspot connection using `nmcli connection down Hotspot`
- **AND** it removes the host mode marker file
- **AND** it re-enables NetworkManager management of the WiFi interface
- **AND** it switches to client mode for normal WiFi operation

#### Scenario: Host Mode Detection

- **WHEN** the system status is queried
- **THEN** it checks for the existence of `/etc/raspiwifi/host_mode` marker file
- **AND** if marker exists, returns `mode: "host"` with hotspot details
- **AND** if marker missing, queries actual NetworkManager device status
- **AND** provides accurate WiFi state regardless of mode

#### Scenario: Boot-time Hotspot Fallback

- **WHEN** the system boots without WiFi connectivity
- **THEN** it waits for the configured timeout period (WIFI_BOOT_TIMEOUT)
- **AND** if no WiFi connection is established within timeout, activates hotspot mode
- **AND** the fallback can be disabled via HOTSPOT_ENABLE_FALLBACK configuration
- **AND** the system logs the fallback decision clearly

#### Scenario: Hotspot Configuration Customization

- **WHEN** hotspot settings are configured in radio.conf
- **THEN** the system uses custom HOTSPOT_SSID and HOTSPOT_PASSWORD values
- **AND** hotspot IP address and DHCP range can be customized
- **AND** the hotspot URL for client access can be configured
- **AND** all settings take effect immediately when hotspot mode is activated

#### Scenario: NetworkManager Hotspot Recovery

- **WHEN** hotspot mode encounters issues or needs to be restarted
- **THEN** the system can recover by disconnecting and re-creating the hotspot connection
- **AND** it handles NetworkManager state conflicts gracefully
- **AND** it provides clear error messages for hotspot creation failures
- **AND** it can fall back to alternative hotspot approaches if needed

#### Scenario: Concurrent Mode Prevention

- **WHEN** the system is in hotspot mode
- **THEN** it prevents simultaneous WiFi client connections
- **AND** it ensures only one mode (client or hotspot) is active at a time
- **AND** mode transitions are atomic and reliable
- **AND** the system state remains consistent during transitions