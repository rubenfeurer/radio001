## ADDED Requirements

### Requirement: Security job has security-events write permission
The `security` job in `ci-cd.yml` SHALL have `permissions: security-events: write` at job level so the Trivy SARIF upload to GitHub Code Scanning succeeds.

#### Scenario: Trivy SARIF upload succeeds
- **WHEN** the security job runs on any CI trigger
- **THEN** the "Upload Trivy scan results" step SHALL succeed
- **AND** the job-level `permissions: security-events: write` SHALL be present
