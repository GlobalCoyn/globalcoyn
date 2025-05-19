#!/bin/bash
# test_app_build.sh
# Test script for validating the GlobalCoyn macOS app build

# Exit on error
set -e

# Set variables
APP_NAME="GlobalCoyn"
DIST_DIR="$(pwd)/dist"
APP_BUNDLE="$DIST_DIR/$APP_NAME.app"
DMG_FILE="$DIST_DIR/$APP_NAME.dmg"
TEST_DIR="$(pwd)/test_output"
LOG_FILE="$TEST_DIR/test_results.log"

# Create test directory
mkdir -p "$TEST_DIR"

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function for section headers
header() {
    log ""
    log "===================================================="
    log "  $1"
    log "===================================================="
    log ""
}

# Function to check if a file exists
check_file() {
    if [ -f "$1" ]; then
        log "✓ File exists: $1"
        return 0
    else
        log "✗ File missing: $1"
        return 1
    fi
}

# Function to check if a directory exists
check_dir() {
    if [ -d "$1" ]; then
        log "✓ Directory exists: $1"
        return 0
    else
        log "✗ Directory missing: $1"
        return 1
    fi
}

# Start testing
header "Starting GlobalCoyn App Build Tests"
log "Test timestamp: $(date)"

# Check app bundle existence
header "Checking App Bundle"
if check_dir "$APP_BUNDLE"; then
    log "App bundle found at: $APP_BUNDLE"
else
    log "ERROR: App bundle not found, build may have failed"
    exit 1
fi

# Check DMG file existence
header "Checking DMG File"
if check_file "$DMG_FILE"; then
    log "DMG file found at: $DMG_FILE"
    log "DMG file size: $(du -h "$DMG_FILE" | cut -f1)"
else
    log "WARNING: DMG file not found, DMG creation may have failed"
fi

# Verify app bundle structure
header "Verifying App Bundle Structure"
check_dir "$APP_BUNDLE/Contents"
check_dir "$APP_BUNDLE/Contents/MacOS"
check_dir "$APP_BUNDLE/Contents/Resources"
check_file "$APP_BUNDLE/Contents/Info.plist"
check_file "$APP_BUNDLE/Contents/MacOS/$APP_NAME"

# Verify key resources
header "Verifying Key Resources"
check_dir "$APP_BUNDLE/Contents/Resources/core"
check_dir "$APP_BUNDLE/Contents/Resources/network"
check_dir "$APP_BUNDLE/Contents/Resources/resources"
check_file "$APP_BUNDLE/Contents/Resources/working_node.sh"
check_file "$APP_BUNDLE/Contents/Resources/GlobalCoyn.command"

# Check permissions
header "Checking File Permissions"
if [ -x "$APP_BUNDLE/Contents/MacOS/$APP_NAME" ]; then
    log "✓ App executable has proper permissions"
else
    log "✗ App executable is not executable"
fi

# Check if app is signed
header "Checking Code Signature"
if codesign -v "$APP_BUNDLE" 2>/dev/null; then
    log "✓ App is signed"
    codesign -dv --verbose=2 "$APP_BUNDLE" >> "$LOG_FILE" 2>&1
    log "Signature details added to log file"
else
    log "✗ App is not signed"
fi

# Test app launching (without actually running it)
header "Testing App Launch Capability"
if [ -x "$APP_BUNDLE/Contents/MacOS/$APP_NAME" ]; then
    log "✓ App executable can be launched"
    # Check if app has necessary library dependencies
    if otool -L "$APP_BUNDLE/Contents/MacOS/$APP_NAME" > "$TEST_DIR/lib_dependencies.txt" 2>&1; then
        log "✓ Library dependencies look good"
        log "Library dependencies saved to test_output/lib_dependencies.txt"
    else
        log "✗ Could not check library dependencies"
    fi
else
    log "✗ App executable cannot be launched"
fi

# Copy source files for comparison
header "Copying Key Source Files for Reference"
mkdir -p "$TEST_DIR/source_backup"
if [ -f "improved_app_wrapper.py" ]; then
    cp improved_app_wrapper.py "$TEST_DIR/source_backup/"
    log "✓ Copied improved_app_wrapper.py to test_output/source_backup/"
fi

if [ -f "enhanced_node_script.sh" ]; then
    cp enhanced_node_script.sh "$TEST_DIR/source_backup/"
    log "✓ Copied enhanced_node_script.sh to test_output/source_backup/"
fi

if [ -f "dependency_installer.py" ]; then
    cp dependency_installer.py "$TEST_DIR/source_backup/"
    log "✓ Copied dependency_installer.py to test_output/source_backup/"
fi

# Save build config for reference
header "Saving Build Configuration"
if [ -f "GlobalCoyn.spec" ]; then
    cp GlobalCoyn.spec "$TEST_DIR/source_backup/"
    log "✓ Copied PyInstaller spec file to test_output/source_backup/"
fi

if [ -f "build_variables.sh" ]; then
    cp build_variables.sh "$TEST_DIR/source_backup/"
    log "✓ Copied build variables to test_output/source_backup/"
fi

# Final summary
header "Test Summary"
log "App bundle verification completed"
log "Test results saved to: $LOG_FILE"
log "Test output directory: $TEST_DIR"

if [ -f "$DMG_FILE" ]; then
    log "DMG file is ready for distribution at: $DMG_FILE"
else
    log "WARNING: No DMG file found for distribution"
fi

log "Test completed at: $(date)"

# Print final message
echo ""
echo "Test completed! Results are saved to $LOG_FILE"
echo ""

exit 0