// WiFi status API endpoint
// Returns current WiFi connection status and details

import { exec } from 'child_process'
import { promisify } from 'util'
import type { WiFiStatus } from '~/types'

const execAsync = promisify(exec)

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  // Test comment to trigger pre-commit linting

  try {
    const wifiStatus = await getWiFiStatus(config)

    return {
      success: true,
      data: wifiStatus,
      timestamp: Date.now()
    }
  } catch (error) {
    console.error('WiFi status error:', error)

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get WiFi status',
      timestamp: Date.now()
    }
  }
})

async function getWiFiStatus(config: any): Promise<WiFiStatus> {
  const isDevelopment = config.public.isDevelopment
  const wifiInterface = config.wifiInterface || 'wlan0'

  if (isDevelopment) {
    // Return mock data for development
    return {
      wifiInterface: wifiInterface,
      status: 'disconnected',
      mode: 'hotspot',
      ip: '192.168.4.1'
    }
  }

  try {
    // Check if interface exists and is up
    const { stdout: ifconfig } = await execAsync(`ip addr show ${wifiInterface} 2>/dev/null || echo "interface not found"`)

    if (ifconfig.includes('interface not found')) {
      return {
        wifiInterface: wifiInterface,
        status: 'disconnected',
        mode: 'offline'
      }
    }

    // Check if interface is up
    const isUp = ifconfig.includes('state UP')
    if (!isUp) {
      return {
        wifiInterface: wifiInterface,
        status: 'disconnected',
        mode: 'offline'
      }
    }

    // Get IP address
    const ipMatch = ifconfig.match(/inet (\d+\.\d+\.\d+\.\d+)/)
    const ip = ipMatch ? ipMatch[1] : undefined

    // Check if running in hotspot mode
    try {
      const { stdout: hostapd } = await execAsync('systemctl is-active hostapd 2>/dev/null || echo "inactive"')
      if (hostapd.trim() === 'active') {
        return {
          wifiInterface: wifiInterface,
          status: 'connected',
          mode: 'hotspot',
          ip: ip || '192.168.4.1',
          ssid: config.hotspotSsid || 'Radio-Setup'
        }
      }
    } catch {
      // Continue to check client mode
    }

    // Check client mode connection
    try {
      const { stdout: iwconfig } = await execAsync(`iwconfig ${wifiInterface} 2>/dev/null`)

      if (iwconfig.includes('Access Point: Not-Associated')) {
        return {
          wifiInterface: wifiInterface,
          status: 'disconnected',
          mode: 'client'
        }
      }

      // Extract SSID
      const ssidMatch = iwconfig.match(/ESSID:"([^"]+)"/)
      const ssid = ssidMatch ? ssidMatch[1] : undefined

      // Extract frequency
      const freqMatch = iwconfig.match(/Frequency:(\d+\.\d+)\s*GHz/)
      const frequency = freqMatch ? `${freqMatch[1]} GHz` : undefined

      // Extract signal quality (if available)
      const signalMatch = iwconfig.match(/Signal level=(-?\d+)/)
      let signal: number | undefined
      if (signalMatch) {
        const signalDbm = parseInt(signalMatch[1])
        // Convert dBm to percentage (rough approximation)
        signal = Math.max(0, Math.min(100, 2 * (signalDbm + 100)))
      }

      return {
        wifiInterface: wifiInterface,
        status: ssid ? 'connected' : 'disconnected',
        mode: 'client',
        ssid,
        ip,
        signal,
        frequency
      }
    } catch {
      return {
        wifiInterface: wifiInterface,
        status: 'disconnected',
        mode: 'client'
      }
    }
  } catch (error) {
    console.error('Error getting WiFi status:', error)
    return {
      wifiInterface: wifiInterface,
      status: 'disconnected',
      mode: 'offline'
    }
  }
}
