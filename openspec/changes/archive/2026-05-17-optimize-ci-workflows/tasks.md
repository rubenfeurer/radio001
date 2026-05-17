## 1. ci-cd.yml — Fix build failures and deprecated actions

- [x] 1.1 Fix `docker-build` job: change `file: ./docker/Dockerfile` → `file: ./docker/Dockerfile.backend`
- [x] 1.2 Upgrade `github/codeql-action/upload-sarif@v3` → `@v4` in the `security` job
- [x] 1.3 Upgrade Docker actions in `docker-build` job to Node.js 24-compatible versions: `setup-qemu-action`, `setup-buildx-action`, `login-action`, `metadata-action`, `build-push-action`

## 2. develop-ci.yml — Remove redundant and stub jobs

- [x] 2.1 Remove `quick-test-validation` job (duplicates `backend-smoke-test` pytest run)
- [x] 2.2 Remove `success-notification` job (echo-only, no real work)
- [x] 2.3 Remove `failure-notification` job (echo-only, no real work)
- [x] 2.4 Remove `pull_request: branches: [develop]` trigger (PRs targeting develop never happen)

## 3. develop-ci.yml — Add caching

- [x] 3.1 Add `cache: 'npm'` to all `setup-node` steps

## 4. ci-cd.yml — Remove stub and dead jobs

- [x] 4.1 Remove `deploy-staging` job (placeholder echoes only)
- [x] 4.2 Remove `deploy-production` job (placeholder echoes only)
- [x] 4.3 Remove `docs` job (placeholder echoes only)
- [x] 4.4 Remove `notify` job (placeholder echoes only)
- [x] 4.5 Remove dead "Comment PR with test results" step from `test-analysis` job

## 5. ci-cd.yml — Fix Docker wait and caching

- [x] 5.1 Replace hardcoded `sleep 45` with retry loop matching the pattern in `develop-ci.yml`
- [x] 5.2 Remove `--no-cache` flag from Docker build in integration job
- [x] 5.3 Add `cache: 'npm'` to the `setup-node` step in the integration job
