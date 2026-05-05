import type {
	WiFiNetwork,
	WiFiCredentials,
	SystemStatus,
	ApiResponse,
	SavedNetwork,
	ConnectionProgress
} from '../types';

export const wifiState = $state({
	networks: [] as WiFiNetwork[],
	status: null as SystemStatus | null,
	isScanning: false,
	isConnecting: false,
	isLoading: false,
	error: null as string | null,
	lastScanTime: null as number | null,
	savedNetworks: [] as SavedNetwork[],
	isLoadingSaved: false,
	connectionProgress: {
		status: 'idle',
		attempt: 0,
		maxAttempts: 1,
		message: ''
	} as ConnectionProgress
});

function setError(message: string) {
	wifiState.error = message;
	setTimeout(() => (wifiState.error = null), 5000);
}

export const scanNetworks = async () => {
	if (wifiState.isScanning) return;

	wifiState.isScanning = true;
	wifiState.error = null;

	try {
		const response = await fetch('/api/wifi/scan', { method: 'POST' });
		const result: ApiResponse = await response.json();

		if (result.success && result.data) {
			const backendData = result.data as any[];
			wifiState.networks = backendData.map((network) => ({
				ssid: network.ssid,
				signal: network.signal,
				security: network.encryption as WiFiNetwork['security'],
				frequency: network.frequency,
				connected: false
			}));
			wifiState.lastScanTime = Date.now();
		} else {
			throw new Error(result.message || 'Failed to scan networks');
		}
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Network scan failed';
		setError(message);
		console.error('WiFi scan error:', err);
	} finally {
		wifiState.isScanning = false;
	}
};

export const connectToNetwork = async (credentials: WiFiCredentials): Promise<boolean> => {
	wifiState.isConnecting = true;
	wifiState.error = null;

	wifiState.connectionProgress = {
		status: 'connecting',
		attempt: 1,
		maxAttempts: 1,
		message: `Connecting to ${credentials.ssid}...`
	};

	try {
		const response = await fetch('/api/wifi/connect', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(credentials)
		});

		const result: ApiResponse = await response.json();

		if (result.success) {
			wifiState.connectionProgress = {
				status: 'verifying',
				attempt: 1,
				maxAttempts: 1,
				message: `Verifying connection to ${credentials.ssid}...`
			};

			let verified = false;
			for (let i = 0; i < 3; i++) {
				await new Promise((resolve) => setTimeout(resolve, 1000));
				try {
					const statusResponse = await fetch('/api/wifi/status');
					const statusResult: ApiResponse = await statusResponse.json();
					if (
						statusResult.success &&
						statusResult.data?.connected &&
						statusResult.data?.ssid === credentials.ssid
					) {
						verified = true;
						break;
					}
				} catch (e) {
					console.warn('Status check failed:', e);
				}
			}

			const msg = verified
				? `Connected to ${credentials.ssid}!`
				: `Connection initiated to ${credentials.ssid}`;
			wifiState.connectionProgress = { status: 'success', attempt: 1, maxAttempts: 1, message: msg };

			if (verified && wifiState.status) {
				wifiState.status = {
					...wifiState.status,
					network: {
						...wifiState.status.network,
						wifi: { ...wifiState.status.network.wifi, status: 'connected', ssid: credentials.ssid }
					}
				};
			}

			setTimeout(() => {
				wifiState.connectionProgress = { status: 'idle', attempt: 0, maxAttempts: 1, message: '' };
			}, 3000);

			return true;
		} else {
			wifiState.connectionProgress = {
				status: 'failed',
				attempt: 1,
				maxAttempts: 1,
				message: result.message || 'Connection failed'
			};
			wifiState.error = result.message || 'Connection failed';
			setTimeout(() => {
				wifiState.connectionProgress = { status: 'idle', attempt: 0, maxAttempts: 1, message: '' };
			}, 5000);
			return false;
		}
	} catch (err) {
		const errorMessage = err instanceof Error ? err.message : 'Connection failed';
		wifiState.connectionProgress = {
			status: 'failed',
			attempt: 0,
			maxAttempts: 1,
			message: errorMessage
		};
		wifiState.error = errorMessage;
		console.error('Error connecting to network:', err);
		setTimeout(() => {
			wifiState.connectionProgress = { status: 'idle', attempt: 0, maxAttempts: 1, message: '' };
		}, 5000);
		return false;
	} finally {
		wifiState.isConnecting = false;
	}
};

export const getStatus = async () => {
	wifiState.isLoading = true;
	wifiState.error = null;

	try {
		const response = await fetch('/api/system/status');
		if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		const systemStatus: SystemStatus = await response.json();
		wifiState.status = systemStatus;
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Status check failed';
		setError(message);
		console.error('System status error:', err);
	} finally {
		wifiState.isLoading = false;
	}
};

export const resetToHotspot = async (): Promise<boolean> => {
	wifiState.isLoading = true;
	wifiState.error = null;

	try {
		const response = await fetch('/api/system/hotspot-mode', { method: 'POST' });
		const result: ApiResponse = await response.json();

		if (result.success) {
			if (wifiState.status) {
				wifiState.status = {
					...wifiState.status,
					network: {
						...wifiState.status.network,
						wifi: { ...wifiState.status.network.wifi, mode: 'hotspot', status: 'disconnected' }
					}
				};
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
		wifiState.isLoading = false;
	}
};

export const getNetworkBySSID = (ssid: string): WiFiNetwork | undefined => {
	return wifiState.networks.find((n) => n.ssid === ssid);
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

export const getSavedNetworks = async () => {
	wifiState.isLoadingSaved = true;
	wifiState.error = null;

	try {
		const response = await fetch('/api/wifi/saved');
		if (!response.ok) throw new Error(`HTTP ${response.status}`);

		const result: ApiResponse = await response.json();
		if (result.success && result.data) {
			wifiState.savedNetworks = result.data.networks || [];
		} else {
			throw new Error(result.message || 'Failed to get saved networks');
		}
	} catch (err) {
		const errorMessage = err instanceof Error ? err.message : 'Failed to load saved networks';
		wifiState.error = errorMessage;
		console.error('Error getting saved networks:', err);
		setTimeout(() => (wifiState.error = null), 5000);
	} finally {
		wifiState.isLoadingSaved = false;
	}
};

export const forgetNetwork = async (networkId: number, ssid: string): Promise<boolean> => {
	wifiState.isLoadingSaved = true;
	wifiState.error = null;

	try {
		const response = await fetch(`/api/wifi/saved/${networkId}`, { method: 'DELETE' });
		if (!response.ok) {
			const result = await response.json();
			throw new Error(result.detail || `HTTP ${response.status}`);
		}

		const result: ApiResponse = await response.json();
		if (result.success) {
			await getSavedNetworks();
			return true;
		} else {
			throw new Error(result.message || 'Failed to forget network');
		}
	} catch (err) {
		const errorMessage = err instanceof Error ? err.message : `Failed to forget ${ssid}`;
		wifiState.error = errorMessage;
		console.error('Error forgetting network:', err);
		setTimeout(() => (wifiState.error = null), 5000);
		return false;
	} finally {
		wifiState.isLoadingSaved = false;
	}
};

export function updateWiFiStatus(newStatus: SystemStatus) {
	wifiState.status = newStatus;
}

export function updateWiFiNetworks(newNetworks: WiFiNetwork[]) {
	wifiState.networks = newNetworks;
	wifiState.lastScanTime = Date.now();
}
