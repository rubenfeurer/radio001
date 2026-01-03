<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { WiFiNetwork, SavedNetwork } from '$lib/types';
	import {
		networks,
		isScanning,
		isConnecting,
		error,
		connectionProgress,
		savedNetworks,
		isLoadingSaved,
		scanNetworks,
		connectToNetwork,
		getSavedNetworks,
		forgetNetwork,
		getSignalColor,
		requiresPassword
	} from '$lib/stores/wifi';

	// SvelteKit page props - explicitly define what we accept
	export let data: any = undefined;

	let activeTab: 'available' | 'saved' = 'available';
	let selectedNetwork: WiFiNetwork | null = null;
	let password = '';
	let showPassword = false;
	let confirmingDelete: number | null = null;

	onMount(() => {
		scanNetworks();
		getSavedNetworks();
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

	const handleForget = async (network: SavedNetwork) => {
		confirmingDelete = network.id;
	};

	const confirmForget = async (network: SavedNetwork) => {
		const success = await forgetNetwork(network.id, network.ssid);
		confirmingDelete = null;

		if (success) {
			console.log(`Forgot network: ${network.ssid}`);
		}
	};

	const cancelForget = () => {
		confirmingDelete = null;
	};
</script>

<svelte:head>
	<title>Radio WiFi - WiFi Manager</title>
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
							WiFi Manager
						</h1>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							Connect to networks and manage saved WiFi
						</p>
					</div>
				</div>
				<button
					on:click={() => {
						if (activeTab === 'available') {
							scanNetworks();
						} else {
							getSavedNetworks();
						}
					}}
					disabled={$isScanning || $isLoadingSaved}
					class="btn-secondary p-2"
					title={activeTab === 'available' ? 'Refresh networks' : 'Refresh saved networks'}
				>
					<svg class="w-4 h-4" class:animate-spin={$isScanning || $isLoadingSaved} fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
							d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
					</svg>
				</button>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-md mx-auto px-4 py-6">
		<!-- Tabs -->
		<div class="mb-6">
			<div class="border-b border-gray-200 dark:border-gray-700">
				<nav class="-mb-px flex space-x-8">
					<button
						on:click={() => activeTab = 'available'}
						class="py-2 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'available'
							? 'border-primary-600 text-primary-600 dark:text-primary-400'
							: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'}"
					>
						<div class="flex items-center space-x-2">
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
									d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
							</svg>
							<span>Available Networks</span>
						</div>
					</button>
					<button
						on:click={() => activeTab = 'saved'}
						class="py-2 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'saved'
							? 'border-primary-600 text-primary-600 dark:text-primary-400'
							: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'}"
					>
						<div class="flex items-center space-x-2">
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
									d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
							</svg>
							<span>Saved Networks</span>
							{#if $savedNetworks.length > 0}
								<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900/30 dark:text-primary-400">
									{$savedNetworks.length}
								</span>
							{/if}
						</div>
					</button>
				</nav>
			</div>
		</div>

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

		<!-- Connection Progress -->
		{#if $connectionProgress.status !== 'idle'}
			<div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
				<div class="flex items-start">
					{#if $connectionProgress.status === 'connecting' || $connectionProgress.status === 'verifying'}
						<svg class="animate-spin h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
						</svg>
					{:else if $connectionProgress.status === 'success'}
						<svg class="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
						</svg>
					{:else if $connectionProgress.status === 'failed'}
						<svg class="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
						</svg>
					{/if}
					<div class="ml-3 flex-1">
						<p class="text-sm font-medium {$connectionProgress.status === 'success' ? 'text-green-600 dark:text-green-400' : $connectionProgress.status === 'failed' ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'}">
							{$connectionProgress.message}
						</p>
						{#if $connectionProgress.maxAttempts > 1}
							<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
								Attempt {$connectionProgress.attempt}/{$connectionProgress.maxAttempts}
							</p>
						{/if}
					</div>
				</div>
			</div>
		{/if}

		<!-- Available Networks Tab -->
		{#if activeTab === 'available'}
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
		{/if}

		<!-- Saved Networks Tab -->
		{#if activeTab === 'saved'}
			{#if $isLoadingSaved}
				<div class="flex justify-center items-center py-12">
					<svg class="animate-spin h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
					</svg>
					<span class="ml-3 text-gray-600 dark:text-gray-400">Loading saved networks...</span>
				</div>
			{:else if $savedNetworks.length === 0}
				<!-- Empty State -->
				<div class="card p-8 text-center">
					<svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
							d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
					</svg>
					<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">No saved networks</h3>
					<p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
						Connect to a network in the Available Networks tab to save it.
					</p>
					<button
						on:click={() => activeTab = 'available'}
						class="btn-primary mx-auto"
					>
						Browse Available Networks
					</button>
				</div>
			{:else}
				<!-- Saved Networks List -->
				<div class="card divide-y divide-gray-200 dark:divide-gray-700">
					{#each $savedNetworks as network (network.id)}
						<div class="p-4">
							<div class="flex items-center justify-between">
								<!-- Network Info -->
								<div class="flex-1">
									<div class="flex items-center space-x-2">
										<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
												d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
										</svg>
										<span class="text-base font-medium text-gray-900 dark:text-white">
											{network.ssid}
										</span>
										{#if network.current}
											<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
												Connected
											</span>
										{/if}
										{#if network.disabled}
											<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400">
												Disabled
											</span>
										{/if}
									</div>
								</div>

								<!-- Actions -->
								<div class="ml-4">
									{#if confirmingDelete === network.id}
										<!-- Confirmation Dialog -->
										<div class="flex items-center space-x-2">
											<span class="text-sm text-gray-600 dark:text-gray-400">Forget?</span>
											<button
												on:click={() => confirmForget(network)}
												class="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
											>
												Yes
											</button>
											<button
												on:click={cancelForget}
												class="px-3 py-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm rounded hover:bg-gray-300 dark:hover:bg-gray-600"
											>
												No
											</button>
										</div>
									{:else}
										<button
											on:click={() => handleForget(network)}
											disabled={network.current}
											class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 shadow-sm text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
											title={network.current ? 'Cannot forget currently connected network' : 'Forget this network'}
										>
											<svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
													d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
											</svg>
											Forget
										</button>
									{/if}
								</div>
							</div>
						</div>
					{/each}
				</div>

				<!-- Help Text -->
				<div class="mt-4 text-sm text-gray-500 dark:text-gray-400 space-y-1">
					<p>• Connected networks cannot be forgotten until you connect to another network</p>
					<p>• Forgetting a network removes its saved password</p>
				</div>
			{/if}
		{/if}
	</main>
</div>
