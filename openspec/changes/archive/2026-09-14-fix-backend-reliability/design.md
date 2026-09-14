# Design — fix-backend-reliability

## Context

Six verified backend defects from docs/project-review-2026-09.md ("Medium" section). All are in code that already has good route/manager test coverage (~5,800 lines), so each fix lands with a test that would have caught it. No new dependencies; no data model changes. The only externally visible contract changes are the forget-network API key and the truthfulness of mutating radio responses.

Current state (verified against source):

1. `StationManager.import_stations` (station_manager.py:364-401) wraps its body in `async with self._lock:` and then calls `_save_stations()` (line 396), which itself does `async with self._lock:` (line 111). `asyncio.Lock` is non-reentrant, so the inner acquire never succeeds; the surrounding `asyncio.wait_for(..., timeout=10.0)` cancels after 10 s and the method returns `False`. Every import fails, slowly. The covering test (`test_import_stations`, backend/tests/unit/test_station_manager.py:349-373) calls the method and asserts nothing — the trailing `if hasattr(...)` block has no assertions.
2. `RadioManager.create_instance` (radio_manager.py:113-117) sets `cls._instance = cls(...)` then `await cls._instance._initialize()`. If `_initialize()` raises, `_instance` stays set; every subsequent `create_instance`/`get_instance` returns the broken object.
3. `WiFiManager.forget_network(network_id: int)` (wifi_manager.py:627-684) indexes into a *fresh* `list_saved_networks()` result, while the route (wifi.py:140-158) has already done its own enumeration to validate the id. Each `list_saved_networks` call runs nmcli again; if NetworkManager's connection list changes between the two enumerations (or between the UI fetching the list and the user clicking Forget), the positional index resolves to a different profile and the wrong network is deleted.
4. The `/api/system` metrics path (system.py:130-149) constructs a new `WiFiManager` inside the tick and calls `get_status()` (~4 nmcli subprocesses), every 5 s per connected WS client, despite `set_system_wifi_manager()` (system.py:31) existing precisely to inject the real instance.
5. `POST /api/radio/volume` (radio.py:114) and `POST /api/radio/stations/{slot}/play` (stations.py:167-171) schedule the mutation via `BackgroundTasks` and immediately return `success=True`. In the toggle route, the "starting"/"stopping" message is computed from `get_status()` *after* `add_task`, so if the background task runs first the message describes the opposite action.
6. `ConnectionManager.broadcast` (websocket.py:104-139) awaits `connection.send_text()` sequentially with no timeout — one client with a full TCP buffer stalls delivery to all others. The send loop iterates `self.active_connections.copy()` without holding `self._lock`, while `connect`/`disconnect`/cleanup mutate the set under the lock.

## Goals / Non-Goals

**Goals:**
- Every listed defect fixed with a regression test.
- Mutating radio endpoints report what actually happened.
- Forget-network keyed by a stable identifier end to end (API, manager, frontend).
- No behavior change beyond the two spec'd deltas.

**Non-Goals:**
- Stream-death recovery / status callback wiring (review "High" item — separate change).
- Frontend `response.ok` checking (review notes it; frontend hardening is out of scope except the forget-network call site).
- WiFi PSK/argv or settings-injection security items (separate change).
- Refactoring the ApiResponse triplication or other delete-list items.

## Decisions

### D1: Lock discipline in StationManager — unlocked `_save_stations_locked()` helper

Split persistence into `_save_stations_locked()` (assumes caller holds `self._lock`; does the actual serialize + atomic tmp/rename write) and keep `_save_stations()` as a locking wrapper (`async with self._lock: await self._save_stations_locked()`) for any external/unlocked callers. `import_stations` calls `_save_stations_locked()` from inside its existing `async with self._lock:` block.

- *Alternative — remove the lock from `_save_stations` entirely*: callers at lines 203/235/269 already hold no lock at those call sites? They do not hold it (their mutations lock separately), so removing the lock there would drop write serialization. Rejected.
- *Alternative — re-entrant lock emulation*: complexity with no asyncio stdlib support. Rejected.
- Also remove the `asyncio.wait_for(..., 10.0)` wrapper: it existed to paper over the deadlock; with correct locking it only adds a failure mode. Keep returning `False` on validation/IO errors.

### D2: Singleton registration only after successful init

In `create_instance`, construct into a local variable, `await instance._initialize()`, and assign `cls._instance = instance` only on success. On failure, leave `cls._instance is None` and re-raise so startup (`main.py` lifespan) fails loudly. `get_instance()` keeps its current contract — raises `RuntimeError` when `_instance is None` — which now also covers the failed-init case; routes surface this as a 500. A subsequent `create_instance` call may retry initialization because no instance was registered.

