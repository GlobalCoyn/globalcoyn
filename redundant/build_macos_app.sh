#!/bin/bash
# build_macos_app.sh
# Master build script for GlobalCoyn macOS app
# Runs the entire build process from setup to testing

# Exit on error (but not for command parameter checking)
set -e

# Default settings
SKIP_ENV_SETUP=false
SKIP_SIGNING=false
SKIP_DMG=false
SKIP_TESTS=false
CLEAN_BUILD=true
DEVELOPER_ID=""
NOTARIZATION_USERNAME=""
NOTARIZATION_PASSWORD=""
APP_VERSION="1.0.0"
VERBOSE=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-env-setup)
            SKIP_ENV_SETUP=true
            ;;
        --skip-signing)
            SKIP_SIGNING=true
            ;;
        --skip-dmg)
            SKIP_DMG=true
            ;;
        --skip-tests)
            SKIP_TESTS=true
            ;;
        --no-clean)
            CLEAN_BUILD=false
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
        --verbose)
            VERBOSE=true
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --skip-env-setup           Skip environment setup step"
            echo "  --skip-signing             Skip code signing"
            echo "  --skip-dmg                 Skip DMG creation"
            echo "  --skip-tests               Skip build tests"
            echo "  --no-clean                 Don't clean previous build artifacts"
            echo "  --developer-id ID          Developer ID for code signing"
            echo "  --notarization-username U  Username for notarization"
            echo "  --notarization-password P  Password for notarization"
            echo "  --app-version VERSION      App version (default: 1.0.0)"
            echo "  --verbose                  Show verbose output"
            echo "  --help                     Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown parameter: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
    shift
done

# Function to print a section header
print_header() {
    echo ""
    echo "============================================================"
    echo "  $1"
    echo "============================================================"
    echo ""
}

# Function to print verbose output
log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo "$1"
    fi
}

# Start build process
print_header "Starting GlobalCoyn macOS App Build Process"
echo "Build started at: $(date)"
echo "App version: $APP_VERSION"

# Clean previous build artifacts if requested
if [ "$CLEAN_BUILD" = true ]; then
    print_header "Cleaning Previous Build Artifacts"
    log_verbose "Removing build/ and dist/ directories"
    rm -rf build dist
    echo "Build artifacts cleaned"
fi

# Set up build environment if requested
if [ "$SKIP_ENV_SETUP" = false ]; then
    print_header "Setting Up Build Environment"
    
    # Check if setup_build_env.sh exists
    if [ -f "setup_build_env.sh" ]; then
        chmod +x setup_build_env.sh
        ./setup_build_env.sh
    else
        echo "WARNING: setup_build_env.sh not found, skipping environment setup"
    fi
    
    # Update build_variables.sh with command line parameters
    if [ -f "build_variables.sh" ]; then
        log_verbose "Updating build_variables.sh with command line parameters"
        
        # Update app version
        if [ -n "$APP_VERSION" ]; then
            sed -i '' "s/export APP_VERSION=\".*\"/export APP_VERSION=\"$APP_VERSION\"/" build_variables.sh
        fi
        
        # Update Developer ID if provided
        if [ -n "$DEVELOPER_ID" ]; then
            sed -i '' "s/export DEVELOPER_ID=\".*\"/export DEVELOPER_ID=\"$DEVELOPER_ID\"/" build_variables.sh
        fi
        
        # Update notarization username if provided
        if [ -n "$NOTARIZATION_USERNAME" ]; then
            sed -i '' "s/export NOTARIZATION_USERNAME=\".*\"/export NOTARIZATION_USERNAME=\"$NOTARIZATION_USERNAME\"/" build_variables.sh
        fi
        
        # Update notarization password if provided
        if [ -n "$NOTARIZATION_PASSWORD" ]; then
            sed -i '' "s/export NOTARIZATION_PASSWORD=\".*\"/export NOTARIZATION_PASSWORD=\"$NOTARIZATION_PASSWORD\"/" build_variables.sh
        fi
    else
        echo "WARNING: build_variables.sh not found, creating minimal version"
        cat > build_variables.sh << EOF
#!/bin/bash
# Build variables for GlobalCoyn macOS app

# Application settings
export APP_NAME="GlobalCoyn"
export APP_VERSION="$APP_VERSION"
export APP_BUNDLE_ID="com.globalcoyn.app"
export APP_COPYRIGHT="© 2023-2025 GlobalCoyn Project"

# Build directories
export BUILD_DIR="\$(pwd)/build"
export DIST_DIR="\$(pwd)/dist"
export MACOS_APP_DIR="\$(pwd)/blockchain/apps/macos_app"

# Code signing settings
export DEVELOPER_ID="$DEVELOPER_ID"
export NOTARIZATION_USERNAME="$NOTARIZATION_USERNAME"
export NOTARIZATION_PASSWORD="$NOTARIZATION_PASSWORD"

# Bootstrap node settings
export BOOTSTRAP_NODE1="node1.globalcoyn.com:8001"
export BOOTSTRAP_NODE2="node2.globalcoyn.com:8001"
EOF
        chmod +x build_variables.sh
    fi
fi

