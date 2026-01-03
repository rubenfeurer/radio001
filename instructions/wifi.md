# WiFi Setup Enhancement Plan - Using Default Pi Tools (wpa_cli)

## Overview

Enhance the WiFi setup interface with connection timeout, automatic retry, and saved network management using **Raspberry Pi's default `wpa_cli` tool** instead of custom implementations.

**Scope**: Option B - Moderate Enhancement
**Approach**: Leverage standard Pi OS tools (wpa_cli, wpa_supplicant) following RaspiWiFi patterns
**Estimated Effort**: 6-8 hours

---

## User Requirements Summary

1. ❌ **Hidden SSID support** - NOT needed (skipped)
2. ✅ **Connection timeout** - 40 seconds recommended
3. ✅ **Automatic retry** - 3 attempts with exponential backoff (0s, 5s, 10s)
4. ✅ **Saved networks** - View and forget only (using wpa_cli)
5. ✅ **Use Pi defaults** - wpa_cli for all network management

---

## Architecture Decision: Use wpa_cli

### Why wpa_cli?

- ✅ **Built into every Raspberry Pi OS** - No dependencies
- ✅ **Standard Pi tool** - Used by raspi-config and default WiFi management
- ✅ **Already partially used** - scripts/wifi-init.sh uses it for status
- ✅ **Safer than raw config files** - Handles locking and validation
- ✅ **Dynamic management** - No file parsing needed

### What wpa_cli Provides

```bash
# List all saved networks
wpa_cli -i wlan0 list_networks
# Output: network id / ssid / bssid / flags
# 0    HomeNetwork    any    [CURRENT]
# 1    OfficeWiFi     any    [DISABLED]

# Get connection status
wpa_cli -i wlan0 status
# Output: wpa_state=COMPLETED, ssid=HomeNetwork, ip_address=192.168.1.100

# Remove saved network
wpa_cli -i wlan0 remove_network 0
wpa_cli -i wlan0 save_config

# Reconfigure/reconnect
wpa_cli -i wlan0 reconfigure
```

---

## Implementation Plan

### Phase 1: Backend - wpa_cli Integration (3-4 hours)

#### File: `backend/main.py`

**1.1 Add wpa_cli Helper Method** (New, after line 230)

```python
@staticmethod
async def run_wpa_cli(command: List[str]) -> str:
    """
    Execute wpa_cli command and return output.
    
    Args:
        command: List of wpa_cli command arguments (e.g., ['list_networks'])
    
    Returns:
        stdout output as string
    """
    if Config.IS_DEVELOPMENT:
        # Mock data for development
        if command == ['list_networks']:
            return "network id / ssid / bssid / flags\n0\tTestNetwork\tany\t[DISABLED]\n"
        elif command == ['status']:
            return "wpa_state=DISCONNECTED\n"
        return ""
    
    try:
        process = await asyncio.create_subprocess_exec(
            "wpa_cli",
            "-i",
            Config.WIFI_INTERFACE,
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"wpa_cli command failed: {stderr.decode()}")
            raise Exception(f"wpa_cli error: {stderr.decode()}")
        
        return stdout.decode().strip()
    except Exception as e:
        logger.error(f"Failed to execute wpa_cli: {e}")
        raise
```

**1.2 Add Connection Validation Method** (New, after run_wpa_cli)

```python
@staticmethod
async def wait_for_connection(ssid: str, timeout: int = 40) -> bool:
    """
    Wait for WiFi connection to complete (pre-reboot validation).
    
    Uses wpa_cli to poll connection status every 2 seconds.
    
    Args:
        ssid: Expected SSID to connect to
        timeout: Maximum wait time in seconds (default: 40)
    
    Returns:
        True if connected successfully, False if timeout/failed
    """
    logger.info(f"Waiting for connection to {ssid} (timeout: {timeout}s)")
    
    start_time = asyncio.get_event_loop().time()
    poll_interval = 2  # Check every 2 seconds
    
    while (asyncio.get_event_loop().time() - start_time) < timeout:
        try:
            # Get wpa_supplicant state
            status_output = await WiFiManager.run_wpa_cli(['status'])
            
            # Parse status output
            status_dict = {}
            for line in status_output.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    status_dict[key] = value
            
            wpa_state = status_dict.get('wpa_state', '')
            current_ssid = status_dict.get('ssid', '')
            
            logger.debug(f"Connection status: state={wpa_state}, ssid={current_ssid}")
            
            # Check if connected
            if wpa_state == 'COMPLETED' and current_ssid == ssid:
                ip_address = status_dict.get('ip_address', 'N/A')
                logger.info(f"Successfully connected to {ssid} (IP: {ip_address})")
                return True
            
            # Check for failure states
            if wpa_state in ['DISCONNECTED', 'INACTIVE']:
                logger.warning(f"Connection failed: wpa_state={wpa_state}")
                # Don't return immediately, give it more time
        
        except Exception as e:
            logger.error(f"Error checking connection status: {e}")
        
        await asyncio.sleep(poll_interval)
    
    logger.error(f"Connection timeout after {timeout}s")
    return False
```

