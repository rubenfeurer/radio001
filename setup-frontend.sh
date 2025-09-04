#!/bin/bash

# Setup script to create SvelteKit frontend for Radio WiFi Configuration
# This script replaces the Nuxt frontend with a SvelteKit frontend to avoid ARM64 oxc-parser issues

set -e

echo "🚀 Setting up SvelteKit frontend for Radio WiFi Configuration"

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -d "backend" ]; then
    echo "❌ Please run this script from the radio001 project root directory"
    exit 1
fi

# Create frontend directory structure
echo "📁 Creating frontend directory structure..."
mkdir -p frontend/src/lib/components
mkdir -p frontend/src/lib/stores
mkdir -p frontend/src/routes/setup
mkdir -p frontend/src/routes/settings
mkdir -p frontend/src/routes/status
mkdir -p frontend/static

cd frontend

# Create package.json
echo "📦 Creating package.json..."
cat > package.json << 'EOF'
{
  "name": "radio-wifi-frontend",
  "version": "1.0.0",
  "description": "SvelteKit frontend for Radio WiFi Configuration",
  "private": true,
  "scripts": {
    "dev": "vite dev --host 0.0.0.0 --port 3000",
    "build": "vite build",
    "preview": "vite preview --host 0.0.0.0 --port 3000",
    "check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
    "check:watch": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json --watch",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix"
  },
  "devDependencies": {
    "@sveltejs/adapter-static": "^3.0.1",
    "@sveltejs/kit": "^2.0.0",
    "@sveltejs/vite-plugin-svelte": "^3.0.0",
    "@tailwindcss/forms": "^0.5.7",
    "@tailwindcss/typography": "^0.5.10",
    "@types/node": "^20.10.0",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.56.0",
    "eslint-config-prettier": "^9.1.0",
    "eslint-plugin-svelte": "^2.35.1",
    "postcss": "^8.4.32",
    "prettier": "^3.1.1",
    "prettier-plugin-svelte": "^3.1.2",
    "svelte": "^4.2.7",
    "svelte-check": "^3.6.0",
    "tailwindcss": "^3.4.0",
    "tslib": "^2.4.1",
    "typescript": "^5.0.0",
    "vite": "^5.0.3"
  },
  "type": "module",
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=8.0.0"
  }
}
EOF

# Create SvelteKit configuration
echo "⚙️  Creating SvelteKit configuration..."
cat > svelte.config.js << 'EOF'
import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter({
			pages: 'build',
			assets: 'build',
			fallback: 'index.html',
			precompress: false,
			strict: true
		}),
		prerender: {
			handleMissingId: 'warn'
		}
	}
};

export default config;
EOF

# Create Vite configuration
echo "⚡ Creating Vite configuration..."
cat > vite.config.js << 'EOF'
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		host: '0.0.0.0',
		port: 3000,
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true
			}
		}
	}
});
EOF

# Create TypeScript configuration
echo "🔷 Creating TypeScript configuration..."
cat > tsconfig.json << 'EOF'
{
	"extends": "./.svelte-kit/tsconfig.json",
	"compilerOptions": {
		"allowJs": true,
		"checkJs": true,
		"esModuleInterop": true,
		"forceConsistentCasingInFileNames": true,
		"resolveJsonModule": true,
		"skipLibCheck": true,
		"sourceMap": true,
		"strict": true,
		"moduleResolution": "bundler"
	}
}
EOF

# Create Tailwind configuration
echo "🎨 Creating Tailwind configuration..."
cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	darkMode: 'class',
	theme: {
		extend: {
			colors: {
				primary: {
					50: '#eff6ff',
					100: '#dbeafe',
					200: '#bfdbfe',
					300: '#93c5fd',
					400: '#60a5fa',
					500: '#3b82f6',
					600: '#2563eb',
					700: '#1d4ed8',
					800: '#1e40af',
					900: '#1e3a8a'
				}
			}
		}
	},
	plugins: [
		require('@tailwindcss/forms'),
		require('@tailwindcss/typography')
	]
};
EOF

