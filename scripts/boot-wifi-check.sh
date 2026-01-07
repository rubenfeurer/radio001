#!/bin/bash

# Boot WiFi Check Script
# Checks WiFi connectivity on boot and switches between client/hotspot modes
# Uses NetworkManager (nmcli) instead of wpa_supplicant

set -e

# Configuration from environment variables
WIFI_INTERFACE="${WIFI_INTERFACE:-wlan0}"
WIFI_TIMEOUT="${WIFI_TIMEOUT:-5}"
HOST_MODE_FILE="${HOST_MODE_FILE:-/etc/raspiwifi/host_mode}"
HOTSPOT_SSID="${HOTSPOT_SSID:-Radio-Setup}"
HOTSPOT_PASSWORD="${HOTSPOT_PASSWORD:-Configure123!}"
HOTSPOT_IP="${HOTSPOT_IP:-192.168.4.1}"
HOTSPOT_RANGE="${HOTSPOT_RANGE:-192.168.4.2,192.168.4.20}"
HOTSPOT_ENABLE_FALLBACK="${HOTSPOT_ENABLE_FALLBACK:-true}"

# Logging function
log() {
    echo "[boot-wifi-check] $1"
}

warn() {
    echo "[boot-wifi-check] WARNING: $1" >&2
}

error() {
    echo "[boot-wifi-check] ERROR: $1" >&2
}

# Wait for WiFi interface to appear
wait_for_interface() {
    local max_wait=10
    local elapsed=0

    log "Waiting for WiFi interface $WIFI_INTERFACE..."

    while [ $elapsed -lt $max_wait ]; do
        if ip link show "$WIFI_INTERFACE" >/dev/null 2>&1; then
            log "WiFi interface $WIFI_INTERFACE found"
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done

    error "WiFi interface $WIFI_INTERFACE not found after ${max_wait}s"
    return 1
}

# Check if WiFi is connected using nmcli
check_wifi_connection() {
    if ! command -v nmcli >/dev/null 2>&1; then
        warn "nmcli not available"
        return 1
    fi

    # Check if any WiFi connection is active
    local state=$(nmcli -t -f TYPE,STATE device status 2>/dev/null | grep "^wifi:" | cut -d: -f2)

    if [ "$state" = "connected" ]; then
        log "WiFi is connected"
        return 0
    fi

    log "WiFi not connected (state: ${state:-unknown})"
    return 1
}

# Wait for WiFi connection with timeout
wait_for_wifi() {
    local elapsed=0

    log "Waiting up to ${WIFI_TIMEOUT}s for WiFi connection..."

    while [ $elapsed -lt "$WIFI_TIMEOUT" ]; do
        if check_wifi_connection; then
            log "WiFi connection established after ${elapsed}s"
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done

    log "No WiFi connection after ${WIFI_TIMEOUT}s timeout"
    return 1
}

# Generate configuration file from template
generate_config() {
    local template="$1"
    local output="$2"

    if [ ! -f "$template" ]; then
        error "Template file not found: $template"
        return 1
    fi

    log "Generating $output from template..."

    # Use envsubst to replace environment variables
    if command -v envsubst >/dev/null 2>&1; then
        envsubst < "$template" > "$output"
    else
        # Fallback: manual replacement
        sed -e "s/\${WIFI_INTERFACE}/$WIFI_INTERFACE/g" \
            -e "s/\${HOTSPOT_SSID}/$HOTSPOT_SSID/g" \
            -e "s/\${HOTSPOT_PASSWORD}/$HOTSPOT_PASSWORD/g" \
            -e "s/\${HOTSPOT_IP}/$HOTSPOT_IP/g" \
            -e "s/\${HOTSPOT_RANGE}/$HOTSPOT_RANGE/g" \
            "$template" > "$output"
    fi

    log "Generated $output"
    return 0
}

