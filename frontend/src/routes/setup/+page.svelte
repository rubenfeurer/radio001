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
		resetToHotspot,
		getSignalColor,
		requiresPassword
	} from '$lib/stores/wifi';

	// Combined network with saved status
	interface CombinedNetwork extends WiFiNetwork {
		isSaved?: boolean;
		isCurrent?: boolean;
		savedId?: number;
	}

	let selectedNetwork: CombinedNetwork | null = null;
	let password = '';
	let showPassword = false;
	let confirmingForget = false;
	let confirmingReset = false;

	// Combine available networks with saved network info
	$: combinedNetworks = $networks.map((network) => {
		const savedNetwork = $savedNetworks.find((s) => s.ssid === network.ssid);
		return {
			...network,
			isSaved: !!savedNetwork,
			isCurrent: savedNetwork?.current || false,
			savedId: savedNetwork?.id
		} as CombinedNetwork;
	});

	onMount(() => {
		scanNetworks();
		getSavedNetworks();
	});

	const handleNetworkClick = (network: CombinedNetwork) => {
		selectedNetwork = network;
		password = '';
		confirmingForget = false;
	};

	const handleConnect = async () => {
		if (!selectedNetwork) return;

		const success = await connectToNetwork({
			ssid: selectedNetwork.ssid,
			password: password,
			security: selectedNetwork.security
		});

		if (success) {
			selectedNetwork = null;
			password = '';
		}
	};

	const handleForget = async () => {
		if (!selectedNetwork?.savedId) return;

		const success = await forgetNetwork(selectedNetwork.savedId, selectedNetwork.ssid);

		if (success) {
			selectedNetwork = null;
			confirmingForget = false;
			// Refresh both lists
			await getSavedNetworks();
			await scanNetworks();
		}
	};

	const closeDialog = () => {
		selectedNetwork = null;
		password = '';
		confirmingForget = false;
	};

	const handleResetToHotspot = async () => {
		const success = await resetToHotspot();
		if (success) {
			// System will reboot - show message
			confirmingReset = false;
		}
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
					<button on:click={() => goto('/')} class="btn-secondary p-2">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M10 19l-7-7m0 0l7-7m-7 7h18"
							/>
						</svg>
					</button>
					<div>
						<h1 class="text-xl font-bold text-gray-900 dark:text-white">WiFi Manager</h1>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							Connect to networks and manage WiFi
						</p>
					</div>
				</div>
				<button
					on:click={() => {
						scanNetworks();
						getSavedNetworks();
					}}
					disabled={$isScanning || $isLoadingSaved}
					class="btn-secondary p-2"
					title="Refresh networks"
				>
					<svg
						class="w-4 h-4"
						class:animate-spin={$isScanning || $isLoadingSaved}
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
						/>
					</svg>
				</button>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-md mx-auto px-4 py-6">
		<!-- Error Display -->
		{#if $error}
			<div
				class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6"
			>
				<div class="flex items-center">
					<svg
						class="w-5 h-5 text-red-400 mr-2"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
					<p class="text-red-800 dark:text-red-200 text-sm">{$error}</p>
				</div>
			</div>
		{/if}

		<!-- Connection Progress -->
		{#if $connectionProgress.status !== 'idle'}
			<div
				class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6"
			>
				<div class="flex items-start">
					{#if $connectionProgress.status === 'connecting' || $connectionProgress.status === 'verifying'}
						<svg
							class="animate-spin h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5"
							fill="none"
							viewBox="0 0 24 24"
						>
							<circle
								class="opacity-25"
								cx="12"
								cy="12"
								r="10"
								stroke="currentColor"
								stroke-width="4"
							/>
							<path
								class="opacity-75"
								fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
							/>
						</svg>
					{:else if $connectionProgress.status === 'success'}
						<svg
							class="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5"
							fill="currentColor"
							viewBox="0 0 20 20"
						>
							<path
								fill-rule="evenodd"
								d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
								clip-rule="evenodd"
							/>
						</svg>
					{:else if $connectionProgress.status === 'failed'}
						<svg
							class="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5"
							fill="currentColor"
							viewBox="0 0 20 20"
						>
							<path
								fill-rule="evenodd"
								d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
								clip-rule="evenodd"
							/>
						</svg>
					{/if}
					<div class="ml-3 flex-1">
						<p
							class="text-sm font-medium {$connectionProgress.status === 'success'
								? 'text-green-600 dark:text-green-400'
								: $connectionProgress.status === 'failed'
									? 'text-red-600 dark:text-red-400'
									: 'text-blue-600 dark:text-blue-400'}"
						>
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

		<!-- Networks List -->
		<div class="card mb-6">
			<div class="p-4 border-b border-gray-200 dark:border-gray-700">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white">WiFi Networks</h2>
			</div>

			<div class="max-h-96 overflow-y-auto">
				{#if $isScanning}
					<div class="p-6 text-center">
						<svg
							class="w-8 h-8 animate-spin text-primary-600 mx-auto mb-4"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
							/>
						</svg>
						<p class="text-gray-600 dark:text-gray-400">Scanning for networks...</p>
					</div>
				{:else if combinedNetworks.length === 0}
					<div class="p-6 text-center">
						<svg
							class="w-8 h-8 text-gray-400 mx-auto mb-4"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
							/>
						</svg>
						<p class="text-gray-600 dark:text-gray-400">No networks found</p>
						<button on:click={() => { scanNetworks(); getSavedNetworks(); }} class="btn-primary mt-4">
							Scan Again
						</button>
					</div>
				{:else}
					{#each combinedNetworks as network}
						<button
							on:click={() => handleNetworkClick(network)}
							class="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-200 dark:border-gray-700 last:border-b-0 transition-colors"
						>
							<div class="flex items-center justify-between">
								<div class="flex-1">
									<div class="flex items-center space-x-2">
										<span class="font-medium text-gray-900 dark:text-white">
											{network.ssid}
										</span>

										<!-- Security Icon -->
										{#if network.security !== 'Open'}
											<svg
												class="w-4 h-4 text-gray-400"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
												/>
											</svg>
										{/if}

										<!-- Current Connection Badge -->
										{#if network.isCurrent}
											<span
												class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
											>
												Connected
											</span>
										{:else if network.isSaved}
											<span
												class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
											>
												Saved
											</span>
										{/if}
									</div>
									<p class="text-sm text-gray-500 dark:text-gray-400">{network.security}</p>
								</div>
								<div class="flex items-center space-x-2">
									<span class="text-sm {getSignalColor(network.signal)}">{network.signal}%</span>
									<svg
										class="w-4 h-4 {getSignalColor(network.signal)}"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"
										/>
									</svg>
								</div>
							</div>
						</button>
					{/each}
				{/if}
			</div>
		</div>

		<!-- Action Dialog -->
		{#if selectedNetwork}
			<div class="card p-6">
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
					{selectedNetwork.ssid}
				</h3>

				{#if selectedNetwork.isCurrent}
					<!-- Currently Connected - Show Forget Option -->
					{#if confirmingForget}
						<div class="space-y-4">
							<p class="text-sm text-gray-600 dark:text-gray-400">
								Are you sure you want to forget this network? You'll need to re-enter the password
								to connect again.
							</p>
							<div class="flex space-x-3">
								<button on:click={() => (confirmingForget = false)} class="btn-secondary flex-1">
									Cancel
								</button>
								<button on:click={handleForget} class="btn-primary flex-1 bg-red-600 hover:bg-red-700">
									Forget Network
								</button>
							</div>
						</div>
					{:else}
						<div class="space-y-4">
							<div class="flex items-center space-x-2 text-green-600 dark:text-green-400">
								<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
									<path
										fill-rule="evenodd"
										d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
										clip-rule="evenodd"
									/>
								</svg>
								<span class="text-sm font-medium">Currently connected to this network</span>
							</div>
							<div class="flex space-x-3">
								<button on:click={closeDialog} class="btn-secondary flex-1">Close</button>
								<button on:click={() => (confirmingForget = true)} class="btn-secondary flex-1">
									Forget Network
								</button>
							</div>
						</div>
					{/if}
				{:else if selectedNetwork.isSaved}
					<!-- Saved Network - Quick Reconnect -->
					<div class="space-y-4">
						<p class="text-sm text-gray-600 dark:text-gray-400">
							This network is saved. Connect using the saved password.
						</p>
						<div class="flex space-x-3">
							<button on:click={closeDialog} class="btn-secondary flex-1">Cancel</button>
							<button
								on:click={handleConnect}
								class="btn-primary flex-1"
								disabled={$isConnecting}
							>
								{#if $isConnecting}
									<svg
										class="w-4 h-4 animate-spin mr-2"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
										/>
									</svg>
									Connecting...
								{:else}
									Connect
								{/if}
							</button>
						</div>
					</div>
				{:else}
					<!-- New Network - Ask for Password -->
					{#if requiresPassword(selectedNetwork)}
						<div class="mb-4">
							<label
								for="password"
								class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
							>
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
									on:click={() => (showPassword = !showPassword)}
									class="absolute inset-y-0 right-0 pr-3 flex items-center"
								>
									{#if showPassword}
										<svg
											class="w-5 h-5 text-gray-400"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"
											/>
										</svg>
									{:else}
										<svg
											class="w-5 h-5 text-gray-400"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
											/>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
											/>
										</svg>
									{/if}
								</button>
							</div>
						</div>
					{:else}
						<p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
							This is an open network. No password required.
						</p>
					{/if}

					<div class="flex space-x-3">
						<button on:click={closeDialog} class="btn-secondary flex-1" disabled={$isConnecting}>
							Cancel
						</button>
						<button
							on:click={handleConnect}
							class="btn-primary flex-1"
							disabled={$isConnecting || (requiresPassword(selectedNetwork) && !password.trim())}
						>
							{#if $isConnecting}
								<svg
									class="w-4 h-4 animate-spin mr-2"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
									/>
								</svg>
								Connecting...
							{:else}
								Connect
							{/if}
						</button>
					</div>
				{/if}
			</div>
		{/if}

		<!-- Reset to Hotspot Button -->
		<div class="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
			{#if confirmingReset}
				<div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
					<div class="flex items-start">
						<svg class="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
						</svg>
						<div class="ml-3 flex-1">
							<h3 class="text-sm font-medium text-yellow-800 dark:text-yellow-400">
								Reset to Hotspot Mode?
							</h3>
							<div class="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
								<p>This will:</p>
								<ul class="list-disc list-inside mt-1 space-y-1">
									<li>Disconnect from current WiFi network</li>
									<li>Enable hotspot mode (SSID: Radio-Setup)</li>
									<li>Reboot the system</li>
								</ul>
								<p class="mt-2">After reboot, connect to "Radio-Setup" network and navigate to <strong>http://radiod.local</strong></p>
							</div>
							<div class="mt-4 flex space-x-3">
								<button
									on:click={handleResetToHotspot}
									class="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 text-sm font-medium"
								>
									Yes, Reset to Hotspot
								</button>
								<button
									on:click={() => confirmingReset = false}
									class="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 text-sm font-medium"
								>
									Cancel
								</button>
							</div>
						</div>
					</div>
				</div>
			{:else}
				<button
					on:click={() => confirmingReset = true}
					class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 flex items-center justify-center space-x-2"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
					</svg>
					<span>Reset to Hotspot Mode</span>
				</button>
			{/if}
		</div>
	</main>
</div>
