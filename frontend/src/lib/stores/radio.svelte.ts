import type { RadioStation, PlaybackStatus } from '$lib/types';

export const radioState = $state({
	stations: {} as Record<number, RadioStation | null>,
	currentSlot: null as number | null,
	currentStation: null as RadioStation | null,
	volume: 50,
	isPlaying: false,
	playbackStatus: null as PlaybackStatus | null
});

export async function toggleStation(slot: number) {
	try {
		await fetch(`/api/radio/stations/${slot}/toggle`, { method: 'POST' });
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
	radioState.volume = newVolume;
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
			radioState.volume = data.volume ?? 50;
			radioState.isPlaying = data.is_playing ?? false;
			radioState.currentSlot = data.current_station ?? null;
			radioState.currentStation = data.current_station_info ?? null;
			radioState.playbackStatus = {
				is_playing: data.is_playing,
				current_station: data.current_station_info || null,
				current_slot: data.current_station || null,
				playback_state: data.playback_state
			};
		}
	} catch (e) {
		console.error('Failed to fetch radio status:', e);
	}
}

export function updateVolume(newVolume: number) {
	radioState.volume = newVolume;
}

export function updatePlaybackStatus(status: PlaybackStatus) {
	radioState.playbackStatus = status;
	radioState.isPlaying = status.is_playing;
	radioState.currentSlot = status.current_slot ?? null;
	if (status.current_station) {
		radioState.currentStation = status.current_station;
	} else if (!status.is_playing) {
		radioState.currentStation = null;
	}
}

export function updateStations(stationMap: Record<string, RadioStation | null>) {
	const normalized: Record<number, RadioStation | null> = {};
	for (const [key, value] of Object.entries(stationMap)) {
		normalized[parseInt(key, 10)] = value;
	}
	radioState.stations = normalized;
}

export function updateCurrentStation(station: RadioStation) {
	radioState.currentStation = station;
}
