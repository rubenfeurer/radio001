# Radio Integration Plan

## Overview

Unified Radio + WiFi system combining reliable WiFi management with internet radio capabilities.

## Architecture

```
radio001/
├── frontend/           # SvelteKit frontend
│   ├── src/routes/     # WiFi + Radio pages
│   ├── src/lib/stores/ # State management
│   └── src/lib/components/
├── backend/            # FastAPI backend
│   ├── core/           # Radio business logic
│   ├── hardware/       # GPIO & audio controls
│   └── api/routes/     # API endpoints
├── data/               # Station storage
└── assets/sounds/      # Notification sounds
```

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Infrastructure | Complete |
| 2 | Core Backend (radio manager, stations, audio) | Complete |
| 3 | API Integration | Complete |
| 4 | Frontend Integration | **In Progress** |
| 5 | Hardware Integration (GPIO, buttons) | Backend Complete |
| 6 | UI Integration | Pending |
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
- Mock mode for development (no Pi required)
- 142+ comprehensive tests

### Hardware Support
- GPIO controller for 3 buttons + rotary encoder
- Button press detection (short/long/triple)
- Mock hardware for development
- Pi-ready when deployed

### API Endpoints

**Radio Control:**
- `GET /radio/status` - System status
- `POST /radio/volume` - Set volume
- `POST /radio/stop` - Stop playback

**Stations:**
- `GET /radio/stations` - Get all stations
- `GET /radio/stations/{slot}` - Get station by slot
- `POST /radio/stations/{slot}` - Save station
- `POST /radio/stations/{slot}/toggle` - Play/stop
- `DELETE /radio/stations/{slot}` - Remove station

**WebSocket:**
- `WS /ws/radio` - Real-time updates

## Next Steps (Phase 4)

See [PHASE4_IMPLEMENTATION_PLAN.md](./PHASE4_IMPLEMENTATION_PLAN.md) for details.

1. **Type Definitions** - Extend `types.ts` with radio interfaces
2. **Radio Store** - Create `stores/radio.ts` for state management
3. **UI Components** - StationCard, VolumeControl, RadioStations
4. **Radio Pages** - `/radio` route and pages
5. **Dashboard Integration** - Radio status on main page
6. **Navigation** - Add radio to main navigation

## Configuration

Radio settings in `config/radio.conf`:

```bash
# Station slots
RADIO_STATION_SLOTS=3

# Volume limits
RADIO_DEFAULT_VOLUME=50
RADIO_MIN_VOLUME=30
RADIO_MAX_VOLUME=100

# GPIO pins (Pi only)
BUTTON_PIN_1=17
BUTTON_PIN_2=16
BUTTON_PIN_3=26
ROTARY_CLK=11
ROTARY_DT=9
ROTARY_SW=10
```

## Development

```bash
# Start backend
docker compose -f compose/docker-compose.yml up radio-backend -d

# Test radio API
curl http://localhost:8000/radio/status
curl http://localhost:8000/radio/stations

# Run tests
cd backend && ./run_tests.sh
```

## Default Stations

Pre-configured Swiss radio stations:
1. **Slot 1**: SRF 1 (Swiss public radio)
2. **Slot 2**: SRF 3 (Pop/Rock)
3. **Slot 3**: Radio Swiss Jazz
