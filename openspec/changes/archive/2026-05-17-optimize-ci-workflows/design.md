## Context

Two GitHub Actions workflows handle CI: `develop-ci.yml` (on push to develop) and `ci-cd.yml` (on push to main / release). Both have accumulated redundant jobs, stub placeholder jobs, and missing caching that adds unnecessary runner minutes to every run.

## Goals / Non-Goals

**Goals:**
- Remove jobs that duplicate work already done by another job in the same run
- Remove stub jobs whose entire body is `echo` placeholder text
- Add npm and pip caching to avoid re-downloading dependencies every run
- Replace hardcoded `sleep 45` with the retry-loop pattern already used in develop-ci.yml

**Non-Goals:**
- Changing what tests are run or their scope
- Merging the two workflow files into one
- Adding new CI capabilities

## Decisions

**Delete stubs entirely rather than keeping them disabled** — `deploy-staging`, `deploy-production`, `docs`, and `notify` in `ci-cd.yml` have never done real work. Keeping disabled jobs adds confusion; removing them keeps the workflow readable. Real deployment can be added back when it's actually implemented.

**Drop `quick-test-validation` entirely** — it runs the identical pytest invocation (`-m 'unit or api or integration'`) as `backend-smoke-test`, just natively instead of in Docker. The Docker run already validates the tests in the target environment, so the native re-run provides no additional signal.

**Drop `success-notification` / `failure-notification`** — GitHub's native job status UI (green/red checkmarks) already communicates this. Running a dedicated runner just to echo a summary string is net-negative.

**`cache: 'npm'`on `setup-node`** — built-in to the action, zero extra config, caches `~/.npm`. Both workflows install the same packages on every run so the hit rate will be high.

**pip caching via `cache-dependency-path`** — `setup-python` supports `cache: 'pip'` with a `cache-dependency-path` pointing at `requirements.lock`. Lock file hash changes invalidate the cache automatically.

## Risks / Trade-offs

[Cache stale after dep update] → Cache keys are derived from lock file hashes, so any `requirements.lock` or `package-lock.json` change automatically busts the cache. No manual intervention needed.

[Retry loop vs sleep] → The retry loop may produce slightly noisier logs on slow starts, but it terminates as soon as the service is ready rather than always waiting 45 s. Net win.
