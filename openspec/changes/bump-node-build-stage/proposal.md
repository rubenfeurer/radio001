## Why

The multi-stage Dockerfile will use `node:20-slim` in the frontend build stage (added as part of pi-distribution). Dependabot flagged `node:25` as available. Node 25 is a major version with potential breaking changes to the npm/build tooling used by SvelteKit. Needs a test build before adopting.

## What Changes

- Update the Node build stage in `docker/Dockerfile.backend` from `node:20-slim` to `node:25-slim` (or pinned digest)
- Verify `npm ci && npm run build` succeeds under Node 25
- Confirm the final Python image is unaffected (Node is only in the build stage)

## Capabilities

### Modified Capabilities
- `ci-build-success`: Multi-stage Docker build must succeed with Node 25 build stage

## Impact

- Modified: `docker/Dockerfile.backend` (Node build stage FROM line)
