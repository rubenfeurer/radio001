<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { WiFiNetwork } from '$lib/types';
	import {
		networks,
		isScanning,
		isConnecting,
		error,
		scanNetworks,
		connectToNetwork,
		getSignalColor,
		requiresPassword
	} from '$lib/stores/wifi';

	// SvelteKit page props - explicitly define what we accept
	export let data: any = undefined;

	let selectedNetwork: WiFiNetwork | null = null;
	let password = '';
	let showPassword = false;

	onMount(() => {
		scanNetworks();
	});

	const handleNetworkSelect = (network: WiFiNetwork) => {
		selectedNetwork = network;
		password = '';
	};

	const handleConnect = async () => {
		if (!selectedNetwork) return;

		const success = await connectToNetwork({
			ssid: selectedNetwork.ssid,
			password: password,
			security: selectedNetwork.security
		});

		if (success) {
			goto('/');
		}
	};
</script>

<svelte:head>
	<title>Radio WiFi - Setup</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<header class="bg-white dark:bg-gray-800 shadow">
		<div class="max-w-md mx-auto px-4">
			<div class="flex items-center justify-between py-4">
				<div class="flex items-center space-x-3">
					<button
						on:click={() => goto('/')}
						class="btn-secondary p-2"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
						</svg>
					</button>
					<div>
						<h1 class="text-xl font-bold text-gray-900 dark:text-white">
							WiFi Setup
						</h1>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							Configure your WiFi connection
						</p>
					</div>
				</div>
				<button
					on:click={scanNetworks}
					disabled={$isScanning}
					class="btn-secondary p-2"
				>
					<svg class="w-4 h-4" class:animate-spin={$isScanning} fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
							d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
					</svg>
				</button>
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

		<!-- Networks List -->
		<div class="card mb-6">
			<div class="p-4 border-b border-gray-200 dark:border-gray-700">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Available Networks</h2>
			</div>

			<div class="max-h-96 overflow-y-auto">
				{#if $isScanning}
					<div class="p-6 text-center">
						<svg class="w-8 h-8 animate-spin text-primary-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
								d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
						</svg>
						<p class="text-gray-600 dark:text-gray-400">Scanning for networks...</p>
					</div>
				{:else if $networks.length === 0}
					<div class="p-6 text-center">
						<svg class="w-8 h-8 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
								d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
						</svg>
						<p class="text-gray-600 dark:text-gray-400">No networks found</p>
						<button on:click={scanNetworks} class="btn-primary mt-4">
							Scan Again
						</button>
					</div>
				{:else}
					{#each $networks as network}
						<button
							on:click={() => handleNetworkSelect(network)}
							class="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-200 dark:border-gray-700 last:border-b-0"
							class:bg-primary-50={selectedNetwork?.ssid === network.ssid}
						>
							<div class="flex items-center justify-between">
								<div class="flex-1">
									<div class="flex items-center space-x-2">
										<span class="font-medium text-gray-900 dark:text-white">
											{network.ssid}
										</span>
										{#if network.security !== 'Open'}
											<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
													d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
											</svg>
										{/if}
									</div>
									<p class="text-sm text-gray-500 dark:text-gray-400">
										{network.security}
									</p>
								</div>
								<div class="flex items-center space-x-2">
									<span class="text-sm {getSignalColor(network.signal)}">
										{network.signal}%
									</span>
									<svg class="w-4 h-4 {getSignalColor(network.signal)}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
											d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
									</svg>
								</div>
							</div>
						</button>
					{/each}
				{/if}
			</div>
		</div>

		<!-- Connection Form -->
		{#if selectedNetwork}
			<div class="card p-6">
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
					Connect to {selectedNetwork.ssid}
				</h3>

				{#if requiresPassword(selectedNetwork)}
					<div class="mb-4">
						<label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Password
						</label>
						<div class="relative">
							{#if showPassword}
								<input
									id="password"
									type="text"
									bind:value={password}
									placeholder="Enter WiFi password"
									class="input pr-10"
									disabled={$isConnecting}
								/>
							{:else}
								<input
									id="password"
									type="password"
									bind:value={password}
									placeholder="Enter WiFi password"
									class="input pr-10"
									disabled={$isConnecting}
								/>
							{/if}
							<button
								type="button"
								on:click={() => showPassword = !showPassword}
								class="absolute inset-y-0 right-0 pr-3 flex items-center"
							>
								{#if showPassword}
									<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
											d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
									</svg>
								{:else}
									<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
											d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
											d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
									</svg>
								{/if}
							</button>
						</div>
					</div>
				{/if}

				<div class="flex space-x-3">
					<button
						on:click={() => selectedNetwork = null}
						class="btn-secondary flex-1"
						disabled={$isConnecting}
					>
						Cancel
					</button>
					<button
						on:click={handleConnect}
						class="btn-primary flex-1"
						disabled={$isConnecting || (requiresPassword(selectedNetwork) && !password.trim())}
					>
						{#if $isConnecting}
							<svg class="w-4 h-4 animate-spin mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
									d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
							</svg>
							Connecting...
						{:else}
							Connect
						{/if}
					</button>
				</div>
			</div>
		{/if}
	</main>
</div>
