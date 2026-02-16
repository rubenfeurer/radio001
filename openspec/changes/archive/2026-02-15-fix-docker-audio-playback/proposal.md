## Why

Radio playback fails in the Docker container. The backend uses `python-mpv` (Python bindings) but the Docker image (`python:3.11-slim`) never installs the actual `mpv` binary or `libmpv` shared library. When `AudioPlayer.initialize()` runs, the `import mpv` succeeds (the Python package is installed) but `libmpv` can't be found at runtime, causing a silent fallback that leaves the player in a broken state — `mock_mode` gets set but `_is_initialized` logic is inconsistent, resulting in "AudioPlayer not initialized" errors on every play attempt.

Additionally, `mpv` is a poor fit for this use case: it pulls ~3.5MB plus a massive dependency chain (GPU drivers, Wayland, X11, Vulkan) that are unnecessary for headless audio streaming on a Raspberry Pi. All radio stations use MP3 streams.

The audio hardware IS accessible inside the container (`/dev` is mounted, `bcm2835 Headphones` and HDMI audio devices are visible via `/proc/asound/cards`), but there is no audio player to use them.

## What Changes

Replace the MPV-based audio player with `mpg123` — a lightweight, headless MP3 stream player (1MB installed, minimal dependencies) that is well-suited for Raspberry Pi. Add `alsa-utils` for ALSA audio output support. Control `mpg123` as a subprocess from `AudioPlayer` rather than using library bindings.

## Capabilities

### New Capabilities
_(none — this fixes an existing capability that doesn't work)_

### Modified Capabilities
- `radio-integration`: Audio playback engine changes from MPV (broken) to mpg123 (working). Same external API, different underlying player.

## Impact

- `backend/Dockerfile`: Add `mpg123` and `alsa-utils` to `apt-get install`
- `backend/hardware/audio_player.py`: Replace MPV library bindings with `mpg123` subprocess control
- `backend/requirements.txt`: Remove `python-mpv` dependency
- `compose/docker-compose.prod.yml`: Already has `/dev:/dev:rw` mount (audio devices accessible)
- No API changes — `AudioPlayer` interface (`play`, `stop`, `set_volume`, etc.) stays the same
