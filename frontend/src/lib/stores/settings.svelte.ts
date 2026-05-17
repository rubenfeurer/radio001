import type { RadioSettings, SettingsSaveResponse } from '$lib/types';

export const settingsState = $state({
	settings: null as RadioSettings | null,
	loading: false,
	error: null as string | null,
	restartRequired: [] as string[]
});

export async function loadSettings(): Promise<RadioSettings | null> {
	settingsState.loading = true;
	settingsState.error = null;
	try {
		const res = await fetch('/api/system/settings');
		if (!res.ok) throw new Error(`Failed to load settings (${res.status})`);
		const data: RadioSettings = await res.json();
		settingsState.settings = data;
		return data;
	} catch (e) {
		settingsState.error = e instanceof Error ? e.message : 'Failed to load settings';
		return null;
	} finally {
		settingsState.loading = false;
	}
}

export async function saveSettings(
	partial: RadioSettings
): Promise<{ response: SettingsSaveResponse | null; validationErrors: Record<string, string> }> {
	try {
		const res = await fetch('/api/system/settings', {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(partial)
		});

		if (res.status === 422) {
			const detail = await res.json();
			const errors: Record<string, string> = {};
			if (Array.isArray(detail?.detail)) {
				for (const err of detail.detail) {
					const field = err.loc?.at(-1);
					if (field) errors[String(field)] = err.msg;
				}
			}
			return { response: null, validationErrors: errors };
		}

		if (!res.ok) throw new Error(`Save failed (${res.status})`);

		const data: SettingsSaveResponse = await res.json();
		settingsState.restartRequired = data.restart_required;
		if (settingsState.settings) {
			settingsState.settings = { ...settingsState.settings, ...partial };
		}
		return { response: data, validationErrors: {} };
	} catch (e) {
		const msg = e instanceof Error ? e.message : 'Save failed';
		return { response: null, validationErrors: { _global: msg } };
	}
}

export async function restartContainer(): Promise<boolean> {
	try {
		const res = await fetch('/api/system/restart', { method: 'POST' });
		return res.ok;
	} catch {
		return false;
	}
}
