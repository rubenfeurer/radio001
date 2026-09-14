#!/usr/bin/env bash
# install.sh — One-command Radio Pi installer.
#
# Usage (on the Pi, as root):
#   curl -fsSL https://raw.githubusercontent.com/rubenfeurer/radio001/main/scripts/install.sh | sudo bash
#
# Idempotent: re-running preserves existing radio.conf (including the
# generated hotspot password) and station data.

set -euo pipefail

INSTALL_DIR="/opt/radio"
CONFIG_DIR="${INSTALL_DIR}/config"
DATA_DIR="${INSTALL_DIR}/data"
COMPOSE_FILE="${INSTALL_DIR}/docker-compose.yml"
CONF_FILE="${CONFIG_DIR}/radio.conf"
SERVICE_FILE="/etc/systemd/system/radio.service"
IMAGE="ghcr.io/rubenfeurer/radio001:stable"
REPO_RAW="https://raw.githubusercontent.com/rubenfeurer/radio001/main"

CURRENT_STEP="starting"
trap 'echo ""; echo "ERROR: install failed during: ${CURRENT_STEP}" >&2; echo "Re-running this script is safe — it is idempotent and will not overwrite radio.conf or station data." >&2' ERR

# ── Prerequisites ────────────────────────────────────────────────────────────

CURRENT_STEP="prerequisite checks"

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: Run as root:  sudo bash scripts/install.sh" >&2
    exit 1
fi

if ! command -v curl &>/dev/null; then
    echo "ERROR: 'curl' is required but not installed." >&2
    exit 1
fi

if ! command -v docker &>/dev/null; then
    CURRENT_STEP="Docker installation"
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

CURRENT_STEP="creating directories"
echo "Creating directories..."
mkdir -p "${CONFIG_DIR}" "${DATA_DIR}" /etc/raspiwifi
chmod 755 "${DATA_DIR}"

# ── docker-compose.yml ───────────────────────────────────────────────────────
# Downloaded from the repo — docker/compose.prod.yml is the single source of
# truth (an embedded copy here drifted from it in the past). Atomic: a failed
# download leaves any existing compose file untouched.

CURRENT_STEP="downloading docker-compose.yml"
echo "Downloading ${COMPOSE_FILE} from ${REPO_RAW}/docker/compose.prod.yml..."
COMPOSE_TMP=$(mktemp)
curl -fsSL "${REPO_RAW}/docker/compose.prod.yml" -o "${COMPOSE_TMP}"
if [[ ! -s "${COMPOSE_TMP}" ]]; then
    echo "ERROR: downloaded compose file is empty." >&2
    rm -f "${COMPOSE_TMP}"
    exit 1
fi
if ! docker compose -f "${COMPOSE_TMP}" config -q; then
    echo "ERROR: downloaded compose file failed validation." >&2
    rm -f "${COMPOSE_TMP}"
    exit 1
fi
mv "${COMPOSE_TMP}" "${COMPOSE_FILE}"
chmod 644 "${COMPOSE_FILE}"

# ── radio.conf (idempotent — skip if already exists) ─────────────────────────

if [[ -f "${CONF_FILE}" ]]; then
    echo "Skipping ${CONF_FILE} (already exists, preserving user config)."
    HOTSPOT_PASSWORD=$(grep -E '^HOTSPOT_PASSWORD=' "${CONF_FILE}" | cut -d= -f2- || echo "(see ${CONF_FILE})")
else
    CURRENT_STEP="writing radio.conf"
    echo "Writing default ${CONF_FILE}..."
    # Per-device random hotspot password (12 alphanumerics ≥ WPA2 minimum);
    # a fixed published default would let anyone join the setup hotspot
    HOTSPOT_PASSWORD=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 12)
    CONF_TMP=$(mktemp)
    cat > "${CONF_TMP}" <<CONF_EOF
# Radio Pi configuration
# Edit this file to customise your radio. Changes take effect on next restart.

HOTSPOT_SSID=Radio-Setup
HOTSPOT_PASSWORD=${HOTSPOT_PASSWORD}
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
    chmod 600 "${CONF_TMP}"
    mv "${CONF_TMP}" "${CONF_FILE}"
fi

# ── systemd service ───────────────────────────────────────────────────────────
# Type=oneshot + RemainAfterExit runs `docker compose up -d` once; the actual
# container is supervised by dockerd (restart: unless-stopped), so no
# Restart= here (invalid for oneshot on current systemd anyway).

