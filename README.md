# Radio001

A **Raspberry Pi internet radio** with WiFi configuration UI. Built with **SvelteKit frontend** and **FastAPI backend**, running in Docker.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Architecture](https://img.shields.io/badge/architecture-ARM64-green.svg)
![Frontend](https://img.shields.io/badge/frontend-SvelteKit-ff3e00.svg)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688.svg)

## Features

### Internet Radio
- 3-slot station system — save and switch between favourite stations
- Volume control via rotary encoder or frontend slider
- Physical buttons for instant station switching
- Real-time frontend updates via WebSocket

### WiFi Management
- NetworkManager integration (nmcli)
- Scan, connect, forget networks
- Hotspot mode for headless configuration (no reboot)
- mDNS access via `http://radio.local`

### Hardware Controls
- 3 GPIO buttons → station slots 1/2/3
- Rotary encoder → volume (turn) + long-press function (push)
- lgpio driver — no daemon, works on Pi OS Trixie 64-bit

## Quick Start (Raspberry Pi)

```bash
git clone <repo-url> radio001
cd radio001

# Edit hardware pins, stations, volume defaults
nano config/radio.conf

# Start
docker compose -f compose/docker-compose.prod.yml up -d
```

Access at `http://radio.local` or `http://<pi-ip>`.

## Configuration

All settings live in **`config/radio.conf`** — a plain key=value file. No rebuild required when changing it; restart the container to apply.

```bash
# Restart after config changes
docker compose -f compose/docker-compose.prod.yml restart radio-backend
```

### Key settings

| Setting | Default | Description |
|---------|---------|-------------|
| `BUTTON_PIN_1/2/3` | 17, 16, 26 | BCM pin numbers for station buttons |
| `ROTARY_CLK/DT/SW` | 11, 9, 10 | Rotary encoder BCM pins |
| `ROTARY_CLOCKWISE_INCREASES` | true | Flip if encoder direction is reversed |
| `ROTARY_VOLUME_STEP` | 5 | Volume change per encoder click |
| `DEFAULT_VOLUME` | 50 | Volume on startup (0–100) |
| `ALSA_MIXER_CONTROL` | PCM | Run `amixer scontrols` to list options |
| `DEFAULT_STATION_1/2/3_NAME/URL` | SRF stations | Pre-loaded station slots |
| `HOTSPOT_SSID/PASSWORD` | Radio-Setup / Configure123! | AP credentials for WiFi setup |

## Project Structure

```
radio001/
├── config/
│   ├── radio.conf          # Main config — edit this
│   ├── stations.json       # Saved station state (runtime)
│   ├── avahi/              # mDNS service definition
│   ├── polkit/             # NetworkManager permissions
│   └── systemd/            # Boot service
├── backend/
│   ├── core/               # Radio logic (station manager, radio manager)
│   ├── hardware/           # GPIO controller, audio player
│   ├── api/routes/         # FastAPI endpoints + WebSocket
│   └── main.py             # App entry point, config loader
├── frontend/               # SvelteKit UI
│   └── src/
│       ├── routes/         # Pages: /, /radio, /setup, /settings
│       └── lib/            # Stores, components
├── compose/
│   ├── docker-compose.prod.yml
│   └── docker-compose.yml
├── openspec/               # Spec-driven development artifacts
└── scripts/                # Helper scripts
```

## Development Setup

```bash
# Backend (Docker)
docker compose -f compose/docker-compose.yml up radio-backend -d

# Frontend (local)
cd frontend && npm install && npm run dev
# → http://localhost:5173
# → API proxied to http://localhost:8000
```

## GPIO Wiring Reference

| Function | BCM | Physical Pin |
|----------|-----|-------------|
| Button 1 | 17 | 11 |
| Button 2 | 16 | 36 |
| Button 3 | 26 | 37 |
| Rotary CLK | 11 | 23 |
| Rotary DT | 9 | 21 |
| Rotary SW | 10 | 19 |

All pins use internal pull-ups. Buttons/encoder should connect to GND on press.

## API

Interactive docs at `http://<pi-ip>:8000/docs`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/radio/status` | Current play state, volume, active slot |
| GET | `/radio/stations/` | All 3 station slots |
| POST | `/radio/play/{slot}` | Play station in slot |
| POST | `/radio/volume` | Set volume |
| POST | `/radio/stations/{slot}` | Save station to slot |
| GET | `/wifi/status` | WiFi connection status |
| POST | `/wifi/connect` | Connect to network |
| POST | `/system/hotspot-mode` | Switch to hotspot AP |
| WS | `/ws/` | Real-time status updates |

## Spec-Driven Development

```bash
npm run opsx:new "feature-name"   # Plan a change
npm run opsx:apply                 # Implement tasks
npm run opsx:archive               # Archive when done
```

## License

MIT