# Create PostCSS configuration
echo "🎨 Creating PostCSS configuration..."
cat > postcss.config.js << 'EOF'
export default {
	plugins: {
		tailwindcss: {},
		autoprefixer: {}
	}
};
EOF

# Create ESLint configuration
echo "🔍 Creating ESLint configuration..."
cat > .eslintrc.cjs << 'EOF'
/** @type { import("eslint").Linter.Config } */
module.exports = {
	root: true,
	extends: [
		'eslint:recommended',
		'@typescript-eslint/recommended',
		'eslint-config-prettier'
	],
	parser: '@typescript-eslint/parser',
	plugins: ['@typescript-eslint'],
	parserOptions: {
		sourceType: 'module',
		ecmaVersion: 2020,
		extraFileExtensions: ['.svelte']
	},
	env: {
		browser: true,
		es2017: true,
		node: true
	},
	overrides: [
		{
			files: ['*.svelte'],
			processor: 'svelte3/svelte3'
		}
	]
};
EOF

# Create Prettier configuration
echo "💅 Creating Prettier configuration..."
cat > .prettierrc << 'EOF'
{
	"useTabs": true,
	"singleQuote": true,
	"trailingComma": "none",
	"printWidth": 100,
	"plugins": ["prettier-plugin-svelte"],
	"pluginSearchDirs": ["."],
	"overrides": [{ "files": "*.svelte", "options": { "parser": "svelte" } }]
}
EOF

# Create app.html
echo "📄 Creating app.html template..."
cat > src/app.html << 'EOF'
<!doctype html>
<html lang="en" class="%sveltekit.theme%">
	<head>
		<meta charset="utf-8" />
		<link rel="icon" href="%sveltekit.assets%/favicon.ico" />
		<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
		<meta name="description" content="Easy WiFi configuration for your Raspberry Pi Radio device" />
		<meta name="theme-color" content="#3b82f6" />
		<meta name="apple-mobile-web-app-capable" content="yes" />
		<meta name="apple-mobile-web-app-status-bar-style" content="default" />
		<title>Radio WiFi Setup</title>
		%sveltekit.head%
	</head>
	<body data-sveltekit-preload-data="hover" class="min-h-screen bg-gray-50 dark:bg-gray-900">
		<div style="display: contents">%sveltekit.body%</div>
	</body>
</html>
EOF

# Create global CSS
echo "🎨 Creating global CSS..."
cat > src/app.postcss << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
	html {
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
	}
}

@layer components {
	.btn {
		@apply inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed;
	}

	.btn-primary {
		@apply btn text-white bg-primary-600 hover:bg-primary-700 focus:ring-primary-500;
	}

	.btn-secondary {
		@apply btn text-gray-700 bg-white border-gray-300 hover:bg-gray-50 focus:ring-primary-500 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700;
	}

	.card {
		@apply bg-white dark:bg-gray-800 shadow border border-gray-200 dark:border-gray-700 rounded-lg;
	}

	.input {
		@apply block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white;
	}
}
EOF

# Create main layout
echo "🎨 Creating main layout..."
cat > src/routes/+layout.svelte << 'EOF'
<script lang="ts">
	import '../app.postcss';
	import { onMount } from 'svelte';

	// Dark mode management
	let darkMode = false;

	onMount(() => {
		// Check for saved theme or default to system preference
		const savedTheme = localStorage.getItem('theme');
		if (savedTheme === 'dark') {
			darkMode = true;
		} else if (savedTheme === 'light') {
			darkMode = false;
		} else {
			darkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
		}
		updateTheme();
	});

	function updateTheme() {
		if (darkMode) {
			document.documentElement.classList.add('dark');
			localStorage.setItem('theme', 'dark');
		} else {
			document.documentElement.classList.remove('dark');
			localStorage.setItem('theme', 'light');
		}
	}

	function toggleTheme() {
		darkMode = !darkMode;
		updateTheme();
	}
</script>

<main class="min-h-screen">
	<slot />
</main>
EOF

# Create TypeScript types
echo "🔷 Creating TypeScript types..."
cat > src/lib/types.ts << 'EOF'
// Type definitions for Radio WiFi Configuration
// Migrated from Nuxt types

