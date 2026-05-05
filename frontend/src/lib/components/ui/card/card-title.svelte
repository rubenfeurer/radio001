<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		children?: import('svelte').Snippet;
		[key: string]: unknown;
	}

	let { class: className, children, ...rest }: Props = $props();
</script>

<h3 class={cn('text-lg font-semibold leading-none tracking-tight', className)} {...rest}>
	{@render children?.()}
</h3>
