# Bootstrap Node Reset Plan for GlobalCoyn Production

## 1. SSH into the server
```bash
ssh ec2-user@globalcoyn.com
# or
ssh -i your-key.pem ec2-user@your-ec2-ip
```

## 2. Stop both bootstrap node services
```bash
sudo systemctl stop globalcoyn-bootstrap1.service globalcoyn-bootstrap2.service
```

## 3. Reset the blockchain data
```bash
# For Node 1
cd /home/ec2-user/bootstrap_node_1
rm blockchain_data.json blockchain_data.json.backup*
rm *.log

# For Node 2
cd /home/ec2-user/bootstrap_node_2
rm blockchain_data.json blockchain_data.json.backup*
rm *.log
```

## 4. Update configuration to ensure they're fresh bootstrap nodes
For each node's `production_config.json`:
- Set `bootstrap_mode` to `true`
- Ensure `p2p_port` and `web_port` are unique for each node
- Make sure `seed_nodes` array is empty for first initialization

## 5. Configure service files to use the domain name
Check and update service files:
```bash
sudo nano /etc/systemd/system/globalcoyn-bootstrap1.service
sudo nano /etc/systemd/system/globalcoyn-bootstrap2.service
```

Ensure they contain:
- Proper environment variables for domain configuration
- Correct working directories
- Correct Python path

## 6. Reload systemd and restart services
```bash
sudo systemctl daemon-reload
sudo systemctl start globalcoyn-bootstrap1.service
sudo systemctl start globalcoyn-bootstrap2.service
```

## 7. Verify nodes are running and creating a fresh blockchain
```bash
# Check status
sudo systemctl status globalcoyn-bootstrap1.service
sudo systemctl status globalcoyn-bootstrap2.service

# Check API
curl -X GET http://localhost:8001/api/blockchain -H "Content-Type: application/json" | python3 -m json.tool
curl -X GET http://localhost:8002/api/blockchain -H "Content-Type: application/json" | python3 -m json.tool
```

## 8. Create wallet and mine genesis block (if needed)
If the nodes don't automatically create a genesis block:
```bash
# Generate seed phrase
curl -X GET http://localhost:8001/api/wallet/generate-seed -H "Content-Type: application/json" | python3 -m json.tool

# Import wallet
curl -X POST http://localhost:8001/api/wallet/import/seed -H "Content-Type: application/json" -d '{"seed_phrase": "YOUR_SEED_PHRASE"}' | python3 -m json.tool

# Mine genesis block
curl -X POST http://localhost:8001/api/blockchain/blocks/mine -H "Content-Type: application/json" -d '{"miner_address": "YOUR_WALLET_ADDRESS"}' | python3 -m json.tool
```

## 9. Configure nginx to route domains
Ensure nginx is routing traffic correctly from globalcoyn.com to the bootstrap nodes:
```bash
sudo nano /etc/nginx/sites-available/globalcoyn
```

Configure the file to route traffic to the correct ports:
```
server {
    listen 80;
    server_name globalcoyn.com www.globalcoyn.com;

    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /explorer/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend
    location / {
        root /path/to/frontend/build;
        try_files $uri $uri/ /index.html;
    }
}
```

## 10. Test API endpoints using the domain
```bash
curl -X GET https://globalcoyn.com/api/blockchain -H "Content-Type: application/json" | python3 -m json.tool
```

## 11. Deploy the frontend application
```bash
# Deploy your updated website with transaction links
cd /path/to/your/website/build
# Deploy commands here...
```