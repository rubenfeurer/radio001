## Why

The install script currently requires Docker to be pre-installed, making it unsuitable for non-technical end users who receive a fresh Pi and expect a single command to get the radio running. The README also lists "Docker installed" as a prerequisite, which is a barrier for the target audience.

## What Changes

- `scripts/install.sh`: auto-install Docker (via `get.docker.com`) if not already present, then add the calling user to the `docker` group
- `README.md`: remove "Docker installed" prerequisite; update Quick Start to a single curl command with no prior setup required
- `docs/deployment-and-updates.md`: update installation prerequisites section to reflect no manual Docker install needed

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `pi-install`: the install script SHALL install Docker automatically if absent; no Docker prerequisite SHALL be required of the user

## Impact

- `scripts/install.sh` — add Docker install block before the Docker check
- `README.md` — Quick Start prerequisites simplified to: Pi OS 64-bit + internet connection
- `docs/deployment-and-updates.md` — Installation section updated