export interface WiFiNetwork {
	ssid: string;
	bssid?: string;
	signal: number;
	frequency?: string;
	channel?: number;
	security: 'Open' | 'WEP' | 'WPA' | 'WPA2' | 'WPA3' | 'WPA/WPA2';
	connected?: boolean;
	saved?: boolean;
}

export interface WiFiCredentials {
	ssid: string;
	password: string;
	security?: string;
	hidden?: boolean;
}

export interface WiFiStatus {
	wifiInterface: string;
	status: 'connected' | 'disconnected' | 'connecting' | 'failed' | 'scanning';
	ssid?: string;
	ip?: string;
	signal?: number;
	frequency?: string;
	mode: 'client' | 'hotspot' | 'offline';
}

export interface SystemStatus {
	hostname: string;
	uptime: number;
	memory: {
		total: number;
		used: number;
		free: number;
	};
	cpu: {
		load: number;
		temperature?: number;
	};
	network: {
		wifi: WiFiStatus;
		ethernet?: {
			connected: boolean;
			ip?: string;
		};
	};
	services: {
		[key: string]: boolean;
	};
}

export interface ApiResponse<T = any> {
	success: boolean;
	data?: T;
	error?: string;
	message?: string;
	timestamp: number;
}

export interface ConnectionResult {
	success: boolean;
	message: string;
	ssid?: string;
	ip?: string;
	error?: string;
}
EOF

# Create WiFi store
echo "🏪 Creating WiFi store..."
cat > src/lib/stores/wifi.ts << 'EOF'
// WiFi management store for SvelteKit
// Replaces Nuxt useWiFi composable

import { writable, derived, get } from 'svelte/store';
import type { WiFiNetwork, WiFiCredentials, SystemStatus, ApiResponse } from '../types';

// Reactive state stores
export const networks = writable<WiFiNetwork[]>([]);
export const status = writable<SystemStatus | null>(null);
export const isScanning = writable(false);
export const isConnecting = writable(false);
export const isLoading = writable(false);
export const error = writable<string | null>(null);
export const lastScanTime = writable<number | null>(null);

// Derived stores (computed values)
export const currentNetwork = derived(
	[status, networks],
	([$status, $networks]) => {
		if (!$status?.network.wifi.ssid) return null;
		return $networks.find(network => network.ssid === $status.network.wifi.ssid);
	}
);

export const isConnected = derived(
	status,
	($status) => $status?.network.wifi.status === 'connected'
);

export const isInHotspotMode = derived(
	status,
	($status) => $status?.network.wifi.mode === 'hotspot'
);

export const isScanOutdated = derived(
	lastScanTime,
	($lastScanTime) => {
		if (!$lastScanTime) return true;
		return Date.now() - $lastScanTime > 60000; // 1 minute
	}
);

// Helper functions
const setError = (message: string) => {
	error.set(message);
	setTimeout(() => error.set(null), 5000);
};

// API functions
export const scanNetworks = async () => {
	if (get(isScanning)) return;

	isScanning.set(true);
	error.set(null);

	try {
		const response = await fetch('/api/wifi/scan', {
			method: 'POST'
		});

		const result: ApiResponse = await response.json();

		if (result.success && result.data) {
			networks.set(result.data as WiFiNetwork[]);
			lastScanTime.set(Date.now());
		} else {
			throw new Error(result.message || 'Failed to scan networks');
		}
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Network scan failed';
		setError(message);
		console.error('WiFi scan error:', err);
	} finally {
		isScanning.set(false);
	}
};

export const connectToNetwork = async (credentials: WiFiCredentials): Promise<boolean> => {
	if (get(isConnecting)) return false;

	isConnecting.set(true);
	error.set(null);

	try {
		const response = await fetch('/api/wifi/connect', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(credentials)
		});

		const result: ApiResponse = await response.json();

		if (result.success) {
			// Update status to show connecting
			const currentStatus = get(status);
			if (currentStatus) {
				status.set({
					...currentStatus,
					network: {
						...currentStatus.network,
						wifi: {
							...currentStatus.network.wifi,
							status: 'connecting',
							ssid: credentials.ssid
						}
					}
				});
			}
			return true;
		} else {
			throw new Error(result.message || 'Connection failed');
		}
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Connection failed';
		setError(message);
		console.error('WiFi connection error:', err);
		return false;
	} finally {
		isConnecting.set(false);
	}
};

