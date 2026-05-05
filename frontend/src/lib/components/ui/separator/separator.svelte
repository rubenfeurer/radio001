<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		orientation?: 'horizontal' | 'vertical';
		class?: string;
		[key: string]: unknown;
	}

	let { orientation = 'horizontal', class: className, ...rest }: Props = $props();
</script>

<div
	role="separator"
	class={cn(
		'shrink-0 bg-border',
		orientation === 'horizontal' ? 'h-[1px] w-full' : 'h-full w-[1px]',
		className
	)}
	{...rest}
></div>
