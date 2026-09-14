# dockerfile-accuracy — Delta Specification

## ADDED Requirements

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
