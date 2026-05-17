## Why

The two CI workflows (`develop-ci.yml` and `ci-cd.yml`) contain a build-breaking Dockerfile path bug, redundant jobs, stub jobs that burn runners for no value, missing dependency caching, hardcoded waits, and deprecated action versions — collectively causing build failures and adding unnecessary minutes to every CI run.

## What Changes

- **Fix (blocker)**: Correct `file: ./docker/Dockerfile` → `./docker/Dockerfile.backend` in `docker-build` job (file doesn't exist, ARM64 image never builds)
- **Fix (deprecation)**: Upgrade `github/codeql-action/upload-sarif@v3` → `@v4` (deprecated December 2026)
- **Fix (deprecation)**: Upgrade all Docker actions (`setup-qemu`, `setup-buildx`, `login-action`, `metadata-action`, `build-push-action`) to latest versions that support Node.js 24
- Remove `quick-test-validation` job from `develop-ci.yml` (duplicate of `backend-smoke-test`)
- Remove `success-notification` and `failure-notification` jobs from `develop-ci.yml` (just echo text)
- Remove `deploy-staging`, `deploy-production`, `docs`, and `notify` stub jobs from `ci-cd.yml` (all placeholder echo steps)
- Remove dead "Comment PR with test results" step from `test-analysis` in `ci-cd.yml` (ci-cd.yml never triggers on PRs)
- Remove `--no-cache` flag from Docker build in `ci-cd.yml` integration job
- Replace hardcoded `sleep 45` in `ci-cd.yml` with retry loop (matching develop-ci.yml pattern)
- Add `cache: 'npm'` to `setup-node` steps in both workflows

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ci-pipeline`: Workflow job structure changes — redundant and stub jobs removed, caching added.

## Impact

- `.github/workflows/develop-ci.yml`
- `.github/workflows/ci-cd.yml`
