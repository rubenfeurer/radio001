# Design — Fix Installer and Hotspot

## Context

Three intertwined problems, all rooted in `scripts/install.sh` and the hotspot path:

1. **Dead dnsmasq code.** `wifi_manager.py:694-697` and `:764-774` shell out to `sudo systemctl {unmask,start,stop,mask} dnsmasq` from inside the container. The image has no `systemctl`, sudoers does not allow it, and the container has no host-systemd access — so the calls always fail (they run with `check=False`, so failure is silently logged). Meanwhile `install.sh:216-248` installs dnsmasq on the host, writes `/etc/dnsmasq.d/radio-hotspot.conf`, masks the service, and rewrites `/etc/systemd/resolved.conf` (`DNSStubListener=no` + restart of systemd-resolved) purely to serve that path. Net effect: `radio.local` never resolves in hotspot mode, but the installer still mutates host DNS config.
2. **Installer papercuts.** The compose file is an embedded heredoc that has already drifted from `docker/compose.prod.yml` (Watchtower `containrrr/watchtower:1.7.1` in install.sh vs unpinned in compose.prod.yml). The data dir gets `chmod 777`. The final message claims `http://radio.local` although nothing listens on :80 (app is on :8000). `set -euo pipefail` means a mid-script failure (e.g. apt) leaves a partially configured host with no cleanup or guidance.
3. **Invalid systemd unit + password divergence.** `radio.service` combines `Type=oneshot` + `RemainAfterExit=yes` with `Restart=on-failure` — rejected/ignored by current systemd — and puts `StartLimitIntervalSec`/`StartLimitBurst` in `[Service]` where they belong in `[Unit]`. Three divergent published hotspot passwords exist: `radio123` (install.sh heredoc), `Configure123!` (config/radio.conf and the `system.py:230` fallback), `radio123` (docker/compose.ci.yml).

## Goals / Non-Goals

**Goals:**
- Delete the dnsmasq dead code on both sides (container and host) and stop touching `/etc/systemd/resolved.conf`.
- Make the hotspot experience honest: UI, API instructions, and installer output point to `http://192.168.4.1:8000` while in hotspot mode.
- Single source of truth for the Pi compose file: `docker/compose.prod.yml`, downloaded at install time.
- Correct, minimal systemd unit; Docker (`restart: unless-stopped`) is the container supervisor.
- Random per-device hotspot password generated at install, persisted in `radio.conf`, visible in the settings/setup UI; fixed documented default only for dev/CI.
- Safe partial-failure behaviour in `install.sh`.

**Non-Goals:**
- Deleting `config/systemd/radio-wifi.service` and `scripts/install-service.sh` — scoped to the separate `cleanup-dead-code-and-docs` change.
- Any alternative mechanism to make `radio.local` resolve in hotspot mode (e.g. host-side dispatcher scripts). If wanted later, it is a new change.
- Fixing the cleartext exposure of `HOTSPOT_PASSWORD` via `GET /api/system/settings` (tracked under the API-security work); here we only unify where the value comes from.
- mDNS behaviour in client mode (avahi) — unchanged.

## Decisions

### D1: Remove dnsmasq entirely rather than move it to the host

The review offered two options: run dnsmasq management on the host, or drop it and print `192.168.4.1`. We drop it. Rationale: the feature never worked in production (dead since the container migration), nobody has depended on it, and host-side lifecycle management would need a NetworkManager dispatcher hook or host agent — new machinery for marginal UX. NetworkManager's `nmcli device wifi hotspot` already runs its own DHCP/DNS via its internal dnsmasq instance; clients get the gateway IP by DHCP, so `http://192.168.4.1:8000` always works. Consequences:

- `wifi_manager.py`: delete the four `systemctl` invocations and associated logging in `switch_to_host_mode()` / `switch_to_client_mode()`.
- `install.sh`: delete the whole dnsmasq section (apt install, `/etc/dnsmasq.d/radio-hotspot.conf`, mask) and the `resolved.conf` stub-listener edit. Do not attempt to undo those edits on hosts where a previous installer made them — masked dnsmasq and `DNSStubListener=no` are harmless; a note in the change is enough.
- Spec side: the `hotspot-dns-resolution` requirements for dnsmasq are REMOVED; the "setup page URL" requirement is modified to be mode-aware (gateway IP in hotspot mode).

### D2: Download `docker/compose.prod.yml` instead of embedding it