export const getStatus = async () => {
	isLoading.set(true);
	error.set(null);

	try {
		const response = await fetch('/api/wifi/status');
		const result: ApiResponse = await response.json();

		if (result.success && result.data) {
			status.set(result.data as SystemStatus);
		} else {
			throw new Error(result.message || 'Failed to get status');
		}
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Status check failed';
		setError(message);
		console.error('WiFi status error:', err);
	} finally {
		isLoading.set(false);
	}
};

export const resetToHotspot = async (): Promise<boolean> => {
	isLoading.set(true);
	error.set(null);

	try {
		const response = await fetch('/api/system/reset', {
			method: 'POST'
		});

		const result: ApiResponse = await response.json();

		if (result.success) {
			// Update status to show hotspot mode
			const currentStatus = get(status);
			if (currentStatus) {
				status.set({
					...currentStatus,
					network: {
						...currentStatus.network,
						wifi: {
							...currentStatus.network.wifi,
							mode: 'hotspot',
							status: 'disconnected'
						}
					}
				});
			}
			return true;
		} else {
			throw new Error(result.message || 'Reset failed');
		}
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Reset failed';
		setError(message);
		console.error('WiFi reset error:', err);
		return false;
	} finally {
		isLoading.set(false);
	}
};

// Utility functions
export const getNetworkBySSID = (ssid: string): WiFiNetwork | undefined => {
	return get(networks).find(network => network.ssid === ssid);
};

export const requiresPassword = (network: WiFiNetwork): boolean => {
	return network.security !== 'Open';
};

export const getSignalColor = (signal: number | undefined): string => {
	if (!signal) return 'text-gray-400';
	if (signal >= 75) return 'text-green-500';
	if (signal >= 50) return 'text-yellow-500';
	if (signal >= 25) return 'text-orange-500';
	return 'text-red-500';
};
EOF

# Create basic home page
echo "🏠 Creating home page..."
cat > src/routes/+page.svelte << 'EOF'
<script lang="ts">
	import { onMount } from 'svelte';
	import { status, getStatus, isLoading, error } from '$lib/stores/wifi';

	let refreshing = false;

	const refresh = async () => {
		refreshing = true;
		await getStatus();
		refreshing = false;
	};

	onMount(() => {
		getStatus();
		// Auto-refresh every 30 seconds
		const interval = setInterval(getStatus, 30000);
		return () => clearInterval(interval);
	});
</script>

