## 1. Verify gpio group GID on Pi

- [x] 1.1 SSH into Pi and run `getent group gpio` to confirm the GID (expected ~997)
- [x] 1.2 Confirm `/dev/gpiochip0` group ownership: `ls -la /dev/gpiochip0`

## 2. Fix Dockerfile — lgpio installation

- [x] 2.1 Replace the silent-fail lgpio RUN block in `docker/Dockerfile.backend` with an architecture-conditional install: skip on amd64, install `python3-lgpio` via apt on arm64
- [x] 2.2 Add `usermod -a -G gpio radio` to the user setup RUN block (alongside the existing `usermod -a -G audio radio`)
- [x] 2.3 Verify the updated Dockerfile builds successfully for arm64 (CI or local `docker buildx build --platform linux/arm64`)

## 3. Fix compose.prod.yml — gpio group at runtime

- [x] 3.1 Add `group_add: ["986"]` (gpio GID) to the `radio-backend` service in `docker/compose.prod.yml`
- [x] 3.2 Verify `install.sh` embeds the updated compose — the compose block in `install.sh` must include `group_add` (install.sh has an inline copy of the compose file)

## 4. Improve GPIOController diagnostics

- [x] 4.1 In `backend/hardware/gpio_controller.py` `_initialize_hardware()`, change the bare `except Exception as e` to log the specific exception: `logger.error(f"GPIO hardware init failed: {e} — falling back to mock mode")`
- [x] 4.2 Remove (or demote to DEBUG) the `GPIO mock interface initialized` log line so it doesn't appear at INFO level in production when mock mode is a fallback, not intentional

## 5. Deploy and verify on Pi

- [x] 5.1 Commit all changes on develop, PR to main, wait for CI to build and push arm64 image
- [x] 5.2 On Pi: `docker pull ghcr.io/rubenfeurer/radio001:latest && docker compose -f /opt/radio/docker-compose.yml up -d`
- [x] 5.3 Verify lgpio importable: `docker exec radio-backend-prod python3 -c "import lgpio; print('ok')"`
- [x] 5.4 Verify startup log shows `GPIO hardware initialized successfully via lgpio` (not mock)
- [x] 5.5 Press each of the 3 station buttons and confirm station changes
- [x] 5.6 Turn rotary encoder and confirm volume changes in UI and audio output

## 6. Fix ALSA volume control

Root cause: `amixer` without `-c` targets card 0 (HDMI). Pi headphone output is card 2 (bcm2835 Headphones). Simple control name is `PCM`, not `PCM Playback Volume`. Command must use `sset` (simple set), not `set`.

- [x] 6.1 Fix `audio_player.py._set_alsa_volume`: change `"set"` → `"sset"`; change default `ALSA_MIXER_CONTROL` from `"PCM Playback Volume"` → `"PCM"`
- [x] 6.2 Update `ALSA_MIXER_CONTROL=PCM` in `docker/compose.prod.yml` and the inline compose block in `scripts/install.sh`
- [x] 6.3 Commit on develop, PR → main, wait for CI image build
- [x] 6.4 Pull new image on Pi and restart container
- [x] 6.5 Turn rotary encoder and confirm audio volume changes in output (mark 5.6 complete)