**1.3 Add Retry Logic to connect_network** (Modify existing, lines 323-372)

Replace existing `connect_network` method with retry version:

```python
@staticmethod
async def connect_network(credentials: WiFiCredentials) -> bool:
    """
    Connect to WiFi network with automatic retry (RaspiWiFi method with validation).
    
    Attempts connection up to 3 times with exponential backoff:
    - Attempt 1: Immediate (0s delay)
    - Attempt 2: 5s delay
    - Attempt 3: 10s delay
    
    Validates connection BEFORE rebooting system.
    """
    max_attempts = 3
    retry_delays = [0, 5, 10]  # Exponential backoff
    
    # Backup current config in case we need to rollback
    backup_path = Path("/tmp/wpa_supplicant.conf.backup")
    try:
        if Config.WPA_SUPPLICANT_FILE.exists() and not Config.IS_DEVELOPMENT:
            import shutil
            shutil.copy(Config.WPA_SUPPLICANT_FILE, backup_path)
            logger.info(f"Backed up current config to {backup_path}")
    except Exception as e:
        logger.warning(f"Could not backup config: {e}")
    
    for attempt in range(1, max_attempts + 1):
        logger.info(f"Connection attempt {attempt}/{max_attempts} to {credentials.ssid}")
        
        # Add delay before retry (skip for first attempt)
        if attempt > 1:
            delay = retry_delays[attempt - 1]
            logger.info(f"Waiting {delay}s before retry...")
            await asyncio.sleep(delay)
        
        try:
            # Write wpa_supplicant.conf
            if not await WiFiManager._write_wpa_config(credentials):
                logger.error(f"Attempt {attempt}: Failed to write config")
                continue
            
            # Reconfigure wpa_supplicant to apply new config
            if not Config.IS_DEVELOPMENT:
                try:
                    await WiFiManager.run_wpa_cli(['reconfigure'])
                    logger.info("Reconfigured wpa_supplicant with new credentials")
                except Exception as e:
                    logger.error(f"Failed to reconfigure wpa_supplicant: {e}")
                    continue
            
            # Wait for connection with 40s timeout
            if await WiFiManager.wait_for_connection(credentials.ssid, timeout=40):
                logger.info(f"Successfully connected on attempt {attempt}")
                return True
            
            logger.warning(f"Attempt {attempt} failed: Connection timeout")
        
        except Exception as e:
            logger.error(f"Attempt {attempt} failed with exception: {e}")
    
    # All attempts failed - restore backup if exists
    logger.error(f"All {max_attempts} connection attempts failed")
    
    if backup_path.exists() and not Config.IS_DEVELOPMENT:
        try:
            import shutil
            shutil.copy(backup_path, Config.WPA_SUPPLICANT_FILE)
            await WiFiManager.run_wpa_cli(['reconfigure'])
            logger.info("Restored original WiFi configuration")
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
    
    return False

@staticmethod
async def _write_wpa_config(credentials: WiFiCredentials) -> bool:
    """Helper method to write wpa_supplicant.conf (extracted from connect_network)"""
    if Config.IS_DEVELOPMENT:
        logger.info(f"Development mode: Simulating WiFi connection to {credentials.ssid}")
        await asyncio.sleep(1)
        return True
    
    try:
        logger.info(f"Creating wpa_supplicant.conf for {credentials.ssid}")
        
        # Create wpa_supplicant.conf (same as RaspiWiFi)
        wpa_config = [
            "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev",
            "update_config=1",
            "",
            "network={",
            f'    ssid="{credentials.ssid}"',
        ]
        
        if credentials.password:
            wpa_config.append(f'    psk="{credentials.password}"')
        else:
            wpa_config.append("    key_mgmt=NONE")
        
        wpa_config.append("}")
        
        # Write to temp file
        temp_file = Path("/tmp/wpa_supplicant.conf.tmp")
        temp_file.write_text("\n".join(wpa_config))
        logger.debug(f"Wrote temporary config to {temp_file}")
        
        # Move to final location (requires root)
        process = await asyncio.create_subprocess_exec(
            "sudo", "mv", str(temp_file), str(Config.WPA_SUPPLICANT_FILE),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            logger.info(f"Successfully wrote {Config.WPA_SUPPLICANT_FILE}")
            return True
        else:
            logger.error(f"Failed to move config file: {stderr.decode()}")
            return False
    
    except Exception as e:
        logger.error(f"Error writing WiFi credentials: {e}", exc_info=True)
        return False
```

