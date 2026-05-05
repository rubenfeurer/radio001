## Why

Two runtime dependencies flagged by Dependabot have significant version gaps:

- `pydantic 2.5.3 → 2.13.3`: Pydantic minor versions have introduced validation behaviour changes in the past (e.g. `Dict[str, float]` strictness). All API models must be verified.
- `aiohttp 3.9.1 → 3.13.5`: Used for radio stream URL validation. Minor API changes possible across 4 minor versions.

Both ship to production on the Pi so must be tested before merging.

## What Changes

- Update `pydantic==2.5.3` → `pydantic==2.13.3` in `backend/requirements.in`
- Update `aiohttp==3.9.1` → `aiohttp==3.13.5` in `backend/requirements.in`
- Regenerate `backend/requirements.lock` with new hashes
- Run full backend test suite and confirm no validation regressions

## Capabilities

### Modified Capabilities
- `ci-build-success`: Docker build must succeed with updated lock file

## Impact

- Modified: `backend/requirements.in` (version pins)
- Modified: `backend/requirements.lock` (regenerated)
