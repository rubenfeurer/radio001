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
   docker-compose up radio-backend -d
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
docker-compose -f docker-compose.prod.yml up -d
```

## 📁 Project Structure

```
radio-wifi/
├── frontend/              # SvelteKit frontend (new)
│   ├── src/
│   │   ├── routes/        # Page components
│   │   ├── lib/
│   │   │   ├── components/# Reusable components  
│   │   │   ├── stores/    # Svelte stores (state)
│   │   │   └── types.ts   # TypeScript types
│   │   └── app.html       # HTML template
│   ├── static/            # Static assets
│   └── package.json
├── backend/               # FastAPI backend (unchanged)
│   ├── main.py            # FastAPI application
│   └── requirements.txt
├── app/                   # Legacy Nuxt (deprecated)
├── docker/                # Docker configurations
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
docker-compose up radio-backend    # Start backend
docker-compose logs radio-backend  # View logs
docker-compose exec radio-backend bash  # Shell access
```

### Full Stack Development

```bash
# Terminal 1: Backend
docker-compose up radio-backend

# Terminal 2: Frontend  
cd frontend && npm run dev

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

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/wifi/status` | Current WiFi status |
| POST | `/api/wifi/scan` | Scan for networks |
| POST | `/api/wifi/connect` | Connect to network |
| POST | `/api/system/reset` | Reset to hotspot mode |
| GET | `/health` | Health check |

## 🐳 Docker

### Development
```bash
docker-compose up -d          # Start all services
docker-compose up radio-backend -d  # Backend only
```

### Production  
```bash
docker-compose -f docker-compose.prod.yml up -d
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
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Configure as access point:**
   ```bash
   sudo ./scripts/setup-pi.sh
   ```

## 🔍 Troubleshooting

### ARM64 Issues (Solved!)
- ❌ **Problem**: `oxc-parser` no ARM64 binaries
- ✅ **Solution**: Use SvelteKit (no oxc-parser dependency)

### Development Issues
```bash
# Reset everything
docker-compose down -v
cd frontend && rm -rf node_modules && npm install
docker-compose up --build
```

### Backend Issues  
```bash
# Check backend logs
docker-compose logs radio-backend

# Restart backend
docker-compose restart radio-backend
```

## 📚 Documentation

- [Development Guide](./DEVELOPMENT.md)
- [SvelteKit Migration](./SVELTEKIT-MIGRATION.md)
- [Deployment Guide](./DEPLOYMENT.md)  
- [API Documentation](./API.md)
- [Troubleshooting](./TROUBLESHOOTING.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- [SvelteKit](https://kit.svelte.dev) - Amazing frontend framework
- [FastAPI](https://fastapi.tiangolo.com) - Fast and reliable backend
- [Tailwind CSS](https://tailwindcss.com) - Utility-first CSS framework
- [RaspiWiFi](https://github.com/jasbur/RaspiWifi) - Inspiration for Pi WiFi setup

---

**Made with ❤️ for Raspberry Pi developers**

*No more ARM64 oxc-parser headaches! 🎉*