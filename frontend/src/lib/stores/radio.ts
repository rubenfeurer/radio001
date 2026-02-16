import { writable, derived } from 'svelte/store';
import type { RadioStation, PlaybackStatus } from '$lib/types';

// State stores - stations keyed by slot number (1-3)
export const stations = writable<Record<number, RadioStation | null>>({});
export const currentSlot = writable<number | null>(null);
export const currentStation = writable<RadioStation | null>(null);
export const volume = writable<number>(50);
export const isPlaying = writable<boolean>(false);
export const playbackStatus = writable<PlaybackStatus | null>(null);

// Derived stores
export const hasStations = derived(stations, ($stations) =>
	Object.values($stations).some((s) => s !== null)
);

// Actions via REST API
export async function toggleStation(slot: number) {
	try {
		await fetch(`/api/radio/stations/${slot}/toggle`, { method: 'POST' });
		// Re-fetch status to update UI (in case WebSocket is slow or offline)
		setTimeout(() => fetchStatus(), 500);
	} catch (e) {
		console.error('Failed to toggle station:', e);
	}
}

export async function stopPlayback() {
	try {
		await fetch('/api/radio/stop', { method: 'POST' });
		setTimeout(() => fetchStatus(), 500);
	} catch (e) {
		console.error('Failed to stop playback:', e);
	}
}

export async function setVolume(newVolume: number) {
	// Optimistic update
	volume.set(newVolume);
	try {
		await fetch('/api/radio/volume', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ volume: newVolume })
		});
	} catch (e) {
		console.error('Failed to set volume:', e);
	}
}

export async function fetchStations() {
	try {
		const response = await fetch('/api/radio/stations/');
		if (response.ok) {
			const data = await response.json();
			if (data.stations) {
				updateStations(data.stations);
			}
		}
	} catch (e) {
		console.error('Failed to fetch stations:', e);
	}
}

export async function fetchStatus() {
	try {
		const response = await fetch('/api/radio/status');
		if (response.ok) {
			const data = await response.json();
			volume.set(data.volume ?? 50);
			isPlaying.set(data.is_playing ?? false);
			currentSlot.set(data.current_station ?? null);
			currentStation.set(data.current_station_info ?? null);
			playbackStatus.set({
				is_playing: data.is_playing,
				current_station: data.current_station_info || null,
				current_slot: data.current_station || null,
				playback_state: data.playback_state
			});
		}
	} catch (e) {
		console.error('Failed to fetch radio status:', e);
	}
}

// Update handlers (called from websocket.ts message handler)
export function updateVolume(newVolume: number) {
	volume.set(newVolume);
}

export function updatePlaybackStatus(status: PlaybackStatus) {
	playbackStatus.set(status);
	isPlaying.set(status.is_playing);
	currentSlot.set(status.current_slot ?? null);
	if (status.current_station) {
		currentStation.set(status.current_station);
	} else if (!status.is_playing) {
		currentStation.set(null);
	}
}

export function updateStations(stationMap: Record<string, RadioStation | null>) {
	// Backend sends keys as strings ("1", "2", "3"), normalize to numbers
	const normalized: Record<number, RadioStation | null> = {};
	for (const [key, value] of Object.entries(stationMap)) {
		normalized[parseInt(key, 10)] = value;
	}
	stations.set(normalized);
}

export function updateCurrentStation(station: RadioStation) {
	currentStation.set(station);
}
