#!/bin/bash
# Create a signed and notarized DMG for the GlobalCoyn macOS app
# This script handles DMG creation, code signing, and optionally notarization

# Exit on any error
set -e

# Load build variables
if [ -f "build_variables.sh" ]; then
    source build_variables.sh
else
    # Default variables if build_variables.sh doesn't exist
    APP_NAME="GlobalCoyn"
    APP_VERSION="1.0.0"
    APP_BUNDLE_ID="com.globalcoyn.app"
    APP_COPYRIGHT="© 2023-2025 GlobalCoyn Project"
    BUILD_DIR="$(pwd)/build"
    DIST_DIR="$(pwd)/dist"
    MACOS_APP_DIR="$(pwd)/blockchain/apps/macos_app"
    # By default, use an empty certificate ID which will skip signing
    DEVELOPER_ID=""
    NOTARIZATION_USERNAME=""
    NOTARIZATION_PASSWORD=""
fi

# Command line argument to force skipping code signing
SKIP_SIGNING=false
SKIP_NOTARIZATION=false
FORCE_NOTARIZATION=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-signing)
            SKIP_SIGNING=true
            ;;
        --skip-notarization)
            SKIP_NOTARIZATION=true
            ;;
        --force-notarization)
            FORCE_NOTARIZATION=true
            ;;
        --developer-id)
            DEVELOPER_ID="$2"
            shift
            ;;
        --notarization-username)
            NOTARIZATION_USERNAME="$2"
            shift
            ;;
        --notarization-password)
            NOTARIZATION_PASSWORD="$2"
            shift
            ;;
        --app-version)
            APP_VERSION="$2"
            shift
            ;;
        *)
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
    shift
done

# Function to print a header
print_header() {
    echo ""
    echo "============================================================"
    echo "  $1"
    echo "============================================================"
    echo ""
}

# Validate the app bundle exists
APP_BUNDLE="$DIST_DIR/$APP_NAME.app"
if [ ! -d "$APP_BUNDLE" ]; then
    echo "ERROR: App bundle not found at $APP_BUNDLE"
    echo "Please build the app first using PyInstaller"
    exit 1
fi

print_header "Creating signed DMG for $APP_NAME v$APP_VERSION"

# Check for create-dmg tool
if ! command -v create-dmg &> /dev/null; then
    echo "ERROR: create-dmg tool not found"
    echo "Please install it using brew: brew install create-dmg"
    exit 1
fi

# Create a temporary directory for DMG preparation
TEMP_DIR=$(mktemp -d)
DMG_ROOT="$TEMP_DIR/dmg_root"
mkdir -p "$DMG_ROOT"
echo "Created temporary directory: $TEMP_DIR"

# Create Applications symbolic link
ln -s /Applications "$DMG_ROOT/Applications"

# Copy app bundle to the DMG root
echo "Copying app bundle to DMG directory..."
cp -R "$APP_BUNDLE" "$DMG_ROOT/"

# Create a README file
cat > "$DMG_ROOT/README.txt" << EOF
GlobalCoyn Cryptocurrency Wallet v$APP_VERSION
========================================

Thank you for installing GlobalCoyn!

To install:
1. Drag the GlobalCoyn app to the Applications folder
2. Launch it from Applications

Your blockchain data and wallet will be stored in ~/Documents/GlobalCoyn/

For support, visit:
https://globalcoyn.com
EOF

# Code signing section (if applicable)
if [ "$SKIP_SIGNING" = false ] && [ -n "$DEVELOPER_ID" ] && [ "$DEVELOPER_ID" != "Developer ID Application: Your Company Name (XXXXXXXXXX)" ]; then
    print_header "Code signing app bundle"
    
    echo "Using Developer ID: $DEVELOPER_ID"
    
    # Sign the entire app bundle
    echo "Signing app bundle..."
    codesign --force --options runtime --deep --sign "$DEVELOPER_ID" "$DMG_ROOT/$APP_NAME.app"
    
    # Verify signature
    echo "Verifying signature..."
    codesign --verify --verbose "$DMG_ROOT/$APP_NAME.app"
    
    # Will create a signed DMG
    WILL_SIGN_DMG=true
