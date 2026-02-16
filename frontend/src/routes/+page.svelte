<script lang="ts">
	import { onMount } from 'svelte';
	import { status, getStatus, isLoading, error } from '$lib/stores/wifi';
	import { isConnected, wsClient } from '$lib/stores/websocket';
	import {
		stations, currentSlot, currentStation, volume, isPlaying,
		toggleStation, setVolume, fetchStations, fetchStatus
	} from '$lib/stores/radio';

	// SvelteKit page props - explicitly define what we accept
	export let data: any = undefined;

	let refreshing = false;
	let localVolume = 50;

	// Keep localVolume in sync with store (for WebSocket updates)
	$: localVolume = $volume;

	const refresh = async () => {
		refreshing = true;
		await getStatus();
		await fetchStatus();
		await fetchStations();
		refreshing = false;
	};

	onMount(() => {
		// Initial fetch via REST
		getStatus();

		// Connect WebSocket and fetch radio state
		wsClient.connect();
		fetchStatus();
		fetchStations();
	});

	function handleStationClick(slot: number) {
		const station = $stations[slot];
		if (!station) return;
		toggleStation(slot);
	}

	function handleVolumeInput(e: Event) {
		const target = e.target as HTMLInputElement;
		const newVolume = parseInt(target.value, 10);
		setVolume(newVolume);
	}
</script>

<svelte:head>
	<title>Radio WiFi - Dashboard</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<header class="bg-white dark:bg-gray-800 shadow">
		<div class="max-w-md mx-auto px-4">
			<div class="flex items-center justify-between py-4">
				<div class="flex items-center space-x-3">
					<div class="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
						<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
								d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
						</svg>
					</div>
					<div>
						<h1 class="text-xl font-bold text-gray-900 dark:text-white">
							Radio WiFi
						</h1>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							{$status?.hostname || 'radio'}.local
						</p>
					</div>
				</div>
				<div class="flex items-center gap-2">
					<button
						on:click={refresh}
						disabled={refreshing}
						class="btn-secondary"
					>
						<svg class="w-4 h-4" class:animate-spin={refreshing} fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
								d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
						</svg>
					</button>
				</div>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-md mx-auto px-4 py-6">
		<!-- Error Display -->
		{#if $error}
			<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
				<div class="flex items-center">
					<svg class="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
							d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<p class="text-red-800 dark:text-red-200 text-sm">
						{$error}
					</p>
				</div>
			</div>
		{/if}

		<!-- Status Card -->
		<div class="card p-6 mb-6">
			<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">WiFi Status</h2>

			{#if $isLoading}
				<div class="animate-pulse">
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
				</div>
			{:else if $status}
				<div class="space-y-3">
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Status:</span>
						<span class="text-sm font-medium" class:text-green-600={$status?.network?.wifi?.status === 'connected'}
							class:text-yellow-600={$status?.network?.wifi?.status === 'connecting'}
							class:text-red-600={$status?.network?.wifi?.status === 'disconnected'}>
							{$status?.network?.wifi?.status || 'Unknown'}
						</span>
					</div>

					{#if $status?.network?.wifi?.ssid}
						<div class="flex justify-between items-center">
							<span class="text-sm text-gray-600 dark:text-gray-400">Network:</span>
							<span class="text-sm font-medium text-gray-900 dark:text-white">
								{$status?.network?.wifi?.ssid}
							</span>
						</div>
					{/if}

					{#if $status?.network?.wifi?.ip}
						<div class="flex justify-between items-center">
							<span class="text-sm text-gray-600 dark:text-gray-400">IP Address:</span>
							<span class="text-sm font-mono text-gray-900 dark:text-white">
								{$status?.network?.wifi?.ip}
							</span>
						</div>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Radio Card -->
		<div class="card p-6 mb-6">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Radio</h2>
				{#if !$isConnected}
					<span class="text-xs text-yellow-600 dark:text-yellow-400">live updates offline</span>
				{/if}
			</div>

			<!-- Now Playing -->
			<div class="flex items-center justify-between mb-4">
				<div class="flex items-center space-x-2">
					<span class="w-2 h-2 rounded-full {$isPlaying ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}"></span>
					<span class="text-sm text-gray-700 dark:text-gray-300">
						{#if $isPlaying && $currentStation}
							{$currentStation.name}
						{:else}
							Stopped
						{/if}
					</span>
				</div>
				{#if $isPlaying && $currentStation?.location}
					<span class="text-xs text-gray-500 dark:text-gray-400">{$currentStation.location}</span>
				{/if}
			</div>

			<!-- Station Slot Buttons -->
			<div class="grid grid-cols-3 gap-2 mb-4">
				{#each [1, 2, 3] as slot}
					{@const station = $stations[slot]}
					{@const isActive = $isPlaying && $currentSlot === slot}
					<button
						on:click={() => handleStationClick(slot)}
						disabled={!station}
						class="flex flex-col items-center justify-center p-3 rounded-lg border-2 text-center transition-colors
							{isActive
								? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30'
								: station
									? 'border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600'
									: 'border-gray-100 dark:border-gray-800 opacity-50 cursor-not-allowed'}"
					>
						<span class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{slot}</span>
						<span class="text-xs truncate w-full {isActive ? 'text-primary-700 dark:text-primary-300 font-semibold' : 'text-gray-700 dark:text-gray-300'}">
							{station?.name || '(empty)'}
						</span>
					</button>
				{/each}
			</div>

			<!-- Volume Slider -->
			<div class="flex items-center space-x-3">
				<svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
						d="M15.536 8.464a5 5 0 010 7.072M12 6l-4 4H4v4h4l4 4V6z" />
				</svg>
				<input
					type="range"
					min="0"
					max="100"
					bind:value={localVolume}
					on:input={handleVolumeInput}
					class="flex-1 h-2 rounded-lg appearance-none cursor-pointer bg-gray-200 dark:bg-gray-700 accent-primary-600"
				/>
				<span class="text-xs text-gray-500 dark:text-gray-400 w-8 text-right">{localVolume}</span>
			</div>
		</div>

		<!-- Action Buttons -->
		<div class="space-y-3">
			<a href="/setup" class="btn-primary w-full justify-center">
				<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
						d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
				</svg>
				WiFi Manager
			</a>

			<a href="/status" class="btn-secondary w-full justify-center">
				<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
						d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
				</svg>
				System Status
			</a>

			<a href="/settings" class="btn-secondary w-full justify-center">
				<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
						d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
				</svg>
				Settings
			</a>
		</div>
	</main>
</div>
