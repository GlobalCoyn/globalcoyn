#!/bin/bash
# GlobalCoyn macOS App Builder
# Creates a standalone macOS .app that connects to existing blockchain network

set -e  # Exit on any error

# Set up environment variables
BUILD_DIR="$(pwd)/build"
DIST_DIR="$(pwd)/dist"
APP_NAME="GlobalCoyn"
VERSION="2.0.1"
MACOS_APP_DIR="$(pwd)/blockchain/apps/macos_app"

echo "===== GlobalCoyn macOS App Builder ====="
echo "Building version: $VERSION"

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR/GlobalCoyn"
mkdir -p "$DIST_DIR"

# Verify source files exist
if [ ! -d "$MACOS_APP_DIR" ]; then
    echo "ERROR: macOS app source directory not found: $MACOS_APP_DIR"
    exit 1
fi

if [ ! -f "$MACOS_APP_DIR/macos_app.py" ]; then
    echo "ERROR: macos_app.py not found in source directory"
    exit 1
fi

# Copy all files from the macOS app directory
echo "Copying macOS app files..."
cp -r "$MACOS_APP_DIR"/* "$BUILD_DIR/GlobalCoyn/"

# Create Resources directory
mkdir -p "$BUILD_DIR/GlobalCoyn/Resources"

# Copy app icon if it exists
if [ -f "$MACOS_APP_DIR/resources/macapplogo.png" ]; then
    cp "$MACOS_APP_DIR/resources/macapplogo.png" "$BUILD_DIR/GlobalCoyn/Resources/"
    echo "Copied app logo from resources directory"
fi

# Create a bootstrap launcher script
echo "Creating bootstrap launcher script..."
cat > "$BUILD_DIR/GlobalCoyn/GlobalCoyn.command" << 'EOF'
#!/bin/bash
# GlobalCoyn Bootstrap Launcher
# This script checks for dependencies and launches the app

# Terminal colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Go to the app directory
cd "$(dirname "$0")" || exit
APP_DIR="$(pwd)"
echo -e "${GREEN}Starting GlobalCoyn application from: $APP_DIR${NC}"

# Create user data directory in ~/Documents
USER_DATA_DIR="$HOME/Documents/GlobalCoyn"
mkdir -p "$USER_DATA_DIR"
echo "Using data directory: $USER_DATA_DIR"

# Check for Python
echo "Checking Python installation..."
PYTHON_FOUND=false
PYTHON_CMD=""

# Try Python commands in order of preference
for cmd in python3 python "python3.9" "python3.10" "python3.11" "/usr/local/bin/python3" "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"; do
    if command_exists "$cmd"; then
        VERSION=$($cmd --version 2>&1)
        if [[ $VERSION == *"Python 3"* ]]; then
            PYTHON_CMD="$cmd"
            PYTHON_FOUND=true
            echo -e "${GREEN}Found Python: $VERSION at $PYTHON_CMD${NC}"
            break
        fi
    fi
done

# If Python not found, show error and exit
if [ "$PYTHON_FOUND" = false ]; then
    echo -e "${RED}Error: Python 3 not found${NC}"
    echo "GlobalCoyn requires Python 3.7 or higher."
    
    # Ask user if they want to install Python
    echo -e "${YELLOW}Would you like to install Python? (y/n)${NC}"
    read -r install_python
    
    if [[ $install_python == "y" || $install_python == "Y" ]]; then
        echo "Installing Python..."
        
        # Download Python installer
        if [ ! -f "python3-installer.pkg" ]; then
            echo "Downloading Python installer..."
            curl -O https://www.python.org/ftp/python/3.11.4/python-3.11.4-macos11.pkg
            mv python-3.11.4-macos11.pkg python3-installer.pkg
        fi
        
        # Install Python
        echo "Running Python installer..."
        open python3-installer.pkg
        
        echo "Please follow the Python installer instructions."
        echo "After installation is complete, please run GlobalCoyn again."
        read -p "Press Enter to close this window..." x
        exit 1
    else
        echo "Python is required to run GlobalCoyn."
        read -p "Press Enter to close this window..." x
        exit 1
    fi
fi

# Check for pip
if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
    echo -e "${YELLOW}Installing pip...${NC}"
    
    # Try to install pip
    if [ -f "$APP_DIR/get-pip.py" ]; then
        echo "Using bundled get-pip.py"
        $PYTHON_CMD "$APP_DIR/get-pip.py" --user
    else
        echo "Downloading get-pip.py..."
        curl -O https://bootstrap.pypa.io/get-pip.py
        $PYTHON_CMD get-pip.py --user
        rm get-pip.py
    fi
fi

# Install required packages
echo "Checking and installing required packages..."
# Function to check if a Python package is installed
package_installed() {
    $PYTHON_CMD -c "import $1" >/dev/null 2>&1
}

# Install packages if needed
for package in requests psutil flask; do
    if ! package_installed "$package"; then
        echo -e "${YELLOW}Installing $package...${NC}"
        $PYTHON_CMD -m pip install "$package" --user
    fi
done

# Copy necessary files to data directory if they don't exist
if [ ! -f "$USER_DATA_DIR/node_config.json" ]; then
    echo "Creating node configuration..."
    cat > "$USER_DATA_DIR/node_config.json" << CONFIGEOF
{
    "node_number": 3,
    "p2p_port": 9002,
    "web_port": 8003,
    "data_directory": "$USER_DATA_DIR",
    "production_mode": false,
    "bootstrap_nodes": [
        {
            "host": "13.61.79.186",
            "port": 8100
        },
        {
            "host": "13.61.79.186",
            "port": 8101
        }
    ]
}
CONFIGEOF
fi

# Make sure working_node.sh is executable if it exists
if [ -f "$APP_DIR/working_node.sh" ]; then
    chmod +x "$APP_DIR/working_node.sh"
fi

# Add app directory to Python path and run the app
echo -e "${GREEN}Launching GlobalCoyn application...${NC}"
export PYTHONPATH="$APP_DIR:$PYTHONPATH"
$PYTHON_CMD "$APP_DIR/app_wrapper.py"

# Check if app started successfully
if [ $? -ne 0 ]; then
    echo -e "${RED}Error running the application. See error details above.${NC}"
    read -p "Press Enter to close this window..." x
    exit 1
fi
EOF

# Make the bootstrap launcher executable
chmod +x "$BUILD_DIR/GlobalCoyn/GlobalCoyn.command"

# Create get-pip.py if it doesn't exist
if [ ! -f "$MACOS_APP_DIR/get-pip.py" ]; then
    echo "Downloading get-pip.py..."
    curl -o "$BUILD_DIR/GlobalCoyn/get-pip.py" https://bootstrap.pypa.io/get-pip.py
fi

# Create .app structure 
echo "Creating .app bundle..."
APP_BUNDLE_DIR="$DIST_DIR/$APP_NAME.app"
mkdir -p "$APP_BUNDLE_DIR/Contents/MacOS"
mkdir -p "$APP_BUNDLE_DIR/Contents/Resources"

# Copy files to app bundle
cp -r "$BUILD_DIR/GlobalCoyn"/* "$APP_BUNDLE_DIR/Contents/Resources/"

# Create launcher script
cat > "$APP_BUNDLE_DIR/Contents/MacOS/GlobalCoyn" << 'EOF'
#!/bin/bash
# App bundle launcher

# Get the bundle path
BUNDLE_PATH=$(dirname "$(dirname "$(dirname "$0")")")
RESOURCES_PATH="$BUNDLE_PATH/Contents/Resources"

# Change to resources directory and launch the application
cd "$RESOURCES_PATH" || exit 1
bash "./GlobalCoyn.command"
EOF

chmod +x "$APP_BUNDLE_DIR/Contents/MacOS/GlobalCoyn"

# Create Info.plist
cat > "$APP_BUNDLE_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>GlobalCoyn</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.globalcoyn.wallet</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>GlobalCoyn</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleVersion</key>
    <string>${VERSION}</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2025 GlobalCoyn. All rights reserved.</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create app icon if available
if [ -f "$BUILD_DIR/GlobalCoyn/Resources/macapplogo.png" ]; then
    echo "Creating app icon from macapplogo.png..."
    
    # Create iconset directory
    ICONSET_DIR="$BUILD_DIR/AppIcon.iconset"
    mkdir -p "$ICONSET_DIR"
    
    # Generate different icon sizes
    sips -z 16 16 "$BUILD_DIR/GlobalCoyn/Resources/macapplogo.png" --out "$ICONSET_DIR/icon_16x16.png" >/dev/null 2>&1 || true
    sips -z 32 32 "$BUILD_DIR/GlobalCoyn/Resources/macapplogo.png" --out "$ICONSET_DIR/icon_32x32.png" >/dev/null 2>&1 || true
    sips -z 128 128 "$BUILD_DIR/GlobalCoyn/Resources/macapplogo.png" --out "$ICONSET_DIR/icon_128x128.png" >/dev/null 2>&1 || true
    sips -z 256 256 "$BUILD_DIR/GlobalCoyn/Resources/macapplogo.png" --out "$ICONSET_DIR/icon_256x256.png" >/dev/null 2>&1 || true
    sips -z 512 512 "$BUILD_DIR/GlobalCoyn/Resources/macapplogo.png" --out "$ICONSET_DIR/icon_512x512.png" >/dev/null 2>&1 || true
    
    # Create high-resolution versions
    cp "$ICONSET_DIR/icon_16x16.png" "$ICONSET_DIR/icon_16x16@2x.png" || true
    cp "$ICONSET_DIR/icon_32x32.png" "$ICONSET_DIR/icon_32x32@2x.png" || true
    cp "$ICONSET_DIR/icon_128x128.png" "$ICONSET_DIR/icon_128x128@2x.png" || true
    cp "$ICONSET_DIR/icon_256x256.png" "$ICONSET_DIR/icon_256x256@2x.png" || true
    
    # Convert to .icns
    if command -v iconutil >/dev/null 2>&1; then
        iconutil -c icns "$ICONSET_DIR" -o "$APP_BUNDLE_DIR/Contents/Resources/AppIcon.icns"
        echo "Created app icon: AppIcon.icns"
    else
        echo "WARNING: iconutil not found. App icon will not be created."
    fi
fi

# Create a symbolic link to Applications folder for easy installation
echo "Creating symbolic link to Applications folder..."
ln -sf /Applications "$DIST_DIR/Applications"

# Create a README file
cat > "$DIST_DIR/README.txt" << EOF
GlobalCoyn Wallet v${VERSION}
===========================

Installation Instructions:
-------------------------
1. Drag the GlobalCoyn app to the Applications folder
2. Open the app from your Applications folder

Your blockchain data will be stored in ~/Documents/GlobalCoyn/

Troubleshooting:
--------------
- If you see a warning about the app being from an unidentified developer,
  right-click (or Control-click) the app icon and select "Open"
- If you encounter any issues, please check the log file at:
  ~/Documents/GlobalCoyn/globalcoyn.log

For support, visit: https://globalcoyn.com/support
EOF

# Create a DMG file (optional)
if command -v hdiutil >/dev/null 2>&1; then
    echo "Creating DMG file..."
    hdiutil create -volname "GlobalCoyn $VERSION" -srcfolder "$DIST_DIR" -ov -format UDZO "$DIST_DIR/$APP_NAME-$VERSION.dmg"
    echo "Created DMG file: $DIST_DIR/$APP_NAME-$VERSION.dmg"
else
    echo "WARNING: hdiutil not found. DMG file will not be created."
    
    # Create a zip file instead
    echo "Creating ZIP archive..."
    cd "$DIST_DIR"
    zip -r "$APP_NAME-$VERSION.zip" "$APP_NAME.app" "README.txt" "Applications"
    echo "Created ZIP archive: $DIST_DIR/$APP_NAME-$VERSION.zip"
fi

echo "===== Build Complete ====="
echo "App bundle: $DIST_DIR/$APP_NAME.app"

if [ -f "$DIST_DIR/$APP_NAME-$VERSION.dmg" ]; then
    echo "DMG file: $DIST_DIR/$APP_NAME-$VERSION.dmg"
elif [ -f "$DIST_DIR/$APP_NAME-$VERSION.zip" ]; then
    echo "ZIP archive: $DIST_DIR/$APP_NAME-$VERSION.zip"
fi

echo ""
echo "To use the app:"
echo "1. Drag GlobalCoyn.app to your Applications folder"
echo "2. Launch the app from Applications"