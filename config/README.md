# Configuration Directory

Central configuration for Radio001 system settings.

## 📋 Configuration File

### `radio.conf`

Main configuration file for all system settings. Copy from `radio.conf.example` to get started:

```bash
cp config/radio.conf.example config/radio.conf
```

**Important:** `radio.conf` is gitignored - customize it for your setup without committing credentials.

## ⚙️ Configuration Sections

### WiFi Hotspot
```bash
HOTSPOT_SSID=Radio-Setup           # Your hotspot name
HOTSPOT_PASSWORD=Configure123!     # Min 8 characters for WPA2
HOTSPOT_IP=192.168.4.1            # Hotspot IP address
HOTSPOT_DHCP_RANGE=192.168.4.2,192.168.4.20  # DHCP range
```

### Network Access
```bash
MDNS_HOSTNAME=radio               # Access via http://radio.local
HOTSPOT_URL=http://192.168.4.1    # Hotspot mode URL
HOSTNAME_URL=http://radio.local   # Client mode URL
```

### Boot Behavior
```bash
HOTSPOT_ENABLE_FALLBACK=true      # Auto-fallback to hotspot
WIFI_BOOT_TIMEOUT=5               # WiFi check timeout (seconds)
WIFI_CONNECT_TIMEOUT=40           # Connection timeout (seconds)
```

### Radio Settings
```bash
RADIO_STATION_SLOTS=3             # Number of station slots
RADIO_DEFAULT_VOLUME=50           # Default volume (0-100)
RADIO_VOLUME_STEP=5               # Volume adjustment step
```

### Audio
```bash
AUDIO_DEVICE=default              # Audio output device
ENABLE_SOUND_NOTIFICATIONS=true   # Enable system sounds
```

## 🚀 Usage

### Development
Config is automatically loaded via Docker volume mount:
```yaml
volumes:
  - ../config/radio.conf:/app/config/radio.conf:ro
```

### Production
Copy config to Pi and update docker-compose:
```bash
scp config/radio.conf pi@radiod.local:~/radio001/config/
```

### Environment Override
Config values can be overridden via environment variables:
```bash
export HOTSPOT_SSID="MyCustomAP"
docker compose up
```

## 📝 Configuration Priority

1. **Environment variables** (highest priority)
2. **`radio.conf` file**
3. **Built-in defaults** (lowest priority)

## 🔒 Security Notes

- Keep `radio.conf` private (gitignored by default)
- Use strong passwords (min 8 characters for WPA2)
- Change default credentials before deployment
- Backup your config before updates

## 📂 Other Config Files

### `polkit/`
PolicyKit rules for NetworkManager permissions (required for WiFi management).

### Templates
- `radio.conf.example` - Example configuration with defaults
