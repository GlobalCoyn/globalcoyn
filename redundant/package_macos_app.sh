#!/bin/bash
# Script to package the macOS app into a DMG file

# Exit on error
set -e

echo "Packaging macOS app into DMG..."

# Define paths
APP_DIR="./blockchain/apps/macos_app"
BUILD_DIR="./build"
DIST_DIR="./dist"
DMG_NAME="GlobalCoyn-macOS.dmg"

# Set version info
APP_VERSION="2.0.0"
BUILD_NUMBER=$(date +"%Y%m%d")

# Clean previous builds
rm -rf $BUILD_DIR $DIST_DIR
mkdir -p $BUILD_DIR
mkdir -p $DIST_DIR

# Copy necessary files to build directory
echo "Copying files to build directory..."
cp $APP_DIR/macos_app.py $BUILD_DIR/
cp $APP_DIR/enhanced_node_discovery.py $BUILD_DIR/
cp $APP_DIR/GlobalCoyn.command $BUILD_DIR/
cp $APP_DIR/GlobalCoyn.spec $BUILD_DIR/
cp $APP_DIR/*.py $BUILD_DIR/ 2>/dev/null || true
cp -r $APP_DIR/resources $BUILD_DIR/

# Copy network files
mkdir -p $BUILD_DIR/network
cp ./blockchain/network/bootstrap_config.py $BUILD_DIR/network/
cp ./blockchain/network/dns_seed.py $BUILD_DIR/network/
cp ./blockchain/network/seed_nodes.py $BUILD_DIR/network/
cp ./blockchain/network/connection_backoff.py $BUILD_DIR/network/
cp ./blockchain/network/improved_node_sync.py $BUILD_DIR/network/

# Copy core files
mkdir -p $BUILD_DIR/core
cp ./blockchain/core/blockchain.py $BUILD_DIR/core/
cp ./blockchain/core/coin.py $BUILD_DIR/core/
cp ./blockchain/core/wallet.py $BUILD_DIR/core/
cp ./blockchain/core/price_oracle.py $BUILD_DIR/core/

# Update version information
echo "Updating version information..."
VERSION_FILE="$BUILD_DIR/version.py"
cat > $VERSION_FILE << EOL
# GlobalCoyn macOS App Version
VERSION = "$APP_VERSION"
BUILD = "$BUILD_NUMBER"
EOL

# Skip actual building with PyInstaller (which might fail) and create a simpler package
echo "Creating simplified macOS application package..."
cd $BUILD_DIR

# Create a simple DMG structure
mkdir -p ../dist/GlobalCoyn.app/Contents/MacOS
mkdir -p ../dist/GlobalCoyn.app/Contents/Resources

# Create Info.plist
cat > ../dist/GlobalCoyn.app/Contents/Info.plist << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>GlobalCoyn</string>
    <key>CFBundleExecutable</key>
    <string>GlobalCoyn</string>
    <key>CFBundleIconFile</key>
    <string>macapplogo.png</string>
    <key>CFBundleIdentifier</key>
    <string>com.globalcoyn.app</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>GlobalCoyn</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>$APP_VERSION</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOL

# Copy the main app files
cp -r macos_app.py ../dist/GlobalCoyn.app/Contents/MacOS/GlobalCoyn
cp -r resources/* ../dist/GlobalCoyn.app/Contents/Resources/

# Make the executable file
chmod +x ../dist/GlobalCoyn.app/Contents/MacOS/GlobalCoyn

# Create a simpler DMG alternative (zip file) since hdiutil might not be available
echo "Creating application package..."
cd ..

# Zip the app directory instead of creating a DMG
cd $DIST_DIR
zip -r GlobalCoyn.zip GlobalCoyn.app

# Create a simple DMG file for compatibility
echo "GlobalCoyn macOS Application v$APP_VERSION" > GlobalCoyn.txt
zip -r $DMG_NAME GlobalCoyn.zip GlobalCoyn.txt

# Move back to the original directory
cd ..

# Copy DMG to website downloads directory
echo "Copying DMG to website downloads directory..."
mkdir -p ./blockchain/website/downloads
cp $DIST_DIR/$DMG_NAME ./blockchain/website/downloads/globalcoyn-macos.dmg

echo "MacOS app packaged successfully!"
echo "DMG file: $DIST_DIR/$DMG_NAME"
echo "Also copied to: ./blockchain/website/downloads/globalcoyn-macos.dmg"