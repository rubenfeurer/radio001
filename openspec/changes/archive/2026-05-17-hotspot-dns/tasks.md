## 1. install.sh — dnsmasq setup

- [x] 1.1 Add `dnsmasq` to the `apt-get install` block in `scripts/install.sh`
- [x] 1.2 After installing, disable systemd-resolved's stub listener if active: append `DNSStubListener=no` to `/etc/systemd/resolved.conf` and restart `systemd-resolved`
- [x] 1.3 Write `/etc/dnsmasq.d/radio-hotspot.conf` from install.sh, substituting `WIFI_INTERFACE` (default `wlan0`):
  ```
  interface=${WIFI_INTERFACE}
  bind-interfaces
  no-dhcp-interface=${WIFI_INTERFACE}
  address=/radio.local/192.168.4.1
  ```
- [x] 1.4 Mask dnsmasq so it does not start automatically on boot: `systemctl mask dnsmasq`

## 2. Backend — dnsmasq lifecycle in wifi_manager.py

- [x] 2.1 In `backend/core/wifi_manager.py` `switch_to_host_mode()`, add `sudo systemctl unmask dnsmasq && sudo systemctl start dnsmasq` after the nmcli hotspot command succeeds; log a warning (not an error) if it fails
- [x] 2.2 In `switch_to_client_mode()` (or wherever hotspot is deactivated), add `sudo systemctl stop dnsmasq && sudo systemctl mask dnsmasq`

## 3. Boot script — dnsmasq lifecycle in boot-wifi-check.sh

- [x] 3.1 In `scripts/boot-wifi-check.sh`, start dnsmasq after the nmcli hotspot command succeeds (same pattern as task 2.1)
- [x] 3.2 In the script's client-mode / WiFi-connected path, stop and mask dnsmasq if it is running

## 4. Frontend — fix setup page

- [x] 4.1 In `frontend/src/routes/setup/+page.svelte`, fix the typo: replace `radiod.local` with `radio.local`
- [x] 4.2 Ensure the instruction text shows `http://radio.local` as the URL to navigate to after connecting to the hotspot (update surrounding copy if needed for clarity)

## 5. Deploy and verify

- [x] 5.1 Commit all changes on `develop`, open PR to `main`, wait for CI and ARM64 image build
- [ ] 5.2 SSH to Pi and re-run `install.sh` (or manually apply steps 1.1–1.4) to install dnsmasq
- [ ] 5.3 Trigger hotspot mode via the UI (`POST /api/system/hotspot-mode`) and verify dnsmasq starts: `systemctl is-active dnsmasq`
- [ ] 5.4 Connect a phone to the "Radio-Setup" hotspot and navigate to `http://radio.local` — confirm the radio UI loads
- [ ] 5.5 Connect an Android device (no native mDNS) and verify `radio.local` resolves correctly
- [ ] 5.6 Switch back to client WiFi mode and verify dnsmasq stops: `systemctl is-active dnsmasq` returns `inactive`
