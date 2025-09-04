# Development Guide

Complete development setup and workflow guide for the Radio WiFi Configuration project.

## 🚀 Quick Start

```bash
# Setup development environment
./scripts/setup-dev.sh

# Start development
./scripts/docker-dev.sh start

# Make changes and commit (auto-checks run)
git add .
git commit -m "feat: add new WiFi feature"
git push
```

## 🏗️ Architecture

**Frontend (Nuxt 3):**
- Vue 3 + TypeScript + Tailwind CSS
- Pinia state management with `useWiFi` composable
- API proxy for backend communication
- Hot reload enabled

**Backend (FastAPI):**
- Python 3.11+ with RaspiWiFi-inspired WiFi management
- Minimal dependencies for reliability
- Mock data for development, real system calls in production

**Infrastructure:**
- Docker containers with platform optimization
- Automatic Apple Silicon (ARM64) vs Intel (AMD64) detection
- Volume mounts for live code changes

## 🐳 Docker Development Environment

### Key Concepts

- **Dependencies are containerized** - Node.js and Python packages install in Docker
- **IDE import errors are normal** - Packages resolve correctly in containers
- **Type checking works in container** - Use Docker for accurate results
- **Hot reload enabled** - Code changes reflect immediately

### Essential Commands

```bash
# Development workflow
./scripts/docker-dev.sh start     # Start all services
./scripts/docker-dev.sh stop      # Stop services  
./scripts/docker-dev.sh logs      # View logs
./scripts/docker-dev.sh cleanup   # Clean resources

# Development access
./scripts/docker-dev.sh shell radio-app        # Frontend shell
./scripts/docker-dev.sh shell radio-backend    # Backend shell
./scripts/docker-dev.sh restart               # Restart services
```

### Platform Optimization

The system automatically detects and optimizes for your platform:
- **Apple Silicon (M1/M2)**: ARM64 optimized images with faster builds
- **Intel/AMD64**: Standard multi-platform images

## 🔄 Development Workflow

### Pre-commit Checks (Local)

Automatic checks run on every commit:
- ✅ **ESLint auto-fixes** - Code style and formatting
- ✅ **TypeScript checking** - Type compilation validation
- ✅ **Conventional commits** - Message format validation
- ⚡ **30-second feedback** vs 5-10 minutes in CI

### CI/CD (Push/PR)

Integration tests and deployment:
- ✅ **Docker integration tests** - Full stack validation
- ✅ **Security scanning** - Vulnerability detection  
- ✅ **Multi-platform builds** - ARM64 + AMD64 images
- ✅ **Automated deployment** - Staging and production

### Benefits

| Aspect | Before | After |
|--------|---------|-------|
| Feedback Time | 5-10 min (CI) | 30 sec (local) |
| Failed Commits | Multiple fixes | Single clean commit |
| CI Runtime | ~15 minutes | ~8 minutes |
| Developer Experience | Frustrating waits | Instant feedback |

## 📝 Commit Guidelines

### Format

```
type(scope): description

[optional body]
[optional footer]
```

### Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat: add WiFi network scanning` |
| `fix` | Bug fix | `fix(api): handle connection timeouts` |
| `docs` | Documentation | `docs: update setup guide` |
| `style` | Code formatting | `style: fix ESLint warnings` |
| `refactor` | Code restructuring | `refactor: extract parsing logic` |
| `perf` | Performance | `perf: optimize scanning speed` |
| `test` | Adding tests | `test: add useWiFi unit tests` |
| `chore` | Maintenance | `chore(deps): update Docker images` |

### Scopes

- `api` - Backend API changes
- `ui` - Frontend UI changes  
- `docker` - Container configuration
- `ci` - CI/CD pipeline
- `deps` - Dependencies

### Examples

```bash
# Good examples
git commit -m "feat: add WiFi network scanning functionality"
git commit -m "fix(api): handle connection timeout errors"  
git commit -m "docs: update development setup guide"
git commit -m "chore(deps): update Nuxt to v3.8.4"

# Bad examples (will be rejected)
git commit -m "fix stuff"
git commit -m "Fixed the WiFi bug"
git commit -m "update documentation"
```

## 🔧 Code Quality & Type Safety

### TypeScript Best Practices

**API Response Handling** - Always use type guards:
```typescript
// ✅ Correct - proper type guards
if (response.success && 'data' in response) {
  data.value = response.data
} else if (!response.success && 'error' in response) {
  throw new Error(response.error)
}

// ❌ Wrong - causes union type errors
if (response.success) {
  data.value = response.data
}
```

**Nested Property Access**:
```typescript
// ✅ Correct - access nested properties
status.value.network.wifi.ssid = network.ssid

// ❌ Wrong - direct property access
status.value.ssid = network.ssid
```

### Common Issues & Fixes

1. **Union Type Errors**: Use `'property' in object` type guards
2. **Missing Properties**: Update type definitions in `types/index.ts`
3. **Import Errors in IDE**: Expected - packages are in Docker containers
4. **Build Failures**: Run checks in Docker environment for accuracy

### Quality Commands

```bash
# Run in Docker container for accurate results
./scripts/docker-dev.sh shell radio-app
npm run type-check    # TypeScript compilation
npm run lint          # ESLint checking
npm run lint:fix      # Auto-fix issues
npm run build         # Build application
```

## 📁 Project Structure

