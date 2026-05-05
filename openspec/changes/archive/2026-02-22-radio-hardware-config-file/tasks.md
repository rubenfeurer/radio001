# Tasks: Radio Hardware Config File

## Config File

- [x] Create `config/radio.conf` with all user-facing settings, inline comments, and physical pin references

## Backend — Load Config

- [x] Add dotenv loader to `backend/main.py` startup: load `config/radio.conf` (path: `/app/config/radio.conf` in Docker, `../config/radio.conf` in dev) before `Config` class is evaluated
- [x] Convert all user-facing hardcoded values in `Config` to `os.getenv(KEY, default)`:
  - GPIO: `BUTTON_PIN_1/2/3`, `ROTARY_CLK/DT/SW`, `ROTARY_CLOCKWISE_INCREASES`, `ROTARY_VOLUME_STEP`
  - Button timings: `LONG_PRESS_DURATION`, `TRIPLE_PRESS_INTERVAL`
  - Volume: `DEFAULT_VOLUME`, `MIN_VOLUME`, `MAX_VOLUME`, `NOTIFICATION_VOLUME`

## Backend — GPIO Controller

- [x] Read `_rotation_debounce` from `config.ROTARY_DEBOUNCE` (add to Config, default `0.05`)

## Backend — Audio Player

- [x] Read ALSA mixer control name from `ALSA_MIXER_CONTROL` env var (default `"PCM"`) instead of hardcoded `"PCM"` / `"Master"` fallback

## Backend — WiFi / Hotspot

- [x] Move hotspot settings from compose `environment:` block to `radio.conf`: `HOTSPOT_SSID`, `HOTSPOT_PASSWORD`, `HOTSPOT_IP`, `HOTSPOT_DHCP_RANGE`
- [x] Move WiFi interface settings to `radio.conf`: `WIFI_INTERFACE`, `ETH_INTERFACE`
- [x] Remove those vars from `compose/docker-compose.prod.yml` `environment:` block (they now come from the mounted config file)

## Backend — Station Manager

- [x] Read default station slot 1 name/URL from `DEFAULT_STATION_1_NAME` / `DEFAULT_STATION_1_URL`
- [x] Read default station slot 2 name/URL from `DEFAULT_STATION_2_NAME` / `DEFAULT_STATION_2_URL`
- [x] Read default station slot 3 name/URL from `DEFAULT_STATION_3_NAME` / `DEFAULT_STATION_3_URL`

## Verification

- [ ] Edit a pin in `radio.conf`, restart container (no rebuild), confirm new pin is used
- [ ] Change `DEFAULT_VOLUME` in `radio.conf`, restart, confirm volume initializes correctly
- [ ] Change a default station URL, clear slot, confirm new default loads
