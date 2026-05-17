## MODIFIED Requirements

### Requirement: Docker jobs have packages write permission
The docker-build and docker-manifest jobs SHALL have `permissions: packages: write` at job level so they can push images to GHCR even when the workflow-level permission is `contents: read`.

### Requirement: No duplicate integration jobs
The `ci-cd.yml` workflow SHALL contain only one integration test job. The redundant `integration-tests` job SHALL be removed.

### Requirement: Pytest tests have a per-test timeout
All `python -m pytest` invocations in CI workflows SHALL include `--timeout=120` so that a hanging test fails within 2 minutes rather than blocking the runner indefinitely.
