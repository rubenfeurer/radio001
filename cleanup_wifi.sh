#!/bin/bash

# WiFi Cleanup Script for Old Radio Project
# Removes all WiFi-related components to prepare for integration with new WiFi system

set -e  # Exit on any error

PROJECT_ROOT="radio-old"
BACKUP_DIR="wifi-backup-$(date +%Y%m%d-%H%M%S)"

echo "🧹 Starting WiFi component cleanup for old radio project..."
echo "📂 Project root: $PROJECT_ROOT"
echo "💾 Backup directory: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"
echo "✅ Created backup directory"

# Function to backup and remove file
backup_and_remove() {
    local file_path="$1"
    if [[ -f "$file_path" ]]; then
        echo "🔄 Backing up and removing: $file_path"
        # Create backup directory structure
        local backup_path="$BACKUP_DIR/${file_path#$PROJECT_ROOT/}"
        mkdir -p "$(dirname "$backup_path")"
        cp "$file_path" "$backup_path"
        rm "$file_path"
    elif [[ -d "$file_path" ]]; then
        echo "🔄 Backing up and removing directory: $file_path"
        # Create backup directory structure
        local backup_path="$BACKUP_DIR/${file_path#$PROJECT_ROOT/}"
        mkdir -p "$(dirname "$backup_path")"
        cp -r "$file_path" "$backup_path"
        rm -rf "$file_path"
    else
        echo "⚠️  File not found (skipping): $file_path"
    fi
}

echo ""
echo "📁 BACKEND FILES"
echo "=================="

# Backend API routes
backup_and_remove "$PROJECT_ROOT/src/api/routes/wifi.py"
backup_and_remove "$PROJECT_ROOT/src/api/routes/ap.py"
backup_and_remove "$PROJECT_ROOT/src/api/routes/mode.py"

# Backend core components
backup_and_remove "$PROJECT_ROOT/src/core/wifi_manager.py"
backup_and_remove "$PROJECT_ROOT/src/core/ap_manager.py"
backup_and_remove "$PROJECT_ROOT/src/core/mode_manager.py"

echo ""
echo "🎨 FRONTEND FILES"
echo "=================="

# Frontend components
backup_and_remove "$PROJECT_ROOT/web/src/lib/components/APWifi.svelte"
backup_and_remove "$PROJECT_ROOT/web/src/lib/components/ClientWifi.svelte"
backup_and_remove "$PROJECT_ROOT/web/src/lib/components/WiFiStatus.svelte"
backup_and_remove "$PROJECT_ROOT/web/src/lib/components/ModeControl.svelte"

# Frontend routes
backup_and_remove "$PROJECT_ROOT/web/src/routes/wifi"

# Frontend stores
backup_and_remove "$PROJECT_ROOT/web/src/lib/stores/mode.ts"

echo ""
echo "🧪 TEST FILES"
echo "=============="

# Test files
backup_and_remove "$PROJECT_ROOT/tests/api/test_wifi.py"
backup_and_remove "$PROJECT_ROOT/tests/core/test_wifi_manager.py"

echo ""
echo "📝 MODIFYING CONFIGURATION FILES"
echo "=================================="

# Backup original config file
if [[ -f "$PROJECT_ROOT/config/config.py" ]]; then
    echo "🔄 Backing up config.py"
    cp "$PROJECT_ROOT/config/config.py" "$BACKUP_DIR/config.py.original"

    echo "✂️  Removing WiFi settings from config.py"
    # Remove WiFi-related configuration lines
    sed -i.bak '/AP_SSID\|AP_PASSWORD\|AP_CHANNEL\|AP_BAND\|COUNTRY_CODE/d' "$PROJECT_ROOT/config/config.py"
    rm "$PROJECT_ROOT/config/config.py.bak"
fi

# Backup and modify models.py
if [[ -f "$PROJECT_ROOT/src/core/models.py" ]]; then
    echo "🔄 Backing up models.py"
    cp "$PROJECT_ROOT/src/core/models.py" "$BACKUP_DIR/models.py.original"

    echo "✂️  Removing WiFi models from models.py"
    # Create a temporary file with WiFi-related classes removed
    python3 - << 'EOF'
