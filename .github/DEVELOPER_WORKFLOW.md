# Developer Workflow Guide

This document outlines the optimized development workflow for the Radio WiFi Configuration project, designed for fast local development and efficient CI/CD.

## 🚀 Quick Start

```bash
# Clone and start development
git clone <repository-url>
cd radio001
./scripts/docker-dev.sh start

# Make changes, commit with automatic checks
git add .
git commit -m "feat: add new WiFi feature"
git push
```

## 🔄 Development Workflow Overview

### **Local Development (Pre-commit)**
- ✅ **Automatic lint fixes** - ESLint auto-fixes issues
- ✅ **Type checking** - TypeScript compilation validation
- ✅ **Commit message validation** - Conventional commits enforced
- ✅ **Code formatting** - Consistent style applied

### **CI/CD (Push/PR)**
- ✅ **Integration tests** - Full Docker stack testing
- ✅ **Security scanning** - Dependency vulnerability checks
- ✅ **Cross-platform builds** - ARM64 + AMD64 Docker images
- ✅ **Multi-arch deployment** - Production-ready releases

## 🛠️ Pre-commit Setup

### Automatic Installation
The pre-commit hooks install automatically when you run:

```bash
cd app && npm install
```

### What Happens on Commit

1. **Lint & Fix**: ESLint runs and auto-fixes issues
2. **Type Check**: TypeScript compilation validates types
3. **Conventional Commits**: Commit message format validated
4. **Auto-stage**: Fixed files automatically added to commit

### Commit Message Format

**Required format**: `type(scope): description`

**Valid types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation updates
- `style`: Code formatting
- `refactor`: Code restructuring
- `perf`: Performance improvements
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:
```bash
git commit -m "feat: add WiFi network scanning"
git commit -m "fix(api): handle connection timeout errors"
git commit -m "docs: update development guide"
git commit -m "chore(deps): update Docker base images"
```

## 🐳 Docker Development

### Container-First Development
- All dependencies install in Docker containers
- Local IDE may show import errors (expected)
- Type checking and builds work correctly in containers

### Development Commands

```bash
# Essential workflow
./scripts/docker-dev.sh start     # Start development environment
./scripts/docker-dev.sh logs      # View logs
./scripts/docker-dev.sh shell radio-app  # Access frontend container
./scripts/docker-dev.sh stop      # Stop services

# Troubleshooting
./scripts/docker-dev.sh restart   # Restart services
./scripts/docker-dev.sh cleanup   # Clean Docker resources
```

### Manual Checks (if needed)

```bash
# Run checks manually in container
./scripts/docker-dev.sh shell radio-app
npm run type-check
npm run lint:fix
npm run build
```

## 🔍 Code Quality Standards

### TypeScript Best Practices

**API Response Handling** - Always use type guards:
```typescript
// ✅ Correct
if (response.success && 'data' in response) {
  data.value = response.data
} else if (!response.success && 'error' in response) {
  throw new Error(response.error)
}

// ❌ Incorrect - causes union type errors
if (response.success) {
  data.value = response.data
}
```

**Nested Property Access**:
```typescript
// ✅ Correct
status.value.network.wifi.ssid = network.ssid

// ❌ Incorrect
status.value.ssid = network.ssid
```

### ESLint Configuration
- Configured for Vue 3 + TypeScript
- Auto-fixes formatting issues
- Warns on `any` types (acceptable for rapid development)
- Enforces conventional patterns

## 🚫 Bypassing Checks (Emergency Only)

### Skip Pre-commit Hooks
```bash
# Emergency commits only
git commit --no-verify -m "fix: urgent production hotfix"
```

### Skip Type Checking
```bash
# Temporary bypass (not recommended)
SKIP_TYPE_CHECK=true git commit -m "wip: work in progress"
```

## 🔄 CI/CD Pipeline

### What Runs in CI
1. **Integration Tests**: Full Docker stack validation
2. **Security Scanning**: Trivy vulnerability scanning
3. **Multi-platform Builds**: AMD64 + ARM64 Docker images
4. **Deployment**: Staging and production releases

### What Doesn't Run in CI (Done Locally)
- ❌ Linting (done pre-commit)
- ❌ Type checking (done pre-commit)
- ❌ Basic builds (done pre-commit)

### CI Triggers
- **Push to main/develop**: Full pipeline
- **Pull Request**: Integration tests only
- **Release**: Production deployment
- **Manual**: Via GitHub Actions UI

## 🐛 Troubleshooting

### Pre-commit Hook Issues

**Hook not running**:
```bash
cd app && npm run prepare
chmod +x .husky/pre-commit .husky/commit-msg
```

**Type check failures**:
```bash
./scripts/docker-dev.sh shell radio-app
npm run type-check
# Fix issues, then retry commit
```

### IDE Issues

**TypeScript import errors**:
- Expected behavior - packages are in Docker
- Builds work correctly in containers
- Use Docker shell for accurate type checking

**ESLint not working in IDE**:
```bash
# Install ESLint extension for your IDE
# Configure to use project's .eslintrc.cjs
```

### Docker Issues

**Containers not starting**:
```bash
./scripts/docker-dev.sh cleanup
./scripts/docker-dev.sh start
```

**Permission errors**:
```bash
# Ensure Docker Desktop is running
docker info
```

## 📈 Performance Benefits

### Before (CI-only checks)
- 🐌 **5-10 minutes** CI feedback
- 🚫 **Multiple commits** to fix lint issues
- 💸 **Higher CI costs** from repeated runs

### After (Pre-commit hooks)
- ⚡ **30 seconds** local feedback
- ✅ **Single clean commit**
- 💰 **Lower CI costs** from fewer runs
- 🚀 **Faster development** cycle

## 🤝 Team Collaboration

### For New Developers

1. **Clone repository**
2. **Run `./scripts/docker-dev.sh start`**
3. **Hooks install automatically**
4. **Start developing immediately**

### For Code Reviews

- Pre-commit ensures consistent code quality
- Focus reviews on logic and architecture
- Less time spent on formatting and lint issues

### For Releases

- CI builds production-ready multi-arch images
- Automated security scanning
- Conventional commits enable automated changelogs

## ⚙️ Configuration Files

### Local Development
- `.husky/pre-commit` - Lint and type check hooks
- `.husky/commit-msg` - Conventional commit validation
- `app/package.json` - Lint-staged configuration

### CI/CD
- `.github/workflows/ci-cd.yml` - Optimized CI pipeline
- Focus on integration tests and multi-platform builds
- Reduced runtime from ~15min to ~8min

## 🎯 Best Practices

### Daily Development
1. **Start Docker environment**: `./scripts/docker-dev.sh start`
2. **Make changes** with hot reload
3. **Commit frequently** with automatic checks
4. **Push to trigger** integration tests

### Before Major Changes
1. **Run full test suite** locally
2. **Check Docker builds** work
3. **Verify type definitions** are correct
4. **Update documentation** if needed

### Code Reviews
- Pre-commit ensures code quality
- Focus on business logic and architecture
- Use conventional commits for clear history

This workflow provides **fast local development** with **reliable CI/CD**, ensuring high code quality without slowing down the development process.