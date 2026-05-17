# ci-pipeline Specification

## Purpose
Defines requirements for the GitHub Actions CI/CD pipeline — workflow correctness, permissions, and test runner behaviour.

## Requirements

### Requirement: Docker jobs have packages write permission
The docker-build and docker-manifest jobs SHALL have `permissions: packages: write` at job level so they can push images to GHCR even when the workflow-level permission is `contents: read`.

#### Scenario: docker-build job pushes to GHCR
- **WHEN** the docker-build job runs on a push to `main` or a GitHub Release
- **THEN** it SHALL successfully push the image to GHCR
- **AND** the job-level `permissions: packages: write` SHALL be present

#### Scenario: docker-manifest job creates multi-arch manifest
- **WHEN** the docker-manifest job runs after docker-build
- **THEN** it SHALL successfully push the manifest to GHCR
- **AND** the job-level `permissions: packages: write` SHALL be present

### Requirement: No duplicate integration jobs
The `ci-cd.yml` workflow SHALL contain only one integration test job. The redundant `integration-tests` job SHALL be removed.

#### Scenario: Single integration job runs
- **WHEN** the CI pipeline triggers on push to `main`
- **THEN** exactly one integration test job SHALL run
- **AND** no duplicate job producing identical test results SHALL exist

### Requirement: Pytest tests have a per-test timeout
All `python -m pytest` invocations in CI workflows SHALL include `--timeout=120` (or higher for integration tests) so that a hanging test fails within a bounded time rather than blocking the runner indefinitely.

#### Scenario: Hanging test is killed by timeout
- **WHEN** a test hangs indefinitely (e.g. stuck asyncio task)
- **THEN** pytest-timeout SHALL kill it after at most 120 seconds
- **AND** the test SHALL be marked as FAILED, not left pending

#### Scenario: Integration tests allow longer timeout
- **WHEN** integration tests run inside a Docker container
- **THEN** the timeout SHALL be at least 300 seconds to account for container startup overhead
