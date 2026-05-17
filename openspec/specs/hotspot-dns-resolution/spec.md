## ADDED Requirements

### Requirement: radio.local resolves in hotspot mode
When the Pi is in hotspot (AP) mode, any client connected to the hotspot SHALL be able to resolve `radio.local` to `192.168.4.1` via standard DNS (port 53). Resolution MUST work on macOS, iOS, Android, and Windows without any client-side configuration.

#### Scenario: DNS resolution from macOS client
- **WHEN** a macOS device is connected to the Pi hotspot and queries `radio.local`
- **THEN** the DNS response returns `192.168.4.1`
- **THEN** `http://radio.local:8000` loads the radio UI

#### Scenario: DNS resolution from Android client
- **WHEN** an Android device is connected to the Pi hotspot and queries `radio.local`
- **THEN** the DNS response returns `192.168.4.1` (Android does not use mDNS — standard DNS required)

#### Scenario: No resolution in client WiFi mode
- **WHEN** the Pi is connected to a normal WiFi network (client mode) and dnsmasq is stopped
- **THEN** `radio.local` on the LAN resolves via avahi/mDNS as before (no regression)

---

### Requirement: dnsmasq lifecycle tied to hotspot mode
dnsmasq SHALL be started when the Pi enters hotspot mode and stopped when it leaves hotspot mode. It SHALL NOT run during normal client WiFi operation.

#### Scenario: dnsmasq starts with hotspot activation via API
- **WHEN** `POST /api/system/hotspot-mode` triggers `switch_to_host_mode()`
- **THEN** dnsmasq is started (`systemctl start dnsmasq`) after the nmcli hotspot command succeeds

#### Scenario: dnsmasq stops with hotspot deactivation
- **WHEN** the Pi switches back to client WiFi mode
- **THEN** dnsmasq is stopped (`systemctl stop dnsmasq`)

#### Scenario: dnsmasq starts with boot-time hotspot fallback
- **WHEN** `boot-wifi-check.sh` creates a hotspot because no WiFi network is reachable
- **THEN** dnsmasq is started immediately after the nmcli hotspot command

#### Scenario: dnsmasq failure does not block hotspot
- **WHEN** dnsmasq fails to start (e.g. port 53 conflict)
- **THEN** the hotspot still activates; an error is logged but the hotspot is not aborted
- **THEN** clients can still reach the radio at `192.168.4.1:8000` directly

---

### Requirement: dnsmasq install and configuration
`install.sh` SHALL install dnsmasq and write `/etc/dnsmasq.d/radio-hotspot.conf` with the correct interface and address entry. The config SHALL use the `WIFI_INTERFACE` value from radio.conf (defaulting to `wlan0`).

#### Scenario: Idempotent install
- **WHEN** `install.sh` is run more than once
- **THEN** the dnsmasq config is overwritten with the correct values and no error occurs

#### Scenario: systemd-resolved conflict avoided
- **WHEN** `systemd-resolved` is running with its DNS stub listener on port 53
- **THEN** `install.sh` disables the stub listener so dnsmasq can bind to port 53

---

### Requirement: Setup page shows correct URL
The WiFi setup page SHALL display `radio.local` (not a raw IP and not the typo `radiod.local`) as the URL to navigate to after connecting to the hotspot.

#### Scenario: Correct URL shown
- **WHEN** the setup page displays hotspot connection instructions
- **THEN** the URL shown is `http://radio.local` (or `http://radio.local:8000` if port is non-standard)
- **THEN** the string `radiod.local` does not appear anywhere on the page
