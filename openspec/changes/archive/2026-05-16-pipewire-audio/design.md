## Context

The Pi runs Raspberry Pi OS Bookworm which ships PipeWire as the default audio session daemon (with `pipewire-pulse` for PulseAudio compatibility). The PulseAudio socket lives at `/run/user/1000/pulse/native`.

Currently `mpg123` writes PCM samples directly to `hw:Headphones` (raw ALSA), bypassing PipeWire. The ALSA PCM hardware mixer register is the only volume gate. Both the OS volume slider (via PipeWire → alsa-sink) and our `amixer -c Headphones sset PCM` write this same register — last write wins, creating two competing controls.

Confirmed in exploration:
- `mpg123 -o pulse` plays successfully from inside the container when `PULSE_SERVER=unix:/run/user/1000/pulse/native`
- `pactl set-sink-volume @DEFAULT_SINK@ 70%` unifies with the OS slider
- The container user `radio` connects to the host PipeWire session owned by `radio-d` (UID 1000) via the mounted socket

## Goals / Non-Goals

**Goals:**
- Single unified volume control: OS slider and rotary encoder are the same thing
- Remove hardcoded ALSA card names/indices from the primary audio path
- Graceful fallback to direct ALSA when PipeWire socket is unavailable

**Non-Goals:**
- PipeWire stream-level isolation (separate per-app volumes)
- Supporting multiple audio sinks or sink selection in the UI
- Removing ALSA env vars entirely (kept for fallback)

## Decisions

### D1 — Route mpg123 through PipeWire via PulseAudio socket

**Decision:** Use `mpg123 -o pulse` with `PULSE_SERVER=unix:/run/user/1000/pulse/native`.

**Rationale:** PipeWire ships `pipewire-pulse` which presents a full PulseAudio-compatible socket. mpg123 has first-class PulseAudio support (`-o pulse`). This requires no new audio libraries — just `pulseaudio-utils` for `pactl`.

**Alternative considered:** Route via PipeWire native protocol (using `pw-play` or libpipewire). Rejected: requires `pipewire-dev` and significant code changes for marginal benefit.

**Alternative considered:** Use ALSA's PulseAudio plugin (`libasound2-plugins`). Rejected: adds complexity and the direct `-o pulse` approach is already confirmed working.

### D2 — Volume control via `pactl set-sink-volume @DEFAULT_SINK@`

**Decision:** Replace `amixer -c Headphones sset PCM` with `pactl set-sink-volume @DEFAULT_SINK@ {volume}%`.

**Rationale:** PipeWire exposes volume via the PulseAudio API. `@DEFAULT_SINK@` targets whatever PipeWire has selected as the default output — no hardcoded device name. The OS slider controls the same sink volume, so after this change both controls are the same PipeWire value.

**Alternative considered:** Control the mpg123 stream volume specifically (`pactl set-sink-input-volume`). Rejected: requires tracking the sink-input index dynamically; `@DEFAULT_SINK@` is simpler and equivalent for a single-output device.

### D3 — Fallback to direct ALSA if PipeWire socket absent

**Decision:** `AudioPlayer.initialize()` probes for the PipeWire socket at startup. If present, uses PulseAudio path. If absent, falls back to direct ALSA (`hw:Headphones`), logging a warning.

**Rationale:** A bare Pi image or a Pi booted without a user session has no PipeWire socket. Falling back silently keeps the radio functional. The fallback also preserves the current working behaviour during the transition.

**Implementation sketch:**
```python
pulse_socket = os.getenv("PULSE_SERVER", "").replace("unix:", "")
if pulse_socket and os.path.exists(pulse_socket):
    self._audio_backend = "pulse"
else:
    self._audio_backend = "alsa"
    logger.warning("PipeWire socket not found — falling back to direct ALSA")
```

### D4 — Mount socket at `/run/user/1000/pulse` in compose

**Decision:** Add volume `- /run/user/1000/pulse:/run/user/1000/pulse:ro` to compose and set `PULSE_SERVER=unix:/run/user/1000/pulse/native`.

**Rationale:** The socket path is fixed for UID 1000 on a standard Raspberry Pi OS install. Mounting read-only is sufficient (the container only connects to the socket, not manages it).

**Risk:** Hardcodes UID 1000. Mitigated: standard Pi OS always assigns UID 1000 to the first user.

### D5 — Ensure PipeWire user session is running before container starts

**Decision:** `install.sh` adds a prerequisite check: verify `pipewire` and `pipewire-pulse` are installed (install if not), and enable `pipewire.service` + `pipewire-pulse.service` as systemd user services for the installing user.

**Rationale:** On a headless Pi without a desktop session, PipeWire user services may not be enabled. The container starting before PipeWire means the socket doesn't exist yet.

**Alternative considered:** Start PipeWire from inside the container. Rejected: PipeWire is a session daemon that must run as the host user; starting it from a container is not practical.

## Risks / Trade-offs

- **PipeWire not running on older Pi OS** → Mitigation: D3 fallback to direct ALSA; D5 ensures it's installed by install.sh
- **Socket path UID assumption (1000)** → Mitigation: acceptable for standard Pi OS; document in install.sh
- **pactl not available** → Mitigation: add `pulseaudio-utils` to Dockerfile; D3 fallback checks pactl availability
- **PipeWire restart clears socket temporarily** → mpg123 loses connection and exits; `_monitor_process` catches the unexpected exit and updates state. Re-play resumes when PipeWire is back. No special handling needed.
- **Volume read-back** → `pactl get-sink-volume @DEFAULT_SINK@` can read current PipeWire volume for sync. Not in scope for this change but easy to add later.

## Migration Plan

1. Add `pulseaudio-utils` to Dockerfile, rebuild image
2. Update `compose.prod.yml`: add socket volume mount and env vars
3. Update `install.sh`: add PipeWire prerequisite, update inline compose
4. Update `audio_player.py`: backend detection, PulseAudio playback path, pactl volume
5. Hot-patch running Pi: update compose file on Pi, restart container
6. Verify: music plays, OS slider and rotary encoder both change volume, UI tracks correctly

**Rollback:** Revert compose env vars to `ALSA_DEVICE=hw:Headphones`, remove socket mount, container uses ALSA fallback path immediately on restart.
