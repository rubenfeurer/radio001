<script lang="ts">
	export let signal: number | undefined = undefined;
	export let size: 'sm' | 'md' | 'lg' = 'md';

	$: bars = signal ? Math.ceil((signal / 100) * 4) : 0;
	$: color = getSignalColor(signal);

	function getSignalColor(signal: number | undefined): string {
		if (!signal) return 'text-gray-400';
		if (signal >= 75) return 'text-green-500';
		if (signal >= 50) return 'text-yellow-500';
		if (signal >= 25) return 'text-orange-500';
		return 'text-red-500';
	}

	$: sizeClasses = {
		sm: 'w-4 h-4',
		md: 'w-5 h-5',
		lg: 'w-6 h-6'
	}[size];
</script>

<div class="flex items-center space-x-1 {color}">
	<svg class={sizeClasses} viewBox="0 0 24 24" fill="none" stroke="currentColor">
		<!-- Bar 1 (always visible if signal > 0) -->
		<rect
			x="2" y="18" width="2" height="4"
			fill={bars >= 1 ? 'currentColor' : 'none'}
			stroke="currentColor"
			stroke-width="0.5"
		/>
		<!-- Bar 2 -->
		<rect
			x="6" y="15" width="2" height="7"
			fill={bars >= 2 ? 'currentColor' : 'none'}
			stroke="currentColor"
			stroke-width="0.5"
		/>
		<!-- Bar 3 -->
		<rect
			x="10" y="12" width="2" height="10"
			fill={bars >= 3 ? 'currentColor' : 'none'}
			stroke="currentColor"
			stroke-width="0.5"
		/>
		<!-- Bar 4 -->
		<rect
			x="14" y="9" width="2" height="13"
			fill={bars >= 4 ? 'currentColor' : 'none'}
			stroke="currentColor"
			stroke-width="0.5"
		/>
	</svg>

	{#if signal !== undefined}
		<span class="text-xs font-medium">{signal}%</span>
	{/if}
</div>