CURRENT_STEP="writing radio.service"
echo "Writing ${SERVICE_FILE}..."
SERVICE_TMP=$(mktemp)
cat > "${SERVICE_TMP}" <<'SERVICE_EOF'
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
User=root
Environment=COMPOSE_PROJECT_NAME=radio-wifi
Environment=NODE_ENV=production
StandardOutput=journal
StandardError=journal
SyslogIdentifier=radio-wifi

[Install]
WantedBy=multi-user.target
SERVICE_EOF
chmod 644 "${SERVICE_TMP}"
mv "${SERVICE_TMP}" "${SERVICE_FILE}"

# ── PipeWire prerequisites ────────────────────────────────────────────────────
# The radio container routes audio through the host PipeWire session.
# Ensure pipewire and pipewire-pulse are installed and the user service is running.

CURRENT_STEP="PipeWire setup"
echo "Checking PipeWire prerequisites..."
if ! command -v pipewire &>/dev/null; then
    echo "Installing pipewire and pipewire-pulse..."
    apt-get update -qq && apt-get install -y --no-install-recommends pipewire pipewire-pulse wireplumber
fi

if [[ -n "${SUDO_USER:-}" ]]; then
    INSTALL_USER="${SUDO_USER}"
    USER_UID=$(id -u "${SUDO_USER}")
else
    INSTALL_USER="$(whoami)"
    USER_UID=$(id -u)
fi

# Enable PipeWire user services
echo "Enabling PipeWire user services for ${INSTALL_USER}..."
systemctl --user -M "${INSTALL_USER}@" enable --now pipewire.service pipewire-pulse.service 2>/dev/null || \
    loginctl enable-linger "${INSTALL_USER}" 2>/dev/null || true

# Wait for PipeWire socket to appear (up to 15 seconds)
PULSE_SOCKET="/run/user/${USER_UID}/pulse/native"
echo "Waiting for PipeWire socket at ${PULSE_SOCKET}..."
for i in $(seq 1 15); do
    if [[ -S "${PULSE_SOCKET}" ]]; then
        echo "PipeWire socket ready."
        break
    fi
    sleep 1
done
if [[ ! -S "${PULSE_SOCKET}" ]]; then
    echo "WARNING: PipeWire socket not found at ${PULSE_SOCKET}."
    echo "         The radio will fall back to direct ALSA audio."
    echo "         To fix: log in as ${INSTALL_USER} and run: systemctl --user start pipewire pipewire-pulse"
fi

# ── Pull image and fix data ownership ────────────────────────────────────────

CURRENT_STEP="pulling image"
echo "Pulling latest image (${IMAGE})..."
docker compose -f "${COMPOSE_FILE}" pull

# The container app user (not root, not world) owns the data dir — resolve
# its UID/GID from the image rather than hard-coding it
CURRENT_STEP="setting data dir ownership"
RADIO_UID=$(docker run --rm --entrypoint "" "${IMAGE}" id -u radio 2>/dev/null || echo "")
RADIO_GID=$(docker run --rm --entrypoint "" "${IMAGE}" id -g radio 2>/dev/null || echo "")
if [[ -n "${RADIO_UID}" && -n "${RADIO_GID}" ]]; then
    echo "Setting ${DATA_DIR} ownership to container user ${RADIO_UID}:${RADIO_GID}..."
    chown -R "${RADIO_UID}:${RADIO_GID}" "${DATA_DIR}" "${CONFIG_DIR}"
    chmod 755 "${DATA_DIR}"
else
    echo "WARNING: could not resolve container user — leaving ${DATA_DIR} root-owned (755)."
fi

# ── Enable and start systemd service ─────────────────────────────────────────

CURRENT_STEP="enabling radio.service"
echo "Enabling radio.service..."
systemctl daemon-reload
systemctl enable --now radio.service

# ── Done ──────────────────────────────────────────────────────────────────────

PI_IP=$(hostname -I | awk '{print $1}')
echo ""
echo "Installation complete!"
echo "  Radio UI:         http://${PI_IP}:8000  (or http://radio.local:8000 on the LAN)"
echo "  Config:           ${CONF_FILE}"
echo "  Hotspot (setup):  SSID 'Radio-Setup', password: ${HOTSPOT_PASSWORD}"
echo "                    When in hotspot mode, the UI is at http://192.168.4.1:8000"
echo ""
echo "Service status:"
systemctl status radio.service --no-pager || true
