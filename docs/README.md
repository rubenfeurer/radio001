# Documentation

Welcome to the Radio WiFi Configuration project documentation! This guide will help you navigate through all available documentation.

## 📚 Documentation Index

### Getting Started
- **[Project README](../README.md)** - Main project overview and quick start guide

### Development
- **[Development Guide](./DEVELOPMENT.md)** - Complete development workflow and setup
- **[SvelteKit Migration](./SVELTEKIT-MIGRATION.md)** - Migration from Nuxt to SvelteKit details
- **[Workflow Guide](./WORKFLOW.md)** - Git workflow and contribution guidelines

### Deployment & Operations
- **[Deployment Guide](./DEPLOYMENT.md)** - Production deployment on Raspberry Pi
- **[Troubleshooting](./TROUBLESHOOTING.md)** - Common issues and solutions

## 🏗️ Architecture Overview

This project uses a **hybrid architecture** that solves ARM64 compatibility issues:

```
Development:
┌─────────────────┐    ┌──────────────────┐
│   SvelteKit     │────│   FastAPI        │
│   (Local Dev)   │ API│   (Docker)       │
│   :3000         │────│   :8000          │
└─────────────────┘    └──────────────────┘

Production:
┌─────────────────┐    ┌──────────────────┐
│     Nginx       │────│   FastAPI        │
│ Static SvelteKit│ API│   (Docker)       │
│     :80         │────│   :8000          │
└─────────────────┘    └──────────────────┘
```

## 🚀 Quick Navigation

### For Developers
1. **New to the project?** → Start with [Development Guide](./DEVELOPMENT.md)
2. **Understanding the migration?** → Read [SvelteKit Migration](./SVELTEKIT-MIGRATION.md)
3. **Need to contribute?** → Follow [Workflow Guide](./WORKFLOW.md)

### For DevOps/Deployment
1. **Deploying to production?** → Use [Deployment Guide](./DEPLOYMENT.md)
2. **Having issues?** → Check [Troubleshooting](./TROUBLESHOOTING.md)

### For Project Management
1. **Project overview** → [Main README](../README.md)
2. **Feature status** → [Development Guide](./DEVELOPMENT.md#features)

## 🔧 Key Commands Reference

### Development
```bash
# Start development
npm run dev:backend    # Backend only
npm run dev:frontend   # Frontend only
npm run dev:full       # Both services

# Testing & Quality
npm run lint          # Lint frontend
npm run type-check    # TypeScript checking
npm run quick:check   # Both lint + type check
```

### Production
```bash
# Build & Deploy
npm run build         # Build frontend
npm run prod:up       # Start production stack
npm run prod:down     # Stop production stack
npm run prod:logs     # View production logs
```

### Docker Services
```bash
# Development
docker-compose -f compose/docker-compose.yml up radio-backend -d

# Production  
docker-compose -f compose/docker-compose.prod.yml up -d

# CI/CD
docker-compose -f compose/docker-compose.ci.yml up
```

## 📁 Project Structure Quick Reference

```
radio-wifi/
├── frontend/                    # SvelteKit frontend
│   ├── src/routes/             # File-based routing
│   ├── src/lib/components/     # Reusable components
│   ├── src/lib/stores/         # State management
│   └── src/lib/types.ts        # TypeScript definitions
├── backend/                     # FastAPI backend
│   ├── main.py                 # API application
│   └── requirements.txt        # Python dependencies
├── compose/                     # Docker Compose configurations
│   ├── docker-compose.yml      # Development
│   ├── docker-compose.prod.yml # Production
│   └── docker-compose.ci.yml   # CI/CD
├── docker/                      # Dockerfiles
├── nginx/                       # Production web server
├── config/                      # System configurations
├── scripts/                     # Deployment scripts
└── docs/                       # This documentation
```

## 🎯 Common Tasks

### I want to...

**Start developing locally**
1. Read [Development Guide](./DEVELOPMENT.md#local-development)
2. Run `npm run dev:backend` and `npm run dev:frontend`

**Deploy to Raspberry Pi** 
1. Follow [Deployment Guide](./DEPLOYMENT.md#raspberry-pi-deployment)
2. Use deployment scripts in `/scripts/`

**Understand the SvelteKit migration**
1. Read [SvelteKit Migration](./SVELTEKIT-MIGRATION.md)
2. Check the before/after comparisons

**Fix a bug or contribute**
1. Follow [Workflow Guide](./WORKFLOW.md#development-workflow) 
2. Create feature branch and PR

**Troubleshoot issues**
1. Check [Troubleshooting](./TROUBLESHOOTING.md)
2. Look for your specific error message

## 🔍 Documentation Standards

All documentation follows these principles:
- **Practical**: Step-by-step instructions with commands
- **Complete**: Cover both development and production scenarios
- **Current**: Updated with latest architecture (SvelteKit + FastAPI)
- **Searchable**: Clear headings and structure
- **Examples**: Real commands and code snippets

## 🆘 Need Help?

1. **Check existing docs** - Search through the documentation above
2. **Common issues** - Look in [Troubleshooting](./TROUBLESHOOTING.md)
3. **Development setup** - Follow [Development Guide](./DEVELOPMENT.md)
4. **Create an issue** - Open GitHub issue with detailed description

---

**Last Updated**: December 2024  
**Architecture**: SvelteKit + FastAPI Hybrid  
**Target Platform**: Raspberry Pi Zero 2 W (ARM64)