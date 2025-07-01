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
                WiFi Setup
              </h1>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Configure your network connection
              </p>
            </div>
          </div>
          <UButton
            variant="ghost"
            size="sm"
            @click="refreshNetworks"
            :loading="isScanning"
          >
            <Icon name="heroicons:arrow-path" class="w-4 h-4" />
          </UButton>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="radio-container py-6 space-y-6">
      <!-- Current Status -->
      <UCard v-if="status">
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Current Status
            </h2>
            <UBadge
              :color="statusColor"
              :label="statusText"
              size="sm"
            />
          </div>
        </template>

        <div v-if="status.status === 'connected'" class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
              Connected to
            </span>
            <span class="text-sm text-gray-900 dark:text-white font-mono">
              {{ status.ssid }}
            </span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
              IP Address
            </span>
            <span class="text-sm text-gray-900 dark:text-white font-mono">
              {{ status.ip }}
            </span>
          </div>
        </div>
        <div v-else-if="status.mode === 'hotspot'" class="text-center py-2">
          <Icon name="heroicons:wifi" class="w-8 h-8 text-orange-500 mx-auto mb-2" />
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Device is in hotspot mode
          </p>
        </div>
        <div v-else class="text-center py-2">
          <Icon name="heroicons:wifi-slash" class="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p class="text-sm text-gray-600 dark:text-gray-400">
            No active connection
          </p>
        </div>
      </UCard>

      <!-- Network Scanner -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Available Networks
            </h2>
            <div class="flex items-center space-x-2">
              <span v-if="lastScanTime" class="text-xs text-gray-500">
                {{ formatScanTime(lastScanTime) }}
              </span>
              <UButton
                size="xs"
                variant="outline"
                @click="refreshNetworks"
                :loading="isScanning"
              >
                <Icon name="heroicons:magnifying-glass" class="w-3 h-3 mr-1" />
                Scan
              </UButton>
            </div>
          </div>
        </template>

        <!-- Scanning State -->
        <div v-if="isScanning" class="text-center py-8">
          <div class="radio-spinner mx-auto mb-3"></div>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Scanning for networks...
          </p>
        </div>

        <!-- No Networks Found -->
        <div v-else-if="networks.length === 0" class="text-center py-8">
          <Icon name="heroicons:wifi-slash" class="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">
            No networks found
          </p>
          <UButton
            size="sm"
            variant="outline"
            @click="refreshNetworks"
          >
            Try Again
          </UButton>
        </div>

        <!-- Networks List -->
        <div v-else class="space-y-2">
          <div
            v-for="network in sortedNetworks"
            :key="network.ssid"
            class="network-item"
            :class="{ 'network-item-selected': selectedNetwork?.ssid === network.ssid }"
            @click="selectNetwork(network)"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3 flex-1 min-w-0">
                <div class="flex-shrink-0">
                  <SignalStrength :strength="network.signal" />
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center space-x-2">
                    <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {{ network.ssid }}
                    </p>
                    <UBadge
                      v-if="network.connected"
                      size="xs"
                      color="green"
                      label="Connected"
                    />
                    <UBadge
                      v-else-if="network.saved"
                      size="xs"
                      color="blue"
                      label="Saved"
                    />
                  </div>
                  <div class="flex items-center space-x-2 mt-1">
                    <span class="text-xs text-gray-500">
                      {{ formatSecurity(network.security) }}
                    </span>
                    <span v-if="network.frequency" class="text-xs text-gray-500">
                      {{ network.frequency }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <Icon
                  v-if="requiresPassword(network)"
                  name="heroicons:lock-closed"
                  class="w-4 h-4 text-gray-400"
                />
                <Icon
                  name="heroicons:chevron-right"
                  class="w-4 h-4 text-gray-400"
                />
              </div>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Connection Form -->
      <UCard v-if="selectedNetwork">
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Connect to {{ selectedNetwork.ssid }}
            </h2>
            <UButton
              variant="ghost"
              size="sm"
              @click="selectedNetwork = null"
            >
              <Icon name="heroicons:x-mark" class="w-4 h-4" />
            </UButton>
          </div>
        </template>

        <form @submit.prevent="handleConnect" class="space-y-4">
          <!-- Network Info -->
          <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                Network
              </span>
              <div class="flex items-center space-x-2">
                <SignalStrength :strength="selectedNetwork.signal" size="sm" />
                <span class="text-sm text-gray-600 dark:text-gray-400">
                  {{ selectedNetwork.signal }}%
                </span>
              </div>
            </div>
            <p class="text-sm text-gray-900 dark:text-white font-mono">
              {{ selectedNetwork.ssid }}
            </p>
            <p class="text-xs text-gray-500 mt-1">
              {{ formatSecurity(selectedNetwork.security) }}
              <span v-if="selectedNetwork.frequency">
                • {{ selectedNetwork.frequency }}
              </span>
            </p>
          </div>

          <!-- Password Input -->
          <div v-if="requiresPassword(selectedNetwork)">
            <UFormGroup
              label="Password"
              :error="passwordError"
              required
            >
              <UInput
                v-model="password"
                type="password"
                placeholder="Enter WiFi password"
                :disabled="isConnecting"
                size="lg"
              />
            </UFormGroup>
          </div>

          <!-- Advanced Options -->
          <UAccordion
            :items="[{
              label: 'Advanced Options',
              icon: 'heroicons:cog-6-tooth',
              defaultOpen: false,
              slot: 'advanced'
            }]"
          >
            <template #advanced>
              <div class="space-y-4 pt-4">
                <UFormGroup label="Connection Options">
                  <div class="space-y-3">
                    <UCheckbox
                      v-model="autoConnect"
                      label="Connect automatically"
                    />
                    <UCheckbox
                      v-model="saveNetwork"
                      label="Save this network"
                    />
                  </div>
                </UFormGroup>
              </div>
            </template>
          </UAccordion>

          <!-- Connection Actions -->
          <div class="flex space-x-3 pt-2">
            <UButton
              type="submit"
              color="primary"
              size="lg"
              :loading="isConnecting"
              :disabled="requiresPassword(selectedNetwork) && !password.trim()"
              block
            >
              <Icon name="heroicons:wifi" class="w-4 h-4 mr-2" />
              {{ isConnecting ? 'Connecting...' : 'Connect' }}
            </UButton>
          </div>
        </form>
      </UCard>

      <!-- Manual Network Entry -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Add Hidden Network
            </h2>
            <UButton
              variant="ghost"
              size="sm"
              @click="showManualEntry = !showManualEntry"
            >
              <Icon
                :name="showManualEntry ? 'heroicons:chevron-up' : 'heroicons:chevron-down'"
                class="w-4 h-4"
              />
            </UButton>
          </div>
        </template>

        <UCollapse :open="showManualEntry">
          <form @submit.prevent="handleManualConnect" class="space-y-4">
            <UFormGroup
              label="Network Name (SSID)"
              :error="manualSsidError"
              required
            >
              <UInput
                v-model="manualSsid"
                placeholder="Enter network name"
                :disabled="isConnecting"
                size="lg"
              />
            </UFormGroup>

            <UFormGroup label="Security Type">
              <USelect
                v-model="manualSecurity"
                :options="securityOptions"
                size="lg"
              />
            </UFormGroup>

            <UFormGroup
              v-if="manualSecurity !== 'Open'"
              label="Password"
              :error="manualPasswordError"
              required
            >
              <UInput
                v-model="manualPassword"
                type="password"
                placeholder="Enter password"
                :disabled="isConnecting"
                size="lg"
              />
            </UFormGroup>

            <UButton
              type="submit"
              color="primary"
              size="lg"
              :loading="isConnecting"
              :disabled="!manualSsid.trim() || (manualSecurity !== 'Open' && !manualPassword.trim())"
              block
            >
              <Icon name="heroicons:plus" class="w-4 h-4 mr-2" />
              Add Network
            </UButton>
          </form>
        </UCollapse>
      </UCard>
    </main>

    <!-- Connection Status Modal -->
    <UModal v-model="showConnectionModal">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold">
              {{ connectionStatus.title }}
            </h3>
          </div>
        </template>

        <div class="text-center py-6">
          <div v-if="connectionStatus.type === 'connecting'" class="space-y-4">
            <div class="radio-spinner mx-auto"></div>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              {{ connectionStatus.message }}
            </p>
          </div>
          <div v-else-if="connectionStatus.type === 'success'" class="space-y-4">
            <Icon name="heroicons:check-circle" class="w-16 h-16 text-green-500 mx-auto" />
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-white mb-1">
                {{ connectionStatus.message }}
              </p>
              <p class="text-xs text-gray-500">
                The device will now restart to apply changes
              </p>
            </div>
          </div>
          <div v-else-if="connectionStatus.type === 'error'" class="space-y-4">
            <Icon name="heroicons:x-circle" class="w-16 h-16 text-red-500 mx-auto" />
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-white mb-1">
                {{ connectionStatus.message }}
              </p>
              <p class="text-xs text-gray-500">
                Please check your credentials and try again
              </p>
            </div>
          </div>
        </div>

        <template #footer>
          <div class="flex justify-end space-x-3">
            <UButton
              v-if="connectionStatus.type !== 'connecting'"
              @click="closeConnectionModal"
              variant="outline"
            >
              Close
            </UButton>
            <UButton
              v-if="connectionStatus.type === 'error'"
              @click="retryConnection"
              color="primary"
            >
              Try Again
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import type { WiFiNetwork, WiFiCredentials } from '~/types'

