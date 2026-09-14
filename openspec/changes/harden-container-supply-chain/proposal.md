# Harden Container Supply Chain

## Why

The production container runs `privileged: true` with a blanket `/dev:/dev:rw` mount and grants the `radio` user unrestricted passwordless sudo for `cp/mv/rm/chmod/mkdir/touch` — one injection bug or poisoned dependency gives any LAN/hotspot client host root (project review 2026-09, Critical item 4). The build also pulls lgpio over plain HTTP with no checksum, runs a non-deterministic `npm install` with no lockfile, and pins images inconsistently (Supply chain, High).

## What Changes

- Drop `privileged: true` and the `/dev:/dev:rw` mount from `docker/compose.prod.yml` and the compose heredoc in `scripts/install.sh`. The existing narrow grants remain: `cap_add: NET_ADMIN, NET_RAW`, `devices: /dev/gpiochip0, /dev/snd, /dev/net/tun`, `group_add: "986"` — matching the Required Host Devices table in `docs/deployment-and-updates.md`.
- Constrain the sudoers file in `docker/Dockerfile.backend:61` to only the commands the backend actually invokes via sudo (all in `backend/core/wifi_manager.py`): `nmcli`, and `rm`/`mkdir`/`touch` restricted to the `/etc/raspiwifi` host-mode marker paths. Remove `cp`, `mv`, `chmod`, `killall`, `ip`, `reboot`, `shutdown` (no sudo callers exist).
- Pin the lgpio download (`Dockerfile.backend:79`): switch to HTTPS and verify a pinned SHA-256 before extraction; build fails on mismatch.
- Deterministic frontend build: commit `frontend/package-lock.json` (currently missing), copy it in the frontend build stage, and replace `npm install` with `npm ci`.
- Consistent image pinning: pin `node:26-slim` by digest (python already is), pin watchtower to `containrrr/watchtower:1.7.1` in `docker/compose.prod.yml` (already pinned in `install.sh`), and remove build-time `apt-get upgrade -y` from `Dockerfile.backend:21`.

Not breaking for users; the container must still provide audio, GPIO, and nmcli-based WiFi management without privileged mode (verified manually on the Pi).

## Capabilities

### New Capabilities

- `container-least-privilege`: The production container runs without privileged mode, with only enumerated device/capability/group grants, and in-container sudo is restricted to an explicit whitelist of the commands the backend actually needs.

### Modified Capabilities

- `dockerfile-accuracy`: Add supply-chain integrity requirements — pinned base images, checksum-verified third-party downloads (lgpio), lockfile-driven deterministic frontend build, no blind build-time `apt-get upgrade`.
- `pi-install`: The compose file written by `install.sh` must not use `privileged: true` or a blanket `/dev` mount, and must stay in sync with `docker/compose.prod.yml`.
- `auto-update`: The Watchtower image must be version-pinned identically in both compose sources.

## Impact

- `docker/compose.prod.yml` — remove `privileged`, remove `/dev:/dev:rw`, pin watchtower
- `scripts/install.sh` — same changes in the compose heredoc
- `docker/Dockerfile.backend` — sudoers whitelist, lgpio HTTPS + SHA-256, `npm ci` + lockfile COPY, node digest pin, drop `apt-get upgrade -y`
- `frontend/package-lock.json` — new committed file
- `docs/deployment-and-updates.md` — Security/devices sections reference `privileged: true`; update wording after removal
- Runtime risk: if a needed device or capability was silently covered by privileged mode, WiFi/audio/GPIO could regress — mitigated by manual verification on the Pi before release
