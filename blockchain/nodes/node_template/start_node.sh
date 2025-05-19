#!/bin/bash

# Function to check if a port is available
is_port_available() {
    local port=$1
    # Try binding to the port temporarily using nc (netcat)
    # If nc fails with status 0, port is already in use
    # If nc fails with status non-0, port is available
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

# Determine the next available node number if not explicitly provided
if [ -z "$GCN_NODE_NUM" ]; then
    # Start from node number 1
    GCN_NODE_NUM=1
    
    # Check for existing node log files to find the highest existing node number
    for log_file in node_*.log; do
        if [[ $log_file =~ node_([0-9]+)\.log ]]; then
            node_num=${BASH_REMATCH[1]}
            # If we find a higher node number, use the next one
            if (( node_num >= GCN_NODE_NUM )); then
                GCN_NODE_NUM=$((node_num + 1))
            fi
        fi
    done
    
    echo "Auto-assigned node number: $GCN_NODE_NUM"
fi

# Export the node number
export GCN_NODE_NUM

# Find available ports starting from base values
base_p2p_port=$((9000 + $GCN_NODE_NUM - 1))
base_web_port=$((8000 + $GCN_NODE_NUM))

# Find available ports and store them in variables
p2p_port=$(find_available_port $base_p2p_port)
web_port=$(find_available_port $base_web_port)

# Export the environment variables with the numeric values only
export GCN_P2P_PORT=$p2p_port
export GCN_WEB_PORT=$web_port
export GCN_DATA_FILE="blockchain_data.json"

echo "Starting GlobalCoyn node $GCN_NODE_NUM"
echo "P2P Port: $GCN_P2P_PORT (base port: $base_p2p_port)"
echo "Web Port: $GCN_WEB_PORT (base port: $base_web_port)"
echo "Data File: $GCN_DATA_FILE"

# Make sure core modules are in Python path
CURRENT_DIR=$(pwd)
PARENT_DIR=$(dirname "$CURRENT_DIR")
BLOCKCHAIN_DIR=$(dirname "$PARENT_DIR")
CORE_DIR="$BLOCKCHAIN_DIR/core"
ROOT_DIR=$(dirname "$BLOCKCHAIN_DIR")

echo "Setting Python path:"
echo "CURRENT_DIR: $CURRENT_DIR"
echo "PARENT_DIR: $PARENT_DIR"
echo "BLOCKCHAIN_DIR: $BLOCKCHAIN_DIR"
echo "CORE_DIR: $CORE_DIR"
echo "ROOT_DIR: $ROOT_DIR"

export PYTHONPATH="$ROOT_DIR:$CURRENT_DIR:$CORE_DIR:$BLOCKCHAIN_DIR:$PYTHONPATH"
echo "PYTHONPATH: $PYTHONPATH"

# Start the Flask app with more detailed error output
echo "Starting Flask app..."
python3 -u app.py > node_${GCN_NODE_NUM}.log 2>&1 &

echo "Node started. Check node_${GCN_NODE_NUM}.log for output."
echo "API is accessible at http://localhost:$GCN_WEB_PORT"
echo "P2P network is running on port $GCN_P2P_PORT"