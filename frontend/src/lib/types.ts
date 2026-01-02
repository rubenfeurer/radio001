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

export interface RadioStation {
	id: string;
	name: string;
	url: string;
	genre?: string;
	bitrate?: number;
	country?: string;
	favicon?: string;
}

export interface PlaybackStatus {
	is_playing: boolean;
	current_station?: RadioStation;
	stream_title?: string;
	bitrate?: number;
	codec?: string;
	error?: string;
}
