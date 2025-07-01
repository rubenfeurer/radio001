// System restart network API endpoint
// Restarts network services and interfaces

import { exec } from 'child_process'
import { promisify } from 'util'

const execAsync = promisify(exec)

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()

  try {
    await restartNetworkServices(config)

    return {
      success: true,
      message: 'Network services restarted successfully',
      timestamp: Date.now()
    }
  } catch (error) {
    console.error('Network restart error:', error)

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to restart network services',
      timestamp: Date.now()
    }
  }
})

async function restartNetworkServices(config: any): Promise<void> {
  const isDevelopment = config.public.isDevelopment
  const wifiInterface = config.wifiInterface || 'wlan0'

  if (isDevelopment) {
    // Simulate restart in development
    console.log('[DEV] Simulating network restart')
    await new Promise(resolve => setTimeout(resolve, 2000))
    return
  }

  try {
    console.log('Restarting network services...')

    // Stop network services
    const stopCommands = [
      'sudo systemctl stop wpa_supplicant',
      'sudo systemctl stop dhcpcd',
      'sudo systemctl stop networking',
      `sudo ip link set ${wifiInterface} down`,
      'sudo pkill -f wpa_supplicant || true',
      'sudo pkill -f dhclient || true'
    ]

    for (const command of stopCommands) {
      try {
        await execAsync(command)
        await new Promise(resolve => setTimeout(resolve, 500))
      } catch (error) {
        console.warn(`Command failed (continuing): ${command}`, error)
        // Continue with other commands
      }
    }

    // Wait for services to stop
    await new Promise(resolve => setTimeout(resolve, 3000))

    // Restart network services
    const startCommands = [
      `sudo ip link set ${wifiInterface} up`,
      'sudo systemctl start networking',
      'sudo systemctl start wpa_supplicant',
      'sudo systemctl start dhcpcd'
    ]

    for (const command of startCommands) {
      try {
        await execAsync(command)
        await new Promise(resolve => setTimeout(resolve, 1000))
      } catch (error) {
        console.warn(`Command failed (continuing): ${command}`, error)
        // Continue with other commands
      }
    }

    // Try to restart WiFi connection
    try {
      await execAsync(`sudo wpa_supplicant -B -c /etc/wpa_supplicant/wpa_supplicant.conf -i ${wifiInterface} -D nl80211`)
      await execAsync(`sudo dhclient ${wifiInterface} 2>/dev/null || sudo dhcpcd ${wifiInterface} 2>/dev/null || true`)
    } catch (error) {
      console.warn('Failed to restart WiFi connection:', error)
      // Not critical, continue
    }

    console.log('Network services restart completed')
  } catch (error) {
    console.error('Critical error during network restart:', error)
    throw new Error('Failed to restart network services')
  }
}
