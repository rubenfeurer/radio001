## Why

The current homepage only shows WiFi status and navigation buttons, but users need quick access to radio controls without navigating to a separate page. The radio backend is fully functional with 3-slot station management and volume control, but there's no convenient way to control it from the main dashboard. Adding radio controls to the homepage creates a unified dashboard experience for both WiFi and radio management.

## What Changes

- Add radio station display and control section to the homepage dashboard
- Integrate radio state management (stations, volume, playback status) into the main page
- Add volume control slider with visual feedback
- Display current playing station and playback status
- Add 3-slot station quick-access buttons for instant station switching
- Include play/pause/stop controls for current radio playback
- Maintain responsive mobile-optimized design consistent with existing UI

## Capabilities

### New Capabilities
- `homepage-radio-display`: Homepage shows current radio status, playing station, and volume level
- `homepage-radio-controls`: Users can control radio playback, volume, and station switching directly from homepage
- `homepage-station-slots`: Quick access buttons for all 3 station slots with visual indication of configured vs empty slots

### Modified Capabilities
- `homepage-dashboard`: Enhanced from WiFi-only to unified WiFi + Radio dashboard experience

## Impact

- `frontend/src/routes/+page.svelte`: Add radio control section below WiFi status card
- `frontend/src/lib/stores/radio.ts`: Import and integrate existing radio store functionality
- `frontend/src/lib/stores/websocket.ts`: Ensure radio WebSocket updates work on homepage
- `frontend/src/lib/components/`: May need shared radio control components
- User experience: Homepage becomes primary control interface instead of just navigation hub
- Mobile usability: Quick radio access without page navigation