<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { WiFiNetwork, SavedNetwork } from '$lib/types';
	import {
		wifiState,
		scanNetworks,
		connectToNetwork,
		getSavedNetworks,
		forgetNetwork,
		resetToHotspot,
		getSignalColor,
		requiresPassword
	} from '$lib/stores/wifi.svelte';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Input } from '$lib/components/ui/input';
	import { ArrowLeft, RefreshCw, Lock, Wifi, CheckCircle, XCircle, Loader2 } from 'lucide-svelte';

	interface CombinedNetwork extends WiFiNetwork {
		isSaved?: boolean;
		isCurrent?: boolean;
		savedId?: number;
	}

	let selectedNetwork = $state<CombinedNetwork | null>(null);
	let password = $state('');
	let showPassword = $state(false);
	let confirmingForget = $state(false);
	let confirmingReset = $state(false);

	const combinedNetworks = $derived(
		wifiState.networks
			.reduce((acc, network) => {
				const existing = acc.find((n) => n.ssid === network.ssid);
				if (!existing) {
					const savedNetwork = wifiState.savedNetworks.find((s) => s.ssid === network.ssid);
					acc.push({
						...network,
						isSaved: !!savedNetwork,
						isCurrent: savedNetwork?.current || false,
						savedId: savedNetwork?.id
					} as CombinedNetwork);
				}
				return acc;
			}, [] as CombinedNetwork[])
			.sort((a, b) => {
				if (a.isCurrent) return -1;
				if (b.isCurrent) return 1;
				if (a.isSaved && !b.isSaved) return -1;
				if (b.isSaved && !a.isSaved) return 1;
				return b.signal - a.signal;
			})
	);

	onMount(() => {
		scanNetworks();
		getSavedNetworks();
	});

	const handleNetworkClick = (network: CombinedNetwork) => {
		selectedNetwork = network;
		password = '';
		confirmingForget = false;
	};

	const handleConnect = async () => {
		if (!selectedNetwork) return;
		const success = await connectToNetwork({
			ssid: selectedNetwork.ssid,
			password,
			security: selectedNetwork.security
		});
		if (success) {
			selectedNetwork = null;
			password = '';
		}
	};

	const handleForget = async () => {
		if (!selectedNetwork?.savedId) return;
		const success = await forgetNetwork(selectedNetwork.savedId, selectedNetwork.ssid);
		if (success) {
			selectedNetwork = null;
			confirmingForget = false;
			await getSavedNetworks();
			await scanNetworks();
		}
	};

	const closeDialog = () => {
		selectedNetwork = null;
		password = '';
		confirmingForget = false;
	};

	const handleResetToHotspot = async () => {
		const success = await resetToHotspot();
		if (success) confirmingReset = false;
	};
</script>

<svelte:head>
	<title>Radio WiFi - WiFi Manager</title>
</svelte:head>

