<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Header -->
    <header class="bg-white dark:bg-gray-800 shadow">
      <div class="max-w-md mx-auto px-4">
        <div class="flex items-center justify-between py-4">
          <div class="flex items-center space-x-3">
            <button
              @click="navigateTo('/')"
              class="inline-flex items-center px-2 py-2 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
              </svg>
            </button>
            <div>
              <h1 class="text-xl font-bold text-gray-900 dark:text-white">
                System Status
              </h1>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Detailed system information
              </p>
            </div>
          </div>
          <button
            @click="refreshStatus"
            :disabled="isRefreshing"
            class="inline-flex items-center px-2 py-2 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600 disabled:opacity-50"
          >
            <svg class="w-4 h-4" :class="{ 'animate-spin': isRefreshing }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-md mx-auto px-4 py-6 space-y-6">
      <!-- WiFi Status -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              WiFi Status
            </h2>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
              :class="wifiStatusColor">
              {{ wifiStatusText }}
            </span>
          </div>

          <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div class="space-y-1">
                <p class="font-medium text-gray-700 dark:text-gray-300">Interface</p>
                <p class="text-gray-900 dark:text-white font-mono">
                  {{ systemStatus?.network.wifi.wifiInterface || 'wlan0' }}
                </p>
              </div>
              <div class="space-y-1">
                <p class="font-medium text-gray-700 dark:text-gray-300">Mode</p>
                <p class="text-gray-900 dark:text-white">
                  {{ systemStatus?.network.wifi.mode || 'Unknown' }}
                </p>
              </div>
              <div class="space-y-1" v-if="systemStatus?.network.wifi.ssid">
                <p class="font-medium text-gray-700 dark:text-gray-300">Network</p>
                <p class="text-gray-900 dark:text-white font-mono">
                  {{ systemStatus.network.wifi.ssid }}
                </p>
              </div>
              <div class="space-y-1" v-if="systemStatus?.network.wifi.ip">
                <p class="font-medium text-gray-700 dark:text-gray-300">IP Address</p>
                <p class="text-gray-900 dark:text-white font-mono">
                  {{ systemStatus.network.wifi.ip }}
                </p>
              </div>
              <div class="space-y-1" v-if="systemStatus?.network.wifi.signal">
                <p class="font-medium text-gray-700 dark:text-gray-300">Signal</p>
                <p class="text-gray-900 dark:text-white">
                  {{ systemStatus.network.wifi.signal }}%
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- System Information -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            System Information
          </h2>

          <div class="grid grid-cols-2 gap-4 text-sm">
            <div class="space-y-1">
              <p class="font-medium text-gray-700 dark:text-gray-300">Hostname</p>
              <p class="text-gray-900 dark:text-white font-mono">
                {{ systemStatus?.hostname || 'radio' }}
              </p>
            </div>
            <div class="space-y-1">
              <p class="font-medium text-gray-700 dark:text-gray-300">Uptime</p>
              <p class="text-gray-900 dark:text-white">
                {{ formatUptime(systemStatus?.uptime || 0) }}
              </p>
            </div>
            <div class="space-y-1 col-span-2">
              <p class="font-medium text-gray-700 dark:text-gray-300">Memory Usage</p>
              <div class="space-y-2">
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    class="h-full bg-blue-600 rounded-full transition-all duration-300"
                    :style="{ width: memoryUsagePercent + '%' }"
                  ></div>
                </div>
                <p class="text-xs text-gray-600 dark:text-gray-400">
                  {{ formatBytes(systemStatus?.memory?.used || 0) }} / {{ formatBytes(systemStatus?.memory?.total || 0) }}
                  ({{ memoryUsagePercent }}%)
                </p>
              </div>
            </div>
            <div class="space-y-1" v-if="systemStatus?.cpu?.temperature">
              <p class="font-medium text-gray-700 dark:text-gray-300">CPU Temperature</p>
              <p class="text-gray-900 dark:text-white">
                {{ systemStatus.cpu.temperature }}°C
              </p>
            </div>
            <div class="space-y-1">
              <p class="font-medium text-gray-700 dark:text-gray-300">CPU Load</p>
              <p class="text-gray-900 dark:text-white">
                {{ systemStatus?.cpu?.load || 0 }}%
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Services Status -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Services Status
          </h2>

          <div class="space-y-3">
            <div
              v-for="(status, service) in servicesStatus"
              :key="service"
              class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
            >
              <div>
                <span class="text-sm font-medium text-gray-900 dark:text-white capitalize">
                  {{ service.replace('-', ' ') }}
                </span>
              </div>
              <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                :class="status ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'">
                {{ status ? 'Running' : 'Stopped' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Network Interfaces -->
      <div v-if="networkInterfaces.length > 0" class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Network Interfaces
          </h2>

          <div class="space-y-3">
            <div
              v-for="netInterface in networkInterfaces"
              :key="netInterface.name"
              class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-900 dark:text-white font-mono">
                  {{ netInterface.name }}
                </span>
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                  :class="netInterface.status === 'up' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'">
                  {{ netInterface.status }}
                </span>
              </div>
              <div class="grid grid-cols-2 gap-2 text-xs text-gray-500">
                <div>Type: {{ netInterface.type }}</div>
                <div>IP: {{ netInterface.ip || 'N/A' }}</div>
                <div v-if="netInterface.mac">MAC: {{ netInterface.mac }}</div>
                <div v-if="netInterface.mtu">MTU: {{ netInterface.mtu }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Device Information -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Device Information
          </h2>

          <div class="grid grid-cols-2 gap-4 text-sm">
            <div class="space-y-1">
              <p class="font-medium text-gray-700 dark:text-gray-300">Model</p>
              <p class="text-gray-900 dark:text-white">
                {{ deviceInfo?.model || 'Raspberry Pi' }}
              </p>
            </div>
            <div class="space-y-1">
              <p class="font-medium text-gray-700 dark:text-gray-300">Architecture</p>
              <p class="text-gray-900 dark:text-white">
                {{ deviceInfo?.architecture || 'arm64' }}
              </p>
            </div>
            <div class="space-y-1">
              <p class="font-medium text-gray-700 dark:text-gray-300">OS</p>
              <p class="text-gray-900 dark:text-white">
                {{ deviceInfo?.os || 'Linux' }}
              </p>
            </div>
            <div class="space-y-1">
              <p class="font-medium text-gray-700 dark:text-gray-300">Kernel</p>
              <p class="text-gray-900 dark:text-white">
                {{ deviceInfo?.kernel || 'Unknown' }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            System Actions
          </h2>

          <div class="grid grid-cols-2 gap-3">
            <button
              @click="restartNetwork"
              :disabled="isLoading"
              class="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600 disabled:opacity-50"
            >
              <svg class="w-4 h-4 mr-2" :class="{ 'animate-spin': isLoading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              Restart Network
            </button>

            <button
              @click="navigateTo('/setup')"
              class="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
              </svg>
              WiFi Setup
            </button>

            <button
              @click="confirmReboot"
              :disabled="isLoading"
              class="flex items-center justify-center px-4 py-3 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-white hover:bg-red-50 focus:ring-2 focus:ring-red-500 dark:bg-gray-700 dark:border-red-600 dark:text-red-300 dark:hover:bg-red-900 disabled:opacity-50"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.636 5.636a9 9 0 1012.728 0M12 3v9"></path>
              </svg>
              Reboot System
            </button>

            <button
              @click="exportLogs"
              :disabled="isLoading"
              class="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600 disabled:opacity-50"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
              Export Logs
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Reboot Confirmation Modal -->
    <div v-if="showRebootModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 transition-opacity" aria-hidden="true">
          <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div class="sm:flex sm:items-start">
              <div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                <svg class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L5.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                <h3 class="text-lg leading-6 font-medium text-gray-900">
                  Confirm Reboot
                </h3>
                <div class="mt-2">
                  <p class="text-sm text-gray-500">
                    Are you sure you want to reboot the system? This will temporarily disconnect all network connections.
                  </p>
                </div>
              </div>
            </div>
          </div>
          <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              @click="rebootSystem"
              type="button"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Reboot Now
            </button>
            <button
              @click="showRebootModal = false"
              type="button"
              class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SystemStatus, NetworkInterface, DeviceInfo } from '~/types'

// Meta
useHead({
  title: 'System Status - Radio WiFi'
})

// Reactive state
const systemStatus = ref<SystemStatus | null>(null)
const networkInterfaces = ref<NetworkInterface[]>([])
const deviceInfo = ref<DeviceInfo | null>(null)
const servicesStatus = ref<Record<string, boolean>>({
  'hostapd': false,
  'dnsmasq': false,
  'wpa-supplicant': false
})

// UI state
const isLoading = ref(false)
const isRefreshing = ref(false)
const showRebootModal = ref(false)

// Computed properties
const wifiStatusText = computed(() => {
  if (!systemStatus.value?.network?.wifi) return 'Unknown'
  const wifi = systemStatus.value.network.wifi
  return wifi.status === 'connected' ? `Connected${wifi.ssid ? ` to ${wifi.ssid}` : ''}` : 'Disconnected'
})

const wifiStatusColor = computed(() => {
  const status = systemStatus.value?.network?.wifi?.status
  if (status === 'connected') return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
  if (status === 'connecting') return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
  return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
})

const memoryUsagePercent = computed(() => {
  if (!systemStatus.value?.memory) return 0
  const { used, total } = systemStatus.value.memory
  return Math.round((used / total) * 100)
})

// Helper functions
const formatUptime = (seconds: number): string => {
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
  return `${Math.floor(seconds / 86400)}d ${Math.floor((seconds % 86400) / 3600)}h`
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// API functions
const fetchSystemStatus = async () => {
  try {
    const response = await $fetch('/api/system/status')
    if (response.success && 'data' in response) {
      systemStatus.value = response.data
    } else if (!response.success && 'error' in response) {
      throw new Error(response.error || 'Failed to fetch system status')
    }
  } catch (error) {
    console.error('Failed to fetch system status:', error)
    showNotification('Failed to fetch system status', 'error')
  }
}

const fetchServicesStatus = async () => {
  try {
    // Services status is included in system status
    if (systemStatus.value?.services) {
      servicesStatus.value = systemStatus.value.services
    }
  } catch (error) {
    console.error('Failed to fetch services status:', error)
  }
}

const fetchNetworkInterfaces = async () => {
  try {
    // Create network interfaces from system status
    const interfaces: NetworkInterface[] = []

    if (systemStatus.value?.network?.wifi) {
      const wifi = systemStatus.value.network.wifi
      interfaces.push({
        name: wifi.wifiInterface || 'wlan0',
        type: 'wifi',
        status: wifi.status === 'connected' || wifi.status === 'connecting' ? 'up' : 'down',
        ip: wifi.ip,
        mac: undefined,
        mtu: 1500
      })
    }

    if (systemStatus.value?.network?.ethernet) {
      const eth = systemStatus.value.network.ethernet
      interfaces.push({
        name: 'eth0',
        type: 'ethernet',
        status: eth.connected ? 'up' : 'down',
        ip: eth.ip,
        mac: undefined,
        mtu: 1500
      })
    }

    networkInterfaces.value = interfaces
  } catch (error) {
    console.error('Failed to fetch network interfaces:', error)
  }
}

const fetchDeviceInfo = async () => {
  try {
    // Device info from system status and config
    deviceInfo.value = {
      model: 'Raspberry Pi Zero 2 W',
      architecture: 'arm64',
      os: 'Linux',
      kernel: '6.1.0+',
      memory: Math.round((systemStatus.value?.memory?.total || 1073741824) / (1024 * 1024)),
      storage: 32,
      interfaces: networkInterfaces.value
    }
  } catch (error) {
    console.error('Failed to fetch device info:', error)
  }
}

// Action handlers
const refreshStatus = async () => {
  isRefreshing.value = true
  try {
    await fetchSystemStatus()
    await fetchServicesStatus()
    await fetchNetworkInterfaces()
    await fetchDeviceInfo()
    showNotification('Status refreshed successfully', 'success')
  } catch (error) {
    console.error('Failed to refresh status:', error)
    showNotification('Failed to refresh status', 'error')
  } finally {
    isRefreshing.value = false
  }
}

const restartNetwork = async () => {
  isLoading.value = true
  try {
    const response = await $fetch('/api/system/restart-network', { method: 'POST' })
    if (response.success) {
      showNotification('Network restart initiated', 'success')
      setTimeout(refreshStatus, 5000) // Refresh after 5 seconds
    } else if (!response.success && 'error' in response) {
      throw new Error(response.error || 'Failed to restart network')
    }
  } catch (error) {
    console.error('Failed to restart network:', error)
    showNotification('Failed to restart network', 'error')
  } finally {
    isLoading.value = false
  }
}

const confirmReboot = () => {
  showRebootModal.value = true
}

const rebootSystem = async () => {
  isLoading.value = true
  try {
    const response = await $fetch('/api/system/reset', { method: 'POST' })
    if (response.success) {
      showNotification('System reboot initiated', 'success')
      showRebootModal.value = false
    } else if (!response.success && 'error' in response) {
      throw new Error(response.error || 'Failed to reboot system')
    }
  } catch (error) {
    console.error('Failed to reboot system:', error)
    showNotification('Failed to reboot system', 'error')
  } finally {
    isLoading.value = false
  }
}

const exportLogs = async () => {
  isLoading.value = true
  try {
    // Mock log export for now
    const logs = 'Mock system logs...'
    const blob = new Blob([logs], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `radio-logs-${new Date().toISOString().split('T')[0]}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    showNotification('Logs exported successfully', 'success')
  } catch (error) {
    console.error('Failed to export logs:', error)
    showNotification('Failed to export logs', 'error')
  } finally {
    isLoading.value = false
  }
}

// Simple notification system (since we removed useToast)
const showNotification = (message: string, type: 'success' | 'error') => {
  // For now, just log to console. In a real app, you might want to implement a toast system
  console.log(`${type.toUpperCase()}: ${message}`)
}

// Initialize data on mount
onMounted(() => {
  refreshStatus()
})
</script>