```
radio001/
├── app/                          # Frontend (Nuxt 3)
│   ├── composables/useWiFi.ts    # WiFi state management
│   ├── types/index.ts            # TypeScript definitions
│   ├── pages/                    # Vue pages with API integration
│   └── server/api/               # API proxy routes
├── backend/main.py               # FastAPI application
├── scripts/docker-dev.sh         # Development management
├── docker/                       # Container configurations
├── DEVELOPMENT.md                # This file
├── README.md                     # Project overview
└── TROUBLESHOOTING.md            # Issue resolution guide
```

## 🔌 API Integration Patterns

### Frontend API Calls

```typescript
const fetchData = async () => {
  try {
    const response = await $fetch('/api/endpoint')
    if (response.success && 'data' in response) {
      return response.data
    } else if (!response.success && 'error' in response) {
      throw new Error(response.error)
    }
  } catch (error) {
    console.error('API call failed:', error)
  }
}
```

### Backend Response Format

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

## 🔄 WiFi Management

### RaspiWiFi-Inspired Implementation

- **Network Scanning**: `iwlist scan` command parsing
- **Configuration**: `wpa_supplicant.conf` management  
- **Mode Switching**: Marker files for hotspot ↔ client modes
- **Status Monitoring**: `iwconfig` output parsing
- **Development Mocking**: Realistic mock data without Pi hardware

### Development vs Production

```python
if Config.IS_DEVELOPMENT:
    # Return mock data for development
    return mock_wifi_networks()
else:
    # Execute actual system commands
    result = await execute_iwlist_scan()
```

## 🛠️ Setup & Installation

### New Developer Onboarding

```bash
# One-command setup
./scripts/setup-dev.sh

# What it does:
# ✅ Checks system requirements (Docker, Git)
# ✅ Installs dependencies in containers
# ✅ Sets up pre-commit hooks  
# ✅ Tests Docker environment
# ✅ Validates development setup
```

### Manual Setup

```bash
# Clone repository
git clone <repository-url>
cd radio001

# Install app dependencies (optional - runs in Docker)
cd app && npm install

# Setup Git hooks
npm run prepare

# Start development environment
./scripts/docker-dev.sh start

# Access services
open http://localhost:3000  # Frontend
open http://localhost:8000  # Backend API
```

## 🐛 Debugging & Troubleshooting

### Docker Issues

```bash
# Check Docker status
docker info

# Clean restart
./scripts/docker-dev.sh stop
./scripts/docker-dev.sh cleanup  
./scripts/docker-dev.sh start

# View logs
./scripts/docker-dev.sh logs radio-app
./scripts/docker-dev.sh logs radio-backend
```

### TypeScript Issues

1. **Import errors in IDE**: Expected - packages in Docker
2. **Union type errors**: Add proper type guards  
3. **Property access errors**: Check nested object structure
4. **Build failures**: Run `npm run type-check` in container

### Pre-commit Hook Issues

```bash
# Reinstall hooks
cd app && npm run prepare
chmod +x .husky/pre-commit .husky/commit-msg

# Manual validation
npm run type-check
npm run lint:fix
```

### API Integration Issues

```bash
# Test backend directly
curl http://localhost:8000/health

# Test frontend proxy
curl http://localhost:3000/api/wifi/status

# Check network requests in browser dev tools
```

## 🚫 Emergency Bypasses

**Skip pre-commit hooks** (urgent fixes only):
```bash
git commit --no-verify -m "hotfix: urgent production fix"
```

**Skip specific checks**:
```bash
SKIP_TYPE_CHECK=true git commit -m "wip: work in progress"
```

## 🚀 Deployment

### Development
- Services: `localhost:3000` (frontend), `localhost:8000` (backend)
- Hot reload enabled for both services
- Mock data for WiFi operations

### Production (Raspberry Pi)  
- nginx reverse proxy
- Real WiFi system integration
- Available at `radio.local` via mDNS

## 🤝 Contributing

### Before Submitting PRs

1. ✅ Run type check: `npm run type-check`
2. ✅ Fix lint issues: `npm run lint:fix`  
3. ✅ Test in Docker environment
4. ✅ Update type definitions for new API endpoints
5. ✅ Use conventional commit messages

### Code Standards

- **TypeScript**: Strict type checking, proper union type handling
- **Vue**: Composition API, reactive state management
- **Python**: Type hints, comprehensive error handling
- **API**: Consistent response format, proper error handling

### Pull Request Checklist

- [ ] Code follows project patterns and conventions
- [ ] TypeScript compiles without errors
- [ ] All lint issues resolved
- [ ] API changes include proper type definitions  
- [ ] Documentation updated if needed
- [ ] Conventional commit messages used

## 📚 Resources

- [Project Overview](./README.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
- [Development Scripts](./scripts/)
- [Docker Development](./scripts/docker-dev.sh)
- [Conventional Commits](https://www.conventionalcommits.org/)

## ⚠️ Critical Notes

1. **Container Dependencies**: All packages install in Docker - local IDE may show import errors but builds work
2. **Type Safety**: Always use type guards for union types to prevent runtime errors  
3. **Platform Optimization**: Docker automatically optimizes for your development platform
4. **WiFi Mocking**: Backend provides realistic mock data in development mode
5. **Hot Reload**: Code changes reflect immediately without rebuilding containers

This guide provides everything needed for productive development on the Radio WiFi Configuration project.