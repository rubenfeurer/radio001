## Why

The `security` job in `ci-cd.yml` is missing `security-events: write` permission, causing the Trivy SARIF upload to GitHub Code Scanning to fail with "Resource not accessible by integration". This blocks CI on every main branch push.

## What Changes

- Add `permissions: security-events: write` to the `security` job in `.github/workflows/ci-cd.yml`

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ci-pipeline`: The security job now has explicit `security-events: write` permission so SARIF upload succeeds.

## Impact

- `.github/workflows/ci-cd.yml` — security job permissions block
