## Context

The project has three identical copies of `stations.json` (168k lines each), duplicate sound files across `assets/` and `backend/assets/`, dead files (`data/preferences.json`, `data/default_stations.json`, `backend/package.json`), an unused frontend store, a duplicate Pydantic model, and Docker/config files spread across `docker/`, `compose/`, `nginx/`, `config/`, and `data/` with no clear ownership rule.

The Docker bind mounts in `compose/docker-compose.yml` are what forced the `backend/assets/stations.json` copy into existence — the container's working directory is `/app` (the `backend/` folder), so files outside `backend/` weren't accessible without explicit mounts. The fix is to add the right mounts rather than copy files.

## Goals / Non-Goals

**Goals:**
- One canonical location for each file type: stations library → `config/`, sounds → `config/sounds/`, runtime data → `data/`, Docker files → `docker/`
- Zero duplicate file content
- All dead code and unused files removed
- Docker compose mounts corrected so the container reads from `config/`
- No behavior changes at runtime

**Non-Goals:**
- Refactoring backend logic or APIs
- Changing the frontend UI
- Reorganizing the test suite
- Moving `config/radio.conf` (already mounted correctly)

## Decisions

**D1: `config/` owns all static/deploy-time assets**
`config/stations.json` is authoritative. `config/sounds/` (new path) holds the sound files. This follows the existing pattern — `config/` already holds `radio.conf`, `avahi/`, `polkit/`, `systemd/`. Assets and sounds are configuration, not code.

Alternative considered: keep sounds under `assets/` at root. Rejected because `assets/` has no clear mount strategy and `config/` already has Docker mount infrastructure.

**D2: Docker mounts updated, not file copies**
The compose file gains `- ../config/sounds:/app/assets/sounds:ro` and uses `- ../config/stations.json:/app/assets/stations.json:ro` (bind file mount) so the backend reads from the canonical location. This avoids ever needing a copy.

Alternative considered: move `LIBRARY_FILE` env var to point at `/app/config/stations.json`. Rejected — the `assets/` path is also referenced by `SoundManager` which expects `assets/sounds/`; changing both paths adds more blast radius.

**D3: `wifi_models.py` merged into `models.py`**
Both files are Pydantic model definitions in the same `core/` layer. The split has no benefit — there's no circular import risk, no separate ownership, and it adds an extra import statement everywhere. Merge and update all import sites.

**D4: `system.svelte.ts` deleted, not repurposed**
`systemState` has zero consumers. `wifiState.status` already holds the `SystemStatus` shape and is used by all routes. Introducing a refactor to make `system.svelte.ts` the authority would change behavior; deletion changes nothing.

**D5: Docker config consolidation into `docker/`**
`compose/*.yml` files move to `docker/` with cleaner names (`compose.dev.yml`, `compose.prod.yml`, `compose.ci.yml`). `nginx/*.conf` files move to `docker/nginx/`. `backend/Dockerfile` is deleted (duplicate of `docker/Dockerfile.backend`). All scripts that reference these paths are updated.

## Risks / Trade-offs

- **Broken Docker paths in scripts** → Mitigation: grep all scripts for `compose/` and `nginx/` references and update them as part of the task
- **CI workflows referencing old paths** → Mitigation: check `.github/workflows/*.yml` for hardcoded paths to `compose/` or `docker/` and update
- **Sound files differ between `assets/sounds/` and `backend/assets/sounds/`** → The user confirmed `assets/sounds/` is authoritative; `backend/assets/sounds/` is deleted; sounds copied to `config/sounds/`
- **`wifi_models.py` import changes break tests** → Low risk: `wifi_models` has 3 models; grep confirms only `api/routes/wifi.py` imports them; tests mock at the route level
