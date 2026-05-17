<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { ArrowLeft, Eye, EyeOff, RotateCcw, Save } from 'lucide-svelte';
	import {
		loadSettings,
		saveSettings,
		restartContainer,
		settingsState
	} from '$lib/stores/settings.svelte';
	import type { RadioSettings } from '$lib/types';

	// Form fields — populated on load
	let hotspotSsid = $state('');
	let hotspotPassword = $state('');
	let defaultVolume = $state(50);
	let minVolume = $state(30);
	let maxVolume = $state(100);
	let notificationVolume = $state(40);
	let rotaryClockwise = $state(true);
	let rotaryStep = $state(5);
	let rotaryDebounce = $state(0.05);
	let longPress = $state(2.0);
	let triplePress = $state(0.5);

	// UI state
	let showPassword = $state(false);
	let saving = $state(false);
	let restarting = $state(false);
	let showBanner = $state(false);
	let successMessage = $state('');
	let validationErrors = $state<Record<string, string>>({});

	// Snapshot of loaded values for dirty-checking
	let loaded: RadioSettings = {};

	function populate(s: RadioSettings) {
		loaded = { ...s };
		hotspotSsid = s.HOTSPOT_SSID ?? '';
		hotspotPassword = s.HOTSPOT_PASSWORD ?? '';
		defaultVolume = s.DEFAULT_VOLUME ?? 50;
		minVolume = s.MIN_VOLUME ?? 30;
		maxVolume = s.MAX_VOLUME ?? 100;
		notificationVolume = s.NOTIFICATION_VOLUME ?? 40;
		rotaryClockwise = s.ROTARY_CLOCKWISE_INCREASES ?? true;
		rotaryStep = s.ROTARY_VOLUME_STEP ?? 5;
		rotaryDebounce = s.ROTARY_DEBOUNCE ?? 0.05;
		longPress = s.LONG_PRESS_DURATION ?? 2.0;
		triplePress = s.TRIPLE_PRESS_INTERVAL ?? 0.5;
	}

	function buildDiff(): RadioSettings {
		const current: RadioSettings = {
			HOTSPOT_SSID: hotspotSsid,
			HOTSPOT_PASSWORD: hotspotPassword,
			DEFAULT_VOLUME: defaultVolume,
			MIN_VOLUME: minVolume,
			MAX_VOLUME: maxVolume,
			NOTIFICATION_VOLUME: notificationVolume,
			ROTARY_CLOCKWISE_INCREASES: rotaryClockwise,
			ROTARY_VOLUME_STEP: rotaryStep,
			ROTARY_DEBOUNCE: rotaryDebounce,
			LONG_PRESS_DURATION: longPress,
			TRIPLE_PRESS_INTERVAL: triplePress
		};
		const diff: RadioSettings = {};
		for (const [k, v] of Object.entries(current)) {
			const key = k as keyof RadioSettings;
			if (v !== loaded[key]) (diff as Record<string, unknown>)[key] = v;
		}
		return diff;
	}

	async function handleSave() {
		validationErrors = {};
		const diff = buildDiff();
		if (Object.keys(diff).length === 0) return;

		saving = true;
		try {
			const { response, validationErrors: errs } = await saveSettings(diff);
			if (Object.keys(errs).length > 0) {
				validationErrors = errs;
				return;
			}
			if (response) {
				loaded = { ...loaded, ...diff };
				successMessage = 'Settings saved.';
				setTimeout(() => (successMessage = ''), 3000);
				if (response.restart_required.length > 0) showBanner = true;
			}
		} finally {
			saving = false;
		}
	}

	async function handleRestart() {
		restarting = true;
		await restartContainer();
		showBanner = false;
	}

	onMount(async () => {
		const s = await loadSettings();
		if (s) populate(s);
	});
</script>

<svelte:head>
	<title>Radio WiFi - Settings</title>
</svelte:head>

