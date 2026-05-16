## ADDED Requirements

### Requirement: PipeWire Socket Accessible in Container

The container SHALL have the host PipeWire/PulseAudio socket mounted and `PULSE_SERVER` set so `mpg123` and `pactl` can reach the host audio daemon.

#### Scenario: Socket mount present

- **WHEN** the container starts on a Pi with PipeWire running
- **THEN** `/run/user/1000/pulse/native` is accessible inside the container
- **AND** `PULSE_SERVER=unix:/run/user/1000/pulse/native` is set in the container environment

### Requirement: Audio Playback Routes Through PipeWire

When the PipeWire socket is available, `mpg123` SHALL output via PulseAudio (`-o pulse`) rather than direct ALSA.

#### Scenario: Playback uses PulseAudio backend

- **WHEN** the PipeWire socket is available at startup
- **THEN** `mpg123` is launched with `-o pulse` (no `-a hw:...` device argument)
- **AND** audio is audible through the Pi headphone output

#### Scenario: Fallback to direct ALSA when socket absent

- **WHEN** the PipeWire socket is NOT present at container startup
- **THEN** `mpg123` falls back to `-o alsa -a hw:Headphones`
- **AND** a warning is logged: `PipeWire socket not found — falling back to direct ALSA`
- **AND** audio playback still functions

### Requirement: Volume Control Via PipeWire

When using the PipeWire backend, volume SHALL be controlled via `pactl set-sink-volume @DEFAULT_SINK@`, making the rotary encoder and the OS volume slider the same unified control.

#### Scenario: Volume change applies via pactl

- **WHEN** `set_volume(70)` is called and PipeWire backend is active
- **THEN** `pactl set-sink-volume @DEFAULT_SINK@ 70%` is executed
- **AND** the audible output level changes to match
- **AND** the OS volume slider reflects the new level

#### Scenario: OS slider and rotary encoder are unified

- **WHEN** the OS volume slider is moved to 50%
- **THEN** the radio audio output changes to 50%
- **AND** subsequent rotary encoder turns adjust from 50% (not from a stale internal value)

#### Scenario: Volume fallback uses amixer

- **WHEN** ALSA fallback backend is active
- **THEN** `amixer -c Headphones sset PCM {volume}%` is used for volume control

### Requirement: PipeWire Installed on Pi Host

`install.sh` SHALL verify that `pipewire` and `pipewire-pulse` are installed on the Pi host and that the PipeWire user services are enabled, before starting the container.

#### Scenario: PipeWire installed and enabled

- **WHEN** `install.sh` runs on a Pi
- **THEN** `pipewire` and `pipewire-pulse` packages are present (installed if missing)
- **AND** `pipewire.service` and `pipewire-pulse.service` are enabled as user services for the installing user
- **AND** the PipeWire socket exists at `/run/user/1000/pulse/native` before the container starts
