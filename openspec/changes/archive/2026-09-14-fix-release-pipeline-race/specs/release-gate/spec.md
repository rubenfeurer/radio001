# release-gate Delta — fix-release-pipeline-race

## MODIFIED Requirements

### Requirement: Stable image tag on GitHub Release
The CI pipeline SHALL push a `:stable` tag to GHCR only when a GitHub Release is published — not on every `main` push. Before any tag (`:latest`, `:stable`, semver) is pushed, the pipeline SHALL scan the exact image built in the current run with Trivy; a HIGH or CRITICAL finding (excluding unfixed CVEs and entries in `.trivyignore`) SHALL fail the workflow before anything is published (build → scan → push ordering).

#### Scenario: GitHub Release publishes :stable
- **WHEN** a GitHub Release is published and the Trivy scan of the freshly built image passes
- **THEN** the CI pipeline SHALL build the Docker image
- **AND** push it tagged as `ghcr.io/rubenfeurer/radio001:stable`
- **AND** also push the semver tags (`:v1.2.3`, `:1.2`)

#### Scenario: main push does not update :stable
- **WHEN** a commit is pushed to `main` without a GitHub Release
- **THEN** the CI pipeline SHALL build and push `:latest` (after the scan gate passes)
- **AND** SHALL NOT push or move the `:stable` tag

#### Scenario: :stable is absent before first release
- **WHEN** no GitHub Release has been created yet
- **THEN** `ghcr.io/rubenfeurer/radio001:stable` SHALL NOT exist in GHCR
- **AND** production Pis SHALL continue running their current image until a release is created

#### Scenario: HIGH/CRITICAL finding blocks publishing
- **WHEN** the Trivy scan of the image built in the current run reports a HIGH or CRITICAL vulnerability that is fixed upstream and not listed in `.trivyignore`
- **THEN** the workflow SHALL fail before any push step runs
- **AND** no tag in GHCR SHALL be created or moved by that run

#### Scenario: Scan targets the built artifact, not a registry ref
- **WHEN** the Trivy image scan runs in `release.yml`
- **THEN** it SHALL scan the image produced by the build step of the same workflow run (local image or digest)
- **AND** SHALL NOT scan a previously published registry tag such as `:latest`
