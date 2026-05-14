## Why

Two Dependabot PRs were held back due to major version bumps that could introduce breaking changes. Now that the CI Docker build fix is in place, these need to be verified and merged to keep the dependency graph current and pick up security/compatibility improvements.

## What Changes

- Upgrade `pytest-asyncio` from 0.24.0 to 1.3.0 in `backend/requirements-test.txt` (PR #24)
- Upgrade the frontend build base image from `node:20-slim` to `node:26-slim` in `docker/Dockerfile.backend` (PR #22)
- Confirm CI passes on both PRs after the Docker build fix propagates via Dependabot rebase
- Merge both PRs once green

## Capabilities

### New Capabilities

_(none — this is a dependency maintenance change)_

### Modified Capabilities

- `ci-build-success`: CI pipeline behaviour changes with node 26 and pytest-asyncio 1.x

## Impact

- `backend/requirements-test.txt`: pytest-asyncio version pin
- `docker/Dockerfile.backend`: node base image tag in frontend-builder stage
- Test suite behaviour: pytest-asyncio 1.x has API changes vs 0.x (loop scope defaults, fixture handling)
- Frontend build: node 26 replaces node 20 in the multi-stage build
