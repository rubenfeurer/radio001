# dockerfile-accuracy Specification

## Purpose
Ensures Dockerfiles and compose files accurately reflect the project's actual dependencies, file locations, and build targets — no stale references, no duplicate files, no workaround copies.
## Requirements
### Requirement: Dockerfile Dependency Accuracy

The Dockerfile SHALL accurately reflect the actual system dependencies and SHALL NOT reference unused packages or missing files.

#### Scenario: Package Dependencies Match Reality

- **WHEN** the Dockerfile lists system packages in apt-get install
- **THEN** only packages that are actually used by the system SHALL be included
- **AND** packages that are not used SHALL be removed from the installation list
- **AND** the installed packages SHALL match what the running system actually requires

#### Scenario: Configuration File References

- **WHEN** the Dockerfile contains COPY statements for configuration files
- **THEN** all referenced files SHALL exist in the project
- **AND** no COPY statements SHALL reference missing or obsolete files
- **AND** template files SHALL only be copied if they are actually used by the system

#### Scenario: Legacy Cleanup

- **WHEN** the system has migrated from one approach to another (e.g., hostapd to NetworkManager)
- **THEN** the Dockerfile SHALL be updated to reflect the new approach
- **AND** legacy references SHALL be removed from the build process
- **AND** the build artifacts SHALL match the actual runtime dependencies

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

### Requirement: Base images are pinned immutably
All `FROM` images in `docker/Dockerfile.backend` SHALL be pinned by digest, not by mutable tag alone.

#### Scenario: Node build-stage image pinned by digest
- **WHEN** the frontend build stage is defined
- **THEN** the `node` base image SHALL include a `@sha256:` digest alongside its tag

#### Scenario: Python runtime image remains digest-pinned
- **WHEN** the backend runtime stage is defined
- **THEN** the `python` base image SHALL include a `@sha256:` digest alongside its tag

### Requirement: Third-party downloads are integrity-verified
Any artifact downloaded during the image build from outside the repository or a package registry (currently the lg C library `lg.zip`) SHALL be fetched over HTTPS and verified against a SHA-256 checksum pinned in the Dockerfile before use; the build SHALL fail on mismatch. Vendoring the artifact in the repository is an acceptable alternative.

#### Scenario: lgpio archive fetched with checksum verification
- **WHEN** the arm64 build downloads the lg library archive
- **THEN** the download URL SHALL use `https://`
- **AND** the archive's SHA-256 SHALL be compared against the checksum recorded in the Dockerfile before extraction

#### Scenario: Tampered or changed upstream archive fails the build
- **WHEN** the downloaded archive's SHA-256 does not match the pinned checksum
- **THEN** the image build SHALL fail before the archive is extracted or compiled

### Requirement: Frontend dependency install is deterministic
The frontend build stage SHALL install dependencies with `npm ci` driven by a committed `frontend/package-lock.json`, so identical inputs produce identical dependency trees.

#### Scenario: Lockfile copied and npm ci used
- **WHEN** the frontend build stage installs dependencies
- **THEN** the Dockerfile SHALL copy both `frontend/package.json` and `frontend/package-lock.json` before installing
- **AND** the install command SHALL be `npm ci`, not `npm install`

#### Scenario: Lockfile drift fails the build
- **WHEN** `frontend/package.json` and `frontend/package-lock.json` disagree
- **THEN** `npm ci` SHALL fail the image build instead of silently resolving new versions

### Requirement: No blind build-time package upgrades
The Dockerfile SHALL NOT run `apt-get upgrade` (or equivalent blanket upgrades) at build time; the package surface SHALL be defined by the pinned base image digest plus the explicit `apt-get install` list. Base-image security updates SHALL be taken by bumping the pinned digest.

#### Scenario: apt-get upgrade absent from build
- **WHEN** `docker/Dockerfile.backend` is inspected
- **THEN** no `RUN` instruction SHALL invoke `apt-get upgrade`

