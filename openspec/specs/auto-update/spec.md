# auto-update Specification

## Purpose
Defines requirements for automatic nightly image updates on the Pi via Watchtower.

### Requirement: Nightly Automatic Update
The system SHALL automatically pull and apply the latest image from GHCR nightly at 3am with no user interaction.

#### Scenario: Watchtower pulls new image at scheduled time
- **WHEN** the Watchtower container runs at 3am and a newer image exists at `ghcr.io/rubenfeurer/radio001:latest`
- **THEN** Watchtower SHALL pull the new image
- **AND** restart the radio container with the new image
- **AND** remove the old image to conserve SD card space

#### Scenario: No new image available
- **WHEN** the Watchtower container runs at 3am and no newer image exists
- **THEN** the radio container SHALL continue running without interruption
- **AND** no restart SHALL occur

#### Scenario: Update does not affect persisted data
- **WHEN** a container is restarted with a new image by Watchtower
- **THEN** `/opt/radio/config/radio.conf` SHALL be unchanged
- **AND** station data in `/opt/radio/data/` SHALL be unchanged
- **AND** the bind-mounted volumes SHALL persist across the update

#### Scenario: Watchtower is always active
- **WHEN** the radio systemd service starts
- **THEN** the Watchtower container SHALL start alongside the radio container
- **AND** Watchtower SHALL NOT require a separate `--profile` flag to activate
