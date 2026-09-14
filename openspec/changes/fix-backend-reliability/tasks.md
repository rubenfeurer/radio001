# Tasks — fix-backend-reliability

## 1. StationManager import deadlock

- [x] 1.1 Split persistence in `backend/core/station_manager.py`: add `_save_stations_locked()` (assumes lock held, does serialize + atomic write) and make `_save_stations()` a locking wrapper around it
- [x] 1.2 In `import_stations`, call `_save_stations_locked()` inside the existing `async with self._lock:` block and remove the `asyncio.wait_for(..., 10.0)` workaround wrapper
- [x] 1.3 Repair `test_import_stations` in `backend/tests/unit/test_station_manager.py`: assert `success is True`, assert the imported station is returned by `get_station(1)` with expected name/url, and assert persistence (reload from file or new manager instance sees it); remove the no-op `hasattr` block
- [x] 1.4 Add a regression test that `import_stations` completes well under 1 s (no lock-timeout path) and returns `False` on invalid payloads without hanging

## 2. RadioManager singleton init

- [x] 2.1 In `backend/core/radio_manager.py` `create_instance`, construct into a local variable, await `_initialize()`, and assign `cls._instance` only after successful init; re-raise the init exception without registering
- [x] 2.2 Confirm `get_instance()` raises `RuntimeError` when no successfully initialized instance exists, and that a later `create_instance` call can retry after a failed init
- [x] 2.3 Add tests: failed `_initialize` leaves `get_instance()` raising and allows a successful retry; successful init returns the same instance on repeat calls

## 3. Forget WiFi network by connection name

- [x] 3.1 Change `WiFiManager.forget_network` (`backend/core/wifi_manager.py`) to take `connection_name: str`; verify existence and `current` flag from a single `list_saved_networks()` call, disconnect first if current, then `nmcli connection delete <connection_name>`; return `False` if the name is unknown
- [x] 3.2 Change the route in `backend/api/routes/wifi.py` to `DELETE /api/wifi/saved/{connection_name:path}`; return 404 for unknown names; remove the second enumeration/positional-id validation
- [x] 3.3 Update `frontend/src/lib/stores/wifi.svelte.ts` `forgetNetwork` to send `encodeURIComponent(network.connection_name)`; update its call sites (setup page / WiFi settings dialog) to pass the connection name
- [x] 3.4 Add backend tests: forget by name deletes exactly the named profile (mock nmcli), unknown name yields 404 and no delete, current network gets disconnect-then-delete, names containing spaces/slashes round-trip through the URL

## 4. System metrics WiFiManager reuse

- [x] 4.1 In `backend/api/routes/system.py` metrics collection, use the module-level manager injected via `set_system_wifi_manager()`; delete the throwaway `WiFiManager(...)` construction and its local import
- [x] 4.2 When no manager is injected, omit the WiFi block from metrics and log at debug — do not construct a fallback manager
- [x] 4.3 Add tests asserting the injected instance is used (e.g., mock injected manager's `get_status` called; `WiFiManager` constructor not invoked during a metrics tick) and that metrics still return without an injected manager

## 5. Honest mutating radio responses

- [x] 5.1 `POST /api/radio/volume` (`backend/api/routes/radio.py`): drop `BackgroundTasks`, `await radio_manager.set_volume(actual_volume)`, and base `success`/error response on its return value
- [x] 5.2 `POST /api/radio/stations/{slot}/play` (`backend/api/routes/stations.py`): drop `BackgroundTasks`; capture pre-mutation status to determine intent, `await radio_manager.toggle_station(slot)`, and respond with the actual resulting action ("started"/"stopped") and playback state; report failure when a stream fails to start
- [x] 5.3 Update/extend route tests: success path asserts the manager coroutine was awaited before the response and the message matches the resulting state; failure path (manager returns False/raises) yields a non-success response

## 6. WebSocket broadcast robustness

- [x] 6.1 In `backend/api/routes/websocket.py` `ConnectionManager.broadcast`: snapshot `active_connections` under `self._lock`, send outside the lock, wrap each send in `asyncio.wait_for(..., SEND_TIMEOUT)` (1.0 s module constant), collect timed-out/failed connections, and remove them in the existing locked cleanup
- [x] 6.2 Apply the same lock discipline to `send_personal_message` (membership check/disconnect under lock, no lock held across the awaited send) and to any stats methods iterating the set
- [x] 6.3 Add tests: a client whose `send_text` never completes is dropped after the timeout while other clients still receive the message; concurrent connect/disconnect during broadcast does not raise or corrupt the connection set

## 7. Verification

- [x] 7.1 Run the backend test suite and frontend check (`pytest`, `npm run check`) — all green
- [x] 7.2 Run `openspec validate --change "fix-backend-reliability"` and manually verify each spec scenario has a corresponding passing test
