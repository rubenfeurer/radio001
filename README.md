# Radio001

A unified **Radio + WiFi Configuration** system for Raspberry Pi Zero 2 W, combining reliable WiFi management with full internet radio capabilities. Built with **SvelteKit frontend** and **FastAPI backend**.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Architecture](https://img.shields.io/badge/architecture-ARM64%20Compatible-green.svg)
![Frontend](https://img.shields.io/badge/frontend-SvelteKit-ff3e00.svg)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688.svg)

## ✨ Features

### 📡 **WiFi Management**
- 🌐 **NetworkManager Integration** - Modern WiFi management using nmcli for reliability
- 🔄 **Manual Retry** - Single connection attempt with user-controlled retry for faster feedback
- 🗑️ **Network Forgetting** - Remove saved networks (prevents forgetting active connection)
- 🔥 **Hotspot Mode** - Instant switch to "Radio-Setup" AP for reconfiguration (no reboot)
- ⚡ **Boot Auto-Start** - Automatic startup on power-on with 5s WiFi check and hotspot fallback
- 📱 **Mobile Optimized** - Responsive design works on phones and tablets
- 🔒 **Secure by Default** - WPA2/WPA3 support with secure credential handling
- 🏠 **mDNS Ready** - Access via `http://radiod.local` on supported devices

### 📻 **Internet Radio**
- 🎵 **3-Slot Station System** - Quick access to favorite radio stations
- 🔊 **Volume Control** - Precise audio level management
- 🎛️ **Hardware Controls** - Physical buttons and rotary encoder support
- 📶 **Real-time Updates** - WebSocket communication for live status

### 🚀 **System Features**
- 🐳 **Docker Ready** - Containerized backend for easy deployment
- 🔧 **ARM64 Compatible** - No build issues on Raspberry Pi
- ⚡ **Hot Reload** - Live development with instant updates
- 🎨 **Dark Mode** - Automatic dark/light theme switching

## 🏗️ Architecture

**Hybrid Development Approach**:

```
┌─────────────────┐    ┌──────────────────┐
│   SvelteKit     │────│   FastAPI        │
│   Frontend      │ API│   Backend        │
│   (Local Dev)   │────│   (Docker)       │
└─────────────────┘    └──────────────────┘
      :3000                    :8000
```

- **Frontend**: SvelteKit runs locally (fast development)
- **Backend**: FastAPI + Radio system runs in Docker
- **API**: Frontend proxies requests to backend
- **Production**: Static frontend + Docker backend

## 🚀 Quick Start

### Prerequisites
- **Node.js** 20+ (for local development)
- **Docker** & Docker Compose v2 (for backend)
- **Raspberry Pi Zero 2 W** or compatible ARM64 device (for production)

### Development Setup

#### Automated Setup (Recommended)

The easiest way to get started is using the automated setup script:

```bash
# Clone repository
git clone <repository-url> radio001
cd radio001

# Copy configuration file
cp config/radio.conf.example config/radio.conf
# Edit config/radio.conf to customize settings (optional)

# Run automated setup (installs everything and tests the environment)
./scripts/setup-dev.sh
```

This script will:
- ✅ Check system requirements (Docker, Node.js, Git)
- ✅ Install frontend dependencies
- ✅ Setup Git hooks for code quality
- ✅ Build and test Docker containers
- ✅ Verify the development environment

#### Manual Setup

If you prefer manual setup:

1. **Clone repository:**
   ```bash
   git clone <repository-url> radio001
   cd radio001
   ```

2. **Setup configuration:**
   ```bash
   cp config/radio.conf.example config/radio.conf
   # Edit config/radio.conf to customize (HOTSPOT_SSID, passwords, etc.)
   ```

3. **Start backend (Docker):**
   ```bash
   # Use the helper script
   ./scripts/dev-environment.sh start
   
   # Or manually:
   docker compose -f compose/docker-compose.yml up radio-backend -d
   ```

4. **Start frontend (local):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Access the app:**
   - Frontend: http://localhost:5173 (Vite dev server)
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Production Deployment

Deploy to Raspberry Pi (auto-configures boot startup):
```bash
# Automatic setup - installs systemd service for boot auto-start
./scripts/dev-environment.sh start --prod

# System will auto-start on every boot
# - Checks WiFi connection (5s timeout)
# - Connects to saved WiFi OR starts hotspot mode
# - Access at http://radio.local or http://192.168.4.1 (hotspot)
```

## ⚙️ Configuration

All system settings are managed in **`config/radio.conf`**:

```bash
# Copy example configuration
cp config/radio.conf.example config/radio.conf

# Customize settings
nano config/radio.conf
```

### Key Settings:
- **WiFi Hotspot**: SSID, password, IP address
- **Network URLs**: Hotspot URL, mDNS hostname
- **Boot Behavior**: WiFi timeout, auto-fallback
- **Radio**: Station slots, default volume
- **Audio**: Output device, notifications

See **[config/README.md](./config/README.md)** for full configuration reference.

## 📁 Project Structure

```
radio001/
├── frontend/              # SvelteKit frontend
│   ├── src/routes/        # WiFi + Radio pages
│   ├── src/lib/stores/    # State management
│   └── src/lib/components/# UI components
├── backend/               # FastAPI backend
│   ├── core/              # Radio business logic
│   ├── hardware/          # GPIO & audio controls
│   ├── api/routes/        # API endpoints
│   └── main.py            # Unified WiFi + Radio API
├── openspec/              # Spec-driven development
│   ├── specs/             # Project specifications (single source of truth)
│   │   ├── system-configuration/   # Configuration management
│   │   ├── radio-integration/      # Radio capabilities
│   │   ├── hotspot-configuration/  # Hotspot mode specs
│   │   └── wifi-management/        # WiFi system specs
│   └── changes/           # Development workflow
│       ├── active-change/ # Current work
│       └── archive/       # Completed changes & decisions
├── config/                # Configuration files
│   ├── radio.conf         # Main config (gitignored)
│   ├── radio.conf.example # Example config
│   └── polkit/            # NetworkManager permissions
├── compose/               # Docker configurations
├── scripts/               # Helper scripts (see below)
├── data/                  # Station storage
├── assets/sounds/         # Notification sounds
├── claude.md              # AI development guide
└── README.md              # Project overview & setup
```

## 🔧 Helper Scripts

The `scripts/` directory contains helper scripts organized by purpose:

### 🚀 Setup & Development Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| **setup-dev.sh** | **First-time setup** - Installs dependencies, configures hooks, tests environment | Run once when cloning the repo |
| **dev-environment.sh** | **Daily development** - Start/stop/manage Docker services | Use daily for development work |
| **setup-hooks.sh** | Setup Git pre-commit hooks for code quality | Run if hooks need reinstalling |

### 🧪 Testing & CI Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| **backend-test-status.sh** | Check backend testing infrastructure status | Verify test setup is correct |
| **test-ci.sh** | Run local CI simulation | Test before pushing to CI/CD |
| **ci-pipeline-fix.sh** | Fix CI/CD pipeline issues (ARM64/AMD64) | When CI pipeline has build issues |

### ⚙️ Configuration Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| **setup-github-protection.sh** | Configure GitHub branch protection rules | Initial repo setup (maintainers) |
| **wifi-init.sh** | Initialize WiFi configuration on Raspberry Pi | Raspberry Pi first-time setup |

### Common Usage Examples

```bash
# FIRST TIME SETUP
./scripts/setup-dev.sh

# DAILY DEVELOPMENT
./scripts/dev-environment.sh start     # Start dev environment
./scripts/dev-environment.sh status    # Check what's running
./scripts/dev-environment.sh logs      # View all logs
./scripts/dev-environment.sh logs radio-backend  # Backend logs only
./scripts/dev-environment.sh stop      # Stop all services

# TESTING & TROUBLESHOOTING
./scripts/backend-test-status.sh       # Check test infrastructure
./scripts/test-ci.sh                   # Simulate CI pipeline locally
./scripts/ci-pipeline-fix.sh           # Fix CI/CD issues

# PRODUCTION DEPLOYMENT
./scripts/wifi-init.sh                 # Setup WiFi on Raspberry Pi
```

## 📚 Documentation & Specifications

### OpenSpec Specifications (Single Source of Truth)
| Specification | Description |
|---------------|-------------|
| **[System Configuration](./openspec/specs/system-configuration/spec.md)** | All settings in `radio.conf`, Docker integration |
| **[Radio Integration](./openspec/specs/radio-integration/spec.md)** | Complete radio system capabilities and requirements |
| **[Hotspot Configuration](./openspec/specs/hotspot-configuration/spec.md)** | NetworkManager-based hotspot mode specifications |
| **[WiFi Management](./openspec/specs/wifi-management/spec.md)** | WiFi scanning, connection, and management requirements |

### Development Guides
| Guide | Description |
|-------|-------------|
| **[Claude Development Guide](./claude.md)** | AI-assisted development workflow and commands |
| **[OpenSpec Changes](./openspec/changes/)** | Active development work and decision history |

## 🎯 Current Status

### ✅ **Phase 1 Complete: Backend Infrastructure (95%)**
- ✅ **WiFi Management**: Full network configuration system
- ✅ **Radio Backend**: 3-slot station management with volume control
- ✅ **Hardware Integration**: GPIO controllers with mock mode
- ✅ **API Integration**: Unified WiFi + Radio FastAPI backend
- ✅ **Testing**: Comprehensive test suite (142 tests)

### 🔄 **Phase 4 Ready: Frontend Integration**
- 🔄 **Radio UI Components**: Station cards, volume controls
- 🔄 **State Management**: Radio store integration  
- 🔄 **Navigation**: Unified WiFi + Radio interface

## 🏠 Pages & Features

| Route | Description | Status |
|-------|-------------|--------|
| `/` | Main dashboard with WiFi status | ✅ Complete |
| `/setup` | Unified WiFi manager (scan/connect/forget/reset) | ✅ Complete |
| `/radio` | Radio station management | 🔄 In Progress |
| `/settings` | System settings | ✅ Complete |
| `/status` | Detailed system status | ✅ Complete |

## 📡 API Endpoints

> **[📖 Interactive API Docs →](http://localhost:8000/docs)** | **[Full Documentation →](./docs/README.md#-api-reference)**

### WiFi Endpoints
- `GET /wifi/status` - Current WiFi connection status
- `GET /wifi/scan` - Scan for available networks
- `POST /wifi/connect` - Connect to network (single attempt, user can retry)
- `GET /wifi/saved` - List saved networks from NetworkManager
- `DELETE /wifi/saved/{id}` - Forget saved network
- `POST /system/hotspot-mode` - Switch to hotspot mode (no reboot needed)

### Radio Endpoints *(New)*
- `GET /radio/status` - Current radio system status
- `GET /radio/stations` - Get all configured stations
- `POST /radio/stations/{slot}` - Save station to slot (1-3)
- `POST /radio/volume` - Set volume level
- `WS /ws/radio` - Real-time radio updates

## 🎯 Raspberry Pi Setup

1. **Install Docker:**
   ```bash
   curl -sSL https://get.docker.com | sh
   sudo usermod -aG docker pi
   ```

2. **Deploy application:**
   ```bash
   git clone <repo-url> radio001
   cd radio001
   
   # Setup configuration
   cp config/radio.conf.example config/radio.conf
   nano config/radio.conf  # Customize HOTSPOT_SSID, passwords, URLs, etc.
   
   ./scripts/dev-environment.sh start --prod
   ```
   
   This automatically:
   - ✅ Loads settings from `config/radio.conf`
   - ✅ Installs systemd service for boot auto-start
   - ✅ Builds and starts containers
   - ✅ Configures WiFi check → hotspot fallback
   - ✅ System will start on every reboot

3. **Access via:**
   - **WiFi connected**: http://radio.local or http://[pi-ip]
   - **Hotspot mode**: http://192.168.4.1 (or custom HOTSPOT_URL)
   - **Hardware Controls**: 3 buttons + rotary encoder

## 🛠️ Development Workflow

### Traditional Development
```bash
# Direct code editing
./scripts/dev-environment.sh start
cd frontend && npm run dev
```

### Spec-Driven Development (OpenSpec)
```bash
# Plan before coding
npm run opsx:new "add-station-favorites"    # Create change
npm run opsx:apply                           # Implement with AI
npm run opsx:archive                         # Complete & preserve

# Or guided tutorial
npm run opsx:onboard
```

### Available OpenSpec Commands
```bash
# npm scripts (convenient)
npm run opsx:new          # Start new change
npm run opsx:continue     # Continue existing change  
npm run opsx:apply        # Implement tasks
npm run opsx:onboard      # Guided tutorial

# Slash commands (in AI chat)
/opsx:new <feature-name>  # Start new change
/opsx:ff <feature-name>   # Fast-forward: all artifacts at once
/opsx:apply               # Implement tasks
/opsx:explore             # Think through problems
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. **Optional**: Use OpenSpec for planned changes (`npm run opsx:new amazing-feature`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

## 📄 License

MIT License - see [LICENSE](./LICENSE) file for details.

---

**Made with ❤️ for Raspberry Pi developers**

*Unified WiFi + Radio system with no ARM64 compatibility issues! 🎉*
