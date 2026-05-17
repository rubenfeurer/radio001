## Why

All API calls from the frontend fail silently in production because the Vite dev server proxy strips the `/api` prefix, but the FastAPI backend has no `/api` prefix on its routes. The station library is also missing from the Docker image. These bugs make the radio UI non-functional: slots are empty, stations can't be selected, WiFi scan fails, and a brief 404 flash appears on load.

## What Changes

- Add `/api` prefix to all HTTP routers registered in `backend/main.py` (system, stations, radio, wifi)
- Copy `config/stations.json` to `backend/assets/stations.json` so it is included in the Docker image
- Update `backend/api/routes/radio.py` `_LIBRARY_FILE` default path to match the new asset location

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `homepage-radio-controls`: Radio slot state and controls now load correctly in production (were silently failing due to missing `/api` prefix)
- `radio-integration`: Station library and station selection endpoints now reachable in production

## Impact

- `backend/main.py`: all `include_router` calls gain `/api` prefix
- `backend/api/routes/radio.py`: `_LIBRARY_FILE` default path changes to `/app/assets/stations.json`
- `backend/assets/stations.json`: new file (copy of `config/stations.json`)
- `Dockerfile`: ensure `backend/assets/` is copied into image
- Frontend stores and routes: no changes needed — they already call `/api/...`
