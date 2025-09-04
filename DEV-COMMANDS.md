# Docker Development Quick Reference

Quick reference for Docker-based development commands for the Radio WiFi Configuration project.

## 🚀 Essential Commands

### Start Development
```bash
npm run dev                 # Start full Docker development environment
npm run dev:traefik         # Start with Traefik (access via radio.local)
```

### Monitor & Debug
```bash
npm run dev:status          # Check service status
npm run dev:logs            # View all service logs
npm run dev:logs radio-app  # View frontend logs only
npm run dev:logs radio-backend # View backend logs only
```

### Control Services
```bash
npm run dev:stop            # Stop all services
npm run dev:restart         # Restart all services
npm run dev:rebuild         # Rebuild Docker images
```

### Development Shell Access
```bash
npm run dev:shell radio-app      # Open shell in frontend container
npm run dev:shell radio-backend  # Open shell in backend container
```

### Cleanup
```bash
npm run dev:clean           # Clean up Docker resources
```

## 🌐 Access Points

| Service | Local Access | With Traefik |
|---------|-------------|--------------|
| **Frontend** | http://localhost:3000 | http://radio.local |
| **Backend API** | http://localhost:8000 | http://radio.local/api |
| **API Docs** | http://localhost:8000/docs | http://radio.local/api/docs |
| **Traefik Dashboard** | - | http://localhost:8080 |

## ⚡ Quick Validation (No Docker)

```bash
npm run quick:check         # Lint + Type check
npm run quick:fix          # Auto-fix linting issues
npm run lint               # ESLint only
npm run type-check         # TypeScript only
```

## 🔄 Typical Development Session

```bash
# 1. Start development environment
npm run dev

# 2. Check everything is running
npm run dev:status

# 3. Make code changes...

# 4. View logs if needed
npm run dev:logs

# 5. If you need to rebuild after major changes
npm run dev:rebuild

# 6. Stop when done
npm run dev:stop
```

## 🏗️ Direct Docker Commands (Advanced)

If you need more control, you can use Docker Compose directly:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild specific service
docker-compose build radio-app
docker-compose up -d radio-app
```

## 🔧 Troubleshooting

### Services Won't Start
```bash
npm run dev:clean          # Clean up resources
npm run dev:rebuild        # Rebuild images
npm run dev                # Try again
```

### Port Already in Use
```bash
# Check what's using the ports
lsof -i :3000              # Frontend
lsof -i :8000              # Backend

# Or stop all Docker containers
docker stop $(docker ps -q)
```

### Container Issues
```bash
# Remove all containers and start fresh
npm run dev:clean
npm run dev:rebuild
```

### Access Issues
```bash
# Check Docker network
docker network ls
docker network inspect radio001_radio-network

# Check container connectivity
npm run dev:shell radio-app
curl http://radio-backend:8000/health
```

## 📱 Pi-like Development

For the most Pi-like experience:

```bash
# Start with Traefik
npm run dev:traefik

# Access via:
# - http://radio.local (like on actual Pi)
# - Captive portal simulation
# - mDNS resolution testing
```

## 💡 Pro Tips

1. **Always use Docker** - it mirrors the Pi environment exactly
2. **Use radio.local** - start with `npm run dev:traefik` for realistic testing
3. **Check logs regularly** - `npm run dev:logs` shows real-time output
4. **Shell access** - use `npm run dev:shell` for debugging inside containers
5. **Clean rebuilds** - use `npm run dev:rebuild` after major changes

## 🎯 Quick Health Check

```bash
# Check if everything is working
curl http://localhost:3000/api/health  # Frontend health
curl http://localhost:8000/health      # Backend health

# Or visit in browser:
# http://localhost:3000 (main app)
# http://localhost:8000/docs (API documentation)
```

This setup ensures your development environment matches the production Raspberry Pi environment as closely as possible!