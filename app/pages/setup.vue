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
                WiFi Setup
              </h1>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Configure your WiFi connection
              </p>
            </div>
          </div>
          <button
            @click="handleScanNetworks"
            :disabled="isScanning"
            class="inline-flex items-center px-2 py-2 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg class="w-4 h-4" :class="{ 'animate-spin': isScanning }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-md mx-auto px-4 py-6 space-y-6">
      <!-- Error Display -->
      <div v-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800 dark:text-red-200">
              Connection Error
            </h3>
            <div class="mt-2 text-sm text-red-700 dark:text-red-300">
              <p>{{ error }}</p>
            </div>
            <div class="mt-4">
              <button
                @click="clearError"
                type="button"
                class="bg-red-50 dark:bg-red-900/20 px-2 py-1.5 rounded-md text-sm font-medium text-red-800 dark:text-red-200 hover:bg-red-100 dark:hover:bg-red-900/40 focus:outline-none focus:ring-2 focus:ring-red-600"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Success Message -->
      <div v-if="successMessage" class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-green-800 dark:text-green-200">
              Success
            </h3>
            <div class="mt-2 text-sm text-green-700 dark:text-green-300">
              <p>{{ successMessage }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Current Status -->
      <div v-if="currentStatus" class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Current Status
            </h2>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
              :class="statusBadgeClass">
              {{ statusText }}
            </span>
          </div>

          <div class="space-y-3" v-if="currentStatus.status === 'connected' && currentStatus.ssid">
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Network</span>
              <span class="text-sm text-gray-900 dark:text-white font-mono">
                {{ currentStatus.ssid }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">IP Address</span>
              <span class="text-sm text-gray-900 dark:text-white font-mono">
                {{ currentStatus.ip || 'N/A' }}
              </span>
            </div>
            <div class="flex items-center justify-between" v-if="currentStatus.signal">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Signal Strength</span>
              <div class="flex items-center space-x-2">
                <span class="text-sm text-gray-600 dark:text-gray-400">
                  {{ Math.round(currentStatus.signal) }}%
                </span>
                <div class="flex space-x-0.5">
                  <div v-for="i in 4" :key="i"
                       class="w-1 bg-gray-300 dark:bg-gray-600 rounded-sm"
                       :class="[
                         i <= Math.ceil((currentStatus.signal || 0) / 25) ? 'bg-green-500' : '',
                         i === 1 ? 'h-2' : i === 2 ? 'h-3' : i === 3 ? 'h-4' : 'h-5'
                       ]">
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="text-center py-4">
            <svg class="w-12 h-12 text-gray-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636l-12.728 12.728m0 0L12 12m-6.364 6.364L12 12"></path>
            </svg>
            <p class="text-sm font-medium text-gray-900 dark:text-white mb-1">
              {{ currentStatus.mode === 'hotspot' ? 'Hotspot Mode' : 'Not Connected' }}
            </p>
            <p class="text-xs text-gray-500">
              {{ currentStatus.mode === 'hotspot' ? 'Choose a network below to connect' : 'Choose a network below to connect' }}
            </p>
          </div>
        </div>
      </div>

      <!-- Scanning Status -->
      <div v-if="isScanning" class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6 text-center">
          <div class="inline-block w-6 h-6 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin mx-auto mb-3"></div>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Scanning for WiFi networks...
          </p>
        </div>
      </div>

      <!-- Available Networks -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Available Networks
            </h2>
            <div class="flex items-center space-x-2">
              <span class="text-xs text-gray-500" v-if="lastScanTime">
                {{ formatScanTime(lastScanTime) }}
              </span>
              <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300" v-if="networks.length > 0">
                {{ networks.length }} found
              </span>
            </div>
          </div>

          <!-- No Networks Found -->
          <div v-if="!isScanning && networks.length === 0" class="text-center py-8">
            <svg class="w-12 h-12 text-gray-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
            <p class="text-sm font-medium text-gray-900 dark:text-white mb-1">
              No networks found
            </p>
            <p class="text-xs text-gray-500 mb-4">
              Make sure WiFi is enabled and try scanning again
            </p>
            <button
              @click="handleScanNetworks"
              class="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600"
            >
              Try Again
            </button>
          </div>

          <!-- Networks List -->
          <div v-else-if="!isScanning && networks.length > 0" class="space-y-2">
            <div
              v-for="network in networks"
              :key="network.ssid + network.bssid"
              @click="selectNetwork(network)"
              class="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors"
              :class="{ 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700': selectedNetwork?.ssid === network.ssid }"
            >
              <div class="flex items-center space-x-3">
                <!-- Signal strength icon -->
                <div class="flex flex-col space-y-0.5">
                  <div v-for="i in 4" :key="i"
                       class="w-1 bg-gray-300 dark:bg-gray-600 rounded-sm"
                       :class="[
                         i <= Math.ceil((network.signal || 0) / 25) ? getSignalColor(network.signal) : '',
                         i === 1 ? 'h-1' : i === 2 ? 'h-2' : i === 3 ? 'h-3' : 'h-4'
                       ]">
                  </div>
                </div>
                <div>
                  <div class="flex items-center space-x-2">
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      {{ network.ssid }}
                    </p>
                    <svg v-if="network.security !== 'Open'" class="w-3 h-3 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
                    </svg>
                  </div>
                  <div class="flex items-center space-x-2 text-xs text-gray-500">
                    <span>{{ network.security }}</span>
                    <span>•</span>
                    <span>{{ network.signal }}%</span>
                    <span v-if="network.frequency">•</span>
                    <span v-if="network.frequency">{{ network.frequency }}</span>
                  </div>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <span v-if="network.saved" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                  Saved
                </span>
                <span v-if="network.connected" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  Connected
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Connection Form -->
      <div v-if="selectedNetwork && !selectedNetwork.connected" class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Connect to {{ selectedNetwork.ssid }}
            </h2>
            <button
              @click="selectedNetwork = null"
              class="inline-flex items-center px-2 py-1 text-gray-400 hover:text-gray-600"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>

          <form @submit.prevent="handleConnectToNetwork" class="space-y-4">
            <div v-if="selectedNetwork.security !== 'Open'" class="space-y-2">
              <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Password
              </label>
              <input
                id="password"
                v-model="password"
                type="password"
                placeholder="Enter network password"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
                required
                autocomplete="current-password"
              />
              <p class="text-xs text-gray-500 dark:text-gray-400">
                Security: {{ selectedNetwork.security }}
              </p>
            </div>

            <div v-else class="p-4 bg-green-50 dark:bg-green-900/20 rounded-md">
              <p class="text-sm text-green-800 dark:text-green-200">
                This is an open network and doesn't require a password.
              </p>
            </div>

            <div class="flex space-x-3">
              <button
                type="button"
                @click="selectedNetwork = null"
                class="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-3 px-4 rounded-lg transition-colors duration-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="isConnecting || (selectedNetwork.security !== 'Open' && !password)"
                class="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg v-if="isConnecting" class="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                <svg v-else class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"></path>
                </svg>
                {{ isConnecting ? 'Connecting...' : 'Connect' }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Connected Network Actions -->
      <div v-if="selectedNetwork && selectedNetwork.connected" class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <div class="text-center">
            <div class="w-12 h-12 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center mx-auto mb-3">
              <svg class="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
              </svg>
            </div>
            <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-1">
              Already Connected
            </h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
              You are currently connected to {{ selectedNetwork.ssid }}
            </p>
            <button
              @click="selectedNetwork = null"
              class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
// Meta
definePageMeta({
  title: 'WiFi Setup - Radio WiFi',
  description: 'Configure your WiFi connection'
})

// Reactive state
const networks = ref([])
const currentStatus = ref(null)
const selectedNetwork = ref(null)
const password = ref('')
const error = ref('')
const successMessage = ref('')
const isScanning = ref(false)
const isConnecting = ref(false)
const lastScanTime = ref(null)

// Auto-clear messages
const clearError = () => {
  error.value = ''
}

const clearSuccess = () => {
  successMessage.value = ''
}

const setError = (message) => {
  error.value = message
  setTimeout(clearError, 7000)
}

const setSuccess = (message) => {
  successMessage.value = message
  setTimeout(clearSuccess, 5000)
}

// Computed properties
const statusText = computed(() => {
  if (!currentStatus.value) return 'Unknown'
  const status = currentStatus.value.status
  const mode = currentStatus.value.mode

  if (mode === 'hotspot') return 'Hotspot Mode'
  if (status === 'connected' && currentStatus.value.ssid) return `Connected to ${currentStatus.value.ssid}`
  if (status === 'connecting') return 'Connecting...'
  return 'Disconnected'
})

const statusBadgeClass = computed(() => {
  if (!currentStatus.value) return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
  const status = currentStatus.value.status
  const mode = currentStatus.value.mode

  if (mode === 'hotspot') return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
  if (status === 'connected') return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
  if (status === 'connecting') return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
  return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
})

// Helper functions
const formatScanTime = (time) => {
  if (!time) return 'Never scanned'
  const now = Date.now()
  const diff = Math.floor((now - time) / 1000)
  if (diff < 60) return 'Just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  const hours = Math.floor(diff / 3600)
  return `${hours}h ago`
}

const getSignalColor = (signal) => {
  if (!signal) return 'bg-gray-300 dark:bg-gray-600'
  if (signal >= 75) return 'bg-green-500'
  if (signal >= 50) return 'bg-yellow-500'
  if (signal >= 25) return 'bg-orange-500'
  return 'bg-red-500'
}

// API functions
const fetchWiFiStatus = async () => {
  try {
    const response = await $fetch('/api/wifi/status')
    if (response.success) {
      currentStatus.value = response.data
    } else {
      throw new Error(response.error || 'Failed to get WiFi status')
    }
  } catch (err) {
    console.error('Failed to get WiFi status:', err)
    // Don't show error for status fetch failures
  }
}

const handleScanNetworks = async () => {
  if (isScanning.value) return

  isScanning.value = true
  clearError()

  try {
    const response = await $fetch('/api/wifi/scan', { method: 'POST' })

    if (response.success) {
      networks.value = response.data || []
      lastScanTime.value = Date.now()
      console.log(`Found ${networks.value.length} networks`)
    } else {
      throw new Error(response.error || 'Failed to scan networks')
    }
  } catch (err) {
    console.error('Failed to scan networks:', err)
    const message = err instanceof Error ? err.message : 'Failed to scan for WiFi networks. Please try again.'
    setError(message)
  } finally {
    isScanning.value = false
  }
}

const selectNetwork = (network) => {
  if (network.connected) {
    selectedNetwork.value = network
    return
  }

  selectedNetwork.value = network
  password.value = ''
  clearError()
  clearSuccess()
}

const handleConnectToNetwork = async () => {
  if (!selectedNetwork.value) return

  isConnecting.value = true
  clearError()
  clearSuccess()

  try {
    const payload = {
      ssid: selectedNetwork.value.ssid,
      password: password.value || '',
      security: selectedNetwork.value.security
    }

    const response = await $fetch('/api/wifi/connect', {
      method: 'POST',
      body: payload
    })

    if (response.success) {
      setSuccess(`Connecting to ${selectedNetwork.value.ssid}. The system will switch to client mode.`)
      selectedNetwork.value = null
      password.value = ''

      // Refresh status after a delay
      setTimeout(async () => {
        await fetchWiFiStatus()
      }, 2000)
    } else {
      throw new Error(response.error || 'Failed to connect to network')
    }
  } catch (err) {
    console.error('Failed to connect to network:', err)
    const message = err instanceof Error ? err.message : 'Failed to connect to network. Please check your password and try again.'
    setError(message)
  } finally {
    isConnecting.value = false
  }
}

// Initialize on mount
onMounted(async () => {
  await fetchWiFiStatus()
  if (networks.value.length === 0) {
    await handleScanNetworks()
  }
})

// Head configuration
useHead({
  title: 'WiFi Setup - Radio WiFi Configuration',
  meta: [
    { name: 'description', content: 'Configure your WiFi connection - scan for networks and connect securely' }
  ]
})
</script>
