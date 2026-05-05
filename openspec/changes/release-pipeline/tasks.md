## 1. Dependency Pinning

- [x] 1.1 Rename `backend/requirements.txt` to `backend/requirements.in`
- [x] 1.2 Install `pip-tools` and run `pip-compile --generate-hashes backend/requirements.in -o backend/requirements.lock`
- [x] 1.3 Update `docker/Dockerfile.backend` to install from `requirements.lock` using `pip install --no-deps --require-hashes -r requirements.lock`
- [x] 1.4 Verify Docker build succeeds locally with the lock file

## 2. Dockerfile Hardening

- [x] 2.1 Get the current digest of `python:3.11-slim`: `docker pull python:3.11-slim && docker inspect python:3.11-slim --format='{{index .RepoDigests 0}}'`
- [x] 2.2 Replace `FROM python:3.11-slim` with `FROM python:3.11-slim@sha256:<digest>` in `docker/Dockerfile.backend`
- [x] 2.3 Add `ARG VERSION=dev` and `LABEL org.opencontainers.image.version=$VERSION` to the Dockerfile

## 3. GitHub Actions Release Workflow

- [x] 3.1 Create `.github/workflows/release.yml` with trigger on `push` to `main` and `push` of tags matching `v*.*.*`
- [x] 3.2 Add `setup-qemu-action` and `setup-buildx-action` steps for ARM64 cross-compilation
- [x] 3.3 Add `docker/login-action` step to authenticate with GHCR using `GITHUB_TOKEN`
- [x] 3.4 Add `docker/metadata-action` step to compute tags (`latest` + semver if tagged) and labels
- [x] 3.5 Add `docker/build-push-action` step: platform `linux/arm64`, build arg `VERSION`, push enabled
- [x] 3.6 Add `aquasecurity/trivy-action` step after build (exit-code 1 on HIGH/CRITICAL, ignore unfixed)
- [x] 3.7 Add step to verify `requirements.lock` is in sync with `requirements.in` (run `pip-compile --dry-run`, fail on diff)

## 4. Dependabot Configuration

- [x] 4.1 Create `.github/dependabot.yml` with `pip` ecosystem watching `backend/requirements.in`, weekly schedule
- [x] 4.2 Add `docker` ecosystem entry watching `docker/Dockerfile.backend`, weekly schedule

## 5. Verify Pipeline

- [ ] 5.1 Push to `main` and confirm workflow runs and image appears at `ghcr.io/rubenfeurer/radio001:latest`
- [ ] 5.2 Create a test tag `v0.1.0` and confirm versioned image appears at `ghcr.io/rubenfeurer/radio001:v0.1.0`
- [ ] 5.3 Confirm image is pullable: `docker pull ghcr.io/rubenfeurer/radio001:latest` on a machine without local build
- [ ] 5.4 Confirm `docker inspect` shows correct `org.opencontainers.image.version` label
