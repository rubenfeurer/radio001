## Why

The Dockerfile base image is pinned to `python:3.11-slim@sha256:6d85378d...`. Dependabot flagged `python:3.14-slim` as available. Python 3.14 is a major version bump with potential breaking changes in the standard library and C extension APIs. Testing is required before adopting it on the Pi.

## What Changes

- Update `FROM python:3.11-slim@sha256:...` to `python:3.14-slim@sha256:<new-digest>` in `docker/Dockerfile.backend`
- Regenerate `backend/requirements.lock` under Python 3.14 (hash values change per interpreter)
- Verify all backend tests pass under the new runtime
- Update `ARG VERSION` label remains unchanged

## Capabilities

### Modified Capabilities
- `ci-build-success`: Docker build must succeed with Python 3.14 base image

## Impact

- Modified: `docker/Dockerfile.backend` (FROM line + digest)
- Modified: `backend/requirements.lock` (regenerated under Python 3.14)
