# Radio Integration Plan

## Overview

Unified Radio + WiFi system combining reliable WiFi management with internet radio capabilities.

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Infrastructure | Complete |
| 2 | Core Backend (radio manager, stations, audio) | Complete |
| 3 | API Integration | Complete |
| 4 | Frontend Integration | **In Progress** |
| 5 | Hardware Integration (GPIO, buttons) | Backend Complete |
| 6 | UI Polish | Pending |
| 7 | Data & Storage | Minor tasks remain |
| 8 | Development Tools (mock mode, testing) | Complete |
| 9 | Production Deployment | Backend Ready |

**Overall: Backend 95% complete, Frontend in progress**

## Completed Features

### Backend
- 3-slot station management with JSON persistence
- MPV audio streaming integration
- Volume control with hardware limits (30-100%)
- WebSocket real-time updates
- WiFi management with nmcli (scan, connect, forget, hotspot)
- Hotspot mode via `nmcli device wifi hotspot` (no reboot required)
- Mock mode for development (no Pi required)
- 142+ comprehensive tests

### Hardware Support
- GPIO controller for 3 buttons + rotary encoder
- Button press detection (short/long/triple)
- Mock hardware for development

### API Endpoints

**WiFi:**
- `GET /wifi/status` - Connection status
- `POST /wifi/scan` - Scan networks
- `POST /wifi/connect` - Connect to network
- `GET /wifi/saved` - Saved networks
- `DELETE /wifi/saved/{id}` - Forget network
- `POST /system/hotspot-mode` - Switch to hotspot AP

**Radio:**
- `GET /radio/status` - System status
- `POST /radio/volume` - Set volume
- `POST /radio/stop` - Stop playback
- `GET /radio/stations` - Get all stations
- `POST /radio/stations/{slot}` - Save station
- `POST /radio/stations/{slot}/toggle` - Play/stop
- `DELETE /radio/stations/{slot}` - Remove station
- `WS /ws/radio` - Real-time updates

## Phase 4: Frontend Integration

### Steps
1. **Type Definitions** - Extend `types.ts` with radio interfaces
2. **Radio Store** - Create `stores/radio.ts` for state management
3. **UI Components** - StationCard, VolumeControl, RadioStations
4. **Radio Pages** - `/radio` route
5. **Dashboard Integration** - Radio status on main page
6. **Navigation** - Add radio to main nav

### Target File Structure
```
frontend/src/
├── lib/
│   ├── components/radio/
│   │   ├── StationCard.svelte
│   │   ├── VolumeControl.svelte
│   │   └── RadioStations.svelte
│   ├── stores/
│   │   ├── radio.ts
│   │   └── wifi.ts
│   └── types.ts
└── routes/
    ├── radio/+page.svelte
    └── +page.svelte
```

### WebSocket Messages

| Type | Description |
|------|-------------|
| `station_change` | Station switched or stopped |
| `volume_change` | Volume level updated |
| `playback_state` | Playing/stopped/buffering |
| `error` | Playback errors |

### Design Guidelines
- Match existing WiFi UI card layouts and styles
- Mobile-first (320px+ screens)
- Dark mode support
- Accessible (ARIA labels, keyboard navigation)

## Configuration

Radio settings in `config/radio.conf`:

```bash
RADIO_STATION_SLOTS=3
RADIO_DEFAULT_VOLUME=50
RADIO_VOLUME_STEP=5
```

## Default Stations

Pre-configured Swiss radio stations:
1. **Slot 1**: SRF 1 (Swiss public radio)
2. **Slot 2**: SRF 3 (Pop/Rock)
3. **Slot 3**: Radio Swiss Jazz
