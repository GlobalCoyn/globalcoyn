#!/bin/bash
# Script to verify a DMG file and upload it to the server
# Usage: ./upload_verified_dmg.sh <server_ip> <username> <pem_file>

if [ $# -lt 3 ]; then
  echo "Usage: ./upload_verified_dmg.sh <server_ip> <username> <pem_file>"
  echo "Example: ./upload_verified_dmg.sh 13.61.79.186 ec2-user ~/Downloads/globalcoyn.pem"
  exit 1
fi

SERVER_IP=$1
USERNAME=$2
PEM_FILE=$3
DMG_PATH="blockchain/website/downloads/globalcoyn-macos.dmg"
DOWNLOADS_DIR="/var/www/globalcoyn/frontend/build/downloads"
BACKUP_DIR="/tmp/dmg_backups"

# First verify the DMG is valid
echo "Verifying DMG integrity before upload..."
if ! hdiutil verify "$DMG_PATH"; then
  echo "ERROR: DMG verification failed - cannot upload corrupted DMG"
  exit 1
fi

echo "DMG verified successfully!"

# Try mounting the DMG to ensure it works
echo "Testing DMG by mounting it..."
MOUNT_DIR=$(hdiutil attach -nobrowse "$DMG_PATH" | grep '/Volumes/' | tail -1 | awk '{print $NF}')
if [ -z "$MOUNT_DIR" ]; then
  echo "ERROR: Failed to mount DMG for testing"
  exit 1
fi

echo "DMG mounted at $MOUNT_DIR - it works!"
sleep 2
hdiutil detach "$MOUNT_DIR" -force

# Create backup directory on server
echo "Creating backup directory on server..."
ssh -i ${PEM_FILE} ${USERNAME}@${SERVER_IP} "mkdir -p $BACKUP_DIR"

# Upload DMG to server
echo "Uploading verified DMG to server..."
scp -i ${PEM_FILE} "$DMG_PATH" ${USERNAME}@${SERVER_IP}:~/globalcoyn-macos.dmg

# Update website with new DMG
echo "Updating website with verified DMG..."
ssh -i ${PEM_FILE} ${USERNAME}@${SERVER_IP} << EOF
# Backup any existing DMG
if [ -f "${DOWNLOADS_DIR}/globalcoyn-macos.dmg" ]; then
  cp "${DOWNLOADS_DIR}/globalcoyn-macos.dmg" "${BACKUP_DIR}/globalcoyn-macos.dmg.\$(date +%s)"
  echo "Backed up existing DMG file"
fi

# Create downloads directory if it doesn't exist
sudo mkdir -p ${DOWNLOADS_DIR}

# Copy DMG file to the downloads directory
sudo cp ~/globalcoyn-macos.dmg ${DOWNLOADS_DIR}/

# Set appropriate permissions
sudo chown -R ec2-user:ec2-user ${DOWNLOADS_DIR}
sudo chmod 644 ${DOWNLOADS_DIR}/globalcoyn-macos.dmg

echo "DMG file updated on the server!"
EOF

echo "Website update completed with verified DMG!"
echo "The DMG file has been tested and is definitely not corrupted."