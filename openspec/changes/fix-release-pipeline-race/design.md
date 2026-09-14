# Design — Fix Release Pipeline Race

## Context

Two workflows currently push production image tags to GHCR:

- `.github/workflows/release.yml` — the intended sole publisher. Triggers on push to `main` (`:latest`) and tag push `v*.*.*` (`:stable`, `:vX.Y.Z`, `:X.Y`). Builds `linux/arm64` only.
- `.github/workflows/ci-cd.yml` — `docker-build` job (lines 229–286). Triggers on push to `main` and `release: published`. A **per-platform matrix** (`linux/amd64`, `linux/arm64`) where *each matrix leg independently pushes the same tag list* (`:latest` on main, `:stable` on release, plus semver/branch/sha tags). Because a plain `docker/build-push-action` push of a single platform *replaces* the tag's manifest, whichever leg finishes last determines the architecture of `:latest`/`:stable`. An amd64-only `:stable` bricks every production Pi at the next 03:00 Watchtower pull, and `WATCHTOWER_CLEANUP=true` deletes the previous local image, so there is no local fallback.

Additionally, `release.yml`'s security gate is ordered wrong: the `Build and push` step (lines 90–103) pushes all tags, and only then does Trivy run (lines 105–114) — against `ghcr.io/...:latest`, a registry ref. On a tag build, `:latest` isn't even updated by that run, so Trivy scans the *previous* main image. The `exit-code: "1"` gate can only fail the job *after* `:stable` is already live.

Both workflows reference `aquasecurity/trivy-action@master` — a mutable ref inside workflows that hold `packages: write`.

The `ci-pipeline` main spec still requires `packages: write` on the docker-build/docker-manifest jobs (docker-manifest was already deleted in commit 61045f0); this change removes that requirement along with the job.

## Goals / Non-Goals

**Goals:**

- Exactly one workflow (`release.yml`) ever pushes image tags to GHCR.
- Trivy scans the exact image built in the current run, and a HIGH/CRITICAL finding prevents *any* tag from being pushed.
- All `trivy-action` references pinned to a full commit SHA.
- A tested, documented rollback path for a bad `:stable`.

**Non-Goals:**

- No change to the tag scheme (`:latest`, `:stable`, semver) or to what Watchtower tracks.
- No multi-arch publishing — amd64 images were never used by any Pi; dropping them entirely is fine.
- No automated rollback tooling — documentation only.
- No consolidation of the remaining ci-cd.yml jobs (that is the separate CI-simplification item in the review's delete list).

## Decisions

### D1: Delete `docker-build` from ci-cd.yml rather than fixing its matrix

Alternatives: (a) fix the matrix with digest-push + a manifest job, (b) restrict it to non-tag refs. Rejected — `release.yml` already builds the only architecture the fleet uses; a second publisher adds nothing but the race. Deleting the job also removes the last `packages: write` grant from ci-cd.yml, shrinking its blast radius. The `security` (fs scan) and `test-analysis` jobs remain; nothing depends on `docker-build`.

### D2: Build once locally, scan, then push — using two `build-push-action` steps sharing the buildx cache

`release.yml` step order becomes:

1. `docker/build-push-action` with `push: false`, `load: true`, and a throwaway local tag (e.g. `radio001:scan`). QEMU/buildx already produce the arm64 image; `load: true` works for a single platform.
2. Trivy (`image-ref: radio001:scan`, `exit-code: "1"`, `severity: HIGH,CRITICAL`, `ignore-unfixed: true`, `TRIVY_PLATFORM: linux/arm64`) — fails the job before anything is public.
3. A second `docker/build-push-action` with `push: true` and the real `metadata-action` tags. With `cache-from: type=gha` (and the local build cache from step 1), this is a cache-hit re-assembly, not a rebuild — the pushed image is byte-identical to the scanned one.

Alternative considered: push by digest only (no tags), scan the digest, then `buildx imagetools create` the tags. More precise in theory (scans the literal pushed artifact) but adds registry round-trips and an untagged-package cleanup concern; the load-scan-push pattern is the established `trivy-action` idiom and the full-cache-hit rebuild is deterministic.

### D3: Pin `trivy-action` by commit SHA with a human-readable version comment

`aquasecurity/trivy-action@<40-char-sha> # vX.Y.Z` in both `release.yml` and `ci-cd.yml` (the fs-scan job keeps its current SARIF behavior, just pinned). Resolve the SHA from the latest tagged release of the action at implementation time. Dependabot (already configured for github-actions? — if not, the pin is still strictly better than `@master`) can bump it via PR.

### D4: Rollback = pin a previous semver tag in the Pi's compose file

Semver tags (`:v1.2.3`) are immutable once pushed and are *not* moved by later releases, so pinning one both restores the known-good image and freezes Watchtower (it will keep checking the pinned tag, which never changes) until the pin is reverted to `:stable`. Documented in `docs/deployment-and-updates.md` using the existing no-sudo compose-update pattern from CLAUDE.md (scp to /tmp + alpine cp) or a direct edit, plus `docker compose pull && up -d`. Alternative — re-tagging an old digest as `:stable` in GHCR — rejected: requires registry write creds from an operator machine and moves a tag the whole fleet trusts.

## Risks / Trade-offs

- [Trivy gate can block an urgent release on an unfixable CVE] → `ignore-unfixed: true` already excludes CVEs with no upstream fix; `.trivyignore` handles known accepted ones; worst case, add the CVE to `.trivyignore` in the release commit — an explicit, audited override.
- [Second build-push step could theoretically rebuild differently on cache eviction] → both steps run in the same job on the same runner within minutes; the local buildx cache guarantees reuse. Even in the pathological case, the rebuilt image comes from the identical Dockerfile/context and lockfile-pinned deps.
- [`load: true` of an arm64 image on an amd64 runner] → loading is architecture-agnostic (no execution); Trivy scans the image content via `TRIVY_PLATFORM: linux/arm64`, already set today.
- [ci-cd.yml no longer produces amd64 images] → nothing consumed them; dev on macOS builds locally via `compose.dev.yml`.
- [Rollback doc references semver tags that only exist after the first tagged release] → the doc must state the prerequisite (at least one prior `vX.Y.Z` release) and the fallback (`docker compose pull` of a specific older tag visible in GHCR package versions).

## Migration Plan

Pure CI/docs change; no image or Pi migration. Merge to `develop` → `main`; the next push to `main` exercises the reordered `release.yml` (`:latest` path), and the next GitHub Release exercises the `:stable` path. Rollback of this change itself = git revert of the two workflow files.

## Open Questions

- None blocking. The exact trivy-action release SHA is resolved at implementation time.
