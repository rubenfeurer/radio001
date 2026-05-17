## Context

`WiFiManager.connect_network` checks for an existing NM connection profile with `ssid in check_stdout.decode()` — a raw substring match against `nmcli -t -f NAME connection show` output. NetworkManager may store a connection under a name that contains but does not equal the SSID (e.g., "froschland 1" when "froschland" already existed), causing the subsequent `nmcli connection up <ssid>` to fail with "unknown connection". `forget_network` has the same flaw: it calls `nmcli connection delete <ssid>` instead of using the `connection_name` field that `list_saved_networks` already resolves.

The frontend has two gaps: the currently-connected dialog shows a redundant "Close" button alongside "Forget Network", and saved-but-not-current networks have no forget option at all.

## Goals / Non-Goals

**Goals:**
- Exact-name lookup for NM connection profiles before `connection up` or `connection delete`
- Allow forgetting the currently connected network (disconnect wlan0, then delete profile)
- Frontend: currently-connected → only Forget Network button
- Frontend: saved-not-current → Forget Network button added

**Non-Goals:**
- Changing scan logic, hotspot mode, or any other WiFi path
- Adding a new "disconnect without forget" action

## Decisions

**D1: Resolve connection name before `connection up`**
Instead of the substring check, `connect_network` will call `list_saved_networks()` to get the authoritative `connection_name` for the requested SSID. If a match is found, use that name for `modify` and `up`; if not found, fall through to `nmcli device wifi connect`. This reuses existing logic without duplicating nmcli queries.

**D2: `forget_network` uses `connection_name`, not SSID**
The `target_network` dict from `list_saved_networks` already includes `connection_name`. Pass that to `nmcli connection delete` instead of `ssid`.

**D3: Allow forgetting the currently connected network**
Remove the guard in `wifi_manager.forget_network` and the HTTP 400 in `wifi.py`. When deleting the current connection, call `nmcli device disconnect wlan0` first so the interface drops gracefully before the profile is deleted.

**D4: Frontend dialog simplification**
`isCurrent` state: remove the "Close" button — the user opened the dialog to act on the network, not close it. "Forget Network" remains with its existing confirmation flow.  
`isSaved` state: add a "Forget Network" button that triggers `confirmingForget` state, matching the same confirmation pattern used for current networks.

## Risks / Trade-offs

- **Losing connectivity on forget-current**: Intentional — user explicitly chose to forget. Mitigation: existing confirmation dialog ("Are you sure?") stays in place.
- **Race condition on list_saved_networks lookup in connect_network**: Negligible — connection list is stable during a connect attempt.
