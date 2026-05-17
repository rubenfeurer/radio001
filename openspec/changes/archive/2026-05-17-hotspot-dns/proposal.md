## Why

When a user connects to the Pi's WiFi hotspot (AP mode), `radio.local` does not resolve. NetworkManager advertises the Pi as the DNS gateway (192.168.4.1) but nothing on the Pi answers DNS queries, so hostname resolution silently fails. Users must know the raw IP `192.168.4.1` — an unreasonable expectation for a consumer device. Additionally, the setup page contains a typo (`radiod.local` instead of `radio.local`).

## What Changes

- `dnsmasq` installed on the Pi host via `install.sh` (host-level, not in container)
- `/etc/dnsmasq.d/radio-hotspot.conf` written by `install.sh` — resolves `radio.local` → `192.168.4.1`
- `wifi_manager.py` starts dnsmasq when hotspot activates, stops it when deactivating
- `boot-wifi-check.sh` mirrors the same start/stop logic for the boot-time hotspot path
- Setup page typo fixed: `radiod.local` → `radio.local`
- Setup page URL updated to show `radio.local` (not the raw IP) as the access URL

## Capabilities

### New Capabilities

- `hotspot-dns-resolution`: dnsmasq runs on the Pi host during hotspot mode, answering DNS queries for `radio.local` with `192.168.4.1`. Works for all clients (macOS, iOS, Android, Windows) without mDNS.

### Modified Capabilities

- none

## Impact

- **`scripts/install.sh`**: adds `dnsmasq` to apt-get install; writes `/etc/dnsmasq.d/radio-hotspot.conf`
- **`backend/core/wifi_manager.py`**: `switch_to_host_mode()` and deactivation path start/stop dnsmasq
- **`scripts/boot-wifi-check.sh`**: hotspot activation/deactivation starts/stops dnsmasq
- **`frontend/src/routes/setup/+page.svelte`**: fix typo, show `radio.local` as the URL
- No Docker image changes — dnsmasq is host-level
- No compose changes needed
