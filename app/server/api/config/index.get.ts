// Configuration API endpoint - GET
// Returns current device configuration

import { readFile } from 'fs/promises'
import { existsSync } from 'fs'
import type { AppConfig } from '~/types'

export default defineEventHandler(async (_event) => {
  const config = useRuntimeConfig()

  try {
    const deviceConfig = await getDeviceConfig(config)

    return {
      success: true,
      data: deviceConfig,
      timestamp: Date.now()
    }
  } catch (error) {
    console.error('Config get error:', error)

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get configuration',
      timestamp: Date.now()
    }
  }
})

async function getDeviceConfig(config: ReturnType<typeof useRuntimeConfig>): Promise<AppConfig> {
  const isDevelopment = config.public.isDevelopment

  // Default configuration
  const defaultConfig: AppConfig = {
    hostname: config.hostname || 'radio',
    wifiInterface: config.wifiInterface || 'wlan0',
    ethInterface: config.ethInterface || 'eth0',
    hotspot: {
      ssid: config.hotspotSsid || 'Radio-Setup',
      password: config.hotspotPassword || 'radio123',
      channel: 6,
      ip: config.hotspotIp || '192.168.4.1',
      subnet: '255.255.255.0',
      dhcpRange: config.hotspotRange || '192.168.4.2,192.168.4.20',
      hidden: false
    },
    features: {
      captivePortal: config.enableCaptivePortal || false,
      autoConnect: config.enableAutoConnect || true,
      monitoring: true
    }
  }

  if (isDevelopment) {
    // Return default config in development
    return defaultConfig
  }

  try {
    // Try to read saved configuration
    const configPath = '/etc/radio/config.json'

    if (existsSync(configPath)) {
      const savedConfigData = await readFile(configPath, 'utf-8')
      const savedConfig = JSON.parse(savedConfigData)

      // Merge with defaults
      return {
        ...defaultConfig,
        ...savedConfig,
        hotspot: {
          ...defaultConfig.hotspot,
          ...savedConfig.hotspot
        },
        features: {
          ...defaultConfig.features,
          ...savedConfig.features
        }
      }
    }

    return defaultConfig
  } catch (error) {
    console.error('Error reading config file:', error)
    return defaultConfig
  }
}
