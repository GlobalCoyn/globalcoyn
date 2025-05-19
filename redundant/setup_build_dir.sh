#!/bin/bash
# setup_build_dir.sh
# Script to set up the build directory for the GlobalCoyn macOS app

# Set variables
APP_NAME="GlobalCoyn"
BUILD_DIR="$(pwd)/build"
DIST_DIR="$(pwd)/dist"
MACOS_APP_DIR="$(pwd)/blockchain/apps/macos_app"
VERSION="1.0.0"

echo "Setting up GlobalCoyn macOS App build environment..."

# Clean previous builds
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR/GlobalCoyn"
mkdir -p "$DIST_DIR"

# Create core directories
mkdir -p "$BUILD_DIR/GlobalCoyn/core"
mkdir -p "$BUILD_DIR/GlobalCoyn/network"
mkdir -p "$BUILD_DIR/GlobalCoyn/resources"
mkdir -p "$BUILD_DIR/GlobalCoyn/optimized"
mkdir -p "$BUILD_DIR/GlobalCoyn/docs"

# Copy main application files
echo "Copying application files..."
cp "$MACOS_APP_DIR/app_wrapper.py" "$BUILD_DIR/GlobalCoyn/"
cp "$MACOS_APP_DIR/macos_app.py" "$BUILD_DIR/GlobalCoyn/"
cp "$MACOS_APP_DIR/node_discovery.py" "$BUILD_DIR/GlobalCoyn/"
cp "$MACOS_APP_DIR/node_manager.py" "$BUILD_DIR/GlobalCoyn/"
cp "$MACOS_APP_DIR/config_manager.py" "$BUILD_DIR/GlobalCoyn/"
cp "$MACOS_APP_DIR/working_node.sh" "$BUILD_DIR/GlobalCoyn/"
chmod +x "$BUILD_DIR/GlobalCoyn/working_node.sh"

# Copy resources
echo "Copying resources..."
cp -r "$MACOS_APP_DIR/resources"/* "$BUILD_DIR/GlobalCoyn/resources/"

# Copy optimized modules
echo "Copying optimized modules..."
cp -r "$MACOS_APP_DIR/optimized"/* "$BUILD_DIR/GlobalCoyn/optimized/"

# Create core/__init__.py
touch "$BUILD_DIR/GlobalCoyn/core/__init__.py"
touch "$BUILD_DIR/GlobalCoyn/network/__init__.py"
touch "$BUILD_DIR/GlobalCoyn/optimized/__init__.py"

# Copy core modules if they exist in various locations
CORE_LOCATIONS=(
    "$MACOS_APP_DIR/../core"
    "$(pwd)/blockchain/core"
    "$(pwd)/blockchain/nodes/node1/core"
)

CORE_FILES=("blockchain.py" "coin.py" "wallet.py" "price_oracle.py")
FOUND_CORE=false

for CORE_PATH in "${CORE_LOCATIONS[@]}"; do
    if [[ -d "$CORE_PATH" ]]; then
        echo "Found core modules at $CORE_PATH"
        
        # Copy core files
        for FILE in "${CORE_FILES[@]}"; do
            if [[ -f "$CORE_PATH/$FILE" ]]; then
                echo "Copying $FILE to core directory"
                cp "$CORE_PATH/$FILE" "$BUILD_DIR/GlobalCoyn/core/"
            fi
        done
        
        FOUND_CORE=true
        break
    fi
done

if [[ "$FOUND_CORE" == "false" ]]; then
    echo "WARNING: Could not find core modules, app may not function correctly"
fi

# Look for network modules
NETWORK_LOCATIONS=(
    "$(pwd)/blockchain/network"
    "$(pwd)/blockchain/nodes/node1/network"
)

NETWORK_FILES=("improved_node_sync.py")

for NETWORK_PATH in "${NETWORK_LOCATIONS[@]}"; do
    if [[ -d "$NETWORK_PATH" ]]; then
        echo "Found network modules at $NETWORK_PATH"
        
        # Copy network files
        for FILE in "${NETWORK_FILES[@]}"; do
            if [[ -f "$NETWORK_PATH/$FILE" ]]; then
                echo "Copying $FILE to network directory"
                cp "$NETWORK_PATH/$FILE" "$BUILD_DIR/GlobalCoyn/network/"
            fi
        done
        
        break
    fi
done

# Create an improved launcher script
cat > "$BUILD_DIR/GlobalCoyn/GlobalCoyn.command" << 'EOF'
#!/bin/bash
# GlobalCoyn Launcher Script
# This script is designed to launch the GlobalCoyn application with proper error handling

# Set the application directory to the script's location
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$APP_DIR"

# Create log directory if it doesn't exist
LOG_DIR="$HOME/Library/Logs/GlobalCoyn"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app_launcher.log"

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    log "ERROR: $1"
    echo "----------------------------------------"
    echo "ERROR: $1"
    echo "----------------------------------------"
    echo "Please see the log file at: $LOG_FILE"
    echo "Press any key to exit..."
    read -n 1
    exit 1
}

# Log start of launcher
log "Starting GlobalCoyn launcher script"

# Check Python installation
log "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    handle_error "Python 3 is not installed. Please install Python 3 from python.org"
fi

# Report Python version
PYTHON_VERSION=$(python3 --version)
log "Found $PYTHON_VERSION"

# Check for required Python modules and install if missing
REQUIRED_MODULES=("requests" "psutil" "PyQt5")
MISSING_MODULES=()

for MODULE in "${REQUIRED_MODULES[@]}"; do
    log "Checking for Python module: $MODULE"
    if ! python3 -c "import $MODULE" &> /dev/null; then
        log "Module $MODULE is missing, will try to install"
        MISSING_MODULES+=("$MODULE")
    fi
done

# Install missing modules if any
if [ ${#MISSING_MODULES[@]} -gt 0 ]; then
    log "Installing missing modules: ${MISSING_MODULES[*]}"
    echo "Installing required Python modules..."
    
    # Use get-pip.py if pip is not available
    if ! command -v pip3 &> /dev/null; then
        log "pip3 not found, trying to install using get-pip.py"
        if [ -f "$APP_DIR/get-pip.py" ]; then
            python3 "$APP_DIR/get-pip.py" --user
            export PATH="$HOME/Library/Python/3.*/bin:$PATH"
        else
            handle_error "pip3 is not installed and get-pip.py is missing"
        fi
    fi
    
    # Install each missing module
    for MODULE in "${MISSING_MODULES[@]}"; do
        log "Installing $MODULE"
        pip3 install --user "$MODULE" || handle_error "Failed to install $MODULE"
    done
    
    log "All required modules installed successfully"
