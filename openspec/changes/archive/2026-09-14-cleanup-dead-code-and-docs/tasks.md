# Tasks — cleanup-dead-code-and-docs

## 1. Pre-flight verification

- [x] 1.1 Confirm `fix-release-pipeline-race` is merged (its `docker-build` deletion and Trivy pinning in `ci-cd.yml`/`release.yml` are prerequisites for task group 5; do not proceed with group 5 until then)
- [x] 1.2 Re-run reference greps for every file on the delete list (compose files, workflows, docs, code) and confirm no new references appeared since the review; confirm `config/stations.json` is still byte-identical to `backend/assets/stations.json` (`cmp`)
- [x] 1.3 Verify zero production callers of `AudioPlayer.pause/resume/test_playback/get_playback_info/get_current_url/is_playing` (grep `backend/` excluding `audio_player.py` itself and tests) and of `WSVolumeUpdate/WSStationChange/WSPlaybackStatus/WSSystemStatus` outside `core/models.py` and tests

## 2. Delete dead files and fix dangling references

- [x] 2.1 Delete `docker/entrypoint.sh`
- [x] 2.2 Delete `scripts/wifi-init.sh` and `scripts/boot-wifi-check.sh`; remove the stale link at `backend/tests/integration/README.md:307`
- [x] 2.3 Delete `config/systemd/radio-wifi.service` and `scripts/install-service.sh`
- [x] 2.4 Delete `scripts/backend-test-status.sh`, `scripts/ci-pipeline-fix.sh`, `scripts/test-ci.sh`, `scripts/setup-github-protection.sh`, `scripts/dev-environment.sh`, and `scripts/setup-dev.sh` (sole referencer of `dev-environment.sh`)
- [x] 2.5 Delete `config/stations.json`; remove the `../config/stations.json:/app/assets/stations.json:ro` mount from `docker/compose.dev.yml`; fix the `config/stations.json` docstring at `backend/api/routes/radio.py:360`
- [x] 2.6 Delete `config/avahi/` and remove the `traefik` and `avahi` (`mdns` profile) services from `docker/compose.dev.yml`
- [x] 2.7 Delete `config/polkit/` and remove its mount from `docker/compose.dev.yml`
- [x] 2.8 Grep the whole repo (excluding `openspec/changes/archive/` and `docs/project-review-2026-09.md`) for every deleted filename and confirm zero remaining references
- [ ] 2.9 Verify dev stack still works: `docker compose -f docker/compose.dev.yml config` validates, container builds and serves `/health`, and `/api/radio/stations` returns the station library from `/app/assets/stations.json`

## 3. Backend pruning

- [x] 3.1 Remove `aiohttp` and `python-multipart` from `backend/requirements.in`; regenerate the lock from the project root with `pip-compile --generate-hashes --output-file=backend/requirements.lock backend/requirements.in`; diff the lock to confirm only the removed packages and their orphaned transitives disappeared
- [x] 3.2 Dedupe `ApiResponse`: keep `backend/core/models.py:180`, delete the local copies in `backend/api/routes/wifi.py:29` and `backend/api/routes/system.py:194`, import from `core.models` in both routes
- [x] 3.3 Remove `AudioPlayer.pause`, `resume`, `test_playback`, `get_playback_info`, `get_current_url`, and the `is_playing` property from `backend/hardware/audio_player.py`; update mock attributes in `backend/conftest.py` and `backend/tests/unit/test_radio_manager.py` that set `is_playing` on audio-player mocks
- [x] 3.4 Remove `WSVolumeUpdate`, `WSStationChange`, `WSPlaybackStatus`, `WSSystemStatus` from `backend/core/models.py` (keep `WSMessage`); remove their uses from `backend/tests/api/test_websocket.py:184-191`
- [x] 3.5 Consolidate radio.conf parsing: extract one shared parse helper (e.g. in `core/config.py`), use it from both `backend/main.py` (`_load_radio_conf`) and `backend/api/routes/settings.py` (`_read_conf`); preserve each caller's behavior and add a unit test for the shared parser
- [x] 3.6 Run the full backend suite (`python -m pytest` in `backend/`) — all tests pass
- [ ] 3.7 Build the docker image locally (`docker compose -f docker/compose.dev.yml build`) — succeeds with the regenerated lock

## 4. Doc corrections

- [x] 4.1 `README.md:130` — change `POST /api/radio/play/{slot}` to `POST /api/radio/stations/{slot}/play`
- [x] 4.2 `README.md:105` — dev frontend port is 3000, not 5173
- [x] 4.3 `README.md:94` area — remove `data/` from the project tree (runtime data lives on the Pi at `/opt/radio/data/`)
- [x] 4.4 `README.md:73` — station library path is `backend/assets/stations.json`; also drop the now-deleted `avahi/`, `polkit/`, and `config/stations.json` entries from the tree and any references to deleted scripts
- [x] 4.5 `docs/deployment-and-updates.md:140` — remove the claim that the version is displayed on the Settings page
- [x] 4.6 Grep `README.md` and `docs/` for every deleted filename and stale path — zero remaining references

## 5. CI consolidation (blocked on fix-release-pipeline-race)

- [x] 5.1 Slim `test-backend.yml` into the single test workflow: delete the `test-analysis` and `final-status` jobs and all markdown report generation; keep setup/unit/api/websocket/integration/performance jobs with their existing `--timeout` flags
- [x] 5.2 Move the `security` (Trivy filesystem scan) job from `ci-cd.yml` into the test workflow, preserving the SHA-pinned action from `fix-release-pipeline-race`
- [x] 5.3 Delete `ci-cd.yml` (its `integration` job is a duplicate of the test workflow's `integration-tests`; `test-analysis` is deleted; `docker-build` was already removed by `fix-release-pipeline-race`)
- [x] 5.4 Set triggers: test workflow on push to `main` and pull requests to `main`/`develop`; confirm `develop-ci.yml` remains the only workflow triggered by pushes to `develop`
- [x] 5.5 Confirm every workflow keeps an explicit `permissions` block (CodeQL alert #55 pattern) and that only `release.yml` has `packages: write`
- [ ] 5.6 Verify on a test push: exactly one test workflow plus `release.yml` trigger on `main`; all jobs green

## 6. Spec staleness rewrite and final verification

- [ ] 6.1 At sync/archive time, replace the freeform legacy body of `openspec/specs/homepage-radio-controls/spec.md` with the requirements from this change's delta (correct store filenames, no volume slider, `stations_update` message)
- [x] 6.2 Full verification sweep: backend tests pass, frontend builds (`npm run build` in `frontend/`), docker image builds, and a repo-wide grep for all deleted filenames returns no hits outside `openspec/changes/archive/` and the review doc
- [x] 6.3 Run `openspec validate --change "cleanup-dead-code-and-docs"` and confirm clean before archiving