- *Alternative — register then mark `initialized` flag and check in `get_instance`*: two-state API, every route must handle "exists but broken". Rejected as more surface for the same guarantee.

### D3: Forget network keyed by NetworkManager connection name

- Manager: `forget_network(connection_name: str) -> bool` — verify the profile exists in `list_saved_networks()` output by `connection_name` (single enumeration, used only to detect the `current` flag and existence), disconnect first if current, then `nmcli connection delete <connection_name>`.
- Route: `DELETE /api/wifi/saved/{connection_name:path}` (string path param, URL-encoded by the client; `:path` tolerates names with slashes). 404 when no saved profile has that name. The saved-list payload already includes `connection_name` per entry (wifi_manager.py:606-618), so no response change.
- Frontend: `forgetNetwork` in wifi.svelte.ts sends `encodeURIComponent(network.connection_name)` instead of `network.id`. The numeric `id` field can remain in the payload for now (UI keys/ordering) — dropping it is optional cleanup.
- *Alternative — key by NM connection UUID*: more canonical, but `list_saved_networks` doesn't currently fetch UUIDs and the name is already the exact argument `nmcli connection delete` uses today. Connection names are unique in NetworkManager. Name chosen.

### D4: Metrics use the injected WiFiManager

`get_system_metrics` reads the module-level manager set by `set_system_wifi_manager()`. If none was injected (unit tests, unusual startup), skip the WiFi block and log once at debug — do not construct a fallback `WiFiManager`, which is exactly the waste being removed. This removes the local `WiFiManager` import and ~2,900 subprocess spawns/hour per WS client.

### D5: Honest responses — await the action (synchronous truth)

Chosen semantics: **await**, not "202 accepted".

- `POST /api/radio/volume`: replace `background_tasks.add_task(radio_manager.set_volume, actual_volume)` with `ok = await radio_manager.set_volume(actual_volume)`; return `success=ok`, 500 (or `success=False` with error message) when the volume backend fails. `set_volume` is a fast `pactl`/`amixer` call — no latency concern.
- `POST /api/radio/stations/{slot}/play`: compute the intended action from `get_status()` **before** mutating, then `playing = await radio_manager.toggle_station(slot)`; respond with the actual resulting state (`action: "started"|"stopped"`, `is_playing`). `toggle_station` returns as soon as mpg123 is spawned or stopped — bounded latency (sub-second in practice). Response truthfully covers "the player state changed"; ongoing stream health remains a WebSocket concern.
- `BackgroundTasks` parameters removed from both handlers.
- *Alternative — truthful 202 semantics*: keep background execution, return `accepted` + queued action. Rejected: the actions are fast, the frontend treats the response as an outcome today, and awaiting is the smaller honest change.

### D6: WebSocket broadcast — per-send timeout + consistent locking

- Wrap each send in `asyncio.wait_for(connection.send_text(...), timeout=SEND_TIMEOUT)` with `SEND_TIMEOUT = 1.0` s (module constant). Timeout or exception marks the connection failed; it is dropped in the existing cleanup pass so one stalled client can no longer block or break the loop for others.
- Take a snapshot of `active_connections` *under* `self._lock` at the top of `broadcast` (and in `get_connection_stats` if it iterates), then send outside the lock (never hold the lock across `await send`), and reuse the existing locked cleanup block. `send_personal_message`'s membership check/disconnect path follows the same rule.
- Sends may be gathered concurrently (`asyncio.gather` over per-connection send coroutines) so total broadcast time is bounded by the slowest client up to the timeout, not the sum. Concurrency is an implementation choice; the requirement is only per-send timeout + isolation.

## Risks / Trade-offs

- [Awaiting toggle adds latency when a stream URL is slow to spawn] → `toggle_station` only waits for process start, not stream validation; existing route tests assert response shape, which is preserved.
- [Startup now fails hard when `RadioManager._initialize()` raises] → intended: a crash-looping container with logs beats a silently broken API. `_initialize` already swallows hardware-only errors in mock/degraded paths.
- [Connection names with special characters in the URL] → route uses a `:path` converter and the frontend URL-encodes; test with spaces and slashes.
- [Frontend/backed contract skew during deploy] → none in practice: both ship in one image.
- [1.0 s send timeout could drop a merely-slow client on a congested WLAN] → the client's own reconnect logic re-establishes the socket and receives full state on connect (existing behavior).

## Migration Plan

Single deploy (one image). No data migration. Rollback = previous image tag. The forget-network API change needs no external migration: the only caller is the bundled frontend.

## Open Questions

None — semantics decisions (await vs. accepted; name vs. UUID) are made above.
