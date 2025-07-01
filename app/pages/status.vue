<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Header -->
    <header class="bg-white dark:bg-gray-800 shadow">
      <div class="radio-container">
        <div class="flex items-center justify-between py-4">
          <div class="flex items-center space-x-3">
            <UButton
              variant="ghost"
              size="sm"
              @click="navigateTo('/')"
            >
              <Icon name="heroicons:arrow-left" class="w-4 h-4" />
            </UButton>
            <div>
              <h1 class="text-xl font-bold text-gray-900 dark:text-white">
                System Status
              </h1>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Detailed system information
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
    <main class="radio-container py-6 space-y-6">
      <!-- WiFi Status -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              WiFi Status
            </h2>
            <UBadge
              :color="wifiStatusColor"
              :label="wifiStatusText"
              size="sm"
            />
          </div>
        </template>

        <div class="space-y-4">
          <!-- Connection Details -->
          <div v-if="systemStatus?.network.wifi.status === 'connected'" class="grid grid-cols-2 gap-4">
            <div class="space-y-1">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Network</p>
              <p class="text-sm text-gray-900 dark:text-white font-mono">
                {{ systemStatus.network.wifi.ssid }}
              </p>
            </div>
            <div class="space-y-1">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">IP Address</p>
              <p class="text-sm text-gray-900 dark:text-white font-mono">
                {{ systemStatus.network.wifi.ip || 'N/A' }}
              </p>
            </div>
            <div class="space-y-1">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Signal Strength</p>
              <div class="flex items-center space-x-2">
                <SignalStrength :strength="systemStatus.network.wifi.signal || 0" />
                <span class="text-sm text-gray-600 dark:text-gray-400">
                  {{ systemStatus.network.wifi.signal || 0 }}%
                </span>
              </div>
            </div>
            <div class="space-y-1">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Frequency</p>
              <p class="text-sm text-gray-900 dark:text-white">
                {{ systemStatus.network.wifi.frequency || 'N/A' }}
              </p>
            </div>
          </div>

          <!-- Hotspot Mode -->
          <div v-else-if="systemStatus?.network.wifi.mode === 'hotspot'" class="text-center py-4">
            <Icon name="heroicons:wifi" class="w-12 h-12 text-orange-500 mx-auto mb-3" />
            <p class="text-sm font-medium text-gray-900 dark:text-white mb-1">
              Hotspot Mode Active
            </p>
            <p class="text-xs text-gray-500">
              Access Point: {{ hotspotSSID }}
            </p>
          </div>

          <!-- Disconnected -->
          <div v-else class="text-center py-4">
            <Icon name="heroicons:wifi-slash" class="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p class="text-sm font-medium text-gray-900 dark:text-white mb-1">
              No WiFi Connection
            </p>
            <p class="text-xs text-gray-500">
              WiFi interface is not connected
            </p>
          </div>

          <!-- Interface Details -->
          <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1">
                <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Interface</p>
                <p class="text-sm text-gray-900 dark:text-white font-mono">
                  {{ systemStatus?.network.wifi.interface || 'wlan0' }}
                </p>
              </div>
              <div class="space-y-1">
                <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Mode</p>
                <p class="text-sm text-gray-900 dark:text-white capitalize">
                  {{ systemStatus?.network.wifi.mode || 'offline' }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </UCard>

      <!-- System Information -->
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            System Information
          </h2>
        </template>

        <div class="space-y-4">
          <!-- Basic Info -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Hostname</p>
              <p class="text-sm text-gray-900 dark:text-white font-mono">
                {{ systemStatus?.hostname || 'radio' }}
              </p>
            </div>
            <div class="space-y-1">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Uptime</p>
              <p class="text-sm text-gray-900 dark:text-white">
                {{ formatUptime(systemStatus?.uptime || 0) }}
              </p>
            </div>
          </div>

          <!-- Memory Usage -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Memory Usage</p>
              <span class="text-sm text-gray-600 dark:text-gray-400">
                {{ memoryUsagePercent }}%
              </span>
            </div>
            <div class="progress-bar">
              <div
                class="progress-fill"
                :style="{ width: `${memoryUsagePercent}%` }"
                :class="{
                  'bg-red-500': memoryUsagePercent > 90,
                  'bg-yellow-500': memoryUsagePercent > 75 && memoryUsagePercent <= 90,
                  'bg-green-500': memoryUsagePercent <= 75
                }"
              />
            </div>
            <div class="flex justify-between text-xs text-gray-500">
              <span>{{ formatBytes(systemStatus?.memory.used || 0) }} used</span>
              <span>{{ formatBytes(systemStatus?.memory.total || 0) }} total</span>
            </div>
          </div>

          <!-- CPU Information -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">CPU Load</p>
              <p class="text-sm text-gray-900 dark:text-white">
                {{ (systemStatus?.cpu.load || 0).toFixed(2) }}%
              </p>
            </div>
            <div class="space-y-1">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">CPU Temperature</p>
              <p class="text-sm text-gray-900 dark:text-white">
                {{ systemStatus?.cpu.temperature || 'N/A' }}°C
              </p>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Services Status -->
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            Services Status
          </h2>
        </template>

        <div class="space-y-3">
          <div
            v-for="(status, service) in systemStatus?.services"
            :key="service"
            class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
          >
            <div class="flex items-center space-x-3">
              <div
                class="w-3 h-3 rounded-full"
                :class="{
                  'bg-green-500': status,
                  'bg-red-500': !status
                }"
              />
              <span class="text-sm font-medium text-gray-900 dark:text-white capitalize">
                {{ formatServiceName(service) }}
              </span>
            </div>
            <UBadge
              :color="status ? 'green' : 'red'"
              :label="status ? 'Running' : 'Stopped'"
              size="xs"
            />
          </div>
        </div>
      </UCard>

      <!-- Network Interfaces -->
      <UCard v-if="networkInterfaces.length > 0">
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            Network Interfaces
          </h2>
        </template>

        <div class="space-y-3">
          <div
            v-for="interface in networkInterfaces"
            :key="interface.name"
            class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-gray-900 dark:text-white font-mono">
                {{ interface.name }}
              </span>
              <UBadge
                :color="interface.status === 'up' ? 'green' : 'gray'"
                :label="interface.status"
                size="xs"
              />
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs text-gray-500">
              <div>Type: {{ interface.type }}</div>
              <div>IP: {{ interface.ip || 'N/A' }}</div>
              <div v-if="interface.mac">MAC: {{ interface.mac }}</div>
              <div v-if="interface.mtu">MTU: {{ interface.mtu }}</div>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Device Information -->
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            Device Information
          </h2>
        </template>

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1">
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Model</p>
            <p class="text-sm text-gray-900 dark:text-white">
              {{ deviceInfo.model || 'Raspberry Pi' }}
            </p>
          </div>
          <div class="space-y-1">
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Architecture</p>
            <p class="text-sm text-gray-900 dark:text-white">
              {{ deviceInfo.architecture || 'ARM' }}
            </p>
          </div>
          <div class="space-y-1">
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">OS</p>
            <p class="text-sm text-gray-900 dark:text-white">
              {{ deviceInfo.os || 'Linux' }}
            </p>
          </div>
          <div class="space-y-1">
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Kernel</p>
            <p class="text-sm text-gray-900 dark:text-white">
              {{ deviceInfo.kernel || 'N/A' }}
            </p>
          </div>
        </div>
      </UCard>

      <!-- Actions -->
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            System Actions
          </h2>
        </template>

        <div class="grid grid-cols-2 gap-3">
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
            @click="navigateTo('/setup')"
          >
            <Icon name="heroicons:cog-6-tooth" class="w-4 h-4 mr-2" />
            WiFi Setup
          </UButton>
          <UButton
            variant="outline"
            color="red"
            @click="showRebootModal = true"
          >
            <Icon name="heroicons:power" class="w-4 h-4 mr-2" />
            Reboot System
          </UButton>
          <UButton
            variant="outline"
            @click="exportLogs"
            :loading="isExporting"
          >
            <Icon name="heroicons:document-arrow-down" class="w-4 h-4 mr-2" />
            Export Logs
          </UButton>
        </div>
      </UCard>
    </main>

    <!-- Reboot Confirmation Modal -->
    <UModal v-model="showRebootModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Confirm Reboot</h3>
        </template>

        <div class="py-4">
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Are you sure you want to reboot the system? This will temporarily disconnect all network connections.
          </p>
        </div>

        <template #footer>
          <div class="flex justify-end space-x-3">
            <UButton
              variant="outline"
              @click="showRebootModal = false"
            >
              Cancel
            </UButton>
            <UButton
              color="red"
              @click="rebootSystem"
              :loading="isRebooting"
            >
              Reboot
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import type { SystemStatus, NetworkInterface, DeviceInfo } from '~/types'

