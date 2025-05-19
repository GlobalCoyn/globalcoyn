# GlobalCoyn Deployment Guide

This document provides instructions for deploying GlobalCoyn to production on AWS EC2.

## Prerequisites

- AWS EC2 instance (current: `13.61.79.186`)
- SSH key pair (current: `~/Downloads/globalcoyn.pem`)
- Admin access to the EC2 instance (`ec2-user`)

## Deployment Components

The GlobalCoyn deployment consists of several components:

1. **Website**: Static HTML/CSS/JS files that provide information about GlobalCoyn
2. **Bootstrap Nodes**: Two dedicated nodes that serve as entry points for the network
3. **MacOS App**: Desktop application for GlobalCoyn
4. **Node Package**: Archive containing the GlobalCoyn node software

## Deployment Workflow

### 1. Run Tests

Before deploying, run the integration tests to ensure everything works correctly:

```bash
# Test macOS app integration with bootstrap nodes
./test_macos_integration.sh

# Run blockchain tests
./run_blockchain_tests.sh
```

### 2. Package Components

Package all components for deployment:

```bash
# Package bootstrap nodes
./package_bootstrap_node.sh 1
./package_bootstrap_node.sh 2

# Package macOS app
./package_macos_app.sh
```

### 3. Deploy to Production

Use the deployment script to deploy everything to production:

```bash
# Deploy all components to production
./deploy_to_production.sh
```

This script will:
- Upload bootstrap node packages to the EC2 server
- Install and configure the bootstrap nodes
- Create systemd services for the bootstrap nodes
- Deploy the website to the server
- Deploy the node package and macOS app to the downloads directory

### 4. Manual Verification

After the deployment script completes, manually verify that:

1. The website is accessible at http://13.61.79.186
2. The bootstrap nodes are running
3. The macOS app and node package can be downloaded
4. The macOS app can connect to the bootstrap nodes

## AWS EC2 Server Structure

- Website: `/var/www/globalcoyn/frontend/build`
- Bootstrap Nodes: `/opt/globalcoyn/bootstrap`
- Downloads:
  - MacOS App: `/var/www/globalcoyn/frontend/build/downloads/globalcoyn-macos.dmg`
  - Node Package: `/var/www/globalcoyn/frontend/build/downloads/globalcoyn-node.zip`

## Server Administration

Connect to the server using SSH:

```bash
ssh -i ~/Downloads/globalcoyn.pem ec2-user@13.61.79.186
```

### Checking Service Status

```bash
# Check bootstrap node 1 status
sudo systemctl status bootstrap-node1.service

# Check bootstrap node 2 status
sudo systemctl status bootstrap-node2.service

# Check web server status
sudo systemctl status nginx
```

### Restarting Services

```bash
# Restart bootstrap node 1
sudo systemctl restart bootstrap-node1.service

# Restart bootstrap node 2
sudo systemctl restart bootstrap-node2.service

# Restart web server
sudo systemctl restart nginx
```

### Viewing Logs

```bash
# View bootstrap node 1 logs
sudo journalctl -u bootstrap-node1.service

# View bootstrap node 2 logs
sudo journalctl -u bootstrap-node2.service

# View web server logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Local Development Environment

Before running any scripts, check your Python environment:

```bash
# Check Python environment
./check_environment.sh
```

This will verify that you have the correct Python version and required packages installed.

If you encounter "python: command not found" errors, ensure you're using `python3` instead of `python`:

```bash
# Install required packages
python3 -m pip install requests
```

## Troubleshooting

### Bootstrap Nodes Not Starting

If the bootstrap nodes fail to start:

1. Check the logs:
   ```bash
   sudo journalctl -u bootstrap-node1.service
   ```

2. Check permissions:
   ```bash
   sudo ls -la /opt/globalcoyn/bootstrap
   ```

3. Ensure the deploy user has access:
   ```bash
   sudo chown -R deploy:deploy /opt/globalcoyn/bootstrap
   ```

### Website Not Accessible

If the website is not accessible:

1. Check nginx status:
   ```bash
   sudo systemctl status nginx
   ```

2. Check website files:
   ```bash
   sudo ls -la /var/www/globalcoyn/frontend/build
   ```

3. Check permissions:
   ```bash
   sudo chown -R deploy:deploy /var/www/globalcoyn/frontend
   sudo chmod -R 755 /var/www/globalcoyn/frontend
   ```

4. Restart nginx:
   ```bash
   sudo systemctl restart nginx
   ```

### Python Issues on Local Machine

If you encounter Python-related errors when running the scripts:

1. Ensure you're using Python 3:
   ```bash
   python3 --version
   ```

2. Install required packages:
   ```bash
   python3 -m pip install requests
   ```

3. If you see "ModuleNotFoundError" errors, check that required modules are installed:
   ```bash
   python3 -m pip install <missing_module>
   ```

4. For script execution errors, make sure all scripts are executable:
   ```bash
   chmod +x *.sh
   ```

5. Run the environment check script to diagnose issues:
   ```bash
   ./check_environment.sh
   ```