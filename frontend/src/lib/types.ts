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

export interface SavedNetwork {
	id: number; // wpa_cli network ID
	ssid: string;
	current: boolean; // Currently connected
	disabled: boolean; // Network disabled in wpa_supplicant
}

export interface ConnectionProgress {
	status: 'idle' | 'connecting' | 'verifying' | 'success' | 'failed';
	attempt: number;
	maxAttempts: number;
	message: string;
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

export interface RadioStation {
	name: string;
	url: string;
	slot?: number;
	country?: string;
	location?: string;
	genre?: string;
	bitrate?: string;
	language?: string;
}

export interface PlaybackStatus {
	is_playing: boolean;
	current_station?: RadioStation | null;
	current_slot?: number | null;
	playback_state?: string;
}
