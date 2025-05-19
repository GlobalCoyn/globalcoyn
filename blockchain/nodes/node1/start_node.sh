#!/bin/bash
# Blockchain Node Startup Script

# Fixed configuration for Node 1
NODE_NUM=1
P2P_PORT=9000
WEB_PORT=8001

echo "Starting Blockchain Node $NODE_NUM"
echo "P2P Port: $P2P_PORT"
echo "Web Port: $WEB_PORT"

# Kill any existing processes using the ports
echo "Checking for existing processes on ports $WEB_PORT and $P2P_PORT..."
PID_WEB=$(lsof -ti:$WEB_PORT)
if [ -n "$PID_WEB" ]; then
  echo "Killing existing process on port $WEB_PORT (PID: $PID_WEB)"
  kill -9 $PID_WEB
fi

PID_P2P=$(lsof -ti:$P2P_PORT)
if [ -n "$PID_P2P" ]; then
  echo "Killing existing process on port $P2P_PORT (PID: $PID_P2P)"
  kill -9 $PID_P2P
fi

# Wait a moment for ports to be released
sleep 1

# Set environment variables
export GCN_NODE_NUM=$NODE_NUM
export GCN_P2P_PORT=$P2P_PORT
export GCN_WEB_PORT=$WEB_PORT

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Start the node
echo "Starting Node $NODE_NUM..."
python3 app.py

# Deactivate virtual environment when done
if [ -d "venv" ]; then
    deactivate
fi