// Health check API endpoint for Radio WiFi Configuration
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()

  try {
    // Basic health checks
    const startTime = Date.now()

    // Check system resources
    const memoryUsage = process.memoryUsage()

    // Check if we're in development mode
    const isDevelopment = config.public.isDevelopment

    // Calculate uptime
    const uptime = process.uptime()

    // Basic network interface check (simplified for now)
    let networkStatus = 'unknown'
    try {
      // In production, this would check actual network interfaces
      if (isDevelopment) {
        networkStatus = 'development'
      } else {
        // Placeholder for actual network checking
        networkStatus = 'checking'
      }
    } catch (error) {
      networkStatus = 'error'
    }

    const responseTime = Date.now() - startTime

    // Determine overall health status
    const isHealthy = responseTime < 1000 && memoryUsage.heapUsed < memoryUsage.heapTotal * 0.9

    return {
      success: true,
      status: isHealthy ? 'healthy' : 'degraded',
      timestamp: new Date().toISOString(),
      data: {
        uptime: Math.floor(uptime),
        memory: {
          heapUsed: Math.round(memoryUsage.heapUsed / 1024 / 1024), // MB
          heapTotal: Math.round(memoryUsage.heapTotal / 1024 / 1024), // MB
          external: Math.round(memoryUsage.external / 1024 / 1024), // MB
          rss: Math.round(memoryUsage.rss / 1024 / 1024) // MB
        },
        network: {
          status: networkStatus,
          wifiInterface: config.wifiInterface
        },
        system: {
          hostname: config.hostname,
          nodeVersion: process.version,
          platform: process.platform,
          arch: process.arch,
          isDevelopment
        },
        performance: {
          responseTime: `${responseTime}ms`,
          loadAverage: (() => {
            try {
              const os = require('os')
              return process.platform !== 'win32' && typeof os.loadavg === 'function'
                ? os.loadavg()
                : [0, 0, 0]
            } catch {
              return [0, 0, 0]
            }
          })()
        }
      }
    }
  } catch (error) {
    // Return error status but don't crash
    return {
      success: false,
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error',
      data: {
        uptime: Math.floor(process.uptime()),
        memory: {
          heapUsed: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
          heapTotal: Math.round(process.memoryUsage().heapTotal / 1024 / 1024)
        }
      }
    }
  }
})