`install.sh` fetches `https://raw.githubusercontent.com/rubenfeurer/radio001/main/docker/compose.prod.yml` to a temp file with `curl -fsSL`, and only moves it into `/opt/radio/docker-compose.yml` on success (`mv` after a non-empty sanity check / `docker compose config -q` if available). Alternatives considered: keep the heredoc and add a CI drift check (still two copies, still drift between releases), or bake the compose into the image (chicken-and-egg: compose is needed before any container exists). Download keeps one canonical file, and the atomic temp-file move satisfies the partial-failure goal — a failed download leaves any existing compose file untouched and aborts with a clear message. Watchtower pinning is reconciled in `compose.prod.yml` itself (pin the version there, matching what the heredoc had).

### D3: Ownership instead of `chmod 777`

The container runs as a non-root app user; the data volume needs to be writable by that UID. Replace `chmod 777 "${DATA_DIR}"` with `chown -R <uid>:<gid> "${DATA_DIR}"` where the UID/GID match the container's app user (determined from the image's Dockerfile; if the container runs as root today, `chown root:root` + `chmod 755` documents intent and still removes world-writability). The UID is recorded as a variable at the top of `install.sh` next to `IMAGE` so it is updated alongside image changes.

### D4: systemd unit — oneshot without Restart

`Type=oneshot` + `RemainAfterExit=yes` is the correct shape for a "run `docker compose up -d`, consider yourself active" unit. `Restart=` is both invalid for oneshot and redundant: the actual radio process is supervised by dockerd via `restart: unless-stopped`, and dockerd itself is supervised by systemd. So: drop `Restart=`/`RestartSec=`, drop `StartLimit*` entirely (they only mattered for the restart loop), keep `Requires=docker.service` / `After=docker.service network-online.target`. The `boot-behaviour` spec scenario "Service restarts on failure" is replaced by a "restart supervision delegated to Docker" scenario.

### D5: Install-time random hotspot password

At install, when writing a fresh `radio.conf` (the non-idempotent branch), generate the password with `tr -dc 'A-Za-z0-9' </dev/urandom | head -c 12` (12 chars, ≥ WPA2 8-char minimum, unambiguous alphanumerics for easy phone entry). Persist it as `HOTSPOT_PASSWORD=` in `/opt/radio/config/radio.conf` and print SSID + password in the installer's final summary. Idempotency: an existing `radio.conf` is never rewritten, so re-running install preserves a user's password. Discovery after install: the settings UI already round-trips `HOTSPOT_PASSWORD` via `GET/PUT /api/system/settings`; the setup page additionally shows the current hotspot credentials so a user standing at the device knows what to join. Dev/CI keep the documented fixed default `radio123` (`docker/compose.ci.yml`, mock mode); `config/radio.conf` in the repo (the dev template) is aligned to `radio123` with a comment stating it is dev-only and replaced by a generated value on real installs. The `Configure123!` fallback in `backend/api/routes/system.py:230` is aligned to the same documented default so there is exactly one published default.

### D6: Partial-failure safety

`install.sh` keeps `set -euo pipefail` and adds: an `trap ... ERR` that prints which step failed and that re-running the script is safe; temp-file + `mv` for every file it writes (compose, unit, radio.conf); `systemctl daemon-reload` + `enable --now` only after all files are in place. No rollback machinery — idempotent re-run is the recovery story.

## Risks / Trade-offs

- [Users on the hotspot type `radio.local` out of habit and it fails] → Every surface (installer output, setup page, API instructions, hotspot UI banner) shows `http://192.168.4.1:8000`; client-mode surfaces keep `radio.local:8000` via mDNS/avahi, which is unaffected.
- [Compose download couples install to GitHub availability and to `main`] → Install already curls itself from raw.githubusercontent.com, so no new dependency class; failure is atomic (D2) and re-runnable. Pinning to `main` matches the documented install flow.
- [Existing Pis carry leftover masked dnsmasq + `DNSStubListener=no`] → Harmless (dnsmasq masked = inert; stub listener off = host uses resolv.conf DNS directly). Documented, not auto-reverted, to keep the installer from editing resolved.conf at all.
- [Random password locks out a user who never saw the install output] → Password is persisted in `radio.conf` (readable on the Pi) and shown in the settings UI once connected in client mode; setup page shows it in hotspot mode.
- [`chown` to a wrong UID breaks station persistence] → Verified against the image's runtime user during implementation and covered by the fresh-Pi install verification task.

## Migration Plan

1. Land code + installer changes; CI verifies compose.ci.yml still uses the documented dev default.
2. Reconcile `docker/compose.prod.yml` (Watchtower pin) so the downloaded file matches what installs previously wrote.
3. On existing Pis: re-run `install.sh` (idempotent) — it rewrites compose from the repo, rewrites the unit, fixes data-dir permissions, preserves the existing `radio.conf` (and its password). No password rotation is forced.
4. Rollback: previous install.sh from git history still works; leftover host state is inert either way.

## Open Questions

None — decisions above resolve the review's open choice (drop dnsmasq vs. host-run it) in favour of dropping it.
