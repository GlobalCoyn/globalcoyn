#!/bin/bash
# Script to fix missing dependencies in the GlobalCoyn macOS app
# This script installs the necessary Python packages that GlobalCoyn requires

echo "===== GlobalCoyn macOS App Dependency Fixer ====="
echo "This script will install the required dependencies for the GlobalCoyn app."

# Check if running with sudo privileges
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run with sudo to install system-wide packages."
   echo "Please run: sudo $0"
   exit 1
fi

echo "Checking Python installation..."
PYTHON_PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

if [ -f "$PYTHON_PATH" ]; then
    echo "Found Python at $PYTHON_PATH"
else
    echo "Python not found at expected location. Checking for alternatives..."
    
    # Try to find any available Python 3 installation
    if command -v python3 &> /dev/null; then
        PYTHON_PATH=$(which python3)
        echo "Found Python at $PYTHON_PATH"
    else
        echo "Error: Python 3 is not installed. Please install Python 3 and try again."
        exit 1
    fi
fi

echo "Installing required dependencies..."
"$PYTHON_PATH" -m pip install --upgrade pip
"$PYTHON_PATH" -m pip install requests

echo "Checking app directory..."
APP_DIR="/Applications/GlobalCoyn"
if [ -d "$APP_DIR" ]; then
    echo "GlobalCoyn app found at $APP_DIR"
    
    # Fix the command file to ensure it uses the correct Python
    echo "Updating the GlobalCoyn.command file..."
    cat > "$APP_DIR/GlobalCoyn.command" << 'EOF'
#!/bin/bash
# GlobalCoyn Launcher

# Go to the app directory
cd "$(dirname "$0")" || exit

echo "Starting GlobalCoyn application..."

# Try different Python versions in order of preference
if command -v python3 &> /dev/null; then
    PYTHON_PATH=$(which python3)
elif [ -f "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3" ]; then
    PYTHON_PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
elif [ -f "/usr/bin/python3" ]; then
    PYTHON_PATH="/usr/bin/python3"
else
    echo "Error: Python 3 not found. Please install Python 3 and try again."
    read -p "Press Enter to close this window..."
    exit 1
fi

echo "Using Python at: $PYTHON_PATH"

# Check for required modules
if ! $PYTHON_PATH -c "import requests" &> /dev/null; then
    echo "Installing missing 'requests' module..."
    $PYTHON_PATH -m pip install requests
fi

# Run the application
$PYTHON_PATH app_wrapper.py

if [ $? -ne 0 ]; then
    echo "Error running the application. See error details above."
    read -p "Press Enter to close this window..."
    exit 1
fi
EOF
    
    # Make it executable
    chmod +x "$APP_DIR/GlobalCoyn.command"
    
    echo "Dependencies and launcher have been updated successfully!"
    echo "You can now run GlobalCoyn by double-clicking on GlobalCoyn.command file."
else
    echo "GlobalCoyn app not found at $APP_DIR."
    echo "Please make sure the app is installed in the Applications folder."
    exit 1
fi