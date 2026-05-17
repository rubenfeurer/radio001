## 1. Fix connect_network — exact connection name resolution

- [x] 1.1 In `connect_network`, replace the substring check (`ssid in check_stdout.decode()`) with a call to `list_saved_networks()` that returns the exact `connection_name` for the given SSID
- [x] 1.2 If a matching saved network is found, use `connection_name` (not SSID) for `nmcli connection modify` and `nmcli connection up`; if not found, fall through to `nmcli device wifi connect`

## 2. Fix forget_network — use connection_name and allow current network

- [x] 2.1 In `forget_network`, change `nmcli connection delete <ssid>` to use `target_network["connection_name"]` instead
- [x] 2.2 Remove the guard that blocks forgetting the currently connected network; add `nmcli device disconnect <interface>` before delete when `target_network["current"]` is True

## 3. Remove API guard in wifi.py

- [x] 3.1 In `backend/api/routes/wifi.py` `forget_saved_network`, remove the HTTP 400 block that prevents forgetting the currently connected network

## 4. Frontend — currently-connected dialog

- [x] 4.1 In `setup/+page.svelte`, for the `isCurrent` dialog state, remove the "Close" button so only "Forget Network" remains (keep the existing confirmation flow)

## 5. Frontend — saved-not-current dialog

- [x] 5.1 In `setup/+page.svelte`, for the `isSaved` (non-current) dialog state, add a "Forget Network" button that sets `confirmingForget = true`; add the same confirmation sub-view used for the current-network forget flow
