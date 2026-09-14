## ADDED Requirements

## Purpose
Defines requirements for hotspot (AP) mode configuration, credentials, and hardware-triggered mode toggling.
## Requirements
### Requirement: NetworkManager-Based Hotspot Mode

The system must provide instant hotspot mode switching using NetworkManager without requiring system reboots or complex configuration files. Mode switching SHALL NOT invoke `systemctl` (or otherwise attempt to manage host systemd units) from inside the container.

#### Scenario: Hotspot Mode Activation

- **WHEN** the system needs to switch to hotspot mode (via API or boot fallback)
- **THEN** it creates a host mode marker file at `/etc/raspiwifi/host_mode`
- **AND** it disconnects any active WiFi connections using `nmcli device disconnect`
- **AND** it starts hotspot using `nmcli device wifi hotspot` with configured SSID and password
- **AND** the hotspot provides immediate connectivity without reboot
- **AND** no `systemctl` command (e.g. for dnsmasq) is attempted from the container

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
- **AND** no `systemctl` command (e.g. stopping/masking dnsmasq) is attempted from the container

#### Scenario: Host Mode Detection

- **WHEN** the system status is queried
- **THEN** it checks for the existence of `/etc/raspiwifi/host_mode` marker file
- **AND** if marker exists, returns `mode: "host"` with hotspot details including the gateway IP (`192.168.4.1`) and access URL `http://192.168.4.1:8000`
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

### Requirement: Generated Hotspot Password

The hotspot password SHALL be generated randomly at install time (minimum 8 characters, WPA2-compatible), persisted as `HOTSPOT_PASSWORD` in `/opt/radio/config/radio.conf`, and surfaced to the owner through the setup/settings UI and the installer's final output. Exactly one fixed, documented default password (`radio123`) SHALL exist, used only in development and CI environments; production installs SHALL NOT ship a published default.

#### Scenario: Random password generated on fresh install

- **WHEN** `install.sh` writes a fresh `radio.conf` (no existing config)
- **THEN** it generates a random password of at least 8 WPA2-compatible characters
- **AND** persists it as `HOTSPOT_PASSWORD=` in `radio.conf`
- **AND** prints the hotspot SSID and password in the install summary

#### Scenario: Existing password preserved on re-install

- **WHEN** `install.sh` runs on a Pi that already has `radio.conf`
- **THEN** the existing `HOTSPOT_PASSWORD` value is preserved unchanged

#### Scenario: Password visible in settings UI

- **WHEN** the owner opens the settings page while connected to the radio
- **THEN** the current hotspot SSID and password from `radio.conf` are displayed
- **AND** the setup page shows the hotspot credentials needed to join the AP

#### Scenario: Dev and CI use the single documented default

- **WHEN** the app runs in development or CI (mock mode, `docker/compose.ci.yml`)
- **THEN** the hotspot password default is `radio123`
- **AND** no other default value (e.g. `Configure123!`) exists in the repository, including code fallbacks

### Requirement: Long-Press Toggle Await Test Coverage
The long-press WiFi mode toggle SHALL be covered by unit tests that assert the mode-switch coroutines are genuinely awaited, not merely called.

#### Scenario: Host-mode switch awaited

- **WHEN** the test suite invokes `_handle_long_press_event` with a WiFi manager whose `switch_to_host_mode` is an `AsyncMock` and status reports connected client mode
- **THEN** the test SHALL assert `switch_to_host_mode` was awaited (e.g. `assert_awaited_once`), which fails if the coroutine is only created but never awaited

#### Scenario: Client-mode switch awaited

- **WHEN** the test suite invokes `_handle_long_press_event` with a WiFi manager whose `switch_to_client_mode` is an `AsyncMock` and status reports hotspot (non-client) mode
- **THEN** the test SHALL assert `switch_to_client_mode` was awaited

