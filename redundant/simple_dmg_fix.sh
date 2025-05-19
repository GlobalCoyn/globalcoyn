#!/bin/bash
# Script to create a simple but reliable DMG file for GlobalCoyn
# This script uses macOS-specific tools for maximum compatibility

# Set variables
APP_NAME="GlobalCoyn"
SRC_DIR="blockchain/apps/macos_app"
DIST_DIR="blockchain/website/downloads"
DMG_NAME="globalcoyn-macos.dmg"
TEMP_DIR="/tmp/globalcoyn_build"
SIZE="50m"  # Much smaller size to avoid corruption

echo "Creating a simple, reliable GlobalCoyn DMG installer..."

# Clean up any previous builds
rm -rf "$TEMP_DIR" 2>/dev/null
mkdir -p "$TEMP_DIR"
mkdir -p "$DIST_DIR"

# Prepare a simple folder structure
echo "Preparing app folder structure..."
mkdir -p "$TEMP_DIR/$APP_NAME"

# Copy only essential files
echo "Copying essential files..."
cp "$SRC_DIR/GlobalCoyn.command" "$TEMP_DIR/$APP_NAME/"
chmod +x "$TEMP_DIR/$APP_NAME/GlobalCoyn.command"
cp "$SRC_DIR/app_wrapper.py" "$TEMP_DIR/$APP_NAME/"
cp "$SRC_DIR/simple_launcher.py" "$TEMP_DIR/$APP_NAME/"
cp "$SRC_DIR/macos_app.py" "$TEMP_DIR/$APP_NAME/"
mkdir -p "$TEMP_DIR/$APP_NAME/resources"
cp "$SRC_DIR/resources/macapplogo.png" "$TEMP_DIR/$APP_NAME/resources/"

# Create a simple README file
cat > "$TEMP_DIR/README.txt" << 'EOF'
GlobalCoyn Cryptocurrency Wallet

Installation:
1. Drag the GlobalCoyn folder to your Applications folder
2. Double-click GlobalCoyn.command to start the application

For support: support@globalcoyn.com
EOF

# Create a symbolic link to Applications
ln -s /Applications "$TEMP_DIR/Applications"

# Create a very simple DMG using a reliable approach
echo "Creating DMG with simplified approach..."
hdiutil create -volname "GlobalCoyn" -srcfolder "$TEMP_DIR" -ov -format UDZO "$DIST_DIR/$DMG_NAME"

echo "Done! Simple GlobalCoyn DMG created at $DIST_DIR/$DMG_NAME"
echo "Size: $(du -h "$DIST_DIR/$DMG_NAME" | cut -f1)"

# Testing the DMG to verify it works
echo "Testing the DMG to verify it's not corrupted..."
hdiutil verify "$DIST_DIR/$DMG_NAME"
if [ $? -eq 0 ]; then
  echo "DMG verification passed - DMG is not corrupted"
else
  echo "DMG verification failed - DMG may be corrupted"
  exit 1
fi

echo "DMG creation completed successfully."