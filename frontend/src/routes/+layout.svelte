<script lang="ts">
	import '../app.postcss';

	let { children } = $props();
</script>

<main class="min-h-screen bg-background">
	{@render children()}
</main>
