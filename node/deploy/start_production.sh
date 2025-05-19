#!/bin/bash

# Start GlobalCoyn blockchain node in production mode
export GCN_ENV="production"
export GCN_NODE_NUM=1
export GCN_P2P_PORT=9000
export GCN_WEB_PORT=8001
export GCN_DATA_FILE="blockchain_data.json"
export GCN_DOMAIN="globalcoyn.com"
export GCN_USE_SSL="true"

# Make sure we're in the right directory
cd "$(dirname "$0")/.."

# Setup Python path
CURRENT_DIR=$(pwd)
PARENT_DIR=$(dirname "$CURRENT_DIR")
BLOCKCHAIN_DIR=$(dirname "$PARENT_DIR")
CORE_DIR="$BLOCKCHAIN_DIR/core"
ROOT_DIR=$(dirname "$BLOCKCHAIN_DIR")

export PYTHONPATH="$ROOT_DIR:$CURRENT_DIR:$CORE_DIR:$BLOCKCHAIN_DIR:$PYTHONPATH"

# Start the Flask app
echo "Starting GlobalCoyn node in production mode..."
echo "P2P Port: $GCN_P2P_PORT"
echo "Web Port: $GCN_WEB_PORT"
echo "Domain: $GCN_DOMAIN"

# Use nohup to keep the app running after the terminal closes
nohup python3 -u app.py > node_production.log 2>&1 &

echo "Node started. Check node_production.log for output."
echo "API is accessible at https://$GCN_DOMAIN/api/"
echo "PID: $!"