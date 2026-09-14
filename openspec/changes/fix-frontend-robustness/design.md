# Design — fix-frontend-robustness

## Context

The SvelteKit frontend has a single module-level `WebSocketClient` (`frontend/src/lib/stores/websocket.svelte.ts`) shared by all routes. Two bugs interact:

1. `disconnect()` sets `shouldReconnect = false` (line 80) and nothing ever sets it back to `true` — `connect()` doesn't. The only caller of `disconnect()` is `/status`'s `onDestroy`. After one visit to `/status`, any later socket drop is permanent for the SPA session: `onclose` sees `shouldReconnect === false` and never schedules a reconnect.
2. `connect()` returns early only when `readyState === OPEN` (line 18). If called while a socket is `CONNECTING` (e.g. reconnect timer fires, then the user navigates and `onMount` calls `connect()`), the in-flight socket is overwritten but its `onopen`/`onclose`/`onmessage` handlers stay live — duplicate traffic, `wsState` flapping, and stray reconnect scheduling.

Separately, the API-calling stores swallow failures: `radio.svelte.ts` `toggleStation`/`stopPlayback`/`setVolume` never check `response.ok` and expose no error state, so a backend 500 is indistinguishable from success. The stations picker (`routes/stations/+page.svelte`) does the same and `goto('/')` unconditionally, and parses `?slot=` with a bare `parseInt` (NaN reaches the URL of a POST). The settings volume slider (`routes/settings/+page.svelte:124-127`) POSTs on every `input` event, and the backend's `volume_update` WS broadcast echoes into `updateVolume()`, snapping the `value={radioState.volume}`-bound slider backwards mid-drag.

Constraints: frontend-only change; Svelte 5 runes state modules; no new dependencies; mock mode on macOS must keep working.

## Goals / Non-Goals

**Goals:**
- WebSocket reconnection survives the full SPA session regardless of navigation history; no orphaned sockets.
- Failed playback/volume/station-assignment requests are visible to the user.
- Volume slider is smooth under drag: bounded request rate, no echo snap-back.
- Remove the dead `/status` route and unused components; dedupe format helpers.

**Non-Goals:**
- No backend changes (the "API returns success before the background task runs" issue is a separate backend concern).
- No rewrite of the stale `homepage-radio-controls` spec prose — owned by `cleanup-dead-code-and-docs`.
- No offline queueing/retry of failed POSTs; surfacing the error is enough.

## Decisions

### D1: Reset `shouldReconnect` in `connect()`
`connect()` sets `this.shouldReconnect = true` at the top. Rationale: `connect()` is the caller's statement of intent ("I want a live connection"), so it must undo a prior `disconnect()`. Alternative considered: delete `disconnect()` entirely once `/status` (its only caller) is removed — rejected: keeping a correct `disconnect()` is cheap and future page lifecycles may need it; the reset in `connect()` makes the pair safe in any order.

### D2: Guard both OPEN and CONNECTING in `connect()`
Early-return when `readyState` is `OPEN` **or** `CONNECTING`. Rationale: an in-flight handshake will resolve to open or close on its own; creating a second socket while one is connecting is the orphaning bug. Alternative: tear down the old socket and always create a fresh one — rejected, causes needless churn and still flaps `wsState`.

### D3: Exponential reconnect backoff with cap
Replace the fixed 3 s delay with exponential backoff (e.g. 1 s base, doubling, capped at ~30 s), reset to base on successful `onopen`. Rationale: a down backend on a Pi shouldn't be hammered every 3 s forever, and a jittery network recovers fast with a small base. Kept private to the class; no API change.

### D4: Ping-based liveness
On `onopen`, start a periodic ping (reusing the existing `{type: 'ping'}`/`pong` protocol the handler already knows — `pong` case exists at `websocket.svelte.ts:131`). If no `pong` (or any message) arrives within a timeout, force-close the socket so the normal `onclose` → reconnect path runs. Timers are cleared in `onclose`/`disconnect()`. Rationale: detects half-open TCP connections (common on WiFi/hotspot transitions on the Pi) that otherwise look connected forever. Alternative: rely on browser TCP keepalive — rejected, not exposed/reliable.

### D5: Error state lives in the radio store, displayed by pages
Add `radioState.error: string | null`. `toggleStation`/`stopPlayback`/`setVolume` check `response.ok`, set a short human message on failure (and on thrown fetch errors), and clear it on the next successful action. Homepage renders it (same destructive-tinted pattern already used for `wifiState.error` / `settingsState.error`). Rationale: matches the established per-store error pattern in this codebase; avoids introducing a toast library (no new dependency).

### D6: Stations page — validate slot, stay on failure
- Parse `?slot=` once: must be an integer in the valid slot range (1–3); otherwise treat as no slot (browse-only mode) — never emit a request URL containing `NaN`.
- `selectStation` checks `response.ok` on the assign POST; only navigates home after a successful assignment, otherwise shows an inline error and re-enables the list. The follow-up `/play` call failing is surfaced but non-blocking (assignment succeeded — homepage will reflect actual state).

### D7: Volume slider — throttle + drag-guard
- Throttle/debounce the POST from `handleVolumeInput` (~150–250 ms trailing) so a drag produces a bounded request stream with a final accurate value.
- Track dragging (`pointerdown`/`input` … `pointerup`/`change`) and suppress applying WS `volume_update` echoes to the slider's bound value while dragging (short grace period after release for in-flight echoes). Implemented in the store (`updateVolume` no-ops while a "user is adjusting" flag is set) so both homepage and settings sliders benefit. Alternative: unbind the slider from store state entirely — rejected, loses legitimate external updates (rotary encoder turns must still move the on-screen slider when idle).

### D8: Deletions and dedupe
- Delete `routes/status/+page.svelte` (unlinked — no `href="/status"`/`goto('/status')` anywhere; duplicates settings cards; sole `disconnect()` caller).
- Delete `lib/components/SignalStrength.svelte` and `lib/components/ui/separator/` (zero imports).
- Delete `card-description.svelte` and `card-footer.svelte` and drop their exports from `ui/card/index.ts`; keep `CardHeader`/`CardTitle` (used by `/setup`).
- New `frontend/src/lib/format.ts` exporting `formatUptime`/`formatBytes`; settings page imports it (status page copy dies with the route).

## Risks / Trade-offs

- [Throttling delays the final volume POST slightly] → trailing-edge flush guarantees the last slider value is always sent; delay is imperceptible (<250 ms).
- [Suppressing WS echoes while dragging could hide a genuine concurrent rotary-encoder change] → suppression window is only while actively dragging + short grace; the next status fetch/WS update reconciles.
- [Backend may not answer `ping` with `pong` as assumed] → verify against `backend` WS handler during implementation; if absent, treat any inbound message as liveness and lengthen the timeout, or drop D4's forced close to log-only.
- [Delta overlap with `cleanup-dead-code-and-docs` on `homepage-radio-controls`] → this change only ADDs new requirements (reconnect resilience, error surfacing); the prose rewrite stays in the other change. Archive order: whichever lands second rebases its delta trivially.

## Migration Plan

Pure frontend refactor inside one image: merge to `develop`, CI lint/type check, then `main` → `:latest` for test-Pi verification. Rollback = revert commit. No data or config migration.

## Open Questions

- Does the backend WS handler respond to `{type: 'ping'}` with `pong`? (Handler `pong` case suggests yes — confirm during implementation; fall back per D4 risk note.)
