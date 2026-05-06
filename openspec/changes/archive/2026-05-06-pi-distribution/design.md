## Context

The production compose currently uses `build: context: ..` for the backend (builds locally on the Pi) and mounts `../frontend/build` for the frontend (requires the full source tree and a prior `npm run build`). The Watchtower service exists in the compose but is under a profile and configured for automatic polling — if the image is local, Watchtower has nothing to pull. The systemd service does `docker compose pull` on start, but again the image is local so this is a no-op.

The `release-pipeline` change (dependency) publishes a pre-built ARM64 image to GHCR. This change wires up the device side: a minimal install footprint, a compose file that pulls from GHCR, and Watchtower on a schedule.

## Goals / Non-Goals

**Goals:**
- Install experience: download one script, run it, radio works within 2 minutes
- No source code, git, Node.js, or build tools on the Pi
- Nightly auto-update at 3am with zero user interaction
- Self-contained Docker image (frontend baked in, not mounted from host)
- Version visible in the Settings page of the webapp

**Non-Goals:**
- Rollback on failed update (Watchtower does not support this natively; manual recovery via tag)
- Interactive setup wizard (good defaults in `radio.conf` suffice for test group)
- Fleet management dashboard
- In-app "update now" button (auto-update makes this unnecessary for test group)

## Decisions

### 1. Frontend baked into the backend image

**Decision**: Build the SvelteKit frontend in a Docker multi-stage build and serve the static files from within the backend image via a bundled nginx or directly from uvicorn's static file mounting.

**Rationale**: The current setup mounts `../frontend/build` from the host, which requires the source tree. With the GHCR-pulled image, no source is present. The frontend is small (~500KB gzipped) and changes infrequently — baking it in is the simplest approach. A multi-stage Dockerfile builds the frontend with Node, copies the output to the final Python image.

**Alternative considered**: Separate nginx container pulling from GHCR with pre-built frontend. Rejected because it requires a second image, doubling the release complexity.

**Alternative considered**: Serve frontend from uvicorn's `StaticFiles`. Viable, but requires nginx for production routing (WebSocket, gzip, caching). Decision: add a minimal nginx inside the same container via supervisord, or use a sidecar only if complexity justifies it. For simplicity: multi-stage build → static files served by nginx in the same image via a process manager (supervisord), or separate nginx container sourced from the same GHCR image.

*Simplest viable path*: Multi-stage build in `Dockerfile.backend`: Stage 1 builds frontend with Node 20, Stage 2 is the Python image. Frontend static files are COPY-ed into `/app/static/`. FastAPI serves them via `StaticFiles` mount at `/`. This avoids supervisord complexity entirely.

### 2. Watchtower on cron schedule, not HTTP API

**Decision**: Run Watchtower with `WATCHTOWER_SCHEDULE=0 0 3 * * *` (3am daily) and `WATCHTOWER_CLEANUP=true`. Watchtower is always-on (no profile).

**Rationale**: Non-technical users will never trigger an HTTP API call. Scheduled polling is zero-touch. 3am minimises disruption (radio unlikely to be playing). `WATCHTOWER_CLEANUP` removes old images to preserve SD card space.

**Alternative considered**: Watchtower with HTTP API trigger from webapp. Rejected for the test group — adds complexity (webapp endpoint, reconnect handling, user education) without benefit when auto-update at night is sufficient.

### 3. Install script: minimal footprint, no git

**Decision**: The install script downloads only three files to the Pi:
- `/opt/radio/docker-compose.yml` (embedded in the script as a heredoc)
- `/opt/radio/config/radio.conf` (default config, embedded)
- `/etc/systemd/system/radio.service` (embedded)

Then runs `docker compose pull && docker compose up -d && systemctl enable radio`.

No git clone. No npm. No build tools. Docker is the only prerequisite (Pi OS ships with it or it can be installed in 1 line).

**Rationale**: Minimises attack surface, SD card writes, and things that can go wrong. The entire install state lives in `/opt/radio/` and is easy to inspect or remove.

### 4. VERSION endpoint

**Decision**: Add `GET /system/version` that returns `{"version": "<label>", "image": "ghcr.io/[owner]/radio001"}`. The version is read from the `VERSION` env var (set in the compose file from the Docker label). Settings page displays it as a static string.

**Rationale**: Useful for debugging ("which version is the user on?") and as a foundation for a future update-check feature. Zero risk — read-only endpoint.

## Risks / Trade-offs

- **Watchtower pulls bad image at 3am → radio broken** → Mitigation: Trivy gate in CI means no HIGH/CRITICAL CVEs ship. If a bad build slips through, recovery requires SSH access or reflashing. Acceptable for a test group. Future: add a healthcheck wrapper that reverts on failure.
- **Frontend baked in increases image size** → Node build artifacts are not included in the final image (multi-stage). Image size increase is ~50–100MB. Acceptable on Pi with ≥8GB SD card.
- **`radio.conf` survives updates** → Config is in `/opt/radio/config/` (bind-mounted volume), not in the image. Updates never touch it. ✓
- **User data survives updates** → Station data and state in `/opt/radio/data/` (bind-mounted volume). ✓

## Migration Plan

1. Update `docker/Dockerfile.backend` to multi-stage (Node frontend build + Python backend)
2. Rewrite `compose/docker-compose.prod.yml`: remove `build:`, set `image: ghcr.io/[owner]/radio001:latest`, remove frontend nginx service, add Watchtower with schedule
3. Add `/system/version` endpoint to backend
4. Add version display to Settings page
5. Rewrite `scripts/install.sh`
6. Test install on a clean Pi OS image
7. Share install script URL with test group via GitHub Release
