#!/bin/bash
# Script to deploy the updated GlobalCoyn website to the production server
# Usage: ./deploy_website.sh <server_ip> <username> <pem_file>

if [ $# -lt 3 ]; then
  echo "Usage: ./deploy_website.sh <server_ip> <username> <pem_file>"
  echo "Example: ./deploy_website.sh 13.61.79.186 ec2-user ~/Downloads/globalcoyn.pem"
  exit 1
fi

SERVER_IP=$1
USERNAME=$2
PEM_FILE=$3
SERVER_DIR="/var/www/html"
WEBSITE_DIR="blockchain/website"
TEMP_DIR="/tmp/globalcoyn_website"
BACKUP_DIR="/tmp/globalcoyn_website_backup"

echo "Preparing website for deployment..."

# Create a temporary directory
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# Copy website files
cp -r $WEBSITE_DIR/* $TEMP_DIR/

# Create directories if needed
mkdir -p $TEMP_DIR/assets
mkdir -p $TEMP_DIR/downloads
mkdir -p $TEMP_DIR/docs
mkdir -p $TEMP_DIR/legal
mkdir -p $TEMP_DIR/css
mkdir -p $TEMP_DIR/js

# Create zip archive
ZIP_FILE="/tmp/globalcoyn-website.zip"
cd $TEMP_DIR
zip -r $ZIP_FILE .
cd - > /dev/null

echo "Website packaged. Uploading to server..."

# Upload zip file to server
scp -i ${PEM_FILE} $ZIP_FILE ${USERNAME}@${SERVER_IP}:~

echo "Deploying website on server..."

# Deploy on server
ssh -i ${PEM_FILE} ${USERNAME}@${SERVER_IP} << EOF
# Create backup of existing website
echo "Creating backup of current website..."
sudo mkdir -p $BACKUP_DIR
if [ -d "$SERVER_DIR" ]; then
  sudo cp -r $SERVER_DIR/* $BACKUP_DIR/
fi

# Create server directory if it doesn't exist
sudo mkdir -p $SERVER_DIR

# Extract new website
echo "Extracting new website..."
sudo unzip -o ~/globalcoyn-website.zip -d $SERVER_DIR

# Set proper permissions
echo "Setting permissions..."
sudo chown -R ec2-user:ec2-user $SERVER_DIR
sudo find $SERVER_DIR -type d -exec chmod 755 {} \;
sudo find $SERVER_DIR -type f -exec chmod 644 {} \;

# Clean up
echo "Cleaning up..."
rm ~/globalcoyn-website.zip

echo "Website deployment complete!"
EOF

echo "Website deployment completed successfully."
echo "Website is now available at http://$SERVER_IP/"
echo "Note: You may need to configure your web server (Apache/Nginx) if not already done."
echo "Backup of previous website is at $BACKUP_DIR on the server."