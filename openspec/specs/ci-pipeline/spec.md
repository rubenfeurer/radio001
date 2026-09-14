# ci-pipeline Specification

## Purpose
Defines requirements for the GitHub Actions CI/CD pipeline — workflow correctness, permissions, and test runner behaviour.
## Requirements
### Requirement: No duplicate integration jobs
Across all workflows triggered by a push to `main`, exactly one integration test job SHALL run. Redundant integration jobs duplicated across workflows (`ci-cd.yml`'s `integration` vs `test-backend.yml`'s `integration-tests`) SHALL be consolidated into the single test workflow.

#### Scenario: Single integration job runs
- **WHEN** the CI pipeline triggers on push to `main`
- **THEN** exactly one integration test job SHALL run across all triggered workflows
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

### Requirement: Three-workflow layout
The repository SHALL contain exactly three GitHub Actions workflows: a quick develop gate (lint and type checks, triggered by `develop`), a single consolidated test workflow (triggered by pushes to `main` and pull requests), and `release.yml` (the sole image publisher).

#### Scenario: Push to main triggers one test workflow plus release
- **WHEN** a commit is pushed to `main`
- **THEN** exactly one test workflow SHALL run the pytest suites (unit, api, websocket, integration) and the filesystem security scan
- **AND** `release.yml` SHALL be the only other workflow triggered
- **AND** `ci-cd.yml` SHALL no longer exist (its surviving jobs are merged into the test workflow)

#### Scenario: Push to develop triggers only the quick gate
- **WHEN** a commit is pushed to `develop`
- **THEN** only the develop CI workflow SHALL run
- **AND** the heavy test workflow SHALL NOT be triggered by pushes to `develop`

#### Scenario: Consolidation preserves pytest timeouts
- **WHEN** pytest jobs are moved or merged during consolidation
- **THEN** every `python -m pytest` invocation SHALL retain its `--timeout` flag (120s, or 300s+ for integration) as required elsewhere in this spec

### Requirement: No report-generation jobs
CI workflows SHALL NOT contain jobs whose sole purpose is aggregating other jobs' results into markdown reports or status summaries. Pass/fail status SHALL be conveyed by job conclusions in the Actions UI.

#### Scenario: Markdown report jobs removed
- **WHEN** the workflows are inspected
- **THEN** no `test-analysis` or `final-status` job SHALL exist in any workflow
- **AND** no job SHALL generate markdown test reports as artifacts

### Requirement: ci-cd.yml publishes no container images
The `ci-cd.yml` workflow SHALL NOT build-and-push, tag, or otherwise publish container images to any registry. Image publishing SHALL happen exclusively in `release.yml`.

#### Scenario: Push to main does not publish from ci-cd.yml
- **WHEN** a commit is pushed to `main` and `ci-cd.yml` runs
- **THEN** no job in `ci-cd.yml` SHALL push an image or move any GHCR tag
- **AND** the only workflow pushing `:latest` for that commit SHALL be `release.yml`

#### Scenario: GitHub Release does not trigger publishing from ci-cd.yml
- **WHEN** a GitHub Release is published
- **THEN** `ci-cd.yml` SHALL NOT push `:stable`, semver, or any other tag
- **AND** no `packages: write` permission SHALL be present in `ci-cd.yml`

### Requirement: Trivy action pinned to a commit SHA
Every use of `aquasecurity/trivy-action` in CI workflows SHALL reference a full 40-character commit SHA (with a trailing version comment), never a mutable ref such as `@master`.

#### Scenario: Workflows reference an immutable trivy-action ref
- **WHEN** any workflow step uses `aquasecurity/trivy-action`
- **THEN** the `uses:` ref SHALL be a full commit SHA
- **AND** a comment SHALL record the corresponding release version

