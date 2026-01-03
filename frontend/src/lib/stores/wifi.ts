// WiFi management store for SvelteKit
// Replaces Nuxt useWiFi composable

import { writable, derived, get } from 'svelte/store';
import type {
	WiFiNetwork,
	WiFiCredentials,
	SystemStatus,
	ApiResponse,
	SavedNetwork,
	ConnectionProgress
} from '../types';

// Reactive state stores
export const networks = writable<WiFiNetwork[]>([]);
export const status = writable<SystemStatus | null>(null);
export const isScanning = writable(false);
export const isConnecting = writable(false);
export const isLoading = writable(false);
export const error = writable<string | null>(null);
export const lastScanTime = writable<number | null>(null);

// Saved networks state
export const savedNetworks = writable<SavedNetwork[]>([]);
export const isLoadingSaved = writable(false);

// Connection progress tracking
export const connectionProgress = writable<ConnectionProgress>({
	status: 'idle',
	attempt: 0,
	maxAttempts: 3,
	message: ''
});

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
	isConnecting.set(true);
	error.set(null);

	// Initialize progress
	connectionProgress.set({
		status: 'connecting',
		attempt: 1,
		maxAttempts: 3,
		message: `Connecting to ${credentials.ssid}...`
	});

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
			// Connection successful
			connectionProgress.set({
				status: 'success',
				attempt: 3,
				maxAttempts: 3,
				message: `Connected to ${credentials.ssid}! System rebooting...`
			});

			// Update status
			const currentStatus = get(status);
			if (currentStatus) {
				status.set({
					...currentStatus,
					network: {
						...currentStatus.network,
						wifi: {
							...currentStatus.network.wifi,
							status: 'connected',
							ssid: credentials.ssid
						}
					}
				});
			}

			// Clear progress after delay
			setTimeout(() => {
				connectionProgress.set({
					status: 'idle',
					attempt: 0,
					maxAttempts: 3,
					message: ''
				});
			}, 5000);

			return true;
		} else {
			// Connection failed after retries
			connectionProgress.set({
				status: 'failed',
				attempt: 3,
				maxAttempts: 3,
				message: result.message || 'Connection failed'
			});

			error.set(result.message || 'Connection failed');

			// Clear progress after delay
			setTimeout(() => {
				connectionProgress.set({
					status: 'idle',
					attempt: 0,
					maxAttempts: 3,
					message: ''
				});
			}, 5000);

			return false;
		}
	} catch (err) {
		const errorMessage = err instanceof Error ? err.message : 'Connection failed';

		connectionProgress.set({
			status: 'failed',
			attempt: 0,
			maxAttempts: 3,
			message: errorMessage
		});

		error.set(errorMessage);
		console.error('Error connecting to network:', err);

		// Clear progress after delay
		setTimeout(() => {
			connectionProgress.set({
				status: 'idle',
				attempt: 0,
				maxAttempts: 3,
				message: ''
			});
		}, 5000);

		return false;
	} finally {
		isConnecting.set(false);
	}
};

export const getStatus = async () => {
	isLoading.set(true);
	error.set(null);

	try {
		const response = await fetch('/api/system/status');

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		// Backend now returns SystemStatus directly (no ApiResponse wrapper)
		const systemStatus: SystemStatus = await response.json();
		status.set(systemStatus);
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Status check failed';
		setError(message);
		console.error('System status error:', err);
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

/**
 * Get list of saved WiFi networks from wpa_cli
 */
export const getSavedNetworks = async () => {
	isLoadingSaved.set(true);
	error.set(null);

	try {
		const response = await fetch('/api/wifi/saved');

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}`);
		}

		const result: ApiResponse = await response.json();

		if (result.success && result.data) {
			savedNetworks.set(result.data.networks || []);
		} else {
			throw new Error(result.message || 'Failed to get saved networks');
		}
	} catch (err) {
		const errorMessage = err instanceof Error ? err.message : 'Failed to load saved networks';
		error.set(errorMessage);
		console.error('Error getting saved networks:', err);

		// Auto-dismiss error
		setTimeout(() => error.set(null), 5000);
	} finally {
		isLoadingSaved.set(false);
	}
};

/**
 * Forget/remove a saved WiFi network
 */
export const forgetNetwork = async (networkId: number, ssid: string): Promise<boolean> => {
	isLoadingSaved.set(true);
	error.set(null);

	try {
		const response = await fetch(`/api/wifi/saved/${networkId}`, {
			method: 'DELETE'
		});

		if (!response.ok) {
			const result = await response.json();
			throw new Error(result.detail || `HTTP ${response.status}`);
		}

		const result: ApiResponse = await response.json();

		if (result.success) {
			// Refresh saved networks list
			await getSavedNetworks();
			return true;
		} else {
			throw new Error(result.message || 'Failed to forget network');
		}
	} catch (err) {
		const errorMessage = err instanceof Error ? err.message : `Failed to forget ${ssid}`;
		error.set(errorMessage);
		console.error('Error forgetting network:', err);

		// Auto-dismiss error
		setTimeout(() => error.set(null), 5000);
		return false;
	} finally {
		isLoadingSaved.set(false);
	}
};

// WebSocket update handlers (called from websocket.ts)
export function updateWiFiStatus(newStatus: SystemStatus) {
	status.set(newStatus);
}

export function updateWiFiNetworks(newNetworks: WiFiNetwork[]) {
	networks.set(newNetworks);
	lastScanTime.set(Date.now());
}
