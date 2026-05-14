## 1. Install Script

- [x] 1.1 Replace the Docker prerequisite check in `scripts/install.sh` with an auto-install block: if `docker` is not in PATH, run `curl -fsSL https://get.docker.com | sh`
- [x] 1.2 After Docker install, add `$SUDO_USER` to the `docker` group (skip silently if `$SUDO_USER` is empty)
- [x] 1.3 Add a progress message before the Docker install step: "Docker not found — installing Docker..."

## 2. Documentation

- [x] 2.1 Update `README.md` Quick Start prerequisites: remove "Docker installed", keep only "Raspberry Pi OS 64-bit" and "internet connection"
- [x] 2.2 Update `docs/deployment-and-updates.md` Installation section: remove Docker as a manual prerequisite, note it is installed automatically
- [x] 2.3 Add the GitHub repo link to `README.md` so end users know where to find the install command
