# GlobalCoyn Deployment Guide

This guide explains how to deploy the GlobalCoyn website, application, and node software to production.

## Prerequisites

- AWS EC2 server with public IP (e.g., 13.61.79.186)
- SSH access to the server with the appropriate private key (e.g., globalcoyn.pem)
- Nginx configured on the server
- Python 3.9+ installed on the server

## Preparing for Deployment

Before deploying to the server, you need to prepare all the necessary files:

### 1. Package the GlobalCoyn macOS App

```bash
cd /Users/adamneto/Desktop/blockchain/blockchain/apps/macos_app
chmod +x create_dmg.sh
./create_dmg.sh
```

This will create a DMG file at `dist/GlobalCoyn.dmg`

### 2. Package the GlobalCoyn Node

```bash
cd /Users/adamneto/Desktop/blockchain/blockchain
chmod +x package_node.sh
./package_node.sh
```

This will create a zip file at `website/downloads/globalcoyn-node.zip`

### 3. Prepare the Website for Deployment

```bash
cd /Users/adamneto/Desktop/blockchain/blockchain
chmod +x deploy_website.sh
./deploy_website.sh
```

This script will:
- Copy the DMG file to the website downloads directory
- Create a deployment package at `deploy/globalcoyn-website.zip`

## Deploying to AWS EC2

### 1. Upload the Website Package

```bash
scp -i ~/Downloads/globalcoyn.pem /Users/adamneto/Desktop/blockchain/blockchain/deploy/globalcoyn-website.zip ec2-user@13.61.79.186:~
```

### 2. SSH into Your Server

```bash
ssh -i ~/Downloads/globalcoyn.pem ec2-user@13.61.79.186
```

### 3. Extract and Deploy the Website

```bash
# Extract the website package
unzip -o globalcoyn-website.zip

# Deploy to the web server directory
sudo rm -rf /var/www/globalcoyn/frontend/build
sudo mv website /var/www/globalcoyn/frontend/build
sudo chown -R deploy:deploy /var/www/globalcoyn/frontend/build

# Restart web server
sudo systemctl restart nginx
```

## Deploying Blockchain Nodes

For production nodes, you should deploy at least 3 nodes for redundancy.

1. Upload the node software to each server and extract it
2. Configure each node with a unique node number and ports
3. Start the nodes using the provided script

Example for setting up multiple nodes:
```bash
# Node 1
export GCN_NODE_NUM=1
export GCN_P2P_PORT=9000
export GCN_WEB_PORT=8001
./start_node.sh

# Node 2
export GCN_NODE_NUM=2
export GCN_P2P_PORT=9001
export GCN_WEB_PORT=8002
./start_node.sh

# Node 3
export GCN_NODE_NUM=3
export GCN_P2P_PORT=9002
export GCN_WEB_PORT=8003
./start_node.sh
```

## Monitoring and Maintenance

- Set up monitoring for the nodes to ensure they stay in sync
- Regularly back up the blockchain data
- Check logs for any errors or issues

## Updating the Website

When making updates to the website:

1. Make changes to the local files
2. Run the deployment script again
3. Upload and deploy the new package

## Domain Configuration

Ensure your DNS records are pointing to your EC2 instance:
- Create an A record for globalcoyn.com pointing to your server IP
- Set up SSL certificates for secure connections