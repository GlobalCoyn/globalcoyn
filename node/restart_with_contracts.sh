#!/bin/bash

# Kill existing node process if running
echo "Stopping any running nodes..."
pkill -f "python3.*app.py" || true

# Forcefully terminate any processes on port 8001
echo "Forcefully closing port 8001 if occupied..."
lsof -i :8001 -t | xargs kill -9 2>/dev/null || true
lsof -i :9000 -t | xargs kill -9 2>/dev/null || true

# Wait a moment for ports to be released
echo "Waiting for ports to be released..."
sleep 5

# Start the node with contract routes
cd /Users/adamneto/Desktop/blockchain/GlobalCoyn/node

# Set up paths for module imports
CURRENT_DIR=$(pwd)
PARENT_DIR=$(dirname "$CURRENT_DIR")
CORE_DIR="$PARENT_DIR/core"

echo "Setting Python path:"
echo "CURRENT_DIR: $CURRENT_DIR"
echo "PARENT_DIR: $PARENT_DIR"
echo "CORE_DIR: $CORE_DIR"

# Function to check if a port is available
is_port_available() {
    local port=$1
    nc -z 127.0.0.1 $port >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        return 1  # Port is NOT available
    else
        return 0  # Port is available
    fi
}

# Function to find an available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    local max_attempts=20
    local attempt=0
    
    while ! is_port_available $port && [ $attempt -lt $max_attempts ]; do
        echo "Port $port is in use, trying next port..." >&2  # Direct to stderr, not stdout
        port=$((port + 1))
        attempt=$((attempt + 1))
    done
    
    echo "$port"  # Ensure only the port number is returned
}

# Use specific ports for main node
P2P_PORT=9000
echo "Using P2P port: $P2P_PORT"
WEB_PORT=8001
echo "Using Web port: $WEB_PORT"

# Export environment variables
export PYTHONPATH="$PARENT_DIR:$CORE_DIR:$PYTHONPATH"
export GCN_NODE_NUM=1
export GCN_P2P_PORT=$P2P_PORT
export GCN_WEB_PORT=$WEB_PORT
export GCN_DATA_FILE="globalcoyn_blockchain_data.json"
export GCN_ENV="development"

echo "PYTHONPATH: $PYTHONPATH"
echo "API will be accessible at http://localhost:$WEB_PORT"

# Start the node
python3 app.py