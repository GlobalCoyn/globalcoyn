#!/bin/bash
# Enhanced Node Startup Script for GlobalCoyn
# This script provides robust node startup with dependency checks,
# better error handling, and fallback mechanisms for bootstrap nodes

# Default values
NODE_DIR="$PWD"
NODE_NUM=3
P2P_PORT=9001
WEB_PORT=8003
SETUP_ONLY=false
LOG_DIR="$HOME/Library/Logs/GlobalCoyn"
LOG_FILE="$LOG_DIR/node_startup.log"
DATA_DIR="$HOME/Documents/GlobalCoyn"
MAX_RETRIES=3
NODE_TIMEOUT=60  # seconds

# Bootstrap nodes - in order of preference
BOOTSTRAP_NODES=(
    "node1.globalcoyn.com:8001"
    "node2.globalcoyn.com:8001"
    "13.61.79.186:8001"
    "localhost:8001"
)

# Create log directory
mkdir -p "$LOG_DIR"
mkdir -p "$DATA_DIR"

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling function
handle_error() {
    log "ERROR: $1"
    echo "----------------------------------------"
    echo "ERROR: $1"
    echo "----------------------------------------"
    echo "Please see the log file at: $LOG_FILE"
    if [ "${2:-0}" -ne 0 ]; then
        exit "$2"
    fi
}

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
        --data-dir)
            DATA_DIR="$2"
            shift
            ;;
        --setup-only)
            SETUP_ONLY=true
            ;;
        --bootstrap-node)
            # Add custom bootstrap node to the beginning of the array (highest priority)
            BOOTSTRAP_NODES=("$2" "${BOOTSTRAP_NODES[@]}")
            shift
            ;;
        *)
            handle_error "Unknown parameter: $1" 1
            ;;
    esac
    shift
done

log "Starting GlobalCoyn node setup with the following parameters:"
log "- Node directory: $NODE_DIR"
log "- Node number: $NODE_NUM"
log "- P2P port: $P2P_PORT"
log "- Web port: $WEB_PORT"
log "- Data directory: $DATA_DIR"
log "- Setup only: $SETUP_ONLY"

# Create the node directory if it doesn't exist
if [[ ! -d "$NODE_DIR" ]]; then
    log "Creating node directory: $NODE_DIR"
    mkdir -p "$NODE_DIR" || handle_error "Failed to create node directory: $NODE_DIR" 1
fi

# Create the data directory if it doesn't exist
if [[ ! -d "$DATA_DIR" ]]; then
    log "Creating data directory: $DATA_DIR"
    mkdir -p "$DATA_DIR" || handle_error "Failed to create data directory: $DATA_DIR" 1
fi

# Function to check Python installation
check_python() {
    log "Checking Python installation..."
    if ! command -v python3 &> /dev/null; then
        handle_error "Python 3 is not installed. Please install Python 3 from python.org" 1
    fi
    
    local PYTHON_VERSION
    PYTHON_VERSION=$(python3 --version)
    log "Found $PYTHON_VERSION"
}

