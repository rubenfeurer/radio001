# auto-update Specification

## Purpose
Defines requirements for automatic nightly image updates on the Pi via Watchtower.
## Requirements
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

### Requirement: Documented rollback for a bad stable image
The deployment documentation SHALL describe a rollback procedure for a bad `:stable` image: pinning the Pi's compose file to a previous immutable semver tag (`:vX.Y.Z`), pulling and restarting, and reverting the pin to `:stable` once a fixed release exists. The documentation SHALL note that `WATCHTOWER_CLEANUP=true` deletes the previous local image (so rollback re-pulls from GHCR) and that Watchtower keeps checking the pinned tag, which never moves, effectively freezing updates until the pin is reverted.

#### Scenario: Operator rolls back a bad stable release
- **WHEN** a released `:stable` image malfunctions on production Pis
- **THEN** the documented procedure SHALL restore the previous version by pinning its semver tag in `/opt/radio/docker-compose.yml` and running `docker compose pull && docker compose up -d`
- **AND** the procedure SHALL work without requiring GHCR write access

#### Scenario: Rollback prerequisite is documented
- **WHEN** an operator consults the rollback documentation before any tagged release exists
- **THEN** the documentation SHALL state that rollback requires at least one prior `vX.Y.Z` release
- **AND** SHALL point to the GHCR package versions list as the source of available tags

### Requirement: Watchtower Image Pinning
The Watchtower service SHALL reference a version-pinned image (`containrrr/watchtower:1.7.1`), and the pin SHALL be identical in `docker/compose.prod.yml` and the compose file written by `scripts/install.sh`.

#### Scenario: Watchtower pinned in both compose sources
- **WHEN** `docker/compose.prod.yml` and the compose heredoc in `scripts/install.sh` are inspected
- **THEN** both SHALL specify `containrrr/watchtower:1.7.1` (or a later deliberately bumped pin, identical in both files)
- **AND** neither SHALL reference `containrrr/watchtower` without a version tag

#### Scenario: Watchtower version bumps are deliberate
- **WHEN** the Watchtower version is changed
- **THEN** both compose sources SHALL be updated in the same commit

