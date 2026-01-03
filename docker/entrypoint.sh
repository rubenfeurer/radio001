#!/bin/bash
set -e

# Container entrypoint script for Radio WiFi Configuration
# Handles mDNS setup, WiFi initialization, and application startup

# Configuration
HOSTNAME=${HOSTNAME:-radio}
APP_PORT=${NUXT_PORT:-3000}
WIFI_INTERFACE=${WIFI_INTERFACE:-wlan0}
HOTSPOT_SSID=${HOTSPOT_SSID:-Radio-Setup}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Function to check if running on Raspberry Pi
is_raspberry_pi() {
    if [ -f /proc/cpuinfo ]; then
        grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null || \
        grep -q "BCM" /proc/cpuinfo 2>/dev/null
    else
        false
    fi
}

# Function to setup hostname
setup_hostname() {
    log "Setting up hostname: $HOSTNAME"

    # Set hostname in container
    if [ -w /etc/hostname ]; then
        echo "$HOSTNAME" > /etc/hostname
        success "Hostname set to $HOSTNAME"
    else
        warn "Cannot write to /etc/hostname - running in restricted mode"
    fi
}

# Function to setup mDNS (Avahi)
setup_mdns() {
    log "Setting up mDNS (Avahi) for $HOSTNAME.local"

    # Only setup mDNS if we have the necessary tools and permissions
    if command -v avahi-daemon >/dev/null 2>&1; then
        # Create Avahi configuration
        mkdir -p /etc/avahi

        # Avahi daemon configuration
        cat > /etc/avahi/avahi-daemon.conf << EOF
[server]
host-name=$HOSTNAME
domain-name=local
use-ipv4=yes
use-ipv6=no
ratelimit-interval-usec=1000000
ratelimit-burst=1000

[wide-area]
enable-wide-area=yes

[publish]
publish-addresses=yes
publish-hinfo=yes
publish-workstation=yes
publish-domain=yes

[reflector]
enable-reflector=no

[rlimits]
rlimit-core=0
rlimit-data=4194304
rlimit-fsize=0
rlimit-nofile=768
rlimit-stack=4194304
rlimit-nproc=3
EOF

        # HTTP service advertisement
        mkdir -p /etc/avahi/services
        cat > /etc/avahi/services/http.service << EOF
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name replace-wildcards="yes">Radio WiFi Config on %h</name>
  <service>
    <type>_http._tcp</type>
    <port>$APP_PORT</port>
    <txt-record>path=/</txt-record>
  </service>
</service-group>
EOF

        success "mDNS configuration created"

        # Start Avahi daemon if we have permissions
        if [ -w /var/run ]; then
            mkdir -p /var/run/avahi-daemon
            # Note: In production, Avahi should be started by the system init
            log "mDNS service configured - daemon will be started by system"
        fi
    else
        warn "Avahi not available - mDNS will not be configured"
    fi
}

# Function to check WiFi interface
check_wifi_interface() {
    log "Checking WiFi interface: $WIFI_INTERFACE"

    if is_raspberry_pi; then
        if command -v iwconfig >/dev/null 2>&1; then
            if iwconfig "$WIFI_INTERFACE" >/dev/null 2>&1; then
                success "WiFi interface $WIFI_INTERFACE found"
                return 0
            else
                warn "WiFi interface $WIFI_INTERFACE not found"
                return 1
            fi
        else
            warn "wireless-tools not available"
            return 1
        fi
    else
        log "Not running on Raspberry Pi - WiFi interface check skipped"
        return 0
    fi
}

# Function to setup development environment
setup_development() {
    log "Setting up development environment"

    # Create mock WiFi data for development
    mkdir -p /tmp/radio-wifi
    cat > /tmp/radio-wifi/networks.json << EOF
{
  "networks": [
    {
      "ssid": "HomeWiFi",
      "signal": -45,
      "security": "WPA2",
      "frequency": "2.4GHz"
    },
    {
      "ssid": "GuestNetwork",
      "signal": -60,
      "security": "Open",
      "frequency": "5GHz"
    }
  ]
}
EOF

    success "Development environment configured"
}

# Function to wait for network readiness
wait_for_network() {
    log "Waiting for network interface to be ready..."

    local timeout=30
    local count=0

    while [ $count -lt $timeout ]; do
        if ip link show | grep -q "state UP" || [ ! is_raspberry_pi ]; then
            success "Network interface ready"
            return 0
        fi

        sleep 1
        count=$((count + 1))
    done

    warn "Network interface not ready after ${timeout}s - continuing anyway"
    return 0
}

# Function to start the application
start_application() {
    log "Starting Radio WiFi Configuration application..."

    # Ensure the output directory exists
    if [ ! -d ".output" ]; then
        error "Application build not found - please run 'npm run build' first"
        exit 1
    fi

    # Set final environment variables
    export NODE_ENV=${NODE_ENV:-production}
    export NUXT_HOST=${NUXT_HOST:-0.0.0.0}
    export NUXT_PORT=${APP_PORT}
    export HOSTNAME=${HOSTNAME}

    success "Environment configured:"
    log "  - Host: $NUXT_HOST"
    log "  - Port: $NUXT_PORT"
    log "  - Hostname: $HOSTNAME"
    log "  - WiFi Interface: $WIFI_INTERFACE"

    # Start the application
    log "Executing: $@"
    exec "$@"
}

# Main execution flow
main() {
    log "=== Radio WiFi Configuration Container Starting ==="

    # Setup hostname
    setup_hostname

    # Setup mDNS
    setup_mdns

    # PRODUCTION ONLY: Run boot WiFi check
    if [ "$NODE_ENV" = "production" ]; then
        log "Running boot WiFi check..."
        if [ -x /usr/local/bin/boot-wifi-check.sh ]; then
            /usr/local/bin/boot-wifi-check.sh || warn "WiFi check failed - continuing anyway"
        else
            warn "Boot WiFi check script not found - skipping"
        fi
    fi

    # Wait for network
    wait_for_network

    # Check WiFi interface (only on Pi)
    check_wifi_interface

    # Setup development environment if needed
    if [ "$NODE_ENV" = "development" ]; then
        setup_development
    fi

    # Start the application
    start_application "$@"
}

# Handle signals for graceful shutdown
trap 'log "Received shutdown signal"; exit 0' SIGTERM SIGINT

# Run main function with all arguments
main "$@"
