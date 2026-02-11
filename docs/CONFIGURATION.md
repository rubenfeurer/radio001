# Configuration Guide

Quick reference for configuring Radio001.

## 📋 Setup

```bash
# 1. Copy example config
cp config/radio.conf.example config/radio.conf

# 2. Edit your settings
nano config/radio.conf

# 3. Restart to apply changes
docker compose -f compose/docker-compose.yml restart
```

## ⚙️ Common Customizations

### Change Hotspot Name & Password
```bash
# In config/radio.conf
HOTSPOT_SSID=Radio001
HOTSPOT_PASSWORD=turnon
```

### Change Hotspot IP Address
```bash
# In config/radio.conf
HOTSPOT_IP=192.168.10.1
HOTSPOT_DHCP_RANGE=192.168.10.2,192.168.10.20
HOTSPOT_URL=http://192.168.10.1
```

### Change mDNS Hostname
```bash
# In config/radio.conf
MDNS_HOSTNAME=radio001
HOSTNAME_URL=http://radio001.local

# Access via: http://radio001.local
```

### Adjust WiFi Timeouts
```bash
# Boot timeout (how long to wait for WiFi on startup)
WIFI_BOOT_TIMEOUT=10

# Connection timeout (manual connection attempts)
WIFI_CONNECT_TIMEOUT=60
```

### Disable Hotspot Fallback
```bash
# Prevent auto-fallback to hotspot on boot
HOTSPOT_ENABLE_FALLBACK=false
```

### Radio Settings
```bash
# Number of station slots
RADIO_STATION_SLOTS=5

# Default volume (0-100)
RADIO_DEFAULT_VOLUME=60

# Volume step for buttons
RADIO_VOLUME_STEP=10
```

## 🔄 Configuration Priority

Settings are loaded in this order (later overrides earlier):

1. **Built-in defaults** (hardcoded in scripts/code)
2. **`config/radio.conf`** (your custom settings)
3. **Environment variables** (docker-compose or shell exports)

### Example Override:
```bash
# Override SSID via environment variable
export HOTSPOT_SSID="TempAP"
docker compose up
```

## 📂 File Locations

| File | Purpose | Location |
|------|---------|----------|
| `radio.conf` | Your config | `config/radio.conf` (gitignored) |
| `radio.conf.example` | Template | `config/radio.conf.example` (tracked) |
| `config/README.md` | Full reference | [View](./config/README.md) |

## 🐳 Docker Integration

Config is loaded in two ways in `docker-compose.yml`:

```yaml
# Loaded as env vars for the backend process
env_file:
  - ../config/radio.conf

# Also mounted for boot scripts
volumes:
  - ../config/radio.conf:/app/config/radio.conf:ro
```

Hotspot config templates are also mounted:
```yaml
volumes:
  - ../config/hostapd/hostapd.conf.template:/etc/hostapd/hostapd.conf.template:ro
  - ../config/dnsmasq/dnsmasq.conf.template:/etc/dnsmasq.conf.template:ro
```

Changes require restart:
```bash
docker compose restart radio-backend
```

## 🔐 Security

- ✅ `radio.conf` is gitignored by default
- ✅ Keep passwords private (min 8 chars for WPA2)
- ✅ Change defaults before production deployment
- ✅ Backup your config before updates

## 🚀 Production Checklist

Before deploying to Raspberry Pi:

- [ ] Copy `radio.conf.example` to `radio.conf`
- [ ] Set unique `HOTSPOT_SSID`
- [ ] Set strong `HOTSPOT_PASSWORD` (8+ chars)
- [ ] Customize `MDNS_HOSTNAME` if needed
- [ ] Review timeout values
- [ ] Backup the config file
- [ ] Test configuration locally first

## 📚 Related Documentation

- **[config/README.md](./config/README.md)** - Detailed configuration reference
- **[README.md](./README.md)** - Project overview and setup
- **[Boot WiFi Behavior](./README.md#what-happens-on-reboot)** - Boot sequence explanation