**1.4 Add Saved Networks API Methods** (New, after connect_network)

```python
@staticmethod
async def list_saved_networks() -> List[Dict[str, Any]]:
    """
    List all saved WiFi networks using wpa_cli.
    
    Returns:
        List of saved networks with id, ssid, and flags
    """
    try:
        output = await WiFiManager.run_wpa_cli(['list_networks'])
        
        # Parse output
        # Format: network id / ssid / bssid / flags
        # 0    HomeNetwork    any    [CURRENT]
        # 1    OfficeWiFi     any    [DISABLED]
        
        lines = output.strip().split('\n')
        if len(lines) < 2:  # Header + at least one network
            return []
        
        networks = []
        for line in lines[1:]:  # Skip header
            parts = line.split('\t')
            if len(parts) >= 2:
                network_id = parts[0].strip()
                ssid = parts[1].strip()
                flags = parts[3].strip() if len(parts) >= 4 else ''
                
                is_current = '[CURRENT]' in flags
                is_disabled = '[DISABLED]' in flags
                
                networks.append({
                    'id': int(network_id),
                    'ssid': ssid,
                    'current': is_current,
                    'disabled': is_disabled
                })
        
        logger.info(f"Found {len(networks)} saved networks")
        return networks
    
    except Exception as e:
        logger.error(f"Failed to list saved networks: {e}")
        return []

@staticmethod
async def forget_network(network_id: int) -> bool:
    """
    Remove a saved WiFi network using wpa_cli.
    
    Args:
        network_id: Network ID from list_networks
    
    Returns:
        True if successfully removed
    """
    try:
        # Remove network
        await WiFiManager.run_wpa_cli(['remove_network', str(network_id)])
        
        # Save configuration to persist change
        await WiFiManager.run_wpa_cli(['save_config'])
        
        logger.info(f"Successfully removed network ID {network_id}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to remove network {network_id}: {e}")
        return False
```

**1.5 Add New API Endpoints** (New, after existing /wifi/connect endpoint ~line 640)