<div class="min-h-screen bg-background">
	<!-- Restart required banner -->
	{#if showBanner}
		<div class="bg-amber-50 border-b border-amber-200 px-4 py-3">
			<div class="max-w-md mx-auto flex items-center justify-between gap-3">
				<p class="text-sm text-amber-800">
					{restarting ? 'Restarting…' : 'Settings saved. Restart required for changes to take effect.'}
				</p>
				{#if !restarting}
					<div class="flex gap-2 shrink-0">
						<Button size="sm" onclick={handleRestart}>
							<RotateCcw class="w-3 h-3 mr-1" />
							Restart
						</Button>
						<Button size="sm" variant="ghost" onclick={() => (showBanner = false)}>Dismiss</Button>
					</div>
				{/if}
			</div>
		</div>
	{/if}

	<!-- Header -->
	<header class="border-b bg-card">
		<div class="max-w-md mx-auto px-4">
			<div class="flex items-center space-x-3 py-4">
				<Button variant="outline" size="icon" onclick={() => goto('/')}>
					<ArrowLeft class="w-4 h-4" />
				</Button>
				<div>
					<h1 class="text-xl font-bold text-foreground">Settings</h1>
					<p class="text-sm text-muted-foreground">Device configuration</p>
				</div>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-md mx-auto px-4 py-6 space-y-5">
		{#if settingsState.loading}
			<p class="text-center text-muted-foreground text-sm py-12">Loading settings…</p>
		{:else if settingsState.error}
			<Card>
				<CardContent class="pt-6 text-center">
					<p class="text-destructive text-sm">{settingsState.error}</p>
					<Button class="mt-4" onclick={() => loadSettings()}>Retry</Button>
				</CardContent>
			</Card>
		{:else}
			<!-- Success message -->
			{#if successMessage}
				<p class="text-center text-sm text-green-700 font-medium">{successMessage}</p>
			{/if}

			<!-- Global error -->
			{#if validationErrors._global}
				<p class="text-center text-sm text-destructive">{validationErrors._global}</p>
			{/if}

			<!-- Hotspot -->
			<Card>
				<CardContent class="pt-5 space-y-4">
					<h2 class="font-semibold text-foreground">Hotspot</h2>
					<p class="text-xs text-muted-foreground -mt-2">
						WiFi network created when no internet is available.
					</p>

					<div class="space-y-1">
						<label class="text-sm font-medium" for="hotspot-ssid">Network name (SSID)</label>
						<Input id="hotspot-ssid" bind:value={hotspotSsid} placeholder="Radio-Setup" />
						{#if validationErrors.HOTSPOT_SSID}
							<p class="text-xs text-destructive">{validationErrors.HOTSPOT_SSID}</p>
						{/if}
					</div>

					<div class="space-y-1">
						<label class="text-sm font-medium" for="hotspot-pw">Password</label>
						<div class="relative">
							<Input
								id="hotspot-pw"
								type={showPassword ? 'text' : 'password'}
								bind:value={hotspotPassword}
								placeholder="min 8 characters"
								class="pr-10"
							/>
							<button
								type="button"
								aria-label={showPassword ? 'Hide password' : 'Show password'}
								class="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
								onclick={() => (showPassword = !showPassword)}
							>
								{#if showPassword}
									<EyeOff class="w-4 h-4" />
								{:else}
									<Eye class="w-4 h-4" />
								{/if}
							</button>
						</div>
						{#if validationErrors.HOTSPOT_PASSWORD}
							<p class="text-xs text-destructive">{validationErrors.HOTSPOT_PASSWORD}</p>
						{/if}
					</div>
				</CardContent>
			</Card>

			<!-- Volume -->
			<Card>
				<CardContent class="pt-5 space-y-4">
					<h2 class="font-semibold text-foreground">Volume</h2>

					<div class="grid grid-cols-2 gap-3">
						<div class="space-y-1">
							<label class="text-sm font-medium" for="vol-default">Default</label>
							<Input
								id="vol-default"
								type="number"
								min="0"
								max="100"
								bind:value={defaultVolume}
							/>
							{#if validationErrors.DEFAULT_VOLUME}
								<p class="text-xs text-destructive">{validationErrors.DEFAULT_VOLUME}</p>
							{/if}
						</div>
						<div class="space-y-1">
							<label class="text-sm font-medium" for="vol-notif">Notification</label>
							<Input
								id="vol-notif"
								type="number"
								min="0"
								max="100"
								bind:value={notificationVolume}
							/>
							{#if validationErrors.NOTIFICATION_VOLUME}
								<p class="text-xs text-destructive">{validationErrors.NOTIFICATION_VOLUME}</p>
							{/if}
						</div>
						<div class="space-y-1">
							<label class="text-sm font-medium" for="vol-min">Min</label>
							<Input id="vol-min" type="number" min="0" max="100" bind:value={minVolume} />
							{#if validationErrors.MIN_VOLUME}
								<p class="text-xs text-destructive">{validationErrors.MIN_VOLUME}</p>
							{/if}
						</div>
						<div class="space-y-1">
							<label class="text-sm font-medium" for="vol-max">Max</label>
							<Input id="vol-max" type="number" min="0" max="100" bind:value={maxVolume} />
							{#if validationErrors.MAX_VOLUME}
								<p class="text-xs text-destructive">{validationErrors.MAX_VOLUME}</p>
							{/if}
						</div>
					</div>
				</CardContent>
			</Card>

			<!-- Encoder -->
			<Card>
				<CardContent class="pt-5 space-y-4">
					<h2 class="font-semibold text-foreground">Encoder</h2>

					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium">Clockwise increases volume</p>
							<p class="text-xs text-muted-foreground">Disable if your encoder is reversed</p>
						</div>
						<button
							type="button"
							role="switch"
							aria-label="Clockwise increases volume"
							aria-checked={rotaryClockwise}
							onclick={() => (rotaryClockwise = !rotaryClockwise)}
							class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors {rotaryClockwise
								? 'bg-primary'
								: 'bg-input'}"
						>
							<span
								class="pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-sm transition-transform {rotaryClockwise
									? 'translate-x-5'
									: 'translate-x-0'}"
							></span>
						</button>
					</div>

					<div class="grid grid-cols-2 gap-3">
						<div class="space-y-1">
							<label class="text-sm font-medium" for="enc-step">Volume step (1–20)</label>
							<Input id="enc-step" type="number" min="1" max="20" bind:value={rotaryStep} />
							{#if validationErrors.ROTARY_VOLUME_STEP}
								<p class="text-xs text-destructive">{validationErrors.ROTARY_VOLUME_STEP}</p>
							{/if}
						</div>
						<div class="space-y-1">
							<label class="text-sm font-medium" for="enc-debounce">Debounce (s)</label>
							<Input
								id="enc-debounce"
								type="number"
								min="0.01"
								max="1"
								step="0.01"
								bind:value={rotaryDebounce}
							/>
							{#if validationErrors.ROTARY_DEBOUNCE}
								<p class="text-xs text-destructive">{validationErrors.ROTARY_DEBOUNCE}</p>
							{/if}
						</div>
						<div class="space-y-1">
							<label class="text-sm font-medium" for="long-press">Long press (s)</label>
							<Input
								id="long-press"
								type="number"
								min="0.5"
								max="10"
								step="0.1"
								bind:value={longPress}
							/>
							{#if validationErrors.LONG_PRESS_DURATION}
								<p class="text-xs text-destructive">{validationErrors.LONG_PRESS_DURATION}</p>
							{/if}
						</div>
						<div class="space-y-1">
							<label class="text-sm font-medium" for="triple-press">Triple press gap (s)</label>
							<Input
								id="triple-press"
								type="number"
								min="0.1"
								max="2"
								step="0.1"
								bind:value={triplePress}
							/>
							{#if validationErrors.TRIPLE_PRESS_INTERVAL}
								<p class="text-xs text-destructive">{validationErrors.TRIPLE_PRESS_INTERVAL}</p>
							{/if}
						</div>
					</div>
				</CardContent>
			</Card>

			<!-- Save -->
			<Button class="w-full" onclick={handleSave} disabled={saving}>
				<Save class="w-4 h-4 mr-2" />
				{saving ? 'Saving…' : 'Save Settings'}
			</Button>

			<p class="text-center text-xs text-muted-foreground">
				All settings take effect after a restart.
			</p>
		{/if}
	</main>
</div>