// Meta
definePageMeta({
  title: 'System Status',
  description: 'Detailed system status and information'
})

// Runtime config
const config = useRuntimeConfig()
const toast = useToast()

// Reactive state
const systemStatus = ref<SystemStatus | null>(null)
const networkInterfaces = ref<NetworkInterface[]>([])
const deviceInfo = ref<DeviceInfo>({
  model: 'Raspberry Pi',
  architecture: 'ARM',
  os: 'Linux',
  kernel: '',
  memory: 0,
  storage: 0,
  interfaces: []
})

const isRefreshing = ref(false)
const isRestarting = ref(false)
const isRebooting = ref(false)
const isExporting = ref(false)
const showRebootModal = ref(false)

// Computed properties
const hotspotSSID = computed(() => config.public.hostname + '-Setup')

const wifiStatusColor = computed(() => {
  if (!systemStatus.value) return 'gray'
  switch (systemStatus.value.network.wifi.status) {
    case 'connected': return 'green'
    case 'connecting': return 'yellow'
    case 'failed': return 'red'
    default: return 'gray'
  }
})

const wifiStatusText = computed(() => {
  if (!systemStatus.value) return 'Unknown'
  const wifi = systemStatus.value.network.wifi
  switch (wifi.status) {
    case 'connected': return 'Connected'
    case 'connecting': return 'Connecting'
    case 'failed': return 'Failed'
    case 'disconnected':
      return wifi.mode === 'hotspot' ? 'Hotspot Mode' : 'Disconnected'
    default: return 'Unknown'
  }
})

