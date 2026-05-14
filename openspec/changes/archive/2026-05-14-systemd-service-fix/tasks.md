## 1. Fix install.sh

- [x] 1.1 Remove the `echo "Starting services..."` line and `docker compose -f "${COMPOSE_FILE}" up -d` call from install.sh (keep the `docker compose pull` step above it)

## 2. Fix service definition in install.sh

- [x] 2.1 Add `StartLimitIntervalSec=300` and `StartLimitBurst=3` to the `[Service]` section of the embedded service file template in install.sh

## 3. Fix the Pi already installed (radio-d)

- [x] 3.1 Stop existing containers: `docker compose -f /opt/radio/docker-compose.yml down` (done via SSH without sudo)
- [x] 3.2 SSH to radio-d and run `sudo ~/fix-radio-service.sh` (script written to Pi home dir; adds StartLimitIntervalSec/StartLimitBurst and starts service)
- [x] 3.3 Verify: `systemctl status radio.service` shows active (exited) and containers are running

## 4. Commit and push

- [x] 4.1 Commit the install.sh changes on the develop branch with message `fix: prevent double docker-compose start on install; cap service restart loop`
- [x] 4.2 Push to origin/develop
