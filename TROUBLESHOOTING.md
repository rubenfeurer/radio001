# Troubleshooting Guide - Radio WiFi Configuration

This guide covers common issues and solutions for the Radio WiFi Configuration project.

## 🐳 Docker Issues

### Docker Not Running

**Error:**
```
Cannot connect to the Docker daemon at unix:///Users/username/.docker/run/docker.sock. Is the docker daemon running?
```

**Solution:**
```bash
# Start Docker Desktop (macOS/Windows)
open -a Docker

# Or start Docker service (Linux)
sudo systemctl start docker

# Verify Docker is running
docker info
```

### Pydantic Build Errors on Apple Silicon

**Error:**
```
ERROR: Failed to build installable wheels for some pyproject.toml based projects (pydantic-core)
```

**Solutions:**

1. **Use the Apple Silicon optimized build:**
   ```bash
   # The script automatically detects Apple Silicon and uses optimized configuration
   ./scripts/docker-dev.sh start
   ```

2. **Manual Docker Compose with override:**
   ```bash
   # Force use of arm64 optimized images
   docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d --build
   ```

3. **Clear Docker cache and rebuild:**
   ```bash
   # Clean all Docker resources
   ./scripts/docker-dev.sh cleanup
   
   # Rebuild from scratch
   ./scripts/docker-dev.sh rebuild
   ```

4. **Alternative: Use pre-built images (when available):**
   ```bash
   # Pull instead of building locally
   docker-compose pull
   docker-compose up -d
   ```

### Memory Issues

**Error:**
```
ERROR: Container killed due to memory usage
```

**Solution:**
```bash
# Increase Docker Desktop memory limit to 4GB+
# Docker Desktop → Settings → Resources → Memory

# Or use resource limits in docker-compose.override.yml (already configured)
# The override file limits backend to 512MB and frontend to 1GB
```

### Port Already in Use

**Error:**
```
Error starting userland proxy: listen tcp 0.0.0.0:3000: bind: address already in use
```

**Solution:**
```bash
# Find and kill process using the port
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9

# Or use different ports
FRONTEND_PORT=3001 BACKEND_PORT=8001 docker-compose up -d
```

## 🔧 Build Issues

### Version Compatibility

**Error:**
```
WARN: the attribute `version` is obsolete, it will be ignored
```

**Solution:**
This warning can be safely ignored. The `version` field has been removed from newer docker-compose files.

### Node.js Module Issues

**Error:**
```
Module not found: Can't resolve 'some-module'
```

**Solution:**
```bash
# Rebuild node_modules volume
docker-compose down -v
docker volume rm radio001_radio_node_modules
docker-compose up -d --build
```

### Python Package Issues

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Rebuild backend container
./scripts/docker-dev.sh rebuild radio-backend

# Or rebuild all services
./scripts/docker-dev.sh rebuild
```

## 🌐 Network Issues

### Services Can't Communicate

**Error:**
```
Connection refused when frontend tries to reach backend
```

**Solution:**
```bash
# Check if both services are running
./scripts/docker-dev.sh status

# Check network connectivity
docker-compose exec radio-app ping radio-backend

# Restart with fresh network
docker-compose down
docker-compose up -d
```

### API Proxy Issues

**Error:**
```
504 Gateway Timeout from API proxy
```

**Solution:**
```bash
# Check backend health
curl http://localhost:8000/health

# Check backend logs
./scripts/docker-dev.sh logs radio-backend

# Restart backend service
docker-compose restart radio-backend
```

## 📱 Application Issues

### Frontend Not Loading

**Symptoms:**
- Blank page at http://localhost:3000
- Build errors in logs

**Solution:**
```bash
# Check frontend logs
./scripts/docker-dev.sh logs radio-app

# Common fixes:
./scripts/docker-dev.sh rebuild radio-app

# If TypeScript errors:
docker-compose exec radio-app npm run typecheck
```

### Backend API Errors

**Symptoms:**
- 500 errors from API endpoints
- Backend container keeps restarting

**Solution:**
```bash
# Check backend logs
./scripts/docker-dev.sh logs radio-backend

# Check if main.py exists
docker-compose exec radio-backend ls -la

# Restart backend
docker-compose restart radio-backend
```

### Hot Reload Not Working

**Symptoms:**
- Changes to code don't trigger reload
- Need to manually restart containers

**Solution:**
```bash
# Check volume mounts
docker-compose exec radio-app ls -la /app/app

# For macOS users - ensure file watching works
export CHOKIDAR_USEPOLLING=true
export WATCHPACK_POLLING=true
docker-compose up -d --force-recreate
```

## 🔍 Debugging Commands

### Useful Docker Commands

```bash
# View all containers
docker ps -a

# View container logs
docker logs radio-wifi-dev -f
docker logs radio-backend-dev -f

# Execute commands in containers
docker-compose exec radio-app sh
docker-compose exec radio-backend bash

# Check container resource usage
docker stats

# Inspect container details
docker inspect radio-wifi-dev
```

### Health Checks

```bash
# Manual health checks
curl http://localhost:3000/api/health
curl http://localhost:8000/health

# Check service status
./scripts/docker-dev.sh status

# View detailed container info
docker-compose ps
```

### Network Debugging

```bash
# List Docker networks
docker network ls

# Inspect project network
docker network inspect radio001_radio-network

# Test connectivity between containers
docker-compose exec radio-app ping radio-backend
docker-compose exec radio-backend ping radio-app
```

## 🧹 Clean Reset

When all else fails, perform a complete reset:

```bash
# Stop all services
./scripts/docker-dev.sh stop

# Clean up everything
./scripts/docker-dev.sh cleanup

# Remove all project containers and images
docker-compose down -v --rmi all

# Remove Docker build cache
docker builder prune -a

# Start fresh
./scripts/docker-dev.sh start
```

## 🍎 Apple Silicon Specific Issues

### Rosetta Emulation

If you encounter platform issues:

```bash
# Force arm64 platform
export DOCKER_DEFAULT_PLATFORM=linux/arm64

# Or use platform-specific compose
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

### Performance Issues

```bash
# Enable VirtioFS for better performance
# Docker Desktop → Settings → General → "Use VirtioFS"

# Increase resource limits
# Docker Desktop → Settings → Resources
# CPU: 4+ cores
# Memory: 4+ GB
# Disk: 32+ GB
```

## 📞 Getting Help

### Log Collection

When reporting issues, include:

```bash
# System information
uname -a
docker --version
docker-compose --version

# Service status
./scripts/docker-dev.sh status

# Recent logs
./scripts/docker-dev.sh logs > debug-logs.txt
```

### Common Diagnostics

```bash
# Check disk space
docker system df

# Check Docker daemon logs (macOS)
tail -f ~/Library/Containers/com.docker.docker/Data/log/vm/console-ring

# Check Docker daemon logs (Linux)
journalctl -u docker.service -f
```

## 📚 Additional Resources

- [Docker Desktop Troubleshooting](https://docs.docker.com/desktop/troubleshoot/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Nuxt 3 Troubleshooting](https://nuxt.com/docs/guide/concepts/auto-imports#troubleshooting)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

💡 **Pro Tip**: Most issues can be resolved with `./scripts/docker-dev.sh cleanup` followed by `./scripts/docker-dev.sh start`
