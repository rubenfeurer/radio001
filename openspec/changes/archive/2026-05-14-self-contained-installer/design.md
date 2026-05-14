## Context

The install script errors out if Docker isn't present. End users — non-technical people receiving a Pi with fresh Pi OS — don't know what Docker is and shouldn't need to. The fix is to detect and install Docker inside the script before proceeding.

## Goals / Non-Goals

**Goals:**
- Install Docker automatically using the official convenience script if not already installed
- Add the calling user (`$SUDO_USER`) to the `docker` group so they can run docker commands without sudo after reboot
- Keep the script idempotent — re-running on a Pi that already has Docker skips the install step
- Update README and docs to reflect the simplified prerequisites

**Non-Goals:**
- Supporting non-Debian/Raspberry Pi OS distros
- Pinning a specific Docker version (latest stable from get.docker.com is fine)
- Installing Docker Desktop or any GUI tooling

## Decisions

**Decision: Use `get.docker.com` convenience script**

The official `curl -fsSL https://get.docker.com | sh` script is the standard, maintained way to install Docker CE on Debian-based ARM64 systems. It handles apt repo setup, key management, and compose plugin installation in one step.

Alternative considered: manual apt install steps. Rejected — more brittle and requires maintaining repo URL/key details ourselves.

**Decision: Check `command -v docker` before installing**

Skip Docker install entirely if `docker` is already in PATH. This keeps the script idempotent and fast on re-runs.

**Decision: Add `$SUDO_USER` to docker group**

The script runs as root (sudo). `$SUDO_USER` is the original user who invoked sudo. Adding them to the `docker` group lets them run `docker` commands in future sessions without sudo. If `$SUDO_USER` is empty (piped curl | sudo bash case), skip silently — the service runs as root anyway.

## Risks / Trade-offs

- [get.docker.com availability] If Docker's CDN is down, install fails → Mitigation: error message tells user to retry or install Docker manually
- [install time] Docker install adds ~1–2 min to first-run time → Acceptable; shown with a progress message
- [group change requires re-login] User won't be in docker group until next login → Not a problem; the service runs as root