// Meta
definePageMeta({
  title: 'WiFi Setup',
  description: 'Configure WiFi connection for your Radio device'
})

// Composables
const { networks, status, isScanning, isConnecting, error, lastScanTime, scanNetworks, connectToNetwork, getStatus, requiresPassword } = useWiFi()
const toast = useToast()

// Reactive state
const selectedNetwork = ref<WiFiNetwork | null>(null)
const password = ref('')
const passwordError = ref('')
const autoConnect = ref(true)
const saveNetwork = ref(true)

// Manual network entry
const showManualEntry = ref(false)
const manualSsid = ref('')
const manualPassword = ref('')
const manualSecurity = ref('WPA2')
const manualSsidError = ref('')
const manualPasswordError = ref('')

// Connection modal
const showConnectionModal = ref(false)
const connectionStatus = ref({
  type: 'connecting' as 'connecting' | 'success' | 'error',
  title: '',
  message: ''
})

// Security options for manual entry
const securityOptions = [
  { label: 'Open', value: 'Open' },
  { label: 'WEP', value: 'WEP' },
  { label: 'WPA/WPA2', value: 'WPA' },
  { label: 'WPA2', value: 'WPA2' },
  { label: 'WPA3', value: 'WPA3' }
]

// Computed properties
const sortedNetworks = computed(() => {
  return [...networks.value].sort((a, b) => {
    // Connected networks first
    if (a.connected && !b.connected) return -1
    if (!a.connected && b.connected) return 1

    // Saved networks next
    if (a.saved && !b.saved) return -1
    if (!a.saved && b.saved) return 1

    // Then by signal strength
    return (b.signal || 0) - (a.signal || 0)
  })
})

