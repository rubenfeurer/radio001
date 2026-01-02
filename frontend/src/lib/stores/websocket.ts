import { writable } from 'svelte/store';
import { updateWiFiStatus } from './wifi';
import { updateVolume, updatePlaybackStatus, updateStations, updateCurrentStation } from './radio';

export interface WebSocketMessage {
	type: string;
	data?: any;
}

class WebSocketClient {
	private ws: WebSocket | null = null;
	private reconnectTimer: number | null = null;
	private readonly reconnectDelay = 3000;
	private shouldReconnect = true;

	connect() {
		if (this.ws?.readyState === WebSocket.OPEN) {
			console.log('WebSocket already connected');
			return;
		}

		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		const wsUrl = `${protocol}//${window.location.host}/ws/`;

		console.log('Connecting to WebSocket:', wsUrl);

		try {
			this.ws = new WebSocket(wsUrl);

			this.ws.onopen = () => {
				console.log('WebSocket connected');
				isConnected.set(true);
				if (this.reconnectTimer) {
					clearTimeout(this.reconnectTimer);
					this.reconnectTimer = null;
				}

				// Request initial status
				this.send({ type: 'get_status' });
			};

			this.ws.onmessage = (event) => {
				try {
					const message: WebSocketMessage = JSON.parse(event.data);
					handleMessage(message);
				} catch (error) {
					console.error('Failed to parse WebSocket message:', error);
				}
			};

			this.ws.onclose = (event) => {
				console.log('WebSocket disconnected:', event.code, event.reason);
				isConnected.set(false);
				this.ws = null;

				if (this.shouldReconnect) {
					this.scheduleReconnect();
				}
			};

			this.ws.onerror = (error) => {
				console.error('WebSocket error:', error);
			};
		} catch (error) {
			console.error('Failed to create WebSocket connection:', error);
			isConnected.set(false);
			if (this.shouldReconnect) {
				this.scheduleReconnect();
			}
		}
	}

	send(message: WebSocketMessage) {
		if (this.ws?.readyState === WebSocket.OPEN) {
			try {
				this.ws.send(JSON.stringify(message));
			} catch (error) {
				console.error('Failed to send WebSocket message:', error);
			}
		} else {
			console.warn('WebSocket not connected, cannot send message:', message);
		}
	}

	private scheduleReconnect() {
		if (!this.reconnectTimer && this.shouldReconnect) {
			console.log(`Reconnecting in ${this.reconnectDelay}ms...`);
			this.reconnectTimer = window.setTimeout(() => {
				this.reconnectTimer = null;
				this.connect();
			}, this.reconnectDelay);
		}
	}

	disconnect() {
		this.shouldReconnect = false;
		if (this.reconnectTimer) {
			clearTimeout(this.reconnectTimer);
			this.reconnectTimer = null;
		}
		if (this.ws) {
			this.ws.close();
			this.ws = null;
		}
		isConnected.set(false);
	}
}

function handleMessage(message: WebSocketMessage) {
	switch (message.type) {
		case 'system_status':
			if (message.data) {
				updateWiFiStatus(message.data);
			}
			break;

		case 'volume_update':
			if (message.data?.volume !== undefined) {
				updateVolume(message.data.volume);
			}
			break;

		case 'playback_status':
			if (message.data) {
				updatePlaybackStatus(message.data);
			}
			break;

		case 'station_change':
			if (message.data?.station) {
				updateCurrentStation(message.data.station);
			}
			break;

		case 'stations_list':
			if (message.data?.stations) {
				updateStations(message.data.stations);
			}
			break;

		case 'pong':
			// Heartbeat response
			break;

		default:
			console.warn('Unknown WebSocket message type:', message.type);
	}
}

export const isConnected = writable(false);
export const wsClient = new WebSocketClient();
