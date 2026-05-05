## Context

The project has a working FastAPI + SvelteKit application that runs in Docker on Raspberry Pi Zero 2 W (ARM64). Currently, there is no CI/CD pipeline: images are built locally on the Pi from source, requiring git, build tools, and Node.js on the device. The Dockerfile uses a floating `python:3.11-slim` base image and `requirements.txt` has no hash verification. There is no mechanism to publish or distribute updates.

The target is a pipeline that runs on GitHub Actions, builds a multi-arch (linux/arm64) image, scans it for vulnerabilities, and pushes it to GitHub Container Registry (GHCR) so that devices can pull it without any source code on the Pi.

## Goals / Non-Goals

**Goals:**
- Build and publish ARM64 Docker image to GHCR on every push to `main` and on every semver tag
- Gate image publication on Trivy CVE scan (block on HIGH/CRITICAL)
- Bake `VERSION` label into image so running containers know their version
- Pin Python dependencies with `pip-compile` hash-checking
- Pin Dockerfile base image to a digest
- Enable Dependabot for Python and Docker base image updates

**Non-Goals:**
- Multi-arch builds beyond `linux/arm64` (Pi only)
- Image signing with cosign (can add later)
- Self-hosted runners
- Deployment to devices (that is handled by `pi-distribution` change)
- Frontend build in CI (frontend is baked into backend image)

## Decisions

### 1. GHCR over Docker Hub

**Decision**: Use `ghcr.io/[owner]/radio001` as the image registry.

**Rationale**: Free for public images, integrated with GitHub permissions, no separate account needed, trusted by the community. Docker Hub imposes rate limits on unauthenticated pulls which matters for 20 devices polling for updates.

**Alternative considered**: Docker Hub. Rejected due to pull rate limits and separate credential management.

### 2. Tag strategy: `latest` + semver

**Decision**: Push two tags on every release — `ghcr.io/[owner]/radio001:latest` and `ghcr.io/[owner]/radio001:v{semver}`. On `main` pushes (non-tagged), push only `latest`.

**Rationale**: `latest` is what Watchtower tracks on devices. Semver tags give immutable rollback targets. This is the minimal tagging scheme that satisfies both auto-update and rollback needs.

**Alternative considered**: Only semver tags (no `latest`). Rejected because Watchtower would need to know the current tag, adding complexity to the device side.

### 3. Trivy as CVE gate

**Decision**: Run `aquasecurity/trivy-action` after the image build, configured to exit non-zero on HIGH or CRITICAL CVEs. This blocks the push step.

**Rationale**: Trivy is zero-config, runs as a GitHub Action, and scans the built image layer by layer. It catches both OS and Python package vulnerabilities.

**Alternative considered**: Snyk. Rejected because it requires a separate account and token.

### 4. `pip-compile` for dependency pinning

**Decision**: Add `requirements.in` as the human-editable source of truth. `pip-compile --generate-hashes` produces `requirements.lock` with pinned versions and SHA256 hashes. The Dockerfile uses `requirements.lock`.

**Rationale**: Hash-checking prevents supply chain attacks where a package is replaced after pinning. `pip-compile` makes upgrading easy — edit `.in`, run `pip-compile`, commit.

**Alternative considered**: Keep `requirements.txt` with loose pins. Rejected because it allows silent upgrades and has no hash verification.

### 5. Base image pinned to digest

**Decision**: Replace `FROM python:3.11-slim` with `FROM python:3.11-slim@sha256:<digest>`. Dependabot will open PRs when a new digest is available.

**Rationale**: A floating tag means the base image can change between builds, breaking reproducibility and bypassing Trivy baseline.

### 6. VERSION label baked at build time

**Decision**: Pass `VERSION` as a build arg (`--build-arg VERSION=$(git describe --tags --always)`). Set as Docker `LABEL org.opencontainers.image.version=$VERSION`. Backend reads this via `docker inspect` or an env var set in the compose file.

**Rationale**: Allows the webapp to display the running version and check against GHCR for updates. Uses OCI standard label — no custom tooling needed.

## Risks / Trade-offs

- **ARM64 build time on GitHub Actions** → GitHub-hosted runners are x86. Cross-compiling ARM64 via QEMU (docker/setup-qemu-action) adds ~5-10 min build time. Acceptable for a release pipeline (not a hot loop). If it becomes painful, a self-hosted Pi runner is a future option.
- **Trivy false positives block releases** → Trivy may flag CVEs with no fix available. Mitigation: configure `--ignore-unfixed` flag so only fixable vulnerabilities block the build.
- **`requirements.lock` drift** → If a developer installs a new package without updating `.lock`, the Docker build fails. Mitigation: the CI step that runs `pip-compile` and checks for diff catches this.
- **GHCR public image** → Source code is not in the image, but the image layers may reveal implementation details. Acceptable for an open-source project; flag if this changes.

## Migration Plan

1. Add `.github/workflows/release.yml` and `.github/dependabot.yml`
2. Generate `backend/requirements.lock` from existing `requirements.txt` (rename to `requirements.in`)
3. Pin Dockerfile base image digest
4. Update Dockerfile to use `requirements.lock` and accept `VERSION` build arg
5. Push to `main` → first image appears on GHCR
6. Verify image is pullable: `docker pull ghcr.io/[owner]/radio001:latest`

Rollback: revert the workflow file; the image registry retains all previous tags.
