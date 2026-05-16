## 1. Docker image — add pulseaudio-utils

- [x] 1.1 Add `pulseaudio-utils` to the apt-get install block in `docker/Dockerfile.backend` (provides `pactl`)
- [ ] 1.2 Verify `pactl` is available in a local arm64 build or CI run

## 2. AudioPlayer — PipeWire backend

- [x] 2.1 In `audio_player.py.initialize()`, probe for the PipeWire socket: check `os.path.exists` on the path from `PULSE_SERVER` env var (strip `unix:` prefix); set `self._audio_backend = "pulse"` or `"alsa"` accordingly
- [x] 2.2 In `audio_player.py.play()`, use `mpg123 -o pulse` when `_audio_backend == "pulse"`, or `-o alsa -a $ALSA_DEVICE` for `"alsa"` fallback
- [x] 2.3 In `audio_player.py._set_alsa_volume()`, when `_audio_backend == "pulse"`, run `pactl set-sink-volume @DEFAULT_SINK@ {volume}%`; keep `amixer` path for `"alsa"` fallback
- [x] 2.4 Log which backend is active at startup: `AudioPlayer using PipeWire backend` or `AudioPlayer using direct ALSA fallback`

## 3. Compose and install.sh

- [x] 3.1 Add volume mount `- /run/user/1000/pulse:/run/user/1000/pulse:ro` to `radio-backend` service in `docker/compose.prod.yml`
- [x] 3.2 Add env var `PULSE_SERVER=unix:/run/user/1000/pulse/native` to `radio-backend` service in `docker/compose.prod.yml`
- [x] 3.3 Mirror both changes in the inline compose block in `scripts/install.sh`
- [x] 3.4 In `scripts/install.sh`, add a PipeWire prerequisite block before the container starts: install `pipewire` and `pipewire-pulse` if missing, enable `pipewire.service` and `pipewire-pulse.service` as user services for `$SUDO_USER`, and wait for the socket to appear at `/run/user/1000/pulse/native`

## 4. Deploy and verify

- [x] 4.1 Commit all changes on develop, PR to main, wait for CI to build and push arm64 image
- [x] 4.2 Hot-patch Pi: update `/opt/radio/docker-compose.yml` with socket mount and `PULSE_SERVER` (use `docker run alpine` trick), restart container
- [x] 4.3 Verify backend selection log: `docker logs radio-backend-prod | grep -i 'pipewire\|backend'`
- [ ] 4.4 Verify music plays
- [ ] 4.5 Move OS volume slider — confirm audio output changes
- [ ] 4.6 Turn rotary encoder — confirm audio output changes
- [ ] 4.7 Confirm OS slider and rotary encoder reflect each other (unified control)
