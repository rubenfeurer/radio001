## Context

The homepage (`frontend/src/routes/+page.svelte`) already has a Radio card with 3 slot buttons, a volume slider, and a now-playing indicator. The radio store, WebSocket, and REST endpoints for slot management are all in place. There are 28,148 stations in `config/stations.json` — none are exposed to the frontend yet. The backend uses FastAPI with routers registered in `main.py`. The frontend uses SvelteKit with Tailwind CSS and `$lib/stores/radio.ts` for state.

## Goals / Non-Goals

**Goals:**
- Slot buttons on homepage navigate to `/stations?slot=N` to pick a station
- `/stations` page: live search input + flat list showing name, country, location
- Playing slot shows pulsing indicator and a separate play/pause toggle button
- Volume labeled as percentage (e.g. `42%`)
- New backend endpoint serving `stations.json` for client-side search

**Non-Goals:**
- Pagination, infinite scroll, or server-side filtering (client-side filter is sufficient for initial load)
- Editing station metadata (name, URL)
- Genre, bitrate, or language filtering
- Persisting the last selected station across browser sessions

## Decisions

### 1. Navigation: page vs. modal/drawer

**Decision:** Dedicated `/stations` page navigated to with `goto('/stations?slot=N')`.

**Rationale:** The user confirmed "use pages". A separate page avoids layout complexity, works consistently on mobile, and fits the existing app pattern (setup, status, settings are all separate pages). SvelteKit's `$page.url.searchParams` cleanly provides the `slot` param.

**Alternative considered:** Slide-in drawer overlay. Rejected per user preference.

### 2. Data fetching: full upfront load vs. lazy/paginated

**Decision:** Fetch all stations once on mount via `GET /api/radio/stations-library`, store in a local array, filter client-side on every keystroke.

**Rationale:** 28k stations is ~2–3 MB JSON. On a Pi on local WiFi this loads in under 1–2s. Client-side filtering with a simple `includes()` on name/country/location is instant. No server round-trips per search query. SvelteKit's `$derived` / reactive `$:` makes this trivial.

**Risk:** Initial load time on slow connections. Mitigation: show a loading skeleton while fetching; search input is disabled until data is ready.

**Alternative considered:** Server-side search endpoint with query param. Rejected — adds backend complexity and round-trip latency per keystroke; not needed for local use.

### 3. Station list rendering: full list vs. limited display

**Decision:** Display first 100 matching results. Show count ("Showing 100 of 4,231 results — refine your search").

**Rationale:** Rendering 28k DOM nodes is slow. With a search term, results drop quickly. Capping at 100 keeps the DOM lean and encourages users to type more specific queries. No pagination UI needed.

**Alternative considered:** Virtual scroll (e.g. svelte-virtual-list). Rejected — adds a dependency for a local-only app; capping at 100 is simpler and works fine.

### 4. Playing slot UI: overlay vs. separate button

**Decision:** The slot card shows the station name and a play/pause icon button in the bottom-right corner when that slot is playing. Clicking the card body navigates to station picker. Clicking the play/pause button calls `toggleStation(slot)`.

**Rationale:** Separating the two interactions (pick vs. toggle) avoids ambiguity. The card body as a navigation target is a familiar pattern. The play/pause button is clearly labeled with an icon.

**When slot is active (playing):** card gets a colored border + pulsing dot + play/pause button.
**When slot has a station but is not playing:** card shows station name, clicking navigates to picker.
**When slot is empty:** card shows "(empty)", clicking navigates to picker.

### 5. Backend library endpoint placement

**Decision:** Add `GET /radio/library` to the existing `backend/api/routes/radio.py` file (registered under `/radio` prefix → full path `/api/radio/library`).

**Rationale:** Keeps the new route alongside other radio control routes. No new file needed — `radio.py` already handles miscellaneous radio endpoints (status, volume, stop). The `stations.json` path is already known to the backend via `RadioManager` or can be read directly from `config/stations.json`.

**Response shape:**
```json
{ "stations": [ { "name": "...", "url": "...", "country": "...", "location": "..." }, ... ] }
```

**Alternative considered:** Separate `library.py` router. Rejected — adds a file and a router registration for a single endpoint.

### 6. Volume display

**Decision:** Change the volume label from `{localVolume}` to `{localVolume}%`. Keep slider range 0–100 (backend accepts 0–100). Label reads "Volume" next to the slider.

**Rationale:** The proposal said "1–100%", but the backend uses 0–100 internally. Keeping 0–100 range avoids a mapping bug. Displaying `%` suffix is purely cosmetic.

## Risks / Trade-offs

- **2–3 MB JSON load on Pi Zero:** First load may be slow over a congested network. Mitigation: loading state + disabled search input. Subsequent visits benefit from browser cache (no cache-busting needed).
- **`stations.json` path hardcoded in backend:** `config/stations.json` is already used by `StationManager`. Use the same path constant or env variable to avoid duplication.
- **Back navigation after slot pick:** After saving a station to a slot, `history.back()` or `goto('/')` returns the user to the homepage. Use `goto('/')` explicitly to avoid issues if the user landed on `/stations` directly.
