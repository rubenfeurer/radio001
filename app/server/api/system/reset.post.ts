// System reset API endpoint
// Resets the device to hotspot mode (RaspiWiFi reset functionality)

import { exec } from 'child_process'
import { promisify } from 'util'
import { writeFile, unlink } from 'fs/promises'
import { existsSync } from 'fs'

const execAsync = promisify(exec)

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()

  try {
    await resetToHotspotMode(config)

    return {
      success: true,
      message: 'System is resetting to hotspot mode...',
      timestamp: Date.now()
    }
  } catch (error) {
    console.error('System reset error:', error)

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to reset system',
      timestamp: Date.now()
    }
  }
})

async function resetToHotspotMode(config: any): Promise<void> {
  const isDevelopment = config.public.isDevelopment

  if (isDevelopment) {
    // Simulate reset in development
    console.log('[DEV] Simulating system reset to hotspot mode')
    await new Promise(resolve => setTimeout(resolve, 1000))
    return
  }

  try {
    console.log('Resetting system to hotspot mode...')

    // Create host mode marker (RaspiWiFi approach)
    const hostModeFile = '/etc/raspiwifi/host_mode'
    const raspiwifiDir = '/etc/raspiwifi'

    // Ensure directory exists
    try {
      await execAsync(`sudo mkdir -p ${raspiwifiDir}`)
    } catch (error) {
      console.warn('Failed to create raspiwifi directory:', error)
    }

    // Create host mode marker
    try {
      await execAsync(`sudo touch ${hostModeFile}`)
      console.log('Host mode marker created')
    } catch (error) {
      console.warn('Failed to create host mode marker:', error)
    }

    // Stop client mode services
    const stopCommands = [
      'sudo systemctl stop wpa_supplicant',
      'sudo systemctl stop dhcpcd',
      'sudo pkill -f wpa_supplicant || true',
      'sudo pkill -f dhclient || true'
    ]

    for (const command of stopCommands) {
      try {
        await execAsync(command)
        await new Promise(resolve => setTimeout(resolve, 500))
      } catch (error) {
        console.warn(`Stop command failed (continuing): ${command}`, error)
      }
    }

    // Remove saved WiFi configuration
    try {
      await execAsync('sudo rm -f /etc/wpa_supplicant/wpa_supplicant.conf')
      console.log('WiFi configuration cleared')
    } catch (error) {
      console.warn('Failed to remove WiFi config:', error)
    }

    // Configure hotspot
    await configureHotspot(config)

    // Start hotspot services
    const startCommands = [
      'sudo systemctl enable hostapd',
      'sudo systemctl enable dnsmasq',
      'sudo systemctl start hostapd',
      'sudo systemctl start dnsmasq'
    ]

    for (const command of startCommands) {
      try {
        await execAsync(command)
        await new Promise(resolve => setTimeout(resolve, 1000))
      } catch (error) {
        console.warn(`Start command failed (continuing): ${command}`, error)
      }
    }

    // Schedule reboot to ensure clean state
    setTimeout(async () => {
      try {
        console.log('Rebooting system to complete reset...')
        await execAsync('sudo reboot')
      } catch (error) {
        console.error('Failed to reboot system:', error)
      }
    }, 5000) // 5 second delay

    console.log('System reset initiated')
  } catch (error) {
    console.error('Critical error during system reset:', error)
    throw new Error('Failed to reset system to hotspot mode')
  }
}

async function configureHotspot(config: any): Promise<void> {
  const wifiInterface = config.wifiInterface || 'wlan0'
  const hotspotSSID = config.hotspotSsid || 'Radio-Setup'
  const hotspotPassword = config.hotspotPassword || 'radio123'
  const hotspotIP = config.hotspotIp || '192.168.4.1'

  try {
    // Configure hostapd
    const hostapdConfig = [
      `interface=${wifiInterface}`,
      'driver=nl80211',
      `ssid=${hotspotSSID}`,
      'hw_mode=g',
      'channel=6',
      'wmm_enabled=0',
      'macaddr_acl=0',
      'auth_algs=1',
      'ignore_broadcast_ssid=0'
    ]

    if (hotspotPassword && hotspotPassword.length >= 8) {
      hostapdConfig.push('wpa=2')
      hostapdConfig.push(`wpa_passphrase=${hotspotPassword}`)
      hostapdConfig.push('wpa_key_mgmt=WPA-PSK')
      hostapdConfig.push('wpa_pairwise=TKIP')
      hostapdConfig.push('rsn_pairwise=CCMP')
    }

    const hostapdConfigContent = hostapdConfig.join('\n') + '\n'
    await execAsync('sudo mkdir -p /etc/hostapd')
    await writeFile('/tmp/hostapd.conf', hostapdConfigContent)
    await execAsync('sudo mv /tmp/hostapd.conf /etc/hostapd/hostapd.conf')
    await execAsync('sudo chown root:root /etc/hostapd/hostapd.conf')

    // Configure dnsmasq
    const dnsmasqConfig = [
      `interface=${wifiInterface}`,
      'dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h',
      'server=8.8.8.8',
      'server=8.8.4.4'
    ]

    const dnsmasqConfigContent = dnsmasqConfig.join('\n') + '\n'
    await writeFile('/tmp/dnsmasq.conf', dnsmasqConfigContent)
    await execAsync('sudo mv /tmp/dnsmasq.conf /etc/dnsmasq.conf')
    await execAsync('sudo chown root:root /etc/dnsmasq.conf')

    // Configure network interface
    await execAsync(`sudo ip addr flush dev ${wifiInterface}`)
    await execAsync(`sudo ip addr add ${hotspotIP}/24 dev ${wifiInterface}`)
    await execAsync(`sudo ip link set ${wifiInterface} up`)

    // Enable IP forwarding
    await execAsync('echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward')

    console.log('Hotspot configuration completed')
  } catch (error) {
    console.error('Error configuring hotspot:', error)
    throw new Error('Failed to configure hotspot')
  }
}
