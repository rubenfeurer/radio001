# Homepage Radio Controls

## Capability

`homepage-radio-controls`: Users can view radio status and control playback, volume, and station switching directly from the homepage dashboard.

## Behavior

### Radio Card Display
- A "Radio" card section appears between the WiFi Status card and the Action Buttons
- The card contains: now-playing status line, 3 station slot buttons, and a volume slider

### Now Playing Status
- Shows the current station name when playing, or "Stopped" when not playing
- Shows a playing/stopped indicator (visual dot or icon)
- When WebSocket is disconnected, shows "Connecting..." state

### Station Slot Buttons
- 3 buttons displayed in a row, one per slot (1, 2, 3)
- Each button shows the station name if configured, or "(empty)" if unconfigured
- Tapping a slot with a configured station calls `playStation()` to start playback
- Tapping the currently playing slot calls `stopPlayback()` to stop it (toggle behavior)
- The currently playing slot is visually highlighted
- Empty/unconfigured slots are disabled

### Volume Control
- HTML range input slider (0-100)
- Displays current volume level as a number
- On input, calls `setVolume()` which sends WebSocket message
- Updates optimistically on local input, confirmed by WebSocket `volume_update`

### Data Flow
- On mount: calls `loadStations()` and `getStatus()` from radio store
- WebSocket provides real-time updates via existing handlers in `websocket.ts`:
  - `stations_list` → updates station slots
  - `playback_status` → updates playing state and current station
  - `volume_update` → updates volume
  - `station_change` → updates current station

## Dependencies
- `frontend/src/lib/stores/radio.ts` (existing)
- `frontend/src/lib/stores/websocket.ts` (existing)
- `frontend/src/lib/types.ts` (existing RadioStation, PlaybackStatus types)
