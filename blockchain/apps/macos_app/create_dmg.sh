#!/bin/bash
# Script to create a simple DMG file for GlobalCoyn

echo "Creating GlobalCoyn DMG installer"

# Set variables
APP_NAME="GlobalCoyn"
TEMP_DIR="temp_build"
DMG_DIR="dist"

# Clean up and create directories
rm -rf "$TEMP_DIR" "$DMG_DIR" 2>/dev/null
mkdir -p "$TEMP_DIR"
mkdir -p "$DMG_DIR"

# Create a temporary Applications symbolic link
ln -s /Applications "$TEMP_DIR/Applications"

# Copy all necessary files to the build directory
mkdir -p "$TEMP_DIR/$APP_NAME"
cp app_wrapper.py "$TEMP_DIR/$APP_NAME/"
cp macos_app.py "$TEMP_DIR/$APP_NAME/"
cp simple_launcher.py "$TEMP_DIR/$APP_NAME/"
cp GlobalCoyn.command "$TEMP_DIR/$APP_NAME/"
chmod +x "$TEMP_DIR/$APP_NAME/GlobalCoyn.command"
mkdir -p "$TEMP_DIR/$APP_NAME/resources"
cp resources/macapplogo.png "$TEMP_DIR/$APP_NAME/resources/"

# Create a README file
cat > "$TEMP_DIR/README.txt" << 'EOF'
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

# Create DMG file
hdiutil create -volname "$APP_NAME" -srcfolder "$TEMP_DIR" -ov -format UDZO "$DMG_DIR/$APP_NAME.dmg"

# Clean up temp directory
rm -rf "$TEMP_DIR"

echo "Done! GlobalCoyn DMG has been created."
echo "DMG installer is available at $DMG_DIR/$APP_NAME.dmg"