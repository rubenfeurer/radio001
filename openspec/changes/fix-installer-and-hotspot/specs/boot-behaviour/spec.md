## MODIFIED Requirements

### Requirement: Auto-Start on Boot
The system SHALL start the Docker radio stack automatically on Pi power-on via a systemd service, without requiring manual intervention. The `radio.service` unit SHALL be valid under current systemd: `Type=oneshot` with `RemainAfterExit=yes`, no `Restart=` directive (invalid for oneshot units), and no `StartLimit*` settings in the `[Service]` section. Container restart supervision is delegated to Docker via `restart: unless-stopped` in the compose file.

#### Scenario: Service starts radio from pre-built image
- **WHEN** the `radio.service` systemd unit starts (on boot or `systemctl start radio`)
- **THEN** it SHALL run `docker compose -f /opt/radio/docker-compose.yml up -d`
- **AND** no `docker build` step SHALL execute
- **AND** no local source tree SHALL be required

#### Scenario: Service does not pull on start
- **WHEN** the `radio.service` starts
- **THEN** it SHALL NOT run `docker compose pull` before starting
- **AND** image updates are delegated entirely to Watchtower on its nightly schedule

#### Scenario: Container restarts are supervised by Docker, not systemd
- **WHEN** the radio container exits unexpectedly
- **THEN** dockerd SHALL restart the container per the compose `restart: unless-stopped` policy
- **AND** the `radio.service` unit SHALL NOT declare `Restart=` or `RestartSec=`

#### Scenario: Unit file is accepted by systemd without warnings
- **WHEN** `systemctl daemon-reload` loads the installed `radio.service`
- **THEN** systemd SHALL report no invalid or ignored directives for the unit
- **AND** the unit SHALL use `Type=oneshot` with `RemainAfterExit=yes`
- **AND** any start-rate limiting, if present, SHALL live in the `[Unit]` section

#### Scenario: Service install via install script
- **WHEN** `sudo bash scripts/install.sh` is executed on the Pi
- **THEN** the script writes `/etc/systemd/system/radio.service`
- **AND** runs `systemctl daemon-reload && systemctl enable --now radio.service`
- **AND** the radio backend becomes reachable within normal container startup time
