#!/bin/bash
# Script to deploy the updated GlobalCoyn website to production
# Usage: ./deploy_updated_website.sh <server_ip> <username> <pem_file>

if [ $# -lt 3 ]; then
  echo "Usage: ./deploy_updated_website.sh <server_ip> <username> <pem_file>"
  echo "Example: ./deploy_updated_website.sh 13.61.79.186 ec2-user ~/Downloads/globalcoyn.pem"
  exit 1
fi

SERVER_IP=$1
USERNAME=$2
PEM_FILE=$3
TIMESTAMP=$(date +%Y%m%d%H%M%S)
LOG_FILE="deploy-updated-website-$TIMESTAMP.log"

# Start logging
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== GlobalCoyn Updated Website Deployment ==="
echo "Started at: $(date)"
echo "Server: $SERVER_IP"

# Define directories
WEBSITE_DIR="blockchain/website"
TARGET_DIR="/var/www/globalcoyn/frontend/build"
TMP_DIR="/tmp/globalcoyn-website-$TIMESTAMP"
TAR_FILE="/tmp/globalcoyn-website-$TIMESTAMP.tar.gz"

echo "Step 1: Checking for required directories and files..."
if [ ! -d "$WEBSITE_DIR" ]; then
  echo "ERROR: Website directory '$WEBSITE_DIR' not found!"
  exit 1
fi

if [ ! -f "$WEBSITE_DIR/index.html" ]; then
  echo "ERROR: index.html not found in website directory!"
  exit 1
fi

echo "Step 2: Creating deployment package..."
# Create temp directory for packaging
mkdir -p "$TMP_DIR"
cp -r "$WEBSITE_DIR"/* "$TMP_DIR/"

# Create the tar file
cd /tmp
tar -czf "$TAR_FILE" "globalcoyn-website-$TIMESTAMP"
cd - > /dev/null

echo "Package created: $TAR_FILE"

echo "Step 3: Uploading package to server..."
scp -i "$PEM_FILE" "$TAR_FILE" "${USERNAME}@${SERVER_IP}:~/"

echo "Step 4: Deploying on server..."
ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" << EOF
echo "Connected to server. Starting deployment..."

# Backup existing website
echo "Creating backup of existing website..."
BACKUP_DIR="/opt/backups/globalcoyn-website-$TIMESTAMP"
sudo mkdir -p "\$BACKUP_DIR"

if [ -d "$TARGET_DIR" ]; then
  echo "Backing up existing website from $TARGET_DIR..."
  sudo cp -r "$TARGET_DIR" "\$BACKUP_DIR/"
  echo "Backup created at \$BACKUP_DIR"
fi

# Extract new website
echo "Extracting new website..."
sudo rm -rf "$TARGET_DIR"
sudo mkdir -p "$TARGET_DIR"
sudo tar -xzf "$(basename $TAR_FILE)" -C "$TARGET_DIR" --strip-components=1

# Set proper permissions
echo "Setting permissions..."
sudo chown -R deploy:deploy "$TARGET_DIR"
sudo find "$TARGET_DIR" -type d -exec chmod 755 {} \;
sudo find "$TARGET_DIR" -type f -exec chmod 644 {} \;

# Create directories if they don't exist
echo "Ensuring all directories exist..."
sudo mkdir -p "$TARGET_DIR/css"
sudo mkdir -p "$TARGET_DIR/js"
sudo mkdir -p "$TARGET_DIR/assets"
sudo mkdir -p "$TARGET_DIR/docs"
sudo mkdir -p "$TARGET_DIR/docs/images"
sudo mkdir -p "$TARGET_DIR/legal"
sudo mkdir -p "$TARGET_DIR/downloads"

# Clean up
echo "Cleaning up..."
rm "$(basename $TAR_FILE)"

# Restart nginx to apply changes
echo "Restarting nginx..."
sudo systemctl restart nginx

echo "Deployment completed on server side."
EOF

echo "Step 5: Verifying deployment..."
# Test main page
SITE_CHECK=$(ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" "curl -s -o /dev/null -w '%{http_code}' http://localhost/ || echo 'FAILED'")
echo "Main page: HTTP $SITE_CHECK"

# Test whitepaper page
WHITEPAPER_CHECK=$(ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" "curl -s -o /dev/null -w '%{http_code}' http://localhost/docs/whitepaper.html || echo 'FAILED'")
echo "Whitepaper page: HTTP $WHITEPAPER_CHECK"

# Test blockchain-api.js
API_JS_CHECK=$(ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" "curl -s -o /dev/null -w '%{http_code}' http://localhost/js/blockchain-api.js || echo 'FAILED'")
echo "blockchain-api.js: HTTP $API_JS_CHECK"

# Check if all tests passed
if [[ "$SITE_CHECK" == "200" && "$WHITEPAPER_CHECK" == "200" && "$API_JS_CHECK" == "200" ]]; then
  echo "All verification checks passed!"
else
  echo "WARNING: Some verification checks failed. Check the logs for details."
  
  # Check nginx error logs
  echo "Checking nginx error logs..."
  ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" "sudo tail -n 20 /var/log/nginx/error.log"
fi

echo "=== Deployment completed at: $(date) ==="
echo "Website should now be accessible at http://$SERVER_IP/"
echo "Log saved to: $LOG_FILE"

# Clean up local temp files
rm -rf "$TMP_DIR"
rm -f "$TAR_FILE"

echo "Next steps:"
echo "1. Verify the website is displaying correctly at http://$SERVER_IP/"
echo "2. Check that the blockchain statistics are updating with real data"
echo "3. Verify Quick Start Guide links work correctly"
echo "4. Verify the whitepaper page is accessible"