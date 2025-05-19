# GlobalCoyn Frontend Deployment Guide

This guide explains how to build and deploy the GlobalCoyn frontend web application to your production server.

## Prerequisites

- Node.js (v14+) 
- npm (v6+)
- Access to the GlobalCoyn EC2 server
- SSH key for the server (`globalcoyn.pem`)

## Configuration

The frontend is configured to automatically switch between development and production modes based on the environment:

- In development mode, API calls are directed to `http://localhost:8001/api`
- In production mode, API calls are directed to `https://globalcoyn.com/api`

The production mode is activated in one of two ways:
1. The `NODE_ENV` environment variable is set to `production` during build
2. The app is running on a domain matching `globalcoyn.com`

## Build Process

### 1. Prepare the Environment

Make sure your `.env.production` file has the correct values:

```
REACT_APP_API_URL=https://globalcoyn.com/api
REACT_APP_WS_URL=wss://globalcoyn.com/ws
REACT_APP_ENV=production
REACT_APP_DOMAIN=globalcoyn.com
```

### 2. Run the Build Script

We've created a build script that automates the process:

```bash
cd /Users/adamneto/Desktop/blockchain/blockchain/website/app
./build_frontend.sh
```

This script will:
1. Install dependencies
2. Create a production environment file if needed
3. Build the frontend with production settings
4. Create a ZIP file of the build in ~/Downloads/globalcoyn-frontend-build/

### 3. Deploy to Server

After building, transfer the package to your server:

```bash
# Transfer the build package
scp -i ~/Downloads/globalcoyn.pem ~/Downloads/globalcoyn-frontend-build/frontend-build.zip ec2-user@13.61.79.186:~

# SSH into the server
ssh -i ~/Downloads/globalcoyn.pem ec2-user@13.61.79.186
```

Once logged in to the server, deploy the frontend:

```bash
# Extract the build
unzip -o frontend-build.zip

# Set up the frontend directory
sudo mkdir -p /var/www/globalcoyn/frontend
sudo rm -rf /var/www/globalcoyn/frontend/build
sudo mv build /var/www/globalcoyn/frontend/

# Set proper ownership
sudo chown -R deploy:deploy /var/www/globalcoyn/frontend/build

# Restart Nginx to apply changes
sudo systemctl restart nginx
```

## Verify Deployment

Open a web browser and navigate to `https://globalcoyn.com` to verify that the application is running correctly.

Check the following functionality:
- Homepage loads correctly
- Blockchain explorer works
- Wallet creation and management
- Transaction creation and submission
- Mining interface

## Troubleshooting

### Common Issues

1. **404 Not Found**: Check Nginx configuration and ensure it's properly configured to serve the React application.

2. **API Endpoints Not Responding**: Verify that the blockchain node is running and properly configured.

3. **CORS Errors**: Ensure the blockchain node's CORS settings include the frontend domain.

4. **JavaScript Errors**: Check the browser console for any JavaScript errors.

### How to Check Logs

```bash
# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Blockchain node logs 
sudo journalctl -u globalcoyn-node -f
```

## Rollback Procedure

If the deployment fails, you can rollback to the previous version:

```bash
# SSH into the server
ssh -i ~/Downloads/globalcoyn.pem ec2-user@13.61.79.186

# Restore previous build from backup
sudo cp -r /var/backups/globalcoyn/frontend/build_latest /var/www/globalcoyn/frontend/build
sudo chown -R deploy:deploy /var/www/globalcoyn/frontend/build
sudo systemctl restart nginx
```