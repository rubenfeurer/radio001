## Why

Two related bugs make saved-network management unreliable, and the UI flow for saved/connected networks is incomplete. When connecting to a saved network the backend throws "Error: unknown connection '<ssid>'" because it checks for an existing NM connection profile with a substring match rather than an exact name lookup — NM sometimes stores the profile under a slightly different name (e.g., "froschland 1"). `forget_network` has the same flaw, using SSID instead of the NM connection name for deletion. On the frontend, the currently-connected-network dialog shows a "Close" button that adds noise, and saved (non-current) networks have no Forget option at all.

## What Changes

- **BREAKING** (backend): `forget_network` no longer blocks forgetting the currently connected network — it disconnects first, then deletes
- Fix `connect_network`: replace substring check with exact-line match; look up the NM connection name before calling `nmcli connection up <name>`
- Fix `forget_network`: use `connection_name` (not SSID) when calling `nmcli connection delete`
- Remove `wifi.py` guard that returns HTTP 400 on forget-current-network
- Frontend: currently-connected dialog → show only "Forget Network" button
- Frontend: saved-but-not-current dialog → add "Forget Network" button alongside Connect

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `wifi-management`: Connection resolution must use exact NM name match; forget-current-network must disconnect then delete (removing the previous prohibition)

## Impact

- `backend/core/wifi_manager.py` — `connect_network`, `forget_network`
- `backend/api/routes/wifi.py` — remove forget-current-network guard
- `frontend/src/routes/setup/+page.svelte` — dialog UI for isCurrent and isSaved states
