## MODIFIED Requirements

### Requirement: Systemd Service References GHCR-Based Compose
The systemd radio service SHALL start the radio using the production compose file that pulls from GHCR, without performing a local Docker build.

#### Scenario: Service starts radio from pre-built image
- **WHEN** the `radio.service` systemd unit starts (on boot or `systemctl start radio`)
- **THEN** it SHALL run `docker compose -f /opt/radio/docker-compose.yml up -d`
- **AND** no `docker build` step SHALL execute
- **AND** no local source tree SHALL be required

#### Scenario: Service does not pull on start
- **WHEN** the `radio.service` starts
- **THEN** it SHALL NOT run `docker compose pull` before starting
- **AND** image updates are delegated entirely to Watchtower on its nightly schedule

#### Scenario: Service restarts on failure
- **WHEN** the radio container exits unexpectedly
- **THEN** systemd SHALL restart the container via `Restart=on-failure`
- **AND** a restart delay of 10 seconds SHALL be observed before retry
