#!/bin/bash
# Script to fix the website deployment issues by updating the directory structure
# Usage: ./fix_website_deployment.sh <server_ip> <username> <pem_file>

if [ $# -lt 3 ]; then
  echo "Usage: ./fix_website_deployment.sh <server_ip> <username> <pem_file>"
  echo "Example: ./fix_website_deployment.sh 13.61.79.186 ec2-user ~/Downloads/globalcoyn.pem"
  exit 1
fi

SERVER_IP=$1
USERNAME=$2
PEM_FILE=$3
TIMESTAMP=$(date +%Y%m%d%H%M%S)
LOG_FILE="fix_website_deployment_$TIMESTAMP.log"

# Start logging
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== GlobalCoyn Website Deployment Fix ==="
echo "Started at: $(date)"
echo "Server: $SERVER_IP"

echo "Step 1: Creating a new website package with the correct structure..."
WEBSITE_DIR="blockchain/website"
TMP_DIR="/tmp/globalcoyn-website-fix-$TIMESTAMP"
TAR_FILE="/tmp/globalcoyn-website-$TIMESTAMP.tar.gz"

# Create temp directory with the expected structure
mkdir -p "$TMP_DIR/frontend/build"
cp -r "$WEBSITE_DIR"/* "$TMP_DIR/frontend/build/"

# Create the tar file
cd /tmp
tar -czf "$TAR_FILE" "globalcoyn-website-fix-$TIMESTAMP"
cd - > /dev/null

echo "Package created: $TAR_FILE"

echo "Step 2: Uploading package to server..."
scp -i "$PEM_FILE" "$TAR_FILE" "${USERNAME}@${SERVER_IP}:~/"

echo "Step 3: Fixing website deployment on server..."
ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" << EOF
echo "Connected to server. Starting deployment fix..."

# Backup existing website
echo "Creating backup of existing website..."
BACKUP_DIR="/opt/backups/globalcoyn-website-fix-$TIMESTAMP"
sudo mkdir -p "\$BACKUP_DIR"

if [ -d "/var/www/globalcoyn" ]; then
  sudo cp -r "/var/www/globalcoyn" "\$BACKUP_DIR/"
  echo "Backup created at \$BACKUP_DIR"
fi

# Extract the fixed website
echo "Extracting the fixed website package..."
sudo rm -rf "/var/www/globalcoyn"
sudo mkdir -p "/var/www/globalcoyn"
sudo tar -xzf "$(basename $TAR_FILE)" -C "/var/www/globalcoyn" --strip-components=1

# Set proper permissions
echo "Setting proper permissions..."
sudo chown -R deploy:deploy "/var/www/globalcoyn"
sudo find "/var/www/globalcoyn" -type d -exec chmod 755 {} \;
sudo find "/var/www/globalcoyn" -type f -exec chmod 644 {} \;

# Clean up
echo "Cleaning up..."
rm "$(basename $TAR_FILE)"

# Check directory structure
echo "Verifying directory structure..."
find "/var/www/globalcoyn" -type d | sort

# Restart nginx
echo "Restarting nginx..."
sudo systemctl restart nginx
EOF

echo "Step 4: Verifying website accessibility..."
SITE_CHECK=$(ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" "curl -s -o /dev/null -w '%{http_code}' http://localhost/ || echo 'FAILED'")

if [[ "$SITE_CHECK" == "200" ]]; then
  echo "Website is accessible from server (HTTP 200 OK)"
elif [[ "$SITE_CHECK" == "FAILED" ]]; then
  echo "WARNING: Could not test website accessibility. Curl might not be installed or web server not configured."
else
  echo "WARNING: Website accessibility check returned HTTP $SITE_CHECK"
  
  # Check nginx error logs
  echo "Checking nginx error logs..."
  ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" "sudo tail -n 30 /var/log/nginx/error.log"
fi

echo "=== Website deployment fix completed at: $(date) ==="
echo "Log saved to: $LOG_FILE"

# Clean up local temp files
rm -rf "$TMP_DIR"
rm -f "$TAR_FILE"

echo "Next steps:"
echo "1. Visit http://$SERVER_IP/ to verify the website is accessible"
echo "2. Run ./check_nginx_config.sh $SERVER_IP $USERNAME $PEM_FILE to check nginx configuration if needed"