```python
@app.get("/wifi/saved", response_model=ApiResponse)
async def get_saved_networks():
    """Get list of saved WiFi networks using wpa_cli"""
    try:
        networks = await WiFiManager.list_saved_networks()
        return ApiResponse(
            success=True,
            message=f"Found {len(networks)} saved networks",
            data={"networks": networks}
        )
    except Exception as e:
        logger.error(f"Failed to get saved networks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/wifi/saved/{network_id}", response_model=ApiResponse)
async def forget_saved_network(network_id: int):
    """
    Forget/remove a saved WiFi network.
    
    Args:
        network_id: Network ID from wpa_cli list_networks
    """
    try:
        # Check if network exists
        saved_networks = await WiFiManager.list_saved_networks()
        network = next((n for n in saved_networks if n['id'] == network_id), None)
        
        if not network:
            raise HTTPException(status_code=404, detail=f"Network ID {network_id} not found")
        
        # Don't allow forgetting currently connected network
        if network.get('current', False):
            raise HTTPException(
                status_code=400,
                detail="Cannot forget currently connected network. Connect to another network first."
            )
        
        # Remove network
        success = await WiFiManager.forget_network(network_id)
        
        if success:
            return ApiResponse(
                success=True,
                message=f"Successfully forgot network: {network['ssid']}"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to remove network")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forgetting network {network_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**1.6 Update /wifi/connect Endpoint** (Modify existing, ~line 611)

```python
@app.post("/wifi/connect", response_model=ApiResponse)
async def connect_wifi(credentials: WiFiCredentials, background_tasks: BackgroundTasks):
    """
    Connect to WiFi network with retry logic and validation.
    
    Now validates connection BEFORE rebooting system.
    Returns success only if connection verified.
    """
    logger.info(f"Attempting to connect to WiFi: {credentials.ssid}")
    
    # Attempt connection with retry (validates before reboot)
    success = await WiFiManager.connect_network(credentials)
    
    if not success:
        logger.error(f"Failed to connect to {credentials.ssid} after retries")
        return ApiResponse(
            success=False,
            message=f"Failed to connect to '{credentials.ssid}'. Check password and try again.",
            data={
                "ssid": credentials.ssid,
                "attempts": 3,
                "timeout": 40
            }
        )
    
    # Connection successful - now switch to client mode and reboot
    try:
        logger.info(f"Connection verified. Switching to client mode and rebooting...")
        await WiFiManager.switch_to_client_mode()
        
        return ApiResponse(
            success=True,
            message=f"Connected to '{credentials.ssid}'. System rebooting to apply changes...",
            data={
                "ssid": credentials.ssid,
                "instructions": "System will reboot. Reconnect to the new WiFi network and navigate to http://radio.local"
            }
        )
    except Exception as e:
        logger.error(f"Mode switch failed: {e}", exc_info=True)
        return ApiResponse(
            success=False,
            message=f"Connected to WiFi but mode switch failed: {str(e)}",
            data={"ssid": credentials.ssid}
        )
```

---

### Phase 2: Frontend - WiFi Store Updates (2-3 hours)

#### File: `frontend/src/lib/stores/wifi.ts`

**2.1 Add Saved Networks Store** (Add after line 24)

```typescript
// Saved networks state
export const savedNetworks = writable<SavedNetwork[]>([]);
export const isLoadingSaved = writable(false);

// Connection progress tracking
export const connectionProgress = writable<ConnectionProgress>({
	status: 'idle',
	attempt: 0,
	maxAttempts: 3,
	message: ''
});
```

**2.2 Add Saved Networks Functions** (Add after resetToHotspot, ~line 190)

```typescript
/**
 * Get list of saved WiFi networks from wpa_cli
 */
