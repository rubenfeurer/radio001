# ci-pipeline Delta — cleanup-dead-code-and-docs

Note: deleting the `docker-build` publisher job from `ci-cd.yml` and Trivy ordering/pinning are owned by the `fix-release-pipeline-race` change and are intentionally not covered here.

## MODIFIED Requirements

### Requirement: No duplicate integration jobs
Across all workflows triggered by a push to `main`, exactly one integration test job SHALL run. Redundant integration jobs duplicated across workflows (`ci-cd.yml`'s `integration` vs `test-backend.yml`'s `integration-tests`) SHALL be consolidated into the single test workflow.

#### Scenario: Single integration job runs
- **WHEN** the CI pipeline triggers on push to `main`
- **THEN** exactly one integration test job SHALL run across all triggered workflows
- **AND** no duplicate job producing identical test results SHALL exist

## ADDED Requirements

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
