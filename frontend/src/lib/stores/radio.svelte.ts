import type { RadioStation, PlaybackStatus } from '$lib/types';

export const radioState = $state({
	stations: {} as Record<number, RadioStation | null>,
	currentSlot: null as number | null,
	currentStation: null as RadioStation | null,
	volume: 50,
	isPlaying: false,
	playbackStatus: null as PlaybackStatus | null,
	error: null as string | null
});

// While the user drags a volume slider, WS volume_update echoes of earlier
// values must not snap the bound slider backwards; external changes (rotary
// encoder) still apply when idle.
let volumeDragging = false;
let volumeDragGraceTimer: ReturnType<typeof setTimeout> | null = null;

export function setVolumeDragging(dragging: boolean) {
	if (volumeDragGraceTimer) {
		clearTimeout(volumeDragGraceTimer);
		volumeDragGraceTimer = null;
	}
	if (dragging) {
		volumeDragging = true;
	} else {
		// Short grace period so in-flight echoes of drag values are ignored
		volumeDragGraceTimer = setTimeout(() => {
			volumeDragging = false;
			volumeDragGraceTimer = null;
		}, 500);
	}
}

async function extractError(response: Response, fallback: string): Promise<string> {
	try {
		const body = await response.json();
		return body.detail || body.message || fallback;
	} catch {
		return fallback;
	}
}

export async function toggleStation(slot: number) {
	try {
		const response = await fetch(`/api/radio/stations/${slot}/toggle`, { method: 'POST' });
		if (!response.ok) {
			radioState.error = await extractError(response, `Could not play station ${slot}`);
			return;
		}
		radioState.error = null;
		setTimeout(() => fetchStatus(), 500);
	} catch (e) {
		radioState.error = `Could not reach the radio (station ${slot})`;
		console.error('Failed to toggle station:', e);
	}
}

export async function stopPlayback() {
	try {
		const response = await fetch('/api/radio/stop', { method: 'POST' });
		if (!response.ok) {
			radioState.error = await extractError(response, 'Could not stop playback');
			return;
		}
		radioState.error = null;
		setTimeout(() => fetchStatus(), 500);
	} catch (e) {
		radioState.error = 'Could not reach the radio to stop playback';
		console.error('Failed to stop playback:', e);
	}
}

export async function setVolume(newVolume: number) {
	radioState.volume = newVolume;
	try {
		const response = await fetch('/api/radio/volume', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ volume: newVolume })
		});
		if (!response.ok) {
			radioState.error = await extractError(response, 'Could not set volume');
			return;
		}
		radioState.error = null;
	} catch (e) {
		radioState.error = 'Could not reach the radio to set volume';
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
	if (volumeDragging) return;
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
