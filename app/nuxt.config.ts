// Nuxt configuration optimized for Raspberry Pi Zero 2 W
// Radio WiFi Configuration Application

export default defineNuxtConfig({
  // =============================================================================
  // Core Modules
  // =============================================================================
  modules: [
    '@pinia/nuxt',
    '@nuxtjs/tailwindcss'
  ],

  // =============================================================================
  // TypeScript Configuration
  // =============================================================================
  typescript: {
    typeCheck: false,
    strict: false
  },

  // =============================================================================
  // Development Tools
  // =============================================================================
  devtools: {
    enabled: false
  },

  // =============================================================================
  // Runtime Configuration
  // =============================================================================
  runtimeConfig: {
    // Server-only configuration (private)
    wifiInterface: process.env.WIFI_INTERFACE || 'wlan0',
    ethInterface: process.env.ETH_INTERFACE || 'eth0',
    hostname: process.env.HOSTNAME || 'radio',

    // Hotspot configuration
    hotspotSsid: process.env.HOTSPOT_SSID || 'Radio-Setup',
    hotspotPassword: process.env.HOTSPOT_PASSWORD || 'radio123',
    hotspotIp: process.env.HOTSPOT_IP || '192.168.4.1',
    hotspotRange: process.env.HOTSPOT_RANGE || '192.168.4.2,192.168.4.20',

    // Security
    sessionSecret: process.env.SESSION_SECRET || 'dev-secret-key',
    jwtSecret: process.env.JWT_SECRET || 'dev-jwt-secret',

    // Features
    enableCaptivePortal: process.env.ENABLE_CAPTIVE_PORTAL === 'true',
    enableAutoConnect: process.env.ENABLE_AUTO_CONNECT === 'true',

    // Public configuration (client-accessible)
    public: {
      appName: 'Radio WiFi Config',
      version: '1.0.0',
      isDevelopment: process.env.NODE_ENV === 'development',
      hostname: process.env.HOSTNAME || 'radio'
    }
  },

  // =============================================================================
  // Application Configuration
  // =============================================================================
  app: {
    head: {
      title: 'Radio WiFi Setup',
      htmlAttrs: {
        lang: 'en'
      },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no' },
        { name: 'description', content: 'Easy WiFi configuration for your Raspberry Pi Radio device' },
        { name: 'theme-color', content: '#0ea5e9' },
        { name: 'apple-mobile-web-app-capable', content: 'yes' },
        { name: 'apple-mobile-web-app-status-bar-style', content: 'default' },
        { name: 'format-detection', content: 'telephone=no' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        { rel: 'apple-touch-icon', href: '/icon-192.png' },
        { rel: 'manifest', href: '/manifest.json' }
      ]
    }
  },

  // =============================================================================
  // Styling
  // =============================================================================
  css: [
    '~/assets/css/main.css'
  ],

  // =============================================================================
  // Tailwind CSS Configuration
  // =============================================================================
  tailwindcss: {
    cssPath: '~/assets/css/main.css',
  },

  // =============================================================================
  // Server Configuration
  // =============================================================================
  nitro: {
    // Optimizations for Pi Zero 2 W
    experimental: {
      wasm: false // Disable WASM for ARM compatibility
    },
    minify: process.env.NODE_ENV === 'production',
    sourceMap: process.env.NODE_ENV === 'development',

    // Compression
    compressPublicAssets: true,

    // Memory optimizations
    storage: {
      redis: false // Use in-memory storage for simplicity
    }
  },

  // =============================================================================
  // Build Configuration - Pi Zero 2 W Optimizations
  // =============================================================================
  vite: {
    build: {
      target: 'es2020'
    },

    // Development server
    server: {
      hmr: {
        port: 24678
      }
    }
  },

  // =============================================================================
  // Development Server
  // =============================================================================
  devServer: {
    host: '0.0.0.0',
    port: 3000
  },

  // =============================================================================
  // SSR Configuration
  // =============================================================================
  ssr: true,

  // =============================================================================
  // Experimental Features (Memory Optimizations)
  // =============================================================================
  experimental: {
    payloadExtraction: false,
    inlineSSRStyles: false
  },

  // =============================================================================
  // Compatibility
  // =============================================================================
  compatibilityDate: '2024-01-01',

  // =============================================================================
  // Error Handling
  // =============================================================================
  hooks: {
    'render:errorMiddleware': (app) => {
      app.use('/__nuxt_error', (error, req, res, next) => {
        console.error('Nuxt Error:', error)
        next(error)
      })
    }
  },

  // =============================================================================
  // Build Configuration
  // =============================================================================
  build: {
    analyze: false
  }
})
