# GlobalCoyn Blockchain Production Deployment Plan

This document outlines the complete process for deploying a clean production version of the GlobalCoyn blockchain node and frontend.

## 1. Create Production Node

First, we'll create a dedicated production node based on the working node_template:

```bash
# Navigate to the blockchain/nodes directory
cd /Users/adamneto/Desktop/blockchain/blockchain/nodes

# Create a new production node directory
mkdir -p node_production

# Copy core files from node_template, excluding development files
rsync -av --exclude="node_*.log" \
          --exclude="blockchain_data.json.backup.*" \
          --exclude="comprehensive_test.sh" \
          --exclude="simple_test.sh" \
          --exclude="test_api.sh" \
          --exclude="install_dependencies.sh" \
          --exclude="restart_node.sh" \
          --exclude="shutdown_nodes.sh" \
          --exclude="start_node.sh" \
          --exclude=".*" \
          node_template/ node_production/

# Create a production config
cat > node_production/production_config.json << 'EOF'
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
```

## 2. Configure CORS and Production Settings

Create a dedicated CORS setup file for production:

```bash
# Create a production-specific CORS setup
cat > node_production/cors_setup.py << 'EOF'
"""
CORS configuration for the GlobalCoyn blockchain node in production
"""
from flask_cors import CORS
from config_loader import config

def setup_cors(app):
    """
    Configure CORS for the Flask application
    """
    # Get CORS settings from config
    origins = config.get("security", "cors_origins", ["https://globalcoyn.com", "https://www.globalcoyn.com"])
    
    # Apply CORS settings
    cors_config = {
        "origins": origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-API-Key", "Authorization"],
        "supports_credentials": True
    }
    
    # Log CORS configuration
    print(f"Setting up CORS with origins: {origins}")
    
    # Apply CORS to the app
    CORS(app, resources={r"/api/*": cors_config})
    
    return app
EOF
```

## 3. Package Deployment Files

Create a deployment package that includes only the necessary files:

```bash
# Create a deployment package
cd /Users/adamneto/Desktop/blockchain/blockchain

# Create deployment directory
mkdir -p deploy/production_package
DEPLOY_DIR="deploy/production_package"

# Create directory structure
mkdir -p "$DEPLOY_DIR/blockchain/core"
mkdir -p "$DEPLOY_DIR/blockchain/node"
mkdir -p "$DEPLOY_DIR/blockchain/node/deploy"
mkdir -p "$DEPLOY_DIR/blockchain/node/routes"

# Copy core files
echo "Copying core files..."
cp -r core/* "$DEPLOY_DIR/blockchain/core/"

# Copy node files
echo "Copying node files..."
cp -r nodes/node_production/* "$DEPLOY_DIR/blockchain/node/"
cp -r nodes/node_production/routes/* "$DEPLOY_DIR/blockchain/node/routes/"

# Create necessary __init__.py files
touch "$DEPLOY_DIR/blockchain/__init__.py"
touch "$DEPLOY_DIR/blockchain/core/__init__.py"
touch "$DEPLOY_DIR/blockchain/node/__init__.py"
touch "$DEPLOY_DIR/blockchain/node/routes/__init__.py"

# Copy deployment files
cp nodes/node_template/deploy/server_setup.sh "$DEPLOY_DIR/blockchain/node/deploy/"
cp nodes/node_template/deploy/globalcoyn-node.service "$DEPLOY_DIR/blockchain/node/deploy/"

# Create a production-specific nginx configuration
cat > "$DEPLOY_DIR/blockchain/node/deploy/globalcoyn.conf" << 'EOF'
# CORS map for GlobalCoyn
map $http_origin $gcn_cors_origin {
    default "";
    "https://globalcoyn.com" $http_origin;
    "https://www.globalcoyn.com" $http_origin;
}

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

# Create deployment script for the server
cat > "$DEPLOY_DIR/blockchain/node/deploy/clean_deploy.sh" << 'EOF'
#!/bin/bash
# Clean deployment script for GlobalCoyn blockchain node

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}GlobalCoyn Clean Production Deployment${NC}"
echo "================================================================"

# Stop existing services
echo -e "${BLUE}Stopping existing services...${NC}"
sudo systemctl stop globalcoyn-node || true
sudo systemctl disable globalcoyn-node || true

# Clean up existing installation
echo -e "${BLUE}Cleaning up existing installation...${NC}"
INSTALL_DIR="/var/www/globalcoyn"
BACKUP_DIR="${INSTALL_DIR}_backup_$(date +%s)"

# Backup existing files if any
if [ -d "$INSTALL_DIR" ]; then
    sudo mv "$INSTALL_DIR" "$BACKUP_DIR"
    echo -e "${GREEN}Backed up existing installation to $BACKUP_DIR${NC}"
fi

# Create fresh installation directory
sudo mkdir -p "$INSTALL_DIR/blockchain/core"
sudo mkdir -p "$INSTALL_DIR/blockchain/node"
sudo mkdir -p "$INSTALL_DIR/frontend"

# Extract blockchain files
echo -e "${BLUE}Extracting blockchain files...${NC}"
sudo unzip -q -o globalcoyn-blockchain.zip -d /tmp/gcn-deploy
sudo cp -r /tmp/gcn-deploy/blockchain/* "$INSTALL_DIR/blockchain/"
sudo rm -rf /tmp/gcn-deploy

# Extract frontend files if available
if [ -f globalcoyn-website.zip ]; then
    echo -e "${BLUE}Extracting frontend files...${NC}"
    sudo unzip -q -o globalcoyn-website.zip -d "$INSTALL_DIR/frontend/"
fi

# Install required packages
echo -e "${BLUE}Installing required packages...${NC}"
sudo yum update -y
sudo yum install -y python3 python3-pip python3-devel nginx unzip

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
sudo pip3 install flask flask-cors requests cryptography python-dotenv

# Configure Nginx
echo -e "${BLUE}Configuring Nginx...${NC}"
sudo cp "$INSTALL_DIR/blockchain/node/deploy/globalcoyn.conf" /etc/nginx/conf.d/

# Set up systemd service
echo -e "${BLUE}Setting up systemd service...${NC}"
sudo cp "$INSTALL_DIR/blockchain/node/deploy/globalcoyn-node.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable globalcoyn-node

# Set correct permissions
echo -e "${BLUE}Setting permissions...${NC}"
sudo useradd -r deploy || true
sudo chown -R deploy:deploy "$INSTALL_DIR"
sudo chmod -R 755 "$INSTALL_DIR"

# Start services
echo -e "${BLUE}Starting services...${NC}"
sudo systemctl start nginx
sudo systemctl start globalcoyn-node

# Configure firewall
echo -e "${BLUE}Configuring firewall...${NC}"
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=8001/tcp
sudo firewall-cmd --permanent --add-port=9000/tcp
sudo firewall-cmd --reload

# Check service status
echo -e "${BLUE}Checking service status...${NC}"
echo "Nginx status:"
sudo systemctl status nginx --no-pager

echo "GlobalCoyn node status:"
sudo systemctl status globalcoyn-node --no-pager

# Test API
echo -e "${BLUE}Testing API endpoints...${NC}"
sleep 5  # Give the service time to start
curl -s http://localhost:8001/api/blockchain/ | grep -o "status.*online" || echo "API not responding yet"

echo -e "${GREEN}Deployment complete!${NC}"
echo "Next steps:"
echo "1. Test frontend access: https://globalcoyn.com/"
echo "2. Test API access: https://globalcoyn.com/api/blockchain/"
echo "3. Check logs if needed:"
echo "   sudo journalctl -u globalcoyn-node -f"
echo "   sudo tail -f /var/log/nginx/error.log"
EOF

chmod +x "$DEPLOY_DIR/blockchain/node/deploy/clean_deploy.sh"

# Create a ZIP package
cd deploy
zip -r globalcoyn-blockchain.zip production_package/blockchain
echo "Deployment package created: globalcoyn-blockchain.zip"
```

