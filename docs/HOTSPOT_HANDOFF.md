# Hotspot Mode - Implementation & Recovery Guide

## How It Works

All WiFi management uses **nmcli** (NetworkManager CLI). No hostapd or dnsmasq needed.

### Activating Hotspot (`POST /system/hotspot-mode`)

1. Creates `/etc/raspiwifi/host_mode` marker file
2. Disconnects WiFi: `sudo nmcli device disconnect wlan0`
3. Starts hotspot: `sudo nmcli device wifi hotspot ifname wlan0 ssid Radio-Setup password Configure123!`

That single nmcli command handles AP mode, DHCP, and IP assignment.

### Deactivating Hotspot (`POST /wifi/connect`)

When a WiFi connection succeeds, `switch_to_client_mode()` runs:

1. Stops hotspot: `sudo nmcli connection down Hotspot`
2. Removes `/etc/raspiwifi/host_mode` marker
3. Re-enables NM: `sudo nmcli device set wlan0 managed yes`

### Host Mode Detection

`WiFiManager.get_status()` checks if `/etc/raspiwifi/host_mode` exists:
- **Exists**: Returns `mode: "host"`, `ssid: "Radio-Setup"`, `ip: "192.168.4.1"`
- **Missing**: Queries `nmcli device status` for actual WiFi state

## Key Files

| File | Purpose |
|------|---------|
| `backend/core/wifi_manager.py` | `switch_to_host_mode()`, `switch_to_client_mode()`, all WiFi ops |
| `backend/api/routes/system.py` | `POST /system/hotspot-mode` endpoint |
| `backend/api/routes/wifi.py` | `POST /wifi/connect` triggers client mode switch |
| `backend/main.py` | Passes hotspot config (SSID, password, IP) from env to WiFiManager |
| `config/radio.conf` | `HOTSPOT_SSID`, `HOTSPOT_PASSWORD`, `HOTSPOT_IP` settings |
| `/etc/raspiwifi/host_mode` | Marker file — hotspot active when present |

## Docker Requirements

From `compose/docker-compose.yml`:
- `network_mode: host` — container shares host network stack
- `privileged: true` with `NET_ADMIN`, `NET_RAW` capabilities
- Volume mounts: `/etc/NetworkManager`, `/run/dbus`, `/etc/raspiwifi` (all `:rw`)
- `env_file: ../config/radio.conf` — loads hotspot settings as env vars

Sudo permissions (in Dockerfile): `nmcli`, `mkdir`, `touch`, `rm`, `ip`, `killall`

## Recovery Procedures

### If Hotspot Doesn't Appear

```bash
# Check container logs
docker compose -f compose/docker-compose.yml logs --tail=50 radio-backend

# Check if hotspot connection was created
nmcli connection show

# Manual hotspot start
sudo nmcli device wifi hotspot ifname wlan0 ssid Radio-Setup password "Configure123!"
```

### If Stuck in Hotspot Mode (No WiFi)

With physical access (monitor + keyboard):

```bash
# Remove host mode marker
sudo rm -f /etc/raspiwifi/host_mode

# Stop hotspot
sudo nmcli connection down Hotspot

# Re-enable WiFi
sudo nmcli device set wlan0 managed yes
sudo nmcli connection up froschland
```

### If Container Won't Start

```bash
# Check container status
docker compose -f compose/docker-compose.yml ps

# Force recreate
docker compose -f compose/docker-compose.yml up radio-backend -d --force-recreate

# Check logs
docker compose -f compose/docker-compose.yml logs --tail=100 radio-backend
```

## Verification Commands

```bash
# Current network state
nmcli device status
nmcli connection show

# Host mode marker
ls -la /etc/raspiwifi/host_mode

# Container env vars
docker exec radio-backend-dev env | grep HOTSPOT

# Test hotspot endpoint
curl -X POST http://localhost:8000/system/hotspot-mode

# Test WiFi status
curl http://localhost:8000/wifi/status
```

## Known Issues

- `system.py:get_system_metrics()` has a bug: re-imports `os` inside a try block, shadowing the module-level import. Shows as `cannot access local variable 'os'` in logs. Not hotspot-related.
