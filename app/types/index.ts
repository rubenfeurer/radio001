// Type definitions for Radio WiFi Configuration
// Shared types across the application

export interface WiFiNetwork {
  ssid: string
  bssid?: string
  signal: number
  frequency?: string
  channel?: number
  security: 'Open' | 'WEP' | 'WPA' | 'WPA2' | 'WPA3' | 'WPA/WPA2'
  connected?: boolean
  saved?: boolean
}

export interface WiFiCredentials {
  ssid: string
  password: string
  security?: string
  hidden?: boolean
}

export interface WiFiStatus {
  wifiInterface: string
  status: 'connected' | 'disconnected' | 'connecting' | 'failed' | 'scanning'
  ssid?: string
  ip?: string
  signal?: number
  frequency?: string
  mode: 'client' | 'hotspot' | 'offline'
}

export interface ScanResult {
  networks: WiFiNetwork[]
  timestamp: number
  wifiInterface: string
}

export interface SystemStatus {
  hostname: string
  uptime: number
  memory: {
    total: number
    used: number
    free: number
  }
  cpu: {
    load: number
    temperature?: number
  }
  network: {
    wifi: WiFiStatus
    ethernet?: {
      connected: boolean
      ip?: string
    }
  }
  services: {
    avahi: boolean
    hostapd: boolean
    dnsmasq: boolean
  }
}

export interface HotspotConfig {
  ssid: string
  password: string
  channel: number
  ip: string
  subnet: string
  dhcpRange: string
  hidden: boolean
}

export interface AppConfig {
  hostname: string
  wifiInterface: string
  ethInterface: string
  hotspot: HotspotConfig
  features: {
    captivePortal: boolean
    autoConnect: boolean
    monitoring: boolean
  }
}

export interface ConnectionResult {
  success: boolean
  message: string
  ssid?: string
  ip?: string
  error?: string
}

export interface ScanResult {
  networks: WiFiNetwork[]
  timestamp: number
  wifiInterface: string
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
  timestamp: number
}

export interface NetworkInterface {
  name: string
  type: 'wifi' | 'ethernet' | 'loopback'
  status: 'up' | 'down'
  ip?: string
  mac?: string
  mtu?: number
}

export interface WifiScanOptions {
  wifiInterface?: string
  timeout?: number
  cached?: boolean
}

export interface ConnectionOptions {
  timeout?: number
  retries?: number
  autoReconnect?: boolean
}

// Form validation types
export interface ValidationError {
  field: string
  message: string
}

export interface FormState {
  isValid: boolean
  errors: ValidationError[]
  touched: Record<string, boolean>
}

// UI State types
export interface UIState {
  loading: boolean
  error?: string
  success?: string
  currentStep: number
  totalSteps: number
}

export interface WifiSetupStep {
  id: string
  title: string
  description: string
  component: string
  completed: boolean
  optional: boolean
}

// Events
export interface WiFiEvent {
  type: 'scan_started' | 'scan_completed' | 'connection_started' | 'connection_completed' | 'connection_failed' | 'disconnected'
  timestamp: number
  data?: any
}

// Device information
export interface DeviceInfo {
  model: string
  architecture: string
  os: string
  kernel: string
  memory: number
  storage: number
  interfaces: NetworkInterface[]
}

// Configuration persistence
export interface SavedNetwork {
  ssid: string
  security: string
  priority: number
  autoConnect: boolean
  lastConnected?: number
  createdAt: number
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  language: string
  autoConnect: boolean
  showAdvanced: boolean
  notifications: boolean
}

// Error types
export class WiFiError extends Error {
  constructor(
    message: string,
    public code: string,
    public details?: any
  ) {
    super(message)
    this.name = 'WiFiError'
  }
}

export class NetworkError extends Error {
  constructor(
    message: string,
    public interface: string,
    public details?: any
  ) {
    super(message)
    this.name = 'NetworkError'
  }
}

// Utility types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

export type Nullable<T> = T | null

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

// Runtime configuration
export interface RuntimeConfig {
  wifiInterface: string
  ethInterface: string
  hostname: string
  hotspotSsid: string
  hotspotPassword: string
  hotspotIp: string
  hotspotRange: string
  sessionSecret: string
  jwtSecret: string
  enableCaptivePortal: boolean
  enableAutoConnect: boolean
  public: {
    appName: string
    version: string
    isDevelopment: boolean
    hostname: string
  }
}
