## Context

The `AudioPlayer` class (`backend/hardware/audio_player.py`) currently uses `python-mpv` library bindings to control MPV for audio playback. MPV is not installed in the Docker image, so playback always fails. The class has a clean interface: `play(url)`, `stop()`, `set_volume(vol)`, `pause()`, `resume()`, `is_playing()`, with mock mode support and a status callback system. All radio streams are MP3 format from `radio.garden`.

## Goals / Non-Goals

**Goals:**
- Make audio playback work inside the Docker container
- Use minimal dependencies suitable for headless Raspberry Pi
- Maintain the existing `AudioPlayer` interface — no changes to callers
- Support ALSA audio output (bcm2835 Headphones, HDMI)

**Non-Goals:**
- Supporting non-MP3 audio formats (all stations are MP3)
- PulseAudio or PipeWire integration (ALSA direct is sufficient)
- Changing the radio store, API endpoints, or WebSocket protocol

## Decisions

### 1. mpg123 subprocess vs MPV library bindings

**Decision:** Replace MPV with `mpg123` controlled as an `asyncio.subprocess`.

**Rationale:** `mpg123` is 1MB installed with minimal dependencies (just ALSA libs). It handles MP3 streaming natively, runs headless, and is the standard lightweight audio player on Raspberry Pi. Subprocess control via `asyncio.create_subprocess_exec` is simpler and more reliable than library bindings — no shared library loading issues, no import errors.

**Alternative considered:** Install `libmpv-dev` in the Docker image and keep `python-mpv`. Rejected — MPV pulls 3.5MB+ with GPU/X11/Wayland dependencies that are useless in a headless container.

### 2. Volume control approach

**Decision:** Use `amixer` (from `alsa-utils`) for system-level volume control rather than per-process volume.

**Rationale:** `mpg123` supports `-f` (scale factor) for volume, but system-level ALSA volume via `amixer` is more reliable, persists across player restarts, and matches how the hardware rotary encoder controls volume. The existing `AUDIO_DEVICE` config setting maps to an ALSA device.

### 3. Process lifecycle management

**Decision:** Hold a reference to the `mpg123` subprocess. `play()` spawns it, `stop()` terminates it. New `play()` calls stop the previous process first.

**Rationale:** `mpg123` is designed to run as a long-lived streaming process. One process per stream is clean and simple. No IPC or control socket needed — just spawn and kill.

### 4. Mock mode preservation

**Decision:** Keep the existing mock mode logic unchanged. When `mock_mode=True`, skip subprocess spawning and just update internal state.

**Rationale:** Mock mode is used for development and testing without audio hardware. The interface stays the same.

## Risks / Trade-offs

- **MP3 only** — `mpg123` only plays MP3. If stations switch to AAC/OGG, we'd need `ffplay` or `mpv`. Current risk is low since all stations are MP3.
- **No stream metadata** — `mpg123` can output ICY metadata to stdout but parsing it adds complexity. Skipping for now since the frontend doesn't display stream metadata.
- **ALSA device availability** — If the ALSA device isn't available in the container, playback will fail silently. Mitigated by `/dev` mount in docker-compose and the existing `AUDIO_DEVICE` config.
