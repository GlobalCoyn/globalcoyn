#!/bin/bash
# Final fix script for GlobalCoyn blockchain node

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}GlobalCoyn Node Final Fix Script${NC}"
echo "================================================================"

# Stop the service if it's running
echo -e "${BLUE}Stopping existing service...${NC}"
sudo systemctl stop globalcoyn-node

# Verify required directories
echo -e "${BLUE}Verifying required directories...${NC}"
INSTALL_DIR="/var/www/globalcoyn/blockchain"
CORE_DIR="${INSTALL_DIR}/core"
NODE_DIR="${INSTALL_DIR}/node"

if [ ! -d "$CORE_DIR" ]; then
    echo -e "${RED}Core directory missing! Expected at: $CORE_DIR${NC}"
    echo "Please check that the blockchain core modules are installed."
    exit 1
fi

# Check for vital core files
for file in blockchain.py transaction.py block.py wallet.py; do
    if [ ! -f "${CORE_DIR}/$file" ]; then
        echo -e "${RED}Missing core file: ${CORE_DIR}/$file${NC}"
        echo "Please ensure the blockchain core modules are installed correctly."
        exit 1
    fi
done

# Create symlinks from the core directory to Python path
echo -e "${BLUE}Creating symlinks for core modules...${NC}"
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
echo "Site packages directory: $SITE_PACKAGES"

# Create a blockchain directory in site-packages
sudo mkdir -p $SITE_PACKAGES/blockchain
sudo mkdir -p $SITE_PACKAGES/blockchain/core

# Create __init__.py files
sudo touch $SITE_PACKAGES/blockchain/__init__.py
sudo touch $SITE_PACKAGES/blockchain/core/__init__.py

# Link core files to site-packages
for file in $CORE_DIR/*.py; do
    filename=$(basename $file)
    sudo ln -sf $file $SITE_PACKAGES/blockchain/core/$filename
    echo "Linked: $file -> $SITE_PACKAGES/blockchain/core/$filename"
    
    # Also create direct links for the main modules
    sudo ln -sf $file $SITE_PACKAGES/$filename
    echo "Linked: $file -> $SITE_PACKAGES/$filename"
done

# Create direct import wrapper
echo -e "${BLUE}Creating direct import wrapper...${NC}"
WRAPPER_PATH="${NODE_DIR}/direct_import_app.py"
cat > direct_import_app.py << 'EOF'
#!/usr/bin/env python3
"""
Direct import wrapper for GlobalCoyn blockchain node app.py
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("wrapper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("wrapper")

logger.info("Starting GlobalCoyn blockchain node wrapper")

# Get directories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
core_dir = os.path.join(parent_dir, "core")

logger.info(f"Current directory: {current_dir}")
logger.info(f"Parent directory: {parent_dir}")
logger.info(f"Core directory: {core_dir}")

# Add to path
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, core_dir)

logger.info(f"Python path: {sys.path}")

# List core directory contents
logger.info(f"Core directory contents: {os.listdir(core_dir)}")

# Import core modules directly
try:
    logger.info("Attempting direct import of core modules...")
    
    # Import directly from the core directory
    from blockchain import Blockchain
    from transaction import Transaction
    from block import Block
    from wallet import Wallet
    from mempool import Mempool
    from mining import Miner
    from utils import bits_to_target, target_to_bits, validate_address_format
    from coin import Coin, CoinManager
    
    logger.info("Successfully imported core modules directly")
    
    # Define globals
    globals_dict = {
        "Blockchain": Blockchain,
        "Transaction": Transaction,
        "Block": Block,
        "Wallet": Wallet,
        "Mempool": Mempool,
        "Miner": Miner,
        "bits_to_target": bits_to_target,
        "target_to_bits": target_to_bits,
        "validate_address_format": validate_address_format,
        "Coin": Coin,
        "CoinManager": CoinManager
    }
    
    # Execute the original app.py with our pre-imported modules
    logger.info("Executing app.py with pre-imported modules...")
    app_path = os.path.join(current_dir, "app.py")
    with open(app_path) as f:
        code = compile(f.read(), app_path, 'exec')
        exec(code, globals_dict)
        
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    sys.exit(1)
EOF

sudo mv direct_import_app.py $WRAPPER_PATH
sudo chmod 755 $WRAPPER_PATH
sudo chown deploy:deploy $WRAPPER_PATH
echo -e "${GREEN}Created wrapper script: $WRAPPER_PATH${NC}"

# Update service file
echo -e "${BLUE}Updating service file...${NC}"
SERVICE_FILE="/etc/systemd/system/globalcoyn-node.service"
cat > temp_service << 'EOF'
[Unit]
Description=GlobalCoyn Blockchain Node
After=network.target

[Service]
User=deploy
Group=deploy
WorkingDirectory=/var/www/globalcoyn/blockchain/node
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/var/www/globalcoyn/blockchain:/var/www/globalcoyn/blockchain/core"
Environment="GCN_ENV=production"
Environment="GCN_NODE_NUM=1"
Environment="GCN_P2P_PORT=9000"
Environment="GCN_WEB_PORT=8001"
Environment="GCN_DOMAIN=globalcoyn.com"
Environment="GCN_USE_SSL=true"
Type=simple
ExecStart=/usr/bin/python3 /var/www/globalcoyn/blockchain/node/direct_import_app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo mv temp_service $SERVICE_FILE
echo -e "${GREEN}Updated service file: $SERVICE_FILE${NC}"

# Fix ownership
echo -e "${BLUE}Setting proper permissions...${NC}"
sudo chown -R deploy:deploy $INSTALL_DIR
sudo chmod -R 755 $INSTALL_DIR

# Reload systemd
echo -e "${BLUE}Reloading systemd and starting service...${NC}"
sudo systemctl daemon-reload
sudo systemctl start globalcoyn-node
sleep 5

# Check if service is running
if systemctl is-active --quiet globalcoyn-node; then
    echo -e "${GREEN}✓ Service started successfully${NC}"
    sudo systemctl status globalcoyn-node
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo "Checking logs:"
    sudo journalctl -u globalcoyn-node -n 50 --no-pager
fi

# Test API
echo -e "${BLUE}Testing API endpoint...${NC}"
curl -s http://localhost:8001/api/blockchain/ || echo "API not responding"

echo -e "${GREEN}Fix script completed!${NC}"
echo "If the service started successfully, try accessing the API via:"
echo "  https://globalcoyn.com/api/blockchain/"
echo "If issues persist, check the wrapper logs:"
echo "  cat /var/www/globalcoyn/blockchain/node/wrapper.log"