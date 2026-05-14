## MODIFIED Requirements

### Requirement: Docker Build Completion

The Docker build process SHALL complete successfully without errors related to missing configuration files or dependencies.

#### Scenario: CI Pipeline Docker Build

- **WHEN** the CI pipeline runs `docker build` on the backend Dockerfile
- **THEN** the build SHALL complete successfully without file not found errors
- **AND** the build SHALL NOT fail on COPY statements for missing files
- **AND** all specified packages SHALL be successfully installed

#### Scenario: Frontend builder stage uses node 26

- **WHEN** the multi-stage Dockerfile builds the frontend-builder stage
- **THEN** it SHALL use `node:26-slim` as the base image
- **AND** the `npm install` step SHALL complete without errors on Node 26

#### Scenario: Frontend build does not require a lockfile

- **WHEN** the frontend-builder stage installs npm dependencies
- **THEN** it SHALL use `npm install` (not `npm ci`)
- **AND** the build SHALL succeed even when `package-lock.json` is absent from the repository

#### Scenario: Missing Configuration Files

- **WHEN** the Dockerfile attempts to COPY configuration template files
- **THEN** no "file not found" errors SHALL occur
- **AND** the build SHALL continue to completion

#### Scenario: Package Installation

- **WHEN** the Dockerfile installs system dependencies via apt-get
- **THEN** all listed packages SHALL be available and successfully installed
- **AND** no packages SHALL be listed that are not actually used by the system

## ADDED Requirements

### Requirement: pytest-asyncio 1.x compatibility

The backend test suite SHALL be compatible with pytest-asyncio 1.x.

#### Scenario: Async tests run under pytest-asyncio 1.3

- **WHEN** the test suite runs with pytest-asyncio 1.3.0 or later
- **THEN** all async tests marked with `asyncio_mode = auto` SHALL be collected and executed
- **AND** the session-scoped event loop configuration (`asyncio_default_fixture_loop_scope = session`) SHALL be respected
- **AND** no tests SHALL fail due to pytest-asyncio API changes between 0.x and 1.x
