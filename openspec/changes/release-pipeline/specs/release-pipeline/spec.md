## ADDED Requirements

### Requirement: ARM64 Docker Image Publication
The system SHALL build a linux/arm64 Docker image and publish it to GitHub Container Registry (GHCR) on every push to `main` and on every semver tag.

#### Scenario: Push to main triggers image build and publish
- **WHEN** a commit is pushed to the `main` branch
- **THEN** GitHub Actions SHALL build a linux/arm64 Docker image
- **AND** push it to `ghcr.io/[owner]/radio001:latest`
- **AND** the push SHALL only occur after the Trivy scan passes

#### Scenario: Semver tag triggers versioned image publish
- **WHEN** a git tag matching `v*.*.*` is pushed
- **THEN** GitHub Actions SHALL build a linux/arm64 Docker image
- **AND** push it to `ghcr.io/[owner]/radio001:latest`
- **AND** push it to `ghcr.io/[owner]/radio001:<tag>` (e.g., `v1.2.3`)

#### Scenario: VERSION label baked into image
- **WHEN** the Docker image is built
- **THEN** it SHALL include the OCI label `org.opencontainers.image.version` set to the git tag or short SHA
- **AND** the label SHALL be readable via `docker inspect`

### Requirement: CVE Vulnerability Gate
The CI pipeline SHALL scan the built Docker image for vulnerabilities and block publication on HIGH or CRITICAL severity CVEs that have fixes available.

#### Scenario: Image passes CVE scan
- **WHEN** the built image contains no HIGH or CRITICAL fixable CVEs
- **THEN** the pipeline SHALL proceed to push the image to GHCR

#### Scenario: Image fails CVE scan
- **WHEN** the built image contains one or more HIGH or CRITICAL fixable CVEs
- **THEN** the pipeline SHALL fail and SHALL NOT push the image to GHCR
- **AND** the CVE report SHALL be available in the workflow summary

### Requirement: Dependency Hash Verification
Python backend dependencies SHALL be pinned with SHA256 hashes to prevent supply-chain substitution attacks.

#### Scenario: Docker image uses pinned dependencies
- **WHEN** the Docker image is built
- **THEN** pip SHALL install packages from `requirements.lock` with `--require-hashes`
- **AND** the build SHALL fail if any hash does not match

#### Scenario: Lock file is up to date with source
- **WHEN** the CI pipeline runs on any push
- **THEN** it SHALL verify that `requirements.lock` is consistent with `requirements.in`
- **AND** fail if they are out of sync (i.e., a developer added a package without recompiling)

### Requirement: Automated Dependency Updates
The repository SHALL have Dependabot configured to open pull requests for outdated Python packages and Docker base image upgrades.

#### Scenario: Python dependency update PR
- **WHEN** a new version of a Python package in `requirements.in` is available
- **THEN** Dependabot SHALL open a pull request updating the package and regenerating `requirements.lock`

#### Scenario: Docker base image update PR
- **WHEN** a new digest is available for the pinned base image
- **THEN** Dependabot SHALL open a pull request updating the digest in the Dockerfile
