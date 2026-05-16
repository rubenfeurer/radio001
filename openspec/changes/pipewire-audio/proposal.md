## Why

Moving the OS volume slider (PipeWire) affects the radio's audio output because mpg123 outputs directly to ALSA and both PipeWire and our `amixer` call write the same ALSA PCM hardware register — last writer wins. This creates two competing, unsynchronised volume controls. Routing mpg123 through PipeWire unifies them into one.

## What Changes

- `mpg123` playback switches from `-o alsa -a hw:Headphones` (direct ALSA) to `-o pulse` (PipeWire via PulseAudio compat socket)
- Volume control switches from `amixer -c Headphones sset PCM` to `pactl set-sink-volume @DEFAULT_SINK@`
- The PulseAudio socket (`/run/user/1000/pulse`) is mounted into the container
- `PULSE_SERVER` env var is set in compose so the container can reach the host daemon
- `pulseaudio-utils` is added to the Docker image (provides `pactl`)
- `install.sh` ensures PipeWire is installed and the user session is enabled on the Pi host before starting the container
- Fallback: if the PulseAudio socket is not present at startup, `AudioPlayer` falls back to direct ALSA (`hw:Headphones`) so the radio still works on a bare Pi without a user session
- `ALSA_DEVICE` and `ALSA_MIXER_CARD` env vars are repurposed as fallback-only values (no longer the primary audio path)

## Capabilities

### New Capabilities

- `pipewire-volume-control`: Volume is controlled via PipeWire (pactl), making the OS slider and the rotary encoder the same unified control. Includes fallback to direct ALSA if PipeWire socket is unavailable.

### Modified Capabilities

- `radio-integration`: Playback backend changes from direct ALSA to PipeWire; volume control API changes from amixer to pactl. Observable behaviour (play, stop, volume 0–100) is unchanged, but the audio path and volume authority change.

## Impact

- `backend/hardware/audio_player.py` — playback and volume control methods
- `docker/Dockerfile.backend` — add `pulseaudio-utils`
- `docker/compose.prod.yml` — add socket volume mount and `PULSE_SERVER` env var
- `scripts/install.sh` — add PipeWire host prerequisite check/install; update inline compose block
- No API or frontend changes
