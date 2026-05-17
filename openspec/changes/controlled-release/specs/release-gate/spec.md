## ADDED Requirements

### Requirement: Stable image tag on GitHub Release
The CI pipeline SHALL push a `:stable` tag to GHCR only when a GitHub Release is published — not on every `main` push.

#### Scenario: GitHub Release publishes :stable
- **WHEN** a GitHub Release is published
- **THEN** the CI pipeline SHALL build the Docker image
- **AND** push it tagged as `ghcr.io/rubenfeurer/radio001:stable`
- **AND** also push the semver tags (`:v1.2.3`, `:1.2`)

#### Scenario: main push does not update :stable
- **WHEN** a commit is pushed to `main` without a GitHub Release
- **THEN** the CI pipeline SHALL build and push `:latest`
- **AND** SHALL NOT push or move the `:stable` tag

#### Scenario: :stable is absent before first release
- **WHEN** no GitHub Release has been created yet
- **THEN** `ghcr.io/rubenfeurer/radio001:stable` SHALL NOT exist in GHCR
- **AND** production Pis SHALL continue running their current image until a release is created
