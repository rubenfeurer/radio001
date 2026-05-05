# Tasks: Radio Boot and Hardware Features

## 1. Config

- [x] 1.1 Change `LONG_PRESS_DURATION=2.0` in `config/radio.conf`
- [x] 1.2 Add `RADIO_STATE_FILE=/app/data/radio_state.json` to `config/radio.conf`
- [x] 1.3 Add `RADIO_STATE_FILE` to `Config` class in `backend/main.py`

## 2. WAV Sound File Generation

- [x] 2.1 Replace `_create_default_sound_files()` in `backend/core/sound_manager.py` with a tone generator using Python stdlib (`wave`, `struct`, `math`) that generates audible two-tone WAV files (success: C5→E5, error: A4→E4)
- [x] 2.2 Update sound file detection in `SoundManager` to treat files with `st_size < 200` as placeholders (in addition to missing files)

## 3. URL Pre-Caching

- [x] 3.1 Update `AudioPlayer.play()` in `backend/hardware/audio_player.py` to check `_url_cache` before calling `_resolve_url()`, and store result in cache on miss (cache dict and lock already added)
- [x] 3.2 Add `_precache_station_urls()` method to `RadioManager` in `backend/core/radio_manager.py` that gets all station URLs and calls `audio_player.precache_urls()`
- [x] 3.3 Call `asyncio.create_task(self._precache_station_urls())` at end of `RadioManager._initialize()`

## 4. Long-Press Wiring

- [x] 4.1 Add `long_press_callback` parameter to `GPIOController.__init__()` in `backend/hardware/gpio_controller.py` (after `volume_callback`)
- [x] 4.2 Update `GPIOController._handle_long_press()` to call `self.long_press_callback(gpio_pin)` via `self._loop.call_soon_threadsafe()` when set
- [x] 4.3 Add `wifi_manager=None` parameter to `RadioManager.__init__()` and `RadioManager.create_instance()` in `backend/core/radio_manager.py`
- [x] 4.4 Add `RadioManager._handle_long_press_event(gpio_pin)` method that calls `wifi_manager.switch_to_host_mode()` or `switch_to_client_mode()` based on current WiFi status, plays success/error sound
- [x] 4.5 Pass `long_press_callback=self._handle_long_press_event` to `GPIOController` in `RadioManager._initialize_hardware()`
- [x] 4.6 Add `wifi_manager=None` parameter to `setup_radio_manager_with_websocket()` in `backend/api/routes/websocket.py` and forward to `RadioManager.create_instance()`
- [x] 4.7 Pass `wifi_manager=wifi_manager` when calling `setup_radio_manager_with_websocket()` in `backend/main.py`

## 5. Boot Sounds + Auto-Play

- [x] 5.1 Add `_state_file` attribute to `RadioManager.__init__()` using `config.RADIO_STATE_FILE`
- [x] 5.2 Add `_save_playback_state(slot, volume)` method to `RadioManager` (atomic write via tmp→rename)
- [x] 5.3 Add `_load_playback_state()` method to `RadioManager` (returns `{"slot": int, "volume": int}` or `None`)
- [x] 5.4 Call `_save_playback_state()` in `RadioManager.play_station()` on success
- [x] 5.5 Call `_save_playback_state()` in `RadioManager.set_volume()` when a station is active
- [x] 5.6 Replace unconditional `play_startup_sound()` in `RadioManager._initialize()` with WiFi-aware boot sound logic (check `wifi_manager.get_status()`, play `startup.wav` on connected client mode, `error.wav` otherwise)
- [x] 5.7 Add auto-play restore at end of `RadioManager._initialize()`: call `_load_playback_state()`, if found set volume and `create_task(play_station(slot))`

## 6. Systemd Install Script

- [x] 6.1 Create `scripts/install-service.sh` that copies the service file to `/etc/systemd/system/`, runs `systemctl daemon-reload && systemctl enable && systemctl start radio-wifi.service`
