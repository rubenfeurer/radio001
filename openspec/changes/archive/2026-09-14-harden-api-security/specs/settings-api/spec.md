## MODIFIED Requirements

### Requirement: Write settings with validation
The system SHALL expose a `PUT /api/system/settings` endpoint that accepts a partial JSON object of allowlisted fields, validates each value, writes changed fields back to `radio.conf` atomically (preserving comments and structure), and returns which fields were changed and which require restart.

String field values MUST be validated before writing:
- Values containing `\n`, `\r`, or any other control character MUST be rejected.
- `HOTSPOT_SSID` MUST be 1–32 bytes and `HOTSPOT_PASSWORD` MUST be 8–63 characters.
- `HOTSPOT_SSID` and `HOTSPOT_PASSWORD` MUST contain only printable ASCII characters (0x20–0x7E).

Writes to `radio.conf` MUST be atomic: the new content is written to a temporary file in the same directory and then renamed over `radio.conf`, so that at no point does a partially written config file exist on disk.

#### Scenario: Valid partial update
- **WHEN** a PUT request is made with a valid subset of allowlisted fields
- **THEN** the response is HTTP 200 with `{ changed: [...], restart_required: [...] }`
- **THEN** only those keys are updated in `radio.conf`; all other lines are preserved unchanged

#### Scenario: Unknown field ignored
- **WHEN** a PUT request includes a field not in the allowlist
- **THEN** that field is silently ignored; allowlisted fields in the same request are applied normally

#### Scenario: Invalid value rejected
- **WHEN** a PUT request includes an allowlisted field with an invalid value (e.g. password shorter than 8 chars, volume out of 0–100)
- **THEN** the response is HTTP 422 with a validation error describing the constraint

#### Scenario: Newline injection rejected
- **WHEN** a PUT request includes a string field whose value contains `\n` or `\r` (e.g. `"x\nWIFI_INTERFACE=eth0"`)
- **THEN** the response is HTTP 422 with a validation error
- **THEN** `radio.conf` is not modified and no injected key can be loaded into the environment at next boot

#### Scenario: Over-length string rejected
- **WHEN** a PUT request sets `HOTSPOT_SSID` longer than 32 bytes or `HOTSPOT_PASSWORD` longer than 63 characters
- **THEN** the response is HTTP 422 with a validation error describing the length limit

#### Scenario: Disallowed characters rejected
- **WHEN** a PUT request sets `HOTSPOT_SSID` or `HOTSPOT_PASSWORD` containing characters outside printable ASCII (0x20–0x7E)
- **THEN** the response is HTTP 422 with a validation error describing the allowed character set

#### Scenario: Volume range consistency
- **WHEN** a PUT request sets MIN_VOLUME > DEFAULT_VOLUME or DEFAULT_VOLUME > MAX_VOLUME
- **THEN** the response is HTTP 422 with an error explaining the ordering constraint

#### Scenario: Concurrent write protection
- **WHEN** two PUT requests arrive simultaneously
- **THEN** a file lock ensures writes are serialised and neither request corrupts the file

#### Scenario: Atomic write survives interruption
- **WHEN** the write process is interrupted (e.g. power loss or crash) between generating the new content and completing the write
- **THEN** `radio.conf` on disk is either the complete previous version or the complete new version, never truncated or partially written
