# Tasks — fix-frontend-robustness

## 1. Dead code removal and dedupe

- [x] 1.1 Create `frontend/src/lib/format.ts` exporting `formatUptime` and `formatBytes`; update `frontend/src/routes/settings/+page.svelte` to import them and delete its local copies (lines 108-122)
- [x] 1.2 Delete `frontend/src/routes/status/+page.svelte` (route directory); verify no `href`/`goto` references `/status` anywhere in `frontend/src`
- [x] 1.3 Delete `frontend/src/lib/components/SignalStrength.svelte` and `frontend/src/lib/components/ui/separator/` (both have zero imports)
- [x] 1.4 Delete `frontend/src/lib/components/ui/card/card-description.svelte` and `card-footer.svelte`; remove their exports from `frontend/src/lib/components/ui/card/index.ts` (keep `CardHeader`/`CardTitle` — used by `/setup`)

## 2. WebSocket client fixes (frontend/src/lib/stores/websocket.svelte.ts)

- [x] 2.1 Set `this.shouldReconnect = true` at the top of `connect()` so a prior `disconnect()` never permanently disables reconnection
- [x] 2.2 Change the `connect()` early-return guard to cover both `WebSocket.OPEN` and `WebSocket.CONNECTING` so an in-flight socket is never orphaned
- [x] 2.3 Replace the fixed 3 s `reconnectDelay` with exponential backoff (base ~1 s, doubling, cap ~30 s), reset to base in `onopen`
- [x] 2.4 Add ping/liveness: periodic `{type: 'ping'}` while open; verify the backend WS handler answers with `pong` (frontend handler already has a `pong` case) — if no liveness confirmation within the timeout, close the socket to trigger the normal reconnect path; treat any inbound message as liveness if the backend does not answer pings
- [x] 2.5 Clear ping/liveness timers in `onclose` and `disconnect()` alongside the reconnect timer

## 3. Error surfacing in radio store and pages

- [x] 3.1 Add `error: string | null` to `radioState` in `frontend/src/lib/stores/radio.svelte.ts`
- [x] 3.2 In `toggleStation`, `stopPlayback`, and `setVolume`: check `response.ok`, set a user-readable `radioState.error` on non-OK responses and on thrown fetch errors, and clear it on success
- [x] 3.3 Display `radioState.error` on the homepage (`frontend/src/routes/+page.svelte`) using the existing destructive-tinted error pattern (as used for `wifiState.error`)

## 4. Stations page robustness (frontend/src/routes/stations/+page.svelte)

- [x] 4.1 Validate `?slot=`: accept only integers in the valid slot range (1-3); treat anything else as no slot (browse-only) so no request URL can contain `NaN`
- [x] 4.2 In `selectStation`: check `response.ok` on the assignment POST; on failure show an inline error, re-enable the list, and do not navigate; only `goto('/')` after a successful assignment; surface (but don't block on) a failed follow-up `/play` request

## 5. Volume slider fix (frontend/src/routes/settings/+page.svelte)

- [x] 5.1 Throttle/debounce `handleVolumeInput` (~150-250 ms, trailing edge) so a drag sends a bounded request stream and the final released value is always sent
- [x] 5.2 Add a dragging flag (set on `pointerdown`/`input`, cleared on `pointerup`/`change` plus a short grace period) and suppress applying WS `volume_update` echoes to `radioState.volume` while it is set (guard in `updateVolume` in `radio.svelte.ts`), so external volume changes still move the slider when idle

## 6. Verification

- [x] 6.1 Run `npm run check` in `frontend/` — no type or Svelte errors (deleted components/routes leave no dangling imports)
- [x] 6.2 Run `npm run build` in `frontend/` — production build succeeds
- [ ] 6.3 Manual smoke test in dev (`docker compose -f docker/compose.dev.yml up`): drag the settings volume slider (no snap-back, throttled POSTs in network tab), kill/restart the backend and confirm the WS reconnects with backoff, open `/stations?slot=abc` and confirm no `NaN` request is sent
