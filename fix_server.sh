#!/bin/bash

# First, create the service file
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
ExecStart=/usr/bin/python3 app.py
Restart=always
TimeoutStartSec=30
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Move the service file to systemd directory
sudo mv globalcoyn-node.service /etc/systemd/system/

# Update Nginx configuration
cat > globalcoyn.conf << 'EOF'
server {
    listen 80;
    server_name globalcoyn.com www.globalcoyn.com localhost 13.61.79.186;
    
    # Root directory for frontend files
    root /var/www/globalcoyn/frontend/build;
    index index.html;
    
    # Frontend routing (React/SPA support)
    location / {
        try_files $uri $uri/ /index.html;
        expires 1h;
    }
    
    # Blockchain API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        add_header 'Access-Control-Allow-Origin' '*';
    }
    
    location /wallet/ {
        proxy_pass http://127.0.0.1:8001/wallet/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        add_header 'Access-Control-Allow-Origin' '*';
    }
}
EOF

# Move the Nginx config to the correct location
sudo mv globalcoyn.conf /etc/nginx/conf.d/

# Test Nginx configuration
sudo nginx -t

# Check if folder structure exists
sudo mkdir -p /var/www/globalcoyn/blockchain/node

# Look for app.py
echo "Looking for app.py files in /var/www:"
sudo find /var/www -name "app.py"

# Reload and restart services
sudo systemctl daemon-reload
sudo systemctl enable globalcoyn-node
sudo systemctl restart nginx

echo "Configuration completed. Check if app.py exists in the correct location."
echo "If everything looks good, start the blockchain node with:"
echo "sudo systemctl start globalcoyn-node"