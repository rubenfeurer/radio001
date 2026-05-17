## ADDED Requirements

### Requirement: Read current settings
The system SHALL expose a `GET /api/system/settings` endpoint that returns the current values of all allowlisted config fields read directly from `radio.conf`.

#### Scenario: Successful read
- **WHEN** a GET request is made to `/api/system/settings`
- **THEN** the response is HTTP 200 with a JSON object containing all allowlisted field names and their current values

#### Scenario: Config file missing
- **WHEN** `radio.conf` cannot be read
- **THEN** the response is HTTP 500 with an error message

---

### Requirement: Write settings with validation
The system SHALL expose a `PUT /api/system/settings` endpoint that accepts a partial JSON object of allowlisted fields, validates each value, writes changed fields back to `radio.conf` (preserving comments and structure), and returns which fields were changed and which require restart.

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

#### Scenario: Volume range consistency
- **WHEN** a PUT request sets MIN_VOLUME > DEFAULT_VOLUME or DEFAULT_VOLUME > MAX_VOLUME
- **THEN** the response is HTTP 422 with an error explaining the ordering constraint

#### Scenario: Concurrent write protection
- **WHEN** two PUT requests arrive simultaneously
- **THEN** a file lock ensures writes are serialised and neither request corrupts the file

---

### Requirement: Allowlisted fields only
The system SHALL maintain an explicit allowlist of config keys that may be read or written via the settings API. Keys outside the allowlist MUST NOT appear in GET responses or be accepted in PUT requests.

Allowlisted fields:
- `HOTSPOT_SSID`, `HOTSPOT_PASSWORD`
- `DEFAULT_VOLUME`, `MIN_VOLUME`, `MAX_VOLUME`, `NOTIFICATION_VOLUME`
- `ROTARY_CLOCKWISE_INCREASES`, `ROTARY_VOLUME_STEP`, `ROTARY_DEBOUNCE`
- `LONG_PRESS_DURATION`, `TRIPLE_PRESS_INTERVAL`

#### Scenario: Allowlist enforced on GET
- **WHEN** a GET request is made
- **THEN** the response contains exactly the allowlisted fields and no others

#### Scenario: Allowlist enforced on PUT
- **WHEN** a PUT request includes a non-allowlisted key such as `BUTTON_PIN_1`
- **THEN** that key is ignored and no error is returned

---

### Requirement: Restart-required metadata
The system SHALL know which fields require a container restart to take effect and SHALL return this information in PUT responses.

Fields requiring restart: all fields (hardware and audio settings take effect at startup).

#### Scenario: Restart required fields returned
- **WHEN** a PUT request successfully changes one or more fields
- **THEN** the response includes a `restart_required` list containing the names of changed fields that need restart
