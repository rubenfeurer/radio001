# Radio WiFi Configuration

A modern, containerized WiFi provisioning solution for Raspberry Pi Zero 2 W, built with Nuxt 3 and optimized for easy setup and deployment.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Node.js](https://img.shields.io/badge/node.js-18+-green.svg)
![Docker](https://img.shields.io/badge/docker-20+-blue.svg)
![Platform](https://img.shields.io/badge/platform-linux%2Farm64-lightgrey.svg)

## 🌟 Features

- 🚀 **Modern Stack**: Built with Nuxt 3, TypeScript, and Nuxt UI
- 📱 **Mobile-First**: Responsive design optimized for smartphone configuration
- 🐳 **Containerized**: Fully dockerized with multi-architecture support
- 🔗 **mDNS Support**: Access via `radio.local` for easy discovery
- 🔄 **Auto-Switch**: Seamless switching between hotspot and client modes
- ⚡ **Pi Zero 2 W Optimized**: Memory and CPU optimizations for 512MB RAM
- 🌐 **Captive Portal**: Optional captive portal for automatic redirection
- 🔧 **Easy Setup**: One-command deployment with Docker Compose

## 🏗️ Architecture

```
radio001/
├── app/                      # Nuxt 3 Application
│   ├── assets/              # Static assets and styles
│   ├── components/          # Vue components
│   ├── composables/         # Nuxt composables
│   ├── pages/               # Application pages
│   ├── server/              # API routes and server utilities
│   ├── types/               # TypeScript definitions
│   └── nuxt.config.ts       # Nuxt configuration
├── docker/                  # Docker configurations
│   ├── Dockerfile           # Production container
│   ├── Dockerfile.dev       # Development container
│   └── entrypoint.sh        # Container entrypoint script
├── scripts/                 # System scripts
│   └── wifi-init.sh         # WiFi initialization script
├── config/                  # System configuration
│   ├── avahi/              # mDNS configuration
│   └── hostapd/            # Hotspot configuration
├── .github/workflows/       # CI/CD pipelines
├── docker-compose.yml       # Development environment
├── docker-compose.prod.yml  # Production environment
└── README.md
```

## 🚀 Quick Start

### Development Setup (Docker)

The project is fully containerized for consistent development across all platforms:

#### Prerequisites

- Docker and Docker Compose
- Git

#### Development Server

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd radio001
   ```

2. **Start development environment:**
   ```bash
   # Basic development environment
   ./scripts/docker-dev.sh start
   
   # Or use Docker Compose directly
   docker-compose up -d
   ```

   This will:
   - Build both frontend (Nuxt 3) and backend (FastAPI) containers
   - Start the frontend on http://localhost:3000
   - Start the backend on http://localhost:8000
   - Enable hot reload for both services

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

#### Development Commands

```bash
# Basic commands
./scripts/docker-dev.sh start     # Start services
./scripts/docker-dev.sh stop      # Stop services
./scripts/docker-dev.sh restart   # Restart services
./scripts/docker-dev.sh status    # Check status

# Advanced commands
./scripts/docker-dev.sh logs                    # View all logs
./scripts/docker-dev.sh logs radio-backend     # View backend logs
./scripts/docker-dev.sh shell radio-app        # Open shell in frontend
./scripts/docker-dev.sh rebuild                # Rebuild all images

# With additional services
./scripts/docker-dev.sh start --traefik        # Start with radio.local access
./scripts/docker-dev.sh start --all            # Start with all services
```

#### Manual Docker Commands

If you prefer using Docker Compose directly:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Production Deployment

### Prerequisites

- Docker and Docker Compose
- Raspberry Pi Zero 2 W (for production)
- Node.js 18+ (for local development)

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd radio001
   ```

2. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. **Start development environment:**
   ```bash
   # Using Docker (recommended)
   npm run dev:docker
   
   # Or locally
   npm run install:app
   npm run dev
   ```

4. **Access the application:**
   - Local: http://localhost:3000
   - mDNS: http://radio.local:3000 (if on Pi)

### Production Deployment

#### On Raspberry Pi

1. **Prepare the Pi:**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker
   curl -sSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   sudo systemctl enable docker
   
   # Install Docker Compose
   sudo apt install docker-compose-plugin
   ```

2. **Clone and configure:**
   ```bash
   git clone <repository-url>
   cd radio001
   cp .env.example .env
   # Edit .env for production settings
   ```

3. **Deploy:**
   ```bash
   # Build and start production containers
   npm run prod:up
   
   # Check logs
   npm run prod:logs
   ```

4. **Access the interface:**
   - Direct IP: http://[pi-ip-address]
   - mDNS: http://radio.local

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Application
NODE_ENV=production
HOSTNAME=radio
NUXT_PORT=3000

# Network
WIFI_INTERFACE=wlan0
ETH_INTERFACE=eth0

# Hotspot
HOTSPOT_SSID=Radio-Setup
HOTSPOT_PASSWORD=radio123
HOTSPOT_IP=192.168.4.1

# Features
ENABLE_CAPTIVE_PORTAL=true
ENABLE_AUTO_CONNECT=true
```

### WiFi Interface Configuration

The system automatically detects and configures WiFi interfaces. For manual configuration:

1. **Check available interfaces:**
   ```bash
   iwconfig
   ```

2. **Update environment:**
   ```env
   WIFI_INTERFACE=wlan0  # Your WiFi interface
   ```

## 📱 Usage

### First-Time Setup

1. **Power on your Raspberry Pi** with the Radio WiFi Configuration
2. **Connect to the hotspot** named `Radio-Setup` (or your configured SSID)
3. **Open a web browser** and navigate to `http://radio.local` or `http://192.168.4.1`
4. **Follow the setup wizard** to configure your WiFi network
5. **The Pi will automatically switch** to client mode and connect to your network

### Changing Networks

1. **Access the interface** via `http://radio.local`
2. **Click "Configure WiFi"** or "Change Network"
3. **Select a new network** from the scan results
4. **Enter credentials** and connect

### System Management

- **View Status**: Real-time connection and system status
- **Network Scan**: Discover available WiFi networks
- **System Info**: Monitor CPU, memory, and network usage
- **Logs**: Access system and application logs

## 🛠️ Development

### Project Structure

#### `/app` - Nuxt 3 Application
- **Modern Vue 3 setup** with Composition API
- **TypeScript support** with strict type checking
- **Nuxt UI components** for consistent design
- **Server-side API routes** for WiFi management
- **Responsive design** optimized for mobile devices

#### `/docker` - Containerization
- **Multi-stage builds** for optimized image sizes
- **ARM64 support** for Raspberry Pi
- **Development and production** configurations
- **Health checks** and proper signal handling

#### `/scripts` - System Integration
- **WiFi management** scripts for scanning and connection
- **Hotspot automation** for seamless mode switching
- **System monitoring** and health checks

### API Endpoints

The application provides RESTful API endpoints:

- `GET /api/health` - System health check
- `GET /api/wifi/status` - Current WiFi status
- `POST /api/wifi/scan` - Scan for networks
- `POST /api/wifi/connect` - Connect to network
- `GET /api/system/status` - System information

### Available Scripts

```bash
# Development
npm run dev              # Start local development
npm run dev:docker       # Start with Docker
npm run dev:logs         # View development logs

# Building
npm run build           # Build application
npm run build:docker    # Build Docker image

# Production
npm run prod:up         # Start production containers
npm run prod:down       # Stop production containers
npm run prod:logs       # View production logs

# Maintenance
npm run health          # Check application health
npm run clean           # Clean build artifacts
npm run clean:docker    # Clean Docker resources
```

## 🔒 Security

### Network Security
- **WPA2/WPA3 support** for secure connections
- **Hotspot password protection** with configurable credentials
- **Network isolation** in hotspot mode

### Application Security
- **Input validation** for all network configurations
- **Secure credential storage** with encryption
- **Rate limiting** for API endpoints
- **CSRF protection** for forms

### Container Security
- **Non-root user** execution
- **Minimal base images** with security updates
- **Read-only filesystems** where possible
- **Capability restrictions** for network operations

## 🐛 Troubleshooting

### Common Issues

#### WiFi Interface Not Found
```bash
# Check available interfaces
iwconfig

# Verify interface name in .env
echo $WIFI_INTERFACE
```

#### Cannot Access radio.local
```bash
# Check Avahi service
sudo systemctl status avahi-daemon

# Restart mDNS
sudo systemctl restart avahi-daemon
```

#### Hotspot Not Starting
```bash
# Check hostapd logs
sudo journalctl -u hostapd

# Verify interface supports AP mode
iw list | grep -A 10 "Supported interface modes"
```

#### Container Health Check Failing
```bash
# Check container logs
docker logs radio-wifi-prod

# Test health endpoint manually
curl http://localhost:3000/api/health
```

### Log Locations

- **Application logs**: `/opt/radio/logs/`
- **Container logs**: `docker logs <container-name>`
- **System logs**: `/var/log/syslog`
- **WiFi logs**: `/var/log/wpa_supplicant.log`

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Guidelines

- **Follow TypeScript best practices**
- **Add tests for new features**
- **Update documentation**
- **Test on actual Raspberry Pi hardware**
- **Ensure mobile responsiveness**

## 📋 Roadmap

### Phase 1: Core Infrastructure ✅
- [x] Project structure and Docker setup
- [x] Nuxt 3 application foundation
- [x] mDNS configuration
- [x] Basic health monitoring

### Phase 2: WiFi Management 🚧
- [ ] WiFi network scanning
- [ ] Network connection management
- [ ] Hotspot automation
- [ ] Status monitoring

### Phase 3: Enhanced Features 📋
- [ ] Captive portal implementation
- [ ] Network profiles and priorities
- [ ] Advanced security options
- [ ] Performance monitoring

### Phase 4: Production Features 📋
- [ ] Backup and restore
- [ ] Remote management
- [ ] Multi-device coordination
- [ ] Analytics and insights

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Nuxt.js team** for the excellent framework
- **Raspberry Pi Foundation** for amazing hardware
- **Docker** for containerization technology
- **Avahi** for mDNS implementation
- **hostapd** for WiFi hotspot functionality

## 📞 Support

- **Documentation**: [Project Wiki](wiki-url)
- **Issues**: [GitHub Issues](issues-url)
- **Discussions**: [GitHub Discussions](discussions-url)
- **Email**: [support@example.com](mailto:support@example.com)

---

**Built with ❤️ for the Raspberry Pi community**