import sys
import re

input_file = "radio-old/src/core/models.py"
output_file = "radio-old/src/core/models.py.new"

with open(input_file, 'r') as f:
    content = f.read()

# Remove NetworkMode enum
content = re.sub(r'class NetworkMode\(str, Enum\):.*?\n\n', '', content, flags=re.DOTALL)

# Remove WiFi-related classes
wifi_classes = ['WiFiNetwork', 'WiFiStatus']
for class_name in wifi_classes:
    pattern = f'class {class_name}\\(BaseModel\\):.*?(?=\\n\\nclass|\\n\\n$|$)'
    content = re.sub(pattern, '', content, flags=re.DOTALL)

# Clean up extra newlines
content = re.sub(r'\n{3,}', '\n\n', content)

with open(output_file, 'w') as f:
    f.write(content)
EOF

    if [[ -f "$PROJECT_ROOT/src/core/models.py.new" ]]; then
        mv "$PROJECT_ROOT/src/core/models.py.new" "$PROJECT_ROOT/src/core/models.py"
        echo "✅ Updated models.py"
    fi
fi

# Backup and modify radio_manager.py
if [[ -f "$PROJECT_ROOT/src/core/radio_manager.py" ]]; then
    echo "🔄 Backing up radio_manager.py"
    cp "$PROJECT_ROOT/src/core/radio_manager.py" "$BACKUP_DIR/radio_manager.py.original"

    echo "✂️  Removing WiFi imports and dependencies from radio_manager.py"
    # Remove WiFi-related imports and code
    sed -i.bak '/from src\.core\.mode_manager/d' "$PROJECT_ROOT/src/core/radio_manager.py"
    sed -i.bak '/from src\.core\.wifi_manager/d' "$PROJECT_ROOT/src/core/radio_manager.py"
    sed -i.bak '/NetworkMode/d' "$PROJECT_ROOT/src/core/radio_manager.py"
    sed -i.bak '/self\._wifi_manager/d' "$PROJECT_ROOT/src/core/radio_manager.py"
    rm "$PROJECT_ROOT/src/core/radio_manager.py.bak"
fi

# Update main page to remove WiFi components
if [[ -f "$PROJECT_ROOT/web/src/routes/+page.svelte" ]]; then
    echo "🔄 Backing up main page"
    cp "$PROJECT_ROOT/web/src/routes/+page.svelte" "$BACKUP_DIR/page.svelte.original"

    echo "✂️  Removing WiFi components from main page"
    sed -i.bak '/import.*WiFiStatus\|import.*ModeControl/d' "$PROJECT_ROOT/web/src/routes/+page.svelte"
    sed -i.bak '/<WiFiStatus\|<ModeControl/d' "$PROJECT_ROOT/web/src/routes/+page.svelte"
    sed -i.bak '/currentMode/d' "$PROJECT_ROOT/web/src/routes/+page.svelte"
    rm "$PROJECT_ROOT/web/src/routes/+page.svelte.bak"
fi

echo ""
echo "🧽 CLEANING UP EMPTY DIRECTORIES"
echo "=================================="

# Remove empty directories
find "$PROJECT_ROOT" -type d -empty -delete 2>/dev/null || true

echo ""
echo "✅ CLEANUP COMPLETE!"
echo "===================="
echo "📊 Summary:"
echo "   - All WiFi-related files have been removed"
echo "   - Configuration files have been cleaned"
echo "   - Original files backed up to: $BACKUP_DIR"
echo ""
echo "🔍 Next steps:"
echo "   1. Review the cleaned project structure"
echo "   2. Test that core radio functionality still works"
echo "   3. Begin integration with new WiFi system"
echo ""
echo "💡 To restore WiFi files if needed:"
echo "   cp -r $BACKUP_DIR/* $PROJECT_ROOT/"
