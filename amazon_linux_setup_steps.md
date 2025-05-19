# GlobalCoyn Setup on Amazon Linux

Here are the commands to set up GlobalCoyn with domain support on Amazon Linux EC2:

## 1. Update system
```bash
sudo yum update -y
```

## 2. Stop existing bootstrap node services
```bash
sudo systemctl stop globalcoyn-bootstrap1.service globalcoyn-bootstrap2.service
```

## 3. Update systemd service files

For Node 1:
```bash
sudo nano /etc/systemd/system/globalcoyn-bootstrap1.service
```

Use this content:
```
[Unit]
Description=GlobalCoyn Bootstrap Node 1
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/bootstrap_node_1
Environment="PYTHONPATH=/home/ec2-user/bootstrap_node_1"
Environment="GCN_P2P_PORT=9000"
Environment="GCN_WEB_PORT=8001"
Environment="GCN_NODE_NUM=1" 
Environment="GCN_DOMAIN=globalcoyn.com"
Environment="GCN_BOOTSTRAP_MODE=true"
Environment="GCN_ENABLE_MINING=true"
ExecStart=/usr/bin/python3 app.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

For Node 2:
```bash
sudo nano /etc/systemd/system/globalcoyn-bootstrap2.service
```

Use this content:
```
[Unit]
Description=GlobalCoyn Bootstrap Node 2
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/bootstrap_node_2
Environment="PYTHONPATH=/home/ec2-user/bootstrap_node_2"
Environment="GCN_P2P_PORT=9001"
Environment="GCN_WEB_PORT=8002"
Environment="GCN_NODE_NUM=2"
Environment="GCN_DOMAIN=globalcoyn.com"
Environment="GCN_BOOTSTRAP_MODE=true"
Environment="GCN_ENABLE_MINING=true"
ExecStart=/usr/bin/python3 app.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

## 4. Configure Nginx on Amazon Linux

Create a new Nginx configuration file:
```bash
sudo nano /etc/nginx/conf.d/globalcoyn.conf
```

Paste the configuration from the file we created (globalcoyn_nginx_amazonlinux.conf).

## 5. Verify Nginx configuration
```bash
sudo nginx -t
```

## 6. Create the web root directory
```bash
sudo mkdir -p /var/www/globalcoyn/html
sudo chown -R ec2-user:ec2-user /var/www/globalcoyn/html
```

## 7. Set up SSL with Certbot (if not already done)
```bash
sudo amazon-linux-extras install epel -y
sudo yum install certbot python3-certbot-nginx -y
sudo certbot --nginx -d globalcoyn.com -d www.globalcoyn.com
```

## 8. Reset blockchain data and logs (for a fresh start)
```bash
# For Node 1
cd /home/ec2-user/bootstrap_node_1
rm -f blockchain_data.json blockchain_data.json.backup*
rm -f *.log

# For Node 2
cd /home/ec2-user/bootstrap_node_2
rm -f blockchain_data.json blockchain_data.json.backup*
rm -f *.log
```

## 9. Reload systemd configuration and restart services
```bash
sudo systemctl daemon-reload
sudo systemctl restart nginx
sudo systemctl start globalcoyn-bootstrap1.service
sudo systemctl start globalcoyn-bootstrap2.service
```

## 10. Verify services are running
```bash
sudo systemctl status globalcoyn-bootstrap1.service
sudo systemctl status globalcoyn-bootstrap2.service
```

## 11. Test API endpoints
```bash
# Test Node 1
curl -X GET http://localhost:8001/api/blockchain -H "Content-Type: application/json" | python3 -m json.tool

# Test Node 2
curl -X GET http://localhost:8002/api/blockchain -H "Content-Type: application/json" | python3 -m json.tool

# Test via domain (if DNS is pointing to your server)
curl -X GET https://globalcoyn.com/api/blockchain -H "Content-Type: application/json" | python3 -m json.tool
```

## 12. Enable services to start on boot
```bash
sudo systemctl enable globalcoyn-bootstrap1.service
sudo systemctl enable globalcoyn-bootstrap2.service
```

## 13. Create wallet and initialize blockchain if needed
If nodes don't automatically create a genesis block:
```bash
# Create wallet
curl -X POST http://localhost:8001/api/wallet/create -H "Content-Type: application/json" | python3 -m json.tool

# Mine genesis block using created wallet address
curl -X POST http://localhost:8001/api/blockchain/blocks/mine -H "Content-Type: application/json" -d '{"miner_address": "YOUR_WALLET_ADDRESS"}' | python3 -m json.tool
```