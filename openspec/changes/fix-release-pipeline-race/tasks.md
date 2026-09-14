# Tasks — fix-release-pipeline-race

## 1. Remove the racing publisher from ci-cd.yml

- [x] 1.1 Delete the `docker-build` job (per-platform matrix, lines ~229–286) from `.github/workflows/ci-cd.yml`
- [x] 1.2 Remove any `needs: docker-build` references and the job's `packages: write` permission; verify no job in ci-cd.yml retains registry write access
- [x] 1.3 Validate ci-cd.yml YAML parses and remaining jobs (integration tests, security fs-scan, test analysis) are intact

## 2. Reorder release.yml to build → scan → push

- [x] 2.1 Split the single `docker/build-push-action` step into: build with `push: false`, `load: true`, local tag `radio001:scan` (keep `cache-from`/`cache-to: type=gha`)
- [x] 2.2 Move the Trivy image scan after the build step, targeting `radio001:scan` with `exit-code: "1"`, `severity: HIGH,CRITICAL`, `ignore-unfixed: true`, `TRIVY_PLATFORM: linux/arm64`
- [x] 2.3 Add the push step after the scan: `docker/build-push-action` with `push: true` and the existing `metadata-action` tags, reusing the buildx cache
- [x] 2.4 Validate release.yml YAML parses and the step order is build → scan → push with no tag pushed before the scan

## 3. Pin trivy-action

- [x] 3.1 Resolve the latest tagged release of `aquasecurity/trivy-action` to its full commit SHA
- [x] 3.2 Replace `@master` with the SHA (plus `# vX.Y.Z` comment) in `.github/workflows/release.yml` and `.github/workflows/ci-cd.yml`

## 4. Document rollback

- [x] 4.1 Add a "Rolling back a bad :stable release" section to `docs/deployment-and-updates.md`: pin `:vX.Y.Z` in `/opt/radio/docker-compose.yml` (using the no-sudo scp + alpine cp pattern), `docker compose pull && up -d`, revert the pin after a fixed release; note the WATCHTOWER_CLEANUP re-pull implication, the tag-freeze effect, and the prerequisite of at least one prior semver release

## 5. Verify

- [x] 5.1 Run a YAML/workflow syntax check over both changed workflows (e.g. `actionlint` if available, else `python -c "import yaml; yaml.safe_load(...)"`)
- [x] 5.2 Grep the repo to confirm `:stable`/`:latest` push logic exists only in release.yml and no `trivy-action@master` reference remains
