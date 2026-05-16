# Radio Pi — Claude Code Instructions

## Project Overview

Internet radio player running on a Raspberry Pi inside a Docker container. FastAPI backend + SvelteKit frontend (baked into the same image). Physical hardware controls (GPIO buttons, rotary encoder) via lgpio. Audio via PipeWire → mpg123.

## Architecture

### API
- All HTTP routes: `/api/system`, `/api/radio`, `/api/radio/stations`, `/api/wifi`
- WebSocket: `/ws` (no prefix)
- Health check: `/health` (no prefix — used by Docker healthcheck)
- Frontend calls `/api/...` always. In dev, Vite proxies it. In prod, FastAPI handles it directly.

### Key file locations
- Station library: `backend/assets/stations.json` (baked into image via `COPY backend/ .`)
- Config (Pi): `/opt/radio/config/radio.conf`
- Data (Pi): `/opt/radio/data/`
- Compose (Pi): `/opt/radio/docker-compose.yml` (written by install.sh, do not edit manually)

### Production image
`ghcr.io/rubenfeurer/radio001:latest` — built by `release.yml` on push to `main`. Frontend static files served by FastAPI `StaticFiles`. No nginx, no separate frontend service.

### Audio stack
- mpg123 routes through host PipeWire (`-o pulse`) via socket at `/run/user/1000/pulse/native`
- Volume controlled via `pactl set-sink-volume @DEFAULT_SINK@`
- Fallback: direct ALSA (`hw:Headphones`) if PipeWire socket absent — uses `amixer -c Headphones sset PCM`
- ALSA card name `Headphones` (not index) — index changes across reboots
- `AudioPlayer` logs which backend is active at startup

### GPIO / hardware
- lgpio built from source (Joan's lg C library: `http://abyz.me.uk/lg/lg.zip`) — not in Debian trixie apt
- GPIO group GID on this Pi: **986** (confirmed via `getent group gpio`)
- Container group_add: `["986"]`; Dockerfile: `groupadd -g 986 gpio`

## Development

### Running locally (macOS)
```bash
docker compose -f docker/compose.dev.yml up
```
- `network_mode: host` does NOT work on macOS Docker Desktop — use explicit port mapping `127.0.0.1:8000:8000`
- Vite proxy targets `http://127.0.0.1:8000` (not `localhost` — avoids IPv6 resolution)
- WebSocket proxy needs `changeOrigin: true`
- `NODE_ENV=development` enables mock mode for GPIO/WiFi (required on Mac)

### Python dependencies
`backend/requirements.lock` uses `--require-hashes`. After any dependency change:
```bash
cd backend && pip-compile --generate-hashes requirements.in -o requirements.lock
```
CI fails if lock file is out of sync.

### Branches
- `develop` — active development, runs quick CI (lint, type check)
- `main` — production, triggers ARM64 image build and push to GHCR

## Pi Deployment

### SSH
```bash
ssh radio-d          # uses ~/.ssh/config: HostName radio-d.local, User radio-d
```
Key: `~/.ssh/id_ed25519_radio-d`

### First install
```bash
curl -fsSL https://raw.githubusercontent.com/rubenfeurer/radio001/main/scripts/install.sh | sudo bash
```
Writes compose to `/opt/radio/`, installs `radio.service` systemd unit, starts container.

### Update compose file on Pi (no sudo)
Since `/opt/radio/docker-compose.yml` is owned by root, use docker to write it:
```bash
scp docker/compose.prod.yml radio-d:/tmp/docker-compose.yml
ssh radio-d "docker run --rm -v /opt/radio:/opt/radio -v /tmp:/tmp alpine cp /tmp/docker-compose.yml /opt/radio/docker-compose.yml"
```

### Pull new image
```bash
ssh radio-d "docker compose -f /opt/radio/docker-compose.yml pull && docker compose -f /opt/radio/docker-compose.yml up -d"
```

### Useful diagnostics
```bash
ssh radio-d "docker logs radio-backend-prod --tail 50"
ssh radio-d "docker exec radio-backend-prod python3 -c 'import lgpio; print(\"ok\")'"
ssh radio-d "docker exec radio-backend-prod amixer -c Headphones sset PCM 70%"
```

### Watchtower
Auto-pulls `:latest` nightly at 03:00. Requires `DOCKER_API_VERSION=1.40` (Docker Engine 29.x incompatibility with default watchtower API version).

## Security & Dependabot

### Setup (already enabled)
- **Dependabot alerts**: enabled — shows vulnerable dependencies in the Security tab
- **Automated security fixes**: enabled — Dependabot opens PRs to patch vulnerable deps
- **Dependabot config**: `.github/dependabot.yml` — weekly updates for pip (`/backend`) and docker (`/docker`); major versions ignored

### Handling Dependabot PRs
1. Check CI passes on the PR
2. For **security fixes**: merge promptly after CI passes — no need to wait for a release cycle
3. For **version bumps**: review changelog for breaking changes, then merge if CI is green
4. After merging a pip update: regenerate `requirements.lock` if Dependabot didn't already do it

### CodeQL / code scanning alerts
- Alerts appear at `github.com/rubenfeurer/radio001/security/code-scanning`
- All GitHub Actions workflows must have explicit `permissions` blocks (CodeQL alert #55 pattern)
  - Read-only workflows: `permissions: contents: read`
  - Release workflow (pushes to GHCR): `permissions: contents: read` + `packages: write`

### Vulnerability triage
- **Critical/High**: fix immediately, create hotfix PR directly to `main`
- **Moderate**: fix in next development cycle via `develop` → `main`
- **Low**: batch with regular maintenance

## OpenSpec Workflow

Changes are tracked in `openspec/changes/<name>/`. Use `/opsx:` skills:
- `/opsx:ff <name>` — create all artifacts fast (proposal → design → specs → tasks)
- `/opsx:apply <name>` — implement tasks
- `/opsx:explore <name>` — think through a problem before starting
- `/opsx:archive <name>` — archive after all tasks complete

Active changes: `openspec/changes/` — archived: `openspec/changes/archive/`
