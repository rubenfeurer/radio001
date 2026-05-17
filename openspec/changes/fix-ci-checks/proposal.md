## Why

CI checks on PR #44 are broken in two ways:
1. `ci-cd.yml` fails immediately with "workflow file issue" and 0 jobs — caused by the workflow-level `permissions: contents: read` added in the security hardening commit, which removes `packages: write` from the docker-build job that pushes to GHCR.
2. `test-backend.yml` test jobs hang indefinitely — no `--timeout` on pytest means a single hanging test blocks the runner forever.

## What Changes

- Add `packages: write` permission to the docker-build and docker-manifest jobs in `ci-cd.yml`
- Remove the redundant `integration-tests` job in `ci-cd.yml` (it duplicates `integration` and causes confusion)
- Add `--timeout=120` to all pytest invocations in `test-backend.yml` so a hanging test fails fast instead of blocking the runner

## Capabilities

### Modified Capabilities
- `ci-pipeline`: GitHub Actions workflows for backend tests and release builds
