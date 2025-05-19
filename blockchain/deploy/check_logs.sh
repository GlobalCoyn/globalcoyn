#!/bin/bash
# Script to check blockchain node logs and fix issues

echo "Getting detailed service logs..."
sudo journalctl -u globalcoyn-node -n 100 --no-pager

echo "Checking Python dependencies..."
pip3 list | grep -E "flask|cors|requests|cryptography"

echo "Checking if port 8001 has any conflicts..."
sudo lsof -i :8001

echo "Examining app.py for errors..."
cd /var/www/globalcoyn/blockchain/node/
if [ -f app.py ]; then
  grep -n "except" app.py | head -n 20
  echo "First 20 lines of app.py:"
  head -n 20 app.py
else
  echo "app.py not found in expected location"
fi

echo "Checking import paths..."
python3 -c "import sys; print(sys.path)"

echo "Testing Python can import Flask..."
python3 -c "import flask; print(f'Flask version: {flask.__version__}')" || echo "Flask import failed"

echo "Attempting a manual restart with more verbose output..."
cd /var/www/globalcoyn/blockchain/node/
sudo systemctl stop globalcoyn-node
sleep 2
export GCN_ENV=production 
export GCN_NODE_NUM=1
export GCN_P2P_PORT=9000
export GCN_WEB_PORT=8001
export GCN_DOMAIN=globalcoyn.com
export GCN_USE_SSL=true
PYTHONPATH=/var/www/globalcoyn/blockchain python3 -v app.py > startup_debug.log 2>&1 &
echo "Started app in background, check startup_debug.log for details"

echo "Checking app.py permissions..."
ls -la app.py