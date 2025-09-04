# Troubleshooting Guide

Common issues and solutions for the Radio WiFi Configuration project.

## 🐳 Docker Issues

### Docker Not Running
```bash
# Check Docker status
docker info

# Start Docker Desktop (macOS/Windows)
open -a Docker

# Start Docker service (Linux)
sudo systemctl start docker
```

### Build Failures on Apple Silicon
**Error**: `Failed to build installable wheels for pydantic-core`

**Solution**: Use the setup script (handles platform detection automatically)
```bash
./scripts/setup-dev.sh
./scripts/docker-dev.sh start
```

### Platform Mismatch Errors
**Error**: `exec format error` or `exec /bin/sh: exec format error`

**Cause**: Trying to run ARM64 containers on AMD64 system (or vice versa)

**Solutions**:
```bash
# Force correct platform for your system
export DOCKER_DEFAULT_PLATFORM=linux/amd64  # For Intel/AMD
export DOCKER_DEFAULT_PLATFORM=linux/arm64  # For Apple Silicon

# Use CI configuration (AMD64) for testing
./scripts/test-ci.sh

# Clean rebuild with correct platform
./scripts/docker-dev.sh cleanup
./scripts/docker-dev.sh start
```

### Port Conflicts
**Error**: `Port 3000 is already in use`

**Solution**:
```bash
# Find and kill process using the port
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9

# Or use different ports
FRONTEND_PORT=3001 BACKEND_PORT=8001 ./scripts/docker-dev.sh start
```

### Memory Issues
**Error**: Container exits with out of memory errors

**Solution**: Increase Docker Desktop memory to 4GB+ in Settings → Resources

### Container Won't Start
```bash
# Clean restart
./scripts/docker-dev.sh stop
./scripts/docker-dev.sh cleanup
./scripts/docker-dev.sh start

# Check logs
./scripts/docker-dev.sh logs
```

## 🛠️ Development Issues

### TypeScript Import Errors in IDE
**Issue**: IDE shows import errors for packages

**Solution**: This is expected behavior - packages are installed in Docker containers
```bash
# For accurate type checking, use Docker
./scripts/docker-dev.sh shell radio-app
npm run type-check
```

### Pre-commit Hooks Not Working
```bash
# Reinstall hooks
cd app && npm run prepare
chmod +x .husky/pre-commit .husky/commit-msg

# Test hooks manually
npm run lint:fix
npm run type-check
```

### Hot Reload Not Working
```bash
# For macOS users - enable polling
export CHOKIDAR_USEPOLLING=true
export WATCHPACK_POLLING=true
./scripts/docker-dev.sh restart
```

### TypeScript Union Type Errors
**Error**: `Property 'data' does not exist on type...`

**Solution**: Use proper type guards
```typescript
// ✅ Correct
if (response.success && 'data' in response) {
  data.value = response.data
} else if (!response.success && 'error' in response) {
  throw new Error(response.error)
}

// ❌ Wrong
if (response.success) {
  data.value = response.data
}
```

## 🌐 Network Issues

### Cannot Access radio.local
**Issue**: mDNS resolution not working

**Solutions**:
```bash
# Check if containers are running
docker ps

# Use direct IP instead
curl http://localhost:3000/api/health
curl http://localhost:8000/health

# Check mDNS service (Linux)
systemctl status avahi-daemon
```

### API Connection Timeouts
```bash
# Check backend health
curl http://localhost:8000/health

# Check backend logs
./scripts/docker-dev.sh logs radio-backend

# Restart backend service
./scripts/docker-dev.sh restart
```

### Frontend Blank Page
```bash
# Check frontend logs
./scripts/docker-dev.sh logs radio-app

# Rebuild frontend
./scripts/docker-dev.sh shell radio-app
npm run build

# Check for JavaScript errors in browser console
```

## 📱 Application Issues

### WiFi Scan Fails on Raspberry Pi
**Issue**: No networks found or scan errors

**Solutions**:
```bash
# Check WiFi interface
sudo ip addr show wlan0
sudo iwconfig wlan0

# Check permissions
sudo usermod -aG netdev $USER

# Manual scan test
sudo iwlist wlan0 scan

# Check system logs
journalctl -u wpa_supplicant
sudo dmesg | grep wlan
```