# Activate hotspot mode
activate_hotspot_mode() {
    log "========================================="
    log "Activating HOTSPOT mode"
    log "========================================="

    # Create host mode marker
    mkdir -p "$(dirname "$HOST_MODE_FILE")"
    touch "$HOST_MODE_FILE"
    log "Created host mode marker: $HOST_MODE_FILE"

    # Disconnect any active WiFi connections
    log "Disconnecting active WiFi connections..."
    nmcli device disconnect "$WIFI_INTERFACE" 2>/dev/null || true
    sleep 2

    # Configure interface with static IP
    log "Configuring $WIFI_INTERFACE with IP $HOTSPOT_IP..."
    ip addr flush dev "$WIFI_INTERFACE" 2>/dev/null || true
    ip addr add "${HOTSPOT_IP}/24" dev "$WIFI_INTERFACE"
    ip link set "$WIFI_INTERFACE" up

    # Generate hostapd configuration
    if [ -f "/etc/hostapd/hostapd.conf.template" ]; then
        generate_config "/etc/hostapd/hostapd.conf.template" "/etc/hostapd/hostapd.conf"
    else
        warn "hostapd template not found, using default configuration"
    fi

    # Generate dnsmasq configuration
    if [ -f "/etc/dnsmasq.conf.template" ]; then
        generate_config "/etc/dnsmasq.conf.template" "/etc/dnsmasq.conf"
    else
        warn "dnsmasq template not found, using default configuration"
    fi

    # Start hostapd
    log "Starting hostapd..."
    if [ -f "/etc/hostapd/hostapd.conf" ]; then
        hostapd -B /etc/hostapd/hostapd.conf 2>&1 | head -n 5
        sleep 2

        if pgrep hostapd >/dev/null; then
            log "hostapd started successfully"
        else
            error "hostapd failed to start"
        fi
    else
        error "hostapd configuration not found"
    fi

    # Start dnsmasq
    log "Starting dnsmasq..."
    if [ -f "/etc/dnsmasq.conf" ]; then
        dnsmasq -C /etc/dnsmasq.conf 2>&1 | head -n 5
        sleep 1

        if pgrep dnsmasq >/dev/null; then
            log "dnsmasq started successfully"
        else
            error "dnsmasq failed to start"
        fi
    else
        error "dnsmasq configuration not found"
    fi

    log "========================================="
    log "HOTSPOT mode active"
    log "SSID: $HOTSPOT_SSID"
    log "Password: $HOTSPOT_PASSWORD"
    log "IP: $HOTSPOT_IP"
    log "Access: http://$HOTSPOT_IP or http://radio.local"
    log "========================================="
}

# Activate client mode
activate_client_mode() {
    log "========================================="
    log "Activating CLIENT mode"
    log "========================================="

    # Remove host mode marker if it exists
    if [ -f "$HOST_MODE_FILE" ]; then
        rm -f "$HOST_MODE_FILE"
        log "Removed host mode marker: $HOST_MODE_FILE"
    fi

    # Ensure NetworkManager is managing the WiFi interface
    nmcli device set "$WIFI_INTERFACE" managed yes 2>/dev/null || true

    log "========================================="
    log "CLIENT mode active - WiFi connected"
    log "========================================="
}

# Main execution
main() {
    log "========================================="
    log "Boot WiFi Check Starting (NetworkManager)"
    log "========================================="
    log "WiFi interface: $WIFI_INTERFACE"
    log "WiFi timeout: ${WIFI_TIMEOUT}s"
    log "Hotspot fallback: $HOTSPOT_ENABLE_FALLBACK"
    log "Host mode file: $HOST_MODE_FILE"

    # Check if hotspot fallback is disabled
    if [ "$HOTSPOT_ENABLE_FALLBACK" != "true" ]; then
        log "Hotspot fallback disabled - skipping WiFi check"
        return 0
    fi

    # Wait for WiFi interface
    if ! wait_for_interface; then
        warn "WiFi interface not available - skipping WiFi check"
        return 0
    fi

    # Check if host mode marker exists
    if [ -f "$HOST_MODE_FILE" ]; then
        log "Host mode marker found - activating hotspot immediately"
        activate_hotspot_mode
        return 0
    fi

    # Wait for WiFi connection
    if wait_for_wifi; then
        activate_client_mode
        return 0
    else
        log "No WiFi connection detected - falling back to hotspot mode"
        activate_hotspot_mode
        return 0
    fi
}

# Run main function
main "$@"
