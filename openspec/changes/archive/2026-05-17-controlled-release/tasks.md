## 1. CI Workflow — add :stable tag

- [x] 1.1 In `.github/workflows/ci-cd.yml`, add `type=raw,value=stable,enable=${{ github.event_name == 'release' }}` to the `metadata-action` tags block in the `docker-build` job

## 2. Production compose — switch to :stable

- [x] 2.1 In `docker/compose.prod.yml`, change `image: ghcr.io/rubenfeurer/radio001:latest` to `image: ghcr.io/rubenfeurer/radio001:stable`
- [x] 2.2 Update the comment at the top of `compose.prod.yml` to say "Watchtower pulls :stable on GitHub Release"

## 3. Install script — use :stable for fresh installs

- [x] 3.1 In `scripts/install.sh`, change `IMAGE="ghcr.io/rubenfeurer/radio001:latest"` to `:stable` and update the inline compose template to reference `:stable`

## 4. First release — produce :stable image

- [x] 4.1 Re-trigger the release event: v0.1.0 was created but the `release: types: [published]` workflow event did not fire — `:stable` was never built. Delete and recreate v0.1.0 (or create v0.1.1) to trigger the build.
- [x] 4.2 Confirm `ghcr.io/rubenfeurer/radio001:stable` appears in GHCR packages after CI completes

## 5. Pi migration — push updated compose

- [x] 5.1 Push updated `compose.prod.yml` to each Pi and restart:
  ```bash
  scp docker/compose.prod.yml radio-z1:/tmp/docker-compose.yml
  ssh radio-z1 "docker run --rm -v /opt/radio:/opt/radio -v /tmp:/tmp alpine cp /tmp/docker-compose.yml /opt/radio/docker-compose.yml"
  ssh radio-z1 "docker compose -f /opt/radio/docker-compose.yml up -d"
  ```
- [x] 5.2 Verify container on each Pi is running `:stable`
