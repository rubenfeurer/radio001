## MODIFIED Requirements

### Requirement: Station Library Availability
The system SHALL include the radio station library file inside the Docker image so that the library endpoint is functional without external volume mounts or manual file placement.

#### Scenario: Station library present in Docker image
- **WHEN** the Docker image is built
- **THEN** the station library JSON file SHALL be present at `/app/assets/stations.json` inside the image
- **AND** the file SHALL contain the full list of radio stations

#### Scenario: Station library endpoint returns data
- **WHEN** the frontend calls `/api/radio/library`
- **THEN** the backend SHALL return a list of radio stations from the library file
- **AND** SHALL NOT return a 404 response due to a missing file

#### Scenario: Station library endpoint reachable in production
- **WHEN** a user navigates to the station selection page in production
- **THEN** the frontend SHALL successfully fetch the station library from `/api/radio/library`
- **AND** the list of stations SHALL be displayed for selection

### Requirement: WiFi Scan Endpoint Reachable
The system SHALL expose the WiFi scan endpoint under the `/api` prefix so that network scan requests from the frontend reach the FastAPI handler in production.

#### Scenario: WiFi scan works in production
- **WHEN** the frontend calls `/api/wifi/scan`
- **THEN** FastAPI SHALL route the request to the WiFi scan handler
- **AND** SHALL return available networks as JSON
- **AND** SHALL NOT return an HTML or 404 response
