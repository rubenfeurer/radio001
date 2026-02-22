# Tasks: Radio Homepage and Stations Page

## Backend

- [x] Add `LIBRARY_FILE = Path("../config/stations.json")` (or equivalent resolved path) to `Config` in `backend/main.py`
- [x] Add `GET /library` route to `backend/api/routes/radio.py` that reads `config/stations.json` and returns `{ "stations": [...] }` — stream or load the file, return as JSON

## Frontend — Stations Page

- [x] Create `frontend/src/routes/stations/+page.svelte` with:
  - Read `?slot` query param from `$page.url.searchParams`
  - On mount: fetch `GET /api/radio/library`, store result in local `allStations` array; set `loading = false`
  - Reactive filter: `$: filtered = allStations.filter(s => query matches s.name, s.country, s.location).slice(0, 100)`
  - Search input (autofocused, disabled while loading) bound to `query`
  - Result count line: "Showing N of M" (or "No results")
  - Station list: each item shows name (bold), country, location — tappable row
  - On station select: `POST /api/radio/stations/{slot}` with station data, then `goto('/')`
  - If no `?slot` param: show list in browse-only mode (no save action)
  - Back button/link to `/`

## Frontend — Homepage Slot Cards

- [x] Slot card body taps play/stop the slot; settings gear icon navigates to `/stations?slot=N`
- [x] Stop button (large, mobile-friendly) shown on right when slot is playing
- [x] Settings gear icon always visible on right of each card
- [x] Active slot card: colored border + pulsing dot indicator
- [x] Slots displayed as full-width stacked cards (vertical flex, not 3-column grid)
- [x] Volume label shows `{localVolume}%`

## Backend

- [x] `GET /radio/library` added to `radio.py`; reads `/app/assets/stations.json` (baked into Docker image)
- [x] `stations.json` copied into Docker image at `/app/assets/stations.json` via Dockerfile
- [x] Removed unused `LIBRARY_FILE` from `Config` in `main.py`

## Stations Page — Refinements

- [x] Auto-play station after saving to slot (`POST /api/radio/stations/{slot}/play`)
- [x] Search filters by name, country, and location

## Verification

- [x] Tapping slot card body plays/stops that slot
- [x] Tapping gear icon on slot card navigates to station picker
- [x] Stop button stops playback without navigating
- [x] `/stations` page loads, live-filters by name, country, location
- [x] Selecting a station saves it to the slot, auto-plays it, and returns to homepage
- [x] Volume slider shows `%` suffix
- [x] `GET /api/radio/library` returns station list from Docker image asset
- [x] Audio output uses Pi's default ALSA device (mpg123 default, no config change)
