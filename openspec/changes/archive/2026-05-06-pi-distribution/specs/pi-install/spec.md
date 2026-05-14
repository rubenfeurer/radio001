## ADDED Requirements

### Requirement: One-Command Pi Install
The system SHALL provide a self-contained install script that sets up a working radio on a fresh Raspberry Pi OS installation without requiring git, Node.js, or build tools.

#### Scenario: Successful install on clean Pi OS
- **WHEN** a user runs `bash install.sh` on a Pi with Docker installed and an internet connection
- **THEN** the script SHALL create `/opt/radio/` directory structure
- **AND** write `/opt/radio/docker-compose.yml` referencing the GHCR image
- **AND** write `/opt/radio/config/radio.conf` with safe defaults
- **AND** install `/etc/systemd/system/radio.service`
- **AND** run `systemctl enable --now radio.service`
- **AND** the radio backend SHALL become reachable at `http://radio.local` within 2 minutes

#### Scenario: Install is idempotent
- **WHEN** the install script is run a second time on an already-installed Pi
- **THEN** it SHALL not corrupt existing config or station data in `/opt/radio/`
- **AND** it SHALL restart the service with the latest image

#### Scenario: Install leaves no source code on device
- **WHEN** the install is complete
- **THEN** the Pi SHALL contain no cloned git repository
- **AND** the Pi SHALL contain no Node.js installation from the script
- **AND** all application code SHALL reside inside the Docker image

### Requirement: Self-Contained Docker Image
The Docker image published to GHCR SHALL contain both the backend and the frontend static files, requiring no host-mounted source directories.

#### Scenario: Frontend served from image
- **WHEN** the container starts from the GHCR image
- **THEN** the frontend UI SHALL be accessible at `http://radio.local`
- **AND** no volume mount from a source tree SHALL be required for the UI to function

#### Scenario: Config and data survive image updates
- **WHEN** the container is updated to a new image version
- **THEN** `/opt/radio/config/radio.conf` SHALL be unchanged
- **AND** station data in `/opt/radio/data/` SHALL be unchanged
