## Why

The project has accumulated duplicated files, unused artifacts, and scattered config that adds maintenance overhead without adding value. Cleaning this up makes the codebase easier to navigate, reduces the risk of editing the wrong copy of a file, and removes dead code that can mislead future development.

## What Changes

- Delete `assets/stations.json` and `backend/assets/stations.json` — `config/stations.json` is the single authoritative copy; Docker mounts updated accordingly
- Delete `assets/sounds/` and `backend/assets/sounds/` duplicates — `config/sounds/` becomes the single location; Docker mounts updated
- Delete `data/default_stations.json` and `data/preferences.json` — both are unused; defaults come from env vars, preferences are never read
- Delete `backend/package.json` — meaningless for a Python project
- Delete `frontend/src/lib/stores/system.svelte.ts` — `systemState` is never imported or used; `wifiState.status` already holds system status
- Merge `backend/core/wifi_models.py` into `backend/core/models.py` — both are Pydantic models in the same layer; no reason to split
- Remove duplicate `ApiResponse` class defined in `backend/main.py` — already defined in `backend/core/models.py`
- Delete `backend/Dockerfile` — duplicate of `docker/Dockerfile.backend`
- Consolidate Docker config: merge `compose/` and `nginx/` into `docker/` so all container/deploy files are in one place
- Update Docker compose mounts to point at `config/` for stations and sounds

## Capabilities

### New Capabilities

- `project-structure`: Canonical layout of assets, config, and Docker files — defines where each file type lives

### Modified Capabilities

- `dockerfile-accuracy`: Docker compose mounts change to reflect new canonical file locations

## Impact

- `compose/docker-compose.yml` and `compose/docker-compose.prod.yml` — volume mount paths updated
- `backend/core/` — `wifi_models.py` merged; all route files that import from it updated
- `backend/main.py` — duplicate `ApiResponse` removed
- `frontend/src/lib/stores/` — `system.svelte.ts` deleted
- No API surface changes; no frontend behavior changes
