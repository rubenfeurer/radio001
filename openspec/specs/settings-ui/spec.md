## ADDED Requirements

### Requirement: Settings page loads current config
The settings page at `/settings` SHALL fetch current values from `GET /api/system/settings` on load and populate all form fields with those values.

#### Scenario: Page loads successfully
- **WHEN** the user navigates to `/settings`
- **THEN** all form fields display the current values from `radio.conf`

#### Scenario: Load fails
- **WHEN** the GET request fails
- **THEN** an error message is shown and form fields remain empty/disabled

---

### Requirement: Grouped settings form
The settings page SHALL present fields in three named groups: **Hotspot**, **Volume**, and **Encoder**. Each group is visually separated. All fields in a group are editable inline.

Hotspot group: SSID (text), Password (text, masked by default with show/hide toggle)
Volume group: Default Volume (number 0–100), Min Volume (number 0–100), Max Volume (number 0–100), Notification Volume (number 0–100)
Encoder group: Clockwise Increases Volume (toggle/checkbox), Volume Step (number 1–20), Debounce (number, seconds)

#### Scenario: All groups rendered
- **WHEN** settings load successfully
- **THEN** the page shows three groups with the correct fields in each

#### Scenario: Password visibility toggle
- **WHEN** the user clicks the show/hide icon on the password field
- **THEN** the password toggles between masked and visible

---

### Requirement: Save settings
The settings page SHALL have a Save button that sends changed fields to `PUT /api/system/settings`. Only fields that differ from the loaded values are sent.

#### Scenario: Successful save
- **WHEN** the user edits one or more fields and clicks Save
- **THEN** a PUT request is made with only the changed fields
- **THEN** a success message is briefly shown

#### Scenario: Validation error from API
- **WHEN** the PUT response is HTTP 422
- **THEN** the validation error message is displayed inline near the relevant field

#### Scenario: No changes
- **WHEN** the user clicks Save without changing anything
- **THEN** no request is made

---

### Requirement: Restart required banner
After a successful save, if the API response includes any fields in `restart_required`, the page SHALL show a persistent banner: "Settings saved. Restart required for changes to take effect." with a Restart button.

#### Scenario: Banner shown after save with restart-required fields
- **WHEN** a successful PUT response includes `restart_required` with one or more fields
- **THEN** a sticky banner appears at the top of the page with a Restart button

#### Scenario: Restart button triggers restart
- **WHEN** the user clicks Restart in the banner
- **THEN** a POST request is made to `/api/system/restart`
- **THEN** the UI shows "Restarting…" and the banner is dismissed

#### Scenario: Banner dismissed without restart
- **WHEN** the user dismisses the banner without clicking Restart
- **THEN** the banner is removed and no restart request is made
