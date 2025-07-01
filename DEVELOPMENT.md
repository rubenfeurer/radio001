# Radio WiFi Configuration - Development Guide

This guide covers development setup, architecture, and contribution guidelines for the Radio WiFi Configuration project.

## 🏗️ Project Architecture

### Overview

The Radio WiFi Configuration system consists of two main components:

1. **Frontend (Nuxt 3)** - Modern web application for WiFi configuration
2. **Backend (FastAPI)** - API server for system operations and WiFi management

### Technology Stack

**Frontend:**
- Nuxt 3 (Vue.js framework)
- TypeScript
- Nuxt UI (component library)
- Tailwind CSS
- Pinia (state management)

**Backend:**
- FastAPI (Python web framework)
- Pydantic (data validation)
- Python system calls for WiFi management

**Infrastructure:**
- Docker & Docker Compose
- Nginx (production reverse proxy)
- Avahi (mDNS service discovery)

## 🔧 Development Environment

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd radio001

# Start all services
./scripts/start-dev.sh

# Access application
open http://localhost:3000
```

### Manual Setup

#### Frontend Development

```bash
cd app

# Install dependencies
npm install

# Start development server
npm run dev

# Other commands
npm run build      # Build for production
npm run preview    # Preview production build
npm run typecheck  # TypeScript checking
npm run lint       # Code linting
```

#### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start development server
python main.py --reload

# Other commands
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

Create `.env` files for local development:

**Frontend (.env):**
```bash
NODE_ENV=development
NUXT_HOST=0.0.0.0
NUXT_PORT=3000
API_HOST=localhost
API_PORT=8000
```

**Backend (.env):**
```bash
API_PORT=8000
WIFI_INTERFACE=wlan0
NODE_ENV=development
```

## 📁 Project Structure

```
radio001/
├── app/                          # Frontend Application
│   ├── assets/css/              # Global styles
│   ├── components/              # Vue components
│   │   └── SignalStrength.vue   # WiFi signal indicator
│   ├── composables/             # Vue composables
│   │   └── useWiFi.ts          # WiFi state management
│   ├── pages/                   # Application pages
│   │   ├── index.vue           # Dashboard
│   │   ├── setup.vue           # WiFi setup
│   │   ├── status.vue          # System status
│   │   └── settings.vue        # Configuration
│   ├── server/api/              # API proxy routes
│   │   ├── [...path].ts        # Backend proxy
│   │   ├── health.ts           # Health check
│   │   ├── system/             # System APIs
│   │   ├── wifi/               # WiFi APIs
│   │   └── config/             # Configuration APIs
│   ├── types/                   # TypeScript definitions
│   │   └── index.ts            # Shared types
│   ├── nuxt.config.ts          # Nuxt configuration
│   └── package.json            # Dependencies
├── backend/                     # Backend Application
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt        # Python dependencies
│   └── package.json            # Node.js metadata
├── scripts/                     # Utility scripts
│   ├── start-dev.sh            # Development startup
│   └── wifi-init.sh            # WiFi initialization
├── docker/                      # Docker configurations
│   ├── Dockerfile              # Production image
│   ├── Dockerfile.dev          # Development image
│   └── entrypoint.sh           # Container entrypoint
└── config/                      # System configuration
    ├── avahi/                  # mDNS configuration
    └── hostapd/                # Hotspot configuration
```

## 🔌 API Reference

### WiFi Management

**GET /api/wifi/status**
- Returns current WiFi connection status

**POST /api/wifi/scan**
- Scans for available WiFi networks

**POST /api/wifi/connect**
- Connects to a WiFi network
- Body: `{ ssid: string, password: string }`

### System Management

**GET /api/system/status**
- Returns system information (CPU, memory, services)

**POST /api/system/restart-network**
- Restarts network services

**POST /api/system/reset**
- Resets system to hotspot mode

### Configuration

**GET /api/config**
- Returns current device configuration

**POST /api/config**
- Updates device configuration

## 🎨 Frontend Development

### Component Guidelines

- Use Nuxt UI components where possible
- Follow Vue 3 Composition API patterns
- Implement TypeScript interfaces for all props
- Use Tailwind CSS for styling

**Example Component:**
```vue
<template>
  <UCard>
    <template #header>
      <h2>{{ title }}</h2>
    </template>
    
    <div class="space-y-4">
      <!-- Component content -->
    </div>
  </UCard>
