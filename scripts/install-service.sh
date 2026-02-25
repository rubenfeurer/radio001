#!/usr/bin/env bash
# install-service.sh — Install and enable the radio-wifi systemd service on Raspberry Pi.
# Run once as root: sudo bash scripts/install-service.sh

set -euo pipefail

SERVICE_NAME="radio-wifi.service"
SERVICE_SRC="$(dirname "$(realpath "$0")")/../config/systemd/${SERVICE_NAME}"
SERVICE_DST="/etc/systemd/system/${SERVICE_NAME}"

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run as root (sudo)." >&2
    exit 1
fi

if [[ ! -f "$SERVICE_SRC" ]]; then
    echo "ERROR: Service file not found: $SERVICE_SRC" >&2
    exit 1
fi

echo "Copying $SERVICE_NAME to $SERVICE_DST"
cp "$SERVICE_SRC" "$SERVICE_DST"
chmod 644 "$SERVICE_DST"

echo "Reloading systemd daemon"
systemctl daemon-reload

echo "Enabling $SERVICE_NAME (auto-start on boot)"
systemctl enable "$SERVICE_NAME"

echo "Starting $SERVICE_NAME"
systemctl start "$SERVICE_NAME"

echo ""
echo "Done. Service status:"
systemctl status "$SERVICE_NAME" --no-pager || true
