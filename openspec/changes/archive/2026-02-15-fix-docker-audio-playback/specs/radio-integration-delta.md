# Delta: radio-integration

## Changed Requirements

### Audio Playback Engine
- **Was:** MPV via `python-mpv` library bindings
- **Now:** `mpg123` via `asyncio.subprocess`
- The `AudioPlayer` class interface is unchanged: `play(url)`, `stop()`, `set_volume(volume)`, `pause()`, `resume()`, `is_playing()`
- Volume control uses `amixer` (ALSA) for system-level volume
- `mpg123` process is spawned per stream and terminated on stop

### Docker Dependencies
- **Was:** `python-mpv` Python package (MPV not actually installed)
- **Now:** `mpg123` and `alsa-utils` system packages installed in Dockerfile
- `python-mpv` removed from `requirements.txt`
