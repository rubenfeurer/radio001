## ADDED Requirements

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
- **WHEN** the image is built with starlette ≥ 0.40.0
- **THEN** CVE-2024-47874 and CVE-2026-24486 SHALL NOT appear in the Trivy scan results
