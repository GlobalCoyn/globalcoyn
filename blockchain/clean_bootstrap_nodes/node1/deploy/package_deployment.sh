#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create deployment package for GlobalCoyn blockchain node
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_DIR="$(dirname "$SCRIPT_DIR")"
BLOCKCHAIN_DIR="$(dirname "$(dirname "$NODE_DIR")")"
DEPLOY_DIR="$BLOCKCHAIN_DIR/deploy"

echo -e "${YELLOW}=== GlobalCoyn Blockchain Deployment Packaging ===${NC}"
echo "Working from: $NODE_DIR"

# Run pre-deployment checks
echo -e "${YELLOW}\nRunning pre-deployment checks...${NC}"
python3 "$SCRIPT_DIR/pre_deploy_check.py"

if [ $? -ne 0 ]; then
    echo -e "${RED}Pre-deployment checks failed. Aborting.${NC}"
    exit 1
fi

# Create deployment directory structure
echo -e "${YELLOW}\nCreating deployment package...${NC}"
mkdir -p "$DEPLOY_DIR/blockchain"
mkdir -p "$DEPLOY_DIR/blockchain/core"
mkdir -p "$DEPLOY_DIR/blockchain/node"
mkdir -p "$DEPLOY_DIR/blockchain/scripts"

# Core files
echo "Copying core files..."
cp -r "$BLOCKCHAIN_DIR/core"/* "$DEPLOY_DIR/blockchain/core/"

# Node files
echo "Copying node files..."
cp -r "$NODE_DIR"/* "$DEPLOY_DIR/blockchain/node/"
# Remove any previous deployment builds
rm -rf "$DEPLOY_DIR/blockchain/node/deploy"
mkdir -p "$DEPLOY_DIR/blockchain/node/deploy"
cp "$SCRIPT_DIR/start_production.sh" "$DEPLOY_DIR/blockchain/node/deploy/"
chmod +x "$DEPLOY_DIR/blockchain/node/deploy/start_production.sh"

# Scripts
echo "Copying scripts..."
cp -r "$BLOCKCHAIN_DIR/scripts"/* "$DEPLOY_DIR/blockchain/scripts/"

# README and LICENSE
echo "Copying documentation..."
cp "$BLOCKCHAIN_DIR/LICENSE" "$DEPLOY_DIR/blockchain/" 2>/dev/null || echo "No LICENSE file found"
cp "$BLOCKCHAIN_DIR/README.md" "$DEPLOY_DIR/blockchain/" 2>/dev/null || echo "No README.md file found"

# Create deployment zip
echo -e "${YELLOW}\nCreating deployment archive...${NC}"
cd "$DEPLOY_DIR"
rm -f "globalcoyn-blockchain.zip"
zip -r "globalcoyn-blockchain.zip" "blockchain/"

if [ $? -eq 0 ]; then
    PACKAGE_SIZE=$(du -h "globalcoyn-blockchain.zip" | cut -f1)
    echo -e "${GREEN}✅ Deployment package created successfully: ${YELLOW}$DEPLOY_DIR/globalcoyn-blockchain.zip ${GREEN}($PACKAGE_SIZE)${NC}"
    
    echo -e "\n${YELLOW}To deploy:${NC}"
    echo "1. Transfer the package to your server:"
    echo "   scp -i ~/Downloads/globalcoyn.pem $DEPLOY_DIR/globalcoyn-blockchain.zip ec2-user@13.61.79.186:~"
    echo ""
    echo "2. SSH into the server:"
    echo "   ssh -i ~/Downloads/globalcoyn.pem ec2-user@13.61.79.186"
    echo ""
    echo "3. Extract and set up the blockchain node:"
    echo "   unzip -o globalcoyn-blockchain.zip"
    echo "   sudo mkdir -p /var/www/globalcoyn/blockchain"
    echo "   sudo cp -r blockchain/* /var/www/globalcoyn/blockchain/"
    echo "   sudo chown -R deploy:deploy /var/www/globalcoyn/blockchain"
    echo ""
    echo "4. Start the node:"
    echo "   cd /var/www/globalcoyn/blockchain/node/deploy"
    echo "   ./start_production.sh"
    
else
    echo -e "${RED}Failed to create deployment package.${NC}"
    exit 1
fi

echo -e "${YELLOW}\nDon't forget to build and deploy the frontend application!${NC}"
echo -e "${YELLOW}See the README for more information on that process.${NC}"