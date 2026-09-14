# ci-pipeline Delta — fix-release-pipeline-race

## REMOVED Requirements

### Requirement: Docker jobs have packages write permission
**Reason**: The `docker-build` job is deleted from `ci-cd.yml` (its per-platform matrix raced `release.yml` on the same `:stable`/`:latest` tags, nondeterministically leaving a single-arch image on a production tag), and the `docker-manifest` job was already removed in commit 61045f0. With no image-publishing jobs left, `ci-cd.yml` needs no `packages: write` grant anywhere.
**Migration**: `release.yml` is the sole publisher of images to GHCR and already carries `permissions: contents: read` + `packages: write`. No other workflow requires registry write access.

## ADDED Requirements

### Requirement: ci-cd.yml publishes no container images
The `ci-cd.yml` workflow SHALL NOT build-and-push, tag, or otherwise publish container images to any registry. Image publishing SHALL happen exclusively in `release.yml`.

#### Scenario: Push to main does not publish from ci-cd.yml
- **WHEN** a commit is pushed to `main` and `ci-cd.yml` runs
- **THEN** no job in `ci-cd.yml` SHALL push an image or move any GHCR tag
- **AND** the only workflow pushing `:latest` for that commit SHALL be `release.yml`

#### Scenario: GitHub Release does not trigger publishing from ci-cd.yml
- **WHEN** a GitHub Release is published
- **THEN** `ci-cd.yml` SHALL NOT push `:stable`, semver, or any other tag
- **AND** no `packages: write` permission SHALL be present in `ci-cd.yml`

### Requirement: Trivy action pinned to a commit SHA
Every use of `aquasecurity/trivy-action` in CI workflows SHALL reference a full 40-character commit SHA (with a trailing version comment), never a mutable ref such as `@master`.

#### Scenario: Workflows reference an immutable trivy-action ref
- **WHEN** any workflow step uses `aquasecurity/trivy-action`
- **THEN** the `uses:` ref SHALL be a full commit SHA
- **AND** a comment SHALL record the corresponding release version
