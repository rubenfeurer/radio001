## Why

With the release pipeline publishing images to GHCR, the missing piece is getting those images onto user devices without requiring technical knowledge. Currently, installation requires git, Node.js, Docker build tools, and manual systemd setup — far beyond a non-technical user. This change delivers a one-command install experience and nightly auto-updates so the ~20 test users never need to touch a terminal again.

## What Changes

- Rewrite `scripts/install.sh` as a self-contained Pi installer: creates `/opt/radio/`, writes a minimal `docker-compose.yml` pointing to the GHCR image (no `build:`), copies default `radio.conf`, and installs the systemd service — no git clone or build tools required
- Rewrite `compose/docker-compose.prod.yml` to pull the pre-built GHCR image instead of building locally; bake the frontend static build into the backend image so no separate nginx + build mount is needed
- Enable Watchtower in the production compose on a nightly cron schedule (3am) so devices update automatically without user action
- Add a `/api/system/version` endpoint so the webapp can display the running image version in the Settings page

## Capabilities

### New Capabilities
- `pi-install`: one-command install script for non-technical users (no source code, no build tools on Pi)
- `auto-update`: nightly Watchtower-based auto-update pulling from GHCR

### Modified Capabilities
- `boot-behaviour`: systemd service now references the GHCR-based compose file; no local build on start

## Impact

- Rewritten: `scripts/install.sh`
- Rewritten: `compose/docker-compose.prod.yml` (remove `build:`, add Watchtower with schedule, fix frontend to be baked into image)
- Modified: `docker/Dockerfile.backend` — copy and build frontend static files so it's self-contained
- New: `backend/api/routes/system.py` — add `/system/version` endpoint
- New: Settings page version display (frontend, minor)
- Modified: `config/systemd/radio-wifi.service` — point to new compose, remove pull-on-start (Watchtower handles updates)
