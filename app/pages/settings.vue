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
                Settings
              </h1>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Configure device preferences
              </p>
            </div>
          </div>
          <UButton
            v-if="hasUnsavedChanges"
            color="primary"
            size="sm"
            @click="saveSettings"
            :loading="isSaving"
          >
            Save Changes
          </UButton>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="radio-container py-6 space-y-6">
      <!-- Device Settings -->
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            Device Settings
          </h2>
        </template>

        <div class="space-y-6">
          <!-- Hostname -->
          <UFormGroup
            label="Device Hostname"
            description="This is how the device appears on your network"
          >
            <UInput
              v-model="settings.hostname"
              placeholder="radio"
              @input="markAsChanged"
            />
          </UFormGroup>

          <!-- Theme -->
          <UFormGroup
            label="Theme"
            description="Choose your preferred interface theme"
          >
            <USelect
              v-model="settings.theme"
              :options="themeOptions"
              @change="markAsChanged"
            />
          </UFormGroup>

          <!-- Language -->
          <UFormGroup
            label="Language"
            description="Interface language preference"
          >
            <USelect
              v-model="settings.language"
              :options="languageOptions"
              @change="markAsChanged"
            />
          </UFormGroup>
        </div>
      </UCard>

      <!-- WiFi Settings -->
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            WiFi Configuration
          </h2>
        </template>

        <div class="space-y-6">
          <!-- Auto-connect -->
          <UFormGroup
            label="Auto-connect"
            description="Automatically connect to saved networks"
          >
            <UToggle
              v-model="settings.autoConnect"
              @change="markAsChanged"
            />
          </UFormGroup>

          <!-- WiFi Interface -->
          <UFormGroup
            label="WiFi Interface"
            description="Network interface for WiFi connections"
          >
            <USelect
              v-model="settings.wifiInterface"
              :options="interfaceOptions"
              @change="markAsChanged"
            />
          </UFormGroup>

          <!-- Connection Timeout -->
          <UFormGroup
            label="Connection Timeout"
            description="Maximum time to wait for WiFi connection (seconds)"
          >
            <UInput
              v-model.number="settings.connectionTimeout"
              type="number"
              min="10"
              max="120"
              @input="markAsChanged"
            />
          </UFormGroup>

          <!-- Scan Interval -->
          <UFormGroup
            label="Auto-scan Interval"
            description="How often to automatically scan for networks (minutes)"
          >
            <UInput
              v-model.number="settings.scanInterval"
              type="number"
              min="1"
              max="60"
              @input="markAsChanged"
            />
          </UFormGroup>
        </div>
      </UCard>

      <!-- Hotspot Settings -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Hotspot Configuration
            </h2>
            <UButton
              variant="outline"
              size="sm"
              @click="testHotspot"
              :loading="isTesting"
            >
              Test Hotspot
            </UButton>
          </div>
        </template>

        <div class="space-y-6">
          <!-- Hotspot SSID -->
          <UFormGroup
            label="Hotspot Name (SSID)"
            description="Name of the WiFi hotspot when in setup mode"
          >
            <UInput
              v-model="settings.hotspotSSID"
              placeholder="Radio-Setup"
              @input="markAsChanged"
            />
          </UFormGroup>

          <!-- Hotspot Password -->
          <UFormGroup
            label="Hotspot Password"
            description="Password for the setup hotspot (leave empty for open network)"
          >
            <UInput
              v-model="settings.hotspotPassword"
              type="password"
              placeholder="Enter password"
              @input="markAsChanged"
            />
          </UFormGroup>

          <!-- Hotspot Channel -->
          <UFormGroup
            label="WiFi Channel"
            description="WiFi channel for the hotspot (1-11 for 2.4GHz)"
          >
            <USelect
              v-model="settings.hotspotChannel"
              :options="channelOptions"
              @change="markAsChanged"
            />
          </UFormGroup>

          <!-- Hotspot IP -->
          <UFormGroup
            label="Hotspot IP Address"
            description="IP address for the hotspot interface"
          >
            <UInput
              v-model="settings.hotspotIP"
              placeholder="192.168.4.1"
              @input="markAsChanged"
            />
          </UFormGroup>

          <!-- Hidden Network -->
          <UFormGroup
            label="Hidden Network"
            description="Hide the hotspot from network lists"
          >
            <UToggle
              v-model="settings.hotspotHidden"
              @change="markAsChanged"
            />
          </UFormGroup>
        </div>
      </UCard>

      <!-- Advanced Settings -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Advanced Settings
            </h2>
            <UButton
              variant="ghost"
              size="sm"
              @click="showAdvanced = !showAdvanced"
            >
              <Icon
                :name="showAdvanced ? 'heroicons:chevron-up' : 'heroicons:chevron-down'"
                class="w-4 h-4"
              />
            </UButton>
          </div>
        </template>

        <UCollapse :open="showAdvanced">
          <div class="space-y-6 pt-4">
            <!-- Captive Portal -->
            <UFormGroup
              label="Captive Portal"
              description="Automatically redirect users to setup page when connected to hotspot"
            >
              <UToggle
                v-model="settings.captivePortal"
                @change="markAsChanged"
              />
            </UFormGroup>

            <!-- Debug Mode -->
            <UFormGroup
              label="Debug Mode"
              description="Enable detailed logging for troubleshooting"
            >
              <UToggle
                v-model="settings.debugMode"
                @change="markAsChanged"
              />
            </UFormGroup>

            <!-- Monitoring -->
            <UFormGroup
              label="Network Monitoring"
              description="Continuously monitor connection quality"
            >
              <UToggle
                v-model="settings.monitoring"
                @change="markAsChanged"
              />
            </UFormGroup>

            <!-- Auto-restart -->
            <UFormGroup
              label="Auto-restart on Failure"
              description="Automatically restart network services if connection fails"
            >
              <UToggle
                v-model="settings.autoRestart"
                @change="markAsChanged"
              />
            </UFormGroup>

            <!-- Reset Button -->
            <div class="border-t border-gray-200 dark:border-gray-700 pt-6">
              <UFormGroup
                label="Factory Reset"
                description="Reset all settings to default values"
              >
                <UButton
                  color="red"
                  variant="outline"
                  @click="showResetModal = true"
                >
                  <Icon name="heroicons:exclamation-triangle" class="w-4 h-4 mr-2" />
                  Reset to Defaults
                </UButton>
              </UFormGroup>
            </div>
          </div>
        </UCollapse>
      </UCard>

      <!-- System Information -->
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            System Information
          </h2>
        </template>

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1">
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Version</p>
            <p class="text-sm text-gray-900 dark:text-white">
              {{ config.public.version }}
            </p>
          </div>
          <div class="space-y-1">
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Build</p>
            <p class="text-sm text-gray-900 dark:text-white">
              {{ config.public.isDevelopment ? 'Development' : 'Production' }}
            </p>
          </div>
          <div class="space-y-1">
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Config File</p>
            <p class="text-sm text-gray-900 dark:text-white font-mono">
              /etc/radio/config.json
            </p>
          </div>
          <div class="space-y-1">
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Last Updated</p>
            <p class="text-sm text-gray-900 dark:text-white">
              {{ formatDate(lastUpdated) }}
            </p>
          </div>
        </div>
      </UCard>

      <!-- Actions -->
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            Configuration Actions
          </h2>
        </template>

        <div class="grid grid-cols-2 gap-3">
          <UButton
            variant="outline"
            @click="exportConfig"
            :loading="isExporting"
          >
            <Icon name="heroicons:document-arrow-down" class="w-4 h-4 mr-2" />
            Export Config
          </UButton>
          <UButton
            variant="outline"
            @click="$refs.importInput.click()"
          >
            <Icon name="heroicons:document-arrow-up" class="w-4 h-4 mr-2" />
            Import Config
          </UButton>
          <UButton
            variant="outline"
            @click="validateConfig"
            :loading="isValidating"
          >
            <Icon name="heroicons:shield-check" class="w-4 h-4 mr-2" />
            Validate Config
          </UButton>
          <UButton
            variant="outline"
            @click="navigateTo('/status')"
          >
            <Icon name="heroicons:chart-bar" class="w-4 h-4 mr-2" />
            View Status
          </UButton>
        </div>
      </UCard>

      <!-- Hidden file input for config import -->
      <input
        ref="importInput"
        type="file"
        accept=".json"
        class="hidden"
        @change="importConfig"
      />
    </main>

    <!-- Reset Confirmation Modal -->
    <UModal v-model="showResetModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold text-red-600">
            Confirm Factory Reset
          </h3>
        </template>

        <div class="py-4">
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
            This will reset all settings to their default values. This action cannot be undone.
          </p>
          <p class="text-sm font-medium text-gray-900 dark:text-white">
            Are you sure you want to continue?
          </p>
        </div>

        <template #footer>
          <div class="flex justify-end space-x-3">
            <UButton
              variant="outline"
              @click="showResetModal = false"
            >
              Cancel
            </UButton>
            <UButton
              color="red"
              @click="resetToDefaults"
              :loading="isResetting"
            >
              Reset All Settings
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Save Confirmation -->
    <div
      v-if="showSaveSuccess"
      class="fixed bottom-4 right-4 z-50"
    >
      <UAlert
        icon="heroicons:check-circle"
        color="green"
        variant="solid"
        title="Settings Saved"
        description="Your changes have been applied successfully"
        @close="showSaveSuccess = false"
        :close-button="{ icon: 'heroicons:x-mark', color: 'white', variant: 'link' }"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { UserPreferences, AppConfig } from '~/types'

