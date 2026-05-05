## ADDED Requirements

### Requirement: System Configuration Management

The system must provide a unified configuration file that controls all aspects of WiFi, radio, and system behavior with clear documentation and validation.

#### Scenario: Configuration File Setup

- **WHEN** a user first sets up the system
- **THEN** they can copy `config/radio.conf.example` to `config/radio.conf`
- **AND** the example file contains all available configuration options with documentation
- **AND** the system uses sensible defaults for any missing configuration values

#### Scenario: Hotspot Configuration

- **WHEN** a user customizes hotspot settings in `config/radio.conf`
- **THEN** they can set HOTSPOT_SSID, HOTSPOT_PASSWORD, and HOTSPOT_IP
- **AND** the system validates these settings before applying them
- **AND** changes take effect after container restart

#### Scenario: mDNS Hostname Configuration

- **WHEN** a user sets MDNS_HOSTNAME in the configuration file
- **THEN** the system becomes accessible at `http://{hostname}.local`
- **AND** the hostname is used consistently across all services
- **AND** the system handles hostname conflicts gracefully

#### Scenario: WiFi Timeout Configuration

- **WHEN** a user configures WIFI_BOOT_TIMEOUT and WIFI_CONNECT_TIMEOUT
- **THEN** the boot script waits the specified time before falling back to hotspot
- **AND** manual connection attempts respect the connection timeout
- **AND** timeout values are validated to be reasonable (1-300 seconds)

#### Scenario: Radio Station Configuration

- **WHEN** a user configures DEFAULT_VOLUME and STATION_SLOTS in the config file
- **THEN** the radio system initializes with these defaults
- **AND** volume levels are constrained to safe ranges (30-100%)
- **AND** station slots are properly initialized as empty or with default streams

#### Scenario: Configuration Validation

- **WHEN** the system starts with an invalid configuration file
- **THEN** it logs specific validation errors for each invalid setting
- **AND** it falls back to safe defaults for invalid values
- **AND** it continues to operate with valid settings while noting problems

#### Scenario: Configuration Updates

- **WHEN** a user modifies the configuration file
- **THEN** the system can reload configuration without full restart (where possible)
- **AND** critical changes that require restart are clearly documented
- **AND** the system provides feedback about which changes took effect

#### Scenario: Environment Variable Override

- **WHEN** environment variables are set that match configuration keys
- **THEN** environment variables take precedence over config file values
- **AND** this allows for Docker deployment flexibility
- **AND** the precedence order is clearly documented (ENV > config file > defaults)