## 1. Multi-Stage Dockerfile (Frontend Baked In)

- [x] 1.1 Add Stage 1 to `docker/Dockerfile.backend`: `FROM node:20-slim AS frontend-builder`, copy `frontend/`, run `npm ci && npm run build`
- [x] 1.2 In the final Python stage, `COPY --from=frontend-builder /app/frontend/build /app/static`
- [x] 1.3 Mount `StaticFiles` in `backend/main.py` at `/` serving from `/app/static` (ensure API routes take priority)
- [ ] 1.4 Build image locally and confirm `http://localhost:8000` serves the SvelteKit UI without a host volume mount

## 2. Production Compose Rewrite

- [x] 2.1 Rewrite `compose/docker-compose.prod.yml`: replace `build: context: ..` with `image: ghcr.io/[owner]/radio001:latest`
- [x] 2.2 Remove the separate frontend nginx service and its volume mount of `../frontend/build`
- [x] 2.3 Add Watchtower service: `image: containrrr/watchtower`, `WATCHTOWER_SCHEDULE=0 0 3 * * *`, `WATCHTOWER_CLEANUP=true`, mount `/var/run/docker.sock`
- [x] 2.4 Ensure Watchtower has no `profiles:` key (always active)
- [x] 2.5 Add named volumes for `config` (`/opt/radio/config`) and `data` (`/opt/radio/data`) bind mounts

## 3. Systemd Service Update

- [x] 3.1 Update `config/systemd/radio-wifi.service` (or equivalent) `ExecStart` to `docker compose -f /opt/radio/docker-compose.yml up -d`
- [x] 3.2 Remove any `docker compose pull` pre-start step from the service file
- [x] 3.3 Confirm `Restart=on-failure` and `RestartSec=10s` are present in the service unit

## 4. Version Endpoint

- [x] 4.1 Add `GET /api/system/version` route to `backend/api/routes/system.py` returning `{"version": os.getenv("VERSION", "dev"), "image": "ghcr.io/[owner]/radio001"}`
- [x] 4.2 Register the route in the FastAPI app if not already wired through the router
- [x] 4.3 Add `ENV VERSION=dev` to `docker/Dockerfile.backend` (overridden at build time via `--build-arg VERSION`)
- [x] 4.4 Display version string in the Settings page (`frontend/src/routes/settings/+page.svelte`)

## 5. Install Script

- [x] 5.1 Rewrite `scripts/install.sh`: create `/opt/radio/config/` and `/opt/radio/data/` directories
- [x] 5.2 Embed `/opt/radio/docker-compose.yml` as a heredoc (referencing GHCR image, including Watchtower)
- [x] 5.3 Embed `/opt/radio/config/radio.conf` defaults as a heredoc (skip write if file already exists — idempotency)
- [x] 5.4 Embed `/etc/systemd/system/radio.service` as a heredoc
- [x] 5.5 Run `docker compose -f /opt/radio/docker-compose.yml pull && docker compose -f /opt/radio/docker-compose.yml up -d`
- [x] 5.6 Run `systemctl daemon-reload && systemctl enable --now radio.service`
- [x] 5.7 Verify script is idempotent: running a second time must not overwrite existing `radio.conf` or station data

## 6. Verification

- [ ] 6.1 Build and run the multi-stage image locally; confirm frontend loads at `http://localhost:8000` with no host mounts
- [ ] 6.2 Run install script against a clean Docker environment (or Pi) and confirm radio is reachable within 2 minutes
- [ ] 6.3 Run install script a second time and confirm `radio.conf` is unchanged and service restarts cleanly
- [ ] 6.4 Confirm `GET /api/system/version` returns `{"version": "dev", "image": "ghcr.io/[owner]/radio001"}` in local dev
