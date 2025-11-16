# Radio001

A unified **Radio + WiFi Configuration** system for Raspberry Pi Zero 2 W, combining reliable WiFi management with full internet radio capabilities. Built with **SvelteKit frontend** and **FastAPI backend**.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Architecture](https://img.shields.io/badge/architecture-ARM64%20Compatible-green.svg)
![Frontend](https://img.shields.io/badge/frontend-SvelteKit-ff3e00.svg)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688.svg)

## ✨ Features

### 📡 **WiFi Management**
- 🌐 **Easy WiFi Setup** - Simple web interface for network configuration
- 📱 **Mobile Optimized** - Responsive design works on phones and tablets
- 🔒 **Secure by Default** - WPA2/WPA3 support with secure credential handling

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
- **Docker** & Docker Compose (for backend)
- **Raspberry Pi Zero 2 W** or compatible ARM64 device (for production)

### Development Setup

1. **Clone and setup:**
   ```bash
   git clone <repository-url> radio001
   cd radio001
   ```

2. **Start backend (Docker):**
   ```bash
   docker-compose -f compose/docker-compose.yml up radio-backend -d
   ```

3. **Setup frontend (Local):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the app:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs

### Production Deployment

Deploy to Raspberry Pi:
```bash
# Build and deploy
./scripts/deploy-pi.sh

# Or manually:
docker-compose -f compose/docker-compose.prod.yml up -d
```

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
├── compose/               # Docker configurations
├── data/                  # Station storage
├── assets/sounds/         # Notification sounds
└── docs/                  # Documentation
```

## 📚 Documentation

> **[📖 View Complete Documentation →](./docs/index.md)**

### Quick Links
- **[📋 System Overview](./docs/README.md)** - Detailed features, architecture, and API reference
- **[🎯 Integration Plan](./docs/RADIO_INTEGRATION_PLAN.md)** - Technical roadmap and implementation status
- **[🚀 Phase 4 Implementation Plan](./docs/PHASE4_IMPLEMENTATION_PLAN.md)** - Step-by-step frontend integration guide
- **[🚀 Quick Start](#-quick-start)** - Get up and running in 5 minutes

### What You'll Find
- **Architecture & Design** - Hybrid SvelteKit + FastAPI system
- **API Documentation** - WiFi + Radio endpoints with examples
- **Development Guide** - Setup, testing, and contribution workflow
- **Deployment Guide** - Raspberry Pi production deployment
- **Phase Progress** - Current implementation status (Phase 1: 95% complete)
- **Phase 4 Plan** - Detailed frontend integration implementation guide

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
- 📋 **[Implementation Plan](./docs/PHASE4_IMPLEMENTATION_PLAN.md)**: Step-by-step guide ready

## 🏠 Pages & Features

| Route | Description | Status |
|-------|-------------|--------|
| `/` | Main dashboard with WiFi + Radio status | ✅ WiFi Complete |
| `/setup` | WiFi network setup wizard | ✅ Complete |
| `/radio` | Radio station management | 🔄 In Progress |
| `/settings` | System settings | ✅ Complete |
| `/status` | Detailed system status | ✅ Complete |

## 📡 API Endpoints

### WiFi Endpoints
- `GET /api/wifi/status` - Current WiFi connection status
- `POST /api/wifi/scan` - Scan for available networks
- `POST /api/wifi/connect` - Connect to network

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
   docker-compose -f compose/docker-compose.prod.yml up -d
   ```

3. **Access via:**
   - **Web Interface**: http://radio.local or http://[pi-ip]
   - **Hardware Controls**: 3 buttons + rotary encoder

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](./LICENSE) file for details.

---

**Made with ❤️ for Raspberry Pi developers**

*Unified WiFi + Radio system with no ARM64 compatibility issues! 🎉*
