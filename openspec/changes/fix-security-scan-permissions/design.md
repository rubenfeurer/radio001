## Context

The `security` job in `.github/workflows/ci-cd.yml` runs Trivy and uploads results as SARIF to GitHub Code Scanning. The workflow-level permissions are `contents: read` only. Without a job-level `security-events: write` grant, the upload step fails with "Resource not accessible by integration", breaking CI on every `main` push.

## Goals / Non-Goals

**Goals:**
- Add `permissions: security-events: write` to the `security` job so SARIF upload succeeds
- Keep all other job permissions unchanged

**Non-Goals:**
- Changing Trivy scan configuration or ignore rules
- Modifying any other job's permissions

## Decisions

**Single job-level permission grant** — Add `security-events: write` alongside the existing pattern of job-level `permissions` blocks (as already done for docker-build and docker-manifest). This avoids widening workflow-level permissions and follows the least-privilege approach already established in this repo.

## Risks / Trade-offs

[Minimal risk] → This is a one-line YAML addition with no logic changes. SARIF upload was already attempted; granting the required permission makes it succeed rather than introducing new behavior.
