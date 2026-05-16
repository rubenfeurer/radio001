## 1. Compose — unlock config write access

- [ ] 1.1 Change config volume mount from `:ro` to `:rw` in `docker/compose.prod.yml`
- [ ] 1.2 Mirror the same change in the inline compose block in `scripts/install.sh`

## 2. Backend — settings API router

- [ ] 2.1 Create `backend/api/routes/settings.py` with `GET /api/system/settings` — reads `radio.conf`, returns allowlisted fields as JSON
- [ ] 2.2 Add file-lock (`fcntl.flock`) around all file reads/writes to prevent concurrent corruption
- [ ] 2.3 Implement `PUT /api/system/settings` — validates input, writes changed keys back to `radio.conf` in-place (preserving comments and unedited lines), returns `{ changed, restart_required }`
- [ ] 2.4 Add Pydantic request/response models for the settings endpoints in `backend/core/models.py`
- [ ] 2.5 Register the settings router in `backend/main.py` under `/api/system`

## 3. Backend — restart endpoint

- [ ] 3.1 Add `POST /api/system/restart` to the system router — triggers `docker restart` or kills the process so systemd restarts the container
- [ ] 3.2 Ensure the restart endpoint is non-blocking: respond HTTP 200 before the process exits

## 4. Frontend — settings store and API client

- [ ] 4.1 Create `frontend/src/lib/stores/settings.svelte.ts` with `loadSettings()` and `saveSettings(partial)` functions that call the settings API
- [ ] 4.2 Add TypeScript types for the settings payload and API response to `frontend/src/lib/types.ts`

## 5. Frontend — settings page

- [ ] 5.1 Replace the stub in `frontend/src/routes/settings/+page.svelte` with the full settings form
- [ ] 5.2 Implement the three field groups: Hotspot (SSID, Password with show/hide), Volume (Default, Min, Max, Notification), Encoder (Direction toggle, Step, Debounce)
- [ ] 5.3 On load, call `loadSettings()` and populate all fields; show error state if load fails
- [ ] 5.4 Implement Save button: diff current values against loaded values, call `saveSettings()` with only changed fields, do nothing if no changes
- [ ] 5.5 Show inline validation errors from the API (HTTP 422 responses) near the relevant field
- [ ] 5.6 After successful save, show the restart-required banner if `restart_required` is non-empty; banner includes a Restart button and a dismiss option
- [ ] 5.7 Restart button calls `POST /api/system/restart`, shows "Restarting…" state, then dismisses banner

## 6. Deploy and verify

- [ ] 6.1 Commit all changes on `develop`, open PR to `main`, wait for CI and ARM64 image build
- [ ] 6.2 Update `/opt/radio/docker-compose.yml` on Pi with `:rw` mount (scp + alpine trick)
- [ ] 6.3 Pull new image and restart container on Pi
- [ ] 6.4 Navigate to `/settings`, verify all fields load with current conf values
- [ ] 6.5 Change hotspot SSID and save — verify `radio.conf` on Pi is updated, conf comments preserved
- [ ] 6.6 Confirm restart banner appears and Restart button triggers a clean container restart
