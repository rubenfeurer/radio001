# Troubleshooting Guide

Common issues and solutions for the Radio WiFi Configuration project using the **SvelteKit + FastAPI hybrid architecture**.

## 🚨 ARM64 Issues (SOLVED!)

### The oxc-parser Problem
**❌ Old Problem**: `Cannot find module '@oxc-parser/binding-linux-arm64-gnu'`

**✅ Solution**: Migrated to SvelteKit (no oxc-parser dependency)

**Why This Happened**:
- Nuxt 3.17.1+ introduced oxc-parser
- oxc-parser lacks ARM64 binaries
- Affected Raspberry Pi Zero 2 W and M1/M2 Macs

**Migration Benefits**:
- ✅ No more ARM64 compatibility issues
- ✅ Faster local development
- ✅ Smaller bundle sizes
- ✅ Better performance

## 🛠️ Development Issues

### Backend Won't Start (Docker)

**Error**: `docker-compose up radio-backend` fails

**Diagnosis**:
```bash
# Check Docker status
docker --version
docker-compose --version

# View detailed error logs
docker-compose logs radio-backend

# Check if port is in use
lsof -i :8000
```

**Solutions**:
```bash
# Clean restart
docker-compose down -v
docker-compose up radio-backend -d

# Rebuild backend container
docker-compose build --no-cache radio-backend

# Check backend health
curl http://localhost:8000/health
```

### Frontend Won't Start (Local)

**Error**: `npm run dev` fails in frontend directory

**Common Causes & Solutions**:

1. **Node.js Version Issue**:
   ```bash
   # Check Node version (requires 18+)
   node --version
   
   # Install correct version
   nvm install 18
   nvm use 18
   ```

2. **Dependencies Not Installed**:
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Port Conflict**:
   ```bash
   # Check what's using port 3000
   lsof -i :3000
   
   # Kill conflicting process
   kill -9 $(lsof -ti:3000)
   
   # Or use different port
   npm run dev -- --port 3001
   ```

4. **TypeScript Errors**:
   ```bash
   # Check for type errors
   npm run check
   
   # Fix common issues
   npm run lint:fix
   ```

### API Proxy Not Working

**Error**: Frontend can't reach backend API

**Symptoms**:
- API calls return 404 or timeout
- Network tab shows failed requests to `/api/*`

**Diagnosis**:
```bash
# Test backend directly
curl http://localhost:8000/health

# Test frontend proxy
curl http://localhost:3000/api/health

# Check Vite proxy config
cat frontend/vite.config.js
```

**Solutions**:

1. **Backend Not Running**:
   ```bash
   docker-compose up radio-backend -d
   ```

2. **Proxy Misconfiguration**:
   ```javascript
   // frontend/vite.config.js
   export default defineConfig({
     server: {
       proxy: {
         '/api': {
           target: 'http://localhost:8000',
           changeOrigin: true
         }
       }
     }
   });
   ```

3. **Network Issues**:
   ```bash
   # Check Docker network
   docker network ls
   docker inspect radio001_radio-network
   ```

## 🖥️ Frontend-Specific Issues

### SvelteKit Build Errors

**Error**: `npm run build` fails

**Common Issues**:

1. **TypeScript Errors**:
   ```bash
   # Check types
   npm run check
   
   # Fix in src/lib/types.ts
   ```

2. **Import Resolution**:
   ```bash
   # Check for invalid imports
   grep -r "from.*app/" src/
   
   # Use correct Svelte imports
   # ❌ import { page } from '$app/page'
   # ✅ import { page } from '$app/stores'
   ```

3. **Adapter Issues**:
   ```javascript
   // svelte.config.js
   import adapter from '@sveltejs/adapter-static';
   
   export default {
     kit: {
       adapter: adapter({
         fallback: 'index.html'  // For SPA routing
       })
     }
   };
   ```

### Store Reactivity Issues

**Problem**: Store values not updating in components

**Solution**:
```svelte
<script lang="ts">
  import { networks } from '$lib/stores/wifi';
  
  // ✅ Correct - reactive statement
  $: networkList = $networks;
  
  // ✅ Correct - direct store access
  {#each $networks as network}
    <div>{network.ssid}</div>
  {/each}
</script>
```

### Routing Issues

**Problem**: Page routes not working

**Diagnosis**:
```bash
# Check route structure
ls -la frontend/src/routes/
```

**Solutions**:

