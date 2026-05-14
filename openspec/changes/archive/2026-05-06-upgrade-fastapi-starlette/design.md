## Context

The backend uses `fastapi==0.104.1` which pins `starlette==0.27.0`. Two CVEs affect this version:
- **CVE-2024-47874** — DoS via crafted multipart/form-data request (fixed starlette 0.40.0)
- **CVE-2026-24486** — path traversal in static file serving (fixed in later starlette)

The Trivy scan in `release.yml` is currently set to `continue-on-error: true` as a workaround. The goal is to fix the root cause and restore the blocking gate.

`fastapi 0.115.x` is the current stable release line and ships with `starlette>=0.40.0`. It is a minor version bump from 0.104 with no breaking public API changes for this project's usage.

## Goals / Non-Goals

**Goals:**
- Eliminate CVE-2024-47874 and CVE-2026-24486 from the image
- Restore Trivy as a blocking gate (`exit-code: "1"`)
- Keep all existing tests passing with no logic changes
- Upgrade `httpx` in test deps to 0.28.x (unlocked once starlette 0.40 is in place, as TestClient no longer uses the deprecated `app=` kwarg)

**Non-Goals:**
- Adopting new fastapi 0.115 features (no feature work)
- Changing any API routes or business logic
- Migrating Pydantic v1-style models (already on Pydantic v2 — warnings exist but are pre-existing)

## Decisions

**Use fastapi 0.115.x (not 0.110.x or latest)**
fastapi 0.115.x is the latest stable release line that ships starlette ≥ 0.40.0. Earlier 0.11x versions ship starlette 0.36–0.38, which still contain CVE-2024-47874. Latest (0.115.x as of writing) is the safe target.

**Upgrade uvicorn to 0.32.x alongside**
uvicorn 0.24 pins older h11/httptools versions. fastapi 0.115 is tested against uvicorn 0.32; upgrading together avoids subtle ASGI compatibility issues.

**Bump httpx to 0.28.x in test deps**
starlette 0.40 ships a TestClient that uses `ASGITransport` internally — it no longer needs the deprecated `app=` kwarg. `conftest.py` already uses `ASGITransport` explicitly (applied in the release-pipeline change), so this is compatible. `pytest-httpx==0.35.0` supports httpx 0.28.x + pytest 8.x.

**Regenerate lock with Docker (Python 3.13)**
`requirements.lock` must be regenerated inside the same Python 3.13 base image used in CI to guarantee hash reproducibility.

## Risks / Trade-offs

- **Pydantic deprecation warnings** — `core/models.py` uses class-based `Config` (Pydantic v1 style). fastapi 0.115 still supports this but emits warnings. These are pre-existing and out of scope; they will not cause test failures.
  → Mitigation: document as a follow-up task in the Pydantic-migrate change.

- **Starlette 0.40 middleware changes** — starlette 0.40 removed some deprecated middleware APIs. Our project uses only standard `CORSMiddleware` and `app.include_router`; no impact expected.
  → Mitigation: run full test suite to verify.

- **Lock file drift** — upgrading three packages (fastapi, uvicorn, starlette) will pull in new transitive dep versions and new hashes. CI verify-lockfile step will catch any mismatch.
  → Mitigation: regenerate lock inside Docker to match CI environment exactly.

## Migration Plan

1. Update `requirements.in`: fastapi → 0.115.5, uvicorn → 0.32.1
2. Regenerate `requirements.lock` inside `python:3.13-slim` Docker container
3. Update `requirements-test.txt`: httpx → 0.28.1, pytest-httpx → 0.35.0
4. Run backend test suite locally (unit + api + websocket + integration)
5. Restore Trivy `exit-code: "1"` in `release.yml`
6. Open PR to develop → verify CI green → merge → merge to main → confirm Trivy passes

Rollback: revert the `requirements.in`, `requirements.lock`, and `requirements-test.txt` changes; Trivy continues-on-error is already the current state.
