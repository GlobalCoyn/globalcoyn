#!/bin/bash

# Production Contract-Enabled Restart Script for Bootstrap Nodes
# This script restarts bootstrap nodes with proper contract functionality

echo "=== GlobalCoyn Production Contract Restart ==="

# Function to restart a bootstrap node with contract support
restart_bootstrap_node() {
    local node_num=$1
    local node_dir="/home/ec2-user/bootstrap_node_${node_num}"
    local p2p_port=$((9000 + node_num - 1))
    local web_port=$((8001 + node_num - 1))
    
    echo "Restarting Bootstrap Node $node_num..."
    echo "Directory: $node_dir"
    echo "P2P Port: $p2p_port"
    echo "Web Port: $web_port"
    
    # Kill existing processes for this node
    echo "Stopping existing processes for node $node_num..."
    pkill -f "python3.*app.py.*$web_port" || true
    lsof -i :$web_port -t | xargs kill -9 2>/dev/null || true
    lsof -i :$p2p_port -t | xargs kill -9 2>/dev/null || true
    
    # Wait for ports to be released
    sleep 3
    
    # Check if node directory exists
    if [ ! -d "$node_dir" ]; then
        echo "ERROR: Node directory $node_dir does not exist"
        return 1
    fi
    
    # Change to node directory
    cd "$node_dir"
    
    # Verify required files exist
    if [ ! -f "app.py" ]; then
        echo "ERROR: app.py not found in $node_dir"
        return 1
    fi
    
    if [ ! -f "core/globalcoyn_blockchain.py" ]; then
        echo "WARNING: globalcoyn_blockchain.py not found, checking for blockchain.py..."
        if [ ! -f "core/blockchain.py" ]; then
            echo "ERROR: No blockchain module found in $node_dir/core/"
            return 1
        fi
    fi
    
    # Set up environment variables
    export PYTHONPATH="$node_dir:$node_dir/core:$PYTHONPATH"
    export GCN_NODE_NUM=$node_num
    export GCN_P2P_PORT=$p2p_port
    export GCN_WEB_PORT=$web_port
    export GCN_ENV="production"
    export GCN_BOOTSTRAP_MODE=true
    export GCN_ENABLE_MINING=true
    export GCN_DOMAIN="globalcoyn.com"
    
    echo "Environment set:"
    echo "  PYTHONPATH: $PYTHONPATH"
    echo "  GCN_NODE_NUM: $GCN_NODE_NUM"
    echo "  GCN_P2P_PORT: $GCN_P2P_PORT"
    echo "  GCN_WEB_PORT: $GCN_WEB_PORT"
    echo "  GCN_ENV: $GCN_ENV"
    
    # Start the node in background
    echo "Starting Bootstrap Node $node_num with contract support..."
    nohup python3 app.py > "bootstrap_node_${node_num}_contract.log" 2>&1 &
    
    local node_pid=$!
    echo "Bootstrap Node $node_num started with PID: $node_pid"
    
    # Wait a moment for startup
    sleep 5
    
    # Test if the node is responding
    local max_attempts=6
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Testing node $node_num (attempt $attempt/$max_attempts)..."
        
        if curl -s "http://localhost:$web_port/api/blockchain" > /dev/null 2>&1; then
            echo "✅ Bootstrap Node $node_num is responding"
            
            # Test contract functionality
            if curl -s "http://localhost:$web_port/api/contracts/types" > /dev/null 2>&1; then
                echo "✅ Bootstrap Node $node_num contract functionality working"
                return 0
            else
                echo "⚠️  Bootstrap Node $node_num responding but contracts not working"
                return 1
            fi
        else
            echo "⚠️  Bootstrap Node $node_num not responding yet, waiting..."
            sleep 5
            attempt=$((attempt + 1))
        fi
    done
    
    echo "❌ Bootstrap Node $node_num failed to start properly"
    return 1
}

# Function to test contract deployment
test_contract_deployment() {
    local web_port=$1
    local node_name="Node $((web_port - 8000))"
    
    echo "Testing contract deployment on $node_name (port $web_port)..."
    
    local response=$(curl -s -X POST "http://localhost:$web_port/api/contracts/templates/token" \
        -H "Content-Type: application/json" \
        -d '{
            "creator": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "name": "ProductionTestToken",
            "symbol": "PTT",
            "initial_supply": 1000000,
            "fee": 100
        }')
    
    if echo "$response" | grep -q '"status":"success"'; then
        echo "✅ $node_name contract deployment working!"
        return 0
    else
        echo "❌ $node_name contract deployment failed:"
        echo "$response"
        return 1
    fi
}

# Main execution
echo "Starting production contract-enabled restart..."

# Stop systemd services first
echo "Stopping systemd services..."
sudo systemctl stop globalcoyn-bootstrap1.service || true
sudo systemctl stop globalcoyn-bootstrap2.service || true

# Wait for services to stop
sleep 5

# Restart both bootstrap nodes
echo "Restarting bootstrap nodes with contract support..."

restart_bootstrap_node 1
node1_status=$?

restart_bootstrap_node 2
node2_status=$?

# Wait for both nodes to fully start
echo "Waiting for nodes to fully initialize..."
sleep 10

# Test both nodes
echo "Testing contract functionality..."

if [ $node1_status -eq 0 ]; then
    test_contract_deployment 8001
    node1_contract_status=$?
else
    echo "❌ Node 1 startup failed, skipping contract test"
    node1_contract_status=1
fi

if [ $node2_status -eq 0 ]; then
    test_contract_deployment 8002
    node2_contract_status=$?
else
    echo "❌ Node 2 startup failed, skipping contract test"
    node2_contract_status=1
fi

# Summary
echo ""
echo "=== Restart Summary ==="
if [ $node1_status -eq 0 ] && [ $node1_contract_status -eq 0 ]; then
    echo "✅ Bootstrap Node 1: SUCCESS (contracts working)"
else
    echo "❌ Bootstrap Node 1: FAILED"
fi

if [ $node2_status -eq 0 ] && [ $node2_contract_status -eq 0 ]; then
    echo "✅ Bootstrap Node 2: SUCCESS (contracts working)"
else
    echo "❌ Bootstrap Node 2: FAILED"
fi

# Final test with domain
echo ""
echo "Testing domain endpoint..."
if curl -s "https://globalcoyn.com/api/contracts/types" > /dev/null 2>&1; then
    echo "✅ Domain contract endpoint working"
else
    echo "⚠️  Domain contract endpoint not working (may be nginx routing)"
fi

if [ $node1_contract_status -eq 0 ] || [ $node2_contract_status -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS: At least one node has working contract functionality!"
    exit 0
else
    echo ""
    echo "💥 FAILED: Contract functionality not working on any node"
    exit 1
fi