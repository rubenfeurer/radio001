## Context

`install.sh` performs two distinct roles: first-time setup (write config, write service file) and initial service start. The bug is that it does both a direct `docker compose up -d` AND `systemctl enable --now`, causing a double-start conflict. The containers have explicit `container_name` values (`radio-backend-prod`, `radio-watchtower`), so any attempt to create them while they already exist fails with a conflict error rather than a no-op.

A secondary issue: the embedded service definition uses `Restart=on-failure` with `RestartSec=10s` but no `StartLimitBurst` cap. Systemd's default burst window (5 starts in 10s) is never reached because each restart waits 10s — effectively no cap, leading to the infinite loop observed.

## Goals / Non-Goals

**Goals:**
- Service starts successfully on a fresh install with no manual intervention
- Genuine boot failures (e.g., Docker daemon not ready) are retried a bounded number of times, then stop
- No change to the running behaviour after a successful start

**Non-Goals:**
- Changing how existing running Pis update (Watchtower handles that)
- Changing the service type (Type=oneshot RemainAfterExit=yes is correct for `docker compose up -d`)

## Decisions

**Remove direct `docker compose up -d` from install.sh, keep `docker compose pull`.**
`docker compose pull` pre-caches the image so first start is fast. `docker compose up -d` is redundant because `systemctl enable --now` runs it immediately after. Keeping pull + removing up is the minimal change.

Alternative considered: keep the direct `up -d` and add `--remove-orphans` to the service ExecStart. Rejected — it doesn't fix the conflict (containers exist, project names match, `--remove-orphans` removes unrelated containers, not duplicate-named ones).

Alternative considered: add a `sleep 2` between `up -d` and `systemctl enable`. Rejected — fragile, doesn't survive slow systems.

**Add `StartLimitIntervalSec=300 StartLimitBurst=3` to the service.**
In any 5-minute window, at most 3 start attempts. With `RestartSec=10s` this means 3 attempts ~30 seconds apart, then the service enters failed state and requires manual `systemctl reset-failed && systemctl start`. This is the correct behaviour for a persistent configuration problem.

The containers themselves have `restart: unless-stopped` — they recover independently of systemd. The systemd service's job is to start the compose stack once at boot; it doesn't need aggressive retry.

## Risks / Trade-offs

- **Pi in the field won't auto-fix**: existing installed Pis have the buggy service file. They need a manual fix or reinstall. The fix for the Pi in question (radio-d) is documented in the migration plan.
- **First-boot slower if pull is slow**: the image is pre-pulled but if pull fails/is skipped, first start waits for pull. Acceptable — same as before, Watchtower and docker daemon handle it.
- **StartLimitBurst=3 might be too conservative**: if the Pi has a slow boot (e.g., SD card seeking), 3 attempts in 5 minutes might not be enough. Mitigation: `After=network-online.target` already guards against the most common early-boot failure.

## Migration Plan

**For the Pi already installed (radio-d):**
1. Stop the service: `systemctl stop radio.service`
2. Clear failed state: `systemctl reset-failed radio.service`
3. Edit `/etc/systemd/system/radio.service` to add `StartLimitIntervalSec=300` and `StartLimitBurst=3` under `[Service]`
4. `systemctl daemon-reload && systemctl start radio.service`
5. Verify: `systemctl status radio.service` shows active

**For future installs:** pick up fix automatically from updated `install.sh`.

**Rollback:** no rollback needed — the fix is additive/subtractive with no data migration.
