#!/bin/bash
# Find the blockchain node app.py file
echo "Searching for app.py files..."
find /var/www -name "app.py" 2>/dev/null

echo -e "\nSearching for blockchain-related directories..."
find /var/www -type d -name "*blockchain*" 2>/dev/null
find /var/www -type d -name "*node*" 2>/dev/null

echo -e "\nChecking what's in /var/www..."
ls -la /var/www