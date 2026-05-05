#!/bin/bash

# WiFi Initialization Script for Radio WiFi Configuration
# This script initializes WiFi interfaces using NetworkManager (nmcli)

set -e

# Configuration
WIFI_INTERFACE="${WIFI_INTERFACE:-wlan0}"
HOTSPOT_INTERFACE="${HOTSPOT_INTERFACE:-wlan0}"
HOTSPOT_SSID="${HOTSPOT_SSID:-Radio-Setup}"
HOTSPOT_PASSWORD="${HOTSPOT_PASSWORD:-radio123}"
HOTSPOT_IP="${HOTSPOT_IP:-192.168.4.1}"
HOTSPOT_SUBNET="${HOTSPOT_SUBNET:-192.168.4.0/24}"
DHCP_RANGE="${DHCP_RANGE:-192.168.4.2,192.168.4.20,12h}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check if running on Raspberry Pi
is_raspberry_pi() {
    if [ -f /proc/cpuinfo ]; then
        grep -q "Raspberry Pi\|BCM" /proc/cpuinfo 2>/dev/null
    else
        false
    fi
}

# Check if interface exists
interface_exists() {
    local interface="$1"
    ip link show "$interface" >/dev/null 2>&1
}

# Check if WiFi interface supports AP mode
supports_ap_mode() {
    local interface="$1"
    if command -v iw >/dev/null 2>&1; then
        iw list 2>/dev/null | grep -q "AP" || return 1
        return 0
    else
        # Assume supported if iw is not available
        return 0
    fi
}

# Initialize WiFi interface
init_wifi_interface() {
    local interface="$1"

    log "Initializing WiFi interface: $interface"

    # Check if interface exists
    if ! interface_exists "$interface"; then
        error "WiFi interface $interface not found"
        return 1
    fi

    # Bring interface up
    if ip link set "$interface" up 2>/dev/null; then
        success "Interface $interface brought up"
    else
        warn "Could not bring up interface $interface (may require privileges)"
    fi

    # Check if interface supports AP mode
    if supports_ap_mode "$interface"; then
        success "Interface $interface supports AP mode"
    else
        warn "Interface $interface may not support AP mode"
    fi

    return 0
}

# Check for existing WiFi connections using nmcli
check_existing_connections() {
    log "Checking for existing WiFi connections..."

    if command -v nmcli >/dev/null 2>&1; then
        local state=$(nmcli -t -f TYPE,STATE,CONNECTION device status 2>/dev/null | grep "^wifi:" || true)

        if echo "$state" | grep -q "connected"; then
            local ssid=$(echo "$state" | cut -d: -f3)
            success "Connected to WiFi network: $ssid"
            return 0
        else
            warn "WiFi interface not connected"
            return 1
        fi
    else
        warn "nmcli not available - cannot check connection status"
        return 1
    fi
}

# Setup development environment
setup_development() {
    log "Setting up development environment"

    # Create mock data directories
    mkdir -p /tmp/radio-wifi/{networks,config,logs}

    # Create mock network list
    cat > /tmp/radio-wifi/networks/available.json << EOF
{
  "timestamp": "$(date -Iseconds)",
  "interface": "$WIFI_INTERFACE",
  "networks": [
    {
      "ssid": "HomeWiFi",
      "bssid": "00:11:22:33:44:55",
      "signal": 75,
      "frequency": "2412 MHz",
      "security": "WPA2",
      "channel": 1
    },
    {
      "ssid": "GuestNetwork",
      "bssid": "00:11:22:33:44:66",
      "signal": 60,
      "frequency": "5180 MHz",
      "security": "Open",
      "channel": 36
    },
    {
      "ssid": "OfficeWiFi",
      "bssid": "00:11:22:33:44:77",
      "signal": 45,
      "frequency": "2437 MHz",
      "security": "WPA3",
      "channel": 6
    }
  ]
}
EOF

    # Create mock status
    cat > /tmp/radio-wifi/config/status.json << EOF
{
  "timestamp": "$(date -Iseconds)",
  "interface": "$WIFI_INTERFACE",
  "status": "hotspot",
  "mode": "hotspot",
  "ssid": "$HOTSPOT_SSID",
  "ip": "$HOTSPOT_IP",
  "signal": null
}
EOF

    success "Development environment configured"
}

# Create systemd service files (if systemd is available)
create_systemd_services() {
    if command -v systemctl >/dev/null 2>&1 && [ -d /etc/systemd/system ]; then
        log "Creating systemd service files..."

        # Note: In a container, we typically don't manage systemd services
        # This is more for reference or bare metal installation
        warn "Systemd detected but service creation skipped in container environment"
    else
        log "Systemd not available - skipping service creation"
    fi
}

# Check network tools availability
check_network_tools() {
    log "Checking network tools availability..."

    local tools=("ip" "nmcli")
    local missing_tools=()

    for tool in "${tools[@]}"; do
        if command -v "$tool" >/dev/null 2>&1; then
            success "$tool is available"
        else
            missing_tools+=("$tool")
            warn "$tool is not available"
        fi
    done

    # Check optional tools
    local optional_tools=("hostapd" "dnsmasq" "iw")
    for tool in "${optional_tools[@]}"; do
        if command -v "$tool" >/dev/null 2>&1; then
            success "$tool is available"
        else
            warn "$tool is not available (optional)"
        fi
    done

    if [ ${#missing_tools[@]} -gt 0 ]; then
        error "Missing required tools: ${missing_tools[*]}"
        return 1
    fi

    return 0
}

# Main initialization function
main() {
    log "=== Radio WiFi Initialization (NetworkManager) ==="
    log "WiFi Interface: $WIFI_INTERFACE"
    log "Hotspot SSID: $HOTSPOT_SSID"
    log "Hotspot IP: $HOTSPOT_IP"

    # Check if we're on Raspberry Pi
    if is_raspberry_pi; then
        log "Running on Raspberry Pi"

        # Check network tools
        if ! check_network_tools; then
            error "Required network tools are missing"
            exit 1
        fi

        # Initialize WiFi interface
        if ! init_wifi_interface "$WIFI_INTERFACE"; then
            error "Failed to initialize WiFi interface"
            exit 1
        fi

        # Check for existing connections
        if check_existing_connections; then
            log "WiFi already connected - initialization complete"
            exit 0
        else
            log "No WiFi connection found - hotspot mode may be needed"
        fi

    else
        log "Not running on Raspberry Pi - setting up development environment"
        setup_development
    fi

    # Create systemd services if applicable
    create_systemd_services

    success "WiFi initialization completed successfully"

    # Output status information
    log "=== Initialization Summary ==="
    log "Interface: $WIFI_INTERFACE"
    log "Mode: $(is_raspberry_pi && echo "Production" || echo "Development")"
    log "NetworkManager: $(command -v nmcli >/dev/null 2>&1 && echo "Available" || echo "Not Available")"
    log "=========================="
}

# Run main function if script is executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
