## Why

`radio.service` fails on every fresh Pi install because `install.sh` starts the Docker containers directly (`docker compose up -d`) and then immediately tries to start them again via `systemctl enable --now radio.service` — Docker Compose fails with "container name already in use", and `Restart=on-failure` with no burst limit creates an infinite restart loop.

## What Changes

- Remove the direct `docker compose up -d` call from `install.sh` (keep `docker compose pull` for image pre-caching); let `systemctl enable --now` be the sole lifecycle starter
- Add `StartLimitIntervalSec=300` and `StartLimitBurst=3` to the service definition to cap retries and prevent infinite restart loops on genuine failures

## Capabilities

### New Capabilities

_(none — bug fix only)_

### Modified Capabilities

- `pi-install`: install flow no longer starts containers directly; systemd is the sole container lifecycle manager
- `boot-behaviour`: service restart loop is now bounded (3 attempts per 5 minutes)

## Impact

- `scripts/install.sh`: remove ~2 lines (the `docker compose up -d` call and its echo)
- Embedded service file in `install.sh`: add `StartLimitIntervalSec` and `StartLimitBurst` directives
- Pi devices: will need a fresh install or manual service file update to pick up the fix
