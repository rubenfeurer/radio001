<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Header -->
    <header class="bg-white dark:bg-gray-800 shadow">
      <div class="radio-container">
        <div class="flex items-center justify-between py-4">
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Icon name="heroicons:radio" class="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 class="text-xl font-bold text-gray-900 dark:text-white">
                Radio WiFi
              </h1>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ config.public.hostname }}.local
              </p>
            </div>
          </div>
          <UButton
            variant="ghost"
            size="sm"
            @click="refreshStatus"
            :loading="isRefreshing"
          >
            <Icon name="heroicons:arrow-path" class="w-4 h-4" />
          </UButton>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="radio-container py-6">
      <!-- Status Card -->
      <UCard class="mb-6">
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Connection Status
            </h2>
            <UBadge
              :color="statusColor"
              :label="statusText"
              size="lg"
            />
          </div>
        </template>

        <div class="space-y-4">
          <!-- Current Connection -->
          <div v-if="wifiStatus.status === 'connected'" class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                Network
              </span>
              <span class="text-sm text-gray-900 dark:text-white font-mono">
                {{ wifiStatus.ssid }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                IP Address
              </span>
              <span class="text-sm text-gray-900 dark:text-white font-mono">
                {{ wifiStatus.ip }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                Signal Strength
              </span>
              <div class="flex items-center space-x-2">
                <SignalStrength :strength="wifiStatus.signal || 0" />
                <span class="text-sm text-gray-600 dark:text-gray-400">
                  {{ wifiStatus.signal }}%
                </span>
              </div>
            </div>
          </div>

          <!-- Hotspot Mode -->
          <div v-else-if="wifiStatus.mode === 'hotspot'" class="space-y-2">
            <div class="flex items-center space-x-2 text-orange-600 dark:text-orange-400">
              <Icon name="heroicons:wifi" class="w-5 h-5" />
              <span class="text-sm font-medium">
                Hotspot Mode Active
              </span>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Connect to "{{ hotspotSSID }}" to configure WiFi
            </p>
          </div>

          <!-- Disconnected -->
          <div v-else class="space-y-2">
            <div class="flex items-center space-x-2 text-red-600 dark:text-red-400">
              <Icon name="heroicons:wifi-slash" class="w-5 h-5" />
              <span class="text-sm font-medium">
                No WiFi Connection
              </span>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Configure WiFi to get started
            </p>
          </div>
        </div>

        <template #footer>
          <div class="flex space-x-3">
            <UButton
              v-if="wifiStatus.status !== 'connected'"
              color="primary"
              block
              @click="navigateTo('/setup')"
            >
              <Icon name="heroicons:cog-6-tooth" class="w-4 h-4 mr-2" />
              Configure WiFi
            </UButton>
            <UButton
              v-else
              variant="outline"
              block
              @click="navigateTo('/setup')"
            >
              <Icon name="heroicons:pencil-square" class="w-4 h-4 mr-2" />
              Change Network
            </UButton>
          </div>
        </template>
      </UCard>

      <!-- System Information -->
      <UCard class="mb-6">
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            System Information
          </h2>
        </template>

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1">
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
              Hostname
            </p>
            <p class="text-sm text-gray-900 dark:text-white font-mono">
              {{ systemStatus.hostname }}
            </p>
          </div>
          <div class="space-y-1">
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
              Uptime
            </p>
            <p class="text-sm text-gray-900 dark:text-white">
              {{ formatUptime(systemStatus.uptime) }}
            </p>
          </div>
          <div class="space-y-1">
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
              Memory Usage
            </p>
            <div class="space-y-1">
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :style="{ width: `${memoryUsagePercent}%` }"
                />
              </div>
              <p class="text-xs text-gray-600 dark:text-gray-400">
                {{ formatBytes(systemStatus.memory.used) }} /
                {{ formatBytes(systemStatus.memory.total) }}
              </p>
            </div>
          </div>
          <div class="space-y-1">
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
              CPU Temperature
            </p>
            <p class="text-sm text-gray-900 dark:text-white">
              {{ systemStatus.cpu.temperature || 'N/A' }}°C
            </p>
          </div>
        </div>
      </UCard>

      <!-- Quick Actions -->
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            Quick Actions
          </h2>
        </template>

        <div class="grid grid-cols-2 gap-3">
          <UButton
            variant="outline"
            @click="scanNetworks"
            :loading="isScanning"
          >
            <Icon name="heroicons:magnifying-glass" class="w-4 h-4 mr-2" />
            Scan Networks
          </UButton>
          <UButton
            variant="outline"
            @click="navigateTo('/status')"
          >
            <Icon name="heroicons:chart-bar" class="w-4 h-4 mr-2" />
            View Details
          </UButton>
          <UButton
            variant="outline"
            @click="restartNetwork"
            :loading="isRestarting"
          >
            <Icon name="heroicons:arrow-path" class="w-4 h-4 mr-2" />
            Restart Network
          </UButton>
          <UButton
            variant="outline"
            @click="navigateTo('/settings')"
          >
            <Icon name="heroicons:cog-6-tooth" class="w-4 h-4 mr-2" />
            Settings
          </UButton>
        </div>
      </UCard>
    </main>

    <!-- Loading Overlay -->
    <div
      v-if="isLoading"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    >
      <UCard class="w-64">
        <div class="text-center py-4">
          <div class="radio-spinner mx-auto mb-3"></div>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            {{ loadingMessage }}
          </p>
        </div>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { WiFiStatus, SystemStatus } from '~/types'

// Meta
definePageMeta({
  title: 'Radio WiFi Dashboard',
  description: 'WiFi configuration dashboard for your Raspberry Pi Radio'
})

// Runtime config
const config = useRuntimeConfig()

// Reactive state
const isLoading = ref(false)
const isRefreshing = ref(false)
const isScanning = ref(false)
const isRestarting = ref(false)
const loadingMessage = ref('')

// System status
const systemStatus = ref<SystemStatus>({
  hostname: config.public.hostname,
  uptime: 0,
  memory: { total: 0, used: 0, free: 0 },
  cpu: { load: 0, temperature: 0 },
  network: {
    wifi: {
      interface: 'wlan0',
      status: 'disconnected',
      mode: 'offline'
    }
  },
  services: {
    avahi: false,
    hostapd: false,
    dnsmasq: false
  }
})

// WiFi status
const wifiStatus = computed(() => systemStatus.value.network.wifi)

// Hotspot SSID from config
const hotspotSSID = computed(() => 'Radio-Setup')

// Status computed properties
const statusColor = computed(() => {
  switch (wifiStatus.value.status) {
    case 'connected': return 'green'
    case 'connecting': return 'yellow'
    case 'scanning': return 'blue'
    case 'failed': return 'red'
    default: return 'gray'
  }
})

const statusText = computed(() => {
  switch (wifiStatus.value.status) {
    case 'connected': return 'Connected'
    case 'connecting': return 'Connecting'
    case 'scanning': return 'Scanning'
    case 'failed': return 'Connection Failed'
    case 'disconnected':
      return wifiStatus.value.mode === 'hotspot' ? 'Hotspot Mode' : 'Disconnected'
    default: return 'Unknown'
  }
})

const memoryUsagePercent = computed(() => {
  const { total, used } = systemStatus.value.memory
  return total > 0 ? Math.round((used / total) * 100) : 0
})

// Utility functions
const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  if (days > 0) return `${days}d ${hours}h`
  if (hours > 0) return `${hours}h ${minutes}m`
  return `${minutes}m`
}

const formatBytes = (bytes: number): string => {
  const sizes = ['B', 'KB', 'MB', 'GB']
  if (bytes === 0) return '0 B'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${Math.round(bytes / Math.pow(1024, i) * 10) / 10} ${sizes[i]}`
}

// API functions
const refreshStatus = async () => {
  isRefreshing.value = true
  try {
    const { data } = await $fetch<{ success: boolean; data: SystemStatus }>('/api/system/status')
    if (data) {
      systemStatus.value = data
    }
  } catch (error) {
    console.error('Failed to refresh status:', error)
    // Show error toast
    const toast = useToast()
    toast.add({
      title: 'Error',
      description: 'Failed to refresh system status',
      color: 'red'
    })
  } finally {
    isRefreshing.value = false
  }
}

const scanNetworks = async () => {
  isScanning.value = true
  try {
    await $fetch('/api/wifi/scan', { method: 'POST' })
    // Navigate to setup page to show results
    await navigateTo('/setup')
  } catch (error) {
    console.error('Failed to scan networks:', error)
  } finally {
    isScanning.value = false
  }
}

const restartNetwork = async () => {
  isRestarting.value = true
  loadingMessage.value = 'Restarting network services...'
  isLoading.value = true

  try {
    await $fetch('/api/system/restart-network', { method: 'POST' })

    // Wait a moment then refresh
    setTimeout(async () => {
      await refreshStatus()
      isLoading.value = false
      loadingMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('Failed to restart network:', error)
    isLoading.value = false
  } finally {
    isRestarting.value = false
  }
}

// Initialize
onMounted(async () => {
  await refreshStatus()

  // Auto-refresh every 30 seconds
  const interval = setInterval(refreshStatus, 30000)

  // Cleanup on unmount
  onUnmounted(() => {
    clearInterval(interval)
  })
})

// Head configuration
useHead({
  title: 'Radio WiFi Dashboard',
  meta: [
    { name: 'description', content: 'WiFi configuration dashboard for your Raspberry Pi Radio' }
  ]
})
</script>
