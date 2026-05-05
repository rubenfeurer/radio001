## Context

The project originally used a hostapd/dnsmasq-based approach for WiFi hotspot functionality but has successfully migrated to using NetworkManager's built-in hotspot capabilities via `nmcli device wifi hotspot`. However, the Dockerfile still contains legacy references to configuration template files and package dependencies from the old approach, causing CI build failures.

Current state analysis shows:
- The running container has only `dnsmasq-base` installed (not full `dnsmasq` or `hostapd`)
- Hotspot functionality works perfectly via NetworkManager
- Template files were never created and are not needed
- Boot script uses `nmcli` exclusively for hotspot management

## Goals / Non-Goals

**Goals:**
- Fix CI build failures caused by missing template files
- Align Dockerfile with actual system dependencies
- Remove unused legacy package installations
- Maintain all existing hotspot functionality

**Non-Goals:**
- Changing the hotspot implementation approach
- Modifying runtime behavior or configuration
- Adding new dependencies or capabilities
- Restructuring the NetworkManager integration

## Decisions

### Decision 1: Remove Template File COPY Statements

Remove the following lines from `backend/Dockerfile`:
```
COPY config/hostapd/hostapd.conf.template /etc/hostapd/hostapd.conf.template
COPY config/dnsmasq/dnsmasq.conf.template /etc/dnsmasq.conf.template
```

**Rationale**: These files don't exist and are not needed since NetworkManager handles hotspot configuration internally via `nmcli device wifi hotspot`.

### Decision 2: Remove hostapd Package

Remove `hostapd` from the apt-get install list.

**Rationale**: The current container already runs without hostapd installed, proving it's not needed for NetworkManager-based hotspot functionality. NetworkManager handles AP creation directly through the kernel's nl80211 interface.

### Decision 3: Replace dnsmasq with dnsmasq-base

Change `dnsmasq` to `dnsmasq-base` in the package list.

**Rationale**: NetworkManager recommends `dnsmasq-base` for shared connections (the lightweight DHCP component), and this is already what's actually installed. The full `dnsmasq` package includes unnecessary DNS caching features.

### Decision 4: Preserve NetworkManager and Related Tools

Keep these packages unchanged:
- `network-manager` (core dependency)
- `wireless-tools`, `iw` (WiFi interface tools)
- `iproute2`, `iputils-ping` (networking utilities)

**Rationale**: These are actively used by the boot script and NetworkManager for WiFi management.

## Implementation Approach

This is a pure cleanup change with no functional modifications:

1. **File Removals**: Remove COPY statements for non-existent template files
2. **Package Updates**: Update apt-get install list to match actual usage
3. **Verification**: Ensure hotspot functionality remains unchanged

The change is backward compatible since we're removing unused dependencies, not changing functional ones.

## Risk Assessment

**Low Risk**: 
- System already runs without the packages we're removing
- No changes to runtime behavior or configuration
- NetworkManager hotspot functionality is proven to work

**Testing Strategy**:
- Verify CI build succeeds
- Test hotspot creation still works via `nmcli device wifi hotspot`
- Confirm container starts and operates normally