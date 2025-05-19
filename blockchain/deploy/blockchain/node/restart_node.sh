#!/bin/bash

# Default node number and ports
NODE_NUM=${1:-1}
export GCN_NODE_NUM=$NODE_NUM
export GCN_P2P_PORT=$((9000 + $NODE_NUM - 1))
export GCN_WEB_PORT=$((8000 + $NODE_NUM))

echo "Restarting GlobalCoyn node $NODE_NUM"
echo "P2P Port: $GCN_P2P_PORT"
echo "Web Port: $GCN_WEB_PORT"

# Kill any existing Python processes using these ports
echo "Checking for existing processes..."

# Find processes using the web port
WEB_PIDS=$(lsof -i :$GCN_WEB_PORT -t)
if [ -n "$WEB_PIDS" ]; then
    echo "Killing processes using web port $GCN_WEB_PORT: $WEB_PIDS"
    kill -9 $WEB_PIDS
fi

# Find processes using the P2P port
P2P_PIDS=$(lsof -i :$GCN_P2P_PORT -t)
if [ -n "$P2P_PIDS" ]; then
    echo "Killing processes using P2P port $GCN_P2P_PORT: $P2P_PIDS"
    kill -9 $P2P_PIDS
fi

# Find any node_*.log files and clean them
echo "Cleaning old log files..."
rm -f node_${NODE_NUM}.log

# Now start the node
echo "Starting node..."
./start_node.sh $NODE_NUM

echo "Node $NODE_NUM restarted. Check node_${NODE_NUM}.log for output."
echo "API is accessible at http://localhost:$GCN_WEB_PORT"