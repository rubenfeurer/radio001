import { writable, derived } from 'svelte/store';
import { wsClient } from './websocket';
import type { RadioStation, PlaybackStatus } from '$lib/types';

// State stores
export const stations = writable<RadioStation[]>([]);
export const currentStation = writable<RadioStation | null>(null);
export const volume = writable<number>(50);
export const isPlaying = writable<boolean>(false);
export const playbackStatus = writable<PlaybackStatus | null>(null);

// Derived stores
export const hasStations = derived(stations, ($stations) => $stations.length > 0);

// Actions
export function playStation(station: RadioStation) {
	wsClient.send({
		type: 'play_station',
		data: { url: station.url }
	});
}

export function stopPlayback() {
	wsClient.send({
		type: 'stop'
	});
}

export function setVolume(newVolume: number) {
	wsClient.send({
		type: 'set_volume',
		data: { volume: newVolume }
	});
}

export function loadStations() {
	wsClient.send({
		type: 'get_stations'
	});
}

export function getStatus() {
	wsClient.send({
		type: 'get_status'
	});
}

// Update handlers (called from websocket.ts message handler)
export function updateVolume(newVolume: number) {
	volume.set(newVolume);
}

export function updatePlaybackStatus(status: PlaybackStatus) {
	playbackStatus.set(status);
	isPlaying.set(status.is_playing);
	if (status.current_station) {
		currentStation.set(status.current_station);
	}
}

export function updateStations(stationList: RadioStation[]) {
	stations.set(stationList);
}

export function updateCurrentStation(station: RadioStation) {
	currentStation.set(station);
}
