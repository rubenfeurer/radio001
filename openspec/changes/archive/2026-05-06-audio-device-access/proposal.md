## Why

The production Docker compose and install script embed `/dev/gpiochip0` and `/dev/net/tun` as explicit device mounts but omit `/dev/snd`. Audio output currently works only because `privileged: true` grants access to all host devices as a side-effect. Dropping `privileged:` (a reasonable future hardening step) would silently break audio. Explicit device mapping makes the audio dependency clear and survivable if privilege is ever reduced.

## What Changes

- Add `/dev/snd` to the `devices:` list in `docker/compose.prod.yml`
- Add `/dev/snd` to the embedded compose heredoc in `scripts/install.sh`
- Add a note in `docs/deployment-and-updates.md` documenting required host devices

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `pi-install`: the self-contained compose embedded in the install script now declares `/dev/snd` explicitly

## Impact

- `docker/compose.prod.yml` — one-line device addition
- `scripts/install.sh` — matching device addition in the heredoc
- `docs/deployment-and-updates.md` — device table added to Security section
