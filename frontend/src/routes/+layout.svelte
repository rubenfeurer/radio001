<script lang="ts">
	import '../app.postcss';
	import { onMount } from 'svelte';

	// SvelteKit layout props - explicitly define what we accept
	export let data: any = undefined;

	// Dark mode management
	let darkMode = false;

	onMount(() => {
		// Check for saved theme or default to system preference
		const savedTheme = localStorage.getItem('theme');
		if (savedTheme === 'dark') {
			darkMode = true;
		} else if (savedTheme === 'light') {
			darkMode = false;
		} else {
			darkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
		}
		updateTheme();
	});

	function updateTheme() {
		if (darkMode) {
			document.documentElement.classList.add('dark');
			localStorage.setItem('theme', 'dark');
		} else {
			document.documentElement.classList.remove('dark');
			localStorage.setItem('theme', 'light');
		}
	}

	function toggleTheme() {
		darkMode = !darkMode;
		updateTheme();
	}
</script>

<main class="min-h-screen">
	<slot />
</main>
