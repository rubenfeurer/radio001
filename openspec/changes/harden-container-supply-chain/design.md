# Design — harden-container-supply-chain

## Context

The production compose (`docker/compose.prod.yml` and the heredoc copy in `scripts/install.sh`) already declares every narrow grant the container needs — `cap_add: NET_ADMIN, NET_RAW`, `devices: /dev/net/tun, /dev/gpiochip0, /dev/snd`, `group_add: "986"`, host networking, D-Bus and PipeWire socket mounts — yet still sets `privileged: true` and mounts `/dev:/dev:rw`, which supersede all of them. `docs/deployment-and-updates.md` ("Required Host Devices") confirms the three device nodes were enumerated precisely so privileged could be removed.

Inside the image, `/etc/sudoers.d/radio` (Dockerfile.backend:61) grants passwordless sudo for `mv, cp, rm, chmod, mkdir, touch, reboot, shutdown, ip, nmcli, killall` with unrestricted arguments. A grep of `backend/` shows the only sudo callers are in `backend/core/wifi_manager.py`:

| Invocation | Lines |
|---|---|
| `sudo nmcli device/connection ...` (rescan, up/down, add, modify, set managed, disconnect, delete) | 193–195, 410, 426, 445, 459, 653, 665, 701, 712, 739, 745 |
| `sudo rm -f /etc/raspiwifi/host_mode` | 707 |
| `sudo mkdir -p /etc/raspiwifi` | 729 |
| `sudo touch /etc/raspiwifi/host_mode` | 731 |
| `sudo systemctl stop/mask/unmask/start dnsmasq` | 695–696, 766–769 |

`systemctl` is not in the current sudoers, so those calls already fail (all use `check=False`) — the review flags them as dead code (separate finding, not fixed here). `reboot` is invoked *without* sudo (`radio_manager.py:423`, `system.py:266`), so the `reboot`/`shutdown` sudoers entries have no callers.

Supply-chain gaps in `docker/Dockerfile.backend`: lgpio fetched via `curl http://abyz.me.uk/lg/lg.zip` (plain HTTP, no checksum, compiled as root); frontend stage copies only `package.json` and runs `npm install` (no `frontend/package-lock.json` exists in the repo at all); `node:26-slim` is tag-only while python is digest-pinned; `apt-get upgrade -y` runs at build time; watchtower is unpinned in `compose.prod.yml` but pinned `1.7.1` in `install.sh` (drift).

## Goals / Non-Goals

**Goals:**
- Production container runs without `privileged: true` and without `/dev:/dev:rw`, keeping audio, GPIO, and nmcli WiFi management working.
- In-container sudo restricted to the exact commands/argument patterns the backend uses.
- Every third-party build input pinned or integrity-checked: base images by digest, lgpio by SHA-256 over HTTPS, npm dependencies by committed lockfile with `npm ci`, watchtower by version in both compose sources.
- `compose.prod.yml` and the `install.sh` heredoc stay identical in their service definitions.

**Non-Goals:**
- Fixing the dead `sudo systemctl ... dnsmasq` hotspot path (review "Hotspot dnsmasq path is dead code" — separate change; we do not add `systemctl` to sudoers).
- Fixing the sudo-less `reboot` calls (pre-existing: they fail for the non-root `radio` user with or without privileged mode; dropping privileged does not regress them).
- Pinning `trivy-action@master` or other CI workflow refs (CI-side supply chain, separate change).
- Rootless container / removing sudo entirely.

## Decisions

### 1. Remove `privileged` + blanket `/dev`, keep existing narrow grants unchanged

The compose files already carry the sufficient grants (verified against the Required Host Devices table: `/dev/snd`, `/dev/gpiochip0`, `/dev/net/tun`). We delete only the two overriding lines (`privileged: true`, `- /dev:/dev:rw`) rather than redesigning the grant set. Alternative — `no-new-privileges` and cap-drop-all — rejected for this change: sudo requires setuid, and minimizing diff keeps the Pi verification meaningful.

### 2. Sudoers: whitelist exact binaries and argument patterns

Replace the single sudoers line with:

