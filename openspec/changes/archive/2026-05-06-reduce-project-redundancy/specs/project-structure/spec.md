## ADDED Requirements

### Requirement: Single canonical location for each asset type
The project SHALL have exactly one copy of each data file, with ownership determined by file type: static configuration belongs in `config/`, runtime state belongs in `data/`, and container/deploy files belong in `docker/`.

#### Scenario: Station library has one copy
- **WHEN** the project is checked out
- **THEN** `stations.json` SHALL exist only at `config/stations.json`
- **AND** no copies SHALL exist at `assets/stations.json` or `backend/assets/stations.json`

#### Scenario: Sound files have one location
- **WHEN** the project is checked out
- **THEN** sound files SHALL exist only under `config/sounds/`
- **AND** no copies SHALL exist at `assets/sounds/` or `backend/assets/sounds/`

#### Scenario: Docker and compose files in one directory
- **WHEN** the project is checked out
- **THEN** all Dockerfiles, docker-compose files, and nginx configs SHALL be under `docker/`
- **AND** the `compose/` and `nginx/` top-level directories SHALL not exist
- **AND** `backend/Dockerfile` SHALL not exist (it is a duplicate of `docker/Dockerfile.backend`)

### Requirement: No unused data files at project root
The project root `data/` directory SHALL contain only files that are actively read by the running system.

#### Scenario: Unused files removed
- **WHEN** the project is checked out
- **THEN** `data/preferences.json` SHALL not exist
- **AND** `data/default_stations.json` SHALL not exist
- **AND** `backend/package.json` SHALL not exist

### Requirement: Frontend stores have no unused modules
Every file in `frontend/src/lib/stores/` SHALL be imported by at least one route or component.

#### Scenario: No dead store files
- **WHEN** the frontend is built
- **THEN** `system.svelte.ts` SHALL not exist in the stores directory
- **AND** no TypeScript errors SHALL be introduced by its removal
