# Radio WiFi Configuration - Development Guide

This guide covers development setup, architecture, and critical learnings for the Radio WiFi Configuration project.

## 🚀 Quick Start

```bash
# Start development environment (auto-detects platform)
./scripts/docker-dev.sh start

# Access services
open http://localhost:3000  # Frontend
open http://localhost:8000  # Backend API
```

## 🏗️ Architecture Overview

**Frontend (Nuxt 3):**
- Vue 3 + TypeScript + Tailwind CSS
- Pinia state management
- API proxy for backend communication

**Backend (FastAPI):**
- Python 3.11+ with minimal dependencies
- RaspiWiFi-inspired WiFi management
- Docker containerized with platform optimization

## 🐳 Docker Development Environment

### Platform Detection

The project automatically detects and optimizes for your platform:
- **Apple Silicon (M1/M2)**: Uses ARM64 optimized images
- **Intel/AMD64**: Uses standard multi-platform images

### Critical Setup Notes

1. **Dependencies are containerized** - Node.js and Python packages install inside Docker
2. **TypeScript types resolve in container** - Local IDE may show import errors but builds work
3. **Volume mounts enable hot reload** - Code changes reflect immediately

### Development Commands

```bash
# Essential commands
./scripts/docker-dev.sh start     # Start all services
./scripts/docker-dev.sh stop      # Stop services
./scripts/docker-dev.sh logs      # View logs
./scripts/docker-dev.sh cleanup   # Clean Docker resources

# Development workflow
./scripts/docker-dev.sh shell radio-app        # Frontend shell
./scripts/docker-dev.sh shell radio-backend    # Backend shell
./scripts/docker-dev.sh restart               # Restart services
```

## 🔧 Code Quality & Type Safety

### Critical TypeScript Patterns

**API Response Handling** - Always use type guards:
```typescript
// ❌ Wrong - causes union type errors
if (response.success) {
  data.value = response.data
}

// ✅ Correct - proper type guards
if (response.success && 'data' in response) {
  data.value = response.data
} else if (!response.success && 'error' in response) {
  throw new Error(response.error)
}
```

**SystemStatus Property Access** - Access nested properties correctly:
```typescript
// ❌ Wrong - direct property access
status.value.ssid = network.ssid

// ✅ Correct - nested property access
status.value.network.wifi.ssid = network.ssid
```

### Lint & Type Check Commands

```bash
# Inside Docker container or with dependencies
npm run type-check    # TypeScript compilation check
npm run lint          # ESLint check
npm run lint:fix      # Auto-fix lint issues
```

### Common Type Issues & Fixes

1. **Union Type Errors**: Use `'property' in object` checks
2. **Missing Properties**: Update type definitions in `types/index.ts`
3. **Reserved Words**: Avoid JavaScript reserved words in interfaces
4. **Import Errors**: Expected in local IDE, resolved in Docker

## 📁 Key File Structure

```
radio001/
├── app/
│   ├── composables/useWiFi.ts    # WiFi state management
│   ├── types/index.ts            # Shared TypeScript types
│   ├── pages/                    # Vue pages with API integration
│   ├── server/api/               # API proxy routes
│   └── nuxt.config.ts           # Nuxt configuration
├── backend/main.py               # FastAPI application
├── scripts/docker-dev.sh         # Development management
└── docker/                       # Container configurations
```

## 🔌 API Integration Patterns

### Frontend API Calls

Use `$fetch` with proper error handling:
```typescript
const fetchData = async () => {
  try {
    const response = await $fetch('/api/endpoint')
    if (response.success && 'data' in response) {
      // Handle success
      return response.data
    } else if (!response.success && 'error' in response) {
      throw new Error(response.error)
    }
  } catch (error) {
    // Handle error
    console.error('API call failed:', error)
  }
}
```

### Backend Response Format

Consistent API response structure:
```python
# Success response
return {
    "success": True,
    "data": result,
    "message": "Operation completed",
    "timestamp": time.time()
}

# Error response
return {
    "success": False,
    "error": "Error message",
    "timestamp": time.time()
}
```

## 🔄 WiFi Management Implementation

### RaspiWiFi-Inspired Patterns

The WiFi system follows proven RaspiWiFi conventions:
- **Scanning**: `iwlist scan` command parsing
- **Configuration**: `wpa_supplicant.conf` management
- **Mode Switching**: Marker files for state tracking
- **Status Monitoring**: `iwconfig` output parsing

### Development vs Production

```python
if Config.IS_DEVELOPMENT:
    # Return mock data for development
    return mock_wifi_networks()
else:
    # Execute actual system commands
    result = await execute_iwlist_scan()
```

## 🛠️ Debugging & Troubleshooting

### Docker Issues

```bash
# Check Docker status
docker info

# View service logs
./scripts/docker-dev.sh logs radio-app
./scripts/docker-dev.sh logs radio-backend

# Clean restart
./scripts/docker-dev.sh stop
./scripts/docker-dev.sh cleanup
./scripts/docker-dev.sh start
```

### TypeScript Issues

1. **Import errors in IDE**: Expected - packages install in Docker
2. **Union type errors**: Add proper type guards
3. **Property access errors**: Check nested object structure
4. **Build failures**: Run `npm run type-check` in container

### API Integration Issues

```bash
# Test backend directly
curl http://localhost:8000/health

# Check API proxy
curl http://localhost:3000/api/wifi/status

# View network requests in browser dev tools
```

## 🚀 Deployment Notes

### Development
- Services run on `localhost:3000` (frontend) and `localhost:8000` (backend)
- Hot reload enabled for both services
- Mock data used for WiFi operations

### Production (Raspberry Pi)
- Services run behind nginx reverse proxy
- Real WiFi system integration
- mDNS available at `radio.local`

## ⚠️ Critical Development Notes

1. **Container Dependencies**: All Node.js and Python packages install in Docker - local IDE may show import errors but builds work correctly
2. **Type Safety**: Always use type guards for union types to prevent runtime errors
3. **Platform Optimization**: Docker automatically optimizes for your development platform
4. **WiFi Mocking**: Backend provides realistic mock data in development mode
5. **Hot Reload**: Code changes reflect immediately without rebuilding containers

## 🤝 Contributing

### Before Submitting PRs

1. Run type check: `npm run type-check`
2. Fix lint issues: `npm run lint:fix`
3. Test in Docker environment
4. Update type definitions if adding new API endpoints

### Code Standards

- **TypeScript**: Strict type checking, proper union type handling
- **Vue**: Composition API, reactive state management
- **Python**: Type hints, proper error handling
- **API**: Consistent response format, comprehensive error handling

## 📚 Key Resources

- [Docker Development Scripts](./scripts/docker-dev.sh)
- [TypeScript Types](./app/types/index.ts)
- [WiFi Composable](./app/composables/useWiFi.ts)
- [Backend API](./backend/main.py)