// Meta
definePageMeta({
  title: 'Settings',
  description: 'Configure device settings and preferences'
})

// Runtime config
const config = useRuntimeConfig()
const toast = useToast()

// Reactive state
const settings = ref({
  // Device Settings
  hostname: 'radio',
  theme: 'system',
  language: 'en',

  // WiFi Settings
  autoConnect: true,
  wifiInterface: 'wlan0',
  connectionTimeout: 30,
  scanInterval: 5,

  // Hotspot Settings
  hotspotSSID: 'Radio-Setup',
  hotspotPassword: 'radio123',
  hotspotChannel: 6,
  hotspotIP: '192.168.4.1',
  hotspotHidden: false,

  // Advanced Settings
  captivePortal: true,
  debugMode: false,
  monitoring: true,
  autoRestart: true
})

const originalSettings = ref({})
const hasUnsavedChanges = ref(false)
const showAdvanced = ref(false)
const showResetModal = ref(false)
const showSaveSuccess = ref(false)

const isSaving = ref(false)
const isExporting = ref(false)
const isValidating = ref(false)
const isResetting = ref(false)
const isTesting = ref(false)

const lastUpdated = ref(new Date())

// Options
const themeOptions = [
  { label: 'System', value: 'system' },
  { label: 'Light', value: 'light' },
  { label: 'Dark', value: 'dark' }
]

