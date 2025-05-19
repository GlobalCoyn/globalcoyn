#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== GlobalCoyn Blockchain Server Setup ===${NC}"
echo -e "This script will set up the GlobalCoyn blockchain node on the server.\n"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run this script with sudo or as root.${NC}"
    exit 1
fi

# Ensure the script is run from the correct directory
if [ ! -f "globalcoyn-blockchain.zip" ]; then
    echo -e "${RED}Error: globalcoyn-blockchain.zip not found in current directory.${NC}"
    echo "Please make sure you've uploaded the deployment package and are running this script from the same directory."
    exit 1
fi

echo -e "${YELLOW}Step 1: Install required packages${NC}"
yum update -y
yum install -y python3 python3-pip python3-devel nginx unzip

# Install Python dependencies globally
pip3 install flask flask-cors requests cryptography 

echo -e "${YELLOW}Step 2: Extract blockchain package${NC}"
unzip -o globalcoyn-blockchain.zip
mkdir -p /var/www/globalcoyn/blockchain
cp -r blockchain/* /var/www/globalcoyn/blockchain/

# Create deploy user if it doesn't exist
if ! id "deploy" &>/dev/null; then
    echo -e "${YELLOW}Creating deploy user...${NC}"
    useradd -m deploy
fi

# Set proper ownership
chown -R deploy:deploy /var/www/globalcoyn/blockchain

echo -e "${YELLOW}Step 3: Install Python dependencies${NC}"
cd /var/www/globalcoyn/blockchain/node
pip3 install -r requirements.txt

echo -e "${YELLOW}Step 4: Configure the blockchain node service${NC}"
cp /var/www/globalcoyn/blockchain/node/deploy/globalcoyn-node.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable globalcoyn-node

echo -e "${YELLOW}Step 5: Configure Nginx${NC}"
cp /var/www/globalcoyn/blockchain/node/deploy/globalcoyn.conf /etc/nginx/conf.d/
systemctl enable nginx

echo -e "${YELLOW}Step 6: Start the services${NC}"
systemctl restart nginx
systemctl start globalcoyn-node

echo -e "${YELLOW}Step 7: Create a backup directory${NC}"
mkdir -p /var/backups/globalcoyn
chown deploy:deploy /var/backups/globalcoyn

# Create a backup script
cat << 'EOF' > /etc/cron.daily/blockchain-backup
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d)
BACKUP_DIR=/var/backups/globalcoyn
mkdir -p $BACKUP_DIR
cp /var/www/globalcoyn/blockchain/node/blockchain_data.json $BACKUP_DIR/blockchain_data_$TIMESTAMP.json

# Keep only the last 10 backups
cd $BACKUP_DIR
ls -t blockchain_data_*.json | tail -n +11 | xargs -r rm
EOF

chmod +x /etc/cron.daily/blockchain-backup

echo -e "${YELLOW}Step 8: Configure firewall${NC}"
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --permanent --add-port=9000/tcp  # P2P port
    firewall-cmd --reload
    echo -e "${GREEN}Firewall configured.${NC}"
else
    echo -e "${YELLOW}Firewalld not found. Please manually configure your firewall if needed.${NC}"
fi

# Verify services are running
echo -e "\n${YELLOW}Checking service status:${NC}"
systemctl status globalcoyn-node --no-pager
systemctl status nginx --no-pager

# Display success message
echo -e "\n${GREEN}=======================================${NC}"
echo -e "${GREEN}GlobalCoyn blockchain node setup complete!${NC}"
echo -e "${GREEN}=======================================${NC}"
echo -e "Blockchain API is accessible at: https://globalcoyn.com/api/blockchain/"
echo -e "Blockchain node log: ${YELLOW}sudo journalctl -u globalcoyn-node -f${NC}"
echo -e "Nginx log: ${YELLOW}sudo tail -f /var/log/nginx/error.log${NC}"
echo -e "\nNext steps:"
echo -e "1. Deploy the frontend web application"
echo -e "2. Test the entire system"
echo -e "3. Configure SSL certificates with Let's Encrypt if needed"