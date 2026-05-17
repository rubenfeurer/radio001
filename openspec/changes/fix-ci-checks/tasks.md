## 1. Fix ci-cd.yml permissions

- [x] 1.1 Add `permissions: packages: write` at job level to the `docker-build` job in `.github/workflows/ci-cd.yml`
- [x] 1.2 Add `permissions: packages: write` at job level to the `docker-manifest` job in `.github/workflows/ci-cd.yml`
- [x] 1.3 Remove the entire `integration-tests` job block (lines ~70–161) from `ci-cd.yml` — it duplicates `integration`

## 2. Fix test-backend.yml hanging tests

- [x] 2.1 Add `pytest-timeout==0.5.3` (or latest) to `backend/requirements-test.txt`
- [x] 2.2 Add `--timeout=120` to every `python -m pytest` invocation in `.github/workflows/test-backend.yml`
