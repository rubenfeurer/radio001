// WiFi management composable for Radio WiFi Configuration
// Provides reactive WiFi state management and API integration

import type { WiFiNetwork, WiFiCredentials, SystemStatus, ApiResponse } from '~/types'

export const useWiFi = () => {
  // Reactive state
  const networks = ref<WiFiNetwork[]>([])
  const status = ref<SystemStatus | null>(null)
  const isScanning = ref(false)
  const isConnecting = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastScanTime = ref<number | null>(null)

  // Configuration
  const config = useRuntimeConfig()

  // Clear error after a delay
  const clearError = () => {
    setTimeout(() => {
      error.value = null
    }, 5000)
  }

  // Set error with auto-clear
  const setError = (message: string) => {
    error.value = message
    clearError()
  }

  // Scan for WiFi networks
  const scanNetworks = async () => {
    if (isScanning.value) return

    isScanning.value = true
    error.value = null

    try {
      const response = await $fetch<ApiResponse>('/api/wifi/scan', {
        method: 'POST'
      })

      if (response.success && response.data) {
        networks.value = response.data as WiFiNetwork[]
        lastScanTime.value = Date.now()
      } else {
        throw new Error(response.message || 'Failed to scan networks')
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Network scan failed'
      setError(message)
      console.error('WiFi scan error:', err)
    } finally {
      isScanning.value = false
    }
  }

  // Connect to a WiFi network
  const connectToNetwork = async (credentials: WiFiCredentials) => {
    if (isConnecting.value) return false

    isConnecting.value = true
    error.value = null

    try {
      const response = await $fetch<ApiResponse>('/api/wifi/connect', {
        method: 'POST',
        body: credentials
      })

      if (response.success) {
        // Update status to show connecting
        if (status.value) {
          status.value.network.wifi.status = 'connecting'
          status.value.network.wifi.ssid = credentials.ssid
        }
        return true
      } else {
        throw new Error(response.message || 'Connection failed')
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Connection failed'
      setError(message)
      console.error('WiFi connection error:', err)
      return false
    } finally {
      isConnecting.value = false
    }
  }

  // Get current WiFi status
  const getStatus = async () => {
    isLoading.value = true
    error.value = null

    try {
      const response = await $fetch<ApiResponse>('/api/wifi/status')

      if (response.success && response.data) {
        status.value = response.data as SystemStatus
      } else {
        throw new Error(response.message || 'Failed to get status')
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Status check failed'
      setError(message)
      console.error('WiFi status error:', err)
    } finally {
      isLoading.value = false
    }
  }

  // Reset to hotspot mode
  const resetToHotspot = async () => {
    isLoading.value = true
    error.value = null

    try {
      const response = await $fetch<ApiResponse>('/api/system/reset', {
        method: 'POST'
      })

      if (response.success) {
        // Update status to show hotspot mode
        if (status.value) {
          status.value.network.wifi.mode = 'hotspot'
          status.value.network.wifi.status = 'disconnected'
        }
        return true
      } else {
        throw new Error(response.message || 'Reset failed')
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Reset failed'
      setError(message)
      console.error('WiFi reset error:', err)
      return false
    } finally {
      isLoading.value = false
    }
  }

  // Auto-refresh status
  const startStatusPolling = (interval = 30000) => {
    const poll = async () => {
      if (!isConnecting.value && !isLoading.value) {
        await getStatus()
      }
    }

    // Initial status check
    poll()

    // Set up polling
    const intervalId = setInterval(poll, interval)

    // Return cleanup function
    return () => clearInterval(intervalId)
  }

  // Get network by SSID
  const getNetworkBySSID = (ssid: string) => {
    return networks.value.find(network => network.ssid === ssid)
  }

  // Check if network requires password
  const requiresPassword = (network: WiFiNetwork) => {
    return network.security !== 'Open'
  }

  // Format signal strength for display
  const getSignalIcon = (signal: number | undefined) => {
    if (!signal) return 'heroicons:wifi-slash'

    if (signal >= 75) return 'heroicons:wifi'
    if (signal >= 50) return 'heroicons:wifi'
    if (signal >= 25) return 'heroicons:wifi'
    return 'heroicons:wifi'
  }

  // Get signal strength color
  const getSignalColor = (signal: number | undefined) => {
    if (!signal) return 'text-gray-400'

    if (signal >= 75) return 'text-green-500'
    if (signal >= 50) return 'text-yellow-500'
    if (signal >= 25) return 'text-orange-500'
    return 'text-red-500'
  }

  // Check if scan is outdated
  const isScanOutdated = computed(() => {
    if (!lastScanTime.value) return true
    return Date.now() - lastScanTime.value > 60000 // 1 minute
  })

  // Current network info
  const currentNetwork = computed(() => {
    if (!status.value?.network.wifi.ssid) return null
    return getNetworkBySSID(status.value.network.wifi.ssid)
  })

  // Connection state
  const isConnected = computed(() => {
    return status.value?.network.wifi.status === 'connected'
  })

  const isInHotspotMode = computed(() => {
    return status.value?.network.wifi.mode === 'hotspot'
  })

  // Initialize on mount
  onMounted(() => {
    getStatus()
  })

  return {
    // State
    networks: readonly(networks),
    status: readonly(status),
    isScanning: readonly(isScanning),
    isConnecting: readonly(isConnecting),
    isLoading: readonly(isLoading),
    error: readonly(error),
    lastScanTime: readonly(lastScanTime),

    // Actions
    scanNetworks,
    connectToNetwork,
    getStatus,
    resetToHotspot,
    startStatusPolling,

    // Utilities
    getNetworkBySSID,
    requiresPassword,
    getSignalIcon,
    getSignalColor,

    // Computed
    isScanOutdated,
    currentNetwork,
    isConnected,
    isInHotspotMode,

    // Manual state management
    clearError,
    setError
  }
}

// Provide global WiFi state management
export const useGlobalWiFi = () => {
  return useWiFi()
}
