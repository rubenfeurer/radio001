# Integration Tests

Integration tests for Radio001 system testing complete user journeys and workflows.

## 🎯 Hotspot Boot User Journey Test

### Overview

**File:** `test_hotspot_boot_user_journey.py`

This test simulates the complete real-world scenario of a user setting up the device for the first time or recovering from a lost WiFi connection.

### Test Scenario

The test covers the complete user journey from system boot to successful WiFi connection:

```
┌─────────────────────────────────────────────────────────────┐
│  HOTSPOT BOOT MODE - USER JOURNEY                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. System boots → No WiFi connection found                  │
│     ├─ Checks for saved WiFi (5s timeout)                   │
│     └─ Enters hotspot mode: "Radio-Setup"                   │
│                                                               │
│  2. User connects to hotspot                                 │
│     ├─ SSID: Radio-Setup                                     │
│     ├─ Password: Configure123!                               │
│     └─ Access: http://192.168.4.1                           │
│                                                               │
│  3. User opens web interface                                 │
│     └─ Navigates to http://192.168.4.1/setup                │
│                                                               │
│  4. User scans for networks                                  │
│     ├─ Clicks "Scan for Networks"                           │
│     └─ Sees available WiFi networks                         │
│                                                               │
│  5. User selects and connects                                │
│     ├─ Clicks on "HomeWiFi"                                 │
│     ├─ Enters password                                       │
│     ├─ Clicks "Connect"                                      │
│     └─ Backend validates connection (40s timeout)           │
│                                                               │
│  6. System switches modes                                    │
│     ├─ Stops hotspot (nmcli connection down Hotspot)        │
│     └─ Switches to client mode                              │
│                                                               │
│  7. User accesses via WiFi                                   │
│     ├─ Connects to "HomeWiFi"                               │
│     ├─ Opens http://radio.local                             │
│     └─ System shows connected status                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Test Coverage

#### ✅ Happy Path Tests

1. **`test_step1_system_boots_in_hotspot_mode`**
   - Verifies system enters hotspot mode on boot
   - Checks hotspot SSID and IP address
   - Confirms hotspot mode marker

2. **`test_step2_user_accesses_web_interface`**
   - Verifies web interface is accessible
   - Tests health check endpoint
   - Confirms system is operational

3. **`test_step3_user_scans_for_networks`**
   - Tests WiFi scanning functionality
   - Verifies network list is returned
   - Checks network details (SSID, signal, encryption)

4. **`test_step4_check_no_saved_networks`**
   - Verifies first-time setup (no saved networks)
   - Tests saved networks endpoint

5. **`test_step5_user_selects_and_connects_to_network`**
   - Tests connection request submission
   - Verifies password handling
   - Confirms connection initiation

6. **`test_step6_system_switches_to_client_mode`**
   - Tests connection validation (40s timeout)
   - Verifies mode switch logic
   - Confirms hotspot shutdown

7. **`test_step7_verify_client_mode_access`**
   - Tests post-connection status
   - Verifies client mode operation
   - Confirms WiFi connection details

8. **`test_complete_user_journey`**
   - Complete end-to-end integration test
   - Tests all steps sequentially
   - Validates entire user flow

#### ❌ Failure Scenario Tests

1. **`test_connection_failure_wrong_password`**
   - Wrong password → connection timeout
   - Error message displayed
   - User can retry

2. **`test_network_out_of_range`**
   - Network disappears after scan
   - Timeout error handling
   - User can rescan

3. **`test_user_can_retry_after_failure`**
   - Failed attempt doesn't lock system
   - User can correct mistake
   - Retry without reboot

### Key Validations

#### Backend Behavior
- ✅ Single connection attempt (no auto-retry)
- ✅ 40-second connection timeout
- ✅ Connection validation before mode switch
- ✅ Proper error messages on failure
- ✅ Mode switching logic
- ✅ Hotspot service management

#### Frontend Flow (API Level)
- ✅ WiFi status endpoint returns correct mode
- ✅ Network scanning works in hotspot mode
- ✅ Connection request accepts credentials
- ✅ Saved networks list is empty on first boot
- ✅ Error responses are properly formatted
- ✅ Success responses include connection confirmation

#### User Experience
- ✅ User can scan for networks multiple times
- ✅ User can retry failed connections
- ✅ Clear error messages guide troubleshooting
- ✅ No manual intervention needed for mode switch
- ✅ System remains accessible during errors

## 🚀 Running the Tests

### Prerequisites

```bash
# Install test dependencies
cd backend
pip install pytest pytest-asyncio
```

### Run All Integration Tests

```bash
cd backend
python -m pytest tests/integration/ -v
```

### Run Hotspot Boot Test Only

```bash
cd backend
python -m pytest tests/integration/test_hotspot_boot_user_journey.py -v
```

### Run with Detailed Output

```bash
cd backend
python -m pytest tests/integration/test_hotspot_boot_user_journey.py -v -s
```

### Run Complete Journey Test

```bash
cd backend
python -m pytest tests/integration/test_hotspot_boot_user_journey.py::TestHotspotBootUserJourney::test_complete_user_journey -v -s
```

### Expected Output

```
tests/integration/test_hotspot_boot_user_journey.py::TestHotspotBootUserJourney::test_complete_user_journey 

