## MODIFIED Requirements

### Requirement: Nightly Automatic Update
The system SHALL automatically pull and apply the latest stable image from GHCR nightly at 3am with no user interaction. Production Pis SHALL track `:stable`; the test Pi tracks `:latest` for manual pre-release verification.

#### Scenario: Watchtower pulls new :stable image at scheduled time
- **WHEN** the Watchtower container runs at 3am and a newer image exists at `ghcr.io/rubenfeurer/radio001:stable`
- **THEN** Watchtower SHALL pull the new image
- **AND** restart the radio container with the new image
- **AND** remove the old image to conserve SD card space

#### Scenario: No new :stable image available
- **WHEN** the Watchtower container runs at 3am and no newer `:stable` image exists
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

#### Scenario: :latest used only for manual test Pi verification
- **WHEN** a developer wants to verify a build on the test Pi before releasing
- **THEN** they SHALL manually run `docker pull ghcr.io/rubenfeurer/radio001:latest` on the test Pi
- **AND** `:latest` SHALL NOT be tracked by Watchtower on any Pi
