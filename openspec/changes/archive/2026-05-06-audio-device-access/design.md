## Context

The production container runs with `privileged: true`, which implicitly grants access to all host devices including `/dev/snd`. This makes audio work today, but it obscures the actual dependency. If `privileged:` is ever removed for security hardening, audio would break with no obvious cause. Explicit device entries communicate intent and survive privilege reduction.

ALSA exposes audio hardware as `/dev/snd/*` (control nodes, PCM nodes). Docker's `devices:` key passes those nodes into the container namespace.

## Goals / Non-Goals

**Goals:**
- Make the audio device dependency explicit in both the compose file and the install script heredoc
- Document required host devices in the deployment docs

**Non-Goals:**
- Removing `privileged: true` (a separate hardening change; GPIO and NetworkManager also need it)
- Changing how ALSA is configured inside the container

## Decisions

**Decision: Use `/dev/snd` (directory-level) rather than individual nodes**

ALSA creates multiple nodes under `/dev/snd/` (`controlC0`, `pcmC0D0p`, etc.) whose exact names depend on the hardware. Mapping the parent `/dev/snd` entry passes all of them through without needing to enumerate hardware-specific node names.

Alternative considered: map individual nodes (`/dev/snd/controlC0`, `/dev/snd/pcmC0D0p`). Rejected — brittle across different Pi audio HATs and USB audio adapters.

## Risks / Trade-offs

- [No risk] This is additive — `/dev/snd` is currently accessible via `privileged: true` anyway, so no behaviour changes on existing installs
- [Existing installs] Devices key in the compose heredoc inside `install.sh` is rewritten on each run, so re-running install.sh on an existing Pi will add the entry automatically
