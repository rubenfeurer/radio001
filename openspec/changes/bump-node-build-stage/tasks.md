## 1. Update Node Build Stage

- [ ] 1.1 In `docker/Dockerfile.backend`, update the frontend build stage `FROM node:20-slim` to `FROM node:25-slim` (once pi-distribution Dockerfile is written; skip if stage not yet added)
- [ ] 1.2 Build the multi-stage image locally and confirm `npm ci && npm run build` completes without errors under Node 25

## 2. Verify

- [ ] 2.1 Confirm the final Python image starts and `/health` responds (Node is build-only, not in final image)
- [ ] 2.2 Confirm frontend static files are present in the image at `/app/static`
