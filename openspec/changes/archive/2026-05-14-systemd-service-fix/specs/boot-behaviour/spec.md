## MODIFIED Requirements

### Requirement: Auto-Start on Boot
The system SHALL start the Docker radio stack automatically on Pi power-on via a systemd service, without requiring manual intervention.

#### Scenario: Service starts radio from pre-built image
- **WHEN** the `radio.service` systemd unit starts (on boot or `systemctl start radio`)
- **THEN** it SHALL run `docker compose -f /opt/radio/docker-compose.yml up -d`
- **AND** no `docker build` step SHALL execute
- **AND** no local source tree SHALL be required

#### Scenario: Service does not pull on start
- **WHEN** the `radio.service` starts
- **THEN** it SHALL NOT run `docker compose pull` before starting
- **AND** image updates are delegated entirely to Watchtower on its nightly schedule

#### Scenario: Service restart attempts are bounded
- **WHEN** the `radio.service` ExecStart exits with a non-zero code
- **THEN** systemd SHALL retry with `Restart=on-failure` and a 10-second delay
- **AND** retries SHALL be capped at 3 attempts within any 5-minute window (`StartLimitBurst=3`, `StartLimitIntervalSec=300`)
- **AND** after exceeding the limit the service SHALL enter the `failed` state and stop retrying automatically

#### Scenario: Service install via install script
- **WHEN** `sudo bash scripts/install.sh` is executed on the Pi
- **THEN** the script writes `/etc/systemd/system/radio.service`
- **AND** the service file SHALL include `StartLimitIntervalSec=300` and `StartLimitBurst=3` under `[Service]`
- **AND** runs `systemctl daemon-reload && systemctl enable --now radio.service`
- **AND** the radio backend becomes reachable within normal container startup time
