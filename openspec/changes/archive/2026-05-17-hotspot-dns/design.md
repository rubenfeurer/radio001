## Context

In hotspot mode, NetworkManager creates an AP on `wlan0` and runs an internal DHCP server that advertises `192.168.4.1` as both the gateway and DNS server. However, nothing on the Pi listens on port 53 at that IP, so all hostname queries from connected clients fail. mDNS (avahi) is unreliable here: multicast queries don't cross AP boundaries reliably, and Android has no native mDNS support.

The Pi's avahi hostname is `radio` (from `HOSTNAME` env var and `config/avahi/avahi-daemon.conf`), making the target URL `radio.local`.

dnsmasq is a lightweight DNS/DHCP server standard on Pi-based hotspot setups. We use it DNS-only (DHCP remains with NetworkManager) to answer `radio.local → 192.168.4.1` for any client that connects to the hotspot.

## Goals / Non-Goals

**Goals:**
- `radio.local` resolves to `192.168.4.1` for all clients connected to the hotspot
- dnsmasq starts automatically when hotspot activates, stops when it deactivates
- Setup page shows `radio.local` as the correct URL (typo fixed)
- Works on macOS, iOS, Android, Windows without any client configuration

**Non-Goals:**
- Replacing NetworkManager's DHCP server (dnsmasq runs DNS-only)
- Making `radio.local` resolve on the normal LAN (avahi already handles that)
- Captive portal / HTTP redirect (out of scope)
- Changing the Pi hostname from `radio` to anything else

## Decisions

**D1: DNS-only dnsmasq, not DHCP**
NetworkManager's built-in DHCP is already working. Running a second DHCP server would conflict. dnsmasq is configured with `port=53` only, no `dhcp-range`. NM already advertises `192.168.4.1` as the DNS server to DHCP clients, so dnsmasq just needs to listen there.
> Alternative: replace NM DHCP with dnsmasq entirely. Rejected — more invasive, risk of breaking existing hotspot behaviour.

**D2: dnsmasq on the host, not in the container**
DNS must be accessible at `192.168.4.1:53` on the host network interface. The container runs with `network_mode: host` but starting a system service inside the container is fragile. Host-level dnsmasq is the correct layer.

**D3: `/etc/dnsmasq.d/` drop-in config**
Rather than modifying the main `/etc/dnsmasq.conf`, write a drop-in at `/etc/dnsmasq.d/radio-hotspot.conf`. This is idempotent (install.sh can overwrite it) and doesn't conflict with any existing dnsmasq installation.

Config content:
```
# Managed by install.sh
interface=wlan0
bind-interfaces
no-dhcp-interface=wlan0
address=/radio.local/192.168.4.1
```

`bind-interfaces` ensures dnsmasq only listens on `wlan0`, not on all interfaces (avoids conflict with system resolver on `eth0` / `lo`). `no-dhcp-interface` disables DHCP on wlan0 (NM handles it).

**D4: Start/stop dnsmasq from wifi_manager.py and boot-wifi-check.sh**
Both hotspot activation paths must manage dnsmasq:
- `wifi_manager.py switch_to_host_mode()`: `sudo systemctl start dnsmasq` after nmcli hotspot command
- `wifi_manager.py` deactivation / `switch_to_client_mode()`: `sudo systemctl stop dnsmasq`
- `boot-wifi-check.sh`: same start/stop around nmcli hotspot invocation

dnsmasq should not run in client mode — it would intercept DNS unnecessarily.

**D5: dnsmasq masked when not in hotspot mode**
To prevent dnsmasq from auto-starting on boot (it should only run during hotspot mode), install.sh masks the unit after installing: `systemctl mask dnsmasq`. wifi_manager and boot script unmask → start, then stop → mask on deactivation.
> Alternative: just start/stop without masking. Risk: dnsmasq starts on next boot before NM is ready, causing conflicts. Masking is safer.

## Risks / Trade-offs

- **Conflict with existing dnsmasq** — If dnsmasq is already installed and running on the Pi, our config could conflict. → `install.sh` stops and masks dnsmasq before writing config, ensuring a clean state.
- **wlan0 interface name** — Hard-coded to `wlan0`. If the interface is renamed (e.g., `wlan1`), dnsmasq won't bind. → Use `WIFI_INTERFACE` from radio.conf in the dnsmasq config template; `install.sh` substitutes the value when writing the file.
- **Port 53 already in use** — `systemd-resolved` may occupy port 53 on some Pi OS versions. → `install.sh` checks for and disables `systemd-resolved`'s stub listener if present (`DNSStubListener=no` in `/etc/systemd/resolved.conf`).

## Migration Plan

1. `install.sh` updated — re-run it on the Pi to install dnsmasq and write config
2. No container restart needed — all changes are host-level
3. Rollback: `sudo apt-get remove dnsmasq`, `sudo rm /etc/dnsmasq.d/radio-hotspot.conf`