1. **File Naming**:
   ```
   ✅ Correct structure:
   routes/
   ├── +page.svelte          # Home (/)
   ├── setup/
   │   └── +page.svelte      # Setup (/setup)
   └── status/
       └── +page.svelte      # Status (/status)
   
   ❌ Wrong:
   routes/
   ├── index.svelte
   ├── setup.svelte
   └── status.svelte
   ```

2. **Navigation**:
   ```svelte
   <script>
     import { goto } from '$app/navigation';
   </script>
   
   <!-- ✅ Correct -->
   <button on:click={() => goto('/setup')}>Setup</button>
   
   <!-- ❌ Wrong -->
   <button on:click={() => navigateTo('/setup')}>Setup</button>
   ```

## 🐳 Production Issues

### Nginx Not Serving Files

**Error**: 404 errors in production

**Diagnosis**:
```bash
# Check if files exist in container
docker exec radio-frontend-prod ls -la /usr/share/nginx/html

# Check nginx configuration
docker exec radio-frontend-prod cat /etc/nginx/conf.d/default.conf

# View nginx logs
docker exec radio-frontend-prod tail -f /var/log/nginx/error.log
```

**Solutions**:

1. **Frontend Not Built**:
   ```bash
   cd frontend
   npm run build
   
   # Verify build output
   ls -la build/
   ```

2. **Volume Mount Issues**:
   ```yaml
   # docker-compose.prod.yml
   services:
     radio-frontend:
       volumes:
         - ./frontend/build:/usr/share/nginx/html:ro  # Ensure path is correct
   ```

3. **File Permissions**:
   ```bash
   # Fix permissions
   chmod -R 755 frontend/build/
   ```

### Backend Container Issues

**Error**: Backend container exits or restarts

**Diagnosis**:
```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# View container logs
docker-compose -f docker-compose.prod.yml logs radio-backend

# Check resource usage
docker stats radio-backend-prod
```

**Solutions**:

1. **Memory Issues** (common on Pi Zero):
   ```bash
   # Check available memory
   free -h
   
   # Increase swap
   sudo dphys-swapfile swapoff
   sudo sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=1024/' /etc/dphys-swapfile
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

2. **Permission Issues**:
   ```bash
   # Check if backend has WiFi access
   docker exec radio-backend-prod ls -la /etc/wpa_supplicant/
   
   # Ensure proper capabilities
   # In docker-compose.prod.yml:
   privileged: true
   cap_add:
     - NET_ADMIN
     - NET_RAW
   ```

## 🔧 System Integration Issues

### WiFi Management Not Working

**Problem**: Can't scan or connect to networks

**Diagnosis**:
```bash
# Check WiFi interface
iwconfig

# Test manual scanning
sudo iwlist wlan0 scan | head -20

# Check system services
sudo systemctl status hostapd
sudo systemctl status dnsmasq
sudo systemctl status wpa_supplicant
```

**Solutions**:

1. **Interface Issues**:
   ```bash
   # Ensure correct interface name
   ip link show
   
   # Update environment variable
   export WIFI_INTERFACE=wlan0  # or wlan1, etc.
   ```

2. **Permission Issues**:
   ```bash
   # Check if container can access WiFi
   docker exec radio-backend-prod iwconfig
   
   # If fails, check container configuration
   ```

3. **Service Conflicts**:
   ```bash
   # Stop conflicting services
   sudo systemctl stop NetworkManager
   sudo systemctl disable NetworkManager
   
   # Use systemd-networkd instead
   sudo systemctl enable systemd-networkd
   ```

### Captive Portal Not Working

**Problem**: Mobile devices don't auto-open browser

**Diagnosis**:
```bash
# Test captive portal endpoints
curl http://radio.local/generate_204
curl http://radio.local/connecttest.txt
curl http://radio.local/hotspot-detect.html
```

**Solutions**:

1. **DNS Issues**:
   ```bash
   # Check DNS resolution
   nslookup radio.local
   
   # Restart avahi
   docker-compose -f docker-compose.prod.yml restart avahi
   ```

2. **Firewall Issues**:
   ```bash
   # Check firewall rules
   sudo ufw status
   
   # Allow HTTP traffic
   sudo ufw allow 80/tcp
   ```

### mDNS Resolution Issues

**Problem**: `radio.local` doesn't resolve

**Diagnosis**:
```bash
# Test mDNS resolution
ping radio.local
avahi-resolve -n radio.local

