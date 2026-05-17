## 1. Backend API prefix

- [x] 1.1 In `backend/main.py`, add `prefix="/api"` to the `include_router` call for `system_router`
- [x] 1.2 In `backend/main.py`, add `prefix="/api"` to the `include_router` call for `stations_router`
- [x] 1.3 In `backend/main.py`, add `prefix="/api"` to the `include_router` call for `radio_router`
- [x] 1.4 In `backend/main.py`, add `prefix="/api"` to the `include_router` call for `wifi_router`

## 2. Frontend dev proxy

- [x] 2.1 In `frontend/vite.config.ts`, remove the `rewrite` function from the `/api` proxy entry so that `/api/*` is forwarded to the backend as-is (no prefix stripping)

## 3. Station library in Docker image

- [x] 3.1 Verify `backend/assets/` directory exists (create it if not)
- [x] 3.2 Copy `config/stations.json` to `backend/assets/stations.json`
- [x] 3.3 Verify the Dockerfile COPY step includes `backend/assets/` in the image

## 4. Verification

- [x] 4.1 Run backend tests (`cd backend && ./run_tests.sh`) — confirm no breakage from route prefix change
- [x] 4.2 Start dev environment and verify radio slots load, station picker works, no 404 flash, WiFi scan works
