## 1. Upgrade Production Dependencies

- [x] 1.1 Update `backend/requirements.in`: bump `fastapi==0.104.1` → `fastapi==0.115.5` and `uvicorn[standard]==0.24.0` → `uvicorn[standard]==0.32.1`
- [x] 1.2 Regenerate `backend/requirements.lock` inside `python:3.13-slim` Docker container using `pip-compile --generate-hashes --output-file=backend/requirements.lock backend/requirements.in`
- [x] 1.3 Verify lock file header reads `Python 3.13` and includes updated fastapi/uvicorn/starlette hashes

## 2. Upgrade Test Dependencies

- [x] 2.1 Update `backend/requirements-test.txt`: bump `httpx==0.27.0` → `httpx==0.28.1` and `pytest-httpx==0.30.0` → `pytest-httpx==0.35.0`
- [x] 2.2 Verify `conftest.py` `AsyncClient(transport=ASGITransport(app=app), ...)` still works with starlette 0.40 (no changes expected — already using correct API)

## 3. Verify Tests Pass

- [x] 3.1 Run unit tests locally and confirm all pass
- [x] 3.2 Run API tests locally and confirm all pass
- [x] 3.3 Run WebSocket tests locally and confirm all pass
- [x] 3.4 Run integration tests locally and confirm all pass

## 4. Re-enable Trivy Security Gate

- [x] 4.1 Remove `continue-on-error: true` from the Trivy scan step in `.github/workflows/release.yml`
- [x] 4.2 Confirm `exit-code: "1"` is set and `ignore-unfixed: true` is retained

## 5. Validate in CI

- [x] 5.1 Open PR develop → main and confirm all test suites pass in CI
- [x] 5.2 Merge to main and confirm release workflow completes: verify-lockfile ✓, build ✓, push ✓, Trivy ✓ (no CVEs)
- [x] 5.3 Confirm `ghcr.io/rubenfeurer/radio001:latest` is updated and Trivy reports zero HIGH/CRITICAL unfixed CVEs
