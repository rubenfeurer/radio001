## Why

CI Docker build fails because the Dockerfile references configuration template files that don't exist (`config/hostapd/hostapd.conf.template` and `config/dnsmasq/dnsmasq.conf.template`) and attempts to install packages we no longer use. Investigation revealed that our system successfully uses NetworkManager's built-in hotspot capabilities without these legacy dependencies. The current container already runs without hostapd, proving the functionality works fine.

## What Changes

- Remove obsolete configuration template file references from Dockerfile
- Remove unused hostapd package from installation
- Replace dnsmasq with dnsmasq-base (more precise, matches current reality)
- Clean up legacy references to old hostapd/dnsmasq-based hotspot approach

## Capabilities

### New Capabilities
- `ci-build-success`: Docker build completes without missing file errors
- `dockerfile-accuracy`: Dockerfile reflects actual system dependencies

### Modified Capabilities
<!-- No existing capabilities are being modified - hotspot functionality remains the same -->

## Impact

- `backend/Dockerfile`: Remove COPY statements for missing templates and update package list
- CI pipeline: Builds will succeed instead of failing  
- Container size: Slightly smaller without unused hostapd package
- No runtime functional changes (system already works this way)