# Check avahi service
docker-compose -f docker-compose.prod.yml logs avahi
```

**Solutions**:

1. **Avahi Not Running**:
   ```bash
   # Start avahi with mdns profile
   docker-compose -f docker-compose.prod.yml --profile mdns up -d
   ```

2. **Network Configuration**:
   ```bash
   # Check network mode
   docker inspect radio-avahi | grep NetworkMode
   
   # Should be "host" for mDNS
   ```

## 🔍 Debugging Commands

### Development Debugging
```bash
# Backend debugging
docker-compose logs radio-backend
docker-compose exec radio-backend bash

# Frontend debugging  
cd frontend
npm run check        # Type checking
npm run lint         # Code linting
npm run build        # Test build

# Network debugging
curl -v http://localhost:8000/health
curl -v http://localhost:3000/api/health
```

### Production Debugging
```bash
# Service status
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs

# System status
sudo systemctl status docker
free -h
df -h

# Network status
iwconfig
ip addr show
sudo systemctl status avahi-daemon
```

### Performance Debugging
```bash
# Resource usage
docker stats
htop

# Network performance
iperf3 -s  # On server
iperf3 -c radio.local  # On client

# Disk I/O
sudo iotop
```

## 📊 Monitoring & Health Checks

### Automated Health Checks
```bash
#!/bin/bash
# health-check.sh
echo "🔍 Radio WiFi Health Check"

# Backend health
if curl -sf http://localhost:8000/health; then
  echo "✅ Backend healthy"
else
  echo "❌ Backend unhealthy"
fi

# Frontend health
if curl -sf http://localhost:3000; then
  echo "✅ Frontend healthy"
else
  echo "❌ Frontend unhealthy"
fi

# WiFi interface
if iwconfig wlan0 | grep -q "IEEE 802.11"; then
  echo "✅ WiFi interface active"
else
  echo "❌ WiFi interface issues"
fi
```

### Log Analysis
```bash
# Analyze nginx logs
tail -f /var/log/nginx/radio_access.log | grep -E "4[0-9]{2}|5[0-9]{2}"

# Analyze backend logs
docker-compose logs radio-backend | grep -i error

# System logs
journalctl -u docker -f
```

## 🚨 Emergency Recovery

### Complete System Reset
```bash
#!/bin/bash
# emergency-reset.sh
echo "⚠️  Performing emergency reset..."

# Stop all services
docker-compose down -v
docker-compose -f docker-compose.prod.yml down -v

# Clean Docker
docker system prune -af
docker volume prune -f

# Reset WiFi configuration
sudo systemctl stop wpa_supplicant hostapd dnsmasq
sudo cp /etc/wpa_supplicant/wpa_supplicant.conf.backup /etc/wpa_supplicant/wpa_supplicant.conf

# Restart services
sudo systemctl restart networking
docker-compose -f docker-compose.prod.yml up -d

echo "✅ Reset complete"
```

### Backup & Restore
```bash
# Create backup
./scripts/backup-config.sh

# Restore from backup
./scripts/restore-config.sh backup_20241201.tar.gz
```

## 📞 Getting Help

### Diagnostic Information
When seeking help, provide:

```bash
# System information
uname -a
docker --version
docker-compose --version
node --version

# Service status
docker-compose ps
curl -I http://localhost:8000/health
curl -I http://localhost:3000

# Log excerpts (last 50 lines)
docker-compose logs --tail=50 radio-backend
docker-compose logs --tail=50 radio-frontend
```

### Common Error Patterns

1. **"Address already in use"** → Port conflict (kill process or change port)
2. **"Cannot find module"** → Missing dependencies (npm install)
3. **"exec format error"** → Platform mismatch (check Docker platform)
4. **"Permission denied"** → File/device permissions (check volumes/devices)
5. **"Connection refused"** → Service not running (check container status)

### Resources
- [SvelteKit Docs](https://kit.svelte.dev/docs)
- [Docker Troubleshooting](https://docs.docker.com/config/daemon/troubleshoot/)
- [Nginx Configuration](https://nginx.org/en/docs/troubleshooting_faq.html)
- [Raspberry Pi Forum](https://www.raspberrypi.org/forums/)

---

This troubleshooting guide covers the most common issues with the new SvelteKit + FastAPI architecture. The migration has eliminated the major ARM64 compatibility issues while introducing a more reliable and performant solution.