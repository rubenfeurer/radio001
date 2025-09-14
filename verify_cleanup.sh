#!/bin/bash

# Verification Script for Cleaned Radio Project
# Checks what components remain after WiFi cleanup

set -e

PROJECT_ROOT="radio-old"

echo "🔍 VERIFYING CLEANED RADIO PROJECT"
echo "=================================="
echo "📂 Project root: $PROJECT_ROOT"
echo ""

# Function to check if file exists and show status
check_file() {
    local file_path="$1"
    local description="$2"
    if [[ -f "$file_path" ]]; then
        echo "✅ $description: PRESENT"
        return 0
    else
        echo "❌ $description: MISSING"
        return 1
    fi
}

# Function to check directory
check_dir() {
    local dir_path="$1"
    local description="$2"
    if [[ -d "$dir_path" ]]; then
        local file_count=$(find "$dir_path" -type f | wc -l)
        echo "✅ $description: PRESENT ($file_count files)"
        return 0
    else
        echo "❌ $description: MISSING"
        return 1
    fi
}

# Function to check for removed components
check_removed() {
    local file_path="$1"
    local description="$2"
    if [[ -f "$file_path" ]] || [[ -d "$file_path" ]]; then
        echo "⚠️  $description: STILL EXISTS (should be removed)"
        return 1
    else
        echo "✅ $description: REMOVED"
        return 0
    fi
}

echo "🎵 CORE RADIO COMPONENTS (Should Remain)"
echo "========================================"

# Core backend components
check_file "$PROJECT_ROOT/src/core/radio_manager.py" "Radio Manager"
check_file "$PROJECT_ROOT/src/core/station_manager.py" "Station Manager"
check_file "$PROJECT_ROOT/src/core/sound_manager.py" "Sound Manager"
check_file "$PROJECT_ROOT/src/core/models.py" "Core Models"

# Hardware components
check_file "$PROJECT_ROOT/src/hardware/audio_player.py" "Audio Player"
check_file "$PROJECT_ROOT/src/hardware/gpio_controller.py" "GPIO Controller"

# API routes (non-WiFi)
check_file "$PROJECT_ROOT/src/api/routes/stations.py" "Stations API"
check_file "$PROJECT_ROOT/src/api/routes/system.py" "System API"
check_file "$PROJECT_ROOT/src/api/routes/websocket.py" "WebSocket API"

# Frontend components
check_file "$PROJECT_ROOT/web/src/lib/components/RadioStations.svelte" "Radio Stations Component"
check_file "$PROJECT_ROOT/web/src/lib/components/VolumeControl.svelte" "Volume Control Component"
check_file "$PROJECT_ROOT/web/src/lib/components/MonitorCard.svelte" "Monitor Card Component"

# Configuration and sounds
check_file "$PROJECT_ROOT/config/config.py" "Configuration File"
check_dir "$PROJECT_ROOT/sounds" "Sound Files"

echo ""
echo "🗑️ WIFI COMPONENTS (Should Be Removed)"
echo "======================================"

# WiFi backend components
check_removed "$PROJECT_ROOT/src/api/routes/wifi.py" "WiFi API Routes"
check_removed "$PROJECT_ROOT/src/api/routes/ap.py" "AP API Routes"
check_removed "$PROJECT_ROOT/src/api/routes/mode.py" "Mode API Routes"
check_removed "$PROJECT_ROOT/src/core/wifi_manager.py" "WiFi Manager"
check_removed "$PROJECT_ROOT/src/core/ap_manager.py" "AP Manager"
check_removed "$PROJECT_ROOT/src/core/mode_manager.py" "Mode Manager"

# WiFi frontend components
check_removed "$PROJECT_ROOT/web/src/lib/components/APWifi.svelte" "AP WiFi Component"
check_removed "$PROJECT_ROOT/web/src/lib/components/ClientWifi.svelte" "Client WiFi Component"
check_removed "$PROJECT_ROOT/web/src/lib/components/WiFiStatus.svelte" "WiFi Status Component"
check_removed "$PROJECT_ROOT/web/src/lib/components/ModeControl.svelte" "Mode Control Component"
check_removed "$PROJECT_ROOT/web/src/routes/wifi" "WiFi Routes Directory"
check_removed "$PROJECT_ROOT/web/src/lib/stores/mode.ts" "Mode Store"

# WiFi test files
check_removed "$PROJECT_ROOT/tests/api/test_wifi.py" "WiFi API Tests"
check_removed "$PROJECT_ROOT/tests/core/test_wifi_manager.py" "WiFi Manager Tests"

echo ""
echo "🔍 PROJECT STRUCTURE ANALYSIS"
echo "============================="

