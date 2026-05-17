## 1. CI Workflow — add :stable tag

- [ ] 1.1 In `.github/workflows/ci-cd.yml`, add `type=raw,value=stable,enable=${{ github.event_name == 'release' }}` to the `metadata-action` tags block in the `docker-build` job

## 2. Production compose — switch to :stable

- [ ] 2.1 In `docker/compose.prod.yml`, change `image: ghcr.io/rubenfeurer/radio001:latest` to `image: ghcr.io/rubenfeurer/radio001:stable`
- [ ] 2.2 Update the comment at the top of `compose.prod.yml` to say "Watchtower pulls :stable on GitHub Release"

## 3. Pi migration — push updated compose

- [ ] 3.1 Push updated `compose.prod.yml` to the test Pi and restart:
  ```bash
  scp docker/compose.prod.yml radio-d:/tmp/docker-compose.yml
  ssh radio-d "docker run --rm -v /opt/radio:/opt/radio -v /tmp:/tmp alpine cp /tmp/docker-compose.yml /opt/radio/docker-compose.yml"
  ssh radio-d "docker compose -f /opt/radio/docker-compose.yml up -d"
  ```
- [ ] 3.2 Verify Watchtower on the Pi now references `:stable`:
  ```bash
  ssh radio-d "docker inspect radio-watchtower | grep -A5 Env"
  ```
  (Watchtower uses the image tag from the compose file; confirm radio-backend-prod is running with `:stable`)

## 4. First release — produce :stable image

- [ ] 4.1 Create a GitHub Release (e.g. `v0.1.0`) to trigger the first `:stable` build:
  ```bash
  gh release create v0.1.0 --title "v0.1.0 — controlled release" --notes "First stable release. Watchtower on production Pis now tracks :stable."
  ```
- [ ] 4.2 Confirm `ghcr.io/rubenfeurer/radio001:stable` appears in GHCR packages after CI completes
