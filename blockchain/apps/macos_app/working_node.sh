#!/bin/bash
# working_node.sh - Helper script for node operation
# This script helps start, stop, and monitor blockchain nodes

# Default values
NODE_DIR="$PWD"
NODE_NUM=1
P2P_PORT=9000
WEB_PORT=8001
SETUP_ONLY=false

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
        --setup-only)
            SETUP_ONLY=true
            ;;
        *)
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
    shift
done

# Create the node directory if it doesn't exist
if [[ ! -d "$NODE_DIR" ]]; then
    echo "Creating node directory: $NODE_DIR"
    mkdir -p "$NODE_DIR"
fi

# Calculate ports based on node number if not explicitly set
if [[ "$P2P_PORT" == "9000" ]]; then
    P2P_PORT=$((9000 + NODE_NUM - 1))
fi

if [[ "$WEB_PORT" == "8001" ]]; then
    WEB_PORT=$((8000 + NODE_NUM))
fi

# Setup function to prepare the node environment
setup_node() {
    echo "Setting up node environment at $NODE_DIR"
    cd "$NODE_DIR" || exit 1
    
    # Check if app.py already exists
    if [[ -f "app.py" ]]; then
        echo "app.py already exists, skipping setup"
        return 0
    fi
    
    echo "Creating node configuration files..."
    
    # First, ensure core directory exists and has required files
    mkdir -p "core"
    
    # Look for core module files in a few possible locations
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
    
    # Potential core module locations
    CORE_LOCATIONS=(
        "$SCRIPT_DIR/../core"
        "$PROJECT_DIR/core"
        "$PROJECT_DIR/blockchain/core"
        "$PROJECT_DIR/nodes/node1/core"
    )
    
    FOUND_CORE=false
    for CORE_PATH in "${CORE_LOCATIONS[@]}"; do
        if [[ -d "$CORE_PATH" ]]; then
            echo "Found core modules at $CORE_PATH"
            
            # Copy core files
            for FILE in blockchain.py coin.py wallet.py price_oracle.py; do
                if [[ -f "$CORE_PATH/$FILE" ]]; then
                    echo "Copying $FILE to core directory"
                    cp "$CORE_PATH/$FILE" "core/"
                fi
            done
            
            FOUND_CORE=true
            break
        fi
    done
    
    if [[ "$FOUND_CORE" == "false" ]]; then
        echo "WARNING: Could not find core modules, node may not function correctly"
    fi
    
    # Create __init__.py in core directory
    touch "core/__init__.py"
    
    # Look for app.py template
    APP_TEMPLATE_LOCATIONS=(
        "$SCRIPT_DIR/../node_template/app.py"
        "$PROJECT_DIR/node_template/app.py"
        "$PROJECT_DIR/nodes/node1/app.py"
        "$PROJECT_DIR/blockchain/nodes/node1/app.py"
    )
    
    FOUND_APP=false
    for APP_PATH in "${APP_TEMPLATE_LOCATIONS[@]}"; do
        if [[ -f "$APP_PATH" ]]; then
            echo "Found app.py template at $APP_PATH"
            cp "$APP_PATH" "app.py"
            FOUND_APP=true
            
            # Check for routes directory
            ROUTES_DIR=$(dirname "$APP_PATH")/routes
            if [[ -d "$ROUTES_DIR" ]]; then
                echo "Copying routes from $ROUTES_DIR"
                mkdir -p "routes"
                cp "$ROUTES_DIR"/* "routes/" 2>/dev/null
            fi
            
            break
        fi
    done
    
    if [[ "$FOUND_APP" == "false" ]]; then
        echo "ERROR: Could not find app.py template, node setup failed"
        return 1
    fi
    
    # Create .env file with node configuration
    cat > ".env" << EOF
GCN_NODE_NUM=$NODE_NUM
GCN_P2P_PORT=$P2P_PORT
GCN_WEB_PORT=$WEB_PORT
GCN_SYNC_THROTTLE=true
GCN_SYNC_INTERVAL=30
GCN_API_RATE_LIMIT=true
GCN_MAX_REQUESTS_PER_MINUTE=30
EOF
    
    # Create a version file to track setup
    echo "1.0.0" > "version.txt"
    
    echo "Node environment setup complete!"
    return 0
}

# Function to start the node
start_node() {
    echo "Starting node $NODE_NUM (P2P: $P2P_PORT, Web: $WEB_PORT)"
    cd "$NODE_DIR" || exit 1
    
    # Set environment variables
    export GCN_NODE_NUM=$NODE_NUM
    export GCN_P2P_PORT=$P2P_PORT
    export GCN_WEB_PORT=$WEB_PORT
    export GCN_SYNC_THROTTLE=true
    export GCN_SYNC_INTERVAL=30
    export GCN_API_RATE_LIMIT=true
    export GCN_MAX_REQUESTS_PER_MINUTE=30
    
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

# First set up the node environment
setup_node

# If setup-only flag is set, exit after setup
if [[ "$SETUP_ONLY" == "true" ]]; then
    echo "Setup complete, exiting without starting node (--setup-only flag set)"
    exit 0
fi

# Start the node if setup was successful
start_node

exit 0