#!/bin/bash
# Script to update the website with fixed DMG
# Usage: ./update_website.sh <server_ip> <username> <pem_file>

if [ $# -lt 3 ]; then
  echo "Usage: ./update_website.sh <server_ip> <username> <pem_file>"
  echo "Example: ./update_website.sh 13.61.79.186 ec2-user ~/Downloads/globalcoyn.pem"
  exit 1
fi

SERVER_IP=$1
USERNAME=$2
PEM_FILE=$3
DOWNLOADS_DIR="/var/www/globalcoyn/frontend/build/downloads"

echo "Uploading fixed DMG to server..."
scp -i ${PEM_FILE} blockchain/website/downloads/globalcoyn-macos.dmg ${USERNAME}@${SERVER_IP}:~

echo "Updating website DMG file..."
ssh -i ${PEM_FILE} ${USERNAME}@${SERVER_IP} << EOF
# Create downloads directory if it doesn't exist
sudo mkdir -p ${DOWNLOADS_DIR}

# Copy DMG file to the downloads directory
sudo cp ~/globalcoyn-macos.dmg ${DOWNLOADS_DIR}/

# Set appropriate permissions
sudo chown -R ec2-user:ec2-user ${DOWNLOADS_DIR}
sudo chmod 644 ${DOWNLOADS_DIR}/globalcoyn-macos.dmg

echo "DMG file updated on the server!"
EOF

echo "Website update completed!"