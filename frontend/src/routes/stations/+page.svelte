<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import type { RadioStation } from '$lib/types';

	let slot: number | null = null;
	let allStations: RadioStation[] = [];
	let query = '';
	let loading = true;
	let saving = false;
	let searchInput: HTMLInputElement;

	$: slot = $page.url.searchParams.has('slot')
		? parseInt($page.url.searchParams.get('slot')!, 10)
		: null;

	$: q = query.toLowerCase().trim();
	$: filtered = q
		? allStations
				.filter(
					(s) =>
						s.name.toLowerCase().includes(q) ||
						(s.country || '').toLowerCase().includes(q) ||
						(s.location || '').toLowerCase().includes(q)
				)
				.slice(0, 100)
		: allStations.slice(0, 100);
	$: total = q
		? allStations.filter(
				(s) =>
					s.name.toLowerCase().includes(q) ||
					(s.country || '').toLowerCase().includes(q) ||
					(s.location || '').toLowerCase().includes(q)
			).length
		: allStations.length;

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
			// Auto-play after saving
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

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<header class="bg-white dark:bg-gray-800 shadow sticky top-0 z-10">
		<div class="max-w-md mx-auto px-4">
			<div class="flex items-center gap-3 py-4">
				<a href="/" class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200">
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
					</svg>
				</a>
				<div>
					<h1 class="text-lg font-bold text-gray-900 dark:text-white">
						{slot !== null ? `Slot ${slot} — Pick a Station` : 'Station Library'}
					</h1>
				</div>
			</div>
			<!-- Search -->
			<div class="pb-4">
				<input
					bind:this={searchInput}
					bind:value={query}
					type="search"
					placeholder="Search by name, country, or city…"
					disabled={loading}
					class="w-full px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
				/>
			</div>
		</div>
	</header>

	<!-- Main -->
	<main class="max-w-md mx-auto px-4 py-4">
		{#if loading}
			<div class="space-y-3">
				{#each Array(8) as _}
					<div class="animate-pulse bg-white dark:bg-gray-800 rounded-lg p-4">
						<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3 mb-2"></div>
						<div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
					</div>
				{/each}
			</div>
		{:else}
			<!-- Result count -->
			<p class="text-xs text-gray-500 dark:text-gray-400 mb-3">
				{#if filtered.length === 0}
					No results
				{:else if filtered.length < total}
					Showing {filtered.length} of {total.toLocaleString()} — refine your search
				{:else}
					{total.toLocaleString()} station{total !== 1 ? 's' : ''}
				{/if}
			</p>

			<!-- Station list -->
			<ul class="space-y-2">
				{#each filtered as station (station.url)}
					<li>
						{#if slot !== null}
							<button
								on:click={() => selectStation(station)}
								disabled={saving}
								class="w-full text-left bg-white dark:bg-gray-800 rounded-lg px-4 py-3 hover:bg-primary-50 dark:hover:bg-primary-900/20 border border-gray-100 dark:border-gray-700 transition-colors disabled:opacity-50"
							>
								<span class="block font-medium text-gray-900 dark:text-white text-sm">{station.name}</span>
								<span class="block text-xs text-gray-500 dark:text-gray-400 mt-0.5">
									{[station.country, station.location].filter(Boolean).join(' · ')}
								</span>
							</button>
						{:else}
							<div class="bg-white dark:bg-gray-800 rounded-lg px-4 py-3 border border-gray-100 dark:border-gray-700">
								<span class="block font-medium text-gray-900 dark:text-white text-sm">{station.name}</span>
								<span class="block text-xs text-gray-500 dark:text-gray-400 mt-0.5">
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