const languageOptions = [
  { label: 'English', value: 'en' },
  { label: 'Spanish', value: 'es' },
  { label: 'French', value: 'fr' },
  { label: 'German', value: 'de' }
]

const interfaceOptions = [
  { label: 'wlan0', value: 'wlan0' },
  { label: 'wlan1', value: 'wlan1' }
]

const channelOptions = Array.from({ length: 11 }, (_, i) => ({
  label: `Channel ${i + 1}`,
  value: i + 1
}))

// Methods
const markAsChanged = () => {
  hasUnsavedChanges.value = true
}

const loadSettings = async () => {
  try {
    const response = await $fetch<{ success: boolean; data: AppConfig }>('/api/config')
    if (response.success && response.data) {
      Object.assign(settings.value, response.data)
      originalSettings.value = { ...settings.value }
      hasUnsavedChanges.value = false
    }
  } catch (error) {
    console.error('Failed to load settings:', error)
    toast.add({
      title: 'Error',
      description: 'Failed to load settings',
      color: 'red'
    })
  }
}

const saveSettings = async () => {
  isSaving.value = true
  try {
    const response = await $fetch<{ success: boolean; message: string }>('/api/config', {
      method: 'POST',
      body: settings.value
    })

    if (response.success) {
      originalSettings.value = { ...settings.value }
      hasUnsavedChanges.value = false
      showSaveSuccess.value = true
      lastUpdated.value = new Date()

      // Auto-hide success message
      setTimeout(() => {
        showSaveSuccess.value = false
      }, 3000)
    } else {
      throw new Error(response.message)
    }
  } catch (error) {
    console.error('Failed to save settings:', error)
    toast.add({
      title: 'Error',
      description: 'Failed to save settings',
      color: 'red'
    })
  } finally {
    isSaving.value = false
  }
}

