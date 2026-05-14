#!/usr/bin/env bash
# install.sh — One-command Radio Pi installer.
#
# Usage (on the Pi, as root):
#   curl -fsSL https://raw.githubusercontent.com/rubenfeurer/radio001/main/scripts/install.sh | sudo bash
#
# Idempotent: re-running preserves existing radio.conf and station data.

set -euo pipefail

INSTALL_DIR="/opt/radio"
CONFIG_DIR="${INSTALL_DIR}/config"
DATA_DIR="${INSTALL_DIR}/data"
COMPOSE_FILE="${INSTALL_DIR}/docker-compose.yml"
CONF_FILE="${CONFIG_DIR}/radio.conf"
SERVICE_FILE="/etc/systemd/system/radio.service"
IMAGE="ghcr.io/rubenfeurer/radio001:latest"

# ── Prerequisites ────────────────────────────────────────────────────────────

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: Run as root:  sudo bash scripts/install.sh" >&2
    exit 1
fi

if ! command -v curl &>/dev/null; then
    echo "ERROR: 'curl' is required but not installed." >&2
    exit 1
fi

if ! command -v docker &>/dev/null; then
    echo "Docker not found — installing Docker..."
    curl -fsSL https://get.docker.com | sh
    if [[ -n "${SUDO_USER:-}" ]]; then
        usermod -aG docker "$SUDO_USER"
    fi
fi

if ! docker compose version &>/dev/null; then
    echo "ERROR: 'docker compose' plugin not available after install." >&2
    exit 1
fi

# ── Directory layout ─────────────────────────────────────────────────────────

echo "Creating directories..."
mkdir -p "${CONFIG_DIR}" "${DATA_DIR}" /etc/raspiwifi
chmod 777 "${DATA_DIR}"

# ── docker-compose.yml ───────────────────────────────────────────────────────
# Always written (it is version-controlled, not user-edited).

echo "Writing ${COMPOSE_FILE}..."
cat > "${COMPOSE_FILE}" <<'COMPOSE_EOF'
# Managed by install.sh — do not edit manually.
services:
  radio-backend:
    image: ghcr.io/rubenfeurer/radio001:latest
    container_name: radio-backend-prod
    network_mode: host
    volumes:
      - /opt/radio/config:/app/config:ro
      - /opt/radio/data:/app/data
      - /etc/raspiwifi:/etc/raspiwifi:rw
      - /dev:/dev:rw
      - /sys/class/net:/sys/class/net:ro
      - /run/dbus:/run/dbus:ro
    environment:
      - NODE_ENV=production
      - API_PORT=8000
      - HOSTNAME=radio
      - WIFI_TIMEOUT=5
      - WIFI_CHECK_ENABLED=true
      - HOST_MODE_FILE=/etc/raspiwifi/host_mode
    restart: unless-stopped
    privileged: true
    cap_add:
      - NET_ADMIN
      - NET_RAW
    devices:
      - /dev/net/tun
      - /dev/gpiochip0
      - /dev/snd
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  watchtower:
    image: containrrr/watchtower:1.7.1
    container_name: radio-watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_SCHEDULE=0 0 3 * * *
      - DOCKER_API_VERSION=1.40
    restart: unless-stopped
COMPOSE_EOF

# ── radio.conf (idempotent — skip if already exists) ─────────────────────────

if [[ -f "${CONF_FILE}" ]]; then
    echo "Skipping ${CONF_FILE} (already exists, preserving user config)."
else
    echo "Writing default ${CONF_FILE}..."
    cat > "${CONF_FILE}" <<'CONF_EOF'
# Radio Pi configuration
# Edit this file to customise your radio. Changes take effect on next restart.

HOTSPOT_SSID=Radio-Setup
HOTSPOT_PASSWORD=radio123
HOTSPOT_IP=192.168.4.1
WIFI_INTERFACE=wlan0

DEFAULT_VOLUME=50
MIN_VOLUME=30
MAX_VOLUME=100

DEFAULT_STATION_1_NAME=SRF 3
DEFAULT_STATION_1_URL=https://stream.srg-ssr.ch/m/srf3/mp3_128
DEFAULT_STATION_2_NAME=Radio Swiss Jazz
DEFAULT_STATION_2_URL=https://stream.srg-ssr.ch/m/rsj/mp3_128
DEFAULT_STATION_3_NAME=Radio Swiss Classic
DEFAULT_STATION_3_URL=https://stream.srg-ssr.ch/m/rsc_de/mp3_128
CONF_EOF
fi

# ── systemd service ───────────────────────────────────────────────────────────

echo "Writing ${SERVICE_FILE}..."
cat > "${SERVICE_FILE}" <<'SERVICE_EOF'
[Unit]
Description=Radio WiFi Configuration Service
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/radio
ExecStart=/usr/bin/docker compose -f /opt/radio/docker-compose.yml up -d
ExecStop=/usr/bin/docker compose -f /opt/radio/docker-compose.yml down
ExecReload=/usr/bin/docker compose -f /opt/radio/docker-compose.yml restart
Restart=on-failure
RestartSec=10s
StartLimitIntervalSec=300
StartLimitBurst=3
User=root
Environment=COMPOSE_PROJECT_NAME=radio-wifi
Environment=NODE_ENV=production
StandardOutput=journal
StandardError=journal
SyslogIdentifier=radio-wifi

[Install]
WantedBy=multi-user.target
SERVICE_EOF

chmod 644 "${SERVICE_FILE}"

# ── Pull image and start ──────────────────────────────────────────────────────

echo "Pulling latest image (${IMAGE})..."
docker compose -f "${COMPOSE_FILE}" pull

# ── Enable and start systemd service ─────────────────────────────────────────

echo "Enabling radio.service..."
systemctl daemon-reload
systemctl enable --now radio.service

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
echo "Installation complete!"
echo "  Radio UI:     http://radio.local  (or http://$(hostname -I | awk '{print $1}'))"
echo "  API:          http://radio.local:8000"
echo "  Config:       ${CONF_FILE}"
echo ""
echo "Service status:"
systemctl status radio.service --no-pager || true
