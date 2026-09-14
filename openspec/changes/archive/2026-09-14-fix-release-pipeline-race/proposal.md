# Fix Release Pipeline Race

## Why

Two workflows publish the same production image tags: `ci-cd.yml`'s per-platform `docker-build` matrix job (lines 229–286) and `release.yml` both push `:stable`/`:latest` to GHCR — last job to finish wins, and because the matrix pushes each platform separately, an amd64-only `:stable` can end up as the tag Watchtower auto-pulls fleet-wide at 03:00 with no rollback (old images are deleted by `WATCHTOWER_CLEANUP`). Separately, `release.yml`'s Trivy gate is decorative: it runs *after* the tags are pushed and scans the `:latest` registry ref (release.yml:105–114), which on a tag build is the *previous* main image — a HIGH/CRITICAL finding blocks nothing.

## What Changes

- **Delete the `docker-build` job from `.github/workflows/ci-cd.yml`** (the per-platform matrix at lines 229–286). `release.yml` becomes the sole publisher of images to GHCR. `ci-cd.yml` retains integration tests, filesystem security scan, and test analysis only.
- **Reorder `.github/workflows/release.yml` to build → scan → push**: Trivy scans the exact image just built (local image / digest, not the `:latest` registry ref) *before* any tag is pushed; a HIGH/CRITICAL finding fails the job and no tag (`:latest`, `:stable`, semver) is published.
- **Pin `aquasecurity/trivy-action` to a full commit SHA** (with a version comment) in both workflows that use it (`ci-cd.yml:176`, `release.yml:106`) — a mutable `@master` ref in a workflow holding `packages: write` is a supply-chain risk.
- **Document a rollback procedure for a bad `:stable`** in `docs/deployment-and-updates.md`: pin the Pi's compose file to a previous semver tag (`:vX.Y.Z`), restart, and note the interaction with Watchtower/`WATCHTOWER_CLEANUP`.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `ci-pipeline`: The requirement that docker-build/docker-manifest jobs carry `packages: write` is removed along with the jobs themselves; new requirements state that `ci-cd.yml` publishes no images (release.yml is the sole publisher) and that all `trivy-action` uses are pinned to a commit SHA.
- `release-gate`: The `:stable`-on-release requirement is extended: tags are pushed only after a Trivy HIGH/CRITICAL scan of the exact image built in that run passes (build → scan → push ordering).
- `auto-update`: Adds a requirement that a rollback procedure for a bad `:stable` image is documented (pinning a previous semver tag), since Watchtower cleanup deletes the local fallback image.

## Impact

- `.github/workflows/ci-cd.yml` — `docker-build` job deleted; Trivy action pinned; no `packages: write` permission needed anywhere in this workflow.
- `.github/workflows/release.yml` — build/scan/push steps reordered; Trivy action pinned; scan target changed from `:latest` registry ref to the locally built image.
- `docs/deployment-and-updates.md` — new rollback section.
- No application code, backend, or frontend changes. No change to what tags exist or what Watchtower tracks — only *who* publishes them and *when*.
- Risk: release publishing now depends on the Trivy gate; a noisy unfixable CVE could block a release (mitigated by existing `.trivyignore` + `ignore-unfixed: true`).
