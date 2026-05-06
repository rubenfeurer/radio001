# Deployment & Update Architecture

## Overview

Radio001 runs as a single Docker container on a Raspberry Pi. The container bundles the FastAPI backend **and** the compiled SvelteKit frontend — no separate web server or host build tools are needed. Updates happen automatically every night via Watchtower.

```
┌─────────────────────────────────────────────────────────┐
│                  GitHub Actions (CI)                    │
│                                                         │
│  push to main ──► build ARM64 image ──► push to GHCR   │
│                   (multi-stage Docker)    :latest tag   │
└──────────────────────────────┬──────────────────────────┘
                               │ ghcr.io/rubenfeurer/radio001:latest
                               │
┌──────────────────────────────▼──────────────────────────┐
│                 Raspberry Pi                            │
│                                                         │
│  systemd radio.service                                  │
│    └─► docker compose up -d                             │
│          ├─► radio-backend  (port 8000)                 │
│          │     ├─ FastAPI API    /system, /radio, /wifi  │
│          │     └─ StaticFiles   /  (SvelteKit UI)       │
│          └─► watchtower                                 │
│                └─ pulls :latest nightly @ 03:00         │
└─────────────────────────────────────────────────────────┘
```

---

## Docker Image — Multi-Stage Build

`docker/Dockerfile.backend` uses two stages so the final image contains no Node.js toolchain:

```
Stage 1 — frontend-builder (node:20-slim)
  COPY frontend/
  RUN npm ci && npm run build
  → /frontend/build/  (static HTML/CSS/JS)

Stage 2 — runtime (python:3.13-slim)
  COPY --from=frontend-builder /frontend/build /app/static
  COPY backend/ .
  RUN pip install -r requirements.lock
  → FastAPI serves /app/static via StaticFiles at "/"
```

API routes (registered before the StaticFiles mount) always take priority. The UI is served as a catch-all SPA fallback (`html=True`).

The `VERSION` build-arg is passed by CI and baked in as `ENV VERSION=<tag>`. It is exposed at `GET /system/version`.

---

## Release Pipeline

| Trigger | What happens |
|---------|-------------|
| Push to `main` | CI builds ARM64 image, pushes `:latest` to GHCR, scans with Trivy |
| Git tag `v*.*.*` | Same build, also pushes `:vX.Y.Z` semver tag |

The pipeline (`release.yml`) fails if Trivy finds unfixed HIGH or CRITICAL CVEs, blocking the release before `:latest` is updated.

---

## Directory Layout on Pi

```
/opt/radio/
├── docker-compose.yml    # Written by install.sh; references GHCR image
├── config/
│   └── radio.conf        # User-editable config (never overwritten by updates)
└── data/                 # Station data, radio state (persisted across updates)

/etc/systemd/system/
└── radio.service         # Starts docker compose on boot
```

Both `/opt/radio/config` and `/opt/radio/data` are bind-mounted into the container, so they survive image updates.

---

## Installation (Fresh Pi)

Requirements: Raspberry Pi OS (64-bit), Docker installed, internet connection.

```bash
curl -fsSL https://raw.githubusercontent.com/rubenfeurer/radio001/main/scripts/install.sh | sudo bash
```

The script (`scripts/install.sh`) is fully self-contained — no git clone or Node.js required on the Pi. It:

1. Creates `/opt/radio/config/` and `/opt/radio/data/`
2. Writes `/opt/radio/docker-compose.yml` (references GHCR image + Watchtower)
3. Writes `/opt/radio/config/radio.conf` with safe defaults (skipped if file already exists)
4. Writes `/etc/systemd/system/radio.service`
5. Runs `docker compose pull && docker compose up -d`
6. Runs `systemctl daemon-reload && systemctl enable --now radio.service`

The script is **idempotent** — running it again preserves `radio.conf` and all station data.

---

## Automatic Updates (Watchtower)

Watchtower runs alongside the radio container and checks GHCR for a newer `:latest` image every night at **03:00**.

```yaml
# In docker-compose.yml on the Pi:
watchtower:
  image: containrrr/watchtower
  environment:
    - WATCHTOWER_SCHEDULE=0 0 3 * * *   # cron: daily at 03:00
    - WATCHTOWER_CLEANUP=true            # remove old images after update
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
```

When a new image is available:
1. Watchtower pulls the new image
2. Stops and restarts the radio container
3. Removes the old image to free SD card space
4. Config and data survive (bind-mounted volumes)

When no new image is available, nothing happens and the radio keeps playing.

---

## Checking the Running Version

```bash
# From the Pi or any device on the network:
curl http://radio.local/system/version
# → {"version": "v1.2.3", "image": "ghcr.io/rubenfeurer/radio001"}
```

The version is also displayed on the Settings page of the UI.

---

## Manual Operations

```bash
# Restart the radio service
sudo systemctl restart radio

# View logs
sudo journalctl -u radio -f

# Force an immediate update check
sudo docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower --run-once radio-backend-prod

# Edit config (takes effect after restart)
sudo nano /opt/radio/config/radio.conf
sudo systemctl restart radio
```

---

## Required Host Devices

The container declares these devices explicitly so audio and hardware access survive if `privileged: true` is ever removed:

| Device | Purpose |
|--------|---------|
| `/dev/snd` | ALSA audio — all sound card nodes (`controlC0`, `pcmC0D0p`, etc.) |
| `/dev/gpiochip0` | GPIO — buttons and rotary encoder via lgpio |
| `/dev/net/tun` | TUN/TAP — required by NetworkManager for VPN-style interface handling |

`/dev/snd` is mapped at the directory level to cover all ALSA nodes regardless of which audio HAT or USB adapter is attached.

## Security

- The release pipeline blocks on any unfixed HIGH or CRITICAL CVE (Trivy scan with `exit-code: 1`)
- Dependencies are pinned with hashes in `backend/requirements.lock`; CI verifies the lock file is in sync with `requirements.in` before building
- The radio container runs as a non-root `radio` user inside the image
