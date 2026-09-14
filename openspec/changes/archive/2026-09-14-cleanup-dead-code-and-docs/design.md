# Design — cleanup-dead-code-and-docs

## Context

The September 2026 project review (`docs/project-review-2026-09.md`) verified a delete list of dead files, duplicated data, unused backend code, and overlapping CI workflows. Reference-graph facts confirmed by grep before this design:

- `docker/entrypoint.sh` is referenced by nothing (the Dockerfile copies `entrypoint-backend.sh` to `/entrypoint.sh` — same target name, different source).
- `boot-wifi-check.sh` is referenced only by `docker/entrypoint.sh` (also deleted), a doc link in `backend/tests/integration/README.md:307`, and a scenario in `openspec/specs/hotspot-dns-resolution/spec.md` (owned by the `fix-installer-and-hotspot` change).
- `radio-wifi.service` is referenced only by `scripts/install-service.sh` and `scripts/dev-environment.sh` — both also on the delete list.
- `scripts/dev-environment.sh` is referenced by `scripts/setup-dev.sh` (not on the review's list). `setup-dev.sh` is itself referenced by nothing else.
- `config/stations.json` is mounted by `docker/compose.dev.yml:22` and named in a docstring at `backend/api/routes/radio.py:360`, plus two main specs (`project-structure`, `dockerfile-accuracy`) that currently declare it canonical — the reverse of reality (`backend/assets/stations.json` is baked into the image via `COPY backend/ .`).
- `config/polkit` is mounted by `docker/compose.dev.yml:36`; `config/avahi` only by the `mdns` profile service.
- Backend: `ApiResponse` defined 3x; `aiohttp`/`python-multipart` imported nowhere; `AudioPlayer.pause/resume/test_playback/get_playback_info/get_current_url/is_playing` have zero production callers (`RadioManager` tracks its own `_status.is_playing`); `WSVolumeUpdate/WSStationChange/WSPlaybackStatus/WSSystemStatus` used only in `tests/api/test_websocket.py`; `WSMessage` is genuinely used by `api/routes/websocket.py`.
- CI on push to `main` runs `ci-cd.yml` (integration, security, test-analysis, docker-build), `test-backend.yml` (setup, unit, api, websocket, integration-tests, performance, test-analysis, final-status — ~300 lines of markdown report generation), and `release.yml`.

## Goals / Non-Goals

**Goals:**
- Remove every file on the verified delete list plus the references that would dangle.
- One definition each: `ApiResponse`, radio.conf parsing, station library file.
- Three workflows total: `develop-ci.yml` (develop), one test workflow (main + PRs), `release.yml` (publisher).
- Docs and the `homepage-radio-controls` spec describe the system as it exists.

**Non-Goals:**
- No behavior changes to playback, WiFi, GPIO, or the API surface used by the frontend.
- No changes to `docker-build` deletion, Trivy ordering/pinning, or release publishing — that is `fix-release-pipeline-race` scope.
- No touching `config/sounds/` (dev overlay mount, not flagged by the review) or the hotspot dnsmasq path (`fix-installer-and-hotspot` scope).
- No new features, no dependency upgrades.

## Decisions

1. **Canonical station library = `backend/assets/stations.json`.** The image bakes `backend/` wholesale; prod has no `config/` at all. Flipping the two main specs (`project-structure`, `dockerfile-accuracy`) to match reality beats moving the file back to `config/`, which would require Dockerfile changes for zero benefit. In dev, the `../backend:/app` source mount already delivers the file; the explicit `config/stations.json` mount is deleted, not repointed.
2. **Delete `scripts/setup-dev.sh` together with `dev-environment.sh`.** It is a wrapper whose core commands call the deleted script; patching it would preserve a second, divergent dev entry point when `docker compose -f docker/compose.dev.yml up` (per CLAUDE.md) is the supported path. Alternative considered: rewrite setup-dev.sh against compose directly — rejected as new surface area in a cleanup change.
3. **Consolidate CI by slimming `test-backend.yml` and deleting `ci-cd.yml`, in that order, after `fix-release-pipeline-race` lands.** Once that change removes `docker-build`, `ci-cd.yml` retains only `integration` (duplicate of `test-backend.yml`'s `integration-tests`), `security` (Trivy fs scan — moved into the test workflow as a plain job), and `test-analysis` (deleted). Merging into `test-backend.yml` (renamed `test.yml`) keeps its superior job granularity and existing `--timeout` flags (required by the `ci-pipeline` spec). Alternative — keep `ci-cd.yml` and delete `test-backend.yml` — rejected: `ci-cd.yml`'s single `integration` job has less coverage granularity and its remaining content is mostly the report job being deleted.
4. **Report jobs are deleted, not ported.** `test-analysis`/`final-status` regenerate what the Actions UI already shows (per-job pass/fail); their markdown artifacts are read by nothing.
5. **`radio.conf` parsing consolidates into `core/config.py` (or nearest existing shared module).** `main._load_radio_conf` (env-seeding at import) and `settings._read_conf` (dict for the settings API) keep their call sites but share one parse function; behavior of both callers is preserved. Keep the stricter of the two parse behaviors where they differ (comment/quote handling) and cover with a unit test.
6. **`homepage-radio-controls` rewrite ships as ADDED requirements in the delta.** The existing main spec is freeform prose with no `### Requirement:` blocks, so MODIFIED/REMOVED cannot target it by name. The delta defines the full correct requirement set; at sync/archive time the freeform legacy body is replaced by the delta's requirements (noted as an explicit task).
7. **`hotspot-dns-resolution`'s reference to `boot-wifi-check.sh` is deferred**, not fixed here — that spec's dnsmasq requirements are being reworked wholesale by `fix-installer-and-hotspot`; touching it from two active changes invites merge conflicts in `openspec/specs/`.

## Risks / Trade-offs

- [Deleting `is_playing` property breaks external callers] → grep shows zero production callers; test mocks in `conftest.py`/`test_radio_manager.py` set it on mocks only and are updated in the same commit; full pytest run gates the change.
- [Removing the `config/stations.json` dev mount changes dev behavior] → the `../backend:/app` mount already provides `/app/assets/stations.json`; verified identical content (byte-identical duplicate), so dev sees the same data.
- [CI consolidation lands before `fix-release-pipeline-race`, silently deleting `docker-build`] → hard ordering: tasks block on that change being merged; if it is abandoned, `docker-build` must be preserved by moving it, which would be a scope renegotiation, not a silent deletion.
- [`requirements.lock` regeneration pulls surprise transitive updates] → run `pip-compile --generate-hashes` from the project root per CLAUDE.md; diff the lock and confirm only `aiohttp`/`python-multipart` (and their orphaned transitives) disappear.
- [Deleting `scripts/setup-dev.sh` breaks someone's habit] → CLAUDE.md documents the compose-based dev flow; README is updated in the same change.

## Migration Plan

1. Land `fix-release-pipeline-race` first (hard dependency for the CI group).
2. File deletions + compose/docstring/doc-link reference cleanup (one commit, greppable).
3. Backend pruning + lock regeneration + test updates.
4. CI consolidation.
5. Doc corrections.
Rollback: every step is a pure deletion/edit in git with no data migration — `git revert` of the offending commit restores state.

## Open Questions

- None blocking. If `fix-release-pipeline-race` is abandoned, the CI tasks (group 5) need re-scoping to include safe handling of `docker-build`.
