## Why

The radio currently requires manual interaction to start playing after boot, has no audio feedback during startup, and physical hardware controls are missing two key behaviours: fast stream switching and a hotspot-toggle gesture. These gaps make the device feel unfinished as a standalone appliance.

## What Changes

- **Stream pre-caching**: Resolve stream redirect URLs in the background at startup so pressing a button starts audio immediately instead of waiting up to 5s for a curl redirect resolution.
- **Rotary long-press → WiFi mode toggle**: Holding the rotary encoder button for 2 seconds switches between WiFi client mode and hotspot mode. Plays `success.wav` on success.
- **Boot sounds**: On startup, play `startup.wav` when connected to WiFi and ready to stream; play `error.wav` when WiFi connection failed and hotspot mode was activated.
- **Auto-play last slot on boot**: Persist the last-played station slot and volume to a state file. On boot, restore volume and auto-play the last active station.
- **Auto-start on boot**: Install and enable a systemd service so the Docker stack starts automatically on Pi power-on. Includes an install script.
- **Real WAV sound files**: Replace placeholder text files in `assets/sounds/` with generated audible tones using Python stdlib (`wave`, `struct`, `math`) — no new dependencies.

## Capabilities

### New Capabilities
- `boot-behaviour`: Auto-start on power-on, boot sounds (WiFi-aware), auto-play last session, state persistence across reboots.

### Modified Capabilities
- `radio-integration`: Stream pre-caching added to AudioPlayer; last-played state persistence added to RadioManager; long-press hardware event wired from GPIOController through RadioManager.
- `hotspot-configuration`: Hotspot/client mode can now be toggled via physical hardware (rotary long-press), not only via the web UI.

## Impact

- `backend/hardware/audio_player.py`: add `_url_cache`, `precache_urls()`, use cache in `play()`
- `backend/hardware/gpio_controller.py`: add `long_press_callback` constructor param, forward in `_handle_long_press()`
- `backend/core/radio_manager.py`: accept `wifi_manager` param; add `_handle_long_press_event()`, `_save_playback_state()`, `_load_playback_state()`, `_precache_station_urls()`; update `_initialize()` for WiFi-aware sounds and auto-play
- `backend/core/sound_manager.py`: replace placeholder WAV generator with audible tone generator (stdlib only)
- `backend/api/routes/websocket.py`: propagate `wifi_manager` to `RadioManager.create_instance()`
- `backend/main.py`: pass `wifi_manager` to radio setup; add `RADIO_STATE_FILE` to Config
- `config/radio.conf`: change `LONG_PRESS_DURATION=2.0`, add `RADIO_STATE_FILE=/app/data/radio_state.json`
- `config/systemd/radio-wifi.service`: verify correct, no change expected
- `scripts/install-service.sh`: new script to install and enable systemd service on Pi
- No API changes, no frontend changes, no new Python dependencies
