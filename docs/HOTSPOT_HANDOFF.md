# Hotspot Mode - Implementation State & Recovery Guide

## Current State (2026-02-11 18:05 CET)

**Branch**: `develop` at commit `65414c2` ("Introduce hotspot-mode flow and update APIs")

**Pi Network**: Connected to WiFi "froschland" at `192.168.50.211` via SSH.

**Container**: `radio-backend-dev` running, healthy, image built at 18:02.

**Host mode marker**: `/etc/raspiwifi/host_mode` does NOT exist (clean state).

## What Was Changed

Hotspot mode switching was rewritten to work **without rebooting**. Previously it tried `sudo reboot` inside Docker which failed with "System has not been booted with systemd as init system".

### Files Modified (commit `65414c2`)

| File | Change |
|------|--------|
| `backend/core/wifi_manager.py` | Added `_run_cmd()` helper, `_generate_config()` for template substitution. Rewrote `switch_to_host_mode()` to inline-activate hotspot (hostapd + dnsmasq + static IP). Rewrote `switch_to_client_mode()` to stop hotspot services and re-enable NetworkManager. No more `sudo reboot`. Added constructor params for hotspot config. |
| `backend/main.py` | Passes `HOTSPOT_SSID`, `HOTSPOT_PASSWORD`, `HOTSPOT_IP`, `HOTSPOT_DHCP_RANGE` from env to WiFiManager. |
| `backend/api/routes/system.py` | Renamed endpoint `POST /system/reset` to `POST /system/hotspot-mode`. Updated response messages. |
| `backend/api/routes/wifi.py` | Updated `POST /wifi/connect` response messages (no more reboot references). |
| `frontend/src/lib/stores/wifi.ts` | Updated API call from `/api/system/reset` to `/api/system/hotspot-mode`. |
| `docker/Dockerfile.backend` | Added `hostapd`, `dnsmasq`, `tee` to sudo NOPASSWD list. |
| `compose/docker-compose.yml` | Added `env_file: ../config/radio.conf`. Added volume mounts for hostapd and dnsmasq config templates. |
| `README.md` | Updated endpoint reference and hotspot feature description. |
| `docs/CONFIGURATION.md` | Updated Docker integration section with env_file and template mounts. |

## How Hotspot Mode Works Now

### Activating Hotspot (`POST /system/hotspot-mode`)

1. Creates `/etc/raspiwifi/host_mode` marker
2. Disconnects WiFi: `sudo nmcli device disconnect wlan0`
3. Waits 2 seconds
4. Flushes IP, sets static `192.168.4.1/24` on `wlan0`
5. Generates `/etc/hostapd/hostapd.conf` from template
6. Generates `/etc/dnsmasq.conf` from template
7. Starts `sudo hostapd -B /etc/hostapd/hostapd.conf`
8. Starts `sudo dnsmasq -C /etc/dnsmasq.conf`
9. Verifies both are running via `pgrep`

### Deactivating Hotspot (`POST /wifi/connect` with SSID/password)

1. WiFi connection is established first via `nmcli`
2. Then `switch_to_client_mode()` runs:
   - Kills `hostapd` and `dnsmasq`
   - Removes `/etc/raspiwifi/host_mode` marker
   - Flushes static IP from `wlan0`
   - Re-enables NetworkManager: `nmcli device set wlan0 managed yes`

## Test Plan (About to Execute)

1. Click "Reset to Hotspot Mode" in the UI (or `curl -X POST http://localhost:8000/system/hotspot-mode`)
2. SSH will drop when WiFi disconnects
3. Wait ~5-10 seconds for "Radio-Setup" AP to appear
4. Connect phone/laptop to "Radio-Setup" (password: `Configure123!`)
5. Navigate to `http://192.168.4.1:8000/health` to verify backend is running
6. Use UI or API to connect back to "froschland"

## Recovery If Hotspot Fails

If the AP doesn't appear after activating hotspot mode:

### Option A: Physical Access
1. Connect monitor + keyboard to Pi
2. Login as `radio` user
3. Check container: `docker logs radio-backend-dev --tail=50`
4. Manual recovery:
   ```bash
   # Remove host mode marker
   sudo rm -f /etc/raspiwifi/host_mode
   # Kill any stale hotspot processes
   sudo killall hostapd dnsmasq 2>/dev/null
   # Re-enable WiFi
   sudo nmcli device set wlan0 managed yes
   sudo nmcli connection up froschland
   ```

### Option B: Reboot
1. Power cycle the Pi
2. The boot script (`scripts/boot-wifi-check.sh`) will:
   - See `/etc/raspiwifi/host_mode` exists -> activate hotspot via shell script
   - OR if marker was removed -> try connecting to saved WiFi "froschland"

### Option C: Wait for container restart
- Container has `restart: unless-stopped`
- If the Python process crashes, it will restart
- On restart, the boot-wifi-check.sh may run (if configured as entrypoint)

## Key Paths

| Path | Purpose |
|------|---------|
| `/etc/raspiwifi/host_mode` | Marker file - hotspot active when present |
| `/etc/hostapd/hostapd.conf.template` | Template (mounted from `config/hostapd/`) |
| `/etc/hostapd/hostapd.conf` | Generated config (written at activation) |
| `/etc/dnsmasq.conf.template` | Template (mounted from `config/dnsmasq/`) |
| `/etc/dnsmasq.conf` | Generated config (written at activation) |
| `config/radio.conf` | All hotspot settings (SSID, password, IP, DHCP) |

## Container Verification Commands

```bash
# Check if container is running
docker compose -f compose/docker-compose.yml ps

# Check logs
docker compose -f compose/docker-compose.yml logs --tail=50 radio-backend

# Check env vars are loaded
docker exec radio-backend-dev env | grep HOTSPOT

# Check sudo permissions include hostapd/dnsmasq
docker exec -u root radio-backend-dev cat /etc/sudoers.d/radio

# Check templates are mounted
docker exec radio-backend-dev ls -la /etc/hostapd/hostapd.conf.template /etc/dnsmasq.conf.template

# Test API endpoint
curl -X POST http://localhost:8000/system/hotspot-mode

# Check hotspot status
curl http://localhost:8000/wifi/status
curl http://localhost:8000/system/status
```

## Known Issues

- `system.py:get_system_metrics()` has a bug: `cannot access local variable 'os'` — it re-imports `os` inside a try block which shadows the module-level import. Not related to hotspot but shows in logs.
- Boot script (`boot-wifi-check.sh`) is a separate flow from the Python backend — it runs at container startup independently.
