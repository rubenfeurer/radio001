// System status API endpoint
// Returns current system status including WiFi, memory, CPU, and services

import { exec } from 'child_process'
import { promisify } from 'util'
import { readFile } from 'fs/promises'
import type { SystemStatus } from '~/types'

const execAsync = promisify(exec)

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()

  try {
    // Get system status
    const status = await getSystemStatus(config)

    return {
      success: true,
      data: status,
      timestamp: Date.now()
    }
  } catch (error) {
    console.error('System status error:', error)

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get system status',
      timestamp: Date.now()
    }
  }
})

async function getSystemStatus(config: any): Promise<SystemStatus> {
  const isDevelopment = config.public.isDevelopment

  if (isDevelopment) {
    // Return mock data for development
    return {
      hostname: config.public.hostname,
      uptime: 3600, // 1 hour
      memory: {
        total: 1024 * 1024 * 1024, // 1GB
        used: 512 * 1024 * 1024,   // 512MB
        free: 512 * 1024 * 1024    // 512MB
      },
      cpu: {
        load: 25.5,
        temperature: 45
      },
      network: {
        wifi: {
          wifiInterface: 'wlan0',
          status: 'disconnected',
          mode: 'hotspot',
          ip: '192.168.4.1'
        },
        ethernet: {
          connected: false
        }
      },
      services: {
        avahi: true,
        hostapd: true,
        dnsmasq: true
      }
    }
  }

  // Production: Get real system data
  const [uptime, memory, cpu, wifi, services] = await Promise.allSettled([
    getUptime(),
    getMemoryInfo(),
    getCpuInfo(),
    getWiFiStatus(config.wifiInterface),
    getServicesStatus()
  ])

  return {
    hostname: config.hostname,
    uptime: uptime.status === 'fulfilled' ? uptime.value : 0,
    memory: memory.status === 'fulfilled' ? memory.value : { total: 0, used: 0, free: 0 },
    cpu: cpu.status === 'fulfilled' ? cpu.value : { load: 0, temperature: 0 },
    network: {
      wifi: wifi.status === 'fulfilled' ? wifi.value : {
        wifiInterface: config.wifiInterface,
        status: 'disconnected',
        mode: 'offline'
      }
    },
    services: services.status === 'fulfilled' ? services.value : {
      avahi: false,
      hostapd: false,
      dnsmasq: false
    }
  }
}

async function getUptime(): Promise<number> {
  try {
    const { stdout } = await execAsync('cat /proc/uptime')
    const uptimeSeconds = parseFloat(stdout.split(' ')[0])
    return uptimeSeconds
  } catch {
    return 0
  }
}

async function getMemoryInfo(): Promise<{ total: number; used: number; free: number }> {
  try {
    const { stdout } = await execAsync('cat /proc/meminfo')
    const lines = stdout.split('\n')

    const totalMatch = lines.find(line => line.startsWith('MemTotal:'))
    const freeMatch = lines.find(line => line.startsWith('MemFree:'))
    const availableMatch = lines.find(line => line.startsWith('MemAvailable:'))

    const total = totalMatch ? parseInt(totalMatch.split(/\s+/)[1]) * 1024 : 0
    const free = freeMatch ? parseInt(freeMatch.split(/\s+/)[1]) * 1024 : 0
    const available = availableMatch ? parseInt(availableMatch.split(/\s+/)[1]) * 1024 : free
    const used = total - available

    return { total, used, free: available }
  } catch {
    return { total: 0, used: 0, free: 0 }
  }
}

async function getCpuInfo(): Promise<{ load: number; temperature?: number }> {
  try {
    // Get CPU load average
    const { stdout: loadavg } = await execAsync('cat /proc/loadavg')
    const load = parseFloat(loadavg.split(' ')[0]) * 100

    // Get CPU temperature (Raspberry Pi specific)
    let temperature: number | undefined
    try {
      const { stdout: temp } = await execAsync('cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo "0"')
      temperature = parseInt(temp.trim()) / 1000
    } catch {
      temperature = undefined
    }

    return { load, temperature }
  } catch {
    return { load: 0 }
  }
}

async function getWiFiStatus(wifiInterface: string): Promise<any> {
  try {
    // Check if interface exists and is up
    const { stdout: ifconfig } = await execAsync(`ip addr show ${wifiInterface} 2>/dev/null || echo "interface not found"`)

    if (ifconfig.includes('interface not found')) {
      return {
        wifiInterface,
        status: 'disconnected',
        mode: 'offline'
      }
    }

    // Check if interface is up
    const isUp = ifconfig.includes('state UP')
    if (!isUp) {
      return {
        wifiInterface,
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
          wifiInterface,
          status: 'connected',
          mode: 'hotspot',
          ip: ip || '192.168.4.1'
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
          wifiInterface,
          status: 'disconnected',
          mode: 'client'
        }
      }

      // Extract SSID
      const ssidMatch = iwconfig.match(/ESSID:"([^"]+)"/)
      const ssid = ssidMatch ? ssidMatch[1] : undefined

      // Extract signal quality (if available)
      const signalMatch = iwconfig.match(/Signal level=(-?\d+)/)
      let signal: number | undefined
      if (signalMatch) {
        const signalDbm = parseInt(signalMatch[1])
        // Convert dBm to percentage (rough approximation)
        signal = Math.max(0, Math.min(100, 2 * (signalDbm + 100)))
      }

      return {
        wifiInterface,
        status: ssid ? 'connected' : 'disconnected',
        mode: 'client',
        ssid,
        ip,
        signal
      }
    } catch {
      return {
        wifiInterface,
        status: 'disconnected',
        mode: 'client'
      }
    }
  } catch {
    return {
      wifiInterface,
      status: 'disconnected',
      mode: 'offline'
    }
  }
}

async function getServicesStatus(): Promise<{ [key: string]: boolean }> {
  const services = ['avahi-daemon', 'hostapd', 'dnsmasq']
  const status: { [key: string]: boolean } = {}

  for (const service of services) {
    try {
      const { stdout } = await execAsync(`systemctl is-active ${service} 2>/dev/null || echo "inactive"`)
      const key = service.replace('-daemon', '')
      status[key] = stdout.trim() === 'active'
    } catch {
      const key = service.replace('-daemon', '')
      status[key] = false
    }
  }

  return status
}
