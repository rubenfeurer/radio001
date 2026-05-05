## 1. Delete Dead Files

- [x] 1.1 Delete `assets/stations.json` (duplicate of `config/stations.json`)
- [x] 1.2 Delete `data/default_stations.json` (unused — defaults come from env vars)
- [x] 1.3 Delete `data/preferences.json` (unused — never read by any backend code)
- [x] 1.4 Delete `backend/package.json` (meaningless for a Python project)
- [x] 1.5 Delete `backend/Dockerfile` (duplicate of `docker/Dockerfile.backend`)
- [x] 1.6 Delete `frontend/src/lib/stores/system.svelte.ts` (unused — zero consumers)

## 2. Consolidate Sound Files

- [x] 2.1 Create `config/sounds/` directory and copy all three `.wav` files from `assets/sounds/` into it (these are the authoritative files)
- [x] 2.2 Delete `assets/sounds/` and `assets/` if it is then empty
- [x] 2.3 Delete `backend/assets/sounds/` (the differing copies)
- [x] 2.4 Delete `backend/assets/stations.json` (duplicate)
- [x] 2.5 Delete `backend/assets/` directory if it is then empty

## 3. Fix Docker Compose Mounts

- [x] 3.1 In `compose/docker-compose.yml`: replace `- ../assets:/app/assets:ro` with two specific mounts: `- ../config/stations.json:/app/assets/stations.json:ro` and `- ../config/sounds:/app/assets/sounds:ro`
- [x] 3.2 Verify the backend container can still reach both paths at `/app/assets/stations.json` and `/app/assets/sounds/`

## 4. Consolidate Docker / Compose / Nginx Directories

- [x] 4.1 Move `compose/docker-compose.yml` → `docker/compose.dev.yml`
- [x] 4.2 Move `compose/docker-compose.prod.yml` → `docker/compose.prod.yml`
- [x] 4.3 Move `compose/docker-compose.ci.yml` → `docker/compose.ci.yml`
- [x] 4.4 Move `compose/nginx-ci.conf` → `docker/nginx-ci.conf`
- [x] 4.5 Move `nginx/default.conf` → `docker/nginx.conf`; delete `nginx/` directory
- [x] 4.6 Delete `compose/` directory
- [x] 4.7 Update `scripts/dev-environment.sh`: change `COMPOSE_FILE` and `COMPOSE_PROD_FILE` paths and the override path to point at `docker/`
- [x] 4.8 Update `scripts/ci-pipeline-fix.sh`: update all `compose/docker-compose.ci.yml` references to `docker/compose.ci.yml`
- [x] 4.9 Update `scripts/backend-test-status.sh`: update `compose/docker-compose.ci.yml` references to `docker/compose.ci.yml`
- [x] 4.10 Update `.github/workflows/ci-cd.yml`: update all `compose/docker-compose.ci.yml` and `compose/docker-compose.prod.yml` references to `docker/compose.ci.yml` and `docker/compose.prod.yml`
- [x] 4.11 Update `docker/compose.prod.yml` (formerly `compose/docker-compose.prod.yml`): change nginx config volume mount from `../nginx/default.conf` to `./nginx.conf`

## 5. Backend Model Consolidation

- [x] 5.1 Append the three models from `backend/core/wifi_models.py` (`WiFiNetworkModel`, `WiFiCredentials`, `WiFiStatusModel`) into `backend/core/models.py`
- [x] 5.2 Delete `backend/core/wifi_models.py`
- [x] 5.3 Update `backend/api/routes/wifi.py`: change `from core.wifi_models import ...` to `from core.models import ...`
- [x] 5.4 Check for any other files importing from `core.wifi_models` and update them
- [x] 5.5 Remove the duplicate `ApiResponse` class defined locally in `backend/main.py` and ensure the import from `core.models` is used instead (or use `main.py`'s own `ApiResponse` only for the root/health endpoints — check if it's needed)
