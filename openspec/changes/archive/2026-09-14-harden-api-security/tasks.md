## 1. Settings input validation

- [x] 1.1 Add a shared field validator on `HOTSPOT_SSID` and `HOTSPOT_PASSWORD` in `SettingsPayload` (`backend/api/routes/settings.py`) rejecting `\n`, `\r`, and all other control characters
- [x] 1.2 Add length caps: `HOTSPOT_SSID` 1–32 bytes, `HOTSPOT_PASSWORD` 8–63 characters (keep existing 8-char minimum message)
- [x] 1.3 Restrict `HOTSPOT_SSID` and `HOTSPOT_PASSWORD` charset to printable ASCII (0x20–0x7E)
- [x] 1.4 Add defence-in-depth check in `_write_conf`: raise (do not write) if any update value contains `\n` or `\r`

## 2. Atomic radio.conf writes

- [x] 2.1 Rewrite `_write_conf` to build the new content in memory, write it to a `.tmp` file in the same directory, `flush()` + `os.fsync()`, preserve the original file mode, then `Path.replace()` over `radio.conf` (mirror `backend/core/station_manager.py` lines 125–130)
- [x] 2.2 Keep writer serialisation: hold the exclusive `fcntl.flock` on the original file (or a dedicated lock file) across the full read → write-tmp → rename sequence
- [x] 2.3 Clean up the `.tmp` file on any failure before the rename

## 3. WiFi PSK and SSID hardening

- [x] 3.1 Add SSID validation at the top of `connect_network` in `backend/core/wifi_manager.py`: reject empty, >32 bytes UTF-8, or control-character SSIDs before any subprocess is spawned
- [x] 3.2 Add a helper that writes `802-11-wireless-security.psk:<password>` to a mode-0600 temp file and guarantees deletion in a `finally` block
- [x] 3.3 Saved-profile path: remove the `nmcli connection modify ... wifi-sec.psk <password>` call; when a password is supplied, activate with `nmcli connection up <connection_name> passwd-file <path>` instead
- [x] 3.4 New-network path (secured): replace `nmcli device wifi connect <ssid> password <pw>` with `nmcli connection add type wifi con-name <name> ifname <iface> ssid <ssid> wifi-sec.key-mgmt wpa-psk` followed by `nmcli connection up <name> passwd-file <path>`; delete the created profile if activation fails
- [x] 3.5 New-network path (open): switch to `nmcli connection add ... ssid <ssid>` + `nmcli connection up <name>` so the SSID is always a property value, never positional

## 4. Tests

- [x] 4.1 Settings tests: PUT with `"x\nWIFI_INTERFACE=eth0"` and `\r` variants in string fields returns 422 and leaves `radio.conf` unchanged
- [x] 4.2 Settings tests: 33-byte SSID, 64-char password, and non-printable-ASCII values return 422; valid boundary values (32-byte SSID, 63-char password) are accepted
- [x] 4.3 Atomic write tests: successful PUT leaves no `.tmp` file and a complete conf; simulated failure between tmp-write and rename leaves the original conf intact
- [x] 4.4 WiFi tests: monkeypatch `asyncio.create_subprocess_exec` to capture argv; assert the PSK appears in no argv on both the saved-profile and new-network paths, and that the passwd-file was mode 0600 and is deleted afterwards
- [x] 4.5 WiFi tests: SSID `-foo` reaches nmcli only as the token after the `ssid` keyword; control-character SSID is rejected with no subprocess spawned

## 5. Verification

- [x] 5.1 Run the backend test suite and lint/type checks locally (mock mode)
- [ ] 5.2 On the test Pi (`ssh radio-d`, `:latest` image): connect to a real WPA2 network via the API and confirm the password is absent from `ps`/`/proc/<pid>/cmdline` during the attempt, and that a `passwd-file`-supplied secret is persisted so reconnect works without re-entering the password
