<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { wifiState, getStatus } from '$lib/stores/wifi.svelte';
	import { wsClient, wsState } from '$lib/stores/websocket.svelte';
	import { radioState, toggleStation, setVolume, fetchStations, fetchStatus } from '$lib/stores/radio.svelte';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { RefreshCw, Wifi, BarChart2, Settings } from 'lucide-svelte';

	let refreshing = $state(false);

	const refresh = async () => {
		refreshing = true;
		await getStatus();
		await fetchStatus();
		await fetchStations();
		refreshing = false;
	};

	onMount(() => {
		getStatus();
		wsClient.connect();
		fetchStatus();
		fetchStations();
	});

	function handleSlotClick(slot: number) {
		toggleStation(slot);
	}

	function handleSlotSettings(e: MouseEvent, slot: number) {
		e.stopPropagation();
		goto(`/stations?slot=${slot}`);
	}

	function handlePlayPause(e: MouseEvent, slot: number) {
		e.stopPropagation();
		toggleStation(slot);
	}

	function handleVolumeInput(e: Event) {
		const target = e.target as HTMLInputElement;
		setVolume(parseInt(target.value, 10));
	}
</script>

<svelte:head>
	<title>Radio WiFi - Dashboard</title>
</svelte:head>

<div class="min-h-screen bg-background">
	<!-- Header -->
	<header class="border-b bg-card">
		<div class="max-w-md mx-auto px-4">
			<div class="flex items-center justify-between py-4">
				<div class="flex items-center space-x-3">
					<div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
						<Wifi class="w-5 h-5 text-primary-foreground" />
					</div>
					<div>
						<h1 class="text-xl font-bold text-foreground">Radio WiFi</h1>
						<p class="text-sm text-muted-foreground">
							{wifiState.status?.hostname || 'radio'}.local
						</p>
					</div>
				</div>
				<Button variant="outline" size="icon" onclick={refresh} disabled={refreshing}>
					<RefreshCw class="w-4 h-4 {refreshing ? 'animate-spin' : ''}" />
				</Button>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-md mx-auto px-4 py-6">
		<!-- Error Display -->
		{#if wifiState.error}
			<div class="border border-destructive/50 bg-destructive/10 rounded-lg p-4 mb-6">
				<p class="text-destructive text-sm">{wifiState.error}</p>
			</div>
		{/if}

		<!-- Status Card -->
		<Card class="mb-6">
			<CardHeader>
				<CardTitle>WiFi Status</CardTitle>
			</CardHeader>
			<CardContent>
				{#if wifiState.isLoading}
					<div class="animate-pulse space-y-2">
						<div class="h-4 bg-muted rounded w-3/4"></div>
						<div class="h-4 bg-muted rounded w-1/2"></div>
					</div>
				{:else if wifiState.status}
					<div class="space-y-3">
						<div class="flex justify-between items-center">
							<span class="text-sm text-muted-foreground">Status:</span>
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
								<span class="text-sm font-medium text-foreground">
									{wifiState.status?.network?.wifi?.ssid}
								</span>
							</div>
						{/if}
						{#if wifiState.status?.network?.wifi?.ip}
							<div class="flex justify-between items-center">
								<span class="text-sm text-muted-foreground">IP Address:</span>
								<span class="text-sm font-mono text-foreground">
									{wifiState.status?.network?.wifi?.ip}
								</span>
							</div>
						{/if}
					</div>
				{/if}
			</CardContent>
		</Card>

		<!-- Radio Card -->
		<Card class="mb-6">
			<CardHeader>
				<div class="flex items-center justify-between">
					<CardTitle>Radio</CardTitle>
					{#if !wsState.isConnected}
						<span class="text-xs text-yellow-600">live updates offline</span>
					{/if}
				</div>
			</CardHeader>
			<CardContent>
				<!-- Station Slot Cards -->
				<div class="flex flex-col gap-2 mb-4">
					{#each [1, 2, 3] as slot}
						{@const station = radioState.stations[slot]}
						{@const isActive = radioState.isPlaying && radioState.currentSlot === slot}
						<div class="flex items-center rounded-lg border-2 transition-colors {
							isActive ? 'border-primary bg-primary/5' : 'border-border'
						}">
							<button
								onclick={() => handleSlotClick(slot)}
								disabled={!station}
								class="flex items-center gap-3 flex-1 min-w-0 px-4 py-3 text-left disabled:cursor-default"
							>
								<div class="flex items-center gap-1.5 flex-shrink-0">
									<span class="text-xs font-medium text-muted-foreground">{slot}</span>
									{#if isActive}
										<span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
									{/if}
								</div>
								<span class="text-sm truncate {
									isActive ? 'text-primary font-semibold' :
									station ? 'text-foreground' : 'text-muted-foreground'
								}">
									{station?.name || '(empty)'}
								</span>
							</button>

							<div class="flex items-center gap-1 pr-2">
								{#if isActive}
									<Button
										variant="ghost"
										size="icon"
										onclick={(e: MouseEvent) => handlePlayPause(e, slot)}
										class="rounded-full"
									>
										<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
											<rect x="6" y="6" width="12" height="12" rx="1" />
										</svg>
									</Button>
								{/if}
								<Button
									variant="ghost"
									size="icon"
									onclick={(e: MouseEvent) => handleSlotSettings(e, slot)}
									class="rounded-full"
								>
									<Settings class="w-4 h-4" />
								</Button>
							</div>
						</div>
					{/each}
				</div>

				<!-- Volume Slider -->
				<div class="flex items-center space-x-3">
					<svg class="w-4 h-4 text-muted-foreground flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
							d="M15.536 8.464a5 5 0 010 7.072M12 6l-4 4H4v4h4l4 4V6z" />
					</svg>
					<input
						type="range"
						min="0"
						max="100"
						value={radioState.volume}
						oninput={handleVolumeInput}
						class="flex-1 h-2 rounded-lg appearance-none cursor-pointer bg-secondary accent-primary"
					/>
					<span class="text-xs text-muted-foreground w-10 text-right">{radioState.volume}%</span>
				</div>
			</CardContent>
		</Card>

		<!-- Action Buttons -->
		<div class="space-y-3">
			<Button href="/setup" class="w-full" variant="default">
				<Wifi class="w-4 h-4 mr-2" />
				WiFi Manager
			</Button>
			<Button href="/status" class="w-full" variant="outline">
				<BarChart2 class="w-4 h-4 mr-2" />
				System Status
			</Button>
			<Button href="/settings" class="w-full" variant="outline">
				<Settings class="w-4 h-4 mr-2" />
				Settings
			</Button>
		</div>
	</main>
</div>
