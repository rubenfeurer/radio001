<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { status, getStatus, isLoading, error } from '$lib/stores/wifi';

	onMount(() => {
		getStatus();
		const interval = setInterval(getStatus, 10000);
		return () => clearInterval(interval);
	});

	const formatUptime = (seconds: number) => {
		const days = Math.floor(seconds / 86400);
		const hours = Math.floor((seconds % 86400) / 3600);
		const minutes = Math.floor((seconds % 3600) / 60);

		if (days > 0) return `${days}d ${hours}h ${minutes}m`;
		if (hours > 0) return `${hours}h ${minutes}m`;
		return `${minutes}m`;
	};

	const formatBytes = (bytes: number) => {
		const sizes = ['B', 'KB', 'MB', 'GB'];
		if (bytes === 0) return '0 B';
		const i = Math.floor(Math.log(bytes) / Math.log(1024));
		return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
	};
</script>

<svelte:head>
	<title>Radio WiFi - System Status</title>
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
							System Status
						</h1>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							Detailed system information
						</p>
					</div>
				</div>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-md mx-auto px-4 py-6 space-y-6">
		<!-- Error Display -->
		{#if $error}
			<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
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

		{#if $isLoading}
			<div class="space-y-6">
				{#each Array(4) as _}
					<div class="card p-6">
						<div class="animate-pulse">
							<div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
							<div class="space-y-2">
								<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
								<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{:else if $status}
			<!-- System Info -->
			<div class="card p-6">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">System Information</h2>
				<div class="space-y-3">
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Hostname:</span>
						<span class="text-sm font-medium text-gray-900 dark:text-white">
							{$status.hostname}
						</span>
					</div>
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Uptime:</span>
						<span class="text-sm font-medium text-gray-900 dark:text-white">
							{formatUptime($status.uptime)}
						</span>
					</div>
				</div>
			</div>

			<!-- Network Status -->
			<div class="card p-6">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Network Status</h2>
				<div class="space-y-3">
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">WiFi Status:</span>
						<span class="text-sm font-medium"
							class:text-green-600={$status.network.wifi.status === 'connected'}
							class:text-yellow-600={$status.network.wifi.status === 'connecting'}
							class:text-red-600={$status.network.wifi.status === 'disconnected'}>
							{$status.network.wifi.status}
						</span>
					</div>
					{#if $status.network.wifi.ssid}
						<div class="flex justify-between items-center">
							<span class="text-sm text-gray-600 dark:text-gray-400">Network:</span>
							<span class="text-sm font-medium text-gray-900 dark:text-white">
								{$status.network.wifi.ssid}
							</span>
						</div>
					{/if}
					{#if $status.network.wifi.ip}
						<div class="flex justify-between items-center">
							<span class="text-sm text-gray-600 dark:text-gray-400">IP Address:</span>
							<span class="text-sm font-mono text-gray-900 dark:text-white">
								{$status.network.wifi.ip}
							</span>
						</div>
					{/if}
					{#if $status.network.wifi.signal}
						<div class="flex justify-between items-center">
							<span class="text-sm text-gray-600 dark:text-gray-400">Signal:</span>
							<span class="text-sm font-medium text-gray-900 dark:text-white">
								{$status.network.wifi.signal}%
							</span>
						</div>
					{/if}
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Mode:</span>
						<span class="text-sm font-medium text-gray-900 dark:text-white">
							{$status.network.wifi.mode}
						</span>
					</div>
				</div>
			</div>

			<!-- Memory Usage -->
			<div class="card p-6">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Memory Usage</h2>
				<div class="space-y-3">
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Total:</span>
						<span class="text-sm font-medium text-gray-900 dark:text-white">
							{formatBytes($status.memory.total)}
						</span>
					</div>
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Used:</span>
						<span class="text-sm font-medium text-gray-900 dark:text-white">
							{formatBytes($status.memory.used)}
						</span>
					</div>
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Free:</span>
						<span class="text-sm font-medium text-gray-900 dark:text-white">
							{formatBytes($status.memory.free)}
						</span>
					</div>
					<div class="mt-2">
						<div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
							<span>Usage</span>
							<span>{Math.round(($status.memory.used / $status.memory.total) * 100)}%</span>
						</div>
						<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
							<div
								class="bg-primary-600 h-2 rounded-full transition-all duration-300"
								style="width: {($status.memory.used / $status.memory.total) * 100}%"
							></div>
						</div>
					</div>
				</div>
			</div>

			<!-- CPU Information -->
			<div class="card p-6">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">CPU Information</h2>
				<div class="space-y-3">
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600 dark:text-gray-400">Load:</span>
						<span class="text-sm font-medium text-gray-900 dark:text-white">
							{$status.cpu.load.toFixed(2)}
						</span>
					</div>
					{#if $status.cpu.temperature}
						<div class="flex justify-between items-center">
							<span class="text-sm text-gray-600 dark:text-gray-400">Temperature:</span>
							<span class="text-sm font-medium text-gray-900 dark:text-white">
								{$status.cpu.temperature.toFixed(1)}°C
							</span>
						</div>
					{/if}
				</div>
			</div>
		{/if}
	</main>
</div>
