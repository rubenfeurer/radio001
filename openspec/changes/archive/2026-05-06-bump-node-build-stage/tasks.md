## 1. Update Node Build Stage

- [x] 1.1 Updated `docker/Dockerfile` node:20 → node:22-slim (LTS). `docker/Dockerfile.backend` has no Node stage yet (blocked on pi-distribution)
- [x] 1.2 Build the multi-stage image locally and confirm `npm ci && npm run build` completes without errors under Node 25

## 2. Verify

- [x] 2.1 Confirm the final Python image starts and `/health` responds (Node is build-only, not in final image)
- [x] 2.2 Confirm frontend static files are present in the image at `/app/static`
