#!/bin/bash
# setup_build_env.sh
# Script to set up the build environment for creating the GlobalCoyn macOS app

echo "Setting up build environment for GlobalCoyn macOS app"

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to install a Homebrew package if it doesn't exist
install_brew_package() {
    if ! command_exists "$1"; then
        echo "Installing $1..."
        brew install "$1" || return 1
    else
        echo "$1 is already installed"
    fi
    return 0
}

# Check for Homebrew and install if needed
if ! command_exists brew; then
    echo "Homebrew is not installed. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Add Homebrew to PATH if needed
    if [[ ":$PATH:" != *":/opt/homebrew/bin:"* ]] && [[ -d "/opt/homebrew/bin" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    echo "Homebrew is already installed"
fi

# Install required packages using Homebrew
echo "Installing required packages..."
install_brew_package create-dmg || echo "Failed to install create-dmg, DMG creation may fail"

# Check for Python 3
if ! command_exists python3; then
    echo "Python 3 is not installed. Installing..."
    brew install python3 || echo "Failed to install Python 3, please install manually"
else
    echo "Python 3 is already installed"
    python3 --version
fi

# Check for pip and install if needed
if ! command_exists pip3; then
    echo "pip3 is not installed. Installing..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
else
    echo "pip3 is already installed"
    pip3 --version
fi

# Install required Python packages
echo "Installing required Python packages..."
pip3 install --upgrade pip
pip3 install PyInstaller requests psutil PyQt5

# Download get-pip.py for inclusion in the app bundle (in case pip is missing on target systems)
echo "Downloading get-pip.py for inclusion in the app bundle..."
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

# Verify installation of PyInstaller
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "ERROR: PyInstaller module not accessible to Python"
    exit 1
else
    if command_exists pyinstaller; then
        echo "PyInstaller installed successfully and command is available"
        pyinstaller --version
    else
        echo "PyInstaller module is installed but command is not in PATH"
        echo "Will use 'python3 -m PyInstaller' instead of direct command"
    fi
fi

# Check for codesign capabilities
if command_exists codesign; then
    echo "codesign is available"
    echo "To sign your application, you will need an Apple Developer certificate"
    
    # Check if any signing identities are available
    SIGNING_IDENTITIES=$(security find-identity -v -p codesigning | grep -i "Developer ID Application")
    if [ -n "$SIGNING_IDENTITIES" ]; then
        echo "Available signing identities:"
        echo "$SIGNING_IDENTITIES"
    else
        echo "No Developer ID Application certificates found"
        echo "You may need to create one in your Apple Developer account"
    fi
else
    echo "codesign is not available, code signing will be skipped"
fi

# Create variables file for build scripts
cat > build_variables.sh << EOF
#!/bin/bash
# Build variables for GlobalCoyn macOS app

# Application settings
export APP_NAME="GlobalCoyn"
export APP_VERSION="1.0.0"
export APP_BUNDLE_ID="com.globalcoyn.app"
export APP_COPYRIGHT="© 2023-2025 GlobalCoyn Project"

# Build directories
export BUILD_DIR="\$(pwd)/build"
export DIST_DIR="\$(pwd)/dist"
export MACOS_APP_DIR="\$(pwd)/blockchain/apps/macos_app"

# Code signing settings
# Replace these with your actual Developer ID if you have one
export DEVELOPER_ID="Developer ID Application: Your Company Name (XXXXXXXXXX)"
export NOTARIZATION_USERNAME="your.email@example.com"
export NOTARIZATION_PASSWORD="@keychain:AC_PASSWORD"

# Bootstrap node settings
export BOOTSTRAP_NODE1="node1.globalcoyn.com:8001"
export BOOTSTRAP_NODE2="node2.globalcoyn.com:8001"
EOF

chmod +x build_variables.sh

echo "Build environment setup complete"
echo "You can now run setup_build_dir.sh to set up the build directory"