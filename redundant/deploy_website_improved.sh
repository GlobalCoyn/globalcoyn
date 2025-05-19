#!/bin/bash
# Improved script to deploy the updated GlobalCoyn website to the production server
# Usage: ./deploy_website_improved.sh <server_ip> <username> <pem_file>

if [ $# -lt 3 ]; then
  echo "Usage: ./deploy_website_improved.sh <server_ip> <username> <pem_file>"
  echo "Example: ./deploy_website_improved.sh 13.61.79.186 ec2-user ~/Downloads/globalcoyn.pem"
  exit 1
fi

SERVER_IP=$1
USERNAME=$2
PEM_FILE=$3
SERVER_DIR="/var/www/globalcoyn"
WEBSITE_DIR="blockchain/website"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
BACKUP_DIR="/opt/backups/globalcoyn-website-$TIMESTAMP"
LOG_FILE="deploy-website-$TIMESTAMP.log"

# Start logging
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== GlobalCoyn Website Deployment ==="
echo "Started at: $(date)"
echo "Server: $SERVER_IP"
echo "Deploying from: $WEBSITE_DIR"
echo "Deploying to: $SERVER_DIR"

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
TAR_FILE="/tmp/globalcoyn-website-$TIMESTAMP.tar.gz"
cd $(dirname "$WEBSITE_DIR")
tar -czf "$TAR_FILE" $(basename "$WEBSITE_DIR")
cd - > /dev/null

echo "Step 3: Verifying deployment package..."
if [ ! -f "$TAR_FILE" ]; then
  echo "ERROR: Failed to create deployment package!"
  exit 1
fi

PACKAGE_SIZE=$(du -h "$TAR_FILE" | cut -f1)
echo "Package created successfully: $TAR_FILE ($PACKAGE_SIZE)"

echo "Step 4: Uploading package to server..."
scp -i "$PEM_FILE" "$TAR_FILE" "${USERNAME}@${SERVER_IP}:~/"

echo "Step 5: Deploying on server..."
ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" << EOF
echo "Connected to server. Starting deployment..."

# Create backup directory
echo "Creating backup directory..."
sudo mkdir -p "$BACKUP_DIR"

# Backup existing website if exists
if [ -d "$SERVER_DIR" ]; then
  echo "Backing up existing website..."
  sudo cp -r "$SERVER_DIR" "$BACKUP_DIR"
else
  echo "No existing website to backup."
  sudo mkdir -p "$SERVER_DIR"
fi

# Extract new website
echo "Extracting new website..."
sudo rm -rf "$SERVER_DIR"/*
sudo mkdir -p "$SERVER_DIR"
sudo tar -xzf ~/$(basename "$TAR_FILE") -C "$SERVER_DIR" --strip-components=1

# Set proper permissions
echo "Setting permissions..."
sudo chown -R ec2-user:ec2-user "$SERVER_DIR"
sudo find "$SERVER_DIR" -type d -exec chmod 755 {} \;
sudo find "$SERVER_DIR" -type f -exec chmod 644 {} \;

# Clean up
echo "Cleaning up..."
rm ~/$(basename "$TAR_FILE")

# Create directories if they don't exist
echo "Ensuring all directories exist..."
sudo mkdir -p "$SERVER_DIR/css"
sudo mkdir -p "$SERVER_DIR/js"
sudo mkdir -p "$SERVER_DIR/assets"
sudo mkdir -p "$SERVER_DIR/docs"
sudo mkdir -p "$SERVER_DIR/legal"
sudo mkdir -p "$SERVER_DIR/downloads"

echo "Deployment completed on server side."
EOF

echo "Step 6: Deployment verification..."
VERIFY_RESULT=$(ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" "ls -la $SERVER_DIR/index.html 2>/dev/null || echo 'NOT FOUND'")

if [[ "$VERIFY_RESULT" == *"NOT FOUND"* ]]; then
  echo "ERROR: Deployment verification failed! index.html not found on server."
  exit 1
else
  echo "Deployment verified successfully!"
  echo "Backup saved at: $BACKUP_DIR"
  echo "Website deployed to: $SERVER_DIR"
fi

echo "Step 7: Testing website accessibility..."
SITE_CHECK=$(ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" "curl -s -o /dev/null -w '%{http_code}' http://localhost/ || echo 'FAILED'")

if [[ "$SITE_CHECK" == "200" ]]; then
  echo "Website is accessible from server (HTTP 200 OK)"
elif [[ "$SITE_CHECK" == "FAILED" ]]; then
  echo "WARNING: Could not test website accessibility. Curl might not be installed or web server not configured."
else
  echo "WARNING: Website accessibility check returned HTTP $SITE_CHECK"
fi

echo "=== Deployment completed at: $(date) ==="
echo "Website should now be accessible at http://$SERVER_IP/"
echo "Log saved to: $LOG_FILE"