# pi-install Specification

## Purpose
Defines requirements for distributing and installing the radio system on a Raspberry Pi without requiring development tools on the device.
## Requirements
### Requirement: One-Command Pi Install
The system SHALL provide a self-contained install script that sets up a working radio on a fresh Raspberry Pi OS installation without requiring git, Node.js, build tools, or a pre-installed Docker. The script SHALL NOT embed a copy of the compose file, SHALL NOT install or configure dnsmasq, and SHALL NOT modify `/etc/systemd/resolved.conf`.

#### Scenario: Successful install on clean Pi OS with no Docker
- **WHEN** a user runs the install script on a Pi with only Raspberry Pi OS and an internet connection
- **THEN** the script SHALL detect that Docker is not installed
- **AND** install Docker automatically using the official convenience script
- **AND** add the invoking user to the `docker` group
- **AND** continue to create `/opt/radio/` directory structure
- **AND** download `docker/compose.prod.yml` from the repository and install it as `/opt/radio/docker-compose.yml` (no embedded compose heredoc)
- **AND** the compose file SHALL declare `/dev/snd` under `devices:` explicitly
- **AND** write `/opt/radio/config/radio.conf` with safe defaults, including a randomly generated `HOTSPOT_PASSWORD`
- **AND** install `/etc/systemd/system/radio.service`
- **AND** run `systemctl enable --now radio.service`
- **AND** the radio backend SHALL become reachable at `http://radio.local:8000` within 2 minutes

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
- **AND** it SHALL preserve the existing `radio.conf`, including a previously generated `HOTSPOT_PASSWORD`
- **AND** it SHALL restart the service with the latest image

#### Scenario: Install leaves no source code on device
- **WHEN** the install is complete
- **THEN** the Pi SHALL contain no cloned git repository
- **AND** the Pi SHALL contain no Node.js installation from the script
- **AND** all application code SHALL reside inside the Docker image

#### Scenario: Compose file has a single source of truth
- **WHEN** the install script provisions `/opt/radio/docker-compose.yml`
- **THEN** the file content SHALL come from `docker/compose.prod.yml` in the repository
- **AND** no second copy of the compose definition SHALL exist in `install.sh` that could drift from the repository file

#### Scenario: Data directory ownership instead of world-writable permissions
- **WHEN** the install script creates `/opt/radio/data`
- **THEN** it SHALL set ownership to match the UID/GID the container process runs as
- **AND** it SHALL NOT apply `chmod 777` or otherwise make the directory world-writable
- **AND** the container SHALL still be able to persist station data and `radio_state.json`

#### Scenario: Install does not modify host DNS configuration
- **WHEN** the install script runs
- **THEN** it SHALL NOT install, mask, or configure dnsmasq
- **AND** it SHALL NOT edit `/etc/systemd/resolved.conf` or restart `systemd-resolved`

#### Scenario: Partial failure leaves no broken state
- **WHEN** a step of the install script fails (e.g. the compose download or an apt operation)
- **THEN** the script SHALL abort with a message identifying the failed step
- **AND** files SHALL be written atomically (temp file then move), so an existing `/opt/radio/docker-compose.yml`, `radio.conf`, or systemd unit is never left half-written
- **AND** re-running the script SHALL be a safe recovery path

#### Scenario: Final message shows working URLs
- **WHEN** the install completes successfully
- **THEN** the final message SHALL show URLs that include port 8000 (`http://<pi-ip>:8000` and `http://radio.local:8000`)
- **AND** it SHALL NOT claim the UI is reachable at `http://radio.local` without a port
- **AND** it SHALL print the hotspot SSID and the generated hotspot password

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

