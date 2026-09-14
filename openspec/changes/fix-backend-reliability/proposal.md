# Fix Backend Reliability

## Why

The September 2026 project review (docs/project-review-2026-09.md, "Medium" section) verified six backend reliability defects: a guaranteed self-deadlock in station import, a singleton that serves half-initialized state after a failed init, a delete-by-index race that can forget the wrong WiFi profile, a metrics loop that spawns ~4 nmcli subprocesses every 5 seconds per WebSocket client, mutating API routes that report success before the action runs, and a WebSocket broadcast loop where one stalled client blocks updates for everyone. Each is a real, reproducible failure mode in code paths users hit daily.

## What Changes

- **Fix `StationManager.import_stations` self-deadlock** (backend/core/station_manager.py:364-401): the method acquires the non-reentrant `asyncio.Lock` and then calls `_save_stations()`, which re-acquires the same lock — every import hangs for the 10 s `wait_for` timeout and returns `False`. Restructure lock discipline so save-while-locked is possible; repair `test_import_stations`, which currently asserts nothing.
- **Fix half-initialized `RadioManager` singleton** (backend/core/radio_manager.py:113-117): `cls._instance` is assigned before `await _initialize()`; if init raises, the broken instance remains registered and is served to all routes via `get_instance()`. Register the instance only after successful initialization and define `get_instance()` to raise when no successfully initialized instance exists.
- **BREAKING** — **Forget WiFi network by connection name instead of positional index**: `forget_network` (backend/core/wifi_manager.py:627-684) and `DELETE /api/wifi/saved/{network_id}` (backend/api/routes/wifi.py:140-158) each re-enumerate saved networks and resolve a positional index; a list change between enumerations deletes the wrong profile. Key the API and manager on the NetworkManager connection name. Frontend caller (frontend/src/lib/stores/wifi.svelte.ts:254-259) updated to pass `connection_name`.
- **Reuse injected WiFiManager in system metrics** (backend/api/routes/system.py:130-149): the metrics tick constructs a throwaway `WiFiManager` (~4 nmcli subprocesses) every 5 s even though `set_system_wifi_manager` injection exists. Use the injected instance; fall back gracefully when absent.
- **Honest API responses for mutating radio routes**: `POST /api/radio/volume` (backend/api/routes/radio.py:114) and `POST /api/radio/stations/{slot}/play` (backend/api/routes/stations.py:167-171) queue BackgroundTasks and return `success=True` before anything happens; the toggle's "starting/stopping" message is computed after scheduling, so it can also describe the wrong direction. Decision: await the action and return the actual outcome (see design.md).
- **WebSocket broadcast robustness** (backend/api/routes/websocket.py:120-136): sends run sequentially with no timeout — one stalled client delays all others indefinitely; the send loop also iterates `active_connections` without the manager's lock while cleanup paths use it. Add a per-send timeout, isolate slow clients, and lock `active_connections` access consistently.
- **Tests** for every item above, including making the existing import test assert success and persistence.

## Capabilities

### New Capabilities

<!-- none — all changes fix or tighten existing behavior -->

### Modified Capabilities

- `wifi-management`: "Saved Network Management" requirement — forgetting a saved network is keyed by NetworkManager connection name (stable identifier) instead of a positional index that can drift between enumerations.
- `radio-integration`: "Real-time Radio Status" requirement — broadcast delivery must not be blocked by a single stalled client (per-send timeout, slow-client isolation). New requirement added for truthful mutating API responses (volume, station toggle).

### Unchanged (implementation-only, no spec delta)

- Import-stations lock discipline, singleton init ordering, and metrics WiFiManager reuse are internal fixes with no observable contract change; they are covered in design.md and tasks.md only.

## Impact

- **Backend code**: `backend/core/station_manager.py`, `backend/core/radio_manager.py`, `backend/core/wifi_manager.py`, `backend/api/routes/wifi.py`, `backend/api/routes/system.py`, `backend/api/routes/radio.py`, `backend/api/routes/stations.py`, `backend/api/routes/websocket.py`.
- **Frontend code**: `frontend/src/lib/stores/wifi.svelte.ts` (forget-network call switches from numeric id to connection name). Since frontend and backend ship in the same image, the breaking API change deploys atomically.
- **API**: `DELETE /api/wifi/saved/{network_id}` (int index) becomes name-keyed (**BREAKING**); radio/station mutation responses now reflect actual outcomes (status codes/message semantics tighten, shape unchanged).
- **Tests**: `backend/tests/unit/test_station_manager.py` repaired; new/extended tests for radio manager init, wifi forget, system metrics reuse, route response semantics, and WebSocket broadcast.
- **No dependency, schema, or deployment changes.**
