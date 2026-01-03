// System status store for SvelteKit
// Manages system metrics and status information

import { writable, derived } from 'svelte/store';
import type { SystemStatus } from '../types';

// Main system status store
export const systemStatus = writable<SystemStatus | null>(null);

// Derived stores
export const isHealthy = derived(systemStatus, ($status) => {
	if (!$status) return false;
	// Consider system healthy if CPU load < 80% and memory usage < 90%
	const cpuHealthy = $status.cpu.load < 80;
	const memoryHealthy = ($status.memory.used / $status.memory.total) * 100 < 90;
	return cpuHealthy && memoryHealthy;
});

export const memoryUsagePercent = derived(systemStatus, ($status) => {
	if (!$status || $status.memory.total === 0) return 0;
	return Math.round(($status.memory.used / $status.memory.total) * 100);
});

export const uptimeFormatted = derived(systemStatus, ($status) => {
	if (!$status) return '0s';
	const seconds = $status.uptime;
	const days = Math.floor(seconds / 86400);
	const hours = Math.floor((seconds % 86400) / 3600);
	const minutes = Math.floor((seconds % 3600) / 60);

	if (days > 0) return `${days}d ${hours}h`;
	if (hours > 0) return `${hours}h ${minutes}m`;
	return `${minutes}m`;
});

// REST API fallback for initial load
export const fetchSystemStatus = async (): Promise<void> => {
	try {
		const response = await fetch('/api/system/status');
		if (!response.ok) throw new Error('Failed to fetch system status');

		const result = await response.json();
		if (result.success && result.data) {
			systemStatus.set(result.data);
		}
	} catch (error) {
		console.error('Failed to fetch system status:', error);
	}
};