</template>

<script setup lang="ts">
interface Props {
  title: string
  data?: any[]
}

const props = defineProps<Props>()

// Component logic
</script>
```

### State Management

Use the `useWiFi` composable for WiFi-related state:

```typescript
const {
  networks,
  status,
  isScanning,
  scanNetworks,
  connectToNetwork
} = useWiFi()
```

### Styling Guidelines

- Use Tailwind CSS utility classes
- Follow mobile-first responsive design
- Use CSS custom properties for theming
- Maintain consistent spacing with Tailwind scale

## 🐍 Backend Development

### FastAPI Patterns

- Use Pydantic models for request/response validation
- Implement proper error handling with HTTPException
- Follow REST API conventions
- Include comprehensive docstrings

**Example API Endpoint:**
```python
@app.post("/api/wifi/connect")
async def connect_wifi(credentials: WiFiCredentials):
    """Connect to a WiFi network"""
    try:
        result = await connect_to_network(credentials)
        return {
            "success": True,
            "message": f"Connected to {credentials.ssid}",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
```

### System Integration

- Use subprocess for system commands
- Implement proper error handling for system calls
- Follow RaspiWiFi patterns for compatibility
- Handle both development and production modes

## 🧪 Testing

### Frontend Testing

```bash
cd app

# Unit tests (when available)
npm run test

# Type checking
npm run typecheck

# Linting
npm run lint
```

### Backend Testing

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio

# Run tests (when available)
pytest

# Type checking
mypy main.py
```

### Manual Testing

1. **WiFi Scanning:**
   - Test network discovery
   - Verify signal strength display
   - Check security type detection

2. **WiFi Connection:**
   - Test successful connections
   - Test incorrect passwords
   - Test hidden networks

3. **System Management:**
   - Test status reporting
   - Test service restart
   - Test mode switching

## 🚀 Deployment

### Development Deployment

```bash
# Using Docker Compose
docker-compose up -d

# Access application
open http://radio.local
```

### Production Deployment

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose ps
```

### Raspberry Pi Deployment

1. Flash Raspberry Pi OS Lite
2. Enable SSH and WiFi (if needed)
3. Install Docker and Docker Compose
4. Clone repository and deploy

## 🤝 Contributing

### Code Style

- **Frontend:** Use Prettier and ESLint
- **Backend:** Use Black and flake8
- **Commits:** Follow conventional commit format

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Update documentation
5. Submit pull request

### Issue Reporting

Include the following in bug reports:
- Device model (Raspberry Pi version)
- Operating system version
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs

## 📝 Troubleshooting

### Common Issues

**Frontend not loading:**
```bash
# Check if services are running
./scripts/start-dev.sh --status

# Check logs
tail -f logs/frontend.log
```

**Backend API errors:**
```bash
# Check backend logs
tail -f logs/backend.log

# Test API directly
curl http://localhost:8000/health
```

**WiFi issues on Raspberry Pi:**
```bash
# Check interface status
ip addr show wlan0

# Check system logs
journalctl -u hostapd
journalctl -u wpa_supplicant
```

### Development Tips

1. **Hot Reload:** Frontend automatically reloads on file changes
2. **API Proxy:** Frontend proxies API calls to backend
3. **Mock Data:** Backend provides mock data in development mode
4. **Logging:** Use browser dev tools and terminal logs for debugging

## 📚 Resources

- [Nuxt 3 Documentation](https://nuxt.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Nuxt UI Components](https://ui.nuxt.com/)
- [RaspiWiFi Reference](https://github.com/jasbur/RaspiWiFi)
- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.