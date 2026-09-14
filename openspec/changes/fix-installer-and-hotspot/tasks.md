# Tasks — Fix Installer and Hotspot

## 1. Remove dnsmasq dead code

- [x] 1.1 Delete the `sudo systemctl stop/mask dnsmasq` calls and related logging from `switch_to_client_mode()` in `backend/core/wifi_manager.py` (lines 694-697)
- [x] 1.2 Delete the `sudo systemctl unmask/start dnsmasq` calls and related logging from `switch_to_host_mode()` in `backend/core/wifi_manager.py` (lines 764-774); keep the hotspot-active log line referencing SSID and gateway IP
- [x] 1.3 Remove the dnsmasq section from `scripts/install.sh` (lines 211-248): apt install, `/etc/systemd/resolved.conf` `DNSStubListener` edit + resolved restart, `/etc/dnsmasq.d/radio-hotspot.conf`, and `systemctl mask dnsmasq`
- [x] 1.4 Update backend tests touching mode switching so no dnsmasq/systemctl expectations remain

## 2. Surface gateway IP in hotspot mode

- [x] 2.1 Update hotspot instructions in `backend/api/routes/system.py` (`~line 244`) and `backend/api/routes/wifi.py` (`~line 105`) to be mode-appropriate: `http://192.168.4.1:8000` for hotspot mode, `http://radio.local:8000` only for client mode
- [x] 2.2 Update `frontend/src/routes/setup/+page.svelte` (`~line 340`) so post-reboot/hotspot instructions show `http://192.168.4.1:8000` (and the hotspot SSID/password), not `http://radio.local`
- [x] 2.3 Grep the repo for remaining hotspot-mode promises of `radio.local` (docs, UI strings, API responses) and fix them; confirm `radiod.local` appears nowhere

## 3. Unify hotspot password

- [x] 3.1 In `scripts/install.sh`, generate a random 12-char alphanumeric password (`tr -dc 'A-Za-z0-9' </dev/urandom | head -c 12`) when writing a fresh `radio.conf`; write it as `HOTSPOT_PASSWORD=`; keep the existing skip-if-exists idempotency so re-runs preserve it
- [x] 3.2 Align the dev/CI default to a single documented value `radio123`: update `config/radio.conf` (replace `Configure123!`, add a dev-only comment) and the fallback in `backend/api/routes/system.py:230`; verify `docker/compose.ci.yml` already uses `radio123`
- [x] 3.3 Ensure the setup/settings UI shows the current hotspot SSID and password from settings (`frontend/src/routes/settings/+page.svelte`, `frontend/src/routes/setup/+page.svelte`)
- [x] 3.4 Print the hotspot SSID and generated password in the install script's final summary

## 4. install.sh robustness

- [x] 4.1 Replace the embedded compose heredoc (lines 53-108) with a `curl -fsSL` download of `docker/compose.prod.yml` from `https://raw.githubusercontent.com/rubenfeurer/radio001/main/` to a temp file, sanity-check it (non-empty; `docker compose -f <tmp> config -q` when available), then `mv` into `/opt/radio/docker-compose.yml`
- [x] 4.2 Reconcile `docker/compose.prod.yml` with what install.sh previously wrote: pin `containrrr/watchtower:1.7.1` (or a deliberate newer pin) so the downloaded file matches the tested config
- [x] 4.3 Replace `chmod 777 "${DATA_DIR}"` with `chown` to the container runtime UID/GID (verify against the image's Dockerfile user) plus non-world-writable mode; define the UID as a variable next to `IMAGE`
- [x] 4.4 Write `radio.conf` and the systemd unit via temp file + `mv` (atomic); add an `ERR` trap that names the failed step and states that re-running the script is safe
- [x] 4.5 Fix the final message (lines 263-267): show `http://<pi-ip>:8000` and `http://radio.local:8000`, drop the port-less `http://radio.local` claim

## 5. systemd unit fix

- [x] 5.1 In the `radio.service` heredoc in `scripts/install.sh`: remove `Restart=on-failure` and `RestartSec=10s`; remove `StartLimitIntervalSec`/`StartLimitBurst` from `[Service]` (move to `[Unit]` only if start-rate limiting is still wanted); keep `Type=oneshot` + `RemainAfterExit=yes`
- [x] 5.2 Verify the unit loads cleanly: `systemd-analyze verify` (or `systemctl daemon-reload` + journal check) reports no invalid/ignored directives

## 6. Verification

- [x] 6.1 Run backend tests and lint/type checks; run `shellcheck scripts/install.sh`
- [x] 6.2 CI compose check: `docker compose -f docker/compose.prod.yml config -q` and `docker compose -f docker/compose.ci.yml config -q` pass
- [ ] 6.3 Fresh-Pi install verification: run the updated `install.sh` on a clean Pi (or re-image), confirm — compose file matches `docker/compose.prod.yml`; data dir not world-writable and station state persists; `systemctl status radio.service` clean with no unit warnings; a random `HOTSPOT_PASSWORD` in `/opt/radio/config/radio.conf` and printed in the summary; no dnsmasq installed/masked by the script and `resolved.conf` untouched; final URLs with `:8000` work
- [ ] 6.4 Hotspot smoke test on the Pi: trigger hotspot mode, join `Radio-Setup` with the generated password from a phone, confirm `http://192.168.4.1:8000` loads the UI and the setup page shows the gateway IP; switch back to client mode and confirm `http://radio.local:8000` still works on the LAN
- [ ] 6.5 Idempotency check: re-run `install.sh` on the same Pi; confirm `radio.conf` (incl. password) and station data are preserved and the service restarts cleanly
