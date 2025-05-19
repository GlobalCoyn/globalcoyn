#!/bin/bash
# Script to fix the macOS DMG creation issue
# This script creates a more reliable DMG file for GlobalCoyn

# Set variables
APP_NAME="GlobalCoyn"
SRC_DIR="blockchain/apps/macos_app"
DIST_DIR="blockchain/website/downloads"
TEMP_DMG="tmp_${APP_NAME}.dmg"
FINAL_DMG="${APP_NAME}-macos.dmg"
VOLUME_NAME="${APP_NAME} Installer"
TEMP_BUILD="tmp_build"

echo "Creating fixed GlobalCoyn macOS DMG installer..."

# Clean up previous builds
rm -rf "$TEMP_BUILD" 2>/dev/null
mkdir -p "$TEMP_BUILD"
mkdir -p "$DIST_DIR"

# Copy all necessary files to the build directory
echo "Copying application files..."
mkdir -p "$TEMP_BUILD/$APP_NAME"
cp "$SRC_DIR/app_wrapper.py" "$TEMP_BUILD/$APP_NAME/"
cp "$SRC_DIR/macos_app.py" "$TEMP_BUILD/$APP_NAME/"
cp "$SRC_DIR/simple_launcher.py" "$TEMP_BUILD/$APP_NAME/"
cp "$SRC_DIR/GlobalCoyn.command" "$TEMP_BUILD/$APP_NAME/"
chmod +x "$TEMP_BUILD/$APP_NAME/GlobalCoyn.command"
mkdir -p "$TEMP_BUILD/$APP_NAME/resources"
cp "$SRC_DIR/resources/macapplogo.png" "$TEMP_BUILD/$APP_NAME/resources/"

# Create a README file
cat > "$TEMP_BUILD/README.txt" << 'EOF'
GlobalCoyn Cryptocurrency Wallet

Installation Instructions:
1. Drag the GlobalCoyn folder to your Applications folder
2. Open the GlobalCoyn folder in Applications
3. Double-click GlobalCoyn.command to start the application

Requirements:
- Python 3.8 or higher
- PyQt5 (will be installed automatically if not present)

For more information, visit globalcoyn.com
EOF

# Create symbolic link to Applications
ln -s /Applications "$TEMP_BUILD/Applications"

# Create a more reliable DMG using a fixed size
echo "Creating fixed-size DMG..."
hdiutil create -size 100m -fs HFS+ -volname "$VOLUME_NAME" "$TEMP_DMG"

# Mount the DMG
echo "Mounting DMG..."
MOUNT_POINT=$(hdiutil attach "$TEMP_DMG" | grep "$VOLUME_NAME" | cut -f 3)
if [ -z "$MOUNT_POINT" ]; then
  echo "Error: Failed to mount the DMG"
  exit 1
fi

echo "DMG mounted at: $MOUNT_POINT"

# Copy files to the mounted DMG
echo "Copying files to DMG..."
cp -R "$TEMP_BUILD"/* "$MOUNT_POINT"

# Wait for files to be written
sleep 2

# Unmount the DMG
echo "Unmounting DMG..."
hdiutil detach "$MOUNT_POINT" -force

# Convert to compressed format
echo "Converting DMG to compressed format..."
hdiutil convert "$TEMP_DMG" -format UDZO -o "$DIST_DIR/$FINAL_DMG"

# Clean up
rm -f "$TEMP_DMG"
rm -rf "$TEMP_BUILD"

echo "Done! Fixed GlobalCoyn DMG has been created."
echo "DMG installer is available at $DIST_DIR/$FINAL_DMG"

# Copy to website downloads folder
echo "Updating website downloads..."
cp "$DIST_DIR/$FINAL_DMG" "blockchain/website/downloads/globalcoyn-macos.dmg"

echo "DMG fix complete! You can now deploy the fixed DMG to the server."