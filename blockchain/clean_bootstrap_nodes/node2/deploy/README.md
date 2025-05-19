# GlobalCoyn Blockchain Deployment

This directory contains scripts and configurations for deploying the GlobalCoyn blockchain node to a production server.

## Deployment Steps

### 1. Prepare for Deployment

Before deploying, make sure you have:
- The GlobalCoyn blockchain deployment package (`globalcoyn-blockchain.zip`)
- SSH access to the server
- The private key file for SSH access (`globalcoyn.pem`)

### 2. Transfer Files to Server

Transfer the deployment package to the server:

```bash
scp -i ~/Downloads/globalcoyn.pem ~/Downloads/globalcoyn-blockchain.zip ec2-user@13.61.79.186:~
```

### 3. SSH Into the Server

Connect to the server via SSH:

```bash
ssh -i ~/Downloads/globalcoyn.pem ec2-user@13.61.79.186
```

### 4. Run the Server Setup Script

Extract the deployment package and run the server setup script:

```bash
unzip -o globalcoyn-blockchain.zip
cd blockchain/node/deploy
chmod +x server_setup.sh
sudo ./server_setup.sh
```

### 5. Verify Deployment

Check that the services are running correctly:

```bash
# Check blockchain node service
sudo systemctl status globalcoyn-node

# Check Nginx service
sudo systemctl status nginx

# Test the API endpoint
curl http://localhost:8001/api/blockchain/
```

### 6. Deploy the Frontend

After the blockchain node is set up, deploy the frontend web application:

```bash
# Extract frontend build
unzip -o frontend-build.zip
sudo rm -rf /var/www/globalcoyn/frontend/build
sudo mv build /var/www/globalcoyn/frontend/
sudo chown -R deploy:deploy /var/www/globalcoyn/frontend/build
sudo systemctl restart nginx
```

## File Locations

- **Blockchain Node**: `/var/www/globalcoyn/blockchain/node`
- **Frontend**: `/var/www/globalcoyn/frontend/build`
- **Nginx Config**: `/etc/nginx/conf.d/globalcoyn.conf`
- **Service Definition**: `/etc/systemd/system/globalcoyn-node.service`
- **Blockchain Data**: `/var/www/globalcoyn/blockchain/node/blockchain_data.json`
- **Backups**: `/var/backups/globalcoyn/`

## Common Management Tasks

### Restart the Blockchain Node

```bash
sudo systemctl restart globalcoyn-node
```

### View Blockchain Node Logs

```bash
sudo journalctl -u globalcoyn-node -f
```

### View Nginx Logs

```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Update the Blockchain Node

If you need to update the blockchain node:

1. Transfer the new deployment package to the server
2. Extract it and update the files
3. Restart the service

```bash
unzip -o new-globalcoyn-blockchain.zip
sudo cp -r blockchain/* /var/www/globalcoyn/blockchain/
sudo chown -R deploy:deploy /var/www/globalcoyn/blockchain
sudo systemctl restart globalcoyn-node
```

## Troubleshooting

### Service Won't Start

Check the service logs:

```bash
sudo journalctl -u globalcoyn-node -e
```

### API Endpoint Not Responding

Check if the service is running:

```bash
sudo systemctl status globalcoyn-node
```

Check that the port is open:

```bash
sudo netstat -tuln | grep 8001
```

### Nginx Configuration Issues

Test the Nginx configuration:

```bash
sudo nginx -t
```

### SSL/HTTPS Issues

Check the SSL certificate files:

```bash
sudo ls -la /etc/letsencrypt/live/globalcoyn.com/
```

Renew SSL certificates if needed:

```bash
sudo certbot renew
```