# Tasks — harden-container-supply-chain

## 1. Frontend build determinism

- [x] 1.1 Generate `frontend/package-lock.json` (run `npm install` in `frontend/` with the same npm major version as `node:26-slim`) and commit it
- [x] 1.2 Update `docker/Dockerfile.backend` frontend stage: `COPY frontend/package.json frontend/package-lock.json ./` and replace `npm install` with `npm ci`

## 2. Dockerfile supply-chain pinning

- [x] 2.1 Pin `node:26-slim` by digest in `docker/Dockerfile.backend` (resolve current digest for linux/arm64+amd64 manifest list, `node:26-slim@sha256:...`)
- [x] 2.2 Remove `apt-get upgrade -y` from the apt `RUN` in `docker/Dockerfile.backend:21`
- [x] 2.3 Download `https://abyz.me.uk/lg/lg.zip`, record its SHA-256, and change the lgpio build step to fetch over HTTPS and verify the pinned checksum (`echo "<sha256>  /tmp/lg.zip" | sha256sum -c -`) before extraction; if HTTPS is unavailable, vendor the zip in the repo instead per design decision 3

## 3. Constrain sudoers

- [x] 3.1 Rewrite `/etc/sudoers.d/radio` generation in `docker/Dockerfile.backend:61`: allow `nmcli` (any args) plus exact-argument entries `rm -f /etc/raspiwifi/host_mode`, `mkdir -p /etc/raspiwifi`, `touch /etc/raspiwifi/host_mode` (both `/bin` and `/usr/bin` spellings); remove `cp`, `mv`, `chmod`, `killall`, `ip`, `reboot`, `shutdown`
- [x] 3.2 Re-grep `backend/` for `sudo` invocations and confirm every caller matches the new whitelist (only `backend/core/wifi_manager.py`; the unpermitted `sudo systemctl ... dnsmasq` calls are known dead code with `check=False` — leave as-is per design non-goals)

## 4. Drop privileged mode from compose sources

- [x] 4.1 In `docker/compose.prod.yml`: delete `privileged: true` and the `- /dev:/dev:rw` volume; keep `cap_add`, `devices`, `group_add`, and all other mounts unchanged; pin `containrrr/watchtower:1.7.1`
- [x] 4.2 Apply the identical edits to the compose heredoc in `scripts/install.sh` and diff the two service definitions to confirm they match
- [x] 4.3 Verify the `devices` list against the Required Host Devices table in `docs/deployment-and-updates.md` (`/dev/snd`, `/dev/gpiochip0`, `/dev/net/tun`)

## 5. Docs

- [x] 5.1 Update `docs/deployment-and-updates.md`: reword the Required Host Devices intro and any Security-section text that states the container runs `privileged: true`
- [x] 5.2 Update `CLAUDE.md` if it references privileged mode or the old sudoers scope (currently it does not — confirm)

## 6. Build and CI verification

- [ ] 6.1 Build the image locally (`docker compose -f docker/compose.dev.yml build` or `docker build -f docker/Dockerfile.backend .`) and confirm `npm ci`, checksum verification, and sudoers file creation succeed
- [ ] 6.2 Push to `develop`, confirm CI green; merge to `main` so `release.yml` publishes `:latest`

## 7. Manual Pi verification (required before release)

- [ ] 7.1 Copy the updated compose to the test Pi (scp + alpine-cp procedure from CLAUDE.md), pull `:latest`, and restart the stack
- [ ] 7.2 Verify on the Pi without privileged mode: container healthy (`/health`), audio playback + volume via PipeWire and `amixer -c Headphones`, GPIO buttons and rotary encoder respond (`/dev/gpiochip0`), WiFi scan/connect and hotspot mode toggle via `sudo nmcli` work, and host-mode marker writes to `/etc/raspiwifi` succeed
- [ ] 7.3 Confirm denied sudo commands: `docker exec radio-backend-prod sudo -l` lists only the whitelisted entries; `sudo cp /etc/passwd /tmp/x` is refused
- [ ] 7.4 Tag a release to publish `:stable` and confirm Watchtower (pinned 1.7.1) rolls it out overnight without regression
