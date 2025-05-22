#!/bin/bash

# Function to check if a port is available
is_port_available() {
    local port=$1
    # Try binding to the port temporarily using nc (netcat)
    nc -z 127.0.0.1 $port >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        return 1  # Port is NOT available (nc connected successfully)
    else
        return 0  # Port is available (nc couldn't connect)
    fi
}

# Function to find an available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    local max_attempts=50
    local attempt=0
    
    while ! is_port_available $port && [ $attempt -lt $max_attempts ]; do
        echo "Port $port is in use, trying next port..." >&2
        port=$((port + 1))
        attempt=$((attempt + 1))
    done
    
    # Check if we found an available port
    if [ $attempt -eq $max_attempts ]; then
        echo "Could not find an available port after $max_attempts attempts." >&2
        echo "Using port $port anyway, but it might not work." >&2
    fi
    
    # Only output the port number, nothing else
    printf "%d" $port
}

# Determine the node number
GCN_NODE_NUM=1
echo "Using node number: $GCN_NODE_NUM"

# Find available ports starting from base values
base_p2p_port=9010  # Different from the default to avoid conflicts
base_web_port=8010  # Different from the default to avoid conflicts

# Find available ports and store them in variables
p2p_port=$(find_available_port $base_p2p_port)
web_port=$(find_available_port $base_web_port)

# Export the environment variables with the numeric values only
export GCN_NODE_NUM=$GCN_NODE_NUM
export GCN_P2P_PORT=$p2p_port
export GCN_WEB_PORT=$web_port
export GCN_DATA_FILE="globalcoyn_blockchain_data.json"
export GCN_ENV="development"

echo "Starting GlobalCoyn node $GCN_NODE_NUM"
echo "P2P Port: $GCN_P2P_PORT (base port: $base_p2p_port)"
echo "Web Port: $GCN_WEB_PORT (base port: $base_web_port)"
echo "Data File: $GCN_DATA_FILE"
echo "Environment: $GCN_ENV"

# Make sure core modules are in Python path
CURRENT_DIR=$(pwd)
PARENT_DIR=$(dirname "$CURRENT_DIR")
CORE_DIR="$PARENT_DIR/core"

echo "Setting Python path:"
echo "CURRENT_DIR: $CURRENT_DIR"
echo "PARENT_DIR: $PARENT_DIR"
echo "CORE_DIR: $CORE_DIR"

export PYTHONPATH="$PARENT_DIR:$CORE_DIR:$PYTHONPATH"
echo "PYTHONPATH: $PYTHONPATH"

# Start the Flask app
echo "Starting Flask app..."
python3 -u app.py > globalcoyn_node.log 2>&1 &

echo "Node started. Check globalcoyn_node.log for output."
echo "API is accessible at http://localhost:$GCN_WEB_PORT"
echo "P2P network is running on port $GCN_P2P_PORT"