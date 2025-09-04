<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Header -->
    <header class="bg-white dark:bg-gray-800 shadow">
      <div class="max-w-md mx-auto px-4">
        <div class="flex items-center justify-between py-4">
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"></path>
              </svg>
            </div>
            <div>
              <h1 class="text-xl font-bold text-gray-900 dark:text-white">
                Radio WiFi
              </h1>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                radio.local
              </p>
            </div>
          </div>
          <button
            @click="refreshStatus"
            :disabled="isRefreshing"
            class="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600 disabled:opacity-50"
          >
            <svg class="w-4 h-4" :class="{ 'animate-spin': isRefreshing }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-md mx-auto px-4 py-6">
      <!-- Status Card -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 mb-6">
        <div class="p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Connection Status
            </h2>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
              {{ statusText }}
            </span>
          </div>

          <div class="space-y-4">
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Network
                </span>
                <span class="text-sm text-gray-900 dark:text-white font-mono">
                  {{ currentNetwork }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                  IP Address
                </span>
                <span class="text-sm text-gray-900 dark:text-white font-mono">
                  {{ currentIP }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Signal Strength
                </span>
                <span class="text-sm text-gray-600 dark:text-gray-400">
                  {{ signalStrength }}%
                </span>
              </div>
            </div>
          </div>

          <div class="mt-6">
            <button
              @click="goToSetup"
              class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
              </svg>
              Configure WiFi
            </button>
          </div>
        </div>
      </div>

      <!-- System Information -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 mb-6">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            System Information
          </h2>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
                Hostname
              </p>
              <p class="text-sm text-gray-900 dark:text-white font-mono">
                {{ hostname }}
              </p>
            </div>
            <div class="space-y-1">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
                Uptime
              </p>
              <p class="text-sm text-gray-900 dark:text-white">
                {{ uptime }}
              </p>
            </div>
            <div class="space-y-1">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
                Memory Usage
              </p>
              <div class="space-y-1">
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                  <div class="h-full bg-blue-600 transition-all duration-300 ease-out" :style="{ width: memoryPercent + '%' }"></div>
                </div>
                <p class="text-xs text-gray-600 dark:text-gray-400">
                  {{ memoryUsed }}MB / {{ memoryTotal }}MB
                </p>
              </div>
            </div>
            <div class="space-y-1">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
                CPU Temperature
              </p>
              <p class="text-sm text-gray-900 dark:text-white">
                {{ cpuTemp }}°C
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Quick Actions
          </h2>

          <div class="grid grid-cols-2 gap-3">
            <button
              @click="scanNetworks"
              :disabled="isScanning"
              class="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600 disabled:opacity-50"
            >
              <svg class="w-4 h-4 mr-2" :class="{ 'animate-spin': isScanning }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
              Scan Networks
            </button>
            <button
              @click="goToStatus"
              class="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
              </svg>
              View Details
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Loading Overlay -->
    <div
      v-if="isLoading"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 w-64">
        <div class="text-center">
          <div class="inline-block w-6 h-6 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin mx-auto mb-3"></div>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            {{ loadingMessage }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Meta
definePageMeta({
  title: 'Radio WiFi Dashboard',
  description: 'WiFi configuration dashboard for your Raspberry Pi Radio'
})

// Reactive state
const isLoading = ref(false)
const isRefreshing = ref(false)
const isScanning = ref(false)
const loadingMessage = ref('')

// Mock data for development
const statusText = ref('Connected')
const currentNetwork = ref('HomeWiFi')
const currentIP = ref('192.168.1.100')
const signalStrength = ref(85)
const hostname = ref('radio')
const uptime = ref('2h 15m')
const memoryPercent = ref(45)
const memoryUsed = ref(230)
const memoryTotal = ref(512)
const cpuTemp = ref(42)

// Methods
const refreshStatus = async () => {
  isRefreshing.value = true
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    console.log('Status refreshed')
  } catch (error) {
    console.error('Failed to refresh status:', error)
  } finally {
    isRefreshing.value = false
  }
}

const scanNetworks = async () => {
  isScanning.value = true
  try {
    // Simulate network scan
    await new Promise(resolve => setTimeout(resolve, 2000))
    await navigateTo('/setup')
  } catch (error) {
    console.error('Failed to scan networks:', error)
  } finally {
    isScanning.value = false
  }
}

const goToSetup = () => {
  navigateTo('/setup')
}

const goToStatus = () => {
  navigateTo('/status')
}

// Initialize on mount
onMounted(async () => {
  await refreshStatus()
})

// Head configuration
useHead({
  title: 'Radio WiFi Dashboard',
  meta: [
    { name: 'description', content: 'WiFi configuration dashboard for your Raspberry Pi Radio' }
  ]
})
</script>
