import type { SystemStatus } from '../types';

export const systemState = $state({
	systemStatus: null as SystemStatus | null
});

export const fetchSystemStatus = async (): Promise<void> => {
	try {
		const response = await fetch('/api/system/status');
		if (!response.ok) throw new Error('Failed to fetch system status');
		const result = await response.json();
		if (result.success && result.data) {
			systemState.systemStatus = result.data;
		}
	} catch (error) {
		console.error('Failed to fetch system status:', error);
	}
};
