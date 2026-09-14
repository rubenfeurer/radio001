## ADDED Requirements

## Purpose
Defines requirements for how clients reach the radio UI while the device is in hotspot (AP) mode.
## Requirements
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

