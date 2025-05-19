#!/bin/bash
# Debug script for GlobalCoyn production service issues
# This script helps identify and fix common issues with the GlobalCoyn blockchain node deployment

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}GlobalCoyn Production Service Debug Script${NC}"
echo "================================================================"

# Step 1: Check if service is running
echo -e "${BLUE}Step 1: Checking if globalcoyn-node service is running...${NC}"
if systemctl is-active --quiet globalcoyn-node; then
    echo -e "${GREEN}✓ globalcoyn-node service is running${NC}"
    systemctl status globalcoyn-node
else
    echo -e "${RED}✗ globalcoyn-node service is NOT running${NC}"
    echo "Attempting to start the service..."
    sudo systemctl start globalcoyn-node
    
    # Check again
    if systemctl is-active --quiet globalcoyn-node; then
        echo -e "${GREEN}✓ Service started successfully${NC}"
    else
        echo -e "${RED}✗ Service failed to start${NC}"
        echo "Checking service logs for errors:"
        sudo journalctl -u globalcoyn-node -n 50 --no-pager
    fi
fi

# Step 2: Check if Python application is listening on port
echo -e "\n${BLUE}Step 2: Checking if application is listening on port 8001...${NC}"
if netstat -tlpn | grep -q ":8001"; then
    echo -e "${GREEN}✓ Application is listening on port 8001${NC}"
    netstat -tlpn | grep ":8001"
else
    echo -e "${RED}✗ No application listening on port 8001${NC}"
    echo "Checking if Python process is running:"
    ps aux | grep python | grep app.py
fi

# Step 3: Check Nginx configuration and status
echo -e "\n${BLUE}Step 3: Checking Nginx configuration and status...${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx service is running${NC}"
    
    # Test Nginx configuration
    if nginx -t; then
        echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
    else
        echo -e "${RED}✗ Nginx configuration has errors${NC}"
    fi
    
    # Check if Nginx is properly set up for API proxying
    if grep -q "proxy_pass.*localhost:8001" /etc/nginx/conf.d/globalcoyn.conf; then
        echo -e "${GREEN}✓ Nginx is configured to proxy API requests${NC}"
    else
        echo -e "${RED}✗ Nginx configuration may be missing API proxy settings${NC}"
        echo "Installing updated configuration with CORS headers..."
        sudo cp /var/www/globalcoyn/blockchain/node/deploy/globalcoyn-cors-fix.conf /etc/nginx/conf.d/globalcoyn.conf
        sudo nginx -t && sudo systemctl reload nginx
    fi
else
    echo -e "${RED}✗ Nginx service is NOT running${NC}"
    echo "Attempting to start Nginx..."
    sudo systemctl start nginx
fi

# Step 4: Test local API access (bypassing Nginx)
echo -e "\n${BLUE}Step 4: Testing local API access (bypassing Nginx)...${NC}"
BLOCKCHAIN_INFO=$(curl -s http://localhost:8001/api/blockchain/ || echo "Connection failed")
if [[ "$BLOCKCHAIN_INFO" == *"status"* ]]; then
    echo -e "${GREEN}✓ Local API is responding correctly${NC}"
    echo "API response: $BLOCKCHAIN_INFO"
else
    echo -e "${RED}✗ Local API is not responding correctly${NC}"
    echo "Response: $BLOCKCHAIN_INFO"
    echo "This indicates the blockchain node application is not functioning properly."
fi

# Step 5: Check CORS settings
echo -e "\n${BLUE}Step 5: Checking CORS configuration...${NC}"
if grep -q "setup_cors" /var/www/globalcoyn/blockchain/node/app.py; then
    echo -e "${GREEN}✓ Application has CORS setup code${NC}"
else
    echo -e "${RED}✗ Application might be missing CORS setup${NC}"
fi

if grep -q "Access-Control-Allow-Origin" /etc/nginx/conf.d/globalcoyn.conf; then
    echo -e "${GREEN}✓ Nginx has CORS headers in configuration${NC}"
else
    echo -e "${RED}✗ Nginx is missing CORS headers${NC}"
    echo "Installing updated configuration with CORS headers..."
    sudo cp /var/www/globalcoyn/blockchain/node/deploy/globalcoyn-cors-fix.conf /etc/nginx/conf.d/globalcoyn.conf
    sudo nginx -t && sudo systemctl reload nginx
fi

# Step 6: Fix file permissions if needed
echo -e "\n${BLUE}Step 6: Checking file permissions...${NC}"
if [ -d "/var/www/globalcoyn/blockchain/node" ]; then
    sudo chown -R deploy:deploy /var/www/globalcoyn/blockchain
    echo -e "${GREEN}✓ Set correct ownership for blockchain files${NC}"
else
    echo -e "${RED}✗ Blockchain node directory not found${NC}"
fi

# Step 7: Test direct API endpoints
echo -e "\n${BLUE}Step 7: Testing key API endpoints directly...${NC}"
for endpoint in "/api/blockchain/" "/api/wallet/generate-seed" "/api/blockchain/blocks/latest"; do
    response=$(curl -s http://localhost:8001$endpoint)
    echo "Testing $endpoint: ${response:0:100}..." 
done

echo -e "\n${GREEN}Debug complete!${NC}"
echo "If issues persist, check the application logs with: sudo journalctl -u globalcoyn-node -f"
echo "And check Nginx logs with: sudo tail -f /var/log/nginx/error.log"