# Function to check and install required Python modules
check_python_modules() {
    local REQUIRED_MODULES=("flask" "requests")
    local MISSING_MODULES=()
    
    for MODULE in "${REQUIRED_MODULES[@]}"; do
        log "Checking for Python module: $MODULE"
        if ! python3 -c "import $MODULE" &> /dev/null; then
            log "Module $MODULE is missing, will try to install"
            MISSING_MODULES+=("$MODULE")
        fi
    done
    
    # Install missing modules if any
    if [ ${#MISSING_MODULES[@]} -gt 0 ]; then
        log "Installing missing modules: ${MISSING_MODULES[*]}"
        echo "Installing required Python modules..."
        
        # Try pip3 first
        if command -v pip3 &> /dev/null; then
            pip3 install --user "${MISSING_MODULES[@]}" || \
              handle_error "Failed to install modules with pip3" 1
        # Then try python3 -m pip
        elif python3 -m pip --version &> /dev/null; then
            python3 -m pip install --user "${MISSING_MODULES[@]}" || \
              handle_error "Failed to install modules with python -m pip" 1
        # Finally try to use get-pip.py if it exists
        elif [ -f "get-pip.py" ]; then
            log "pip not found, trying to install using get-pip.py"
            python3 "get-pip.py" --user || handle_error "Failed to install pip" 1
            python3 -m pip install --user "${MISSING_MODULES[@]}" || \
              handle_error "Failed to install modules after pip installation" 1
        else
            handle_error "pip is not available and get-pip.py not found, cannot install required modules" 1
        fi
        
        log "All required modules installed successfully"
    fi
}

# Function to check if a port is available
is_port_available() {
    local port=$1
    if command -v nc &> /dev/null; then
        nc -z localhost "$port" &> /dev/null
        if [ $? -eq 0 ]; then
            return 1  # Port is in use
        else
            return 0  # Port is available
        fi
    elif command -v python3 &> /dev/null; then
        # Use Python as a fallback to check port
        python3 - <<EOF
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(("127.0.0.1", $port))
    s.close()
    exit(0)  # Port is available
except:
    exit(1)  # Port is in use
EOF
    else
        # If neither nc nor Python is available, assume port is available
        return 0
    fi
}

# Function to find available ports
find_available_ports() {
    log "Checking for available ports..."
    local base_p2p=$P2P_PORT
    local base_web=$WEB_PORT
    local offset=0
    
    while [ $offset -lt 100 ]; do
        local test_p2p=$((base_p2p + offset))
        local test_web=$((base_web + offset))
        
        log "Testing port combination: P2P=$test_p2p, Web=$test_web"
        if is_port_available "$test_p2p" && is_port_available "$test_web"; then
            P2P_PORT=$test_p2p
            WEB_PORT=$test_web
            log "Found available ports: P2P=$P2P_PORT, Web=$WEB_PORT"
            return 0
        fi
        
        offset=$((offset + 1))
    done
    
    handle_error "Could not find available port combination after 100 attempts" 1
}

# Function to check connectivity to bootstrap nodes
check_bootstrap_connectivity() {
    log "Checking connectivity to bootstrap nodes..."
    local connected=false
    
    for node in "${BOOTSTRAP_NODES[@]}"; do
        local host=${node%:*}
        local port=${node#*:}
        
        log "Testing connectivity to bootstrap node: $host:$port"
        
        # Try to connect to the node
        if command -v curl &> /dev/null; then
            if curl -s -m 5 "http://$host:$port/api/status" &> /dev/null; then
                log "Successfully connected to bootstrap node: $node"
                connected=true
                break
            fi
        elif command -v python3 &> /dev/null; then
            # Use Python as a fallback
            if python3 - <<EOF &> /dev/null
import urllib.request
import socket
socket.setdefaulttimeout(5)
try:
    urllib.request.urlopen("http://$host:$port/api/status")
    exit(0)  # Connection successful
except:
    exit(1)  # Connection failed
EOF
            then
                log "Successfully connected to bootstrap node: $node"
                connected=true
                break
            fi
        fi
        
        log "Failed to connect to bootstrap node: $node"
    done
    
    if [ "$connected" = false ]; then
        log "WARNING: Could not connect to any bootstrap nodes"
        return 1
    fi
    
    return 0
}

# Setup function to prepare the node environment
setup_node() {
    log "Setting up node environment at $NODE_DIR"
    cd "$NODE_DIR" || handle_error "Failed to change to node directory: $NODE_DIR" 1
    
    # Check if app.py already exists
    if [[ -f "app.py" ]]; then
        log "app.py already exists, checking if it needs to be updated"
        
        # Check app.py version or timestamp to see if we need to update
        local update_needed=false
        if [[ ! -f "version.txt" ]]; then
            update_needed=true
        else
            local current_version
            current_version=$(cat version.txt)
            if [[ "$current_version" != "1.0.0" ]]; then
                update_needed=true
            fi
        fi
        
        if [[ "$update_needed" == "false" ]]; then
            log "Node files appear to be up to date, skipping setup"
            return 0
        else
            log "Node files need updating"
        fi
    fi
    
    log "Creating or updating node configuration files..."
    
    # First, ensure core directory exists and has required files
    mkdir -p "core"
    
    # Look for core module files in a few possible locations
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
    APP_DIR="$SCRIPT_DIR"
    
    # Potential core module locations
    CORE_LOCATIONS=(
        "$APP_DIR/core"
        "$SCRIPT_DIR/../core"
        "$PROJECT_DIR/core"
        "$PROJECT_DIR/blockchain/core"
        "$PROJECT_DIR/nodes/node1/core"
    )
    
    # Try a more exhaustive search if needed
    if [ ! -d "${CORE_LOCATIONS[0]}" ]; then
        log "Standard core locations not found, performing recursive search"
        # Try to find core directory with blockchain.py
        for location in "$APP_DIR" "$SCRIPT_DIR" "$PROJECT_DIR"; do
            if [ -d "$location" ]; then
                potential_core=$(find "$location" -type d -name "core" -exec test -f {}/blockchain.py \; -print -quit 2>/dev/null)
                if [ -n "$potential_core" ]; then
                    log "Found core directory in recursive search: $potential_core"
                    CORE_LOCATIONS=("$potential_core" "${CORE_LOCATIONS[@]}")
                    break
                fi
            fi
        done
    fi
    
    FOUND_CORE=false
    for CORE_PATH in "${CORE_LOCATIONS[@]}"; do
        if [[ -d "$CORE_PATH" ]]; then
            log "Found core modules at $CORE_PATH"
            
            # Copy core files
            for FILE in blockchain.py coin.py wallet.py price_oracle.py; do
                if [[ -f "$CORE_PATH/$FILE" ]]; then
                    log "Copying $FILE to core directory"
                    cp "$CORE_PATH/$FILE" "core/"
                else
                    log "WARNING: Core file $FILE not found at $CORE_PATH"
                fi
            done
            
            FOUND_CORE=true
            break
        fi
    done
    
    if [[ "$FOUND_CORE" == "false" ]]; then
        handle_error "Could not find core modules, node will not function correctly" 1
    fi
    
    # Create __init__.py in core directory
    touch "core/__init__.py"
    
    # Create routes directory and files if they don't exist
    mkdir -p "routes"
    touch "routes/__init__.py"
    
    # Look for route files in standard locations
    ROUTES_LOCATIONS=(
        "$APP_DIR/routes"
        "$SCRIPT_DIR/../routes"
        "$PROJECT_DIR/routes"
        "$PROJECT_DIR/blockchain/api/routes"
        "$PROJECT_DIR/nodes/node1/routes"
    )
    
    FOUND_ROUTES=false
    for ROUTES_PATH in "${ROUTES_LOCATIONS[@]}"; do
        if [[ -d "$ROUTES_PATH" ]]; then
            log "Found routes at $ROUTES_PATH"
            # Copy all route files (except __init__.py which we already created)
            find "$ROUTES_PATH" -name "*.py" -not -name "__init__.py" -exec cp {} "routes/" \;
            FOUND_ROUTES=true
            break
        fi
    done
    
    if [[ "$FOUND_ROUTES" == "false" ]]; then
        # Create minimal route files if not found
        log "WARNING: Could not find route files, creating minimal versions"
        
        # Create network.py
        cat > "routes/network.py" << 'EOF'
from flask import Blueprint, jsonify, request
import os
import json

network_bp = Blueprint('network', __name__)

@network_bp.route('/status', methods=['GET'])
def get_status():
    """Get the status of this node"""
    return jsonify({
        'status': 'online',
        'node_id': os.environ.get('GCN_NODE_NUM', '3'),
        'p2p_port': os.environ.get('GCN_P2P_PORT', '9001')
    })

@network_bp.route('/peers', methods=['GET'])
def get_peers():
    """Get the list of known peers"""
    return jsonify({'peers': []})

@network_bp.route('/connect', methods=['POST'])
def connect_to_peer():
    """Connect to a new peer"""
    data = request.json
    return jsonify({'success': True, 'message': 'Connection request received'})
EOF

        # Create transactions.py
        cat > "routes/transactions.py" << 'EOF'
from flask import Blueprint, jsonify, request

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/mempool', methods=['GET'])
def get_mempool():
    """Get the current mempool transactions"""
    return jsonify({'mempool': []})

@transactions_bp.route('/submit', methods=['POST'])
def submit_transaction():
    """Submit a new transaction"""
    return jsonify({'success': True, 'message': 'Transaction received'})
EOF
    fi
    
    # Look for app.py template
    APP_TEMPLATE_LOCATIONS=(
        "$APP_DIR/app.py"
        "$SCRIPT_DIR/../node_template/app.py"
        "$PROJECT_DIR/node_template/app.py"
        "$PROJECT_DIR/nodes/node1/app.py"
        "$PROJECT_DIR/blockchain/nodes/node1/app.py"
    )
    
    FOUND_APP=false
    for APP_PATH in "${APP_TEMPLATE_LOCATIONS[@]}"; do
        if [[ -f "$APP_PATH" ]]; then
            log "Found app.py template at $APP_PATH"
            cp "$APP_PATH" "app.py"
            FOUND_APP=true
            break
        fi
    done
    
    if [[ "$FOUND_APP" == "false" ]]; then
        log "Could not find app.py template, creating a basic one"
        
        # Create a basic app.py
        cat > "app.py" << 'EOF'
#!/usr/bin/env python3
"""
GlobalCoyn Node
--------------
A node in the GlobalCoyn blockchain network.
"""

import os
import sys
import json
import logging
from flask import Flask, jsonify, request
from routes.network import network_bp
from routes.transactions import transactions_bp

# Configure logging
logging.basicConfig(
    filename='node.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('globalcoyn-node')

# Create the Flask app
app = Flask(__name__)

# Register blueprints
app.register_blueprint(network_bp, url_prefix='/api/network')
app.register_blueprint(transactions_bp, url_prefix='/api/transactions')

# Basic routes
@app.route('/api/status', methods=['GET'])
def status():
    """Return the status of this node"""
    return jsonify({
        'status': 'online',
        'node_id': os.environ.get('GCN_NODE_NUM', '3'),
        'version': '1.0.0'
    })

@app.route('/api/blockchain', methods=['GET'])
def get_blockchain():
    """Return the current blockchain"""
    return jsonify({
        'length': 1,
        'chain': [{
            'index': 0,
            'timestamp': 0,
            'transactions': [],
            'proof': 0,
            'previous_hash': '0'
        }]
    })

if __name__ == '__main__':
    # Get environment variables or use defaults
    node_num = os.environ.get('GCN_NODE_NUM', '3')
    p2p_port = int(os.environ.get('GCN_P2P_PORT', '9001'))
    web_port = int(os.environ.get('GCN_WEB_PORT', '8003'))
    
    logger.info(f"Starting node {node_num} on P2P port {p2p_port}, Web port {web_port}")
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=web_port, debug=False, threaded=True)
EOF
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
    
    # Create a node_config.json file with more detailed configuration
    cat > "node_config.json" << EOF
{
    "node_number": $NODE_NUM,
    "p2p_port": $P2P_PORT,
    "web_port": $WEB_PORT,
    "data_dir": "$DATA_DIR",
    "bootstrap_nodes": [
        "${BOOTSTRAP_NODES[0]}",
        "${BOOTSTRAP_NODES[1]}"
    ],
    "sync_interval": 30,
    "max_peers": 10,
    "mining_enabled": true,
    "mining_threads": 1,
    "mining_difficulty": "auto",
    "last_updated": "$(date +%s)"
}
EOF
    
    log "Node environment setup complete!"
    return 0
}

# Function to start the node
start_node() {
    log "Starting node $NODE_NUM (P2P: $P2P_PORT, Web: $WEB_PORT)"
    cd "$NODE_DIR" || handle_error "Failed to change to node directory: $NODE_DIR" 1
    
    # Set environment variables
    export GCN_NODE_NUM=$NODE_NUM
    export GCN_P2P_PORT=$P2P_PORT
    export GCN_WEB_PORT=$WEB_PORT
    export GCN_SYNC_THROTTLE=true
    export GCN_SYNC_INTERVAL=30
    export GCN_API_RATE_LIMIT=true
    export GCN_MAX_REQUESTS_PER_MINUTE=30
    export GCN_DATA_DIR="$DATA_DIR"
    
    # Update node_config.json with current settings
    if [[ -f "node_config.json" ]]; then
        local temp_file
        temp_file="node_config.json.tmp"
        
        # Use Python to update the JSON file properly
        python3 - <<EOF
import json
try:
    with open('node_config.json', 'r') as f:
        config = json.load(f)
    
    # Update with current settings
    config['node_number'] = $NODE_NUM
    config['p2p_port'] = $P2P_PORT
    config['web_port'] = $WEB_PORT
    config['data_dir'] = "$DATA_DIR"
    config['bootstrap_nodes'] = ["${BOOTSTRAP_NODES[0]}", "${BOOTSTRAP_NODES[1]}"]
    config['last_updated'] = "$(date +%s)"
    
    with open('node_config.json.tmp', 'w') as f:
        json.dump(config, f, indent=4)
    
    exit(0)
except Exception as e:
    print(f"Error updating node_config.json: {str(e)}")
    exit(1)
EOF
        # Replace the original file if update was successful
        if [ $? -eq 0 ]; then
            mv "$temp_file" "node_config.json"
        else
            log "WARNING: Failed to update node_config.json"
        fi
    fi
    
    # Try to connect to bootstrap nodes before starting
    check_bootstrap_connectivity
    if [ $? -ne 0 ]; then
        log "WARNING: Could not connect to any bootstrap nodes. The node may run in isolated mode."
    fi
    
    # Start the node with retry logic
    local retry_count=0
    local node_started=false
    
    while [ $retry_count -lt $MAX_RETRIES ] && [ "$node_started" = false ]; do
        log "Starting node (attempt $((retry_count + 1))/$MAX_RETRIES)..."
        
        # Start the node in background
        python3 app.py > "$LOG_DIR/node_output.log" 2>&1 &
        local PID=$!
        log "Node started with PID $PID"
        
        # Wait for node to initialize
        log "Waiting for node to initialize (up to $NODE_TIMEOUT seconds)..."
        local wait_time=0
        local node_ready=false
        
        while [ $wait_time -lt $NODE_TIMEOUT ] && [ "$node_ready" = false ]; do
            # Check if process is still running
            if ! kill -0 $PID 2>/dev/null; then
                log "Node process exited unexpectedly"
                break
            fi
            
            # Try to connect to the node API
            if curl -s "http://localhost:$WEB_PORT/api/status" > /dev/null 2>&1; then
                log "Node is running and API is accessible"
                node_ready=true
                node_started=true
                break
            fi
            
            # Wait and increment counter
            sleep 1
            wait_time=$((wait_time + 1))
        done
        
        if [ "$node_ready" = false ]; then
            log "Node failed to start properly in $NODE_TIMEOUT seconds"
            # Kill the process if it's still running
            if kill -0 $PID 2>/dev/null; then
                log "Terminating node process $PID"
                kill $PID
                sleep 1
                # Force kill if still running
                if kill -0 $PID 2>/dev/null; then
                    kill -9 $PID
                fi
            fi
            
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $MAX_RETRIES ]; then
                log "Retrying in 5 seconds..."
                sleep 5
            fi
        fi
    done
    
    if [ "$node_started" = false ]; then
        handle_error "Failed to start node after $MAX_RETRIES attempts" 1
    fi
    
    log "Node started successfully!"
    return 0
}

# Function to check if node is running
check_node() {
    log "Checking node $NODE_NUM..."
    local status_output
    status_output=$(curl -s "http://localhost:$WEB_PORT/api/status" 2>/dev/null)
    
    if [ -n "$status_output" ]; then
        log "Node is running: $status_output"
        return 0
    else
        log "Node is not running or not accessible"
        return 1
    fi
}

# Main execution logic

# Check Python installation
check_python

# Check and install required Python modules
check_python_modules

# Find available ports if needed
find_available_ports

# First set up the node environment
setup_node

# If setup-only flag is set, exit after setup
if [[ "$SETUP_ONLY" == "true" ]]; then
    log "Setup complete, exiting without starting node (--setup-only flag set)"
    exit 0
fi

# Start the node if setup was successful
start_node

# Check if node is running
check_node

log "Node setup and startup complete"
exit 0