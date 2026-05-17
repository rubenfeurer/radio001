## Context

The Pi is running a multi-platform Docker image (`linux/amd64` + `linux/arm64`) built by GitHub Actions CI on an amd64 runner. The current Dockerfile has a deliberately silent-fail lgpio install step:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends liblgpio-dev 2>/dev/null && \
    pip install --no-cache-dir lgpio || true && \
    rm -rf /var/lib/apt/lists/*
```

On the CI runner this step silently fails (either `liblgpio-dev` is absent from the amd64 build environment, or the `apt-get install` exit code short-circuits the `pip install`). The `|| true` swallows the failure, so the image is pushed without lgpio. When pulled on the Pi, `import lgpio` raises `ModuleNotFoundError`, `GPIOController._initialize_hardware()` throws, the except block sets `_gpio_controller = None`, and all hardware input is permanently disabled.

Confirmed on running Pi container:
- `python3 -c "import lgpio"` → `ModuleNotFoundError`
- `/dev/gpiochip0` → accessible inside container
- `id` → `uid=989(radio) groups=989(radio),29(audio),104(netdev)` — no `gpio` group

## Goals / Non-Goals

**Goals:**
- lgpio Python package reliably installed in the arm64 Docker image
- `radio` container user has permission to open `/dev/gpiochip0`
- Station buttons (3×) and rotary encoder (volume + press) functional on Pi
- Startup logs clearly indicate GPIO state (hardware vs mock, and why)

**Non-Goals:**
- Supporting RPi.GPIO or any other GPIO library (lgpio is already wired in)
- Changing the mock-mode fallback logic (still valid for dev/CI)
- Adding new button actions or changing existing button behaviour

## Decisions

### D1 — Build lg C library from source on arm64

**Decision:** Build Joan's `lg` C library from source on arm64 instead of using apt packages.

**Rationale:** Both `python3-lgpio` and `liblgpio-dev` are absent from Debian trixie (confirmed in CI build output). The only reliable path is to download Joan's source zip (`http://abyz.me.uk/lg/lg.zip`), compile it with `make && make install`, run `ldconfig`, then `pip install lgpio` (which wraps the installed shared library via ctypes).

**Alternatives rejected:**
- `apt-get install python3-lgpio` → `E: Unable to locate package python3-lgpio` in Debian trixie
- `apt-get install liblgpio-dev` → `E: Unable to locate package liblgpio-dev` in Debian trixie
- Add lgpio to `requirements.lock` → `requirements.lock` uses `--require-hashes`; lgpio is a C-extension and hashes differ per architecture, adding per-arch hash management for zero benefit

**Working Dockerfile block:**
```dockerfile
RUN arch=$(dpkg --print-architecture) && \
    if [ "$arch" = "arm64" ]; then \
        curl -fsSL http://abyz.me.uk/lg/lg.zip -o /tmp/lg.zip && \
        python3 -c "import zipfile; zipfile.ZipFile('/tmp/lg.zip').extractall('/tmp/')" && \
        cd /tmp/lg && make && make install && \
        ldconfig && \
        cd / && rm -rf /tmp/lg /tmp/lg.zip && \
        pip install --no-cache-dir lgpio; \
    fi
```

**Note:** The `cd /` before cleanup is required. Removing `/tmp/lg` while the shell is inside that directory causes pip to fail with "folder can no longer be found".

### D2 — Architecture-conditional install block

**Decision:** Wrap the lgpio build block in an `arch` check so the amd64 image layer stays unchanged.

**Rationale:** lgpio only makes sense on arm64/Pi. The amd64 image (used in CI and dev) will always fall back to mock mode — building the lg C library on amd64 wastes build time and layer space for no benefit. `build-essential`, `gcc`, `make`, and `curl` are already installed earlier in the Dockerfile so no extra prerequisites are needed.

### D3 — Add gpio group to radio user in Dockerfile

**Decision:** Add `groupadd -g 986 gpio && usermod -a -G gpio radio` and add `group_add: ["986"]` to `compose.prod.yml`.

**Rationale:** `/dev/gpiochip0` on Pi OS is owned by group `gpio` with GID **986** (confirmed via `getent group gpio` and `ls -la /dev/gpiochip0` on the Pi host). Adding group membership in the Dockerfile makes the permission model self-documenting; `group_add` in compose maps the host group into the container at runtime.

**Note:** The design initially estimated GID ~997 based on typical Pi OS documentation. The actual GID on this Pi is **986** — use the numeric GID everywhere (Dockerfile `groupadd -g 986 gpio`, compose `group_add: ["986"]`) to avoid name-resolution mismatch between host and container.

### D4 — Improve diagnostic logging in GPIOController

**Decision:** Log the specific exception when hardware init fails, not just a generic fallback message. Demote the mock-mode confirmation from INFO to DEBUG.

**Before:** Exception swallowed; `GPIO mock interface initialized` appears at INFO level even when mock mode is an unintentional fallback.
**After:** `GPIO hardware init failed: <reason> — falling back to mock mode` at ERROR level; mock confirmation demoted to DEBUG.

### D5 — ALSA volume control: card 2, `sset`, simple name "PCM"

**Decision:** `amixer` calls must specify `-c 2` (card index), use `sset` (simple set), and address the control as `"PCM"` (not `"PCM Playback Volume"`).

**Rationale:** The Pi has multiple ALSA cards:
- Card 0: `vc4-hdmi-0` (HDMI) — no PCM simple control
- Card 2: `bcm2835 Headphones` — has simple control `PCM` with range `[-10239..400]`

Running `amixer` without `-c` targets card 0, producing `Unable to find simple control 'PCM',0`.
Using `set` instead of `sset` invokes the raw mixer interface (requires full path); `sset` is the simple mixer interface that accepts short names like `"PCM"`.

**Confirmed working:** `amixer -c 2 sset PCM 70%` → `Playback -2792 [70%] [-27.92dB] [on]`

**Implementation:**
- `audio_player.py._set_alsa_volume`: use `"sset"` (not `"set"`); default `ALSA_MIXER_CONTROL` to `"PCM"` (not `"PCM Playback Volume"`)
- `compose.prod.yml` and `install.sh`: set `ALSA_MIXER_CONTROL=PCM`

**Env vars (all configurable):**
```
ALSA_DEVICE=hw:2,0          # mpg123 output device
ALSA_MIXER_CARD=2           # amixer card index
ALSA_MIXER_CONTROL=PCM      # amixer simple control name
```

## Risks / Trade-offs

- **lg.zip source URL reliability** → `http://abyz.me.uk/lg/lg.zip` is hosted by the library author. If this goes down, arm64 builds fail. Mitigation: pin to a specific release or mirror the zip; for now this is acceptable for a hobbyist Pi project.
- **gpio GID portability** → GID 986 is correct on this Pi. A different Pi OS image version might use a different GID. Using numeric GID everywhere (not the name "gpio") means the container group still maps correctly as long as the host GID matches.
- **ALSA card index hardcoded to 2** → Another Pi or audio setup might use a different card index. Mitigation: `ALSA_MIXER_CARD` and `ALSA_DEVICE` are configurable via env vars in `compose.prod.yml` / `radio.conf`.
- **Watchtower image replace removes hotfixes** → Hot-patched changes will persist until Watchtower replaces the container. All fixes must land in a released image before the nightly pull.

## Migration Plan

1. Fix Dockerfile (D1, D2, D3) and gpio_controller.py (D4) on develop branch
2. PR → main → CI builds and pushes new arm64 image
3. Manual pull on Pi: `docker pull ghcr.io/rubenfeurer/radio001:latest && docker compose up -d`
4. Verify: `docker exec radio-backend-prod python3 -c "import lgpio; print('ok')"` and button press test
5. Rollback: `docker pull ghcr.io/rubenfeurer/radio001:<previous-sha>` (tag pinning in compose.prod.yml)

## Resolved Questions

- **Does `python3-lgpio` exist in Debian trixie for arm64?** → No. Neither `python3-lgpio` nor `liblgpio-dev` is in trixie. Build from source (see D1).
- **Is the gpio group GID on this Pi 997?** → No. Confirmed GID is **986** via `getent group gpio` on Pi host. All references use 986.
