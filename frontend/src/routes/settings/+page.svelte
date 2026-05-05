<script lang="ts">
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent } from '$lib/components/ui/card';
	import { ArrowLeft, Settings } from 'lucide-svelte';
</script>

<svelte:head>
	<title>Radio WiFi - Settings</title>
</svelte:head>

<div class="min-h-screen bg-background">
	<!-- Header -->
	<header class="border-b bg-card">
		<div class="max-w-md mx-auto px-4">
			<div class="flex items-center space-x-3 py-4">
				<Button variant="outline" size="icon" onclick={() => goto('/')}>
					<ArrowLeft class="w-4 h-4" />
				</Button>
				<div>
					<h1 class="text-xl font-bold text-foreground">Settings</h1>
					<p class="text-sm text-muted-foreground">System preferences</p>
				</div>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-md mx-auto px-4 py-6">
		<Card>
			<CardContent class="pt-6 text-center">
				<Settings class="w-12 h-12 text-muted-foreground mx-auto mb-4" />
				<h2 class="text-lg font-medium text-foreground mb-2">Settings Coming Soon</h2>
				<p class="text-muted-foreground text-sm mb-4">
					Advanced settings and configuration options will be available in a future update.
				</p>
				<Button onclick={() => goto('/')}>Return Home</Button>
			</CardContent>
		</Card>
	</main>
</div>