### Connection Fails After Entering Password
**Possible causes**:
1. **Incorrect password** - Double-check WiFi credentials
2. **Weak signal** - Move closer to router
3. **Network issues** - Check if network accepts new devices
4. **Interface busy** - Restart networking service

**Debug steps**:
```bash
# Check wpa_supplicant logs
journalctl -u wpa_supplicant -f

# Check network manager logs
journalctl -u NetworkManager -f

# Restart networking
sudo systemctl restart networking
```

### Hotspot Mode Not Working
```bash
# Check hostapd service
sudo systemctl status hostapd
journalctl -u hostapd

# Check hostapd configuration
sudo hostapd -dd /etc/hostapd/hostapd.conf

# Check IP forwarding
cat /proc/sys/net/ipv4/ip_forward

# Restart hostapd
sudo systemctl restart hostapd
```

## 🔧 System Issues

### High CPU Usage
```bash
# Check container resource usage
docker stats

# Check system processes
./scripts/docker-dev.sh shell radio-backend
top

# Restart services
./scripts/docker-dev.sh restart
```

### Low Memory on Raspberry Pi
**Solutions**:
1. **Increase swap space**:
   ```bash
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=1024
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

2. **Optimize Docker memory limits** (already configured in docker-compose.prod.yml)

### Service Won't Start on Boot
```bash
# Enable Docker service
sudo systemctl enable docker

# Create systemd service for the application
sudo nano /etc/systemd/system/radio-wifi.service
```

Example systemd service:
```ini
[Unit]
Description=Radio WiFi Configuration
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/docker-compose -f /home/pi/radio001/docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f /home/pi/radio001/docker-compose.prod.yml down
WorkingDirectory=/home/pi/radio001

[Install]
WantedBy=multi-user.target
```

Then enable it:
```bash
sudo systemctl enable radio-wifi
sudo systemctl start radio-wifi
```

## 🔍 Debugging Commands

### Container Diagnostics
```bash
# View all containers
docker ps -a

# Check container logs
./scripts/docker-dev.sh logs radio-app
./scripts/docker-dev.sh logs radio-backend

# Execute commands in containers
./scripts/docker-dev.sh shell radio-app
./scripts/docker-dev.sh shell radio-backend

# Check container resources
docker stats
```

### Health Checks
```bash
# Manual health checks
curl http://localhost:3000/api/health
curl http://localhost:8000/health

# Check service status
./scripts/docker-dev.sh status

# Test WiFi APIs
curl http://localhost:3000/api/wifi/status
curl -X POST http://localhost:3000/api/wifi/scan
```

### Log Analysis
```bash
# Follow all logs
./scripts/docker-dev.sh logs -f

# Frontend logs only
./scripts/docker-dev.sh logs radio-app

# Backend logs only
./scripts/docker-dev.sh logs radio-backend

# CI configuration logs
docker compose -f docker-compose.ci.yml logs

# System logs (Raspberry Pi)
journalctl -f
```

### Platform Testing
```bash
# Test CI configuration locally
./scripts/test-ci.sh

# Check current platform
docker version --format '{{.Server.Arch}}'
uname -m

# Force platform and rebuild
export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker compose -f docker-compose.ci.yml build --no-cache
```

## 🚀 Performance Optimization

### Raspberry Pi Zero 2 W Optimization

**Already implemented**:
- Memory limits for containers
- Resource-efficient Docker images
- Optimized Nuxt configuration
- Minimal dependencies

**Additional optimizations**:
```bash
# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable cups

# Optimize GPU memory split
echo "gpu_mem=16" | sudo tee -a /boot/config.txt

# Enable I2C/SPI only if needed
sudo raspi-config
```

## 🆘 Getting Help

If issues persist:

1. **Check logs**: Run `./scripts/docker-dev.sh logs` for detailed error information
2. **Platform issues**: Verify you're using the correct Docker Compose configuration for your platform
3. **Network connectivity**: Test basic network connectivity before WiFi configuration
4. **System resources**: Ensure adequate memory and storage space

For development issues, see [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup and workflow guidance.