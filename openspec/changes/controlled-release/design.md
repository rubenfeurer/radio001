## Context

The current `ci-cd.yml` uses `docker/metadata-action` to generate tags. On `main` push it produces `:latest`; on a GitHub Release it produces `:v1.2.3` and `:1.2`. Watchtower on all Pis watches `:latest`, so every `main` merge auto-deploys everywhere with no manual gate.

The test Pi and production Pis are identical in configuration — both run `compose.prod.yml` with `image: ghcr.io/rubenfeurer/radio001:latest`.

## Goals / Non-Goals

**Goals:**
- Add `:stable` tag pushed only on GitHub Release events
- Production Pis track `:stable`, not `:latest`
- Test Pi can manually pull `:latest` for pre-release verification
- Zero new infrastructure — no extra workflow files or services

**Non-Goals:**
- Automated test Pi deploy (manual pull is intentional)
- Rollback automation (Watchtower has no rollback; manual `docker pull` + restart)
- Multiple staging environments

## Decisions

**`:stable` not `:production` or `:release`**
`:stable` is conventional, short, and unambiguous. `:production` implies environment, `:release` is ambiguous with release tags.

**GitHub Release as the release gate (not `workflow_dispatch`)**
GitHub Releases create a permanent record with changelog, are visible in the UI, and already trigger the `ci-cd.yml` workflow. A manual dispatch button gives no audit trail. Using releases is zero extra infrastructure.

**`compose.prod.yml` change rather than per-Pi config**
The compose file is the single source of truth for Pi config. Changing the image tag there and re-pushing to Pis is consistent with how other compose changes are deployed. Watchtower reads the compose file's image tag on startup.

**Keep `:latest` building on `main` push**
`:latest` still builds so the test Pi can `docker pull :latest` at any time without needing a release. `:latest` is not watched by Watchtower on any Pi.

## Risks / Trade-offs

- **Risk**: Pi running old compose file still tracks `:latest` after this change → Mitigation: compose file must be re-pushed to each Pi (see migration plan)
- **Risk**: `:stable` lags `:latest` by however long between merges and releases → Accepted: this is the intended behaviour — explicit control means intentional lag
- **Trade-off**: Two distinct tags to reason about → Offset by clear naming and documented flow

## Migration Plan

1. Add `:stable` tag to `ci-cd.yml` metadata-action tags (release event only)
2. Update `docker/compose.prod.yml` image tag from `:latest` to `:stable`
3. Push updated compose to each Pi and restart:
   ```bash
   scp docker/compose.prod.yml radio-d:/tmp/docker-compose.yml
   ssh radio-d "docker run --rm -v /opt/radio:/opt/radio -v /tmp:/tmp alpine cp /tmp/docker-compose.yml /opt/radio/docker-compose.yml"
   ssh radio-d "docker compose -f /opt/radio/docker-compose.yml up -d"
   ```
4. Create a GitHub Release to produce the first `:stable` image (Pis will have nothing to pull until then)

**Rollback**: Push previous `compose.prod.yml` to Pis and manually pull the previous `:stable` tag (pin to `image: ghcr.io/rubenfeurer/radio001:v1.x.x`).

## Open Questions

- None — scope is small and well-defined.
