# Development Workflow Guide

A pragmatic Git workflow for reliable development with quick feedback loops.

## 🌳 Branch Structure

```
main     ──────●─────●─────●──── (Production ready)
           ╱         ╱         ╱
develop ──●─────●───●─────●───●── (Active development)
           ╲   ╱     ╲   ╱
features    ●─●       ●─●────────── (Feature branches)
```

### Branches:
- **`main`** - Production ready, fully validated code
- **`develop`** - Integration branch for ongoing development
- **`feature/*`** - Individual features (optional, can work directly on develop)

## 🚀 Getting Started

### Initialize Development
```bash
# Set up develop branch
npm run workflow:init

# Check current status
npm run workflow:status
```

### Daily Development
```bash
# Quick local checks
npm run quick:check

# Auto-fix common issues
npm run quick:fix

# Start development
npm run dev
```

## 📋 Testing Strategy

### 🏠 Local Testing (Pre-commit)

**On any branch:**
- ✅ ESLint with auto-fixes
- ✅ Basic validation

**On develop branch:**
- ✅ ESLint with auto-fixes
- ✅ TypeScript type checking (non-blocking warnings)
- ⚡ Quick feedback for development

**On main branch:**
- ✅ ESLint with auto-fixes
- ✅ Full TypeScript validation (blocking)
- 🔒 Strict checks before production

### ☁️ CI/CD Testing

**Develop Branch CI** (`develop-ci.yml`):
- ⚡ Fast feedback (~3-5 minutes)
- ✅ Linting & Type checking
- ✅ Build validation
- ✅ Basic Docker build test
- 📊 Development tips and next steps

**Main Branch CI** (`ci-cd.yml`):
- 🔍 Full validation (~15-20 minutes)
- ✅ Pre-flight checks (PRs only)
- ✅ Integration tests with Docker
- ✅ Security scanning
- ✅ Multi-architecture builds
- 🚀 Production deployment

## 🔄 Development Workflow

### 1. Feature Development
```bash
# Work on develop branch
git checkout develop
git pull origin develop

# Make changes
# ... code ...

# Quick local validation
npm run quick:check

# Commit (triggers light pre-commit checks)
git add .
git commit -m "feat: add new feature"

# Push to trigger develop CI
git push origin develop
```

### 2. Ready for Production
```bash
# Create PR to main
npm run workflow:pr

# Or manually:
# Visit GitHub and create PR: develop → main
```

### 3. Production Deployment
```bash
# After PR is approved and merged
git checkout main
git pull origin main

# Production CI/CD runs automatically
# Includes full integration tests, security scans, and deployment
```

## 🎯 Commands Reference

### Workflow Commands
```bash
npm run workflow:init     # Initialize develop branch
npm run workflow:status   # Show current branch and status  
npm run workflow:pr       # Helper to create PR develop → main
```

### Development Commands
```bash
npm run dev              # Start development server
npm run quick:check      # Run linting + type checking
npm run quick:fix        # Auto-fix linting issues
npm run build            # Build for production
npm run type-check       # TypeScript validation
```

### Docker Commands
```bash
npm run dev:docker       # Development with Docker
npm run prod:up          # Production deployment
npm run health           # Health check
```

## ⚡ Quick Reference

### ✅ When to use develop branch:
- Daily development work
- Experimental features
- Quick iterations with fast feedback
- Collaborative development

### ✅ When to merge to main:
- Feature is complete and tested
- Ready for production deployment
- Passed all develop branch validations
- Reviewed and approved

### 🚫 Avoid:
- Direct commits to main (use PRs)
- Pushing broken code to develop
- Skipping local quick checks
- Large, unfocused commits

## 🔧 Troubleshooting

### Pre-commit Hook Issues
```bash
# If hooks aren't working:
cd app && npx husky install

# If type checking fails on develop:
npm run type-check
# Fix issues or commit with warnings (develop allows this)
```

### CI Failures
```bash
# Check develop CI status:
# Visit: https://github.com/your-repo/actions

# Re-run failed jobs if needed
# Fix issues and push again
```

### Branch Sync Issues
```bash
# Sync develop with main:
git checkout develop
git pull origin main
git push origin develop
```

## 📊 Validation Matrix

| Stage | Linting | Type Check | Build | Docker | Integration | Security |
|-------|---------|------------|-------|--------|-------------|----------|
| **Local (develop)** | ✅ Auto-fix | ⚠️ Warn | - | - | - | - |
| **Local (main)** | ✅ Auto-fix | ✅ Block | - | - | - | - |
| **CI (develop)** | ✅ | ✅ | ✅ | ✅ Basic | - | - |
| **CI (main PR)** | ✅ | ✅ | ✅ | ✅ Full | ✅ | ✅ |
| **CI (main push)** | ✅ | ✅ | ✅ | ✅ Deploy | ✅ | ✅ |

## 🎉 Benefits

### For Developers:
- ⚡ **Fast feedback** on develop branch
- 🔧 **Auto-fixing** of common issues
- 🚀 **Quick iterations** without heavy CI overhead
- 💡 **Clear workflow** with helpful guidance

### For Production:
- 🛡️ **Comprehensive validation** before deployment
- 🔒 **Protected main branch** with required checks
- 📋 **Security scanning** and multi-arch builds
- 🎯 **Reliable deployments** with full integration tests

### For Team:
- 📖 **Clear process** that's easy to follow
- 🔄 **Consistent workflow** across all features
- 💬 **PR-based reviews** for quality control
- 📊 **Visibility** into validation status

---

## 💡 Pro Tips

1. **Use develop for daily work** - it's designed for fast iterations
2. **Keep commits focused** - easier to review and debug
3. **Watch the CI feedback** - it provides helpful next steps
4. **Create PRs early** - even for work in progress (use draft PRs)
5. **Keep main clean** - only merge completed, tested features

This workflow balances speed with reliability, giving you quick feedback during development while ensuring production quality on the main branch.