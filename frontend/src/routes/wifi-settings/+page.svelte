<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		savedNetworks,
		isLoadingSaved,
		error,
		getSavedNetworks,
		forgetNetwork
	} from '$lib/stores/wifi';
	import type { SavedNetwork } from '$lib/types';

	let confirmingDelete: number | null = null;

	onMount(() => {
		getSavedNetworks();
	});

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

	const addNetwork = () => {
		goto('/setup');
	};
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 shadow">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
			<div class="flex items-center justify-between">
				<button
					on:click={() => goto('/')}
					class="inline-flex items-center text-primary-600 hover:text-primary-700 dark:text-primary-400"
				>
					<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M15 19l-7-7 7-7"
						/>
					</svg>
					Back
				</button>

				<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Saved Networks</h1>

				<button
					on:click={addNetwork}
					class="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
				>
					<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 4v16m8-8H4"
						/>
					</svg>
					Add Network
				</button>
			</div>
		</div>
	</div>

	<!-- Content -->
	<div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Error Message -->
		{#if $error}
			<div
				class="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"
			>
				<div class="flex items-start">
					<svg
						class="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5"
						fill="currentColor"
						viewBox="0 0 20 20"
					>
						<path
							fill-rule="evenodd"
							d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
							clip-rule="evenodd"
						/>
					</svg>
					<p class="ml-3 text-sm text-red-600 dark:text-red-400">{$error}</p>
				</div>
			</div>
		{/if}

		<!-- Loading State -->
		{#if $isLoadingSaved}
			<div class="flex justify-center items-center py-12">
				<svg class="animate-spin h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24">
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
				<span class="ml-3 text-gray-600 dark:text-gray-400">Loading saved networks...</span>
			</div>
		{:else if $savedNetworks.length === 0}
			<!-- Empty State -->
			<div class="text-center py-12">
				<svg
					class="mx-auto h-12 w-12 text-gray-400"
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
				<h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">No saved networks</h3>
				<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
					Get started by connecting to a WiFi network.
				</p>
				<div class="mt-6">
					<button
						on:click={addNetwork}
						class="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
					>
						<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M12 4v16m8-8H4"
							/>
						</svg>
						Add Network
					</button>
				</div>
			</div>
		{:else}
			<!-- Networks List -->
			<div
				class="bg-white dark:bg-gray-800 shadow rounded-lg divide-y divide-gray-200 dark:divide-gray-700"
			>
				{#each $savedNetworks as network (network.id)}
					<div class="p-4">
						<div class="flex items-center justify-between">
							<!-- Network Info -->
							<div class="flex-1">
								<div class="flex items-center">
									<span class="text-lg font-medium text-gray-900 dark:text-white">
										{network.ssid}
									</span>
									{#if network.current}
										<span
											class="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
										>
											Connected
										</span>
									{/if}
									{#if network.disabled}
										<span
											class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400"
										>
											Disabled
										</span>
									{/if}
								</div>
								<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
									Network ID: {network.id}
								</p>
							</div>

							<!-- Actions -->
							<div class="ml-4">
								{#if confirmingDelete === network.id}
									<!-- Confirmation Dialog -->
									<div class="flex items-center space-x-2">
										<span class="text-sm text-gray-600 dark:text-gray-400"
											>Forget this network?</span
										>
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
											Cancel
										</button>
									</div>
								{:else}
									<button
										on:click={() => handleForget(network)}
										disabled={network.current}
										class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 shadow-sm text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
										title={network.current
											? 'Cannot forget currently connected network'
											: 'Forget this network'}
									>
										<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
											/>
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
			<div class="mt-4 text-sm text-gray-500 dark:text-gray-400">
				<p>• Connected networks cannot be forgotten until you connect to another network</p>
				<p>• Forgetting a network removes its saved password</p>
			</div>
		{/if}
	</div>
</div>