## 4. Update Frontend Configuration

Update the frontend configuration to use the production API endpoints:

```bash
# Navigate to website directory
cd /Users/adamneto/Desktop/blockchain/blockchain/website

# Update API endpoints in walletService.js and other service files
# Check locations of API configuration files
find app/src -type f -exec grep -l "API_URL" {} \;

# Edit the service files to use production URLs
# Example update for walletService.js:
sed -i '' 's|DEV_API_URL = .*|DEV_API_URL = "https://globalcoyn.com/api";|g' app/src/services/walletService.js

# Build the frontend for production
cd app
npm run build

# Create a ZIP package of the frontend
cd build
zip -r ../../../deploy/globalcoyn-website.zip .
echo "Frontend package created: globalcoyn-website.zip"
```

## 5. Server Deployment

Deploy to the production server:

```bash
# Copy packages to the server
scp -i ~/.ssh/globalcoyn.pem \
    /Users/adamneto/Desktop/blockchain/blockchain/deploy/globalcoyn-blockchain.zip \
    /Users/adamneto/Desktop/blockchain/blockchain/deploy/globalcoyn-website.zip \
    ec2-user@globalcoyn.com:~/

# SSH to the server
ssh -i ~/.ssh/globalcoyn.pem ec2-user@globalcoyn.com

# On the server
cd ~
chmod +x /tmp/clean_deploy.sh
./clean_deploy.sh
```

## 6. Verification

Verify the deployment:

1. Test the frontend: https://globalcoyn.com/
2. Test the API: https://globalcoyn.com/api/blockchain/
3. Test wallet creation and other functionality
4. Check the logs:
   ```bash
   sudo journalctl -u globalcoyn-node -f
   sudo tail -f /var/log/nginx/error.log
   ```

## 7. Troubleshooting

If issues arise:

1. **CORS Issues**: Check the Nginx configuration and that correct headers are being sent.
2. **Module Import Issues**: Check Python paths and __init__.py files.
3. **Service Startup Issues**: Check service logs for errors.
4. **API Connection Issues**: Verify network connectivity and firewall rules.