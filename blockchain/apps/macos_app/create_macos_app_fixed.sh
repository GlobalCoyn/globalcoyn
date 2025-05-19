#!/bin/bash
# Script to create a macOS app bundle for GlobalCoyn

echo "Creating GlobalCoyn macOS App Bundle"

# Set variables
APP_NAME="GlobalCoyn"
APP_DIR="$APP_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

# Create directory structure
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Copy Info.plist
cp info.plist "$CONTENTS_DIR/"

# Create the main executable script
cat > "$MACOS_DIR/GlobalCoyn" << 'EOF'
#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
python3 "$DIR/app_wrapper.py"
EOF

# Make it executable
chmod +x "$MACOS_DIR/GlobalCoyn"

# Copy the Python scripts
cp app_wrapper.py "$MACOS_DIR/"
cp macos_app.py "$MACOS_DIR/"
chmod +x "$MACOS_DIR/app_wrapper.py"
chmod +x "$MACOS_DIR/macos_app.py"

# Copy resources
mkdir -p "$RESOURCES_DIR/resources"
cp resources/macapplogo.png "$RESOURCES_DIR/resources/"
# Copy the icon for the app
cp resources/macapplogo.png "$RESOURCES_DIR/macapplogo.png"

# Create an icns file from the png for better macOS integration
echo "Creating icon file..."
mkdir -p "$CONTENTS_DIR/Resources/GlobalCoyn.iconset"
sips -z 16 16     resources/macapplogo.png --out "$CONTENTS_DIR/Resources/GlobalCoyn.iconset/icon_16x16.png"
sips -z 32 32     resources/macapplogo.png --out "$CONTENTS_DIR/Resources/GlobalCoyn.iconset/icon_16x16@2x.png"
sips -z 32 32     resources/macapplogo.png --out "$CONTENTS_DIR/Resources/GlobalCoyn.iconset/icon_32x32.png"
sips -z 64 64     resources/macapplogo.png --out "$CONTENTS_DIR/Resources/GlobalCoyn.iconset/icon_32x32@2x.png"
sips -z 128 128   resources/macapplogo.png --out "$CONTENTS_DIR/Resources/GlobalCoyn.iconset/icon_128x128.png"
sips -z 256 256   resources/macapplogo.png --out "$CONTENTS_DIR/Resources/GlobalCoyn.iconset/icon_128x128@2x.png"
sips -z 256 256   resources/macapplogo.png --out "$CONTENTS_DIR/Resources/GlobalCoyn.iconset/icon_256x256.png"
sips -z 512 512   resources/macapplogo.png --out "$CONTENTS_DIR/Resources/GlobalCoyn.iconset/icon_256x256@2x.png"
sips -z 512 512   resources/macapplogo.png --out "$CONTENTS_DIR/Resources/GlobalCoyn.iconset/icon_512x512.png"
sips -z 1024 1024 resources/macapplogo.png --out "$CONTENTS_DIR/Resources/GlobalCoyn.iconset/icon_512x512@2x.png"
iconutil -c icns "$CONTENTS_DIR/Resources/GlobalCoyn.iconset" -o "$CONTENTS_DIR/Resources/GlobalCoyn.icns"
rm -R "$CONTENTS_DIR/Resources/GlobalCoyn.iconset"

# Update Info.plist to use the icns file and executable
/usr/libexec/PlistBuddy -c "Set :CFBundleIconFile GlobalCoyn.icns" "$CONTENTS_DIR/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleExecutable GlobalCoyn" "$CONTENTS_DIR/Info.plist"

# Create an empty PkgInfo file (macOS convention)
echo "APPL????" > "$CONTENTS_DIR/PkgInfo"

echo "Creating install package..."
mkdir -p dist
# Create a DMG file
hdiutil create -volname "$APP_NAME" -srcfolder "$APP_DIR" -ov -format UDZO "dist/$APP_NAME.dmg"

echo "Done! GlobalCoyn.app has been created."
echo "DMG installer is available at dist/$APP_NAME.dmg"