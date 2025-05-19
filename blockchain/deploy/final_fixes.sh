#!/bin/bash
# Final fixes for GlobalCoyn blockchain node in production

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}GlobalCoyn Production Final Fixes${NC}"
echo "================================================================"

# First, fix the CORS issue in Nginx
echo -e "${BLUE}Fixing Nginx CORS configuration...${NC}"

# Create a map file in the correct location
cat > /tmp/gcn_cors_map.conf << 'EOF'
# Define valid CORS origins in a map
map $http_origin $gcn_cors_origin {
    default "";
    "https://globalcoyn.com" $http_origin;
    "https://www.globalcoyn.com" $http_origin;
    "http://localhost:3000" $http_origin;
}
EOF

sudo mv /tmp/gcn_cors_map.conf /etc/nginx/conf.d/gcn_cors_map.conf

# Update the main Nginx config
cat > /tmp/globalcoyn.conf << 'EOF'
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
    
    # Blockchain API proxy with CORS headers
    location /api/blockchain/ {
        proxy_pass http://localhost:8001/api/blockchain/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
        
        # Dynamic CORS headers
        add_header 'Access-Control-Allow-Origin' $gcn_cors_origin always;
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
        
        # Dynamic CORS headers
        add_header 'Access-Control-Allow-Origin' $gcn_cors_origin always;
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
        
        # Dynamic CORS headers
        add_header 'Access-Control-Allow-Origin' $gcn_cors_origin always;
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
        
        # Dynamic CORS headers
        add_header 'Access-Control-Allow-Origin' $gcn_cors_origin always;
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
        
        # Dynamic CORS headers
        add_header 'Access-Control-Allow-Origin' $gcn_cors_origin always;
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
        
        # Dynamic CORS headers
        add_header 'Access-Control-Allow-Origin' $gcn_cors_origin always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,X-API-Key' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Vary' 'Origin' always;
    }
}
EOF

sudo mv /tmp/globalcoyn.conf /etc/nginx/conf.d/globalcoyn.conf

# Test Nginx config
echo -e "${BLUE}Testing Nginx configuration...${NC}"
if sudo nginx -t; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
    sudo systemctl reload nginx
    echo -e "${GREEN}✓ Nginx reloaded${NC}"
else
    echo -e "${RED}✗ Nginx configuration test failed!${NC}"
    exit 1
fi

# Now, fix the Python service wrapper issue
echo -e "${BLUE}Fixing Python wrapper script...${NC}"

# Create an improved wrapper script that handles __file__ properly
cat > /tmp/direct_import_app.py << 'EOF'
#!/usr/bin/env python3
"""
Direct import wrapper for GlobalCoyn blockchain node app.py
"""
import os
import sys
import logging
import importlib.util

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
    sys.path.insert(0, core_dir)  # Ensure core dir is at the top
    
    # Import modules using importlib if needed
    if not os.path.exists(os.path.join(core_dir, "blockchain.py")):
        logger.error(f"blockchain.py not found in {core_dir}")
        sys.exit(1)
    
    from blockchain import Blockchain
    from transaction import Transaction
    from block import Block
    from wallet import Wallet
    from mempool import Mempool
    from mining import Miner
    from utils import bits_to_target, target_to_bits, validate_address_format
    from coin import Coin, CoinManager
    
    logger.info("Successfully imported core modules directly")
    
    # Now run app.py directly instead of using exec
    logger.info("Running app.py directly...")
    app_path = os.path.join(current_dir, "app.py")
    
    # Create a spec and import the module
    spec = importlib.util.spec_from_file_location("app_module", app_path)
    app_module = importlib.util.module_from_spec(spec)
    
    # Set critical variables before executing
    app_module.__file__ = app_path
    
    # Execute the module
    spec.loader.exec_module(app_module)
        
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    sys.exit(1)
EOF

sudo mv /tmp/direct_import_app.py /var/www/globalcoyn/blockchain/node/direct_import_app.py
sudo chmod 755 /var/www/globalcoyn/blockchain/node/direct_import_app.py
sudo chown deploy:deploy /var/www/globalcoyn/blockchain/node/direct_import_app.py

# Stop and restart the service
echo -e "${BLUE}Restarting blockchain node service...${NC}"
sudo systemctl stop globalcoyn-node
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
    sudo journalctl -u globalcoyn-node -n 20 --no-pager
fi

# Test API
echo -e "${BLUE}Testing API endpoint...${NC}"
API_RESPONSE=$(curl -s http://localhost:8001/api/blockchain/ || echo "API not responding")
if [[ "$API_RESPONSE" == *"status"* ]]; then
    echo -e "${GREEN}✓ API is responding locally${NC}"
    echo "$API_RESPONSE" | head -n 10
else
    echo -e "${RED}✗ API is not responding locally${NC}"
    echo "$API_RESPONSE"
fi

# Test CORS with external URL
echo -e "${BLUE}Testing API endpoint through Nginx...${NC}"
curl -I -H "Origin: https://www.globalcoyn.com" https://globalcoyn.com/api/blockchain/

echo -e "${GREEN}All fixes applied!${NC}"
echo "Next steps:"
echo "1. Test website access at: https://globalcoyn.com/"
echo "2. Test wallet creation in production"
echo "3. If issues persist, check logs:"
echo "   sudo journalctl -u globalcoyn-node -f"
echo "   sudo tail -f /var/log/nginx/error.log"