export const getSavedNetworks = async () => {
	isLoadingSaved.set(true);
	error.set(null);

	try {
		const response = await fetch('/api/wifi/saved');

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}`);
		}

		const result: ApiResponse = await response.json();

		if (result.success && result.data) {
			savedNetworks.set(result.data.networks || []);
		} else {
			throw new Error(result.message || 'Failed to get saved networks');
		}
	} catch (err) {
		const errorMessage = err instanceof Error ? err.message : 'Failed to load saved networks';
		error.set(errorMessage);
		console.error('Error getting saved networks:', err);

		// Auto-dismiss error
		setTimeout(() => error.set(null), 5000);
	} finally {
		isLoadingSaved.set(false);
	}
};

/**
 * Forget/remove a saved WiFi network
 */
export const forgetNetwork = async (networkId: number, ssid: string): Promise<boolean> => {
	isLoadingSaved.set(true);
	error.set(null);

	try {
		const response = await fetch(`/api/wifi/saved/${networkId}`, {
			method: 'DELETE'
		});

		if (!response.ok) {
			const result = await response.json();
			throw new Error(result.detail || `HTTP ${response.status}`);
		}

		const result: ApiResponse = await response.json();

		if (result.success) {
			// Refresh saved networks list
			await getSavedNetworks();
			return true;
		} else {
			throw new Error(result.message || 'Failed to forget network');
		}
	} catch (err) {
		const errorMessage = err instanceof Error ? err.message : `Failed to forget ${ssid}`;
		error.set(errorMessage);
		console.error('Error forgetting network:', err);

		// Auto-dismiss error
		setTimeout(() => error.set(null), 5000);
		return false;
	} finally {
		isLoadingSaved.set(false);
	}
};
```

**2.3 Update connectToNetwork with Progress Tracking** (Modify existing, ~line 81)

```typescript
/**
 * Connect to WiFi network with retry and progress tracking
 */
export const connectToNetwork = async (
	credentials: WiFiCredentials
): Promise<boolean> => {
	isConnecting.set(true);
	error.set(null);

	// Initialize progress
	connectionProgress.set({
		status: 'connecting',
		attempt: 1,
		maxAttempts: 3,
		message: `Connecting to ${credentials.ssid}...`
	});

	try {
		const response = await fetch('/api/wifi/connect', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(credentials)
		});

		const result: ApiResponse = await response.json();

		if (result.success) {
			// Connection successful
			connectionProgress.set({
				status: 'success',
				attempt: 3,
				maxAttempts: 3,
				message: `Connected to ${credentials.ssid}! System rebooting...`
			});

			// Update status
			status.update((s) => ({
				...s,
				status: 'connected',
				ssid: credentials.ssid
			}));

			// Clear progress after delay
			setTimeout(() => {
				connectionProgress.set({
					status: 'idle',
					attempt: 0,
					maxAttempts: 3,
					message: ''
				});
			}, 5000);

			return true;
		} else {
			// Connection failed after retries
			connectionProgress.set({
				status: 'failed',
				attempt: 3,
				maxAttempts: 3,
				message: result.message || 'Connection failed'
			});

			error.set(result.message || 'Connection failed');

			// Clear progress after delay
			setTimeout(() => {
				connectionProgress.set({
					status: 'idle',
					attempt: 0,
					maxAttempts: 3,
					message: ''
				});
			}, 5000);

			return false;
		}
	} catch (err) {
		const errorMessage = err instanceof Error ? err.message : 'Connection failed';

		connectionProgress.set({
			status: 'failed',
			attempt: 0,
			maxAttempts: 3,
			message: errorMessage
		});

		error.set(errorMessage);
		console.error('Error connecting to network:', err);

		// Clear progress after delay
		setTimeout(() => {
			connectionProgress.set({
				status: 'idle',
				attempt: 0,
				maxAttempts: 3,
				message: ''
			});
		}, 5000);

		return false;
	} finally {
		isConnecting.set(false);
	}
};
```

---

### Phase 3: Frontend - Type Definitions (15 minutes)

#### File: `frontend/src/lib/types.ts`

**3.1 Add SavedNetwork Interface** (Add after WiFiStatus, ~line 28)

```typescript
export interface SavedNetwork {
	id: number; // wpa_cli network ID
	ssid: string;
	current: boolean; // Currently connected
	disabled: boolean; // Network disabled in wpa_supplicant
}

export interface ConnectionProgress {
	status: 'idle' | 'connecting' | 'verifying' | 'success' | 'failed';
	attempt: number;
	maxAttempts: number;
	message: string;
}
```

---

### Phase 4: Frontend - WiFi Settings Page (2-3 hours)

#### File: `frontend/src/routes/wifi-settings/+page.svelte` (NEW FILE)

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		savedNetworks,
		isLoadingSaved,
		error,
		getSavedNetworks,
		forgetNetwork
	} from '$lib/stores/wifi';
	import type { SavedNetwork } from '$lib/types';

	let confirmingDelete: number | null = null;

	onMount(() => {
		getSavedNetworks();
	});

	const handleForget = async (network: SavedNetwork) => {
		confirmingDelete = network.id;
	};

	const confirmForget = async (network: SavedNetwork) => {
		const success = await forgetNetwork(network.id, network.ssid);
		confirmingDelete = null;

		if (success) {
			// Optionally show success toast
			console.log(`Forgot network: ${network.ssid}`);
		}
	};

	const cancelForget = () => {
		confirmingDelete = null;
	};

	const addNetwork = () => {
		goto('/setup');
	};
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 shadow">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
			<div class="flex items-center justify-between">
				<button
					on:click={() => goto('/')}
					class="inline-flex items-center text-primary-600 hover:text-primary-700 dark:text-primary-400"
				>
					<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M15 19l-7-7 7-7"
						/>
					</svg>
					Back
				</button>

				<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Saved Networks</h1>

				<button
					on:click={addNetwork}
					class="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
				>
					<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 4v16m8-8H4"
						/>
					</svg>
					Add Network
				</button>
			</div>
		</div>
	</div>

	<!-- Content -->
	<div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Error Message -->
		{#if $error}
			<div class="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
				<div class="flex items-start">
					<svg class="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
						<path
							fill-rule="evenodd"
							d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
							clip-rule="evenodd"
						/>
					</svg>
					<p class="ml-3 text-sm text-red-600 dark:text-red-400">{$error}</p>
				</div>
			</div>
		{/if}

		<!-- Loading State -->
		{#if $isLoadingSaved}
			<div class="flex justify-center items-center py-12">
				<svg class="animate-spin h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
					<path
						class="opacity-75"
						fill="currentColor"
						d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
					/>
				</svg>
				<span class="ml-3 text-gray-600 dark:text-gray-400">Loading saved networks...</span>
			</div>
		{:else if $savedNetworks.length === 0}
			<!-- Empty State -->
			<div class="text-center py-12">
				<svg
					class="mx-auto h-12 w-12 text-gray-400"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"
					/>
				</svg>
				<h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">No saved networks</h3>
				<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
					Get started by connecting to a WiFi network.
				</p>
				<div class="mt-6">
					<button
						on:click={addNetwork}
						class="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
					>
						<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M12 4v16m8-8H4"
							/>
						</svg>
						Add Network
					</button>
				</div>
			</div>
		{:else}
			<!-- Networks List -->
			<div class="bg-white dark:bg-gray-800 shadow rounded-lg divide-y divide-gray-200 dark:divide-gray-700">
				{#each $savedNetworks as network (network.id)}
					<div class="p-4">
						<div class="flex items-center justify-between">
							<!-- Network Info -->
							<div class="flex-1">
								<div class="flex items-center">
									<span class="text-lg font-medium text-gray-900 dark:text-white">
										{network.ssid}
									</span>
									{#if network.current}
										<span
											class="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
										>
											Connected
										</span>
									{/if}
									{#if network.disabled}
										<span
											class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400"
										>
											Disabled
										</span>
									{/if}
								</div>
								<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Network ID: {network.id}</p>
							</div>

							<!-- Actions -->
							<div class="ml-4">
								{#if confirmingDelete === network.id}
									<!-- Confirmation Dialog -->
									<div class="flex items-center space-x-2">
										<span class="text-sm text-gray-600 dark:text-gray-400">Forget this network?</span>
										<button
											on:click={() => confirmForget(network)}
											class="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
										>
											Yes
										</button>
										<button
											on:click={cancelForget}
											class="px-3 py-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm rounded hover:bg-gray-300 dark:hover:bg-gray-600"
										>
											Cancel
										</button>
									</div>
								{:else}
									<button
										on:click={() => handleForget(network)}
										disabled={network.current}
										class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 shadow-sm text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
										title={network.current ? 'Cannot forget currently connected network' : 'Forget this network'}
									>
										<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
											/>
										</svg>
										Forget
									</button>
								{/if}
							</div>
						</div>
					</div>
				{/each}
			</div>

			<!-- Help Text -->
			<div class="mt-4 text-sm text-gray-500 dark:text-gray-400">
				<p>• Connected networks cannot be forgotten until you connect to another network</p>
				<p>• Forgetting a network removes its saved password</p>
			</div>
		{/if}
	</div>
</div>
```

---

### Phase 5: Frontend - Enhanced Setup Page (1 hour)

#### File: `frontend/src/routes/setup/+page.svelte`

**5.1 Import Connection Progress** (Add to imports, line 3)

```typescript
import { connectionProgress } from '$lib/stores/wifi';
```

**5.2 Add Progress Display** (Add after error message, ~line 85)

```svelte
<!-- Connection Progress -->
{#if $connectionProgress.status !== 'idle'}
	<div class="mb-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
		<div class="flex items-start">
			{#if $connectionProgress.status === 'connecting' || $connectionProgress.status === 'verifying'}
				<svg class="animate-spin h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" fill="none" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
				</svg>
			{:else if $connectionProgress.status === 'success'}
				<svg class="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
					<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
				</svg>
			{:else if $connectionProgress.status === 'failed'}
				<svg class="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
					<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
				</svg>
			{/if}
			<div class="ml-3 flex-1">
				<p class="text-sm font-medium {$connectionProgress.status === 'success' ? 'text-green-600 dark:text-green-400' : $connectionProgress.status === 'failed' ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'}">
					{$connectionProgress.message}
				</p>
				{#if $connectionProgress.maxAttempts > 1}
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
						Attempt {$connectionProgress.attempt}/{$connectionProgress.maxAttempts}
					</p>
				{/if}
			</div>
		</div>
	</div>
{/if}
```

---

### Phase 6: Frontend - Navigation Update (15 minutes)

#### File: `frontend/src/routes/+page.svelte`

**6.1 Add Saved Networks Link** (Add to WiFi section, after status display)

```svelte
<!-- WiFi Settings Link -->
<div class="mt-4">
	<a
		href="/wifi-settings"
		class="inline-flex items-center text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
	>
		<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
			/>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
			/>
		</svg>
		Manage Saved Networks
	</a>
</div>
```

---

### Phase 7: Testing (1-2 hours)

#### Add Unit Tests for New Functions

**File**: `backend/tests/api/test_wifi_routes.py`

Add tests for:
- `test_list_saved_networks_success`
- `test_list_saved_networks_empty`
- `test_forget_network_success`
- `test_forget_network_not_found`
- `test_forget_network_currently_connected`
- `test_connect_with_retry_success_first_attempt`
- `test_connect_with_retry_success_second_attempt`
- `test_connect_with_retry_all_failed`
- `test_wait_for_connection_success`
- `test_wait_for_connection_timeout`

**Example Test**:

```python
@pytest.mark.asyncio
async def test_list_saved_networks_success(self):
    """Test listing saved networks using wpa_cli"""
    
    # Mock wpa_cli output
    wpa_cli_output = """network id / ssid / bssid / flags
0	HomeNetwork	any	[CURRENT]
1	OfficeWiFi	any	[DISABLED]"""
    
    with patch.object(WiFiManager, 'run_wpa_cli', return_value=wpa_cli_output):
        networks = await WiFiManager.list_saved_networks()
        
        assert len(networks) == 2
        assert networks[0]['ssid'] == 'HomeNetwork'
        assert networks[0]['current'] is True
        assert networks[1]['ssid'] == 'OfficeWiFi'
        assert networks[1]['disabled'] is True
```

---

## Summary of Changes

### Backend (backend/main.py)
- ✅ New: `run_wpa_cli()` - Execute wpa_cli commands
- ✅ New: `wait_for_connection()` - Pre-reboot validation (40s timeout)
- ✅ Modified: `connect_network()` - Add retry logic (3 attempts, 0s/5s/10s delays)
- ✅ New: `_write_wpa_config()` - Helper for config writing
- ✅ New: `list_saved_networks()` - wpa_cli list_networks
- ✅ New: `forget_network()` - wpa_cli remove_network
- ✅ New: `GET /wifi/saved` - API endpoint for saved networks
- ✅ New: `DELETE /wifi/saved/{id}` - API endpoint to forget network
- ✅ Modified: `POST /wifi/connect` - Use new retry logic

### Frontend Stores (frontend/src/lib/stores/wifi.ts)
- ✅ New: `savedNetworks`, `isLoadingSaved`, `connectionProgress` stores
- ✅ New: `getSavedNetworks()` function
- ✅ New: `forgetNetwork()` function
- ✅ Modified: `connectToNetwork()` - Add progress tracking

### Frontend Types (frontend/src/lib/types.ts)
- ✅ New: `SavedNetwork` interface
- ✅ New: `ConnectionProgress` interface

### Frontend Pages
- ✅ New: `frontend/src/routes/wifi-settings/+page.svelte` - Saved networks management
- ✅ Modified: `frontend/src/routes/setup/+page.svelte` - Connection progress display
- ✅ Modified: `frontend/src/routes/+page.svelte` - Add navigation link

### Tests
- ✅ Add 10+ new unit tests for wpa_cli integration and retry logic

---

## Implementation Checklist

- [ ] Phase 1: Backend wpa_cli integration (3-4 hours)
  - [ ] Add `run_wpa_cli()` helper
  - [ ] Add `wait_for_connection()` validation
  - [ ] Update `connect_network()` with retry
  - [ ] Add `list_saved_networks()` and `forget_network()`
  - [ ] Add API endpoints `/wifi/saved` and `/wifi/saved/{id}`
  - [ ] Update `/wifi/connect` endpoint

- [ ] Phase 2: Frontend WiFi store (2-3 hours)
  - [ ] Add saved networks stores
  - [ ] Add `getSavedNetworks()` and `forgetNetwork()`
  - [ ] Update `connectToNetwork()` with progress

- [ ] Phase 3: Frontend types (15 min)
  - [ ] Add `SavedNetwork` interface
  - [ ] Add `ConnectionProgress` interface

- [ ] Phase 4: WiFi Settings page (2-3 hours)
  - [ ] Create `/wifi-settings` route
  - [ ] Implement saved networks list
  - [ ] Implement forget confirmation dialog

- [ ] Phase 5: Enhanced Setup page (1 hour)
  - [ ] Add connection progress display

- [ ] Phase 6: Navigation (15 min)
  - [ ] Add "Manage Saved Networks" link to dashboard

- [ ] Phase 7: Testing (1-2 hours)
  - [ ] Add backend unit tests
  - [ ] Manual testing on Pi hardware
  - [ ] Test connection retry flow
  - [ ] Test forget network flow

---

## Timeline Estimate

- **Day 1**: Backend implementation (Phases 1-2) - 5-7 hours
- **Day 2**: Frontend stores and types (Phase 3) - 2-3 hours
- **Day 3**: UI implementation (Phases 4-6) - 4-5 hours
- **Day 4**: Testing and refinement (Phase 7) - 2-3 hours

**Total: 13-18 hours** (realistic for careful implementation with testing)

---

## Key Benefits

1. **Uses Default Pi Tools** - wpa_cli is standard on all Pi OS installations
2. **No Extra Dependencies** - Everything already available
3. **Follows RaspiWiFi Patterns** - Compatible with existing architecture
4. **Pre-Reboot Validation** - Verifies connection before system reboot
5. **Automatic Retry** - 3 attempts with exponential backoff
6. **Saved Network Management** - View and forget networks
7. **Better UX** - Real-time progress feedback
8. **Rollback on Failure** - Restores original config if connection fails

---

## Testing Strategy

### Manual Testing Checklist

1. **Connection Success**
   - [ ] Connect to WPA2 network (correct password)
   - [ ] Connect to WPA3 network
   - [ ] Connect to open network (no password)
   - [ ] Verify pre-reboot validation works

2. **Connection Failure & Retry**
   - [ ] Wrong password (should retry 3 times, then fail)
   - [ ] Network out of range (should timeout and retry)
   - [ ] Verify original config restored on failure

3. **Saved Networks**
   - [ ] List saved networks shows all networks
   - [ ] Currently connected network shows "Connected" badge
   - [ ] Cannot forget currently connected network
   - [ ] Successfully forget disconnected network
   - [ ] Verify network removed from wpa_cli list_networks

4. **Progress Feedback**
   - [ ] "Connecting..." shows during attempts
   - [ ] Attempt counter updates (1/3, 2/3, 3/3)
   - [ ] Success message shows on connection
   - [ ] Failure message shows after all retries
   - [ ] Progress clears after 5 seconds

5. **Edge Cases**
   - [ ] Test in development mode (mock data)
   - [ ] Test connection timeout (40s)
   - [ ] Test concurrent connections
   - [ ] Test rapid connect/disconnect

---

## Rollback Plan

If issues occur:

1. **Revert backend changes** - Remove wpa_cli integration, restore original connect_network
2. **Revert frontend changes** - Remove saved networks page, restore original setup page
3. **Database/Config** - Original wpa_supplicant.conf is backed up during connection

---

## Security Considerations

1. **Password Handling** - Passwords never logged or exposed in API responses
2. **Sudo Permissions** - Already configured in Dockerfile for wpa_cli operations
3. **Network ID Validation** - Validate network ID exists before forgetting
4. **Current Network Protection** - Block forgetting currently connected network
5. **Config Backup** - Original config backed up before changes

---

## Future Enhancements (Out of Scope)

- Hidden SSID manual entry
- Network priority/ordering
- Static IP configuration
- Advanced security (WPA-Enterprise)
- QR code WiFi credentials
- Signal strength monitoring
- Auto-reconnect on connection loss
- Bandwidth usage statistics

---

**Ready to implement!** This plan uses Raspberry Pi's default wpa_cli tool for all network management, follows RaspiWiFi patterns, and provides a clean, tested implementation.
