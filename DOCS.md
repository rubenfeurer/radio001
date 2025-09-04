# Documentation Index

Quick navigation guide to all project documentation.

## 📋 Essential Documentation

### [README.md](README.md)
**Project overview and quick start guide**
- Features and capabilities
- Quick setup for developers and production
- Basic configuration and usage
- Architecture overview

### [DEVELOPMENT.md](DEVELOPMENT.md) 
**Complete development setup and workflow**
- Docker development environment
- Pre-commit hooks and CI/CD workflow
- Code quality standards and TypeScript patterns
- API integration patterns
- Commit message guidelines
- Troubleshooting for development issues

### [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
**Issue resolution guide**
- Docker and container issues
- Network and connectivity problems  
- Application-specific troubleshooting
- Raspberry Pi optimization
- Performance debugging

## 🚀 Getting Started

### For New Developers
1. Read [README.md](README.md) for project overview
2. Follow [DEVELOPMENT.md](DEVELOPMENT.md) setup guide
3. Use [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if you encounter issues

### For Production Deployment  
1. See [README.md](README.md) for production setup
2. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for Pi-specific issues

### For Contributors
1. Read [DEVELOPMENT.md](DEVELOPMENT.md) for workflow and standards
2. Follow conventional commit guidelines in [DEVELOPMENT.md](DEVELOPMENT.md)
3. Reference code quality patterns in [DEVELOPMENT.md](DEVELOPMENT.md)

## 📁 Quick Reference

**Setup Commands:**
```bash
# New developer setup
./scripts/setup-dev.sh

# Start development 
./scripts/docker-dev.sh start

# Production deployment
docker compose -f docker-compose.prod.yml up -d
```

**Key Files:**
- `scripts/docker-dev.sh` - Development environment management
- `scripts/setup-dev.sh` - New developer onboarding
- `app/composables/useWiFi.ts` - WiFi state management
- `backend/main.py` - FastAPI backend
- `docker-compose.prod.yml` - Production deployment

## 🔍 Finding Specific Information

| Need help with... | Check |
|-------------------|-------|
| First-time setup | [README.md](README.md) Quick Start |
| Development workflow | [DEVELOPMENT.md](DEVELOPMENT.md) |
| TypeScript errors | [DEVELOPMENT.md](DEVELOPMENT.md) Code Quality section |
| Docker issues | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) Docker section |
| WiFi problems on Pi | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) Application Issues |
| Commit messages | [DEVELOPMENT.md](DEVELOPMENT.md) Commit Guidelines |
| API patterns | [DEVELOPMENT.md](DEVELOPMENT.md) API Integration |
| Performance issues | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) Performance section |

This streamlined documentation structure eliminates redundancy while providing clear guidance for all users.