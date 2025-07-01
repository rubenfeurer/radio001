// WiFi connect API endpoint
// Connects to a WiFi network with provided credentials

import { exec } from 'child_process'
import { promisify } from 'util'
import { writeFile, readFile } from 'fs/promises'
import { existsSync } from 'fs'
import type { WiFiCredentials } from '~/types'

const execAsync = promisify(exec)

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()

  try {
    const body = await readBody(event)
    const credentials: WiFiCredentials = body

    // Validate credentials
    if (!credentials.ssid || credentials.ssid.trim().length === 0) {
      throw new Error('SSID is required')
    }

    if (credentials.ssid.length > 32) {
      throw new Error('SSID must be 32 characters or less')
    }

    if (credentials.password && credentials.password.length > 63) {
      throw new Error('Password must be 63 characters or less')
    }

    const result = await connectToWiFi(credentials, config)

    return {
      success: true,
      message: `Connecting to ${credentials.ssid}. System will reboot to client mode.`,
      data: {
        ssid: credentials.ssid
      },
      timestamp: Date.now()
    }
  } catch (error) {
    console.error('WiFi connect error:', error)

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to connect to WiFi',
      timestamp: Date.now()
    }
  }
})

async function connectToWiFi(credentials: WiFiCredentials, config: any): Promise<boolean> {
  const isDevelopment = config.public.isDevelopment

  if (isDevelopment) {
    // Simulate connection in development
    console.log(`[DEV] Simulating connection to ${credentials.ssid}`)
    await new Promise(resolve => setTimeout(resolve, 1000))
    return true
  }

  try {
    // Create wpa_supplicant configuration
    const wpaConfig = await createWpaSupplicantConfig(credentials)

    // Write temporary configuration file
    const tempConfigPath = '/tmp/wpa_supplicant.conf.tmp'
    await writeFile(tempConfigPath, wpaConfig)

    // Validate the configuration
    const { stdout: testResult } = await execAsync(`wpa_supplicant -c ${tempConfigPath} -i ${config.wifiInterface} -D nl80211 -d 2>&1 | head -20`)

    if (testResult.includes('Could not read interface') || testResult.includes('Failed to initialize')) {
      throw new Error('Invalid WiFi configuration')
    }

    // Move configuration to final location (requires root)
    try {
      await execAsync(`sudo cp ${tempConfigPath} /etc/wpa_supplicant/wpa_supplicant.conf`)
      await execAsync(`sudo chown root:root /etc/wpa_supplicant/wpa_supplicant.conf`)
      await execAsync(`sudo chmod 600 /etc/wpa_supplicant/wpa_supplicant.conf`)
    } catch (error) {
      throw new Error('Failed to save WiFi configuration (insufficient permissions)')
    }

    // Clean up temporary file
    await execAsync(`rm -f ${tempConfigPath}`)

    // Stop hotspot services if running
    await stopHotspotMode()

    // Restart network services
    await restartNetworkServices(config.wifiInterface)

    // Schedule system reboot to apply changes (RaspiWiFi approach)
    setTimeout(async () => {
      try {
        await execAsync('sudo reboot')
      } catch (error) {
        console.error('Failed to reboot system:', error)
      }
    }, 5000) // 5 second delay

    return true
  } catch (error) {
    console.error('WiFi connection failed:', error)
    throw error
  }
}

async function createWpaSupplicantConfig(credentials: WiFiCredentials): Promise<string> {
  // Base configuration
  const config = [
    'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev',
    'update_config=1',
    'country=US',
    ''
  ]

  // Add network block
  config.push('network={')
  config.push(`    ssid="${escapeSSID(credentials.ssid)}"`)

  // Handle different security types
  if (!credentials.password || credentials.password.trim().length === 0) {
    // Open network
    config.push('    key_mgmt=NONE')
  } else {
    // Secured network
    const password = credentials.password.trim()

    if (credentials.security === 'WEP') {
      // WEP key (legacy)
      if (password.match(/^[0-9a-fA-F]+$/)) {
        // Hex key
        config.push(`    wep_key0=${password}`)
      } else {
        // ASCII key
        config.push(`    wep_key0="${password}"`)
      }
      config.push('    key_mgmt=NONE')
      config.push('    wep_tx_keyidx=0')
    } else {
      // WPA/WPA2/WPA3 (most common)
      if (password.length >= 8) {
        config.push(`    psk="${password}"`)
      } else {
        throw new Error('WPA password must be at least 8 characters')
      }

      // Set appropriate key management
      switch (credentials.security) {
        case 'WPA3':
          config.push('    key_mgmt=SAE')
          config.push('    ieee80211w=2')
          break
        case 'WPA2':
          config.push('    key_mgmt=WPA-PSK')
          config.push('    proto=RSN')
          break
        case 'WPA':
          config.push('    key_mgmt=WPA-PSK')
          config.push('    proto=WPA')
          break
        default:
          // Default to WPA2 for maximum compatibility
          config.push('    key_mgmt=WPA-PSK')
          config.push('    proto=RSN WPA')
      }
    }
  }

  // Hidden network support
  if (credentials.hidden) {
    config.push('    scan_ssid=1')
  }

  // Priority (higher for user-added networks)
  config.push('    priority=1')

  config.push('}')
  config.push('')

  return config.join('\n')
}

function escapeSSID(ssid: string): string {
  // Escape special characters in SSID
  return ssid.replace(/\\/g, '\\\\').replace(/"/g, '\\"')
}

async function stopHotspotMode(): Promise<void> {
  try {
    // Stop hotspot services
    const services = ['hostapd', 'dnsmasq']

    for (const service of services) {
      try {
        await execAsync(`sudo systemctl stop ${service} 2>/dev/null || true`)
      } catch {
        // Service might not be running, continue
      }
    }

    // Remove host mode marker (RaspiWiFi approach)
    await execAsync('sudo rm -f /etc/raspiwifi/host_mode 2>/dev/null || true')

    console.log('Hotspot mode stopped')
  } catch (error) {
    console.error('Error stopping hotspot mode:', error)
    // Don't throw, this is not critical
  }
}

async function restartNetworkServices(wifiInterface: string): Promise<void> {
  try {
    // Bring down the interface
    await execAsync(`sudo ip link set ${wifiInterface} down`)

    // Kill any existing wpa_supplicant processes
    await execAsync('sudo pkill -f wpa_supplicant || true')

    // Wait a moment
    await new Promise(resolve => setTimeout(resolve, 2000))

    // Bring up the interface
    await execAsync(`sudo ip link set ${wifiInterface} up`)

    // Start wpa_supplicant
    await execAsync(`sudo wpa_supplicant -B -c /etc/wpa_supplicant/wpa_supplicant.conf -i ${wifiInterface} -D nl80211`)

    // Start DHCP client
    await execAsync(`sudo dhclient ${wifiInterface} 2>/dev/null || sudo dhcpcd ${wifiInterface} 2>/dev/null || true`)

    console.log('Network services restarted')
  } catch (error) {
    console.error('Error restarting network services:', error)
    throw new Error('Failed to restart network services')
  }
}