const exportConfig = async () => {
  isExporting.value = true
  try {
    const response = await fetch('/api/config/export')
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `radio-config-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast.add({
        title: 'Success',
        description: 'Configuration exported',
        color: 'green'
      })
    } else {
      throw new Error('Export failed')
    }
  } catch (error) {
    console.error('Failed to export config:', error)
    toast.add({
      title: 'Error',
      description: 'Failed to export configuration',
      color: 'red'
    })
  } finally {
    isExporting.value = false
  }
}

const importConfig = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return

  try {
    const text = await file.text()
    const importedConfig = JSON.parse(text)

    // Validate imported config
    if (typeof importedConfig !== 'object' || !importedConfig) {
      throw new Error('Invalid configuration file')
    }

    // Merge with current settings
    Object.assign(settings.value, importedConfig)
    markAsChanged()

    toast.add({
      title: 'Success',
      description: 'Configuration imported successfully',
      color: 'green'
    })
  } catch (error) {
    console.error('Failed to import config:', error)
    toast.add({
      title: 'Error',
      description: 'Failed to import configuration',
      color: 'red'
    })
  }

  // Reset file input
  ;(event.target as HTMLInputElement).value = ''
}

const validateConfig = async () => {
  isValidating.value = true
  try {
    const response = await $fetch<{ success: boolean; message: string; errors?: string[] }>('/api/config/validate', {
      method: 'POST',
      body: settings.value
    })

    if (response.success) {
      toast.add({
        title: 'Valid Configuration',
        description: 'All settings are valid',
        color: 'green'
      })
    } else {
      const errors = response.errors?.join(', ') || response.message
      toast.add({
        title: 'Configuration Errors',
        description: errors,
        color: 'red'
      })
    }
  } catch (error) {
    console.error('Failed to validate config:', error)
    toast.add({
      title: 'Error',
      description: 'Failed to validate configuration',
      color: 'red'
    })
  } finally {
    isValidating.value = false
  }
}

const testHotspot = async () => {
  isTesting.value = true
  try {
    const response = await $fetch<{ success: boolean; message: string }>('/api/system/test-hotspot', {
      method: 'POST',
      body: {
        ssid: settings.value.hotspotSSID,
        password: settings.value.hotspotPassword,
        channel: settings.value.hotspotChannel
      }
    })

    if (response.success) {
      toast.add({
        title: 'Test Successful',
        description: 'Hotspot configuration is valid',
        color: 'green'
      })
    } else {
      throw new Error(response.message)
    }
  } catch (error) {
    console.error('Hotspot test failed:', error)
    toast.add({
      title: 'Test Failed',
      description: 'Hotspot configuration has issues',
      color: 'red'
    })
  } finally {
    isTesting.value = false
  }
}

const resetToDefaults = async () => {
  isResetting.value = true
  try {
    const response = await $fetch<{ success: boolean; message: string }>('/api/config/reset', {
      method: 'POST'
    })

    if (response.success) {
      await loadSettings()
      showResetModal.value = false
      toast.add({
        title: 'Reset Complete',
        description: 'All settings have been reset to defaults',
        color: 'green'
      })
    } else {
      throw new Error(response.message)
    }
  } catch (error) {
    console.error('Failed to reset settings:', error)
    toast.add({
      title: 'Error',
      description: 'Failed to reset settings',
      color: 'red'
    })
  } finally {
    isResetting.value = false
  }
}

// Utility functions
const formatDate = (date: Date): string => {
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

// Watch for unsaved changes warning
onBeforeRouteLeave((to, from, next) => {
  if (hasUnsavedChanges.value) {
    const answer = confirm('You have unsaved changes. Are you sure you want to leave?')
    if (answer) {
      next()
    } else {
      next(false)
    }
  } else {
    next()
  }
})

// Initialize
onMounted(async () => {
  await loadSettings()
})

// Head configuration
useHead({
  title: 'Settings - Radio',
  meta: [
    { name: 'description', content: 'Configure device settings and preferences' }
  ]
})
</script>

<style scoped>
.radio-container {
  @apply max-w-2xl mx-auto px-4;
}
</style>