<div class="min-h-screen bg-background">
	<!-- Header -->
	<header class="border-b bg-card sticky top-0 z-10">
		<div class="max-w-md mx-auto px-4">
			<div class="flex items-center justify-between py-4">
				<div class="flex items-center space-x-3">
					<Button variant="outline" size="icon" onclick={() => goto('/')}>
						<ArrowLeft class="w-4 h-4" />
					</Button>
					<div>
						<h1 class="text-xl font-bold text-foreground">WiFi Manager</h1>
						<p class="text-sm text-muted-foreground">Connect to networks and manage WiFi</p>
					</div>
				</div>
				<Button
					variant="outline"
					size="icon"
					onclick={() => { scanNetworks(); getSavedNetworks(); }}
					disabled={wifiState.isScanning || wifiState.isLoadingSaved}
				>
					<RefreshCw class="w-4 h-4 {wifiState.isScanning || wifiState.isLoadingSaved ? 'animate-spin' : ''}" />
				</Button>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-md mx-auto px-4 py-6">
		<!-- Error Display -->
		{#if wifiState.error}
			<div class="border border-destructive/50 bg-destructive/10 rounded-lg p-4 mb-6">
				<p class="text-destructive text-sm">{wifiState.error}</p>
			</div>
		{/if}

		<!-- Connection Progress -->
		{#if wifiState.connectionProgress.status !== 'idle'}
			<div class="border rounded-lg p-4 mb-6 {
				wifiState.connectionProgress.status === 'success' ? 'border-green-200 bg-green-50' :
				wifiState.connectionProgress.status === 'failed' ? 'border-destructive/50 bg-destructive/10' :
				'border-blue-200 bg-blue-50'
			}">
				<div class="flex items-start gap-3">
					{#if wifiState.connectionProgress.status === 'connecting' || wifiState.connectionProgress.status === 'verifying'}
						<Loader2 class="w-5 h-5 text-blue-600 animate-spin mt-0.5" />
					{:else if wifiState.connectionProgress.status === 'success'}
						<CheckCircle class="w-5 h-5 text-green-600 mt-0.5" />
					{:else}
						<XCircle class="w-5 h-5 text-destructive mt-0.5" />
					{/if}
					<p class="text-sm font-medium {
						wifiState.connectionProgress.status === 'success' ? 'text-green-700' :
						wifiState.connectionProgress.status === 'failed' ? 'text-destructive' :
						'text-blue-700'
					}">
						{wifiState.connectionProgress.message}
					</p>
				</div>
			</div>
		{/if}

		<!-- Networks List -->
		<Card class="mb-6">
			<CardHeader>
				<CardTitle>WiFi Networks</CardTitle>
			</CardHeader>
			<div class="max-h-96 overflow-y-auto">
				{#if wifiState.isScanning}
					<div class="p-6 text-center">
						<Loader2 class="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
						<p class="text-muted-foreground">Scanning for networks...</p>
					</div>
				{:else if combinedNetworks.length === 0}
					<div class="p-6 text-center">
						<Wifi class="w-8 h-8 text-muted-foreground mx-auto mb-4" />
						<p class="text-muted-foreground mb-4">No networks found</p>
						<Button onclick={() => { scanNetworks(); getSavedNetworks(); }}>Scan Again</Button>
					</div>
				{:else}
					{#each combinedNetworks as network}
						<button
							onclick={() => handleNetworkClick(network)}
							class="w-full px-4 py-3 text-left hover:bg-muted/50 border-b border-border last:border-b-0 transition-colors"
						>
							<div class="flex items-center justify-between">
								<div class="flex-1">
									<div class="flex items-center gap-2">
										<span class="font-medium text-foreground text-sm">{network.ssid}</span>
										{#if network.security !== 'Open'}
											<Lock class="w-3.5 h-3.5 text-muted-foreground" />
										{/if}
										{#if network.isCurrent}
											<Badge variant="secondary" class="text-green-700 bg-green-100">Connected</Badge>
										{:else if network.isSaved}
											<Badge variant="secondary">Saved</Badge>
										{/if}
									</div>
									</div>
								<div class="flex items-center gap-1.5">
									<span class="text-sm {getSignalColor(network.signal)}">{network.signal}%</span>
									<Wifi class="w-4 h-4 {getSignalColor(network.signal)}" />
								</div>
							</div>
						</button>
					{/each}
				{/if}
			</div>
		</Card>

		<!-- Action Dialog -->
		{#if selectedNetwork}
			<Card class="mb-6">
				<CardHeader>
					<CardTitle>{selectedNetwork.ssid}</CardTitle>
				</CardHeader>
				<CardContent>
					{#if selectedNetwork.isCurrent}
						{#if confirmingForget}
							<div class="space-y-4">
								<p class="text-sm text-muted-foreground">
									Are you sure you want to forget this network? You'll need to re-enter the password to connect again.
								</p>
								<div class="flex gap-3">
									<Button variant="outline" class="flex-1" onclick={() => (confirmingForget = false)}>Cancel</Button>
									<Button variant="destructive" class="flex-1" onclick={handleForget}>Forget Network</Button>
								</div>
							</div>
						{:else}
							<div class="space-y-4">
								<div class="flex items-center gap-2 text-green-600">
									<CheckCircle class="w-5 h-5" />
									<span class="text-sm font-medium">Currently connected</span>
								</div>
								<Button variant="outline" class="w-full" onclick={() => (confirmingForget = true)}>Forget Network</Button>
							</div>
						{/if}
					{:else if selectedNetwork.isSaved}
						{#if confirmingForget}
							<div class="space-y-4">
								<p class="text-sm text-muted-foreground">
									Are you sure you want to forget this network? You'll need to re-enter the password to connect again.
								</p>
								<div class="flex gap-3">
									<Button variant="outline" class="flex-1" onclick={() => (confirmingForget = false)}>Cancel</Button>
									<Button variant="destructive" class="flex-1" onclick={handleForget}>Forget Network</Button>
								</div>
							</div>
						{:else}
							<div class="space-y-4">
								<p class="text-sm text-muted-foreground">Saved network. Connect using the saved password.</p>
								<div class="flex gap-3">
									<Button variant="outline" class="flex-1" onclick={closeDialog}>Cancel</Button>
									<Button class="flex-1" onclick={handleConnect} disabled={wifiState.isConnecting}>
										{#if wifiState.isConnecting}
											<Loader2 class="w-4 h-4 animate-spin mr-2" />Connecting...
										{:else}
											Connect
										{/if}
									</Button>
								</div>
								<Button variant="outline" class="w-full" onclick={() => (confirmingForget = true)}>
									Forget Network
								</Button>
							</div>
						{/if}
					{:else}
						{#if requiresPassword(selectedNetwork)}
							<div class="mb-4">
								<label for="password" class="block text-sm font-medium text-foreground mb-2">Password</label>
								<div class="relative">
									<Input
										id="password"
										type={showPassword ? 'text' : 'password'}
										bind:value={password}
										placeholder="Enter WiFi password"
										disabled={wifiState.isConnecting}
										class="pr-10"
									/>
									<button
										type="button"
										onclick={() => (showPassword = !showPassword)}
										class="absolute inset-y-0 right-0 pr-3 flex items-center text-muted-foreground hover:text-foreground"
									>
										{#if showPassword}
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
											</svg>
										{:else}
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
											</svg>
										{/if}
									</button>
								</div>
							</div>
						{:else}
							<p class="text-sm text-muted-foreground mb-4">Open network. No password required.</p>
						{/if}
						<div class="flex gap-3">
							<Button variant="outline" class="flex-1" onclick={closeDialog} disabled={wifiState.isConnecting}>Cancel</Button>
							<Button
								class="flex-1"
								onclick={handleConnect}
								disabled={wifiState.isConnecting || (requiresPassword(selectedNetwork) && !password.trim())}
							>
								{#if wifiState.isConnecting}
									<Loader2 class="w-4 h-4 animate-spin mr-2" />Connecting...
								{:else}
									Connect
								{/if}
							</Button>
						</div>
					{/if}
				</CardContent>
			</Card>
		{/if}

		<!-- Reset to Hotspot -->
		<div class="mt-8 pt-6 border-t border-border">
			{#if confirmingReset}
				<Card>
					<CardContent class="pt-6">
						<div class="space-y-4">
							<div>
								<h3 class="text-sm font-medium text-foreground mb-2">Change to Hotspot Mode?</h3>
								<ul class="text-sm text-muted-foreground space-y-1 list-disc list-inside">
									<li>Disconnect from current WiFi</li>
									<li>Enable hotspot mode (SSID: Radio-Setup)</li>
									<li>Reboot the system</li>
								</ul>
								<p class="text-sm text-muted-foreground mt-2">
									After reboot, connect to "Radio-Setup" and navigate to <strong>http://radio.local</strong>
								</p>
							</div>
							<div class="flex gap-3">
								<Button variant="destructive" onclick={handleResetToHotspot}>Yes, Reset</Button>
								<Button variant="outline" onclick={() => (confirmingReset = false)}>Cancel</Button>
							</div>
						</div>
					</CardContent>
				</Card>
			{:else}
				<Button variant="outline" class="w-full" onclick={() => (confirmingReset = true)}>
					<Wifi class="w-4 h-4 mr-2" />
					Change to Hotspot Mode
				</Button>
			{/if}
		</div>
	</main>
</div>
