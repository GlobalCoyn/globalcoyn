#!/bin/bash
# Script to check the Python environment and required packages

echo "Checking development environment..."
echo "--------------------------------"

# Check Python version
echo "Python:"
which python || echo "python command not found"
which python3
python3 --version

# Check pip
echo -e "\nPIP:"
python3 -m pip --version

# Check required packages
echo -e "\nRequired Packages:"
python3 -c "
import sys
try:
    import requests
    print('✓ requests')
except ImportError:
    print('✗ requests not installed')

try:
    import json
    print('✓ json')
except ImportError:
    print('✗ json not installed')

try:
    import socket
    print('✓ socket')
except ImportError:
    print('✗ socket not installed')

try:
    import threading
    print('✓ threading')
except ImportError:
    print('✗ threading not installed')

try:
    import time
    print('✓ time')
except ImportError:
    print('✗ time not installed')

try:
    import logging
    print('✓ logging')
except ImportError:
    print('✗ logging not installed')
"

# Check if the required directories exist
echo -e "\nDirectories:"
if [ -d "./blockchain/network" ]; then
    echo "✓ ./blockchain/network exists"
else
    echo "✗ ./blockchain/network does not exist"
fi

if [ -d "./blockchain/core" ]; then
    echo "✓ ./blockchain/core exists"
else
    echo "✗ ./blockchain/core does not exist"
fi

if [ -d "./blockchain/apps/macos_app" ]; then
    echo "✓ ./blockchain/apps/macos_app exists"
else
    echo "✗ ./blockchain/apps/macos_app does not exist"
fi

if [ -d "./blockchain/nodes/node1" ]; then
    echo "✓ ./blockchain/nodes/node1 exists"
else
    echo "✗ ./blockchain/nodes/node1 does not exist"
fi

# Check if the required files exist
echo -e "\nKey Files:"
REQUIRED_FILES=(
    "./blockchain/network/bootstrap_config.py"
    "./blockchain/network/dns_seed.py"
    "./blockchain/network/seed_nodes.py"
    "./blockchain/network/connection_backoff.py"
    "./blockchain/core/blockchain.py"
    "./blockchain/core/coin.py"
    "./blockchain/core/wallet.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file does not exist"
    fi
done

echo "--------------------------------"
echo "To install required packages, run:"
echo "python3 -m pip install requests"
echo "--------------------------------"