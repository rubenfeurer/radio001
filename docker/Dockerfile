# Multi-stage Dockerfile for Radio WiFi Configuration
# Supports both FastAPI backend and Nuxt 3 frontend

# =============================================================================
# Base Python stage for FastAPI backend
# =============================================================================
FROM python:3.11-alpine AS python-base

# Install system dependencies for WiFi management
RUN apk add --no-cache \
    wireless-tools \
    wpa_supplicant \
    hostapd \
    dnsmasq \
    iw \
    sudo \
    bash \
    curl

# Create app user with sudo privileges for network management
RUN addgroup -g 1001 -S radio && \
    adduser -S radio -u 1001 -G radio && \
    echo 'radio ALL=(ALL) NOPASSWD: /sbin/*, /usr/sbin/*, /bin/systemctl, /usr/bin/reboot' > /etc/sudoers.d/radio

WORKDIR /app

# =============================================================================
# Node.js base stage for Nuxt frontend
# =============================================================================
FROM node:20 AS node-base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    dumb-init \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -g 1001 radio && \
    useradd -u 1001 -g radio -s /bin/bash radio

WORKDIR /app

# =============================================================================
# Backend dependencies stage
# =============================================================================
FROM python-base AS backend-deps

# Copy backend requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# =============================================================================
# Frontend dependencies stage
# =============================================================================
FROM node-base AS frontend-deps

# Copy frontend package files
COPY app/package*.json ./app/

# Install frontend dependencies for ARM64
RUN cd app && \
    npm config set fund false && \
    npm config set audit false && \
    npm ci --only=production --no-optional && \
    npm cache clean --force

# =============================================================================
# Frontend build stage
# =============================================================================
FROM frontend-deps AS frontend-build

# Set environment variables for ARM64 compatibility
ENV SKIP_NUXT_PREPARE=true \
    NITRO_PRESET=node-server \
    NODE_ENV=production

# Copy frontend source
COPY app/ ./app/
COPY config/ ./config/

# Build the Nuxt application (skip oxc-parser problematic steps)
RUN cd app && \
    echo "🔧 Building Nuxt app for ARM64..." && \
    npm run build

# =============================================================================
# Production stage - Combined backend and frontend
# =============================================================================
FROM python-base AS production

# Install Python dependencies
COPY --from=backend-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-deps /usr/local/bin /usr/local/bin

# Install Node.js for Nuxt runtime
RUN apk add --no-cache nodejs npm

# Set environment variables
ENV NODE_ENV=production \
    PYTHONPATH=/app \
    API_PORT=8000 \
    NUXT_PORT=3000 \
    HOSTNAME=radio

# Copy application files
COPY --chown=radio:radio backend/ ./backend/
COPY --from=frontend-build --chown=radio:radio /app/app/.output ./frontend/
COPY --chown=radio:radio config/ ./config/
COPY --chown=radio:radio scripts/ ./scripts/

# Copy entrypoint script
COPY --chown=radio:radio docker/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh ./scripts/*.sh

# Create necessary directories
RUN mkdir -p /var/lib/dhcp \
    /var/run/avahi-daemon \
    /etc/avahi/services \
    /etc/raspiwifi \
    /app/logs \
    /app/data && \
    chown -R radio:radio \
        /var/lib/dhcp \
        /var/run/avahi-daemon \
        /etc/avahi/services \
        /etc/raspiwifi \
        /app/logs \
        /app/data

# Create simple startup script for ARM64
RUN cat > /app/start.sh << 'EOF' && chmod +x /app/start.sh
#!/bin/bash
set -e

echo "🚀 Starting Radio WiFi Configuration..."

# Start FastAPI backend in background
echo "🔧 Starting FastAPI backend..."
cd /app/backend
python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start Nuxt frontend
echo "🌐 Starting Nuxt frontend..."
cd /app/frontend
node server/index.mjs &
FRONTEND_PID=$!

# Wait for either process to exit
wait $BACKEND_PID $FRONTEND_PID
EOF

# Expose ports
EXPOSE 3000 8000 53/udp 67/udp 5353/udp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000/api/health && curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER radio

# Use dumb-init for signal handling
ENTRYPOINT ["dumb-init", "--"]

# Start both services
CMD ["./entrypoint.sh"]
