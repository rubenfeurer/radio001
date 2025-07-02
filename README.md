# Radio WiFi Configuration

A modern, containerized WiFi provisioning solution for Raspberry Pi Zero 2 W, built with Nuxt 3 and FastAPI, optimized for easy setup and cross-platform development.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Node.js](https://img.shields.io/badge/node.js-18+-green.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/docker-20+-blue.svg)
![Platform](https://img.shields.io/badge/platform-linux%2Farm64%7Cx86__64-lightgrey.svg)
![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-M1%2FM2%20Ready-green.svg)

## 🌟 Features

- 🚀 **Modern Stack**: Built with Nuxt 3, FastAPI, TypeScript, and Nuxt UI
- 📱 **Mobile-First**: Responsive design optimized for smartphone configuration
- 🐳 **Containerized**: Fully dockerized with multi-architecture support
- 🍎 **Apple Silicon Ready**: Optimized for M1/M2 Macs with automatic platform detection
- 🔗 **mDNS Support**: Access via `radio.local` for easy discovery
- 🔄 **Auto-Switch**: Seamless switching between hotspot and client modes
- ⚡ **Pi Zero 2 W Optimized**: Memory and CPU optimizations for 512MB RAM
- 🌐 **Captive Portal**: Optional captive portal for automatic redirection
- 🔧 **Easy Setup**: One-command deployment with Docker Compose
- 🔄 **Hot Reload**: Real-time development with instant code changes

## 🏗️ Architecture

```
radio001/
├── app/                          # Frontend (Nuxt 3)
│   ├── assets/css/              # Global styles and Tailwind CSS
│   ├── components/              # Vue components
│   │   └── SignalStrength.vue   # WiFi signal indicator
│   ├── composables/             # Vue composables
│   │   └── useWiFi.ts          # WiFi state management
│   ├── pages/                   # Application pages
│   │   ├── index.vue           # Dashboard
│   │   ├── setup.vue           # WiFi setup wizard
│   │   ├── status.vue          # System status
│   │   └── settings.vue        # Configuration
│   ├── server/api/              # API proxy routes
│   │   ├── [...path].ts        # Backend API proxy
│   │   ├── health.ts           # Health check
│   │   ├── system/             # System management APIs
│   │   ├── wifi/               # WiFi management APIs
│   │   └── config/             # Configuration APIs
│   ├── types/                   # TypeScript definitions
│   └── nuxt.config.ts          # Nuxt configuration
├── backend/                     # Backend (FastAPI)
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt        # Python dependencies
│   └── package.json            # Node.js metadata
├── docker/                      # Docker configurations
│   ├── Dockerfile.dev          # Frontend development
│   ├── Dockerfile.backend      # Backend standard
│   ├── Dockerfile.backend.arm64 # Apple Silicon optimized
│   ├── entrypoint-backend.sh   # Backend entrypoint
│   └── entrypoint.sh           # Frontend entrypoint
├── scripts/                     # Development scripts
│   ├── docker-dev.sh           # Docker development manager
│   └── wifi-init.sh            # WiFi initialization
├── config/                      # System configuration
│   ├── avahi/                  # mDNS configuration
│   └── hostapd/                # Hotspot configuration
├── docker-compose.yml          # Development environment
├── docker-compose.override.yml # Apple Silicon overrides
├── docker-compose.prod.yml     # Production environment
├── DEVELOPMENT.md              # Development guide
├── TROUBLESHOOTING.md          # Issue resolution
└── README.md
```

## 🚀 Quick Start

### Development Setup (Docker)

The project is fully containerized with **automatic Apple Silicon (M1/M2) detection** for seamless cross-platform development.

#### Prerequisites

- **Docker Desktop** (latest version recommended)
- **Git**
- **8GB+ RAM** recommended for development

#### Quick Start

1. **Start Docker Desktop:**
   ```bash
   # macOS - ensure Docker Desktop is running
   open -a Docker
   
   # Verify Docker is running
   docker info
   ```

2. **Clone and start:**
   ```bash
   git clone <repository-url>
   cd radio001
   
   # Start development environment (auto-detects platform)
   ./scripts/docker-dev.sh start
   ```

3. **Access the application:**
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

#### What Happens Automatically

The development script will:
- ✅ **Detect your platform** (Apple Silicon, Intel, etc.)
- ✅ **Use optimized Docker images** for your architecture
- ✅ **Build frontend** (Nuxt 3 with TypeScript)
- ✅ **Build backend** (FastAPI with Python 3.11)
- ✅ **Enable hot reload** for both services
- ✅ **Set up networking** between containers
- ✅ **Configure volume mounts** for live code changes

#### Development Commands

```bash
# Essential commands
./scripts/docker-dev.sh start     # Start all services
./scripts/docker-dev.sh stop      # Stop all services
./scripts/docker-dev.sh status    # Check service status
./scripts/docker-dev.sh logs      # View all logs

# Development workflow
./scripts/docker-dev.sh logs radio-app        # Frontend logs
./scripts/docker-dev.sh logs radio-backend    # Backend logs
./scripts/docker-dev.sh shell radio-app       # Shell into frontend
./scripts/docker-dev.sh shell radio-backend   # Shell into backend
./scripts/docker-dev.sh restart              # Restart all services
./scripts/docker-dev.sh rebuild              # Rebuild all images

# Advanced options
./scripts/docker-dev.sh start --traefik      # Enable radio.local access
./scripts/docker-dev.sh start --all          # Start with all optional services
./scripts/docker-dev.sh cleanup              # Clean up Docker resources
```

#### Platform-Specific Notes

**🍎 Apple Silicon (M1/M2 Macs):**
- Automatically uses ARM64-optimized images
- Faster builds with pre-compiled wheels
- Memory-optimized resource limits

**🐧 Intel/AMD64:**
- Uses standard multi-platform images
- Full compatibility with all features

#### Manual Docker Commands

For direct Docker Compose usage:

```bash
# Basic usage
docker-compose up -d                    # Start services
docker-compose logs -f                  # Follow logs
docker-compose down                     # Stop services

# Apple Silicon specific
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Rebuild from scratch
docker-compose down -v
docker-compose up -d --build
```

#### Troubleshooting

**Common Issues:**
- **Docker not running**: `open -a Docker` (macOS)
- **Pydantic build errors**: Script auto-handles with platform detection
- **Port conflicts**: Script will detect and report conflicts
- **Memory issues**: Increase Docker Desktop memory limit to 4GB+

**For detailed troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Production Deployment (Raspberry Pi)

#### Prerequisites

- **Raspberry Pi Zero 2 W** (or newer)
- **Raspberry Pi OS Lite** (64-bit recommended)
- **Docker** and **Docker Compose**
- **8GB+ microSD card**

#### Raspberry Pi Setup

1. **Prepare the Pi:**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker
   curl -sSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   sudo systemctl enable docker
   
   # Install Docker Compose
   sudo apt install docker-compose-plugin -y
   
   # Reboot to apply changes
   sudo reboot
   ```

2. **Clone and configure:**
   ```bash
   git clone <repository-url>
   cd radio001
   
   # Configure for production
   cp .env.example .env
   nano .env  # Edit production settings
   ```

3. **Deploy to production:**
   ```bash
   # Start production environment
   docker-compose -f docker-compose.prod.yml up -d
   
   # Check status
   docker-compose -f docker-compose.prod.yml ps
   
   # View logs
   docker-compose -f docker-compose.prod.yml logs -f
   ```

4. **Access the interface:**
   - **Direct IP**: http://[raspberry-pi-ip]
   - **mDNS**: http://radio.local
   - **Hotspot**: Connect to "Radio-Setup" network

#### Production Commands

```bash
# Service management
docker-compose -f docker-compose.prod.yml up -d      # Start
docker-compose -f docker-compose.prod.yml down       # Stop
docker-compose -f docker-compose.prod.yml restart    # Restart
docker-compose -f docker-compose.prod.yml logs -f    # View logs

# Updates
git pull                                              # Get latest code
docker-compose -f docker-compose.prod.yml up -d --build  # Rebuild and restart

# Backup
docker-compose -f docker-compose.prod.yml exec radio-app tar -czf /tmp/config-backup.tar.gz /etc/radio/
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Application
NODE_ENV=development
HOSTNAME=radio

# Frontend (Nuxt 3)
NUXT_HOST=0.0.0.0
NUXT_PORT=3000

# Backend (FastAPI)
API_HOST=localhost
API_PORT=8000

# Network Configuration
WIFI_INTERFACE=wlan0
ETH_INTERFACE=eth0

# Hotspot Configuration
HOTSPOT_SSID=Radio-Setup
HOTSPOT_PASSWORD=radio123
HOTSPOT_IP=192.168.4.1
HOTSPOT_RANGE=192.168.4.2,192.168.4.20

# Features
ENABLE_CAPTIVE_PORTAL=true
ENABLE_AUTO_CONNECT=true
ENABLE_AUTO_CONNECT=true

# Development
DEBUG=radio:*
CHOKIDAR_USEPOLLING=true
```

### Application Structure

#### Frontend (Nuxt 3)
- **Dashboard** (`/`) - System overview and status
- **WiFi Setup** (`/setup`) - Network scanning and connection
- **System Status** (`/status`) - Detailed system information  
- **Settings** (`/settings`) - Device configuration

#### Backend (FastAPI)
- **WiFi Management** - Scan, connect, status APIs
- **System Management** - Monitor CPU, memory, services
- **Configuration** - Save/load device settings
- **Health Monitoring** - Service status and diagnostics

#### Key Components
- **SignalStrength.vue** - Visual WiFi signal indicator
- **useWiFi.ts** - Reactive WiFi state management
- **API Proxy** - Seamless frontend-backend communication
- **Docker Services** - Containerized frontend and backend

## 📱 Usage

### First-Time Setup

1. **Power on your Raspberry Pi** with the Radio WiFi Configuration
2. **Connect to the hotspot** named `Radio-Setup` (or your configured SSID)
3. **Open a web browser** and navigate to:
   - `http://radio.local` (recommended)
   - `http://192.168.4.1` (direct IP)
4. **Follow the setup wizard** to scan and select your WiFi network
5. **Enter your WiFi credentials** securely
6. **The Pi will automatically reboot** and switch to client mode

### Using the Interface

#### Dashboard
- **Real-time status** - Connection state, signal strength, IP address
- **Quick actions** - Scan networks, restart services, view logs
- **System metrics** - CPU usage, memory, uptime, temperature

#### WiFi Setup
- **Network scanning** - Automatically discover available networks
- **Signal visualization** - Clear signal strength indicators
- **Security handling** - Support for WPA/WPA2/WPA3 and open networks
- **Hidden networks** - Manual entry for hidden SSIDs

#### System Status
- **Detailed monitoring** - Service status, network interfaces, device info
- **Health checks** - WiFi connection quality, system performance
- **Service management** - Restart network services, system reboot

#### Settings
- **Device configuration** - Hostname, theme, language preferences
- **WiFi options** - Auto-connect, scan intervals, connection timeouts
- **Hotspot settings** - SSID, password, channel, IP configuration
- **Advanced options** - Debug mode, captive portal, monitoring

## 🛠️ Development

### Development Architecture

#### Technology Stack

**Frontend:**
- **Nuxt 3** - Vue.js framework with SSR/SPA support
- **TypeScript** - Type-safe development
- **Nuxt UI** - Component library with Tailwind CSS
- **Pinia** - State management
- **Composables** - Reactive WiFi state management

**Backend:**
- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation and serialization
- **Uvicorn** - ASGI server with hot reload
- **System Integration** - Direct WiFi management via Linux tools

**Infrastructure:**
- **Docker** - Containerized development and deployment
- **Docker Compose** - Multi-service orchestration
- **Platform Detection** - Automatic Apple Silicon optimization
- **Hot Reload** - Real-time code changes for both services

#### API Reference

**WiFi Management:**
- `GET /api/wifi/status` - Current connection status
- `POST /api/wifi/scan` - Discover available networks
- `POST /api/wifi/connect` - Connect to network with credentials

**System Management:**
- `GET /api/system/status` - CPU, memory, services, network info
- `POST /api/system/restart-network` - Restart network services
- `POST /api/system/reset` - Reset to hotspot mode

**Configuration:**
- `GET /api/config` - Get current device configuration
- `POST /api/config` - Update device settings
- `POST /api/config/validate` - Validate configuration

#### Development Scripts

```bash
# Docker-based development (recommended)
./scripts/docker-dev.sh start              # Start all services
./scripts/docker-dev.sh stop               # Stop all services
./scripts/docker-dev.sh logs               # View all logs
./scripts/docker-dev.sh logs radio-backend # Backend logs only
./scripts/docker-dev.sh shell radio-app    # Frontend shell
./scripts/docker-dev.sh rebuild            # Rebuild images
./scripts/docker-dev.sh cleanup            # Clean Docker resources

# Platform-specific
./scripts/docker-dev.sh start --traefik    # Enable radio.local
./scripts/docker-dev.sh start --all        # All optional services

# Direct Docker Compose
docker-compose up -d                        # Start services
docker-compose logs -f                      # Follow logs
docker-compose down                         # Stop services
docker-compose up -d --build               # Rebuild and start
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

### Troubleshooting

#### Quick Diagnostics

```bash
# Check if Docker is running
docker info

# Check service status
./scripts/docker-dev.sh status

# View logs for issues
./scripts/docker-dev.sh logs

# Clean restart
./scripts/docker-dev.sh stop
./scripts/docker-dev.sh cleanup
./scripts/docker-dev.sh start
```

#### Common Issues

**🐳 Docker Issues:**
- **Docker not running**: Start Docker Desktop
- **Pydantic build errors**: Automatic Apple Silicon detection handles this
- **Port conflicts**: Script detects and reports conflicts
- **Memory issues**: Increase Docker memory to 4GB+

**🍎 Apple Silicon Specific:**
- **Build failures**: Uses optimized ARM64 images automatically
- **Performance**: Configured with memory limits and platform detection

**🌐 Network Issues:**
- **Cannot access radio.local**: Check if Avahi/mDNS is running
- **API timeouts**: Check if backend service is healthy
- **Frontend blank**: Check frontend build logs

**📱 Application Issues:**
- **WiFi scan fails**: Check permissions and interface availability
- **Connection errors**: Verify network credentials and signal strength

**For detailed troubleshooting guide**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

#### Log Locations

- **Development logs**: `./logs/frontend.log`, `./logs/backend.log`
- **Container logs**: `docker-compose logs`
- **Application logs**: Available via web interface at `/status`

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Guidelines

- **Follow TypeScript best practices**
- **Use Vue 3 Composition API patterns**
- **Test on both development and Raspberry Pi environments**
- **Ensure mobile-first responsive design**
- **Document API changes and new features**
- **Use conventional commit messages**

## 📋 Roadmap

### Phase 1: Core Infrastructure ✅
- [x] Project structure and Docker setup
- [x] Nuxt 3 frontend with TypeScript
- [x] FastAPI backend with auto-reload
- [x] Apple Silicon optimization
- [x] Cross-platform development environment

### Phase 2: WiFi Management ✅
- [x] WiFi network scanning and discovery
- [x] Secure network connection management
- [x] Hotspot mode automation
- [x] Real-time status monitoring
- [x] Signal strength visualization

### Phase 3: User Interface ✅
- [x] Mobile-responsive dashboard
- [x] WiFi setup wizard
- [x] System status and monitoring
- [x] Configuration management
- [x] Signal strength indicators

### Phase 4: Enhanced Features 🚧
- [ ] Captive portal implementation
- [ ] Network profiles and priorities
- [ ] Advanced security options
- [ ] Performance analytics
- [ ] Remote management capabilities

### Phase 5: Production Features 📋
- [ ] Backup and restore functionality
- [ ] Multi-device coordination
- [ ] Enterprise management
- [ ] Custom branding options

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Nuxt.js team** for the excellent framework
- **Raspberry Pi Foundation** for amazing hardware
- **Docker** for containerization technology
- **Avahi** for mDNS implementation
- **hostapd** for WiFi hotspot functionality

## 📞 Support

- **Getting Started**: [DEVELOPMENT.md](DEVELOPMENT.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Issues**: [GitHub Issues](issues-url)
- **Discussions**: [GitHub Discussions](discussions-url)

## 🚀 Quick Commands Reference

```bash
# Start development environment
./scripts/docker-dev.sh start

# View logs
./scripts/docker-dev.sh logs

# Stop services
./scripts/docker-dev.sh stop

# Clean restart
./scripts/docker-dev.sh cleanup && ./scripts/docker-dev.sh start

# Access services
open http://localhost:3000  # Frontend
open http://localhost:8000  # Backend API
```

---

**Built with ❤️ for the Raspberry Pi community**  
*Featuring automatic Apple Silicon optimization and cross-platform Docker development*