============================================================
HOTSPOT BOOT MODE - COMPLETE USER JOURNEY TEST
============================================================

[1] Checking initial system state...
    ✓ System in hotspot mode: Radio-Setup

[2] Verifying web interface accessibility...
    ✓ Web interface accessible at http://192.168.4.1

[3] Scanning for WiFi networks...
    ✓ Found 3 networks
      • HomeWiFi (85%)
      • OfficeNetwork (70%)
      • GuestNetwork (45%)

[4] Checking saved networks...
    ✓ No saved networks (first-time setup)

[5] Connecting to HomeWiFi...
    ✓ Connection request successful
    ⏳ Validating connection (40s timeout)...

[6] Validating connection and switching modes...
    ✓ Connection validated
    ✓ Switching to client mode...

[7] Verifying final state...
    ✓ System now in client mode
    ✓ Connected to: HomeWiFi
    ✓ IP address: 192.168.1.100
    ✓ Signal strength: 85%

============================================================
✅ COMPLETE USER JOURNEY TEST PASSED
============================================================

User can now access system at:
  • http://radio.local
  • http://192.168.1.100
============================================================

PASSED
```

## 🐛 Debugging Failed Tests

### Test Fails at Step 1
**Issue:** System not in hotspot mode
- Check `HOST_MODE_FILE` exists
- Verify boot script ran correctly
- Check NetworkManager status

### Test Fails at Step 3
**Issue:** No networks found
- Verify WiFi interface is up
- Check nmcli scan permissions
- Ensure NetworkManager is running

### Test Fails at Step 5
**Issue:** Connection fails
- Check password is correct
- Verify network is in range
- Review 40s timeout logs
- Check nmcli permissions

### Test Fails at Step 7
**Issue:** Not in client mode
- Check mode switch logic
- Verify `nmcli connection down Hotspot` ran
- Review system logs
- Check HOST_MODE_FILE removed

## 📋 Test Maintenance

### Updating Network List

Edit mock data in test file:

```python
manager.scan_networks.return_value = [
    WiFiNetwork(ssid="YourNetwork", signal=85, encryption="WPA2", frequency="2.4GHz"),
    # Add more networks...
]
```

### Adjusting Timeouts

Modify timeout values in assertions:

```python
# Current: 40s connection timeout
WIFI_CONNECT_TIMEOUT=40

# Update if you change config
```

### Adding New Test Steps

Follow this pattern:

```python
@pytest.mark.asyncio
async def test_step8_your_new_step(self, client, mock_wifi_manager):
    """
    Step 8: Description of new step
    
    User journey: What the user does in this step
    """
    # Your test code here
    pass
```

## 🔗 Related Tests

- `tests/core/test_wifi_manager.py` - Unit tests for WiFi manager
- `tests/api/test_wifi_routes.py` - API endpoint tests (if exists)
- `tests/test_integration.py` - Other integration tests

## 📚 Additional Resources

- [Backend Testing Guide](../TESTING.md)
- [WiFi Manager Documentation](../../core/wifi_manager.py)
- [Boot WiFi Check Script](../../../scripts/boot-wifi-check.sh)
- [Configuration Guide](../../../CONFIGURATION.md)