const memoryUsagePercent = computed(() => {
  if (!systemStatus.value) return 0
  const { total, used } = systemStatus.value.memory
  return total > 0 ? Math.round((used / total) * 100) : 0
})

// Methods
const refreshStatus = async () => {
  isRefreshing.value = true
  try {
    // Get system status
    const statusResponse = await $fetch<{ success: boolean; data: SystemStatus }>('/api/system/status')
    if (statusResponse.success && statusResponse.data) {
      systemStatus.value = statusResponse.data
    }

    // Get network interfaces
    const interfacesResponse = await $fetch<{ success: boolean; data: NetworkInterface[] }>('/api/system/interfaces')
    if (interfacesResponse.success && interfacesResponse.data) {
      networkInterfaces.value = interfacesResponse.data
    }

    // Get device info
    const deviceResponse = await $fetch<{ success: boolean; data: DeviceInfo }>('/api/system/device-info')
    if (deviceResponse.success && deviceResponse.data) {
      deviceInfo.value = deviceResponse.data
    }
  } catch (error) {
    console.error('Failed to refresh status:', error)
    toast.add({
      title: 'Error',
      description: 'Failed to refresh system status',
      color: 'red'
    })
  } finally {
    isRefreshing.value = false
  }
}

const restartNetwork = async () => {
  isRestarting.value = true
  try {
    const response = await $fetch<{ success: boolean; message: string }>('/api/system/restart-network', {
      method: 'POST'
    })

    if (response.success) {
      toast.add({
        title: 'Success',
        description: 'Network services restarted',
        color: 'green'
      })
      // Refresh status after a delay
      setTimeout(refreshStatus, 3000)
    } else {
      throw new Error(response.message)
    }
  } catch (error) {
    console.error('Failed to restart network:', error)
    toast.add({
      title: 'Error',
      description: 'Failed to restart network services',
      color: 'red'
    })
  } finally {
    isRestarting.value = false
  }
}

const rebootSystem = async () => {
  isRebooting.value = true
  try {
    const response = await $fetch<{ success: boolean; message: string }>('/api/system/reboot', {
      method: 'POST'
    })

    if (response.success) {
      toast.add({
        title: 'Rebooting',
        description: 'System is rebooting...',
        color: 'blue'
      })
      showRebootModal.value = false
    } else {
      throw new Error(response.message)
    }
  } catch (error) {
    console.error('Failed to reboot system:', error)
    toast.add({
      title: 'Error',
      description: 'Failed to reboot system',
      color: 'red'
    })
  } finally {
    isRebooting.value = false
  }
}

const exportLogs = async () => {
  isExporting.value = true
  try {
    const response = await fetch('/api/system/logs', {
      method: 'GET'
    })

    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `radio-logs-${new Date().toISOString().split('T')[0]}.txt`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast.add({
        title: 'Success',
        description: 'System logs exported',
        color: 'green'
      })
    } else {
      throw new Error('Failed to export logs')
    }
  } catch (error) {
    console.error('Failed to export logs:', error)
    toast.add({
      title: 'Error',
      description: 'Failed to export system logs',
      color: 'red'
    })
  } finally {
    isExporting.value = false
  }
}

// Utility functions
const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  if (days > 0) return `${days}d ${hours}h ${minutes}m`
  if (hours > 0) return `${hours}h ${minutes}m`
  return `${minutes}m`
}

const formatBytes = (bytes: number): string => {
  const sizes = ['B', 'KB', 'MB', 'GB']
  if (bytes === 0) return '0 B'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${Math.round(bytes / Math.pow(1024, i) * 10) / 10} ${sizes[i]}`
}

const formatServiceName = (service: string): string => {
  switch (service) {
    case 'avahi': return 'mDNS (Avahi)'
    case 'hostapd': return 'Access Point'
    case 'dnsmasq': return 'DHCP/DNS'
    default: return service
  }
}

// Initialize
onMounted(async () => {
  await refreshStatus()

  // Auto-refresh every 30 seconds
  const interval = setInterval(refreshStatus, 30000)

  onUnmounted(() => {
    clearInterval(interval)
  })
})

// Head configuration
useHead({
  title: 'System Status - Radio',
  meta: [
    { name: 'description', content: 'Detailed system status and information for Radio device' }
  ]
})
</script>

<style scoped>
.radio-container {
  @apply max-w-2xl mx-auto px-4;
}

.progress-bar {
  @apply w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden;
}

.progress-fill {
  @apply h-full transition-all duration-300 ease-out;
}
</style>
