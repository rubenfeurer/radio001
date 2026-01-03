# FastAPI Backend Dockerfile for Radio WiFi Configuration
# Optimized for both development and production use

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies (including sudo and wpa_cli for WiFi management)
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    net-tools \
    iputils-ping \
    wireless-tools \
    iw \
    wpasupplicant \
    hostapd \
    dnsmasq \
    sudo \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app directory
WORKDIR /app

# Create non-root user and add to netdev group for wpa_cli access
# Use GID 104 to match host's netdev group (standard on Raspberry Pi OS)
RUN groupmod -g 104 netdev || groupadd -g 104 netdev && \
    groupadd -r radio && \
    useradd -r -g radio -G netdev radio

# Configure passwordless sudo for WiFi management commands (RaspiWiFi-style permissions)
RUN echo "radio ALL=(ALL) NOPASSWD: /bin/mv, /usr/bin/mv, /bin/cp, /usr/bin/cp, /bin/rm, /usr/bin/rm, /bin/chmod, /usr/bin/chmod, /sbin/reboot, /usr/sbin/reboot, /sbin/shutdown, /usr/sbin/shutdown, /sbin/iwlist, /usr/sbin/iwlist" > /etc/sudoers.d/radio && \
    chmod 0440 /etc/sudoers.d/radio

# Copy requirements and install Python dependencies
COPY backend/requirements.txt backend/requirements-test.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install test dependencies for development/CI environments
ARG INSTALL_TEST_DEPS=false
RUN if [ "$INSTALL_TEST_DEPS" = "true" ]; then \
        pip install --no-cache-dir -r requirements-test.txt; \
    fi

# Copy boot check script and configuration templates (from project root)
COPY --chmod=755 scripts/boot-wifi-check.sh /usr/local/bin/boot-wifi-check.sh
COPY config/hostapd/hostapd.conf.template /etc/hostapd/hostapd.conf.template
COPY config/dnsmasq/dnsmasq.conf.template /etc/dnsmasq.conf.template

# Copy application code
COPY backend/ .

# Create necessary directories for testing
RUN mkdir -p /app/data /app/sounds /app/logs /app/htmlcov

# Change ownership to radio user
RUN chown -R radio:radio /app

# Switch to non-root user
USER radio

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set environment variables
ENV API_PORT=8000 \
    NODE_ENV=production \
    MOCK_HARDWARE=false \
    PYTHONPATH=/app

# Start the FastAPI application
CMD ["python", "main.py"]
