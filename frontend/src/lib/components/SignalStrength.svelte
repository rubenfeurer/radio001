<script lang="ts">
	interface Props {
		signal?: number;
		size?: 'sm' | 'md' | 'lg';
	}

	let { signal, size = 'md' }: Props = $props();

	const bars = $derived(signal ? Math.ceil((signal / 100) * 4) : 0);

	const color = $derived(() => {
		if (!signal) return 'text-gray-400';
		if (signal >= 75) return 'text-green-500';
		if (signal >= 50) return 'text-yellow-500';
		if (signal >= 25) return 'text-orange-500';
		return 'text-red-500';
	});

	const sizeClass = $derived(({ sm: 'w-4 h-4', md: 'w-5 h-5', lg: 'w-6 h-6' } as const)[size]);
</script>

<div class="flex items-center space-x-1 {color()}">
	<svg class={sizeClass} viewBox="0 0 24 24" fill="none" stroke="currentColor">
		<rect x="2" y="18" width="2" height="4" fill={bars >= 1 ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="0.5" />
		<rect x="6" y="15" width="2" height="7" fill={bars >= 2 ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="0.5" />
		<rect x="10" y="12" width="2" height="10" fill={bars >= 3 ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="0.5" />
		<rect x="14" y="9" width="2" height="13" fill={bars >= 4 ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="0.5" />
	</svg>
	{#if signal !== undefined}
		<span class="text-xs font-medium">{signal}%</span>
	{/if}
</div>
