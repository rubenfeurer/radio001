import { updateWiFiStatus } from './wifi.svelte';
import { updateVolume, updatePlaybackStatus, updateStations, updateCurrentStation } from './radio.svelte';

export interface WebSocketMessage {
	type: string;
	data?: any;
}

export const wsState = $state({ isConnected: false });

const RECONNECT_BASE_DELAY = 1000;
const RECONNECT_MAX_DELAY = 30000;
const PING_INTERVAL = 15000;
const LIVENESS_TIMEOUT = 10000;

class WebSocketClient {
	private ws: WebSocket | null = null;
	private reconnectTimer: number | null = null;
	private pingTimer: number | null = null;
	private livenessTimer: number | null = null;
	private reconnectDelay = RECONNECT_BASE_DELAY;
	private shouldReconnect = true;

	connect() {
		// connect() states the intent "I want a live connection" — it must
		// undo a prior disconnect(), or one visit to a disconnecting page
		// would permanently disable reconnection for the SPA session
		this.shouldReconnect = true;

		// An in-flight CONNECTING socket will resolve on its own; creating a
		// second one would orphan it with live handlers (state flapping)
		if (
			this.ws?.readyState === WebSocket.OPEN ||
			this.ws?.readyState === WebSocket.CONNECTING
		) {
			return;
		}

		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		const wsUrl = `${protocol}//${window.location.host}/ws/`;

		try {
			this.ws = new WebSocket(wsUrl);

			this.ws.onopen = () => {
				wsState.isConnected = true;
				this.reconnectDelay = RECONNECT_BASE_DELAY;
				if (this.reconnectTimer) {
					clearTimeout(this.reconnectTimer);
					this.reconnectTimer = null;
				}
				this.startPing();
				setTimeout(() => this.send({ type: 'get_status' }), 100);
			};

			this.ws.onmessage = (event) => {
				this.markAlive();
				try {
					const message: WebSocketMessage = JSON.parse(event.data);
					handleMessage(message);
				} catch (error) {
					console.error('Failed to parse WebSocket message:', error);
				}
			};

			this.ws.onclose = () => {
				wsState.isConnected = false;
				this.ws = null;
				this.stopPing();
				if (this.shouldReconnect) this.scheduleReconnect();
			};

			this.ws.onerror = (error) => {
				console.error('WebSocket error:', error);
			};
		} catch (error) {
			console.error('Failed to create WebSocket connection:', error);
			wsState.isConnected = false;
			if (this.shouldReconnect) this.scheduleReconnect();
		}
	}

	send(message: WebSocketMessage) {
		if (this.ws?.readyState === WebSocket.OPEN) {
			try {
				this.ws.send(JSON.stringify(message));
			} catch (error) {
				console.error('Failed to send WebSocket message:', error);
			}
		}
	}

	// Half-open TCP connections (WiFi blips, hotspot transitions) look
	// connected forever; ping and force-close if nothing comes back.
	// Any inbound message counts as liveness, not just pong.
	private startPing() {
		this.stopPing();
		this.pingTimer = window.setInterval(() => {
			this.send({ type: 'ping' });
			if (this.livenessTimer === null) {
				this.livenessTimer = window.setTimeout(() => {
					console.warn('WebSocket liveness timeout — forcing reconnect');
					this.livenessTimer = null;
					this.ws?.close();
				}, LIVENESS_TIMEOUT);
			}
		}, PING_INTERVAL);
	}

	private markAlive() {
		if (this.livenessTimer !== null) {
			clearTimeout(this.livenessTimer);
			this.livenessTimer = null;
		}
	}

	private stopPing() {
		if (this.pingTimer !== null) {
			clearInterval(this.pingTimer);
			this.pingTimer = null;
		}
		this.markAlive();
	}

	private scheduleReconnect() {
		if (!this.reconnectTimer && this.shouldReconnect) {
			this.reconnectTimer = window.setTimeout(() => {
				this.reconnectTimer = null;
				this.connect();
			}, this.reconnectDelay);
			// Exponential backoff, reset to base on successful open
			this.reconnectDelay = Math.min(this.reconnectDelay * 2, RECONNECT_MAX_DELAY);
		}
	}

	disconnect() {
		this.shouldReconnect = false;
		if (this.reconnectTimer) {
			clearTimeout(this.reconnectTimer);
			this.reconnectTimer = null;
		}
		this.stopPing();
		if (this.ws) {
			this.ws.close();
			this.ws = null;
		}
		wsState.isConnected = false;
	}
}

function handleMessage(message: WebSocketMessage) {
	switch (message.type) {
		case 'system_status':
			if (message.data) updateWiFiStatus(message.data);
			break;

		case 'volume_update':
			if (message.data?.volume !== undefined) updateVolume(message.data.volume);
			if (message.data?.is_playing !== undefined) {
				updatePlaybackStatus({
					is_playing: message.data.is_playing,
					current_station: message.data.current_station_info || null,
					current_slot: message.data.current_station || null,
					playback_state: message.data.playback_state
				});
			}
			break;

		case 'playback_status':
			if (message.data) {
				updatePlaybackStatus({
					is_playing: message.data.is_playing,
					current_station: message.data.current_station_info || null,
					current_slot: message.data.current_station || null,
					playback_state: message.data.playback_state
				});
				if (message.data.volume !== undefined) updateVolume(message.data.volume);
			}
			break;

		case 'station_change':
			if (message.data?.station) updateCurrentStation(message.data.station);
			break;

		case 'stations_update':
			if (message.data?.stations) updateStations(message.data.stations);
			break;

		case 'pong':
			break;

		default:
			console.warn('Unknown WebSocket message type:', message.type);
	}
}

export const wsClient = new WebSocketClient();
