# project-structure Specification

## Purpose
Defines the canonical layout of the project — where each file type lives, what directories own which concerns, and what must not be duplicated.
## Requirements
### Requirement: Single canonical location for each asset type
The project SHALL have exactly one canonical copy of each runtime data file. Runtime assets consumed by the backend (station library, sound files) live under `backend/assets/` — the location baked into the production image via `COPY backend/ .`. `config/` holds host-side configuration only, and container/deploy files belong in `docker/`.

#### Scenario: Station library has one copy
- **WHEN** the project is checked out
- **THEN** `stations.json` SHALL exist only at `backend/assets/stations.json`
- **AND** `config/stations.json` SHALL not exist
- **AND** `docker/compose.dev.yml` SHALL NOT mount a `stations.json` from `config/` (the `../backend:/app` source mount provides `/app/assets/stations.json` in dev)

#### Scenario: Sound files have a canonical location
- **WHEN** the backend container runs in production
- **THEN** sound files SHALL be loaded from `backend/assets/sounds/` as baked into the image
- **AND** no additional sound-file copies SHALL be introduced beyond the existing `config/sounds/` development overlay

#### Scenario: Docker and compose files in one directory
- **WHEN** the project is checked out
- **THEN** all Dockerfiles, docker-compose files, and nginx configs SHALL be under `docker/`
- **AND** the `compose/` and `nginx/` top-level directories SHALL not exist
- **AND** `backend/Dockerfile` SHALL not exist (it is a duplicate of `docker/Dockerfile.backend`)

### Requirement: No unused data files at project root
The project root `data/` directory SHALL contain only files that are actively read by the running system.

#### Scenario: Unused files removed
- **WHEN** the project is checked out
- **THEN** `data/preferences.json` SHALL not exist
- **AND** `data/default_stations.json` SHALL not exist
- **AND** `backend/package.json` SHALL not exist

### Requirement: Frontend stores have no unused modules
Every file in `frontend/src/lib/stores/` SHALL be imported by at least one route or component.

#### Scenario: No dead store files
- **WHEN** the frontend is built
- **THEN** `system.svelte.ts` SHALL not exist in the stores directory
- **AND** no TypeScript errors SHALL be introduced by its removal

### Requirement: No dead scripts or stale host configuration
The repository SHALL NOT contain scripts, systemd units, or host-configuration files that are referenced by nothing in the codebase or that duplicate behavior implemented elsewhere.

#### Scenario: Nuxt-era entrypoint removed
- **WHEN** the project is checked out
- **THEN** `docker/entrypoint.sh` SHALL not exist
- **AND** the container entrypoint SHALL be `docker/entrypoint-backend.sh` as copied by `docker/Dockerfile.backend`

#### Scenario: WiFi shell scripts removed
- **WHEN** the project is checked out
- **THEN** `scripts/wifi-init.sh` and `scripts/boot-wifi-check.sh` SHALL not exist (their logic is implemented in `backend/core/wifi_manager.py`)
- **AND** no documentation link SHALL point to them

#### Scenario: Duplicate systemd unit removed
- **WHEN** the project is checked out
- **THEN** `config/systemd/radio-wifi.service` and `scripts/install-service.sh` SHALL not exist
- **AND** the only systemd unit SHALL be the `radio.service` written by `scripts/install.sh`

#### Scenario: One-off scripts removed
- **WHEN** the project is checked out
- **THEN** `scripts/backend-test-status.sh`, `scripts/ci-pipeline-fix.sh`, `scripts/test-ci.sh`, `scripts/setup-github-protection.sh`, `scripts/dev-environment.sh`, and `scripts/setup-dev.sh` SHALL not exist
- **AND** the documented development entry point SHALL be `docker compose -f docker/compose.dev.yml up`

#### Scenario: Stale avahi and polkit configuration removed
- **WHEN** the project is checked out
- **THEN** `config/avahi/` and `config/polkit/` SHALL not exist
- **AND** `docker/compose.dev.yml` SHALL NOT define `traefik` or `mdns` profile services
- **AND** `docker/compose.dev.yml` SHALL NOT mount a polkit configuration directory

### Requirement: Backend has no duplicated models, dead APIs, or unused dependencies
Backend Python code SHALL define each shared model exactly once, SHALL NOT expose public methods with zero production callers, and SHALL NOT declare dependencies that no module imports.

#### Scenario: Single ApiResponse model
- **WHEN** the backend source is searched for `class ApiResponse`
- **THEN** exactly one definition SHALL exist, in `backend/core/models.py`
- **AND** `api/routes/wifi.py` and `api/routes/system.py` SHALL import it from `core.models`

#### Scenario: Unused WebSocket models removed
- **WHEN** the backend source is searched for WebSocket message models
- **THEN** `WSVolumeUpdate`, `WSStationChange`, `WSPlaybackStatus`, and `WSSystemStatus` SHALL not exist
- **AND** `WSMessage` SHALL remain (it is used by `api/routes/websocket.py`)

#### Scenario: AudioPlayer exposes no dead API
- **WHEN** `backend/hardware/audio_player.py` is inspected
- **THEN** `pause`, `resume`, `test_playback`, `get_playback_info`, `get_current_url`, and the `is_playing` property SHALL not exist
- **AND** a grep across `backend/` and `frontend/` SHALL confirm zero remaining callers of these names on `AudioPlayer`

#### Scenario: Single radio.conf parser
- **WHEN** the backend source is searched for radio.conf parsing
- **THEN** exactly one shared parse function SHALL exist
- **AND** both the startup env-seeding path (`main.py`) and the settings API (`api/routes/settings.py`) SHALL use it

#### Scenario: No unused Python dependencies
- **WHEN** `backend/requirements.in` is inspected
- **THEN** `aiohttp` and `python-multipart` SHALL not be listed
- **AND** `backend/requirements.lock` SHALL be regenerated with `pip-compile --generate-hashes` from the project root and stay in sync with `requirements.in`

