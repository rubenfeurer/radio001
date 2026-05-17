## Decisions

**Permissions scope**: Add `packages: write` at job level on `docker-build` and `docker-manifest` only. Workflow-level `contents: read` stays — least-privilege principle.

**Duplicate job removal**: `integration-tests` (job id) and `integration` both have `name: Integration Tests` and run overlapping Docker + pytest steps. Remove `integration-tests`; the `integration` job is more complete and is referenced by downstream jobs (`security`, `test-analysis`, `docker-build`).

**Pytest timeout**: Use `pytest-timeout` plugin with `--timeout=120` (2 minutes per test). This is long enough for slow integration tests but short enough to catch hangs. Add `pytest-timeout` to `requirements-test.txt`.
