# Harden API Security

## Why

The September 2026 project review found three medium-severity input-handling flaws in the unauthenticated LAN API. Settings values are written verbatim into `radio.conf` (`backend/api/routes/settings.py:99`), so a value containing a newline (e.g. `"x\nWIFI_INTERFACE=eth0"`) injects arbitrary config keys that `_load_radio_conf()` in `backend/main.py` loads into `os.environ` at next boot. WiFi PSKs are passed as `nmcli` argv (`backend/core/wifi_manager.py:409-421`, `:444-455`), making them readable in `/proc/<pid>/cmdline` by any local process. API-supplied SSIDs are passed positionally to `nmcli` (`wifi_manager.py:450`), so an SSID starting with `-` can be parsed as an nmcli flag. Additionally, `radio.conf` writes rewrite the file in place with seek/truncate — power loss mid-write corrupts the config.

## What Changes

- Add Pydantic validators on the settings payload rejecting `\n`/`\r` in all string fields, capping string lengths, and restricting the charset of `HOTSPOT_SSID` (and similar fields) to safe characters.
- Make `radio.conf` writes atomic: write to a temp file in the same directory, then `rename`/`replace` over the original — matching the pattern already used in `backend/core/station_manager.py` (`.tmp` + `Path.replace`).
- Stop passing WiFi PSKs in `nmcli` argv: supply secrets via stdin (`nmcli --ask`) or a mode-0600 `passwd-file`, for both the "modify existing profile" and "connect new network" paths.
- Sanitize API-supplied SSIDs (reject leading `-`, control characters, over-length values) and/or use position-safe nmcli forms so an SSID can never be interpreted as an nmcli option.
- Add tests: newline rejection, length caps, atomic write behavior, SSID starting with `-` handled safely, and an assertion that the PSK never appears in the constructed subprocess argv.

Explicitly out of scope (no-auth LAN model is accepted by design): adding authentication, hiding `/docs`, hotspot password generation (covered by another change).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `settings-api`: the "Write settings with validation" requirement gains input-hardening constraints (reject `\n`/`\r`, length caps, SSID charset) and the write is required to be atomic (temp file + rename) instead of in-place seek/truncate.
- `wifi-management`: the connection requirements change so PSKs are never passed via process argv and API-supplied SSIDs are validated/passed in a position-safe way before reaching nmcli.

## Impact

- `backend/api/routes/settings.py` — new field validators, `_write_conf` rewritten to atomic temp-file + rename.
- `backend/core/wifi_manager.py` — `connect_network()` PSK handling (both modify and connect paths) and SSID validation.
- `backend/tests/` — new tests for validators, atomic write, SSID handling, and argv secrecy.
- No API surface changes (same endpoints, same fields); previously-accepted malicious values now return HTTP 422.
- No changes to `backend/main.py`, deployment, or dependencies.
