## Why

The app is ready to ship to a test group of ~20 users, but there is no automated build, no published Docker image, and no mechanism to deliver updates. Every release currently requires manual steps on each device. This change establishes the CI/CD pipeline so that a `git push` produces a versioned, signed ARM64 Docker image on GHCR that devices can pull.

## What Changes

- Add GitHub Actions workflow that builds the ARM64 Docker image and pushes it to `ghcr.io` on every tagged release and on `main` merges
- Add Trivy vulnerability scan step in CI — blocks the push on HIGH/CRITICAL CVEs
- Bake a `VERSION` label (git tag or SHA) into the Docker image at build time
- Pin backend Python dependencies using `pip-compile` with hash verification (`requirements.txt` → `requirements.lock`)
- Pin Dockerfile base image to a specific digest (not floating `:latest`)
- Add GitHub Dependabot config for Python packages and Docker base images

## Capabilities

### New Capabilities
- `release-pipeline`: CI/CD workflow that builds, scans, and publishes versioned ARM64 Docker images to GHCR on each release

### Modified Capabilities
- `ci-build-success`: Extend existing CI spec to include image publishing, CVE gating, and versioned tagging

## Impact

- New: `.github/workflows/release.yml`
- New: `.github/dependabot.yml`
- Modified: `backend/requirements.txt` → add pinned lock file (`backend/requirements.lock`)
- Modified: `docker/Dockerfile.backend` — pin base image digest, add `VERSION` label
- No API changes, no frontend changes, no config changes
