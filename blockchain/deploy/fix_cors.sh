#!/bin/bash
# Fix CORS issues for GlobalCoyn blockchain API

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}GlobalCoyn CORS Fix Script${NC}"
echo "================================================================"

# Backup current Nginx config
echo -e "${BLUE}Backing up current Nginx config...${NC}"
BACKUP_FILE="/etc/nginx/conf.d/globalcoyn.conf.bak.$(date +%s)"
sudo cp /etc/nginx/conf.d/globalcoyn.conf $BACKUP_FILE
echo -e "${GREEN}Backup created at: $BACKUP_FILE${NC}"

# Update main Nginx config to include map for CORS
echo -e "${BLUE}Adding CORS map to Nginx configuration...${NC}"
cat > temp_map_file << 'EOF'
# GlobalCoyn CORS map
map $http_origin $gcn_cors_origin {
    default "";
    "https://globalcoyn.com" $http_origin;
    "https://www.globalcoyn.com" $http_origin;
    "http://localhost:3000" $http_origin;
}
EOF

sudo mv temp_map_file /etc/nginx/conf.d/gcn_cors_map.conf
echo -e "${GREEN}Created CORS map file: /etc/nginx/conf.d/gcn_cors_map.conf${NC}"

# Update all location blocks with dynamic CORS headers
echo -e "${BLUE}Updating API location blocks with dynamic CORS headers...${NC}"
sudo sed -i 's/add_header .Access-Control-Allow-Origin. .https:\/\/www.globalcoyn.com. always;/add_header '\''Access-Control-Allow-Origin'\'' $gcn_cors_origin always;/g' /etc/nginx/conf.d/globalcoyn.conf
sudo sed -i 's/add_header .Vary. .Origin. always;/add_header '\''Vary'\'' '\''Origin'\'' always;/g' /etc/nginx/conf.d/globalcoyn.conf

# Update OPTIONS handler 
echo -e "${BLUE}Updating OPTIONS request handler...${NC}"
cat > temp_options_block << 'EOF'
    # CORS preflight handler for all API endpoints
    location /api/ {
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' $gcn_cors_origin;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,X-API-Key';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Access-Control-Allow-Credentials' 'true';
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            add_header 'Vary' 'Origin';
            return 204;
        }
    }
EOF

# Replace the OPTIONS handler block
sudo sed -i '/# CORS preflight handler for all API endpoints/,/}/c\'"$(cat temp_options_block)" /etc/nginx/conf.d/globalcoyn.conf

# Test Nginx config
echo -e "${BLUE}Testing Nginx configuration...${NC}"
if sudo nginx -t; then
    echo -e "${GREEN}Nginx configuration is valid${NC}"
    sudo systemctl reload nginx
    echo -e "${GREEN}Nginx reloaded${NC}"
else
    echo -e "${RED}Nginx configuration test failed!${NC}"
    # Restore from backup
    sudo cp $BACKUP_FILE /etc/nginx/conf.d/globalcoyn.conf
    sudo rm /etc/nginx/conf.d/gcn_cors_map.conf
    sudo systemctl reload nginx
    echo -e "${YELLOW}Restored previous Nginx configuration${NC}"
fi

# Test CORS headers with curl
echo -e "${BLUE}Testing CORS headers...${NC}"
echo "Testing OPTIONS request:"
curl -I -X OPTIONS -H "Origin: https://www.globalcoyn.com" https://globalcoyn.com/api/wallet/generate-seed
echo -e "\nTesting actual API request:"
curl -I -H "Origin: https://www.globalcoyn.com" https://globalcoyn.com/api/blockchain/

echo -e "${GREEN}CORS fix complete!${NC}"
echo "If you still experience CORS issues, check the Nginx error logs:"
echo "sudo tail -f /var/log/nginx/error.log"