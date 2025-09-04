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
                Settings
              </h1>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Configure device preferences
              </p>
            </div>
          </div>
          <button
            v-if="hasUnsavedChanges"
            @click="saveSettings"
            :disabled="isSaving"
            class="inline-flex items-center px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="isSaving" class="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            {{ isSaving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-md mx-auto px-4 py-6 space-y-6">
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
              Settings Saved
            </h3>
            <div class="mt-2 text-sm text-green-700 dark:text-green-300">
              <p>{{ successMessage }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800 dark:text-red-200">
              Error
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

      <!-- Device Settings -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            Device Settings
          </h2>

          <div class="space-y-6">
            <!-- Hostname -->
            <div>
              <label for="hostname" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Device Hostname
              </label>
              <input
                id="hostname"
                v-model="settings.hostname"
                type="text"
                placeholder="radio"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
                maxlength="63"
                pattern="[a-zA-Z0-9-]+"
                @input="checkChanges"
              />
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Used for mDNS discovery ({{ settings.hostname }}.local)
              </p>
            </div>

            <!-- Theme -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Theme
              </label>
              <div class="space-y-2">
                <label class="flex items-center">
                  <input
                    v-model="settings.theme"
                    type="radio"
                    value="light"
                    class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600"
                    @change="checkChanges"
                  />
                  <span class="ml-2 text-sm text-gray-900 dark:text-white">Light</span>
                </label>
                <label class="flex items-center">
                  <input
                    v-model="settings.theme"
                    type="radio"
                    value="dark"
                    class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600"
                    @change="checkChanges"
                  />
                  <span class="ml-2 text-sm text-gray-900 dark:text-white">Dark</span>
                </label>
                <label class="flex items-center">
                  <input
                    v-model="settings.theme"
                    type="radio"
                    value="system"
                    class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600"
                    @change="checkChanges"
                  />
                  <span class="ml-2 text-sm text-gray-900 dark:text-white">System</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- WiFi Settings -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            WiFi Settings
          </h2>

          <div class="space-y-6">
            <!-- Auto-connect -->
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-sm font-medium text-gray-900 dark:text-white">
                  Auto-connect to saved networks
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  Automatically connect to known networks on startup
                </p>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input
                  v-model="settings.autoConnect"
                  type="checkbox"
                  class="sr-only peer"
                  @change="checkChanges"
                />
                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <!-- Scan Interval -->
            <div>
              <label for="scanInterval" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Network Scan Interval (seconds)
              </label>
              <input
                id="scanInterval"
                v-model.number="settings.scanInterval"
                type="number"
                min="10"
                max="300"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                @input="checkChanges"
              />
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                How often to scan for available networks (10-300 seconds)
              </p>
            </div>

            <!-- Connection Timeout -->
            <div>
              <label for="connectionTimeout" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Connection Timeout (seconds)
              </label>
              <input
                id="connectionTimeout"
                v-model.number="settings.connectionTimeout"
                type="number"
                min="10"
                max="120"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                @input="checkChanges"
              />
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Maximum time to wait for WiFi connection (10-120 seconds)
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Hotspot Settings -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            Hotspot Settings
          </h2>

          <div class="space-y-6">
            <!-- SSID -->
            <div>
              <label for="hotspotSsid" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Hotspot SSID
              </label>
              <input
                id="hotspotSsid"
                v-model="settings.hotspotSsid"
                type="text"
                placeholder="Radio-Setup"
                maxlength="32"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
                @input="checkChanges"
              />
            </div>

            <!-- Password -->
            <div>
              <label for="hotspotPassword" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Hotspot Password
              </label>
              <input
                id="hotspotPassword"
                v-model="settings.hotspotPassword"
                type="password"
                placeholder="Enter password"
                minlength="8"
                maxlength="63"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
                @input="checkChanges"
              />
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Minimum 8 characters for WPA2 security
              </p>
            </div>

            <!-- Channel -->
            <div>
              <label for="hotspotChannel" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                WiFi Channel
              </label>
              <select
                id="hotspotChannel"
                v-model.number="settings.hotspotChannel"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                @change="checkChanges"
              >
                <option v-for="channel in [1, 6, 11]" :key="channel" :value="channel">
                  Channel {{ channel }} ({{ channel === 1 ? '2.412' : channel === 6 ? '2.437' : '2.462' }} GHz)
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Advanced Settings -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            Advanced Settings
          </h2>

          <div class="space-y-6">
            <!-- Enable Captive Portal -->
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-sm font-medium text-gray-900 dark:text-white">
                  Enable Captive Portal
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  Automatically redirect users to setup page in hotspot mode
                </p>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input
                  v-model="settings.captivePortal"
                  type="checkbox"
                  class="sr-only peer"
                  @change="checkChanges"
                />
                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <!-- Debug Mode -->
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-sm font-medium text-gray-900 dark:text-white">
                  Debug Mode
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  Enable detailed logging for troubleshooting
                </p>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input
                  v-model="settings.debugMode"
                  type="checkbox"
                  class="sr-only peer"
                  @change="checkChanges"
                />
                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Reset Settings -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Reset Settings
          </h2>
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Reset all settings to their default values. This action cannot be undone.
          </p>
          <button
            @click="confirmReset"
            class="inline-flex items-center px-4 py-2 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-white hover:bg-red-50 focus:ring-2 focus:ring-red-500 dark:bg-gray-700 dark:border-red-600 dark:text-red-300 dark:hover:bg-red-900"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Reset to Defaults
          </button>
        </div>
      </div>
    </main>

    <!-- Reset Confirmation Modal -->
    <div v-if="showResetModal" class="fixed inset-0 z-50 overflow-y-auto">
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
                  Reset Settings
                </h3>
                <div class="mt-2">
                  <p class="text-sm text-gray-500">
                    Are you sure you want to reset all settings to their default values? This action cannot be undone.
                  </p>
                </div>
              </div>
            </div>
          </div>
          <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              @click="resetSettings"
              type="button"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Reset Settings
            </button>
            <button
              @click="showResetModal = false"
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
// Meta
definePageMeta({
  title: 'Settings - Radio WiFi Configuration',
  description: 'Configure device preferences and WiFi settings'
})

// Reactive state
const settings = ref({
  // Device settings
  hostname: 'radio',
  theme: 'system',

  // WiFi settings
  autoConnect: true,
  scanInterval: 60,
  connectionTimeout: 30,

  // Hotspot settings
  hotspotSsid: 'Radio-Setup',
  hotspotPassword: 'radio123',
  hotspotChannel: 6,

  // Advanced settings
  captivePortal: true,
  debugMode: false
})

const originalSettings = ref(null)
const hasUnsavedChanges = ref(false)
const isSaving = ref(false)
const error = ref('')
const successMessage = ref('')
const showResetModal = ref(false)

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

// Check for changes
const checkChanges = () => {
  if (!originalSettings.value) return

  hasUnsavedChanges.value = JSON.stringify(settings.value) !== JSON.stringify(originalSettings.value)
}

// Load settings from API
const loadSettings = async () => {
  try {
    const response = await $fetch('/api/config')
    if (response.success && response.data) {
      // Map API response to our settings structure
      const config = response.data
      settings.value = {
        hostname: config.hostname || 'radio',
        theme: config.theme || 'system',
        autoConnect: config.features?.autoConnect ?? true,
        scanInterval: config.scanInterval || 60,
        connectionTimeout: config.connectionTimeout || 30,
        hotspotSsid: config.hotspot?.ssid || 'Radio-Setup',
        hotspotPassword: config.hotspot?.password || 'radio123',
        hotspotChannel: config.hotspot?.channel || 6,
        captivePortal: config.features?.captivePortal ?? true,
        debugMode: config.features?.monitoring ?? false
      }
    }

    // Store original settings for comparison
    originalSettings.value = JSON.parse(JSON.stringify(settings.value))
  } catch (err) {
    console.error('Failed to load settings:', err)
    // Keep default values
    originalSettings.value = JSON.parse(JSON.stringify(settings.value))
  }
}

// Save settings to API
const saveSettings = async () => {
  if (!hasUnsavedChanges.value) return

  isSaving.value = true
  clearError()
  clearSuccess()

  try {
    // Map our settings to API format
    const config = {
      hostname: settings.value.hostname,
      theme: settings.value.theme,
      scanInterval: settings.value.scanInterval,
      connectionTimeout: settings.value.connectionTimeout,
      hotspot: {
        ssid: settings.value.hotspotSsid,
        password: settings.value.hotspotPassword,
        channel: settings.value.hotspotChannel
      },
      features: {
        autoConnect: settings.value.autoConnect,
        captivePortal: settings.value.captivePortal,
        monitoring: settings.value.debugMode
      }
    }

    const response = await $fetch('/api/config', {
      method: 'POST',
      body: config
    })

    if (response.success) {
      originalSettings.value = JSON.parse(JSON.stringify(settings.value))
      hasUnsavedChanges.value = false
      setSuccess('Settings saved successfully. Some changes may require a system restart.')
    } else {
      throw new Error(response.error || 'Failed to save settings')
    }
  } catch (err) {
    console.error('Failed to save settings:', err)
    const message = err instanceof Error ? err.message : 'Failed to save settings. Please try again.'
    setError(message)
  } finally {
    isSaving.value = false
  }
}

// Reset settings
const confirmReset = () => {
  showResetModal.value = true
}

const resetSettings = async () => {
  showResetModal.value = false

  // Reset to defaults
  settings.value = {
    hostname: 'radio',
    theme: 'system',
    autoConnect: true,
    scanInterval: 60,
    connectionTimeout: 30,
    hotspotSsid: 'Radio-Setup',
    hotspotPassword: 'radio123',
    hotspotChannel: 6,
    captivePortal: true,
    debugMode: false
  }

  checkChanges()
  setSuccess('Settings reset to defaults. Click "Save Changes" to apply.')
}

// Initialize
onMounted(async () => {
  await loadSettings()
})

// Head configuration
useHead({
  title: 'Settings - Radio WiFi Configuration',
  meta: [
    { name: 'description', content: 'Configure device preferences and WiFi settings for your Raspberry Pi Radio' }
  ]
})
</script>
