# Design — harden-api-security

## Context

The API is intentionally unauthenticated (accepted LAN trust model), so input handling is the only defence layer. Three medium-severity issues from the September 2026 review:

1. **Config injection**: `PUT /api/system/settings` (`backend/api/routes/settings.py`) writes request values verbatim into `radio.conf` via `f"{key}={new_val}\n"` (`_write_conf`, line 99). `_load_radio_conf()` in `backend/main.py` parses every `KEY=VALUE` line into `os.environ` at startup, so a value like `"x\nWIFI_INTERFACE=eth0"` injects arbitrary environment keys at next boot. Existing Pydantic validators cover ranges/min-length only — no newline, length, or charset constraints on strings.
2. **Non-durable writes**: `_write_conf` rewrites `radio.conf` in place (`seek(0)` / `writelines` / `truncate` under `fcntl.flock`). Power loss mid-write leaves a truncated or interleaved file. `backend/core/station_manager.py` already solves this for `stations.json` with `.tmp` + `Path.replace` (lines 125–130).
3. **PSK/SSID handling in `wifi_manager.py` (`connect_network`)**: the saved-profile path runs `nmcli connection modify <name> ... wifi-sec.psk <password>` and the new-network path runs `nmcli device wifi connect <ssid> password <password>`. The password is visible in `/proc/<pid>/cmdline` to any local process for the lifetime of the nmcli call. The SSID is passed positionally, so an API-supplied SSID beginning with `-` can be consumed as an nmcli option.

## Goals / Non-Goals

**Goals:**
- Reject any settings string value containing `\n`/`\r`; cap string lengths; restrict `HOTSPOT_SSID`/`HOTSPOT_PASSWORD` charset to printable ASCII.
- Atomic `radio.conf` writes (temp file in same directory + rename), preserving comments/structure and concurrency safety.
- WiFi PSKs never appear in spawned process argv on either connect path.
- API-supplied SSIDs validated and passed to nmcli in a position-safe form so a leading `-` cannot be parsed as an option.
- Tests covering each of the above.

**Non-Goals:**
- Authentication, rate limiting, or hiding `/docs` (accepted no-auth LAN model).
- Hotspot password generation (separate change).
- Changes to `_load_radio_conf()` parsing in `backend/main.py`.
- Changing the settings API surface (endpoints, field names, response shapes).

## Decisions

### D1: Validate at the Pydantic layer, reject with 422 (not sanitize)

Add validators to `SettingsPayload`:
- A shared validator on all `str` fields (`HOTSPOT_SSID`, `HOTSPOT_PASSWORD`) rejecting `\n` and `\r` (and other C0 control characters) anywhere in the value.
- Length caps aligned with 802.11/WPA2: `HOTSPOT_SSID` 1–32 bytes, `HOTSPOT_PASSWORD` 8–63 characters (WPA2-PSK passphrase bounds; the 8-char minimum already exists).
- Charset restriction to printable ASCII (`0x20`–`0x7E`) for both fields — hostapd/NM SSIDs technically allow more, but this device generates its own hotspot, so the restriction is safe and eliminates `#`/newline/quote ambiguity in the conf file parseback.

*Why reject over sanitize:* silent stripping would store a value different from what the client sent and confirmed; a 422 with a clear message is consistent with the existing validator behaviour (spec scenario "Invalid value rejected").

*Alternative considered:* escaping values in `_write_conf`. Rejected — `_load_radio_conf()` and the shell `source`-style consumers have no unescape step, so escaping would change stored semantics. Defence-in-depth: `_write_conf` additionally asserts no `\n`/`\r` in any value before writing (belt-and-braces against future call sites), raising rather than writing a corrupt file.

### D2: Atomic conf write mirroring `station_manager.py`

Rewrite `_write_conf` to: read the original, build the new content in memory (same line-preserving logic), write it to `radio.conf.tmp` in the **same directory** (same filesystem → atomic rename), `flush()` + `os.fsync()`, copy the original file's mode, then `Path.replace()` over `radio.conf`. Concurrency: keep serialising writers — take the exclusive `fcntl.flock` on the *original* file (or a dedicated lock file) for the whole read→write→rename sequence so two PUTs cannot interleave. Readers (`_read_conf`) are unaffected: rename is atomic, so they see either the old or the new complete file.

*Alternative considered:* `tempfile.NamedTemporaryFile(delete=False)` in `/tmp`. Rejected — cross-filesystem rename is not atomic; temp file must live next to the target (as `station_manager.py` does).

