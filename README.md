# Radio WiFi Configuration

A modern WiFi provisioning solution for Raspberry Pi, built with Nuxt 3 and FastAPI. Provides an easy web interface for configuring WiFi networks on headless Raspberry Pi devices.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-required-blue.svg)
![Platform](https://img.shields.io/badge/platform-linux%2Farm64%7Cx86__64-lightgrey.svg)

## ✨ Features

- 🚀 **Modern Web Interface**: Built with Nuxt 3, TypeScript, and Tailwind CSS
- 📱 **Mobile-Friendly**: Responsive design for smartphone configuration
- 🐳 **Containerized**: Docker-based deployment with automatic platform detection
- 🔄 **Mode Switching**: Automatic hotspot ↔ client mode switching
- 🔗 **Easy Access**: Available via `radio.local` or hotspot connection
- ⚡ **Raspberry Pi Optimized**: Efficient performance on Pi Zero 2 W

## 🏗️ How It Works

1. **Hotspot Mode**: Pi creates "Radio-Setup" WiFi network
2. **Web Interface**: Connect and navigate to setup page
3. **Network Selection**: Scan and select your WiFi network
4. **Credentials**: Enter WiFi password securely
5. **Auto-Switch**: Pi automatically switches to client mode
6. **Management**: Access via `radio.local` for ongoing management

## 🚀 Quick Start

### For Developers

```bash
# Setup and start development
git clone <repository-url>
cd radio001
./scripts/setup-dev.sh
./scripts/docker-dev.sh start

# Access application
open http://localhost:3000    # Frontend
open http://localhost:8000    # Backend API
```

### For Production (Raspberry Pi)

```bash
# Install Docker
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Deploy application
git clone <repository-url>
cd radio001
docker compose -f docker-compose.prod.yml up -d

# Access via browser
# http://radio.local or http://[pi-ip-address]
```

**See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup and development workflow.**

## 🔧 Configuration

### Environment Variables

Configure the application with environment variables in `.env`:

```env
# Network Configuration
WIFI_INTERFACE=wlan0
HOSTNAME=radio

# Hotspot Configuration  
HOTSPOT_SSID=Radio-Setup
HOTSPOT_PASSWORD=radio123
HOTSPOT_IP=192.168.4.1

# Features
ENABLE_CAPTIVE_PORTAL=true
ENABLE_AUTO_CONNECT=true
```

### WiFi Management

The system uses a **RaspiWiFi-inspired approach** with modern FastAPI architecture:

- **Network Scanning**: `iwlist scan` command parsing
- **Configuration**: `wpa_supplicant.conf` management
- **Mode Switching**: Automatic hotspot ↔ client mode switching
- **Status Monitoring**: Real-time connection status
- **Development**: Mock data for testing without Pi hardware

## 📱 Usage

### First-Time Setup

1. **Connect** to "Radio-Setup" WiFi network
2. **Navigate** to `http://radio.local` or `http://192.168.4.1`
3. **Select** your WiFi network from the scan results
4. **Enter** WiFi password
5. **Connect** - Pi automatically switches to client mode

### Web Interface

- **Dashboard**: System status and connection info
- **WiFi Setup**: Network scanning and connection wizard
- **System Status**: Detailed monitoring and controls
- **Settings**: Device configuration and preferences

## 📚 Documentation

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Complete development setup and workflow
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Issue resolution guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow conventional commits: `git commit -m 'feat: add amazing feature'`
4. Push and create a Pull Request

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[RaspiWiFi](https://github.com/jasbur/RaspiWiFi)** for inspiring the WiFi management patterns
- **Raspberry Pi Foundation** for amazing hardware
- **Nuxt.js** and **FastAPI** teams for excellent frameworks

---

**Built with ❤️ for the Raspberry Pi community**