else
    echo "Skipping code signing (no valid Developer ID provided or signing disabled)"
    WILL_SIGN_DMG=false
fi

# Create DMG file name
DMG_FILE="$DIST_DIR/${APP_NAME}-${APP_VERSION}.dmg"

# Delete existing DMG if it exists
if [ -f "$DMG_FILE" ]; then
    echo "Removing existing DMG file..."
    rm "$DMG_FILE"
fi

print_header "Creating DMG file"

# Create the DMG
create-dmg \
  --volname "$APP_NAME Installer" \
  --volicon "$DMG_ROOT/$APP_NAME.app/Contents/Resources/macapplogo.icns" \
  --window-pos 200 120 \
  --window-size 800 450 \
  --icon-size 100 \
  --icon "$APP_NAME.app" 200 190 \
  --hide-extension "$APP_NAME.app" \
  --app-drop-link 600 185 \
  --no-internet-enable \
  "$DMG_FILE" \
  "$DMG_ROOT"

echo "Created DMG file: $DMG_FILE"

# Sign the DMG if we have a Developer ID
if [ "$WILL_SIGN_DMG" = true ]; then
    print_header "Signing DMG file"
    codesign --force --sign "$DEVELOPER_ID" "$DMG_FILE"
    echo "DMG file signed"
fi

# Notarization section (if applicable)
if [ "$SKIP_NOTARIZATION" = false ] && [ "$WILL_SIGN_DMG" = true ] && \
   [ -n "$NOTARIZATION_USERNAME" ] && [ -n "$NOTARIZATION_PASSWORD" ] && \
   [ "$NOTARIZATION_USERNAME" != "your.email@example.com" ]; then
    
    print_header "Notarizing DMG file"
    
    echo "Submitting DMG for notarization..."
    xcrun altool --notarize-app \
        --primary-bundle-id "$APP_BUNDLE_ID" \
        --username "$NOTARIZATION_USERNAME" \
        --password "$NOTARIZATION_PASSWORD" \
        --file "$DMG_FILE"
    
    echo "Notarization submitted. This process may take several minutes."
    echo "Once complete, you can check the status using:"
    echo "xcrun altool --notarization-history 0 -u \"$NOTARIZATION_USERNAME\""
    
    echo "After notarization is approved, staple the ticket to the DMG using:"
    echo "xcrun stapler staple \"$DMG_FILE\""
elif [ "$FORCE_NOTARIZATION" = true ]; then
    print_header "Notarization not possible"
    echo "Notarization was requested, but is not possible because:"
    
    if [ "$WILL_SIGN_DMG" = false ]; then
        echo "- The DMG is not signed (code signing is required for notarization)"
    fi
    
    if [ -z "$NOTARIZATION_USERNAME" ] || [ "$NOTARIZATION_USERNAME" = "your.email@example.com" ]; then
        echo "- No valid notarization username provided"
    fi
    
    if [ -z "$NOTARIZATION_PASSWORD" ] || [ "$NOTARIZATION_PASSWORD" = "@keychain:AC_PASSWORD" ]; then
        echo "- No valid notarization password/keychain item provided"
    fi
else
    echo "Skipping notarization step"
fi

# Clean up
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

print_header "DMG Creation Complete"
echo "DMG file created at: $DMG_FILE"
echo "Size: $(du -h "$DMG_FILE" | cut -f1)"

if [ "$WILL_SIGN_DMG" = true ]; then
    echo "DMG is signed with Developer ID: $DEVELOPER_ID"
else
    echo "DMG is not signed - users may see security warnings when opening the app"
fi

exit 0