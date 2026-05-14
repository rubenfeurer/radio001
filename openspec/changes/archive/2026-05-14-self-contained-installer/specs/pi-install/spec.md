## MODIFIED Requirements

### Requirement: One-Command Pi Install
The system SHALL provide a self-contained install script that sets up a working radio on a fresh Raspberry Pi OS installation without requiring git, Node.js, build tools, or a pre-installed Docker.

#### Scenario: Successful install on clean Pi OS with no Docker
- **WHEN** a user runs the install script on a Pi with only Raspberry Pi OS and an internet connection
- **THEN** the script SHALL detect that Docker is not installed
- **AND** install Docker automatically using the official convenience script
- **AND** add the invoking user to the `docker` group
- **AND** continue to create `/opt/radio/` directory structure
- **AND** write `/opt/radio/docker-compose.yml` referencing the GHCR image
- **AND** the compose file SHALL declare `/dev/snd` under `devices:` explicitly
- **AND** write `/opt/radio/config/radio.conf` with safe defaults
- **AND** install `/etc/systemd/system/radio.service`
- **AND** run `systemctl enable --now radio.service`
- **AND** the radio backend SHALL become reachable at `http://radio.local` within 2 minutes

#### Scenario: Docker already installed — install step skipped
- **WHEN** the install script runs on a Pi that already has Docker installed
- **THEN** the script SHALL skip the Docker installation step
- **AND** proceed directly to setting up the radio application

#### Scenario: Audio device access does not depend on privileged mode
- **WHEN** the radio container starts
- **THEN** ALSA audio output SHALL be available via the explicitly mapped `/dev/snd` device
- **AND** audio SHALL NOT rely solely on `privileged: true` for device access

#### Scenario: Install is idempotent
- **WHEN** the install script is run a second time on an already-installed Pi
- **THEN** it SHALL not corrupt existing config or station data in `/opt/radio/`
- **AND** it SHALL restart the service with the latest image

#### Scenario: Install leaves no source code on device
- **WHEN** the install is complete
- **THEN** the Pi SHALL contain no cloned git repository
- **AND** the Pi SHALL contain no Node.js installation from the script
- **AND** all application code SHALL reside inside the Docker image