fi

# Verify core application files exist
REQUIRED_FILES=("app_wrapper.py" "macos_app.py" "working_node.sh")
for FILE in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$APP_DIR/$FILE" ]; then
        handle_error "Required file $FILE is missing"
    fi
done

# Check for core module files
CORE_FILES=("core/blockchain.py" "core/coin.py" "core/wallet.py")
MISSING_CORE=false
for FILE in "${CORE_FILES[@]}"; do
    if [ ! -f "$APP_DIR/$FILE" ]; then
        log "WARNING: Core file $FILE is missing"
        MISSING_CORE=true
    fi
done

if [ "$MISSING_CORE" = true ]; then
    log "Some core files are missing, application may not function correctly"
    echo "WARNING: Some core files are missing. The application may not function correctly."
    echo "Continue anyway? (y/n)"
    read -n 1 CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        handle_error "Aborted due to missing files"
    fi
fi

# Set up data directory
DATA_DIR="$HOME/Documents/GlobalCoyn"
mkdir -p "$DATA_DIR"
log "Set up data directory at $DATA_DIR"

# Make sure node scripts are executable
chmod +x "$APP_DIR/working_node.sh"

# Launch the application
log "Launching GlobalCoyn application..."
echo "Starting GlobalCoyn application..."
cd "$APP_DIR"
python3 app_wrapper.py 2>&1 | tee -a "$LOG_FILE"

# Check exit code
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    handle_error "Application exited with code $EXIT_CODE"
else
    log "Application exited normally"
fi

exit 0
EOF

# Make the launcher script executable
chmod +x "$BUILD_DIR/GlobalCoyn/GlobalCoyn.command"

# Create a README file
cat > "$BUILD_DIR/GlobalCoyn/README.txt" << EOF
GlobalCoyn Cryptocurrency Wallet v$VERSION
========================================

Thank you for installing GlobalCoyn!

To start the application:
1. Double-click the GlobalCoyn.command file
2. Or, drag the GlobalCoyn.app to your Applications folder and launch it from there

Your blockchain data and wallet will be stored in ~/Documents/GlobalCoyn/

If you encounter any issues, please check the log files at:
~/Library/Logs/GlobalCoyn/

For more information, visit:
https://globalcoyn.com
EOF

# Create a simple data directory setup script
cat > "$BUILD_DIR/GlobalCoyn/setup_data_dir.command" << 'EOF'
#!/bin/bash
# Set up the GlobalCoyn data directory

DATA_DIR="$HOME/Documents/GlobalCoyn"
mkdir -p "$DATA_DIR"
echo "Created GlobalCoyn data directory at: $DATA_DIR"
echo "This is where your blockchain data and wallet will be stored."
echo ""
echo "Press any key to exit..."
read -n1
EOF
chmod +x "$BUILD_DIR/GlobalCoyn/setup_data_dir.command"

echo "Build directory setup complete at: $BUILD_DIR/GlobalCoyn"