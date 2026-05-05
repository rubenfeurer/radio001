<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import type { RadioStation } from '$lib/types';
	import { Button } from '$lib/components/ui/button';
	import { ArrowLeft } from 'lucide-svelte';

	let slot = $state<number | null>(null);
	let allStations = $state<RadioStation[]>([]);
	let query = $state('');
	let loading = $state(true);
	let saving = $state(false);
	let searchInput = $state<HTMLInputElement | null>(null);

	$effect(() => {
		slot = $page.url.searchParams.has('slot')
			? parseInt($page.url.searchParams.get('slot')!, 10)
			: null;
	});

	const q = $derived(query.toLowerCase().trim());

	const filtered = $derived(
		q
			? allStations
					.filter(
						(s) =>
							s.name.toLowerCase().includes(q) ||
							(s.country || '').toLowerCase().includes(q) ||
							(s.location || '').toLowerCase().includes(q)
					)
					.slice(0, 100)
			: allStations.slice(0, 100)
	);

	const total = $derived(
		q
			? allStations.filter(
					(s) =>
						s.name.toLowerCase().includes(q) ||
						(s.country || '').toLowerCase().includes(q) ||
						(s.location || '').toLowerCase().includes(q)
				).length
			: allStations.length
	);

	onMount(async () => {
		try {
			const res = await fetch('/api/radio/library');
			if (res.ok) {
				const data = await res.json();
				allStations = data.stations ?? [];
			}
		} catch (e) {
			console.error('Failed to load station library:', e);
		} finally {
			loading = false;
			searchInput?.focus();
		}
	});

	async function selectStation(station: RadioStation) {
		if (slot === null) return;
		saving = true;
		try {
			await fetch(`/api/radio/stations/${slot}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ name: station.name, url: station.url, slot })
			});
			await fetch(`/api/radio/stations/${slot}/play`, { method: 'POST' });
		} catch (e) {
			console.error('Failed to save/play station:', e);
		}
		goto('/');
	}
</script>

<svelte:head>
	<title>{slot !== null ? `Pick Station for Slot ${slot}` : 'Station Library'}</title>
</svelte:head>

<div class="min-h-screen bg-background">
	<!-- Header -->
	<header class="border-b bg-card sticky top-0 z-10">
		<div class="max-w-md mx-auto px-4">
			<div class="flex items-center gap-3 py-4">
				<Button variant="outline" size="icon" onclick={() => goto('/')}>
					<ArrowLeft class="w-4 h-4" />
				</Button>
				<h1 class="text-lg font-bold text-foreground">
					{slot !== null ? `Slot ${slot} — Pick a Station` : 'Station Library'}
				</h1>
			</div>
			<!-- Search -->
			<div class="pb-4">
				<input
					bind:this={searchInput}
					bind:value={query}
					type="search"
					placeholder="Search by name, country, or city…"
					disabled={loading}
					class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
				/>
			</div>
		</div>
	</header>

	<!-- Main -->
	<main class="max-w-md mx-auto px-4 py-4">
		{#if loading}
			<div class="space-y-3">
				{#each Array(8) as _}
					<div class="animate-pulse bg-card border border-border rounded-lg p-4">
						<div class="h-4 bg-muted rounded w-2/3 mb-2"></div>
						<div class="h-3 bg-muted rounded w-1/3"></div>
					</div>
				{/each}
			</div>
		{:else}
			<p class="text-xs text-muted-foreground mb-3">
				{#if filtered.length === 0}
					No results
				{:else if filtered.length < total}
					Showing {filtered.length} of {total.toLocaleString()} — refine your search
				{:else}
					{total.toLocaleString()} station{total !== 1 ? 's' : ''}
				{/if}
			</p>

			<ul class="space-y-2">
				{#each filtered as station (station.url)}
					<li>
						{#if slot !== null}
							<button
								onclick={() => selectStation(station)}
								disabled={saving}
								class="w-full text-left bg-card border border-border rounded-lg px-4 py-3 hover:bg-muted/50 transition-colors disabled:opacity-50"
							>
								<span class="block font-medium text-foreground text-sm">{station.name}</span>
								<span class="block text-xs text-muted-foreground mt-0.5">
									{[station.country, station.location].filter(Boolean).join(' · ')}
								</span>
							</button>
						{:else}
							<div class="bg-card border border-border rounded-lg px-4 py-3">
								<span class="block font-medium text-foreground text-sm">{station.name}</span>
								<span class="block text-xs text-muted-foreground mt-0.5">
									{[station.country, station.location].filter(Boolean).join(' · ')}
								</span>
							</div>
						{/if}
					</li>
				{/each}
			</ul>
		{/if}
	</main>
</div>
