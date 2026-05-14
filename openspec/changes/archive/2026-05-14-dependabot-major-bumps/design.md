## Context

Two Dependabot PRs were held when CI was failing project-wide due to a missing `frontend/package-lock.json` in the Docker build. That root cause has been fixed (switched to `npm install`). The PRs now need a rebase to pick up the fix, then CI verification before merge.

**pytest-asyncio 0.24 → 1.3:** The 1.x series changed the default `asyncio_default_fixture_loop_scope` and tightened async fixture handling. Our pytest.ini already specifies `asyncio_mode = auto` and `asyncio_default_fixture_loop_scope = session`, which should remain valid in 1.x.

**node 20 → 26:** Node 26 is the current LTS. The change only affects the `frontend-builder` stage of the multi-stage Dockerfile — it does not touch the runtime Python image. SvelteKit/Vite/ESLint have no known Node 26 incompatibilities.

## Goals / Non-Goals

**Goals:**
- Get CI green on both PRs after they rebase against the Docker fix
- Merge both PRs once verified clean
- Update `requirements-test.txt` lock entry for pytest-asyncio if needed

**Non-Goals:**
- Rewriting tests to work around pytest-asyncio 1.x changes (if tests break, investigate and fix minimally)
- Upgrading any other dependencies beyond what Dependabot proposed

## Decisions

**Rebase via Dependabot comment rather than manual cherry-pick:** Commenting `@dependabot rebase` triggers Dependabot to rebase the PR onto the current base branch, picking up the Docker fix automatically. This keeps the PR history clean.

**Merge strategy — verify then merge:** Run CI, inspect any failures, fix if needed (e.g., adjust `asyncio_default_fixture_loop_scope` or test markers), then merge with `--merge` (no squash) to match existing Dependabot merge style.

## Risks / Trade-offs

- **pytest-asyncio 1.x test failures** → Mitigation: Check CI output; likely only fixture scope warnings, fixable with one-line config change
- **Node 26 build regression** → Mitigation: Low risk; frontend build is straightforward npm + vite; CI will catch it immediately

## Migration Plan

1. Comment `@dependabot rebase` on PR #24 and PR #22
2. Wait for CI to run on both rebased PRs
3. If green: merge both
4. If pytest-asyncio tests fail: fix `pytest.ini` / test files on the PR branch, push, re-run CI
5. If node 26 build fails: investigate vite/svelte-kit compatibility, pin to node 24-slim if needed
