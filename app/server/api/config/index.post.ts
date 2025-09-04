// Configuration API endpoint - POST
// Saves device configuration

import { writeFile, mkdir } from 'fs/promises'
import { dirname } from 'path'
import { existsSync } from 'fs'

// Helper function for executing commands
import { exec } from 'child_process'
import { promisify } from 'util'
import type { AppConfig } from '~/types'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()

  try {
    const body = await readBody(event)
    const newConfig: AppConfig = body

    // Validate configuration
    const validation = validateConfig(newConfig)
    if (!validation.valid) {
      return {
        success: false,
        error: validation.errors.join(', '),
        timestamp: Date.now()
      }
    }

    await saveDeviceConfig(newConfig, config)

    return {
      success: true,
      message: 'Configuration saved successfully',
      timestamp: Date.now()
    }
  } catch (error) {
    console.error('Config save error:', error)

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to save configuration',
      timestamp: Date.now()
    }
  }
})

async function saveDeviceConfig(newConfig: AppConfig, runtimeConfig: ReturnType<typeof useRuntimeConfig>): Promise<void> {
  const isDevelopment = runtimeConfig.public.isDevelopment

  if (isDevelopment) {
    // In development, just log the config
    console.log('[DEV] Configuration would be saved:', JSON.stringify(newConfig, null, 2))
    return
  }

  try {
    const configPath = '/etc/radio/config.json'
    const configDir = dirname(configPath)

    // Ensure config directory exists
    if (!existsSync(configDir)) {
      await mkdir(configDir, { recursive: true })
    }

    // Write configuration file
    await writeFile(configPath, JSON.stringify(newConfig, null, 2))

    // Set proper permissions
    try {
      await execAsync(`sudo chown root:root ${configPath}`)
      await execAsync(`sudo chmod 644 ${configPath}`)
    } catch {
      // Permissions might fail in some environments, continue
    }

    console.log('Configuration saved to', configPath)
  } catch (error) {
    console.error('Error saving config file:', error)
    throw new Error('Failed to save configuration file')
  }
}

function validateConfig(config: AppConfig): { valid: boolean; errors: string[] } {
  const errors: string[] = []

  // Validate hostname
  if (!config.hostname || config.hostname.trim().length === 0) {
    errors.push('Hostname is required')
  } else if (!/^[a-zA-Z0-9-]+$/.test(config.hostname)) {
    errors.push('Hostname can only contain letters, numbers, and hyphens')
  } else if (config.hostname.length > 63) {
    errors.push('Hostname must be 63 characters or less')
  }

  // Validate WiFi interface
  if (!config.wifiInterface || !/^[a-zA-Z0-9]+$/.test(config.wifiInterface)) {
    errors.push('Invalid WiFi interface name')
  }

  // Validate hotspot configuration
  if (config.hotspot) {
    if (!config.hotspot.ssid || config.hotspot.ssid.trim().length === 0) {
      errors.push('Hotspot SSID is required')
    } else if (config.hotspot.ssid.length > 32) {
      errors.push('Hotspot SSID must be 32 characters or less')
    }

    if (config.hotspot.password && config.hotspot.password.length > 0) {
      if (config.hotspot.password.length < 8) {
        errors.push('Hotspot password must be at least 8 characters')
      } else if (config.hotspot.password.length > 63) {
        errors.push('Hotspot password must be 63 characters or less')
      }
    }

    if (config.hotspot.channel && (config.hotspot.channel < 1 || config.hotspot.channel > 11)) {
      errors.push('Hotspot channel must be between 1 and 11')
    }

    if (config.hotspot.ip && !/^(\d{1,3}\.){3}\d{1,3}$/.test(config.hotspot.ip)) {
      errors.push('Invalid hotspot IP address format')
    }
  }

  return {
    valid: errors.length === 0,
    errors
  }
}

const execAsync = promisify(exec)
