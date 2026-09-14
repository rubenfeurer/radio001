# Project Review — September 2026

Full-project review (backend, frontend, infra/CI, docs, openspec) for robustness, security, and simplification. Findings verified against code with file:line references.

## Verdict

| Area | Robustness | Security | Simplification |
|------|-----------|----------|----------------|
| Backend (Python) | **Weak** | Acceptable | Acceptable |
| Frontend (SvelteKit) | **Weak** | Solid | Acceptable |
| Infra / CI / Deploy | **Weak** | **Weak** | **Weak** |

The architecture is sound and the code is readable, but the three most user-visible hardware flows are broken, the release pipeline has a live footgun, and roughly a fifth of the repo is dead code that hides the real bugs.

## Critical — fix first

1. **Release tag race can brick every Pi.** `ci-cd.yml:238-285` still contains a per-platform docker-build matrix that pushes the same `:stable`/`:latest` tags as `release.yml` — last job to finish wins. An amd64-only `:stable` would be auto-pulled by Watchtower at 03:00 fleet-wide with no rollback (old image deleted by `WATCHTOWER_CLEANUP`). **Fix: delete the docker-build job from ci-cd.yml; release.yml is the sole publisher.**
2. **Two knob clicks reboot the Pi.** `gpio_controller.py:275-288` — triple-press detection compares against press *start* time (always < 0.5 s), counts never decay, and fires at count ≥ 2. Any two short presses, even minutes apart, trigger `reboot`. No gpio tests exist to catch it.
3. **Long-press hotspot toggle is a no-op.** `radio_manager.py:401,404` call async `switch_to_host_mode()`/`switch_to_client_mode()` without `await` — the success chime plays, the log lies, nothing happens. (The HTTP path awaits correctly, masking the bug.)
4. **Privileged container + blanket sudo + no-auth API = LAN root.** `compose.prod.yml:32` runs `privileged` with `/dev:/dev:rw`; `Dockerfile.backend:61` grants passwordless sudo for unrestricted `cp/mv/rm/chmod`. One injection bug or poisoned dependency gives any LAN/hotspot client host root. The compose already lists the sufficient narrow grants (`cap_add`, `devices`, `group_add`) — drop `privileged` and constrain sudoers.

## High

- **No stream recovery.** `radio_manager.py:73` creates `AudioPlayer` without a status callback: when mpg123 dies (WiFi blip), state stays "playing" forever, and pressing the same button *stops* the dead session instead of restarting. No reconnect logic exists anywhere.
- **mpg123 stderr pipe never drained** (`audio_player.py:141-145`) — a flaky stream fills the 64 KB pipe and wedges playback after hours. Use `DEVNULL`.
- **Notification chimes likely never play**: `sound_manager.py:218-224` generates WAV files but plays them with mpg123, an MPEG-only decoder, with errors silenced. Verify on the Pi.
- **Supply chain**: lgpio fetched over plain HTTP with no checksum into the privileged image (`Dockerfile.backend:79`); frontend uses `npm install` with no lockfile copied (`Dockerfile.backend:8-9`); `trivy-action@master` is a mutable ref in a workflow with `packages: write`. Pin all three.
- **Security gate fires after publish**: `release.yml:90-114` pushes `:stable` first, then Trivy-scans — and scans `:latest` (the *previous* image) on tag builds. Reorder to build → scan → push, and document a rollback one-liner.
- **WebSocket client bugs (frontend)**: visiting `/status` permanently disables reconnect for the whole SPA session (`status/+page.svelte:15-17` + `websocket.svelte.ts:80` — `shouldReconnect` never reset); `connect()` guards only `OPEN`, so a `CONNECTING` socket gets orphaned and causes connection flapping (`websocket.svelte.ts:18`).
- **Hotspot dnsmasq path is dead code**: `wifi_manager.py:695,766-769` calls `sudo systemctl` which isn't in sudoers, isn't installed, and can't reach host systemd — while `install.sh:216-248` modifies host DNS on its behalf. In hotspot mode `radio.local` never resolves. Run it on the host or drop it and print `192.168.4.1`.

## Medium

