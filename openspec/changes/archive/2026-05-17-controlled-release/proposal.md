## Why

Every push to `main` currently triggers a `:latest` image build that Watchtower immediately delivers to all production Pis. There is no way to test on a single Pi before rolling out to the fleet — a bad build goes everywhere automatically.

## What Changes

- Add a `:stable` image tag pushed only when a GitHub Release is created
- Change production Pi Watchtower to track `:stable` instead of `:latest`
- `main` pushes continue to build `:latest` — used for manual testing on the test Pi
- GitHub Releases become the explicit gate for production rollout

## Capabilities

### New Capabilities

- `release-gate`: Controls which image tag (`:stable`) Watchtower uses on production Pis; `:stable` is only pushed on GitHub Release, not on every `main` push

### Modified Capabilities

- `auto-update`: Watchtower image reference changes from `:latest` to `:stable` on production Pis

## Impact

- `.github/workflows/ci-cd.yml`: add `:stable` tag to `metadata-action` tags block (release event only)
- `docker/compose.prod.yml`: change image tag from `:latest` to `:stable`
- Existing Pis: `compose.prod.yml` must be re-pushed to update Watchtower's watched tag
