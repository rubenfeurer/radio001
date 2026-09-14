# Cleanup Dead Code and Docs

## Why

Roughly a fifth of the repo is dead code — Nuxt-era scripts, duplicated 5.6 MB data files, unused backend models/deps, and four overlapping CI workflows — which hides real bugs and slows every review (see `docs/project-review-2026-09.md`, "Simplification — delete list"). Several docs and one main spec describe endpoints, ports, and files that no longer exist, actively misleading contributors.

## What Changes

- **Delete dead files** (all verified unreferenced, or referenced only by other files on this list):
  - `docker/entrypoint.sh` (Nuxt-era; prod entrypoint is `docker/entrypoint-backend.sh`)
  - `scripts/wifi-init.sh`, `scripts/boot-wifi-check.sh` (reimplemented in `wifi_manager.py`)
  - `config/systemd/radio-wifi.service` + `scripts/install-service.sh` (broken duplicate of install.sh's unit)
  - `scripts/backend-test-status.sh`, `scripts/ci-pipeline-fix.sh`, `scripts/test-ci.sh`, `scripts/setup-github-protection.sh`, `scripts/dev-environment.sh` (one-offs; `dev-environment.sh` is referenced only by `scripts/setup-dev.sh`, which must be updated or removed alongside)
  - `config/stations.json` (byte-identical duplicate of `backend/assets/stations.json`, the copy baked into the image) — requires removing the `../config/stations.json` mount from `docker/compose.dev.yml`
  - `config/avahi/*` and the `traefik`/`mdns` profiles in `docker/compose.dev.yml` (stale; avahi file advertises Nuxt port 3000)
  - `config/polkit/*.pkla` + its dev-compose mount (never consulted in prod; backend uses `sudo nmcli`)
- **Backend pruning**:
  - Remove unused deps `aiohttp` and `python-multipart` from `backend/requirements.in`; regenerate `requirements.lock` with hashes from the project root
  - Dedupe the triplicated `ApiResponse` model (`core/models.py:180`, `api/routes/wifi.py:29`, `api/routes/system.py:194`) — keep the `core/models.py` one
  - Remove `AudioPlayer` dead API: `pause`, `resume`, `test_playback`, `get_playback_info`, `get_current_url`, `is_playing` (zero production callers; verified)
  - Remove unused WS models `WSVolumeUpdate`, `WSStationChange`, `WSPlaybackStatus`, `WSSystemStatus` (`WSMessage` stays — used by `api/routes/websocket.py`)
  - Consolidate the two independent `radio.conf` parsers (`main._load_radio_conf` and `settings._read_conf`) into one shared helper
- **CI consolidation** (on push to `main`, three heavy workflows currently run): merge `ci-cd.yml`'s remaining jobs into a single test workflow based on `test-backend.yml`, dropping the ~300-line `test-analysis`/`final-status` markdown report jobs; `develop-ci.yml` stays the quick gate for `develop`; `release.yml` stays the sole publisher. **Out of scope**: deleting the `docker-build` job from `ci-cd.yml` and Trivy ordering/pinning — already covered by the `fix-release-pipeline-race` change, which must land first.
- **Doc corrections**: `README.md` (play endpoint is `POST /api/radio/stations/{slot}/play`; dev frontend port is 3000; no `data/` at repo root; station library is `backend/assets/stations.json`); `docs/deployment-and-updates.md` (version is not shown on the Settings page); rewrite the stale `homepage-radio-controls` spec via delta (old store filenames, removed volume slider, wrong WS message name `stations_list` vs actual `stations_update`).

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `project-structure`: Canonical station-library location flips from `config/stations.json` to `backend/assets/stations.json` (the copy actually baked into the image); new requirements forbid the dead scripts, stale config directories, and duplicated backend models/deps.
- `dockerfile-accuracy`: The compose-mount requirement changes — the station library comes from `backend/assets/` (via the `backend/` source mount in dev, baked in prod), not from a `config/stations.json` mount.
- `ci-pipeline`: The no-duplicate-integration-job requirement broadens to cover all workflows triggered by a push to `main`; new requirements mandate a single consolidated test workflow and forbid markdown report-generation jobs.
- `homepage-radio-controls`: The main spec is freeform and badly stale; this change rewrites it as proper requirements reflecting actual behavior (stores `radio.svelte.ts`/`websocket.svelte.ts`, no homepage volume slider, WS message `stations_update`).

## Impact

- Deleted: ~10 scripts/config files, one 5.6 MB JSON duplicate, two dev-compose profiles and two mounts
- `backend/`: `requirements.in`/`requirements.lock`, `core/models.py`, `api/routes/wifi.py`, `api/routes/system.py`, `api/routes/settings.py`, `main.py`, `hardware/audio_player.py`, plus affected tests (`tests/api/test_websocket.py`, `conftest.py` mocks); docstring fix in `api/routes/radio.py:360`; stale link fix in `backend/tests/integration/README.md:307`
- `.github/workflows/`: `ci-cd.yml` deleted (after `fix-release-pipeline-race` merges), `test-backend.yml` slimmed into the single test workflow
- Docs: `README.md`, `docs/deployment-and-updates.md`
- Known deferred staleness: `openspec/specs/hotspot-dns-resolution/spec.md` references `boot-wifi-check.sh`; that spec is being reworked by the `fix-installer-and-hotspot` change and is not touched here
- No runtime behavior change intended; risk is limited to accidentally deleting something referenced (mitigated by grep verification tasks and full test/build verification)
