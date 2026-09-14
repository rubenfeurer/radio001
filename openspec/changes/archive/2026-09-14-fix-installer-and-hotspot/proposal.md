# Fix Installer and Hotspot

## Why

The hotspot dnsmasq path is dead code: `backend/core/wifi_manager.py` (lines 695-696, 766-774) calls `sudo systemctl unmask/start/stop dnsmasq` from inside the container, but `systemctl` is not installed in the image, is not in sudoers, and cannot reach host systemd — so `radio.local` never resolves in hotspot mode, while `scripts/install.sh` (lines 216-248) installs/masks dnsmasq on the host and rewrites `/etc/systemd/resolved.conf` purely on behalf of that dead path. On top of that, the installer has real papercuts: an embedded compose heredoc already drifting from `docker/compose.prod.yml` (Watchtower pinned to `1.7.1` in one, unpinned in the other), `chmod 777` on the data dir, a systemd unit combining `Type=oneshot` + `Restart=on-failure` (invalid on current systemd, with `StartLimit*` misplaced in `[Service]`), a final message claiming `http://radio.local` when the app listens on `:8000`, and three divergent published hotspot passwords (`radio123` in install.sh, `Configure123!` in config/radio.conf, `radio123` in docker/compose.ci.yml).

## What Changes

- **BREAKING** Remove the container-side `systemctl` dnsmasq calls from `switch_to_host_mode()` / `switch_to_client_mode()` in `backend/core/wifi_manager.py` — in hotspot mode the UI/setup info and API surface the gateway IP `http://192.168.4.1:8000` instead of promising `radio.local`.
- **BREAKING** Remove the host-side dnsmasq install/mask and `/etc/systemd/resolved.conf` `DNSStubListener` manipulation from `scripts/install.sh`.
- Replace the embedded compose heredoc in `install.sh` with a download of `docker/compose.prod.yml` from the repo, eliminating drift.
- Replace `chmod 777` on `/opt/radio/data` with ownership matching the container UID.
- Fix `radio.service`: drop `Restart=`/`RestartSec=` (Docker's `restart: unless-stopped` is the real supervisor), move `StartLimit*` to `[Unit]` (or drop), keep valid `Type=oneshot` + `RemainAfterExit=yes`.
- Fix the installer's final message to print working URLs (`http://<ip>:8000`, `http://radio.local:8000`).
- Make partial-failure paths in `install.sh` safe (no half-written compose/unit files, clear failure messages).
- Generate a random hotspot password at install time, persist it in `radio.conf`, show it in the setup/settings UI; keep a documented fixed default (`radio123`) only for dev/CI.
- NOT in scope: deleting `config/systemd/radio-wifi.service` + `scripts/install-service.sh` — that belongs to the separate `cleanup-dead-code-and-docs` change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pi-install`: install script downloads `docker/compose.prod.yml` instead of embedding a copy; data dir gets container-UID ownership instead of `chmod 777`; no dnsmasq/resolved.conf host changes; random hotspot password generated and persisted at install; final message shows working `:8000` URLs; partial failures leave no broken state.
- `hotspot-dns-resolution`: REMOVE the dnsmasq-based `radio.local`-in-hotspot requirements (dead code, never worked); the setup/UI requirement changes to show the gateway IP `192.168.4.1` in hotspot mode.
- `hotspot-configuration`: hotspot activation/deactivation no longer attempts any `systemctl` call from the container; hotspot details surface the gateway IP; new requirement for install-time generated password with fixed default only in dev/CI.
- `boot-behaviour`: the `radio.service` unit no longer declares `Restart=` — restart supervision is delegated to Docker's `restart: unless-stopped`; the unit is valid under current systemd.

## Impact

- `scripts/install.sh` — compose download, data-dir ownership, dnsmasq/resolved.conf removal, password generation, systemd unit content, final message, error handling.
- `backend/core/wifi_manager.py` — remove `systemctl` dnsmasq calls (lines 694-697, 764-774).
- `backend/api/routes/system.py` / `wifi.py` — hotspot instructions surface `http://192.168.4.1:8000`; no hardcoded `Configure123!` fallback semantics change (password comes from radio.conf).
- `frontend/src/routes/setup/+page.svelte` — hotspot instructions show gateway IP; `frontend/src/routes/settings/+page.svelte` — hotspot password visible to the owner.
- `docker/compose.prod.yml` — single source of truth for the Pi compose file (Watchtower pinning reconciled).
- `docker/compose.ci.yml`, dev mock config — keep documented fixed default password `radio123`.
- Existing Pis: re-running `install.sh` updates the unit and compose; an already-set password in `radio.conf` is preserved (idempotency).