- **Settings newline injection**: `settings.py:99` writes raw values into `radio.conf`; `"x\nWIFI_INTERFACE=eth0"` in an SSID field injects arbitrary config keys loaded into env at next boot. Reject `\n`/`\r`, cap length.
- **WiFi PSKs in argv** (`wifi_manager.py:409-421,444-455`) — visible in `ps`; and `GET /api/system/settings` returns `HOTSPOT_PASSWORD` in cleartext. Also three divergent default hotspot passwords across `install.sh:121`, `radio.conf:12`, `compose.ci.yml:26` — generate one at install time instead.
- **SSID option-injection**: an SSID starting with `-` is parsed by nmcli as a flag (`wifi_manager.py:449`). No `shell=True` anywhere (good).
- **API lies about outcomes**: mutating routes return `success=True` before the background task runs (`radio.py:114`, `stations.py:167-171`); frontend compounds this by never checking `response.ok` (`radio.svelte.ts:12-41`) — a dead stream URL looks identical to success.
- **`forget_network` deletes by positional index across two enumerations** (`wifi_manager.py:627-684`) — a list change between calls deletes the wrong profile. Key by name.
- **Metrics tick spawns a throwaway `WiFiManager` + ~4 nmcli processes every 5 s** (`system.py:130-149`) despite the real instance being injected — ~2,900 subprocess spawns/hour per WS client.
- **`import_stations` self-deadlocks** on its own non-reentrant lock (`station_manager.py:364-401`): always hangs 10 s and fails; the test that covers it asserts nothing.
- **Half-init singleton**: `RadioManager.create_instance` registers the instance before `_initialize()` completes (`radio_manager.py:113-117`) — a failed init serves a broken manager to all routes.
- **Installer/systemd papercuts**: `chmod 777` on data dir; `Type=oneshot` + `Restart=on-failure` is invalid in recent systemd; install.sh embeds a compose copy already drifting from `docker/compose.prod.yml` (Watchtower pinned in one, unpinned in the other); final message says `http://radio.local` but nothing listens on port 80 (app is on 8000).
- **Volume slider races**: fires a POST per input event and WS echo snaps it backwards mid-drag (`settings/+page.svelte:124-127`). Debounce + ignore echoes while dragging.

## Simplification — delete list

Removing dead code here directly removes failure modes above:

- `docker/entrypoint.sh` — entire Nuxt-era file, referenced by nothing.
- `scripts/wifi-init.sh`, `scripts/boot-wifi-check.sh` — logic reimplemented in `wifi_manager.py`; divergent copies.
- `config/systemd/radio-wifi.service` + `scripts/install-service.sh` — broken duplicate of install.sh's unit (nonexistent `radio` user, fights over the same compose project).
- `scripts/backend-test-status.sh`, `ci-pipeline-fix.sh`, `test-ci.sh`, `setup-github-protection.sh`, `dev-environment.sh` — unreferenced one-offs.
- `config/stations.json` — byte-identical 5.6 MB duplicate of `backend/assets/stations.json` (the one actually used).
- `config/avahi/*`, dev-compose `traefik`/`mdns` profiles — stale (avahi file still advertises Nuxt port 3000).
- `config/polkit/*.pkla` — dev-only mount, never consulted in prod (backend uses `sudo nmcli`).
- Frontend: `/status` route (unlinked, duplicates settings cards, and is the trigger of the reconnect bug), `SignalStrength.svelte`, `ui/separator`, unused card subcomponents.
- Backend: `aiohttp` + `python-multipart` deps (unused), triplicated `ApiResponse` model, `AudioPlayer.pause/resume/test_playback/...` (zero callers), unused `WS*` models, two independent `radio.conf` parsers (`main.py` vs `settings.py`).
- CI: consolidate 4 workflows → develop-ci (lint/type), one test workflow (drop `test-backend.yml`'s 300-line report-generation jobs), release.yml. On every push to main, three heavy workflows currently run.

## Doc corrections

- `README.md:130` — `POST /api/radio/play/{slot}` doesn't exist; actual: `POST /api/radio/stations/{slot}/play`.
- `README.md:105` — dev frontend port is 3000, not 5173.
- `README.md:94` — no `data/` at repo root (Pi-only, `/opt/radio/data/`).
- `README.md:73` — station library is `backend/assets/stations.json`.
- `docs/deployment-and-updates.md:140` — version is *not* shown on the Settings page (not implemented).
- `openspec/specs/homepage-radio-controls/spec.md` — badly stale (old store filenames, removed volume slider, wrong WS message names). Other spot-checked specs (settings-ui, wifi-management) match reality. OpenSpec hygiene otherwise excellent: 0 active changes, 33 archived.

## What's good

- No `shell=True` anywhere; all subprocess use is exec-style. No XSS vectors in the frontend (no `{@html}`); WiFi passwords handled correctly (JSON body, transient state, never in URL/storage). Station/state JSON writes are atomic (tmp + rename). Requirements hash-pinned with CI lock-sync check. Route/manager test coverage is genuinely good (~5,800 lines) — the gap is the hardware layer (`gpio_controller`, `audio_player`, `sound_manager` have zero tests, which is exactly where the critical bugs live).

## Suggested order of attack

1. Delete `docker-build` from `ci-cd.yml` (release race).
2. Fix triple-press detection + the missing `await`s (hardware flows), add gpio tests.
3. Drop `privileged`/blanket sudo; pin lgpio (checksum + https) and npm lockfile.
4. Wire `AudioPlayer` status callback into `RadioManager` + add stream reconnect.
5. Reorder release.yml to build → scan → push; document rollback.
6. Run the delete list; fix README/spec staleness.
