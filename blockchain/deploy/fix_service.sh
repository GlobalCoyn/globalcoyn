#!/bin/bash
# Script to fix GlobalCoyn node service issues

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}GlobalCoyn Node Service Fix Script${NC}"
echo "================================================================"

# Stop the service if it's running
echo -e "${BLUE}Stopping existing service...${NC}"
sudo systemctl stop globalcoyn-node

# Check for Python dependencies
echo -e "${BLUE}Installing required Python dependencies...${NC}"
sudo pip3 install flask flask-cors requests cryptography python-dotenv

# Fix paths and permissions
echo -e "${BLUE}Setting proper permissions and ownership...${NC}"
sudo chown -R deploy:deploy /var/www/globalcoyn/blockchain
sudo chmod -R 755 /var/www/globalcoyn/blockchain
sudo chmod +x /var/www/globalcoyn/blockchain/node/app.py

# Fix parent module imports
echo -e "${BLUE}Creating __init__.py files for proper Python module imports...${NC}"
sudo touch /var/www/globalcoyn/blockchain/__init__.py
sudo touch /var/www/globalcoyn/blockchain/core/__init__.py
sudo touch /var/www/globalcoyn/blockchain/node/__init__.py
sudo chown deploy:deploy /var/www/globalcoyn/blockchain/__init__.py
sudo chown deploy:deploy /var/www/globalcoyn/blockchain/core/__init__.py
sudo chown deploy:deploy /var/www/globalcoyn/blockchain/node/__init__.py

# Check if routes directory exists
if [ ! -d "/var/www/globalcoyn/blockchain/node/routes" ]; then
    echo -e "${RED}Routes directory missing! Creating it...${NC}"
    sudo mkdir -p /var/www/globalcoyn/blockchain/node/routes
    sudo touch /var/www/globalcoyn/blockchain/node/routes/__init__.py
    sudo chown -R deploy:deploy /var/www/globalcoyn/blockchain/node/routes
fi

# Create production configuration
echo -e "${BLUE}Ensuring production_config.json exists...${NC}"
if [ ! -f "/var/www/globalcoyn/blockchain/node/production_config.json" ]; then
    echo -e "${RED}Creating production_config.json...${NC}"
    cat > temp_config.json << 'EOF'
{
  "node": {
    "id": 1,
    "p2p_port": 9000,
    "web_port": 8001,
    "host": "0.0.0.0",
    "domain": "globalcoyn.com",
    "use_ssl": true
  },
  "blockchain": {
    "difficulty_adjustment_interval": 2016,
    "target_block_time": 600,
    "initial_difficulty_bits": 20,
    "reward_halving_interval": 210000,
    "initial_mining_reward": 50
  },
  "wallet": {
    "minimum_transaction_fee": 0.0001
  },
  "network": {
    "seed_nodes": [
      {"host": "globalcoyn.com", "p2p_port": 9000},
      {"host": "13.61.79.186", "p2p_port": 9000}
    ]
  },
  "security": {
    "cors_origins": [
      "https://globalcoyn.com",
      "https://www.globalcoyn.com"
    ],
    "api_rate_limit": 100
  }
}
EOF
    sudo mv temp_config.json /var/www/globalcoyn/blockchain/node/production_config.json
    sudo chown deploy:deploy /var/www/globalcoyn/blockchain/node/production_config.json
fi

# Update service file
echo -e "${BLUE}Updating service file...${NC}"
cat > globalcoyn-node.service << 'EOF'
[Unit]
Description=GlobalCoyn Blockchain Node
After=network.target

[Service]
User=deploy
Group=deploy
WorkingDirectory=/var/www/globalcoyn/blockchain/node
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/var/www/globalcoyn/blockchain"
Environment="GCN_ENV=production"
Environment="GCN_NODE_NUM=1"
Environment="GCN_P2P_PORT=9000"
Environment="GCN_WEB_PORT=8001"
Environment="GCN_DOMAIN=globalcoyn.com"
Environment="GCN_USE_SSL=true"
Type=simple
ExecStart=/usr/bin/python3 /var/www/globalcoyn/blockchain/node/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo mv globalcoyn-node.service /etc/systemd/system/globalcoyn-node.service

# Reload systemd
echo -e "${BLUE}Reloading systemd and starting service...${NC}"
sudo systemctl daemon-reload

# Start service
sudo systemctl start globalcoyn-node
sleep 5

# Check if service is running
if systemctl is-active --quiet globalcoyn-node; then
    echo -e "${GREEN}✓ Service started successfully${NC}"
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo "Checking logs:"
    sudo journalctl -u globalcoyn-node -n 50 --no-pager
fi

# Check if application is responding
echo -e "${BLUE}Testing API endpoint...${NC}"
curl -s http://localhost:8001/api/blockchain/ || echo "API not responding"

echo -e "${GREEN}Fix script completed!${NC}"
echo "If issues persist, try manually running the application with:"
echo "cd /var/www/globalcoyn/blockchain/node && PYTHONPATH=/var/www/globalcoyn/blockchain GCN_ENV=production python3 app.py"