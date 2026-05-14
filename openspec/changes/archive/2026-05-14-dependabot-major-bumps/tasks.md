## 1. Rebase PRs against develop

- [x] 1.1 Comment `@dependabot rebase` on PR #24 (pytest-asyncio 0.24→1.3)
- [x] 1.2 Comment `@dependabot rebase` on PR #22 (node 20→26)

## 2. Verify CI on PR #24 (pytest-asyncio)

- [x] 2.1 Wait for CI to complete on PR #24 after rebase
- [x] 2.2 If tests fail due to pytest-asyncio 1.x API changes, fix `pytest.ini` or affected test files on the PR branch and push
- [x] 2.3 Confirm all CI jobs green on PR #24

## 3. Verify CI on PR #22 (node 26)

- [x] 3.1 Wait for CI to complete on PR #22 after rebase
- [x] 3.2 If frontend build fails on node 26, investigate and fix (or fall back to node 24-slim)
- [x] 3.3 Confirm all CI jobs green on PR #22

## 4. Merge

- [x] 4.1 Merge PR #24 once green
- [x] 4.2 Merge PR #22 once green
