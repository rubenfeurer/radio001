# dockerfile-accuracy Delta — cleanup-dead-code-and-docs

## MODIFIED Requirements

### Requirement: Docker compose mounts use canonical file locations
Docker compose volume mounts SHALL reference the single canonical location for each file, not copies created to work around missing mounts. The canonical station library is `backend/assets/stations.json`, baked into the production image via `COPY backend/ .`.

#### Scenario: Station library comes from backend assets
- **WHEN** the backend container starts in development
- **THEN** the station library SHALL be provided by the `../backend:/app` source mount at `/app/assets/stations.json`
- **AND** `docker/compose.dev.yml` SHALL NOT mount a separate `stations.json` from `config/`
- **AND** no `stations.json` copy SHALL exist at `config/stations.json`

#### Scenario: Sound files mounted from config
- **WHEN** the backend container starts in development
- **THEN** sound files MAY be overlaid from the `../config/sounds/` mount in `docker/compose.dev.yml`
- **AND** in production the sound files SHALL come from `backend/assets/sounds/` baked into the image

#### Scenario: Single Dockerfile per build target
- **WHEN** a Docker image is built for the backend
- **THEN** exactly one Dockerfile SHALL exist for that target (at `docker/Dockerfile.backend`)
- **AND** `backend/Dockerfile` SHALL not exist as a duplicate
