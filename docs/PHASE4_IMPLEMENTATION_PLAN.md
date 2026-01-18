# Phase 4: Frontend Integration

## Overview

Add radio UI to existing SvelteKit frontend with state management and real-time WebSocket updates.

## Implementation Steps

### 1. Type Definitions
**File:** `frontend/src/lib/types.ts`

```typescript
export interface RadioStation {
    name: string;
    url: string;
    slot: number;
    country?: string;
    location?: string;
}

export interface RadioStatus {
    current_station: number | null;
    volume: number;
    is_playing: boolean;
    playback_state: 'stopped' | 'playing' | 'paused' | 'buffering' | 'error';
}
```

### 2. Radio Store
**File:** `frontend/src/lib/stores/radio.ts`

Features:
- Station management state (3-slot system)
- Volume control with hardware limits
- Playback status with real-time updates
- WebSocket integration
- API functions for all radio endpoints

### 3. UI Components
**Directory:** `frontend/src/lib/components/radio/`

| Component | Purpose |
|-----------|---------|
| `StationCard.svelte` | Station display with play/stop |
| `VolumeControl.svelte` | Volume slider and buttons |
| `RadioStations.svelte` | Main container for all slots |

### 4. Radio Pages
**Directory:** `frontend/src/routes/radio/`

- `/radio` - Main radio interface with stations and volume
- Real-time "Now Playing" display
- WebSocket connection status

### 5. Dashboard Integration
**File:** `frontend/src/routes/+page.svelte`

- Add radio status card
- Quick play/stop controls
- Current station and volume display

### 6. Navigation
Add radio link to main navigation alongside WiFi.

## File Structure After Implementation

```
frontend/src/
├── lib/
│   ├── components/radio/
│   │   ├── StationCard.svelte
│   │   ├── VolumeControl.svelte
│   │   └── RadioStations.svelte
│   ├── stores/
│   │   ├── radio.ts          # New
│   │   └── wifi.ts           # Existing
│   └── types.ts              # Extended
└── routes/
    ├── radio/+page.svelte    # New
    └── +page.svelte          # Updated
```

## API Endpoints Used

```
GET  /radio/status              # System status
GET  /radio/stations            # All stations
POST /radio/stations/{slot}     # Save station
POST /radio/stations/{slot}/toggle  # Play/stop
POST /radio/volume              # Set volume
POST /radio/stop                # Stop playback
WS   /ws/radio                  # Real-time updates
```

## WebSocket Messages

| Type | Description |
|------|-------------|
| `station_change` | Station switched or stopped |
| `volume_change` | Volume level updated |
| `playback_state` | Playing/stopped/buffering |
| `error` | Playback errors |

## Design Guidelines

- Match existing WiFi UI card layouts and styles
- Mobile-first (320px+ screens)
- Dark mode support
- Accessible (ARIA labels, keyboard navigation)

## Testing Checklist

- [ ] Station loading and display
- [ ] Play/stop functionality
- [ ] Volume control with limits (30-100%)
- [ ] WebSocket real-time updates
- [ ] Error handling
- [ ] Mobile responsiveness
- [ ] Dark mode

## Development

```bash
# Start backend
docker compose -f compose/docker-compose.yml up radio-backend -d

# Start frontend dev server
cd frontend && npm run dev

# Test endpoints
curl http://localhost:8000/radio/status
```