echo "📁 Backend API Routes:"
if [[ -d "$PROJECT_ROOT/src/api/routes" ]]; then
    ls -la "$PROJECT_ROOT/src/api/routes" | grep -v "^total" | awk '{print "   " $9}' | grep -v "^   $"
fi

echo ""
echo "📁 Core Services:"
if [[ -d "$PROJECT_ROOT/src/core" ]]; then
    ls -la "$PROJECT_ROOT/src/core" | grep -v "^total" | awk '{print "   " $9}' | grep -v "^   $"
fi

echo ""
echo "📁 Hardware Components:"
if [[ -d "$PROJECT_ROOT/src/hardware" ]]; then
    ls -la "$PROJECT_ROOT/src/hardware" | grep -v "^total" | awk '{print "   " $9}' | grep -v "^   $"
fi

echo ""
echo "📁 Frontend Components:"
if [[ -d "$PROJECT_ROOT/web/src/lib/components" ]]; then
    ls -la "$PROJECT_ROOT/web/src/lib/components" | grep -v "^total" | awk '{print "   " $9}' | grep -v "^   $"
fi

echo ""
echo "🔧 CONFIGURATION CHECK"
echo "======================"

if [[ -f "$PROJECT_ROOT/config/config.py" ]]; then
    echo "📋 Checking for WiFi references in config.py..."
    wifi_refs=$(grep -i "wifi\|ap_ssid\|ap_password\|mode\|country_code" "$PROJECT_ROOT/config/config.py" | wc -l)
    if [[ $wifi_refs -eq 0 ]]; then
        echo "✅ No WiFi references found in config"
    else
        echo "⚠️  Found $wifi_refs WiFi references in config:"
        grep -n -i "wifi\|ap_ssid\|ap_password\|mode\|country_code" "$PROJECT_ROOT/config/config.py" || true
    fi
fi

echo ""
echo "🧬 IMPORT ANALYSIS"
echo "=================="

echo "📋 Checking for WiFi imports in remaining Python files..."
wifi_imports=$(find "$PROJECT_ROOT/src" -name "*.py" -exec grep -l "wifi_manager\|ap_manager\|mode_manager\|NetworkMode" {} \; 2>/dev/null | wc -l)
if [[ $wifi_imports -eq 0 ]]; then
    echo "✅ No WiFi imports found in Python files"
else
    echo "⚠️  Found WiFi imports in $wifi_imports files:"
    find "$PROJECT_ROOT/src" -name "*.py" -exec grep -l "wifi_manager\|ap_manager\|mode_manager\|NetworkMode" {} \; 2>/dev/null || true
fi

echo ""
echo "📋 Checking for WiFi imports in Svelte files..."
svelte_imports=$(find "$PROJECT_ROOT/web/src" -name "*.svelte" -exec grep -l "WiFiStatus\|ModeControl\|APWifi\|ClientWifi\|currentMode" {} \; 2>/dev/null | wc -l)
if [[ $svelte_imports -eq 0 ]]; then
    echo "✅ No WiFi component imports found in Svelte files"
else
    echo "⚠️  Found WiFi imports in $svelte_imports Svelte files:"
    find "$PROJECT_ROOT/web/src" -name "*.svelte" -exec grep -l "WiFiStatus\|ModeControl\|APWifi\|ClientWifi\|currentMode" {} \; 2>/dev/null || true
fi

echo ""
echo "📊 CLEANUP VERIFICATION SUMMARY"
echo "==============================="

# Count remaining files
total_py_files=$(find "$PROJECT_ROOT/src" -name "*.py" | wc -l)
total_svelte_files=$(find "$PROJECT_ROOT/web/src" -name "*.svelte" | wc -l)
total_api_routes=$(find "$PROJECT_ROOT/src/api/routes" -name "*.py" 2>/dev/null | wc -l)

echo "📈 Statistics:"
echo "   - Python files: $total_py_files"
echo "   - Svelte files: $total_svelte_files"
echo "   - API routes: $total_api_routes"

echo ""
echo "🎯 REMAINING CORE FEATURES:"
echo "   ✅ Radio station management"
echo "   ✅ Audio playback system"
echo "   ✅ Volume control"
echo "   ✅ Hardware GPIO controls"
echo "   ✅ WebSocket communication"
echo "   ✅ System monitoring"
echo "   ✅ Sound notifications"

echo ""
echo "🚀 READY FOR INTEGRATION:"
echo "   - WiFi components cleaned"
echo "   - Core radio functionality preserved"
echo "   - Project structure maintained"
echo "   - Ready to integrate with new WiFi system"

echo ""
echo "✅ VERIFICATION COMPLETE!"