const statusColor = computed(() => {
  if (!status.value) return 'gray'
  switch (status.value.status) {
    case 'connected': return 'green'
    case 'connecting': return 'yellow'
    case 'failed': return 'red'
    default: return 'gray'
  }
})

const statusText = computed(() => {
  if (!status.value) return 'Unknown'
  switch (status.value.status) {
    case 'connected': return 'Connected'
    case 'connecting': return 'Connecting'
    case 'failed': return 'Failed'
    case 'disconnected':
      return status.value.mode === 'hotspot' ? 'Hotspot Mode' : 'Disconnected'
    default: return 'Unknown'
  }
})

// Methods
const selectNetwork = (network: WiFiNetwork) => {
  selectedNetwork.value = network
  password.value = ''
  passwordError.value = ''

  // Scroll to form
  nextTick(() => {
    const form = document.querySelector('.connection-form')
    if (form) {
      form.scrollIntoView({ behavior: 'smooth' })
    }
  })
}

const refreshNetworks = async () => {
  await scanNetworks()
  if (error.value) {
    toast.add({
      title: 'Scan Failed',
      description: error.value,
      color: 'red'
    })
  }
}

const handleConnect = async () => {
  if (!selectedNetwork.value) return

  // Validate password
  if (requiresPassword(selectedNetwork.value) && !password.value.trim()) {
    passwordError.value = 'Password is required'
    return
  }

  const credentials: WiFiCredentials = {
    ssid: selectedNetwork.value.ssid,
    password: password.value,
    security: selectedNetwork.value.security
  }

  await connectToNetwork(credentials)
}

