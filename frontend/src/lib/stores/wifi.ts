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
export const currentNetwork = derived([status, networks], ([$status, $networks]) => {
	if (!$status?.network.wifi.ssid) return null;
	return $networks.find((network) => network.ssid === $status.network.wifi.ssid);
});

export const isConnected = derived(
	status,
	($status) => $status?.network.wifi.status === 'connected'
);

export const isInHotspotMode = derived(
	status,
	($status) => $status?.network.wifi.mode === 'hotspot'
);

export const isScanOutdated = derived(lastScanTime, ($lastScanTime) => {
	if (!$lastScanTime) return true;
	return Date.now() - $lastScanTime > 60000; // 1 minute
});

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
			// Transform backend network data to expected format
			const backendData = result.data as any[];
			const wifiNetworks: WiFiNetwork[] = backendData.map((network) => ({
				ssid: network.ssid,
				signal: network.signal,
				security: network.encryption as WiFiNetwork['security'],
				frequency: network.frequency,
				connected: false
			}));
			networks.set(wifiNetworks);
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
			// Transform backend response to expected SystemStatus structure
			const backendData = result.data as any;
			const systemStatus: SystemStatus = {
				hostname: 'radio', // Default value
				uptime: 0,
				memory: { total: 0, used: 0, free: 0 },
				cpu: { load: 0 },
				network: {
					wifi: {
						wifiInterface: 'wlan0',
						status: backendData.connected ? 'connected' : 'disconnected',
						ssid: backendData.ssid || undefined,
						ip: backendData.ip_address || undefined,
						signal: backendData.signal_strength || undefined,
						mode: backendData.mode === 'host' ? 'hotspot' : 'client'
					}
				},
				services: {}
			};
			status.set(systemStatus);
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
	return get(networks).find((network) => network.ssid === ssid);
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
