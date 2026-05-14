## Context

The frontend dev environment uses Vite's proxy to forward `/api/*` requests to the FastAPI backend, stripping the `/api` prefix before forwarding (e.g., `/api/radio/status` → `http://localhost:8000/radio/status`). In production, no such proxy exists — the frontend is served as static files by FastAPI itself, and browser requests to `/api/radio/status` hit FastAPI directly. Because FastAPI has no `/api`-prefixed routes, the static file handler catches these requests and either returns the SPA's `index.html` (for unknown paths with `html=True`) or a 404 — not a JSON API response.

Additionally, `config/stations.json` (the radio station library) is not copied into the Docker image. The backend expects it at `/app/assets/stations.json`, so the library endpoint always returns 404.

## Goals / Non-Goals

**Goals:**
- Make all frontend API calls work in production without changing any frontend code
- Make the station library available in the Docker image
- Fix all four observed symptoms: empty slots, broken station picker, failed WiFi scan, 404 flash on load

**Non-Goals:**
- Changing the Vite dev proxy (dev environment works correctly today)
- Adding authentication or rate limiting to API routes
- Restructuring the station library format or contents

## Decisions

**Add `/api` prefix to all HTTP routers in `backend/main.py`.**
The frontend already calls every endpoint with `/api/...`. The fix is to match the backend route registration to what the frontend expects. This is the minimal change — no frontend modifications needed.

Alternative considered: remove `/api` from all frontend fetch calls. Rejected — affects dozens of call sites across multiple store files and components; more error-prone and doesn't fix the underlying mismatch.

Alternative considered: add an nginx reverse proxy in the Docker image to rewrite `/api` → `/`. Rejected — adds operational complexity for a simple path prefix fix.

**Copy `config/stations.json` to `backend/assets/stations.json` and include in Docker image.**
The `config/` directory is mounted as a volume in production (`/opt/radio/config:/app/config:ro`) and is not baked into the image. The `assets/` directory is inside the image. Placing the stations library under `backend/assets/` means it's always present without requiring host filesystem configuration.

Alternative considered: mount `config/stations.json` at `/app/assets/stations.json` via compose volumes. Rejected — the stations.json is a distributor asset, not user config. It should ship with the image.

**No changes to `_LIBRARY_FILE` default path.**
The default is already `/app/assets/stations.json` and the `LIBRARY_FILE` env var allows override. We just need to ensure the file exists at that path in the image.

## Risks / Trade-offs

- **Existing Pi installs**: The running Pi (radio-d) will auto-update via Watchtower when the new image is published. The API prefix change is non-breaking from the Pi's perspective — no config changes needed.
- **`/api` prefix conflicts with any existing `/api` routes**: Check that no routes are already registered under `/api` in `main.py` before adding prefix. Static files are mounted last, so they won't shadow the new prefixed routes.
- **stations.json size in image**: The file is ~7MB (168k lines). This increases the Docker image size by ~7MB. Acceptable.
- **Dev environment after this change**: The Vite proxy rewrites `/api/...` → `/...` and forwards to `localhost:8000`. After this change, `localhost:8000` will have routes at `/api/...` — so the proxy rewrite is now wrong for dev. Fix: update Vite proxy to forward to `localhost:8000/api/...` (remove the rewrite, or change target). This must be done together with the backend change.

## Migration Plan

1. Update `backend/main.py`: add `prefix="/api"` to all `include_router` calls (system, stations, radio, wifi). WebSocket router stays at `/ws`.
2. Update `frontend/vite.config.ts`: change proxy so `/api` requests forward to `localhost:8000/api/...` (either remove `rewrite` or update target path).
3. Copy `config/stations.json` → `backend/assets/stations.json` and ensure Dockerfile COPY includes `backend/assets/`.
4. Run backend + frontend tests. Start dev server and verify: radio slots load, station picker works, WiFi scan works, no 404 on load.
5. Commit and push to develop; merge to main to trigger image build; Watchtower picks up new image on Pi.

**Rollback**: Revert the `include_router` prefix change in `main.py` and the Vite proxy change. No data migration needed.
