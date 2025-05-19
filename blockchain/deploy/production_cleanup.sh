#!/bin/bash
# Production Cleanup Script for GlobalCoyn Blockchain Node
# This script cleans up unnecessary development files and ensures only production files remain

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}GlobalCoyn Blockchain Production Cleanup${NC}"
echo "================================================================"

# Stop the service if it's running
echo -e "${BLUE}Stopping service for maintenance...${NC}"
sudo systemctl stop globalcoyn-node

# Define directories
INSTALL_DIR="/var/www/globalcoyn/blockchain"
CORE_DIR="${INSTALL_DIR}/core"
NODE_DIR="${INSTALL_DIR}/node"
BACKUP_DIR="/var/www/globalcoyn/backup_$(date +%s)"

# Create backup
echo -e "${BLUE}Creating backup of current setup...${NC}"
sudo mkdir -p ${BACKUP_DIR}
sudo cp -r ${INSTALL_DIR} ${BACKUP_DIR}/
echo -e "${GREEN}Backup created at: ${BACKUP_DIR}${NC}"

# Clean up development files
echo -e "${BLUE}Removing development files...${NC}"

# List of development files/directories to remove
DEV_FILES=(
  "${NODE_DIR}/node_*.log"
  "${NODE_DIR}/blockchain_data.json.backup.*"
  "${NODE_DIR}/comprehensive_test.sh"
  "${NODE_DIR}/simple_test.sh"
  "${NODE_DIR}/test_api.sh"
  "${NODE_DIR}/install_dependencies.sh"
  "${NODE_DIR}/restart_node.sh"
  "${NODE_DIR}/shutdown_nodes.sh"
  "${NODE_DIR}/start_node.sh"
)

# Remove each development file
for file in "${DEV_FILES[@]}"; do
  if sudo find ${file} -type f 2>/dev/null | grep -q .; then
    echo "  Removing: ${file}"
    sudo rm -f ${file}
  fi
done

# Ensure only production config exists
echo -e "${BLUE}Setting up production configuration...${NC}"
if [ -f "${NODE_DIR}/production_config.json" ]; then
  # Backup the existing config
  sudo cp "${NODE_DIR}/production_config.json" "${NODE_DIR}/production_config.json.bak"
  
  # Update the production config
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
  sudo mv temp_config.json "${NODE_DIR}/production_config.json"
  sudo chown deploy:deploy "${NODE_DIR}/production_config.json"
  echo -e "${GREEN}Updated production_config.json${NC}"
fi

# Update Nginx configuration to support all domains
echo -e "${BLUE}Updating Nginx CORS configuration...${NC}"
cat > temp_nginx.conf << 'EOF'
server {
    listen 80;
    server_name globalcoyn.com www.globalcoyn.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name globalcoyn.com www.globalcoyn.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/globalcoyn.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/globalcoyn.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    
    # HSTS settings
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    
    # Frontend files
    root /var/www/globalcoyn/frontend/build;
    index index.html;
    
    # Frontend routing (React/SPA support)
    location / {
        try_files $uri $uri/ /index.html;
        expires 1h;
    }
    
    # Cache static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    # CORS preflight handler for all API endpoints
    location /api/ {
        if ($request_method = 'OPTIONS') {
            # Support both domains with and without www
            add_header 'Access-Control-Allow-Origin' $http_origin;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,X-API-Key';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Access-Control-Allow-Credentials' 'true';
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }
    
    # Blockchain API proxy with CORS headers
    location /api/blockchain/ {
        proxy_pass http://localhost:8001/api/blockchain/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
        
        # CORS headers - support both domains
        add_header 'Access-Control-Allow-Origin' $http_origin always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,X-API-Key' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Vary' 'Origin' always;
    }
    
    location /api/network/ {
        proxy_pass http://localhost:8001/api/network/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
        
        # CORS headers - support both domains
        add_header 'Access-Control-Allow-Origin' $http_origin always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,X-API-Key' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Vary' 'Origin' always;
    }
    
    location /api/wallet/ {
        proxy_pass http://localhost:8001/api/wallet/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
        
        # CORS headers - support both domains
        add_header 'Access-Control-Allow-Origin' $http_origin always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,X-API-Key' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Vary' 'Origin' always;
    }
    
    location /api/mining/ {
        proxy_pass http://localhost:8001/api/mining/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
        
        # CORS headers - support both domains
        add_header 'Access-Control-Allow-Origin' $http_origin always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,X-API-Key' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Vary' 'Origin' always;
    }
    
    location /api/transactions/ {
        proxy_pass http://localhost:8001/api/transactions/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
        
        # CORS headers - support both domains
        add_header 'Access-Control-Allow-Origin' $http_origin always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,X-API-Key' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Vary' 'Origin' always;
    }
    
    # Handle direct API root path too
    location = /api {
        proxy_pass http://localhost:8001/api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
        
        # CORS headers - support both domains
        add_header 'Access-Control-Allow-Origin' $http_origin always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,X-API-Key' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Vary' 'Origin' always;
    }
    
    # Add a map to check for valid origins
    map $http_origin $cors_origin {
        default "";
        "https://globalcoyn.com" $http_origin;
        "https://www.globalcoyn.com" $http_origin;
    }
}
EOF

sudo mv temp_nginx.conf /etc/nginx/conf.d/globalcoyn.conf
echo -e "${GREEN}Updated Nginx configuration${NC}"

# Test Nginx config
echo -e "${BLUE}Testing Nginx configuration...${NC}"
if sudo nginx -t; then
    echo -e "${GREEN}Nginx configuration is valid${NC}"
    sudo systemctl reload nginx
    echo -e "${GREEN}Nginx reloaded${NC}"
else
    echo -e "${RED}Nginx configuration test failed!${NC}"
    # Restore from backup
    sudo cp "${BACKUP_DIR}/blockchain/node/deploy/globalcoyn.conf" /etc/nginx/conf.d/globalcoyn.conf
    sudo systemctl reload nginx
    echo -e "${YELLOW}Restored previous Nginx configuration${NC}"
fi

# Fix permissions again
echo -e "${BLUE}Ensuring correct permissions...${NC}"
sudo chown -R deploy:deploy ${INSTALL_DIR}
sudo chmod -R 755 ${INSTALL_DIR}

# Restart the service
echo -e "${BLUE}Starting the service...${NC}"
sudo systemctl start globalcoyn-node
sleep 5

# Check if service is running
if systemctl is-active --quiet globalcoyn-node; then
    echo -e "${GREEN}✓ Service started successfully${NC}"
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo "Checking logs:"
    sudo journalctl -u globalcoyn-node -n 20 --no-pager
fi

echo -e "${GREEN}Production cleanup complete!${NC}"
echo "Next steps:"
echo "1. Test API access: curl https://globalcoyn.com/api/blockchain/"
echo "2. Test CORS with preflight: curl -I -X OPTIONS https://globalcoyn.com/api/wallet/generate-seed"
echo "3. Check Nginx error logs: sudo tail -f /var/log/nginx/error.log"
echo "If needed, you can restore from backup at: ${BACKUP_DIR}"