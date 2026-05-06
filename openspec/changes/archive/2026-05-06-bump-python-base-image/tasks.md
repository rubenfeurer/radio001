## 1. Update Base Image

- [x] 1.1 Pull new image: `docker pull python:3.14-slim` and get digest via `docker inspect python:3.14-slim --format='{{index .RepoDigests 0}}'`
- [x] 1.2 Replace `FROM python:3.11-slim@sha256:...` with `FROM python:3.14-slim@sha256:<new-digest>` in `docker/Dockerfile.backend`

## 2. Regenerate Lock File

- [x] 2.1 Regenerate `backend/requirements.lock` under Python 3.14: `docker run --rm -v $(pwd)/backend:/backend python:3.14-slim bash -c "pip install pip-tools -q && pip-compile --generate-hashes --output-file /backend/requirements.lock /backend/requirements.in"`
- [x] 2.2 Verify lock file header shows Python 3.14

## 3. Verify

- [x] 3.1 Build image locally: `docker build -f docker/Dockerfile.backend -t radio001-py314-test .`
- [x] 3.2 Run backend test suite in the new image and confirm all tests pass
- [x] 3.3 Confirm `/health` endpoint responds in the new container
