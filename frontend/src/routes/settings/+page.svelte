<script lang="ts">
	import { goto } from '$app/navigation';
</script>

<svelte:head>
	<title>Radio WiFi - Settings</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<header class="bg-white dark:bg-gray-800 shadow">
		<div class="max-w-md mx-auto px-4">
			<div class="flex items-center justify-between py-4">
				<div class="flex items-center space-x-3">
					<button
						on:click={() => goto('/')}
						class="btn-secondary p-2"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
						</svg>
					</button>
					<div>
						<h1 class="text-xl font-bold text-gray-900 dark:text-white">
							Settings
						</h1>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							System preferences
						</p>
					</div>
				</div>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-md mx-auto px-4 py-6">
		<div class="card p-6 text-center">
			<svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
					d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
			</svg>
			<h2 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Settings Coming Soon</h2>
			<p class="text-gray-600 dark:text-gray-400 text-sm mb-4">
				Advanced settings and configuration options will be available in a future update.
			</p>
			<button on:click={() => goto('/')} class="btn-primary">
				Return Home
			</button>
		</div>
	</main>
</div>
