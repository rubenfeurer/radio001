# container-least-privilege Specification

## Purpose
TBD - created by archiving change harden-container-supply-chain. Update Purpose after archive.
## Requirements
### Requirement: Production container runs without privileged mode
The production radio container SHALL run without `privileged: true` and without a blanket `/dev` bind mount, relying solely on explicitly enumerated grants: `cap_add: NET_ADMIN, NET_RAW`, `devices: /dev/gpiochip0, /dev/snd, /dev/net/tun`, and `group_add: "986"` (gpio). This applies to both `docker/compose.prod.yml` and the compose file written by `scripts/install.sh`.

#### Scenario: No privileged flag or blanket /dev mount in compose sources
- **WHEN** `docker/compose.prod.yml` or the compose heredoc in `scripts/install.sh` is inspected
- **THEN** the `radio-backend` service SHALL NOT contain `privileged: true`
- **AND** the `volumes` list SHALL NOT contain a `/dev:/dev` bind mount
- **AND** the `devices` list SHALL contain exactly `/dev/net/tun`, `/dev/gpiochip0`, and `/dev/snd`, matching the Required Host Devices table in `docs/deployment-and-updates.md`

#### Scenario: Audio works via enumerated device grant
- **WHEN** the unprivileged container plays a station on the Pi
- **THEN** audio SHALL be output through PipeWire via the mounted pulse socket, with ALSA fallback available through the mapped `/dev/snd` device
- **AND** volume control (`pactl` or `amixer -c Headphones`) SHALL succeed

#### Scenario: GPIO works via enumerated device grant
- **WHEN** the unprivileged container starts on the Pi
- **THEN** lgpio SHALL open `/dev/gpiochip0` successfully via membership in the `gpio` group (GID 986)
- **AND** button and rotary encoder events SHALL be received

#### Scenario: WiFi management works via capabilities
- **WHEN** the unprivileged container issues `sudo nmcli` commands over the host D-Bus
- **THEN** WiFi scan, connect, and hotspot mode-switch operations SHALL succeed using only `NET_ADMIN` and `NET_RAW` capabilities

### Requirement: In-container sudo is restricted to an explicit command whitelist
The image's `/etc/sudoers.d/radio` SHALL grant the `radio` user passwordless sudo only for the commands the backend actually invokes via sudo: `nmcli` (any arguments), and `rm -f /etc/raspiwifi/host_mode`, `mkdir -p /etc/raspiwifi`, `touch /etc/raspiwifi/host_mode` as exact argument patterns. No other commands SHALL be sudo-permitted.

#### Scenario: Whitelisted WiFi commands succeed
- **WHEN** the backend runs `sudo nmcli device wifi rescan` or writes the host-mode marker via `sudo mkdir -p /etc/raspiwifi` and `sudo touch /etc/raspiwifi/host_mode`
- **THEN** sudo SHALL execute the command without a password prompt

#### Scenario: Formerly whitelisted file commands are denied
- **WHEN** any process in the container attempts `sudo cp`, `sudo mv`, `sudo chmod`, `sudo killall`, `sudo ip`, `sudo reboot`, or `sudo shutdown`
- **THEN** sudo SHALL deny the command

#### Scenario: File operations outside the marker path are denied
- **WHEN** a process attempts `sudo rm -f /etc/passwd` or `sudo touch /etc/sudoers.d/evil`
- **THEN** sudo SHALL deny the command because the arguments do not match the whitelisted patterns