const handleManualConnect = async () => {
  // Validate inputs
  manualSsidError.value = ''
  manualPasswordError.value = ''

  if (!manualSsid.value.trim()) {
    manualSsidError.value = 'Network name is required'
    return
  }

  if (manualSecurity.value !== 'Open' && !manualPassword.value.trim()) {
    manualPasswordError.value = 'Password is required'
    return
  }

  const credentials: WiFiCredentials = {
    ssid: manualSsid.value,
    password: manualPassword.value,
    security: manualSecurity.value,
    hidden: true
  }

  const success = await connectToNetwork(credentials)

  if (success) {
    // Clear form
    manualSsid.value = ''
    manualPassword.value = ''
    manualSecurity.value = 'WPA2'
    showManualEntry.value = false
  }
}

const formatScanTime = (timestamp: number) => {
  const now = Date.now()
  const diff = now - timestamp
  const minutes = Math.floor(diff / 60000)

  if (minutes < 1) return 'Just now'
  if (minutes === 1) return '1 minute ago'
  return `${minutes} minutes ago`
}

const formatSecurity = (security: string) => {
  switch (security) {
    case 'Open': return 'Open'
    case 'WEP': return 'WEP'
    case 'WPA': return 'WPA'
    case 'WPA2': return 'WPA2'
    case 'WPA3': return 'WPA3'
    case 'WPA/WPA2': return 'WPA/WPA2'
    default: return security
  }
}

const closeConnectionModal = () => {
  showConnectionModal.value = false
  selectedNetwork.value = null
  password.value = ''
}

const retryConnection = () => {
  showConnectionModal.value = false
  if (selectedNetwork.value) {
    handleConnect()
  }
}

// Watch for connection attempts
watch(isConnecting, (connecting) => {
  if (connecting) {
    connectionStatus.value = {
      type: 'connecting',
      title: 'Connecting to WiFi',
      message: `Connecting to ${selectedNetwork.value?.ssid || 'network'}...`
    }
    showConnectionModal.value = true
  }
})

// Watch for connection results
watch(error, (newError) => {
  if (newError && showConnectionModal.value) {
    connectionStatus.value = {
      type: 'error',
      title: 'Connection Failed',
      message: newError
    }
  }
})

// Initialize
onMounted(async () => {
  await getStatus()

  // Auto-scan if no recent scan
  if (!lastScanTime.value || Date.now() - lastScanTime.value > 60000) {
    await refreshNetworks()
  }
})

// Head configuration
useHead({
  title: 'WiFi Setup - Radio',
  meta: [
    { name: 'description', content: 'Configure WiFi connection for your Radio device' }
  ]
})
</script>

<style scoped>
.radio-container {
  @apply max-w-2xl mx-auto px-4;
}

.network-item {
  @apply p-4 border border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer transition-all duration-200 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-sm;
}

.network-item-selected {
  @apply border-blue-500 bg-blue-50 dark:bg-blue-900/20;
}

.radio-spinner {
  @apply w-6 h-6 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin;
}

.progress-bar {
  @apply w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2;
}

.progress-fill {
  @apply bg-blue-600 h-2 rounded-full transition-all duration-300;
}
</style>
