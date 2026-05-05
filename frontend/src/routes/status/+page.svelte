<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { wifiState, getStatus } from '$lib/stores/wifi.svelte';
	import { wsClient } from '$lib/stores/websocket.svelte';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { ArrowLeft } from 'lucide-svelte';

	onMount(() => {
		getStatus();
		wsClient.connect();
	});

	onDestroy(() => {
		wsClient.disconnect();
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
		return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
	};
</script>

<svelte:head>
	<title>Radio WiFi - System Status</title>
</svelte:head>

<div class="min-h-screen bg-background">
	<!-- Header -->
	<header class="border-b bg-card">
		<div class="max-w-md mx-auto px-4">
			<div class="flex items-center space-x-3 py-4">
				<Button variant="outline" size="icon" onclick={() => goto('/')}>
					<ArrowLeft class="w-4 h-4" />
				</Button>
				<div>
					<h1 class="text-xl font-bold text-foreground">System Status</h1>
					<p class="text-sm text-muted-foreground">Detailed system information</p>
				</div>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-md mx-auto px-4 py-6 space-y-6">
		{#if wifiState.error}
			<div class="border border-destructive/50 bg-destructive/10 rounded-lg p-4">
				<p class="text-destructive text-sm">{wifiState.error}</p>
			</div>
		{/if}

		{#if wifiState.isLoading}
			<div class="space-y-6">
				{#each Array(4) as _}
					<Card>
						<CardContent class="pt-6">
							<div class="animate-pulse">
								<div class="h-6 bg-muted rounded w-1/2 mb-4"></div>
								<div class="space-y-2">
									<div class="h-4 bg-muted rounded w-full"></div>
									<div class="h-4 bg-muted rounded w-3/4"></div>
								</div>
							</div>
						</CardContent>
					</Card>
				{/each}
			</div>
		{:else if wifiState.status}
			<!-- System Info -->
			<Card>
				<CardHeader><CardTitle>System Information</CardTitle></CardHeader>
				<CardContent>
					<div class="space-y-3">
						<div class="flex justify-between items-center">
							<span class="text-sm text-muted-foreground">Hostname:</span>
							<span class="text-sm font-medium text-foreground">{wifiState.status.hostname}</span>
						</div>
						<div class="flex justify-between items-center">
							<span class="text-sm text-muted-foreground">Uptime:</span>
							<span class="text-sm font-medium text-foreground">{formatUptime(wifiState.status.uptime)}</span>
						</div>
					</div>
				</CardContent>
			</Card>

			<!-- Network Status -->
			<Card>
				<CardHeader><CardTitle>Network Status</CardTitle></CardHeader>
				<CardContent>
					<div class="space-y-3">
						<div class="flex justify-between items-center">
							<span class="text-sm text-muted-foreground">WiFi Status:</span>
							<span class="text-sm font-medium {
								wifiState.status?.network?.wifi?.status === 'connected' ? 'text-green-600' :
								wifiState.status?.network?.wifi?.status === 'connecting' ? 'text-yellow-600' :
								'text-red-600'
							}">
								{wifiState.status?.network?.wifi?.status || 'Unknown'}
							</span>
						</div>
						{#if wifiState.status?.network?.wifi?.ssid}
							<div class="flex justify-between items-center">
								<span class="text-sm text-muted-foreground">Network:</span>
								<span class="text-sm font-medium text-foreground">{wifiState.status?.network?.wifi?.ssid}</span>
							</div>
						{/if}
						{#if wifiState.status?.network?.wifi?.ip}
							<div class="flex justify-between items-center">
								<span class="text-sm text-muted-foreground">IP Address:</span>
								<span class="text-sm font-mono text-foreground">{wifiState.status?.network?.wifi?.ip}</span>
							</div>
						{/if}
						{#if wifiState.status?.network?.wifi?.signal}
							<div class="flex justify-between items-center">
								<span class="text-sm text-muted-foreground">Signal:</span>
								<span class="text-sm font-medium text-foreground">{wifiState.status?.network?.wifi?.signal}%</span>
							</div>
						{/if}
						<div class="flex justify-between items-center">
							<span class="text-sm text-muted-foreground">Mode:</span>
							<span class="text-sm font-medium text-foreground">{wifiState.status?.network?.wifi?.mode || 'Unknown'}</span>
						</div>
					</div>
				</CardContent>
			</Card>

			<!-- Memory Usage -->
			<Card>
				<CardHeader><CardTitle>Memory Usage</CardTitle></CardHeader>
				<CardContent>
					<div class="space-y-3">
						<div class="flex justify-between items-center">
							<span class="text-sm text-muted-foreground">Total:</span>
							<span class="text-sm font-medium text-foreground">{formatBytes(wifiState.status.memory.total)}</span>
						</div>
						<div class="flex justify-between items-center">
							<span class="text-sm text-muted-foreground">Used:</span>
							<span class="text-sm font-medium text-foreground">{formatBytes(wifiState.status.memory.used)}</span>
						</div>
						<div class="flex justify-between items-center">
							<span class="text-sm text-muted-foreground">Free:</span>
							<span class="text-sm font-medium text-foreground">{formatBytes(wifiState.status.memory.free)}</span>
						</div>
						<div class="mt-2">
							<div class="flex justify-between text-xs text-muted-foreground mb-1">
								<span>Usage</span>
								<span>{Math.round((wifiState.status.memory.used / wifiState.status.memory.total) * 100)}%</span>
							</div>
							<div class="w-full bg-muted rounded-full h-2">
								<div
									class="bg-primary h-2 rounded-full transition-all duration-300"
									style="width: {(wifiState.status.memory.used / wifiState.status.memory.total) * 100}%"
								></div>
							</div>
						</div>
					</div>
				</CardContent>
			</Card>

			<!-- CPU Information -->
			<Card>
				<CardHeader><CardTitle>CPU Information</CardTitle></CardHeader>
				<CardContent>
					<div class="space-y-3">
						<div class="flex justify-between items-center">
							<span class="text-sm text-muted-foreground">Load:</span>
							<span class="text-sm font-medium text-foreground">{wifiState.status.cpu.load.toFixed(2)}</span>
						</div>
						{#if wifiState.status.cpu.temperature}
							<div class="flex justify-between items-center">
								<span class="text-sm text-muted-foreground">Temperature:</span>
								<span class="text-sm font-medium text-foreground">{wifiState.status.cpu.temperature.toFixed(1)}°C</span>
							</div>
						{/if}
					</div>
				</CardContent>
			</Card>
		{/if}
	</main>
</div>
