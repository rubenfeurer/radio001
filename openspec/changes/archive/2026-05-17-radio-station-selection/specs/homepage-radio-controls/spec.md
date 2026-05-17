## MODIFIED Requirements

### Requirement: API Routing for Radio Controls
The system SHALL expose all radio and system HTTP endpoints under the `/api` path prefix so that production frontend requests (which include `/api` in the path) are correctly routed to the FastAPI handlers.

#### Scenario: Radio status endpoint reachable in production
- **WHEN** the frontend calls `/api/radio/status` in production
- **THEN** FastAPI SHALL route the request to the radio status handler
- **AND** SHALL return the current playback status as JSON
- **AND** SHALL NOT return the SPA `index.html` or a 404 response

#### Scenario: Station slots load on homepage in production
- **WHEN** the homepage loads and `loadStations()` is called
- **THEN** the frontend SHALL receive the 3 configured station slots from the backend
- **AND** the station slot buttons SHALL display station names (or "(empty)") rather than remaining blank

#### Scenario: System status endpoint reachable in production
- **WHEN** the frontend calls `/api/system/status` in production
- **THEN** FastAPI SHALL route the request to the system status handler
- **AND** SHALL return the system status as JSON

#### Scenario: Dev proxy remains compatible
- **WHEN** running the frontend dev server (Vite)
- **THEN** requests to `/api/*` SHALL be forwarded to the backend without stripping the `/api` prefix
- **AND** the backend SHALL respond correctly because routes are registered at `/api/...`
