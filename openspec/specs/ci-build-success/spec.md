# ci-build-success Specification

## Purpose
TBD - created by archiving change fix-docker-build-missing-config-templates. Update Purpose after archive.
## Requirements
### Requirement: Docker Build Completion

The Docker build process SHALL complete successfully without errors related to missing configuration files or dependencies.

#### Scenario: CI Pipeline Docker Build

- **WHEN** the CI pipeline runs `docker build` on the backend Dockerfile
- **THEN** the build SHALL complete successfully without file not found errors
- **AND** the build SHALL NOT fail on COPY statements for missing template files
- **AND** all specified packages SHALL be successfully installed

#### Scenario: Missing Configuration Files

- **WHEN** the Dockerfile attempts to COPY configuration template files
- **THEN** no "file not found" errors SHALL occur
- **AND** the build SHALL continue to completion

#### Scenario: Package Installation

- **WHEN** the Dockerfile installs system dependencies via apt-get
- **THEN** all listed packages SHALL be available and successfully installed
- **AND** no packages SHALL be listed that are not actually used by the system

### Requirement: Trivy Security Gate
The release pipeline SHALL block on HIGH and CRITICAL CVEs found in the published image. The Trivy scan step SHALL use `exit-code: "1"` and SHALL NOT use `continue-on-error`.

#### Scenario: Clean image passes Trivy gate
- **WHEN** the ARM64 image is pushed to GHCR and Trivy scans it
- **THEN** no HIGH or CRITICAL unfixed CVEs SHALL be present
- **AND** the pipeline SHALL complete with a success conclusion

#### Scenario: Vulnerable image blocks release
- **WHEN** Trivy finds an unfixed HIGH or CRITICAL CVE in the image
- **THEN** the pipeline SHALL fail
- **AND** the image SHALL remain in GHCR but the release SHALL be considered failed

#### Scenario: starlette CVEs resolved
- **WHEN** the image is built with starlette ≥ 1.0.0
- **THEN** CVE-2024-47874, CVE-2026-24486, and CVE-2025-62727 SHALL NOT appear in the Trivy scan results

