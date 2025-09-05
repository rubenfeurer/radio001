# Deployment Guide

Comprehensive deployment guide for the Radio WiFi Configuration project using the new **SvelteKit + FastAPI hybrid architecture**.

## 🚀 Quick Deployment

### Development Deployment
```bash
# 1. Start backend
docker-compose up radio-backend -d

# 2. Start frontend
cd frontend && npm run dev

# Access: http://localhost:3000
```

### Production Deployment (Raspberry Pi)
```bash
# 1. Build frontend
cd frontend && npm run build

# 2. Deploy with Docker
docker-compose -f docker-compose.prod.yml up -d

# Access: http://radio.local or http://[pi-ip]
```

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐
│     Nginx       │────│   FastAPI        │
│  Static Files   │    │   Backend        │
│  (SvelteKit)    │    │   (Docker)       │
└─────────────────┘    └──────────────────┘
       :80                      :8000
```

**Production Stack:**
- **Frontend**: Static SvelteKit build served by Nginx
- **Backend**: FastAPI in Docker container
- **Proxy**: Nginx proxies `/api/*` to backend
- **DNS**: Avahi for `radio.local` resolution

## 📋 Prerequisites

### Development
- Node.js 18+ (for SvelteKit frontend)
- Docker & Docker Compose (for backend)
- Git (for version control)

### Production (Raspberry Pi)
- Raspberry Pi Zero 2 W or Pi 4
- Raspberry Pi OS (64-bit recommended)
- Docker & Docker Compose
- Network access for initial setup

## 🛠️ Development Deployment

### 1. Repository Setup
```bash
git clone https://github.com/your-username/radio-wifi.git
cd radio-wifi
```

### 2. Backend Setup (Docker)
```bash
# Start backend service
docker-compose up radio-backend -d

# Verify backend is running
curl http://localhost:8000/health
```

### 3. Frontend Setup (Local)
```bash
# Setup SvelteKit frontend
./setup-frontend.sh

# Install dependencies
cd frontend
npm install

# Start development server
npm run dev
```

### 4. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:3000/api/health (proxied)

### 5. Development Commands
```bash
# View backend logs
docker-compose logs radio-backend

# Restart backend
docker-compose restart radio-backend

# Stop all services
docker-compose down

# Frontend development
cd frontend
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build
npm run check        # Type checking
npm run lint         # Code linting
```

## 🎯 Production Deployment

### Raspberry Pi Setup

#### 1. Prepare Raspberry Pi
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

#### 2. Clone and Configure
```bash
# Clone repository
git clone https://github.com/your-username/radio-wifi.git
cd radio-wifi

# Create environment file
cp .env.example .env
nano .env  # Configure as needed
```

#### 3. Build Frontend
```bash
# Setup and build frontend
./setup-frontend.sh
cd frontend
npm install
npm run build
```

#### 4. Deploy Services
```bash
# Start production services
docker-compose -f docker-compose.prod.yml up -d

# Enable mDNS (optional)
docker-compose -f docker-compose.prod.yml --profile mdns up -d
```

#### 5. Configure System Integration
```bash
# Setup WiFi system integration
sudo ./scripts/setup-pi.sh

# Configure as access point (if needed)
sudo ./scripts/configure-hotspot.sh
```

### Production Architecture

```yaml
# docker-compose.prod.yml structure
services:
  radio-backend:     # FastAPI backend
    build: ./backend
    ports: ["8000:8000"]
    
  radio-frontend:    # Nginx + SvelteKit static files
    image: nginx:alpine
    ports: ["80:80"]
    volumes:
      - ./frontend/build:/usr/share/nginx/html:ro
      
  avahi:            # mDNS for radio.local
    image: solidnerd/avahi
    network_mode: host
```

## 🔧 Configuration

### Environment Variables

Create `.env` file:
```env
# Network Configuration
WIFI_INTERFACE=wlan0
HOSTNAME=radio

# Hotspot Configuration  
HOTSPOT_SSID=Radio-Setup
HOTSPOT_PASSWORD=Configure123!
HOTSPOT_IP=192.168.4.1
HOTSPOT_RANGE=192.168.4.2,192.168.4.20

# Security (change in production!)
SESSION_SECRET=your-session-secret-here
JWT_SECRET=your-jwt-secret-here

# Features
ENABLE_CAPTIVE_PORTAL=true
ENABLE_AUTO_CONNECT=true
```

### Nginx Configuration

The production setup uses nginx to:
- Serve static SvelteKit files
- Proxy API requests to FastAPI backend
- Handle SSL termination (if configured)
- Provide captive portal detection

Key configuration in `nginx/default.conf`:
```nginx
# Serve SvelteKit static files
location / {
    try_files $uri $uri/ /index.html;
}

# Proxy API requests
location /api/ {
    proxy_pass http://radio-backend:8000;
}
```

## 📡 Network Configuration

### WiFi Interface Setup

The system manages WiFi through:
- **Client Mode**: Connects to existing WiFi networks
- **Hotspot Mode**: Creates access point for configuration

#### System Files Modified:
- `/etc/wpa_supplicant/wpa_supplicant.conf` - WiFi client configuration
- `/etc/hostapd/hostapd.conf` - Access point configuration
- `/etc/dnsmasq.conf` - DHCP server configuration

#### Required Permissions:
```bash
# Backend container needs access to:
- /etc/wpa_supplicant (read/write)
- /etc/hostapd (read/write)
- /dev/net/tun (device access)
- Network capabilities (NET_ADMIN, NET_RAW)
```

### Captive Portal

For automatic WiFi setup on mobile devices:
- Nginx serves captive portal detection endpoints
- Devices automatically open browser when connecting
- Users redirected to WiFi setup interface

Detection endpoints:
- `/generate_204` (Android)
- `/connecttest.txt` (Windows)
- `/hotspot-detect.html` (iOS)

## 🔍 Monitoring & Maintenance

### Health Checks

Built-in health monitoring:
```bash
# Check service health
curl http://radio.local/health
curl http://radio.local/api/health

# Docker health status
docker-compose -f docker-compose.prod.yml ps
```

### Log Management

```bash
# View service logs
docker-compose -f docker-compose.prod.yml logs radio-backend
docker-compose -f docker-compose.prod.yml logs radio-frontend

# Follow logs in real-time
docker-compose -f docker-compose.prod.yml logs -f

# Nginx access logs
docker exec radio-frontend-prod tail -f /var/log/nginx/radio_access.log
```

### System Updates

```bash
# Update application
git pull origin main
cd frontend && npm run build
docker-compose -f docker-compose.prod.yml up -d --build

# Update system packages
sudo apt update && sudo apt upgrade -y

# Clean Docker resources
docker system prune -f
docker volume prune -f
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Frontend Not Loading
```bash
# Check if nginx is serving files
docker exec radio-frontend-prod ls -la /usr/share/nginx/html

# Rebuild frontend
cd frontend && npm run build

# Restart frontend container
docker-compose -f docker-compose.prod.yml restart radio-frontend
```

#### 2. API Calls Failing
```bash
# Check backend health
curl http://localhost:8000/health

# Check proxy configuration
docker exec radio-frontend-prod cat /etc/nginx/conf.d/default.conf

# View nginx error logs
docker exec radio-frontend-prod tail /var/log/nginx/radio_error.log
```

#### 3. WiFi Management Issues
```bash
# Check WiFi interface
iwconfig

# Check system files
ls -la /etc/wpa_supplicant/
sudo systemctl status hostapd
sudo systemctl status dnsmasq

# Backend container permissions
docker exec radio-backend-prod ls -la /etc/wpa_supplicant/
```

#### 4. mDNS Not Working
```bash
# Test mDNS resolution
ping radio.local

# Check avahi service
docker-compose -f docker-compose.prod.yml logs avahi

# Restart avahi
docker-compose -f docker-compose.prod.yml restart avahi
```

### Performance Optimization

#### 1. Frontend Optimization
```bash
# Build with optimizations
cd frontend
npm run build

# Check bundle size
du -sh build/

# Enable nginx compression (already configured)
```

#### 2. Backend Optimization
```bash
# Monitor resource usage
docker stats radio-backend-prod

# Check memory usage
docker exec radio-backend-prod free -h

# Optimize Docker image
docker-compose -f docker-compose.prod.yml build --no-cache
```

#### 3. System Optimization
```bash
# Reduce memory usage
sudo sysctl vm.swappiness=10

# Optimize for SD card
sudo systemctl disable apt-daily.timer
sudo systemctl disable apt-daily-upgrade.timer
```

## 🔒 Security Considerations

### Production Security

1. **Change Default Passwords**:
   ```env
   HOTSPOT_PASSWORD=YourSecurePassword123!
   SESSION_SECRET=your-unique-session-secret
   JWT_SECRET=your-unique-jwt-secret
   ```

2. **Firewall Configuration**:
   ```bash
   sudo ufw enable
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw allow 22/tcp
   ```

3. **SSL/TLS Setup** (optional):
   ```bash
   # Generate self-signed certificates
   sudo mkdir -p /etc/nginx/ssl
   sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout /etc/nginx/ssl/radio.key \
     -out /etc/nginx/ssl/radio.crt
   ```

4. **Regular Updates**:
   ```bash
   # Setup automatic security updates
   sudo apt install unattended-upgrades
   sudo dpkg-reconfigure unattended-upgrades
   ```

## 📊 Backup & Recovery

### Backup Configuration
```bash
#!/bin/bash
# backup-config.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/radio-backup"

mkdir -p $BACKUP_DIR

# Backup configuration files
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
  /etc/wpa_supplicant \
  /etc/hostapd \
  /etc/dnsmasq.conf

# Backup Docker volumes
docker run --rm -v radio_data:/data -v $BACKUP_DIR:/backup \
  alpine tar -czf /backup/data_$DATE.tar.gz -C /data .

echo "Backup completed: $BACKUP_DIR"
```

### Recovery Process
```bash
#!/bin/bash
# restore-config.sh
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup_file>"
  exit 1
fi

# Stop services
docker-compose -f docker-compose.prod.yml down

# Restore configuration
sudo tar -xzf $BACKUP_FILE -C /

# Restart services
docker-compose -f docker-compose.prod.yml up -d

echo "Restore completed"
```

## 🚀 Advanced Deployment

### Multi-Environment Setup

```bash
# Staging environment
docker-compose -f docker-compose.staging.yml up -d

# Production environment
docker-compose -f docker-compose.prod.yml up -d

# Load balancer setup (multiple Pis)
docker-compose -f docker-compose.cluster.yml up -d
```

### CI/CD Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy to Pi
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Raspberry Pi
        run: |
          ssh pi@radio.local 'cd radio-wifi && git pull && ./deploy.sh'
```

### Container Registry

```bash
# Build and push images
docker build -t your-registry/radio-wifi-backend:latest ./backend
docker push your-registry/radio-wifi-backend:latest

# Deploy from registry
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 📈 Scaling Considerations

### Single Pi Optimization
- Use nginx for static file serving
- Enable gzip compression
- Optimize Docker images
- Use volume mounts for persistent data

### Multi-Pi Cluster
- Shared configuration via Docker Swarm
- Load balancing with nginx upstream
- Centralized logging with ELK stack
- Monitoring with Prometheus/Grafana

## 📚 Additional Resources

- [SvelteKit Deployment](https://kit.svelte.dev/docs/adapters)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Raspberry Pi Setup](https://www.raspberrypi.org/documentation/)
- [WiFi Configuration](https://www.raspberrypi.org/documentation/computers/configuration.html#configuring-networking)

---

This deployment guide covers everything from development setup to production deployment, monitoring, and maintenance. The new architecture eliminates ARM64 compatibility issues while providing a robust, scalable solution for WiFi configuration on Raspberry Pi devices.