### D3: PSKs via `passwd-file`, never argv

Unify both connect paths on NetworkManager's `passwd-file` mechanism:
- Write the secret to a private temp file (created with `0600` via `os.open(..., 0o600)`/`tempfile.NamedTemporaryFile`) containing `802-11-wireless-security.psk:<password>`, pass its **path** to nmcli, and delete it in a `finally` block.
- **Saved-profile path**: drop the `connection modify ... wifi-sec.psk <pw>` call; run `nmcli connection up <connection_name> passwd-file <path>`. NM stores the supplied secret on the profile under default `psk-flags`, preserving the current "update stored password" behaviour.
- **New-network path**: replace `nmcli device wifi connect <ssid> password <pw>` with `nmcli connection add type wifi con-name <name> ifname <iface> ssid <ssid> wifi-sec.key-mgmt wpa-psk`, then `nmcli connection up <name> passwd-file <path>`. On activation failure, delete the just-created profile so failed attempts don't accumulate half-configured profiles (matching current behaviour where a failed `device wifi connect` leaves no usable saved network).
- Open networks keep the current no-password flow (`connection add` without security + `connection up`).

*Alternative considered:* `nmcli --ask` with the password piped to stdin. Workable, but `--ask` behaviour is prompt-driven and brittle in non-tty subprocess use; `passwd-file` is the documented scripting mechanism. The temp file is `0600` and short-lived — strictly better than world-readable `/proc/<pid>/cmdline`.

### D4: SSID validation + position-safe nmcli invocation

Two layers:
1. **Validation** (in `wifi_manager.connect_network`, before any subprocess; also applies to the API model if one exists for the connect endpoint): non-empty, ≤ 32 bytes UTF-8, no `\n`/`\r`/other control characters. Reject with a clear error.
2. **Position safety**: with D3, the SSID is only ever passed as the value following the `ssid` property keyword in `nmcli connection add ... ssid <value>` — nmcli treats the token after a property name as a value, never as an option — so an SSID beginning with `-` is handled correctly rather than rejected (real SSIDs may start with `-`).

The `connection up` path already uses the NM `connection_name` (resolved from `list_saved_networks()`), not the raw SSID.

### D5: Tests

Extend `backend/tests/` (pytest, existing FastAPI TestClient + monkeypatch conventions):
- Settings: PUT with `"x\nWIFI_INTERFACE=eth0"` in `HOTSPOT_SSID`/`HOTSPOT_PASSWORD` → 422 and conf file unchanged; `\r` variant; over-length SSID (33 chars) and password (64 chars) → 422; non-printable charset → 422; valid values still accepted.
- Atomic write: after a successful PUT, conf is complete and correct; `_write_conf` produces the result via rename (assert no lingering `.tmp`, and simulate a failure between write and rename → original intact).
- WiFi: monkeypatch `asyncio.create_subprocess_exec` to capture argv; assert the PSK string appears in **no** captured argv on both paths; assert the passwd-file passed to nmcli had `0600` perms and is deleted afterwards; SSID `-foo` reaches nmcli only as the token after `ssid`; control-character SSID rejected before any subprocess is spawned.

## Risks / Trade-offs

- [NM version differences in `passwd-file`/secret-persistence behaviour] → The Pi runs NetworkManager on Raspberry Pi OS (trixie); `passwd-file` for `connection up` has been stable since NM 1.x. Verify on the test Pi (`ssh radio-d`) before release; the `:latest` channel exists for exactly this.
- [Behaviour change: previously-accepted values now return 422] → Only values that were already corrupting or attacking the conf file; the frontend never generates them. Documented in proposal Impact.
- [`connection add` + `up` replaces one nmcli call with two on the new-network path] → Slightly more failure states; mitigated by deleting the profile when activation fails and surfacing nmcli stderr as today.
- [Temp passwd-file could linger after a crash] → Created inside a `finally`-cleaned scope in a private location; worst case is a `0600` file readable only by the container user — still strictly better than argv exposure.
- [Stricter SSID/password charset could reject exotic-but-legal values] → Applies only to the device's own hotspot settings (values we generate/control), not to joining external networks.

## Open Questions

None blocking. One item to verify during implementation on the test Pi: that a secret supplied via `passwd-file` on `connection up` is persisted to the profile under the default `psk-flags` (expected NM behaviour), so subsequent reconnects work without re-entering the password.
