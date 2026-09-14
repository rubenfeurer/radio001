## REMOVED Requirements

### Requirement: radio.local resolves in hotspot mode
**Reason**: Dead code — the mechanism behind this requirement (dnsmasq started from the container via `sudo systemctl`) never worked: `systemctl` is not installed in the image, is not permitted by sudoers, and the container has no access to host systemd. `radio.local` has never resolved in hotspot mode in production.
**Migration**: Hotspot clients use the gateway IP directly. All setup instructions (UI, API responses, installer output) surface `http://192.168.4.1:8000` while in hotspot mode. Client-mode resolution of `radio.local` via avahi/mDNS is unaffected.

### Requirement: dnsmasq lifecycle tied to hotspot mode
**Reason**: The container-side `sudo systemctl unmask/start/stop/mask dnsmasq` calls in `wifi_manager.py` can never succeed (no systemctl binary, no sudoers entry, no host-systemd access). The lifecycle was never actually managed.
**Migration**: The `systemctl` invocations are deleted from `switch_to_host_mode()` and `switch_to_client_mode()`. NetworkManager's `nmcli device wifi hotspot` provides DHCP for hotspot clients on its own; no dnsmasq is needed for clients to reach `192.168.4.1:8000`.

### Requirement: dnsmasq install and configuration
**Reason**: `install.sh` installed and masked dnsmasq and disabled the systemd-resolved DNS stub listener solely to support the dead container-side start path. Host DNS configuration was being mutated for a feature that never functioned.
**Migration**: The dnsmasq install/mask, `/etc/dnsmasq.d/radio-hotspot.conf`, and `/etc/systemd/resolved.conf` edits are removed from `install.sh`. Hosts installed with the old script keep their (inert) masked dnsmasq and `DNSStubListener=no` setting; no automatic revert is performed as both are harmless.

## MODIFIED Requirements

### Requirement: Setup page shows correct URL
The WiFi setup page SHALL display mode-appropriate access URLs. While the device is in hotspot (AP) mode, instructions SHALL direct clients to the gateway IP `http://192.168.4.1:8000` and SHALL NOT promise `radio.local` (which does not resolve on the hotspot). In client WiFi mode, `http://radio.local:8000` (mDNS) MAY be shown alongside the LAN IP.

#### Scenario: Hotspot mode instructions show gateway IP
- **WHEN** the setup page or API returns hotspot connection instructions (device in or entering hotspot mode)
- **THEN** the URL shown is `http://192.168.4.1:8000`
- **AND** no instruction claims `radio.local` is reachable from the hotspot

#### Scenario: Client mode instructions may use mDNS name
- **WHEN** the device is connected to a WiFi network in client mode
- **THEN** instructions MAY show `http://radio.local:8000` (resolved via avahi/mDNS on the LAN)

#### Scenario: No typo hostname
- **WHEN** the setup page displays any connection instructions
- **THEN** the string `radiod.local` does not appear anywhere on the page