<svelte:head>
	<title>Radio WiFi - Dashboard</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<header class="bg-white dark:bg-gray-800 shadow">
		<div class="max-w-md mx-auto px-4">
			<div class="flex items-center justify-between py-4">
				<div class="flex items-center space-x-3">
					<div class="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
						<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
								d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
						</svg>
					</div>
					<div>
						<h1 class="text-xl font-bold text-gray-900 dark:text-white">
							Radio WiFi
						</h1>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							{$status?.hostname || 'radio'}.local
						</p>
					</div>
				</div>
				<button
					on:click={refresh}
					disabled={refreshing}
					class="btn-secondary"
				>
					<svg class="w-4 h-4" class:animate-spin={refreshing} fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
							d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
					</svg>
				</button>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-md mx-auto px-4 py-6">
		<!-- Error Display -->
		{#if $error}
			<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
				<div class="flex items-center">
					<svg class="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
							d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<p class="text-red-800 dark:text-red-200 text-sm">
						{$error}
					</p>
				</div>
			</div>
		{/if}

		<!-- Status Card -->
		<div class="card p-6 mb-6">
			<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">WiFi Status</h2>

			{#if $isLoading}
				<div class="animate-pulse">
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
				</div>
			{:else if $status}
				<div class="space-y-3">
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Status:</span>
						<span class="text-sm font-medium" class:text-green-600={$status.network.wifi.status === 'connected'}
							class:text-yellow-600={$status.network.wifi.status === 'connecting'}
							class:text-red-600={$status.network.wifi.status === 'disconnected'}>
							{$status.network.wifi.status}
						</span>
					</div>

					{#if $status.network.wifi.ssid}
						<div class="flex justify-between items-center">
							<span class="text-sm text-gray-600 dark:text-gray-400">Network:</span>
							<span class="text-sm font-medium text-gray-900 dark:text-white">
								{$status.network.wifi.ssid}
							</span>
						</div>
					{/if}

					{#if $status.network.wifi.ip}
						<div class="flex justify-between items-center">
							<span class="text-sm text-gray-600 dark:text-gray-400">IP Address:</span>
							<span class="text-sm font-mono text-gray-900 dark:text-white">
								{$status.network.wifi.ip}
							</span>
						</div>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Action Buttons -->
		<div class="space-y-3">
			<a href="/setup" class="btn-primary w-full justify-center">
				<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
						d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
				</svg>
				WiFi Setup
			</a>

			<a href="/status" class="btn-secondary w-full justify-center">
				<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
						d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
				</svg>
				System Status
			</a>

			<a href="/settings" class="btn-secondary w-full justify-center">
				<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
						d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
				</svg>
				Settings
			</a>
		</div>
	</main>
</div>
EOF

# Create basic setup page
echo "🔧 Creating setup page..."
cat > src/routes/setup/+page.svelte << 'EOF'
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		networks,
		isScanning,
		isConnecting,
		error,
		scanNetworks,
		connectToNetwork,
		getSignalColor,
		requiresPassword
	} from '$lib/stores/wifi';

	let selectedNetwork: any = null;
	let password = '';
	let showPassword = false;

	onMount(() => {
		scanNetworks();
	});

	const handleNetworkSelect = (network: any) => {
		selectedNetwork = network;
		password = '';
	};

	const handleConnect = async () => {
		if (!selectedNetwork) return;

		const success = await connectToNetwork({
			ssid: selectedNetwork.ssid,
			password: password,
			security: selectedNetwork.security
		});

		if (success) {
			goto('/');
		}
	};
</script>

<svelte:head>
	<title>Radio WiFi - Setup</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<header class="bg-white dark:bg-gray-800 shadow">
		<div class="max-w-md mx-auto px-4">
			<div class="flex items-center justify-between py-4">
				<div class="flex items-center space-x-3">
					<button
						on:click={() => goto('/')}
						class="btn-secondary p-2"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
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
					on:click={scanNetworks}
					disabled={$isScanning}
					class="btn-secondary p-2"
				>
					<svg class="w-4 h-4" class:animate-spin={$isScanning} fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
							d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
					</svg>
				</button>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-md mx-auto px-4 py-6">
		<!-- Error Display -->
		{#if $error}
			<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
				<div class="flex items-center">
					<svg class="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
							d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<p class="text-red-800 dark:text-red-200 text-sm">
						{$error}
					</p>
				</div>
			</div>
		{/if}

		<!-- Networks List -->
		<div class="card mb-6">
			<div class="p-4 border-b border-gray-200 dark:border-gray-700">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Available Networks</h2>
			</div>

			<div class="max-h-96 overflow-y-auto">
				{#if $isScanning}
					<div class="p-6 text-center">
						<svg class="w-8 h-8 animate-spin text-primary-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
								d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
						</svg>
						<p class="text-gray-600 dark:text-gray-400">Scanning for networks...</p>
					</div>
				{:else if $networks.length === 0}
					<div class="p-6 text-center">
						<svg class="w-8 h-8 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
								d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
						</svg>
						<p class="text-gray-600 dark:text-gray-400">No networks found</p>
						<button on:click={scanNetworks} class="btn-primary mt-4">
							Scan Again
						</button>
					</div>
				{:else}
					{#each $networks as network}
						<button
							on:click={() => handleNetworkSelect(network)}
							class="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-200 dark:border-gray-700 last:border-b-0"
							class:bg-primary-50={selectedNetwork?.ssid === network.ssid}
							class:dark:bg-primary-900/20={selectedNetwork?.ssid === network.ssid}
						>
							<div class="flex items-center justify-between">
								<div class="flex-1">
									<div class="flex items-center space-x-2">
										<span class="font-medium text-gray-900 dark:text-white">
											{network.ssid}
										</span>
										{#if network.security !== 'Open'}
											<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
													d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
											</svg>
										{/if}
									</div>
									<p class="text-sm text-gray-500 dark:text-gray-400">
										{network.security}
									</p>
								</div>
								<div class="flex items-center space-x-2">
									<span class="text-sm {getSignalColor(network.signal)}">
										{network.signal}%
									</span>
									<svg class="w-4 h-4 {getSignalColor(network.signal)}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
											d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
									</svg>
								</div>
							</div>
						</button>
					{/each}
				{/if}
			</div>
		</div>

		<!-- Connection Form -->
		{#if selectedNetwork}
			<div class="card p-6">
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
					Connect to {selectedNetwork.ssid}
				</h3>

				{#if requiresPassword(selectedNetwork)}
					<div class="mb-4">
						<label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Password
						</label>
						<div class="relative">
							<input
								id="password"
								type={showPassword ? 'text' : 'password'}
								bind:value={password}
								placeholder="Enter WiFi password"
								class="input pr-10"
								disabled={$isConnecting}
							/>
							<button
								type="button"
								on:click={() => showPassword = !showPassword}
								class="absolute inset-y-0 right-0 pr-3 flex items-center"
							>
								{#if showPassword}
									<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
											d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
									</svg>
								{:else}
									<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
											d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
											d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
									</svg>
								{/if}
							</button>
						</div>
					</div>
				{/if}

				<div class="flex space-x-3">
					<button
						on:click={() => selectedNetwork = null}
						class="btn-secondary flex-1"
						disabled={$isConnecting}
					>
						Cancel
					</button>
					<button
						on:click={handleConnect}
						class="btn-primary flex-1"
						disabled={$isConnecting || (requiresPassword(selectedNetwork) && !password.trim())}
					>
						{#if $isConnecting}
							<svg class="w-4 h-4 animate-spin mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
									d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
							</svg>
							Connecting...
						{:else}
							Connect
						{/if}
					</button>
				</div>
			</div>
		{/if}
	</main>
</div>
EOF

# Create status page
echo "📊 Creating status page..."
cat > src/routes/status/+page.svelte << 'EOF'
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { status, getStatus, isLoading, error } from '$lib/stores/wifi';

	onMount(() => {
		getStatus();
		const interval = setInterval(getStatus, 10000);
		return () => clearInterval(interval);
	});

	const formatUptime = (seconds: number) => {
		const days = Math.floor(seconds / 86400);
		const hours = Math.floor((seconds % 86400) / 3600);
		const minutes = Math.floor((seconds % 3600) / 60);

		if (days > 0) return `${days}d ${hours}h ${minutes}m`;
		if (hours > 0) return `${hours}h ${minutes}m`;
		return `${minutes}m`;
	};

	const formatBytes = (bytes: number) => {
		const sizes = ['B', 'KB', 'MB', 'GB'];
		if (bytes === 0) return '0 B';
		const i = Math.floor(Math.log(bytes) / Math.log(1024));
		return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
	};
</script>

<svelte:head>
	<title>Radio WiFi - System Status</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<header class="bg-white dark:bg-gray-800 shadow">
		<div class="max-w-md mx-auto px-4">
			<div class="flex items-center justify-between py-4">
				<div class="flex items-center space-x-3">
					<button
						on:click={() => goto('/')}
						class="btn-secondary p-2"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
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
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-md mx-auto px-4 py-6 space-y-6">
		<!-- Error Display -->
		{#if $error}
			<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
				<div class="flex items-center">
					<svg class="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
							d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<p class="text-red-800 dark:text-red-200 text-sm">
						{$error}
					</p>
				</div>
			</div>
		{/if}

		{#if $isLoading}
			<div class="space-y-6">
				{#each Array(4) as _}
					<div class="card p-6">
						<div class="animate-pulse">
							<div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
							<div class="space-y-2">
								<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
								<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{:else if $status}
			<!-- System Info -->
			<div class="card p-6">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">System Information</h2>
				<div class="space-y-3">
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Hostname:</span>
						<span class="text-sm font-medium text-gray-900 dark:text-white">
							{$status.hostname}
						</span>
					</div>
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Uptime:</span>
						<span class="text-sm font-medium text-gray-900 dark:text-white">
							{formatUptime($status.uptime)}
						</span>
					</div>
				</div>
			</div>

			<!-- Network Status -->
			<div class="card p-6">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Network Status</h2>
				<div class="space-y-3">
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">WiFi Status:</span>
						<span class="text-sm font-medium"
							class:text-green-600={$status.network.wifi.status === 'connected'}
							class:text-yellow-600={$status.network.wifi.status === 'connecting'}
							class:text-red-600={$status.network.wifi.status === 'disconnected'}>
							{$status.network.wifi.status}
						</span>
					</div>
					{#if $status.network.wifi.ssid}
						<div class="flex justify-between items-center">
							<span class="text-sm text-gray-600 dark:text-gray-400">Network:</span>
							<span class="text-sm font-medium text-gray-900 dark:text-white">
								{$status.network.wifi.ssid}
							</span>
						</div>
					{/if}
					{#if $status.network.wifi.ip}
						<div class="flex justify-between items-center">
							<span class="text-sm text-gray-600 dark:text-gray-400">IP Address:</span>
							<span class="text-sm font-mono text-gray-900 dark:text-white">
								{$status.network.wifi.ip}
							</span>
						</div>
					{/if}
					{#if $status.network.wifi.signal}
						<div class="flex justify-between items-center">
							<span class="text-sm text-gray-600 dark:text-gray-400">Signal:</span>
							<span class="text-sm font-medium text-gray-900 dark:text-white">
								{$status.network.wifi.signal}%
							</span>
						</div>
					{/if}
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Mode:</span>
						<span class="text-sm font-medium text-gray-900 dark:text-white">
							{$status.network.wifi.mode}
						</span>
					</div>
				</div>
			</div>

			<!-- Memory Usage -->
			<div class="card p-6">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Memory Usage</h2>
				<div class="space-y-3">
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Total:</span>
						<span class="text-sm font-medium text-gray-900 dark:text-white">
							{formatBytes($status.memory.total)}
						</span>
					</div>
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Used:</span>
						<span class="text-sm font-medium text-gray-900 dark:text-white">
							{formatBytes($status.memory.used)}
						</span>
					</div>
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Free:</span>
						<span class="text-sm font-medium text-gray-900 dark:text-white">
							{formatBytes($status.memory.free)}
						</span>
					</div>
					<div class="mt-2">
						<div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
							<span>Usage</span>
							<span>{Math.round(($status.memory.used / $status.memory.total) * 100)}%</span>
						</div>
						<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
							<div
								class="bg-primary-600 h-2 rounded-full transition-all duration-300"
								style="width: {($status.memory.used / $status.memory.total) * 100}%"
							></div>
						</div>
					</div>
				</div>
			</div>

			<!-- CPU Information -->
			<div class="card p-6">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">CPU Information</h2>
				<div class="space-y-3">
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Load:</span>
						<span class="text-sm font-medium text-gray-900 dark:text-white">
							{$status.cpu.load.toFixed(2)}
						</span>
					</div>
					{#if $status.cpu.temperature}
						<div class="flex justify-between items-center">
							<span class="text-sm text-gray-600 dark:text-gray-400">Temperature:</span>
							<span class="text-sm font-medium text-gray-900 dark:text-white">
								{$status.cpu.temperature.toFixed(1)}°C
							</span>
						</div>
					{/if}
				</div>
			</div>
		{/if}
	</main>
</div>
EOF

# Create settings page placeholder
echo "⚙️  Creating settings page..."
cat > src/routes/settings/+page.svelte << 'EOF'
<script lang="ts">
	import { goto } from '$app/navigation';
</script>

<svelte:head>
	<title>Radio WiFi - Settings</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<header class="bg-white dark:bg-gray-800 shadow">
		<div class="max-w-md mx-auto px-4">
			<div class="flex items-center justify-between py-4">
				<div class="flex items-center space-x-3">
					<button
						on:click={() => goto('/')}
						class="btn-secondary p-2"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
						</svg>
					</button>
					<div>
						<h1 class="text-xl font-bold text-gray-900 dark:text-white">
							Settings
						</h1>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							System preferences
						</p>
					</div>
				</div>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-md mx-auto px-4 py-6">
		<div class="card p-6 text-center">
			<svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
					d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
			</svg>
			<h2 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Settings Coming Soon</h2>
			<p class="text-gray-600 dark:text-gray-400 text-sm mb-4">
				Advanced settings and configuration options will be available in a future update.
			</p>
			<button on:click={() => goto('/')} class="btn-primary">
				Return Home
			</button>
		</div>
	</main>
</div>
EOF

# Create SignalStrength component
echo "📶 Creating SignalStrength component..."
cat > src/lib/components/SignalStrength.svelte << 'EOF'
<script lang="ts">
	export let signal: number | undefined = undefined;
	export let size: 'sm' | 'md' | 'lg' = 'md';

	$: bars = signal ? Math.ceil((signal / 100) * 4) : 0;
	$: color = getSignalColor(signal);

	function getSignalColor(signal: number | undefined): string {
		if (!signal) return 'text-gray-400';
		if (signal >= 75) return 'text-green-500';
		if (signal >= 50) return 'text-yellow-500';
		if (signal >= 25) return 'text-orange-500';
		return 'text-red-500';
	}

	$: sizeClasses = {
		sm: 'w-4 h-4',
		md: 'w-5 h-5',
		lg: 'w-6 h-6'
	}[size];
</script>

<div class="flex items-center space-x-1 {color}">
	<svg class={sizeClasses} viewBox="0 0 24 24" fill="none" stroke="currentColor">
		<!-- Bar 1 (always visible if signal > 0) -->
		<rect
			x="2" y="18" width="2" height="4"
			fill={bars >= 1 ? 'currentColor' : 'none'}
			stroke="currentColor"
			stroke-width="0.5"
		/>
		<!-- Bar 2 -->
		<rect
			x="6" y="15" width="2" height="7"
			fill={bars >= 2 ? 'currentColor' : 'none'}
			stroke="currentColor"
			stroke-width="0.5"
		/>
		<!-- Bar 3 -->
		<rect
			x="10" y="12" width="2" height="10"
			fill={bars >= 3 ? 'currentColor' : 'none'}
			stroke="currentColor"
			stroke-width="0.5"
		/>
		<!-- Bar 4 -->
		<rect
			x="14" y="9" width="2" height="13"
			fill={bars >= 4 ? 'currentColor' : 'none'}
			stroke="currentColor"
			stroke-width="0.5"
		/>
	</svg>

	{#if signal !== undefined}
		<span class="text-xs font-medium">{signal}%</span>
	{/if}
</div>
EOF

# Create static assets
echo "🎯 Creating static assets..."
cat > static/favicon.ico << 'EOF'
EOF

# Create app icon
cat > static/icon-192.png << 'EOF'
EOF

# Create manifest
cat > static/manifest.json << 'EOF'
{
	"name": "Radio WiFi Configuration",
	"short_name": "Radio WiFi",
	"description": "Easy WiFi configuration for Raspberry Pi Radio",
	"start_url": "/",
	"display": "standalone",
	"theme_color": "#3b82f6",
	"background_color": "#ffffff",
	"icons": [
		{
			"src": "icon-192.png",
			"sizes": "192x192",
			"type": "image/png"
		}
	]
}
EOF

cd ..

echo "✅ SvelteKit frontend structure created successfully!"
echo ""
echo "📋 Next steps:"
echo "1. cd frontend && npm install"
echo "2. Start backend: docker-compose up radio-backend -d"
echo "3. Start frontend: cd frontend && npm run dev"
echo "4. Access app: http://localhost:3000"
echo ""
echo "🎯 The frontend will proxy API calls to the Docker backend automatically."
echo "📖 See SVELTEKIT-MIGRATION.md for detailed migration guide."
