<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { wifiState, getStatus } from '$lib/stores/wifi.svelte';
	import { wsClient, wsState } from '$lib/stores/websocket.svelte';
	import { radioState, toggleStation, fetchStations, fetchStatus } from '$lib/stores/radio.svelte';
	import { Button } from '$lib/components/ui/button';
	import { Wifi, ChevronRight } from 'lucide-svelte';

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

</script>

<style>
	@keyframes spin-record {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	.slot-active { background: #1c1c1c; }
	:global(.spin-record) { animation: spin-record 5s linear infinite; }
</style>

<svelte:head>
	<title>Radio WiFi - Dashboard</title>
</svelte:head>

<div class="min-h-screen bg-background flex flex-col">
	<!-- Main Content -->
	<main class="max-w-md w-full mx-auto px-4 py-6 flex flex-col flex-1">
		<!-- Error Display -->
		{#if wifiState.error}
			<div class="border border-destructive/50 bg-destructive/10 rounded-sm p-4 mb-6">
				<p class="text-destructive text-sm">{wifiState.error}</p>
			</div>
		{/if}

		<!-- Title -->
		<div class="flex items-center justify-between mb-6">
			<h1 class="text-2xl font-bold text-foreground">Radio001</h1>
			<Button href="/settings" variant="outline" size="sm" class="border-white bg-transparent hover:bg-transparent">Settings</Button>
		</div>

		<!-- Station Slots -->
		<div class="flex flex-col gap-2">
			{#if !wsState.isConnected}
				<p class="text-xs text-yellow-600 text-right">live updates offline</p>
			{/if}
			{#each [1, 2, 3] as slot}
				{@const station = radioState.stations[slot]}
				{@const isActive = radioState.isPlaying && radioState.currentSlot === slot}
				<div class="flex items-center border border-black {isActive ? 'slot-active' : ''}" style="border-radius: 2px; height: 96px">
					<button
						onclick={() => handleSlotClick(slot)}
						disabled={!station}
						class="flex flex-1 min-w-0 px-4 h-full text-left disabled:cursor-default items-center gap-3"
					>
						{#if isActive}
							<svg class="spin-record w-8 h-8 flex-shrink-0 mx-0.5" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1">
							<circle cx="12" cy="12" r="10" vector-effect="non-scaling-stroke" />
							<line x1="2" y1="12" x2="22" y2="12" vector-effect="non-scaling-stroke" />
						</svg>
						{/if}
						<span class="text-lg font-semibold truncate {
							isActive ? 'text-white' :
							station ? 'text-foreground' : 'text-muted-foreground'
						}">
							{station?.name || '(empty)'}
						</span>
					</button>

					<div class="flex items-center pr-4">
						<Button
							variant="ghost"
							size="icon"
							class="rounded-sm {isActive ? 'text-white bg-white/10 hover:bg-white/10 hover:text-white' : 'text-foreground bg-black/[3%] hover:bg-black/[3%]'}"
							onclick={(e: MouseEvent) => handleSlotSettings(e, slot)}
						>
							<ChevronRight class="w-5 h-5" />
						</Button>
					</div>
				</div>
			{/each}
		</div>

		<!-- WiFi Status Row -->
		<div class="flex items-center justify-between rounded-sm bg-card px-4 py-3 mt-auto mb-6">
			<div class="flex items-center gap-2 min-w-0">
				<Wifi class="w-4 h-4 text-muted-foreground flex-shrink-0" />
				<span class="text-sm font-medium truncate text-foreground">
					{wifiState.status?.network?.wifi?.ssid || 'Not connected'}
				</span>
				{#if wifiState.status?.network?.wifi?.signal}
					<span class="text-xs text-muted-foreground flex-shrink-0">{wifiState.status.network.wifi.signal}%</span>
				{/if}
				{#if wifiState.status?.network?.wifi?.status === 'connected'}
					<span class="text-xs text-green-600 font-medium flex-shrink-0">connected</span>
				{/if}
			</div>
			<Button href="/setup" variant="ghost" size="icon" class="ml-3 flex-shrink-0 rounded-sm bg-black/[3%] hover:bg-black/[3%]">
				<ChevronRight class="w-5 h-5" />
			</Button>
		</div>
	</main>
</div>
