#!/bin/bash
# Script to check the nginx configuration on the production server
# Usage: ./check_nginx_config.sh <server_ip> <username> <pem_file>

if [ $# -lt 3 ]; then
  echo "Usage: ./check_nginx_config.sh <server_ip> <username> <pem_file>"
  echo "Example: ./check_nginx_config.sh 13.61.79.186 ec2-user ~/Downloads/globalcoyn.pem"
  exit 1
fi

SERVER_IP=$1
USERNAME=$2
PEM_FILE=$3

echo "Checking nginx configuration on $SERVER_IP..."
ssh -i "$PEM_FILE" "${USERNAME}@${SERVER_IP}" << 'EOF'
  echo "Connected to server. Checking nginx configuration..."
  
  # Check if globalcoyn.conf exists
  if [ -f /etc/nginx/conf.d/globalcoyn.conf ]; then
    echo -e "\nCurrent globalcoyn.conf:"
    sudo cat /etc/nginx/conf.d/globalcoyn.conf
  else
    echo -e "\nglobalcoyn.conf not found!"
    echo "Checking for other site configs:"
    sudo find /etc/nginx/conf.d/ -type f -name "*.conf" -exec echo -e "\n--- {} ---\n" \; -exec sudo cat {} \; -exec echo -e "\n--------\n" \;
  fi
  
  # Check nginx error logs
  echo -e "\nRecent nginx error logs:"
  sudo tail -n 20 /var/log/nginx/error.log
  
  # List current website directory structure
  echo -e "\nCurrent website directory structure:"
  sudo ls -la /var/www/globalcoyn/
  
  # Check if the frontend/build directory exists
  if [ -d "/var/www/globalcoyn/frontend/build" ]; then
    echo -e "\nContents of /var/www/globalcoyn/frontend/build:"
    sudo ls -la /var/www/globalcoyn/frontend/build/
  fi
EOF

echo "Done checking nginx configuration."