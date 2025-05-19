#!/bin/bash
# Script to deploy the macOS app to the website
# Usage: ./deploy_macos_app.sh <server_ip> <username> <pem_file>

if [ $# -lt 3 ]; then
  echo "Usage: ./deploy_macos_app.sh <server_ip> <username> <pem_file>"
  echo "Example: ./deploy_macos_app.sh 13.61.79.186 ec2-user ~/Downloads/globalcoyn.pem"
  exit 1
fi

SERVER_IP=$1
USERNAME=$2
PEM_FILE=$3
DIST_DIR="$(pwd)/dist"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
LOG_FILE="deploy-macos-app-$TIMESTAMP.log"

# Start logging
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== GlobalCoyn macOS App Deployment ==="
echo "Started at: $(date)"
echo "Server: $SERVER_IP"

echo "Step 1: Checking for macOS app..."
# Check if DMG file exists
DMG_FILE=$(find "$DIST_DIR" -name "GlobalCoyn-*.dmg" | sort -r | head -n1)
if [ -n "$DMG_FILE" ]; then
    APP_FILE="$DMG_FILE"
    APP_TYPE="DMG"
    echo "Found DMG file: $DMG_FILE"
else
    # Check if ZIP file exists
    ZIP_FILE=$(find "$DIST_DIR" -name "GlobalCoyn-*.zip" | sort -r | head -n1)
    if [ -n "$ZIP_FILE" ]; then
        APP_FILE="$ZIP_FILE"
        APP_TYPE="ZIP"
        echo "Found ZIP file: $ZIP_FILE"
    else
        echo "ERROR: No macOS app file found in $DIST_DIR"
        echo "Please run ./macos_app_builder.sh first to build the app"
        exit 1
    fi
fi

# Get the app version
APP_VERSION=$(basename "$APP_FILE" | sed -E 's/GlobalCoyn-([0-9]+\.[0-9]+\.[0-9]+)\.(dmg|zip)/\1/')
if [ -z "$APP_VERSION" ]; then
    APP_VERSION="2.0.1" # Default version if we can't extract it
fi

echo "App version: $APP_VERSION"
echo "App file: $APP_FILE"
echo "App type: $APP_TYPE"

echo "Step 2: Uploading to server..."
scp -i "$PEM_FILE" "$APP_FILE" "${USERNAME}@${SERVER_IP}:~/"

echo "Step 3: Deploying to website downloads directory..."
FILENAME=$(basename "$APP_FILE")
ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" << EOF
echo "Connected to server. Starting deployment..."

# Ensure downloads directory exists
sudo mkdir -p /var/www/globalcoyn/frontend/build/downloads

# Copy the app file to the downloads directory
sudo cp ~/"$FILENAME" /var/www/globalcoyn/frontend/build/downloads/

# For DMG files, create a standardized link
if [ "$APP_TYPE" = "DMG" ]; then
    sudo ln -sf /var/www/globalcoyn/frontend/build/downloads/"$FILENAME" /var/www/globalcoyn/frontend/build/downloads/globalcoyn-macos.dmg
    echo "Created link: globalcoyn-macos.dmg -> $FILENAME"
fi

# For ZIP files, create a standardized link
if [ "$APP_TYPE" = "ZIP" ]; then
    sudo ln -sf /var/www/globalcoyn/frontend/build/downloads/"$FILENAME" /var/www/globalcoyn/frontend/build/downloads/globalcoyn-macos.zip
    echo "Created link: globalcoyn-macos.zip -> $FILENAME"
fi

# Set proper permissions
sudo chown -R deploy:deploy /var/www/globalcoyn/frontend/build/downloads/
sudo chmod 644 /var/www/globalcoyn/frontend/build/downloads/"$FILENAME"

# Clean up
rm ~/"$FILENAME"

echo "Deployment completed on server side."
EOF

echo "Step 4: Verifying deployment..."
if [ "$APP_TYPE" = "DMG" ]; then
    SITE_CHECK=$(ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" "curl -s -o /dev/null -w '%{http_code}' http://localhost/downloads/globalcoyn-macos.dmg || echo 'FAILED'")
    echo "macOS DMG download check: HTTP $SITE_CHECK"
else
    SITE_CHECK=$(ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" "curl -s -o /dev/null -w '%{http_code}' http://localhost/downloads/globalcoyn-macos.zip || echo 'FAILED'")
    echo "macOS ZIP download check: HTTP $SITE_CHECK"
fi

echo "Step 5: Updating website download links..."
# Verify if we need to update any HTML files with new version numbers
ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" << EOF
if [ -f "/var/www/globalcoyn/frontend/build/index.html" ]; then
    # Update version tag if it exists
    if grep -q "Version [0-9]" /var/www/globalcoyn/frontend/build/index.html; then
        sudo sed -i "s/Version [0-9][0-9.]*<\/p>/Version $APP_VERSION<\/p>/g" /var/www/globalcoyn/frontend/build/index.html
        echo "Updated version number in index.html to $APP_VERSION"
    fi
fi
EOF

echo "=== Deployment completed at: $(date) ==="
echo "macOS app should now be available at http://$SERVER_IP/downloads/globalcoyn-macos.dmg"
echo "Log saved to: $LOG_FILE"