- `/usr/bin/nmcli` — unrestricted arguments. nmcli is invoked with many subcommand shapes (rescan, connection add/modify/up/down/delete, device set/disconnect); enumerating each pattern would be brittle, and nmcli does not offer shell escapes. Restricting to the binary is the meaningful boundary.
- `/usr/bin/rm -f /etc/raspiwifi/host_mode`, `/usr/bin/mkdir -p /etc/raspiwifi`, `/usr/bin/touch /etc/raspiwifi/host_mode` — exact argument matches for the host-mode marker (path from `HOST_MODE_FILE`, default `/etc/raspiwifi/host_mode`). Debian trixie is merged-/usr; keep the `/bin/...` aliases as well if sudo resolves the caller's PATH form (current file lists both — retain both spellings for the same three commands to avoid PATH-resolution surprises).
- Everything else (`cp`, `mv`, `chmod`, `killall`, `ip`, `reboot`, `shutdown`) removed — grep shows no sudo callers.

Trade-off: if `HOST_MODE_FILE` is ever pointed elsewhere, the sudoers args no longer match. Acceptable: the path is fixed in both compose files and the Dockerfile is the pairing artifact.

### 3. lgpio: HTTPS + pinned SHA-256, not vendoring

Change the fetch to `https://abyz.me.uk/lg/lg.zip`, record the SHA-256 of the current archive as a Dockerfile `ARG`/constant, and verify with `sha256sum -c` before extraction; the build fails on mismatch. Vendoring the zip in-repo was considered (strongest guarantee, survives upstream disappearing) and rejected for now: it adds a binary blob to the repo and the checksum gives equivalent integrity. If the HTTPS endpoint proves unavailable during implementation, fall back to vendoring — the spec requirement (integrity-verified source) permits either. Upstream is unversioned (`lg.zip` mutates in place), so an upstream update requires a deliberate checksum bump — that is the point.

### 4. Frontend determinism: commit lockfile, use `npm ci`

`frontend/package-lock.json` does not exist and must be generated (`npm install` in `frontend/`, commit the lockfile) before the Dockerfile can `COPY frontend/package.json frontend/package-lock.json ./` and run `npm ci`. `npm ci` fails if lockfile and manifest disagree, which is the desired CI behavior.

### 5. Pinning policy: digest for build-stage base images, version tag for runtime services

- `node:26-slim` → pin by digest (same policy as the python base). Build inputs should be immutable.
- watchtower → `containrrr/watchtower:1.7.1` in `compose.prod.yml`, matching `install.sh`. Version tag (not digest) because Watchtower is the component that would otherwise self-update and 1.7.1 is what the fleet already runs; a digest here is acceptable extra rigor but version parity across the two files is the requirement.
- Drop `apt-get upgrade -y`: blind upgrades make builds time-dependent; the digest-pinned base plus explicit package installs define the surface. Security updates arrive by bumping the base digest.

### 6. Keep the two compose sources synchronized by construction

`install.sh`'s heredoc and `docker/compose.prod.yml` must carry identical `radio-backend` and `watchtower` service definitions. No mechanism change here (still two copies); the spec delta makes divergence a requirement violation, and the tasks update both in the same commit.

## Risks / Trade-offs

- [Privileged mode was silently covering an unlisted device/cap (e.g. PipeWire needing another node, NetworkManager needing extra caps)] → Manual verification task on the Pi (test Pi via `:latest`) exercising audio playback, GPIO buttons/rotary, WiFi scan/connect and hotspot toggle before any `:stable` release; rollback is re-adding two lines.
- [lgpio upstream replaces `lg.zip` in place] → Build fails loudly on checksum mismatch; bump checksum deliberately after reviewing upstream diff, or vendor the zip.
- [`npm ci` surfaces a lockfile/manifest mismatch on first CI run] → Generate the lockfile with the same npm major version the `node:26-slim` image ships.
- [Sudoers argument-exact entries break if marker path changes] → Path is defined in one place per artifact (compose env + Dockerfile); documented pairing.
- [Watchtower auto-pulls a `:stable` built before Pi verification] → Existing release process already gates `:stable` on GitHub Release; this change rides that gate.

## Migration Plan

1. Land Dockerfile + compose + install.sh + lockfile changes on `develop` → `main`; `release.yml` pushes `:latest`.
2. Verify on test Pi with `:latest` (manual verification task): container healthy, audio, GPIO, nmcli, hotspot marker writes, no privileged.
3. Update `/opt/radio/docker-compose.yml` on the Pi via the documented scp+alpine-cp procedure (file is root-owned and not auto-synced).
4. Tag a release → `:stable`; Watchtower rolls out the hardened image fleet-wide. Rollback: restore `privileged: true` + `/dev:/dev:rw` in compose on-device and re-release prior image.

## Open Questions

- None blocking. The exact SHA-256 for `lg.zip` is captured at implementation time (download over HTTPS, record hash in the Dockerfile).
