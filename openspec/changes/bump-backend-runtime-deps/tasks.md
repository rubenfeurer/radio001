## 1. Update Requirements

- [ ] 1.1 In `backend/requirements.in`, update `pydantic==2.5.3` → `pydantic==2.13.3`
- [ ] 1.2 In `backend/requirements.in`, update `aiohttp==3.9.1` → `aiohttp==3.13.5`
- [ ] 1.3 Regenerate lock file: `docker run --rm -v $(pwd)/backend:/backend python:3.11-slim bash -c "pip install pip-tools -q && pip-compile --generate-hashes --output-file /backend/requirements.lock /backend/requirements.in"`

## 2. Verify

- [ ] 2.1 Build Docker image locally and confirm it starts cleanly
- [ ] 2.2 Run full backend test suite — pay attention to any Pydantic validation errors
- [ ] 2.3 Manually test `GET /system/status` and `POST /api/wifi/connect` to confirm Pydantic models still validate correctly
- [ ] 2.4 Test URL validation via aiohttp (save a station URL and confirm it's accepted)
