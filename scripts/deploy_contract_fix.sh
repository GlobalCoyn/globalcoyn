#!/bin/bash
#
# Deploy contract fix to bootstrap nodes
#

set -e

echo "Deploying contract fix to bootstrap nodes..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

SERVER1="globalcoyn.com"
SERVER1_USER="ec2-user"
SERVER1_NODE_PATH="/var/www/globalcoyn/bootstrap-node1"

# Create a temporary directory for packaging files
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/contract-fix"
mkdir -p "$PACKAGE_DIR"

# Copy the necessary files
echo -e "${YELLOW}Preparing contract fix package...${NC}"
cp ../core/blockchain.py "$PACKAGE_DIR/"
cp ../core/contract.py "$PACKAGE_DIR/"
cp ../core/transaction.py "$PACKAGE_DIR/"
cp ../core/block.py "$PACKAGE_DIR/"
cp ../core/utils.py "$PACKAGE_DIR/"
cp ../node/fix_contract_import.py "$PACKAGE_DIR/"

# Create the installation script
cat > "$PACKAGE_DIR/install_fix.sh" << 'EOF'
#!/bin/bash

# Stop the service
echo "Stopping GlobalCoyn bootstrap node service..."
sudo systemctl stop globalcoyn-bootstrap1.service

# Backup original files
BACKUP_DIR="contract_backup_$(date +%Y%m%d%H%M%S)"
mkdir -p $BACKUP_DIR
cp *.py $BACKUP_DIR/ 2>/dev/null || true

# Copy new files
echo "Copying contract module files..."
cp blockchain.py contract.py transaction.py block.py utils.py .

# Make fix script executable
chmod +x fix_contract_import.py

# Run the fix script
echo "Running contract import fix script..."
python3 fix_contract_import.py

# Restart the service
echo "Restarting GlobalCoyn bootstrap node service..."
sudo systemctl start globalcoyn-bootstrap1.service

# Check service status
sleep 3
sudo systemctl status globalcoyn-bootstrap1.service

echo "Fix installation completed!"
EOF

# Make the installation script executable
chmod +x "$PACKAGE_DIR/install_fix.sh"

# Create a tarball
echo -e "${YELLOW}Creating tarball...${NC}"
TARBALL="$TEMP_DIR/contract-fix.tar.gz"
tar -czf "$TARBALL" -C "$TEMP_DIR" contract-fix

# Deploy to bootstrap node 1
echo -e "${YELLOW}Deploying to bootstrap node 1 on $SERVER1...${NC}"
scp "$TARBALL" "$SERVER1_USER@$SERVER1:~/"
ssh "$SERVER1_USER@$SERVER1" << EOF
mkdir -p contract-fix
tar -xzf contract-fix.tar.gz
cd contract-fix
cd $SERVER1_NODE_PATH
cp ~/contract-fix/contract-fix/* .
chmod +x install_fix.sh
./install_fix.sh
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Contract fix successfully deployed to bootstrap node 1!${NC}"
else
    echo -e "${RED}Failed to deploy contract fix to bootstrap node 1.${NC}"
    exit 1
fi

# Clean up
rm -rf "$TEMP_DIR"

echo -e "${GREEN}Contract fix deployment completed!${NC}"