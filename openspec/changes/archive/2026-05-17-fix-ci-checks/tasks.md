## 1. Fix ci-cd.yml permissions

- [x] 1.1 Add `permissions: packages: write` at job level to the `docker-build` job in `.github/workflows/ci-cd.yml`
- [x] 1.2 Add `permissions: packages: write` at job level to the `docker-manifest` job in `.github/workflows/ci-cd.yml`
- [x] 1.3 Remove the entire `integration-tests` job block (lines ~70–161) from `ci-cd.yml` — it duplicates `integration`

## 2. Fix test-backend.yml hanging tests

- [x] 2.1 Add `pytest-timeout==0.5.3` (or latest) to `backend/requirements-test.txt`
- [x] 2.2 Add `--timeout=120` to every `python -m pytest` invocation in `.github/workflows/test-backend.yml`

## 3. Fix pytest-asyncio 1.x incompatibility (stay on latest versions)

- [x] 3.1 Revert `requirements-test.txt` to `pytest==9.0.3` + `pytest-asyncio==1.3.0` (0.25.x requires pytest <9, no 0.x supports pytest 9)
- [x] 3.2 Remove `asyncio_mode = auto` and `--asyncio-mode=auto` from `backend/pytest.ini` — auto mode removed in 1.x, strict is now default
- [x] 3.3 Add `pytestmark = pytest.mark.asyncio` to all 8 test files so async tests run under asyncio in strict mode
- [x] 3.4 Check `asyncio_default_fixture_loop_scope = session` still works in 1.x or update to correct key
