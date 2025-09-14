# Radio WiFi Configuration

A modern WiFi provisioning solution for Raspberry Pi Zero 2 W, built with **SvelteKit frontend** and **FastAPI backend**. Provides an easy web interface for configuring WiFi networks on headless Raspberry Pi devices.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Architecture](https://img.shields.io/badge/architecture-ARM64%20Compatible-green.svg)
![Frontend](https://img.shields.io/badge/frontend-SvelteKit-ff3e00.svg)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688.svg)

## ✨ Features

- 🌐 **Easy WiFi Setup** - Simple web interface for network configuration
- 📱 **Mobile Optimized** - Responsive design works on phones and tablets  
- 🔒 **Secure by Default** - WPA2/WPA3 support with secure credential handling
- 🚀 **Fast Performance** - SvelteKit frontend compiles to vanilla JavaScript
- 🐳 **Docker Ready** - Containerized backend for easy deployment
- 🔧 **ARM64 Compatible** - No oxc-parser issues on Raspberry Pi
- ⚡ **Hot Reload** - Live development with instant updates
- 🎨 **Dark Mode** - Automatic dark/light theme switching
- 📶 **Signal Strength** - Real-time WiFi signal monitoring
- 🔄 **Auto-reconnect** - Automatic connection recovery
- 🧪 **Comprehensive Testing** - 142+ tests with CI/CD integration

## 🏗️ Architecture

**Hybrid Development Approach** (solves ARM64 oxc-parser issues):

```
┌─────────────────┐    ┌──────────────────┐
│   SvelteKit     │────│   FastAPI        │
│   Frontend      │ API│   Backend        │
│   (Local Dev)   │────│   (Docker)       │
└─────────────────┘    └──────────────────┘
      :3000                    :8000
```

- **Frontend**: SvelteKit runs locally (no ARM64 issues)
- **Backend**: FastAPI runs in Docker (proven stable)
- **API**: Frontend proxies requests to backend
- **Production**: Static frontend + Docker backend

## 🚀 Quick Start

### Prerequisites

- **Node.js** 20+ (for local development)
- **Docker** & Docker Compose (for backend)
- **Raspberry Pi Zero 2 W** or compatible ARM64 device

### Development Setup

1. **Clone and setup:**
   ```bash
   git clone <repository-url> radio-wifi
   cd radio-wifi
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
radio-wifi/
├── frontend/              # SvelteKit frontend
│   ├── src/
│   │   ├── routes/        # Page components
│   │   ├── lib/
│   │   │   ├── components/# Reusable components  
│   │   │   ├── stores/    # Svelte stores (state)
│   │   │   └── types.ts   # TypeScript types
│   │   └── app.html       # HTML template
│   ├── static/            # Static assets
│   └── package.json       # Frontend dependencies
├── backend/               # FastAPI backend
│   ├── main.py            # FastAPI application
│   └── requirements.txt   # Python dependencies
├── compose/               # Docker Compose files
│   ├── docker-compose.yml      # Development
│   ├── docker-compose.prod.yml # Production
│   └── docker-compose.ci.yml   # CI/CD
├── docker/                # Dockerfiles & scripts
├── nginx/                 # Nginx configuration
├── config/                # System configuration
├── scripts/               # Deployment scripts
└── docs/                  # Documentation
```

## 🔧 Development

### Frontend Development (SvelteKit)

```bash
cd frontend
npm run dev          # Start dev server
npm run build        # Build for production  
npm run preview      # Preview production build
npm run check        # Type checking
npm run lint         # Lint code
```

### Backend Development (FastAPI)

```bash
docker-compose -f compose/docker-compose.yml up radio-backend    # Start backend
docker-compose -f compose/docker-compose.yml logs radio-backend  # View logs
docker-compose -f compose/docker-compose.yml exec radio-backend bash  # Shell access
```

### Backend Testing

```bash
cd backend

# Quick test run
./run_tests.sh                    # All tests
./run_tests.sh -t unit            # Unit tests only
./run_tests.sh -t api             # API tests only
./run_tests.sh -v                 # Verbose output

# Docker testing (CI simulation)
./run_tests.sh -d                 # Run in Docker
./run_tests.sh -d --clean         # Clean Docker run

# Development testing
./run_tests.sh -w                 # Watch mode
./run_tests.sh -t unit -w         # Watch unit tests

# Test status overview
../scripts/test-status.sh         # System overview
```

### Full Stack Development

```bash
# Terminal 1: Backend
docker-compose -f compose/docker-compose.yml up radio-backend

# Terminal 2: Frontend  
cd frontend && npm run dev

# Terminal 3: Tests (optional)
cd backend && ./run_tests.sh -w

# Access: http://localhost:3000
```

## 🏠 Pages & Features

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `+page.svelte` | Main dashboard with WiFi status |
| `/setup` | `setup/+page.svelte` | WiFi network setup wizard |
| `/settings` | `settings/+page.svelte` | System settings |
| `/status` | `status/+page.svelte` | Detailed system status |

## 🔄 Migration from Nuxt

We migrated from Nuxt to SvelteKit to solve ARM64 compatibility issues:

| **Issue** | **Nuxt Solution** | **SvelteKit Solution** |
|-----------|-------------------|----------------------|
| oxc-parser ARM64 | ❌ Complex workarounds | ✅ No oxc-parser dependency |
| Development | ❌ Docker required | ✅ Local development |
| Performance | ❌ Runtime overhead | ✅ Compiled JavaScript |
| Bundle size | ❌ Larger bundles | ✅ Smaller bundles |

See [SVELTEKIT-MIGRATION.md](./SVELTEKIT-MIGRATION.md) for detailed migration guide.

## 📡 API Endpoints

The FastAPI backend provides these endpoints:

### WiFi Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/wifi/status` | Current WiFi status |
| POST | `/api/wifi/scan` | Scan for networks |
| POST | `/api/wifi/connect` | Connect to network |
| POST | `/api/system/reset` | Reset to hotspot mode |
| GET | `/health` | Health check |

### Radio Control (New!)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/radio/status` | Get radio system status |
| GET | `/radio/stations/` | Get all station slots (1-3) |
| GET | `/radio/stations/{slot}` | Get station by slot |
| POST | `/radio/stations/{slot}` | Save station to slot |
| POST | `/radio/stations/{slot}/toggle` | Toggle station playback |
| POST | `/radio/volume` | Set volume level |
| GET | `/radio/volume` | Get volume info |
| POST | `/radio/stop` | Stop all playback |
| GET | `/ws/` | WebSocket for real-time updates |

## 🐳 Docker

### Development
```bash
docker-compose -f compose/docker-compose.yml up -d          # Start all services
docker-compose -f compose/docker-compose.yml up radio-backend -d  # Backend only
```

### Production  
```bash
docker-compose -f compose/docker-compose.prod.yml up -d
```

### ARM64 Compatibility
- ✅ Backend: Runs perfectly in Docker on ARM64
- ✅ Frontend: SvelteKit has no ARM64 issues
- ✅ Development: Local frontend + Docker backend

## 🎯 Raspberry Pi Setup

1. **Install Docker:**
   ```bash
   curl -sSL https://get.docker.com | sh
   sudo usermod -aG docker pi
   ```

2. **Deploy application:**
   ```bash
   git clone <repo-url> radio-wifi
   cd radio-wifi
   docker-compose -f compose/docker-compose.prod.yml up -d
   ```

3. **Configure as access point:**
   ```bash
   sudo ./scripts/setup-pi.sh
   ```

## 🔍 Troubleshooting

### ARM64 Issues (Solved!)
- ❌ **Problem**: `oxc-parser` no ARM64 binaries
- ✅ **Solution**: Use SvelteKit (no oxc-parser dependency)

### Test Failures
```bash
# Check test status
cd backend && ./run_tests.sh

# Debug specific test
python -m pytest tests/unit/test_radio_manager.py::TestRadioManager::test_volume_control -v

# Run in clean environment
./run_tests.sh -d --clean
```

### Development Issues
```bash
# Reset everything
docker-compose -f compose/docker-compose.yml down -v
cd frontend && rm -rf node_modules && npm install
docker-compose -f compose/docker-compose.yml up --build
```

### Backend Issues  
```bash
# Check backend logs
docker-compose -f compose/docker-compose.yml logs radio-backend

# Restart backend
docker-compose -f compose/docker-compose.yml restart radio-backend
```

## 📚 Documentation

- [Development Guide](./docs/DEVELOPMENT.md)
- [Integration Plan](./docs/RADIO_INTEGRATION_PLAN.md) - **Technical roadmap (95% Phase 1 complete)**
- [Testing Guide](./backend/TESTING.md) - **Comprehensive testing documentation**
- [SvelteKit Migration](./docs/SVELTEKIT-MIGRATION.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)  
- [Troubleshooting](./docs/TROUBLESHOOTING.md)
- [Workflow Guide](./docs/WORKFLOW.md)

## 🧪 Testing

### Quick Test Overview
- **142+ comprehensive tests** covering radio system
- **Unit tests** - Core functionality (RadioManager, StationManager)
- **API tests** - All endpoints with validation
- **Integration tests** - Complete workflows
- **WebSocket tests** - Real-time communication
- **CI/CD integrated** - Automated testing on commits

### Test Commands
```bash
# Check test infrastructure
./scripts/test-status.sh

# Run all tests
cd backend && ./run_tests.sh

# Run specific test categories  
./run_tests.sh -t unit          # Unit tests
./run_tests.sh -t api           # API tests
./run_tests.sh -t integration   # Integration tests

# Docker testing (CI simulation)
./run_tests.sh -d               # Full CI environment
```

### GitHub Actions Integration
- ✅ **Main CI/CD** - Full test suite on main branch
- ✅ **Develop CI** - Quick validation on develop
- ✅ **Backend Tests** - Comprehensive testing workflow
- ✅ **Coverage Reports** - Codecov integration
- ✅ **PR Comments** - Automated test result summaries

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. **Run tests locally** (`cd backend && ./run_tests.sh`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. **Ensure CI tests pass** (GitHub Actions will run automatically)
7. Open Pull Request

## 📄 License

MIT License - see [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- [SvelteKit](https://kit.svelte.dev) - Amazing frontend framework
- [FastAPI](https://fastapi.tiangolo.com) - Fast and reliable backend
- [Tailwind CSS](https://tailwindcss.com) - Utility-first CSS framework
- [RaspiWiFi](https://github.com/jasbur/RaspiWifi) - Inspiration for Pi WiFi setup

---

## 🎯 Project Status

### ✅ **Phase 1 Backend: 95% COMPLETE**
- **Radio System**: Full 3-slot station management
- **Hardware Integration**: GPIO controllers + audio (Pi-ready)
- **API Routes**: Complete WiFi + Radio endpoints
- **WebSocket**: Real-time status updates
- **Testing**: 142+ comprehensive tests with CI/CD
- **Development**: Full Docker-based mock environment

### 🔄 **Phase 4: Frontend Integration (In Progress)**
- Radio UI components (SvelteKit)
- State management stores
- Navigation integration
- Mobile-responsive design

### 📊 **Test Coverage**
- **Core modules**: >80% coverage
- **API endpoints**: >90% coverage
- **Hardware mocking**: 100% for development
- **CI/CD integration**: ✅ All workflows active

---

**Made with ❤️ for Raspberry Pi developers**

*No more ARM64 oxc-parser headaches + comprehensive testing! 🎉🧪*