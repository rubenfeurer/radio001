## Why

The homepage radio section currently shows 3 fixed slot buttons with no way to assign stations to them. Users have no discovery flow — there are 28k stations in `stations.json` but no UI to browse or search them. The volume control is a raw 0–100 range input with no clear labeling. Clicking an empty slot does nothing. This change replaces the static slot UI with an interactive experience: clicking a slot opens a searchable station picker, slots show playback state clearly, and volume is displayed as a percentage.

## What Changes

### Homepage (`+page.svelte`)
- Clicking a slot opens a new `/stations` page (passing the target slot as a query param, e.g. `/stations?slot=2`)
- Active (playing) slot shows a visual "playing" indicator and a play/pause toggle button
- Only one station can play at a time (already enforced by backend toggle logic)
- Volume slider labeled and displayed as 1–100% (was unlabeled 0–100)
- Audio output uses system default (no changes needed — mpg123 already uses ALSA default)

### New Stations Page (`frontend/src/routes/stations/+page.svelte`)
- Live search input at top — filters the station list client-side as user types
- Station list items show: **name**, **country**, **location**
- Selecting a station saves it to the target slot (via `POST /api/radio/stations/{slot}`) and navigates back
- If no `?slot=` param, page is still usable as a station browser (no slot assignment)

### Backend
- New route: `GET /api/radio/stations-library` — returns the full `stations.json` list for the frontend to search/filter client-side
- No changes to the 3-slot station management system

## Capabilities

### New Capabilities
- `station-search-page`: Users can search 28k stations by name, country, or location
- `slot-station-picker`: Clicking a slot on the homepage navigates to station search to assign a station to that slot
- `slot-playback-indicator`: Playing slot shows animated indicator and play/pause control

### Modified Capabilities
- `homepage-radio-controls`: Slot buttons navigate to station picker instead of toggling directly when clicked (playing slot still toggles on play/pause button click)
- `homepage-volume-display`: Volume shown as "42%" instead of raw number

## Impact

- `frontend/src/routes/+page.svelte`: Change slot click handler to navigate to `/stations?slot=N`; add play/pause button to active slot; fix volume display to show `%`
- `frontend/src/routes/stations/+page.svelte`: New page — live search + station list
- `backend/api/routes/radio.py` or new `library.py`: Add `GET /api/radio/stations-library` route serving `stations.json`
- `frontend/src/lib/types.ts`: No changes needed (RadioStation already has name, country, location)
- No changes to radio store, WebSocket, or 3-slot backend logic
