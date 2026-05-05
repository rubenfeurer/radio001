## Why

Hardware settings (GPIO pins, volume, button timings) are hardcoded in `backend/main.py` inside a Python `Config` class. Changing a pin requires editing Python source and rebuilding the Docker image. There's no single place a user can go to configure the device to match their wiring. This change introduces `config/radio.conf` — a plain text key=value file that is already mounted into the container via the `radio_config` Docker volume, so changes take effect after a container restart with no rebuild needed.

## What Changes

### New file: `config/radio.conf`
A `.env`-style file with inline comments documenting every user-facing hardware and behavior setting:
- GPIO pins for 3 station buttons and rotary encoder (BCM numbering + physical pin reference in comments)
- Volume defaults, min/max, step size, and direction
- Button press timing (long press, triple press)
- Rotary encoder debounce
- ALSA mixer control name (PCM vs Master, for non-standard audio setups)
- Default radio station for each slot (name + URL)

### Modified: `backend/main.py` `Config` class
All settings in `radio.conf` are moved to `os.getenv(KEY, default)` calls. The `Config` class loads `radio.conf` at startup via `python-dotenv` (already available or stdlib fallback). Internal/infrastructure settings (paths, CORS, server port, hotspot networking) remain hardcoded or in the compose `environment:` block — they are not user-facing hardware settings.

### Modified: `backend/hardware/gpio_controller.py`
Rotary encoder `_rotation_debounce` (currently hardcoded `0.05`) reads from config.

### Modified: `backend/hardware/audio_player.py`
ALSA mixer control name (currently tries `PCM` then `Master` hardcoded) reads from config.

### Modified: `backend/core/station_manager.py`
Default stations for slots 1–3 read name/URL from config instead of being hardcoded Python objects.

## Capabilities

### New Capabilities
- `user-hardware-config`: All hardware and behavior settings editable in one plain-text file without touching Python or rebuilding Docker

### Modified Capabilities
- `gpio-control`: Pin assignments driven by `radio.conf`
- `audio-playback`: ALSA control name driven by `radio.conf`
- `station-management`: Default stations driven by `radio.conf`

## Impact

- `config/radio.conf`: New file (created, committed to repo as the default template)
- `backend/main.py`: ~10 hardcoded values → `os.getenv()` calls; add dotenv load at startup
- `backend/hardware/gpio_controller.py`: 1 hardcoded debounce value → config
- `backend/hardware/audio_player.py`: 1 hardcoded ALSA control name → config
- `backend/core/station_manager.py`: 3 hardcoded default stations → config
- No frontend changes
- No Docker rebuild required after editing `radio.conf` — restart container only
