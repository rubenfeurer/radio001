## MODIFIED Requirements

### Requirement: docker-build job uses correct Dockerfile path
The `docker-build` job in `ci-cd.yml` SHALL reference `./docker/Dockerfile.backend` as the build file, not `./docker/Dockerfile` (which does not exist).

#### Scenario: ARM64 image builds successfully on main push
- **WHEN** a push to `main` triggers the `docker-build` job
- **THEN** both `linux/amd64` and `linux/arm64` images SHALL build and push to GHCR without a "no such file or directory" error

### Requirement: CI actions use Node.js 24-compatible versions
All GitHub Actions in CI workflows SHALL use versions that support Node.js 24 to avoid deprecation warnings and ensure compatibility after September 2026.

#### Scenario: No Node.js 20 deprecation warnings on any job
- **WHEN** any CI workflow runs
- **THEN** no "Node.js 20 actions are deprecated" annotation SHALL appear in the run summary

### Requirement: CodeQL action uses v4
The `github/codeql-action/upload-sarif` step SHALL use `@v4`, not `@v3`, which is deprecated in December 2026.

#### Scenario: SARIF upload uses v4
- **WHEN** the security job uploads Trivy results
- **THEN** it SHALL use `github/codeql-action/upload-sarif@v4`

## ADDED Requirements

### Requirement: CI workflows cache npm dependencies
All `setup-node` steps in CI workflows SHALL use `cache: 'npm'` so npm packages are not re-downloaded on every run.

#### Scenario: npm cache hit on repeated run
- **WHEN** the same `package-lock.json` was used in a previous run
- **THEN** `npm install` SHALL restore from cache instead of downloading from the registry

### Requirement: CI workflows cache pip dependencies
Python setup steps in CI workflows SHALL use `cache: 'pip'` with `cache-dependency-path` pointing at `requirements.lock` so pip packages are not re-downloaded on every run.

#### Scenario: pip cache hit on repeated run
- **WHEN** `requirements.lock` has not changed since the previous run
- **THEN** pip install SHALL restore from cache instead of downloading from PyPI

### Requirement: No redundant test jobs in develop-ci
`develop-ci.yml` SHALL NOT contain a `quick-test-validation` job that re-runs the same pytest suite already executed by `backend-smoke-test`.

#### Scenario: Tests run once per develop push
- **WHEN** a push to develop triggers the CI pipeline
- **THEN** the pytest suite SHALL run exactly once (inside the Docker container in `backend-smoke-test`)

### Requirement: No stub placeholder jobs
CI workflows SHALL NOT contain jobs whose entire implementation is `echo` placeholder text. Jobs with no real implementation SHALL be removed.

#### Scenario: All CI jobs perform real work
- **WHEN** any CI job runs
- **THEN** it SHALL perform a real action (build, test, scan, push) rather than only printing placeholder messages

### Requirement: Service readiness uses retry loop not fixed sleep
`ci-cd.yml` integration job SHALL use a retry loop with `curl` health checks to wait for the backend container, not a hardcoded `sleep 45`.

#### Scenario: Service ready before timeout
- **WHEN** the backend container starts within the retry window
- **THEN** the job SHALL proceed as soon as the health check passes, not after a fixed delay
