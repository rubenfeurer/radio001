// WiFi scan API endpoint
// Scans for available WiFi networks and returns the results

import { exec } from 'child_process'
import { promisify } from 'util'
import type { WiFiNetwork, ScanResult } from '~/types'

const execAsync = promisify(exec)

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()

  try {
    const scanResult = await scanWiFiNetworks(config)

    return {
      success: true,
      data: scanResult.networks,
      message: `Found ${scanResult.networks.length} networks`,
      timestamp: scanResult.timestamp
    }
  } catch (error) {
    console.error('WiFi scan error:', error)

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to scan networks',
      timestamp: Date.now()
    }
  }
})

async function scanWiFiNetworks(config: any): Promise<ScanResult> {
  const isDevelopment = config.public.isDevelopment
  const wifiInterface = config.wifiInterface || 'wlan0'

  if (isDevelopment) {
    // Return mock data for development
    const mockNetworks: WiFiNetwork[] = [
      {
        ssid: 'HomeWiFi',
        bssid: '00:11:22:33:44:55',
        signal: 85,
        frequency: '2.4 GHz',
        channel: 6,
        security: 'WPA2',
        connected: false,
        saved: false
      },
      {
        ssid: 'OfficeNetwork',
        bssid: '66:77:88:99:AA:BB',
        signal: 65,
        frequency: '5 GHz',
        channel: 36,
        security: 'WPA3',
        connected: false,
        saved: true
      },
      {
        ssid: 'GuestNetwork',
        bssid: 'CC:DD:EE:FF:00:11',
        signal: 45,
        frequency: '2.4 GHz',
        channel: 11,
        security: 'Open',
        connected: false,
        saved: false
      },
      {
        ssid: 'NeighborWiFi',
        bssid: '22:33:44:55:66:77',
        signal: 25,
        frequency: '2.4 GHz',
        channel: 1,
        security: 'WPA/WPA2',
        connected: false,
        saved: false
      }
    ]

    return {
      networks: mockNetworks,
      timestamp: Date.now(),
      wifiInterface: wifiInterface
    }
  }

  try {
    // Perform WiFi scan using iwlist
    const { stdout } = await execAsync(`iwlist ${wifiInterface} scan 2>/dev/null`)

    if (!stdout) {
      throw new Error('No scan results returned')
    }

    const networks = parseIwlistOutput(stdout)

    // Get saved networks to mark them
    const savedNetworks = await getSavedNetworks()

    // Get current connection to mark connected network
    const currentConnection = await getCurrentConnection(wifiInterface)

    // Enhance networks with saved/connected status
    const enhancedNetworks = networks.map(network => ({
      ...network,
      saved: savedNetworks.includes(network.ssid),
      connected: currentConnection === network.ssid
    }))

    return {
      networks: enhancedNetworks,
      timestamp: Date.now(),
      wifiInterface: wifiInterface
    }
  } catch (error) {
    console.error('WiFi scan failed:', error)
    throw new Error(`Failed to scan WiFi networks: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

function parseIwlistOutput(output: string): WiFiNetwork[] {
  const networks: WiFiNetwork[] = []
  const cells = output.split(/Cell \d+/)

  for (const cell of cells) {
    if (!cell.trim()) continue

    const network: Partial<WiFiNetwork> = {}

    // Extract SSID
    const ssidMatch = cell.match(/ESSID:"([^"]*)"/)
    if (!ssidMatch || !ssidMatch[1]) continue
    network.ssid = ssidMatch[1]

    // Extract BSSID (MAC address)
    const bssidMatch = cell.match(/Address: ([0-9A-Fa-f:]{17})/)
    if (bssidMatch) {
      network.bssid = bssidMatch[1]
    }

    // Extract signal quality/strength
    const signalMatch = cell.match(/Quality=(\d+)\/(\d+)|Signal level=(-?\d+)\s*dBm/)
    if (signalMatch) {
      if (signalMatch[1] && signalMatch[2]) {
        // Quality format: Quality=70/70
        const quality = parseInt(signalMatch[1])
        const maxQuality = parseInt(signalMatch[2])
        network.signal = Math.round((quality / maxQuality) * 100)
      } else if (signalMatch[3]) {
        // dBm format: Signal level=-45 dBm
        const dbm = parseInt(signalMatch[3])
        // Convert dBm to percentage (rough approximation)
        network.signal = Math.max(0, Math.min(100, 2 * (dbm + 100)))
      }
    }

    // Extract frequency
    const freqMatch = cell.match(/Frequency:(\d+\.?\d*)\s*GHz/)
    if (freqMatch) {
      const freq = parseFloat(freqMatch[1])
      network.frequency = freq >= 5 ? '5 GHz' : '2.4 GHz'

      // Estimate channel from frequency
      if (freq < 3) {
        // 2.4 GHz channels
        network.channel = Math.round((freq - 2.412) / 0.005) + 1
      } else {
        // 5 GHz channels (simplified)
        network.channel = Math.round((freq - 5.000) / 0.005)
      }
    }

    // Extract security/encryption
    let security = 'Open'

    if (cell.includes('Encryption key:off')) {
      security = 'Open'
    } else if (cell.includes('WPA3')) {
      security = 'WPA3'
    } else if (cell.includes('WPA2')) {
      security = 'WPA2'
    } else if (cell.includes('WPA')) {
      security = cell.includes('WPA2') ? 'WPA/WPA2' : 'WPA'
    } else if (cell.includes('WEP')) {
      security = 'WEP'
    } else if (cell.includes('Encryption key:on')) {
      security = 'WPA' // Default assumption for encrypted networks
    }

    network.security = security as WiFiNetwork['security']

    // Only add networks with valid SSID and signal
    if (network.ssid && typeof network.signal === 'number') {
      networks.push(network as WiFiNetwork)
    }
  }

  // Remove duplicates (same SSID, keep the one with stronger signal)
  const uniqueNetworks = new Map<string, WiFiNetwork>()

  for (const network of networks) {
    const existing = uniqueNetworks.get(network.ssid)
    if (!existing || (network.signal || 0) > (existing.signal || 0)) {
      uniqueNetworks.set(network.ssid, network)
    }
  }

  // Sort by signal strength (strongest first)
  return Array.from(uniqueNetworks.values())
    .sort((a, b) => (b.signal || 0) - (a.signal || 0))
}

async function getSavedNetworks(): Promise<string[]> {
  try {
    const { stdout } = await execAsync('cat /etc/wpa_supplicant/wpa_supplicant.conf 2>/dev/null || echo ""')
    const networks: string[] = []

    const ssidMatches = stdout.matchAll(/ssid="([^"]+)"/g)
    for (const match of ssidMatches) {
      networks.push(match[1])
    }

    return networks
  } catch {
    return []
  }
}

async function getCurrentConnection(wifiInterface: string): Promise<string | null> {
  try {
    const { stdout } = await execAsync(`iwconfig ${wifiInterface} 2>/dev/null`)
    const ssidMatch = stdout.match(/ESSID:"([^"]+)"/)
    return ssidMatch ? ssidMatch[1] : null
  } catch {
    return null
  }
}
