#!/bin/bash
# working_node.sh - Helper script for node operation
# This script helps start, stop, and monitor blockchain nodes

# Default values
NODE_DIR="$PWD"
NODE_NUM=1
P2P_PORT=9000
WEB_PORT=8001

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --node-num)
            NODE_NUM="$2"
            shift
            ;;
        --p2p-port)
            P2P_PORT="$2"
            shift
            ;;
        --web-port)
            WEB_PORT="$2"
            shift
            ;;
        --dir)
            NODE_DIR="$2"
            shift
            ;;
        *)
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
    shift
done

# Calculate ports based on node number if not explicitly set
if [[ "$P2P_PORT" == "9000" ]]; then
    P2P_PORT=$((9000 + NODE_NUM - 1))
fi

if [[ "$WEB_PORT" == "8001" ]]; then
    WEB_PORT=$((8000 + NODE_NUM))
fi

# Function to start the node
start_node() {
    echo "Starting node $NODE_NUM (P2P: $P2P_PORT, Web: $WEB_PORT)"
    cd "$NODE_DIR"
    
    # Set environment variables
    export GCN_NODE_NUM=$NODE_NUM
    export GCN_P2P_PORT=$P2P_PORT
    export GCN_WEB_PORT=$WEB_PORT
    
    # Start the node
    python app.py
}

# Function to check if node is running
check_node() {
    echo "Checking node $NODE_NUM..."
    curl -s "http://localhost:$WEB_PORT/api/blockchain" | python -m json.tool
}

# Function to stop the node
stop_node() {
    echo "Stopping node $NODE_NUM..."
    PID=$(ps aux | grep "python app.py" | grep -v grep | awk '{print $2}')
    if [[ -n "$PID" ]]; then
        kill -9 $PID
        echo "Node stopped (PID: $PID)"
    else
        echo "Node not running"
    fi
}

# Default action
start_node

exit 0