## Why

`starlette==0.27.0` (bundled with `fastapi==0.104.1`) has CVE-2024-47874 (DoS via multipart/form-data, fixed in starlette 0.40.0) and CVE-2026-24486 (path traversal). Trivy now blocks the release pipeline on these findings; upgrading fastapi resolves both CVEs and restores a blocking security gate.

## What Changes

- Upgrade `fastapi` from `0.104.1` to `0.115.x` (ships starlette ≥ 0.40.0)
- Upgrade `starlette` transitively to `0.40.x+` (fixes both CVEs)
- Upgrade `uvicorn[standard]` from `0.24.0` to `0.32.x` (compatible with new starlette)
- Upgrade `pydantic` if needed for fastapi 0.115 compatibility
- Regenerate `backend/requirements.lock` with new hashes under Python 3.13
- Update `requirements-test.txt`: bump `httpx` to `0.28.x` and `pytest-httpx` to `0.35.0` (starlette 0.40 ships compatible TestClient)
- Fix `conftest.py` `AsyncClient` usage if needed (starlette 0.40 TestClient uses ASGITransport natively)
- Re-enable Trivy `exit-code: "1"` in `release.yml` once CVEs are resolved

## Capabilities

### New Capabilities

- None

### Modified Capabilities

- `ci-build-success`: Trivy scan gate re-enabled (exit-code 1); pipeline now enforces no unresolved HIGH/CRITICAL CVEs

## Impact

- `backend/requirements.in`: fastapi, uvicorn version bumps
- `backend/requirements.lock`: full regeneration under Python 3.13
- `backend/requirements-test.txt`: httpx, pytest-httpx version bumps
- `backend/tests/conftest.py`: may need ASGITransport update (already done; verify still correct)
- `.github/workflows/release.yml`: restore `exit-code: "1"` on Trivy step
- All existing API, WebSocket, integration tests must continue to pass