# Load build variables
source build_variables.sh
print_header "Build Configuration"
echo "App Name: $APP_NAME"
echo "App Version: $APP_VERSION"
echo "Bundle ID: $APP_BUNDLE_ID"
echo "Build Directory: $BUILD_DIR"
echo "Dist Directory: $DIST_DIR"
echo "Code Signing: $([ -n "$DEVELOPER_ID" ] && echo "Yes - $DEVELOPER_ID" || echo "No")"
echo "Notarization: $([ -n "$NOTARIZATION_USERNAME" ] && echo "Yes - $NOTARIZATION_USERNAME" || echo "No")"

# Setup build directory
print_header "Setting Up Build Directory"
if [ -f "setup_build_dir.sh" ]; then
    chmod +x setup_build_dir.sh
    ./setup_build_dir.sh
else
    echo "ERROR: setup_build_dir.sh not found"
    exit 1
fi

# Copy improved scripts to the build directory
print_header "Copying Enhanced Scripts"

if [ -f "improved_app_wrapper.py" ]; then
    log_verbose "Copying improved_app_wrapper.py to build directory"
    cp "improved_app_wrapper.py" "$BUILD_DIR/GlobalCoyn/"
else
    echo "WARNING: improved_app_wrapper.py not found"
fi

if [ -f "enhanced_node_script.sh" ]; then
    log_verbose "Copying enhanced_node_script.sh to build directory"
    cp "enhanced_node_script.sh" "$BUILD_DIR/GlobalCoyn/working_node.sh"
    chmod +x "$BUILD_DIR/GlobalCoyn/working_node.sh"
else
    echo "WARNING: enhanced_node_script.sh not found"
fi

if [ -f "dependency_installer.py" ]; then
    log_verbose "Copying dependency_installer.py to build directory"
    cp "dependency_installer.py" "$BUILD_DIR/GlobalCoyn/"
else
    echo "WARNING: dependency_installer.py not found"
fi

# Build app with PyInstaller
print_header "Building App with PyInstaller"
if [ -f "GlobalCoyn.spec" ]; then
    # Try direct command first
    if command -v pyinstaller &> /dev/null; then
        echo "Using pyinstaller command"
        pyinstaller --clean GlobalCoyn.spec
    else
        # Fallback to module invocation
        echo "Using python3 -m PyInstaller instead"
        python3 -m PyInstaller --clean GlobalCoyn.spec
    fi
    echo "PyInstaller build completed"
else
    echo "ERROR: GlobalCoyn.spec not found"
    exit 1
fi

# Check if app bundle was created
if [ ! -d "$DIST_DIR/$APP_NAME.app" ]; then
    echo "ERROR: App bundle was not created at $DIST_DIR/$APP_NAME.app"
    exit 1
fi

echo "App bundle created at: $DIST_DIR/$APP_NAME.app"

# Create DMG if requested
if [ "$SKIP_DMG" = false ]; then
    print_header "Creating DMG Installer"
    
    DMG_ARGS=""
    if [ "$SKIP_SIGNING" = true ]; then
        DMG_ARGS="$DMG_ARGS --skip-signing"
    fi
    
    if [ -n "$DEVELOPER_ID" ]; then
        DMG_ARGS="$DMG_ARGS --developer-id \"$DEVELOPER_ID\""
    fi
    
    if [ -n "$NOTARIZATION_USERNAME" ] && [ -n "$NOTARIZATION_PASSWORD" ]; then
        DMG_ARGS="$DMG_ARGS --notarization-username \"$NOTARIZATION_USERNAME\" --notarization-password \"$NOTARIZATION_PASSWORD\""
    fi
    
    if [ -n "$APP_VERSION" ]; then
        DMG_ARGS="$DMG_ARGS --app-version \"$APP_VERSION\""
    fi
    
    if [ -f "create_signed_dmg.sh" ]; then
        chmod +x create_signed_dmg.sh
        eval "./create_signed_dmg.sh $DMG_ARGS"
    else
        echo "ERROR: create_signed_dmg.sh not found"
        exit 1
    fi
fi

# Run tests if requested
if [ "$SKIP_TESTS" = false ]; then
    print_header "Running Tests"
    
    if [ -f "test_app_build.sh" ]; then
        chmod +x test_app_build.sh
        ./test_app_build.sh
    else
        echo "WARNING: test_app_build.sh not found, skipping tests"
    fi
fi

# Complete the build process
print_header "Build Process Complete"
echo "Build completed at: $(date)"

if [ "$SKIP_DMG" = false ] && [ -f "$DIST_DIR/${APP_NAME}-${APP_VERSION}.dmg" ]; then
    echo "DMG file created at: $DIST_DIR/${APP_NAME}-${APP_VERSION}.dmg"
    echo "DMG file size: $(du -h "$DIST_DIR/${APP_NAME}-${APP_VERSION}.dmg" | cut -f1)"
fi

echo "App bundle available at: $DIST_DIR/$APP_NAME.app"
echo ""
echo "To install the app:"
echo "1. Mount the DMG file"
echo "2. Drag the app to Applications folder"
echo "3. Launch from Applications"

exit 0