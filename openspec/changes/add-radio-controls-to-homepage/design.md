## Context

The homepage (`frontend/src/routes/+page.svelte`) currently serves as a WiFi-only dashboard showing connection status and navigation buttons to WiFi Manager, System Status, and Settings. The radio backend is fully functional with a 3-slot station system, volume control, and play/stop/toggle via REST (`/radio/*`, `/radio/stations/*`) and WebSocket (`/ws/radio`). A complete radio store (`frontend/src/lib/stores/radio.ts`) and WebSocket client (`frontend/src/lib/stores/websocket.ts`) already exist with all necessary actions and state management. The frontend uses SvelteKit with Tailwind CSS and custom utility classes (`btn-primary`, `btn-secondary`, `card`).

## Goals / Non-Goals

**Goals:**
- Add radio status display and playback controls directly on the homepage
- Show 3 station slot buttons for instant switching
- Provide volume control with visual feedback
- Reuse existing radio store and WebSocket infrastructure — no new state management
- Maintain mobile-first responsive design with existing styling conventions

**Non-Goals:**
- Station configuration/editing from the homepage (that belongs on a dedicated radio management page)
- Audio visualization or stream metadata display (future enhancement)
- Horizontal/landscape layout optimizations
- Changes to the backend API

## Decisions

### 1. Inline on homepage vs. extracted components

**Decision:** Add radio controls inline in `+page.svelte`, extract to components only if reuse is needed later.

**Rationale:** There's currently only one component in `frontend/src/lib/components/` (SignalStrength.svelte). The radio controls are homepage-specific for now. Extracting prematurely adds files without benefit. If a dedicated radio page is added later, components can be extracted then.

**Alternative considered:** Create `RadioControls.svelte`, `VolumeSlider.svelte`, `StationSlot.svelte` components upfront. Rejected — no second consumer exists yet.

### 2. Data fetching approach

**Decision:** Use the existing WebSocket connection. On mount, call `loadStations()` and `getStatus()` from the radio store. The WebSocket `handleMessage` in `websocket.ts` already dispatches `stations_list`, `playback_status`, `volume_update`, and `station_change` events to the radio store.

**Rationale:** The WebSocket client already auto-connects and sends `get_status` on open. Adding `loadStations()` on mount ensures station data is available. No REST calls needed — everything flows through the existing WebSocket.

**Alternative considered:** REST API calls via fetch. Rejected — WebSocket already provides real-time updates and initial state, duplicating with REST adds complexity.

### 3. Station slot interaction

**Decision:** Each slot button calls the existing `POST /radio/stations/{slot}/toggle` endpoint via WebSocket message (`play_station` / `stop`). Tapping the currently playing station stops it. Tapping a different station switches to it.

**Rationale:** Matches the physical button behavior on the hardware (3 buttons = 3 slots). The toggle pattern is already implemented in the radio store (`playStation`, `stopPlayback`).

### 4. Volume control widget

**Decision:** HTML `<input type="range">` slider styled with Tailwind. Sends `set_volume` WebSocket messages on input. Debounce not needed — the WebSocket handler and backend already handle rapid updates gracefully.

**Rationale:** Native range input works well on mobile touch, is accessible, and requires no dependencies. The existing `setVolume()` store action handles the WebSocket communication.

### 5. Layout structure

**Decision:** Add a "Radio" card section between the WiFi Status card and the Action Buttons. Structure:
1. Now Playing status line (station name + playing/stopped indicator)
2. Station slot buttons (3 buttons in a row)
3. Volume slider with current level

**Rationale:** Keeps the radio controls visually grouped in a single card, consistent with the WiFi Status card pattern. Placing it above navigation buttons gives it prominence since radio control is the primary use case.

## Risks / Trade-offs

- **WebSocket not connected** → Radio card shows loading/disconnected state. The `isConnected` store from `websocket.ts` can gate the UI. Mitigation: show a subtle "connecting..." indicator rather than hiding the entire section.
- **No stations configured** → Slot buttons show as empty/unconfigured. Mitigation: show slot number with "(empty)" label, disable the button, or show a "Configure stations" link.
- **Volume slider feels laggy on Pi Zero** → WebSocket round-trip adds latency. Mitigation: update the local `volume` store optimistically on input before the WebSocket confirmation arrives.
