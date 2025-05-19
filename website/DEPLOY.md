# GlobalCoyn Web Frontend Deployment Guide

This guide explains how to build and deploy the GlobalCoyn web frontend application.

## Prerequisites

- Node.js (v14+)
- npm (v6+)
- Access to the GlobalCoyn EC2 server
- SSH key for the server (`globalcoyn.pem`)

## Build Process

### 1. Update API Configuration

Before building, ensure the API configuration points to the production API endpoints:

Edit `src/config.js` (or equivalent file) to update the API base URL:

```javascript
// Change from local development URLs to production
const API_BASE_URL = "https://globalcoyn.com/api";

export const API_ENDPOINTS = {
  BLOCKCHAIN: `${API_BASE_URL}/blockchain`,
  NETWORK: `${API_BASE_URL}/network`,
  WALLET: `${API_BASE_URL}/wallet`,
  MINING: `${API_BASE_URL}/mining`,
  TRANSACTIONS: `${API_BASE_URL}/transactions`,
};
```

### 2. Build the Application

Follow these steps to build the application:

```bash
# Navigate to the project directory
cd ~/Downloads/globalcoyn-frontend

# Install dependencies
npm install

# Build the application
npm run build
```

The build process will create a `build` directory with optimized production files.

### 3. Package the Build

Create a zip archive of the build folder:

```bash
# Create zip archive
cd ~/Downloads/globalcoyn-frontend
zip -r build.zip build/
```

## Deployment Process

### 1. Transfer the Build to the Server

```bash
# Upload the build.zip to the EC2 server
scp -i ~/Downloads/globalcoyn.pem ~/Downloads/globalcoyn-frontend/build.zip ec2-user@13.61.79.186:~
```

### 2. Deploy on the Server

SSH into the server and deploy the application:

```bash
# SSH into the server
ssh -i ~/Downloads/globalcoyn.pem ec2-user@13.61.79.186

# Once logged in to the server, run these commands:
unzip -o build.zip
sudo rm -rf /var/www/globalcoyn/frontend/build
sudo mv build /var/www/globalcoyn/frontend/
sudo chown -R deploy:deploy /var/www/globalcoyn/frontend/build
sudo systemctl restart globalcoyn  # If you have a service for the frontend
sudo systemctl restart nginx
```

### 3. Verify Deployment

Open a web browser and navigate to https://globalcoyn.com to verify that the application is running correctly.

Check the following functionalities:
- Homepage loads correctly
- Blockchain explorer works
- Wallet creation and management
- Transaction creation and submission
- Mining interface

## Troubleshooting

### Common Issues

1. **404 Not Found**: Check Nginx configuration and ensure it's properly configured to serve the React application.

2. **API Endpoints Not Responding**: Verify that the blockchain node is running and properly configured. Check Nginx proxy settings.

3. **CORS Errors**: Ensure the blockchain node's CORS settings include the frontend domain.

4. **JavaScript Errors**: Check the browser console for any JavaScript errors. It might indicate issues with the build.

### How to Check Logs

```bash
# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Frontend application logs (if applicable)
sudo journalctl -u globalcoyn -f

# Blockchain node logs
sudo tail -f /var/www/globalcoyn/blockchain/node/blockchain.log
```

## Rollback Procedure

If the deployment fails, you can rollback to the previous version:

```bash
# SSH into the server
ssh -i ~/Downloads/globalcoyn.pem ec2-user@13.61.79.186

# Restore previous build from backup
sudo rm -rf /var/www/globalcoyn/frontend/build
sudo cp -r /var/www/globalcoyn/frontend/build_backup /var/www/globalcoyn/frontend/build
sudo chown -R deploy:deploy /var/www/globalcoyn/frontend/build
sudo systemctl restart nginx
```

## Regular Maintenance

Consider setting up the following maintenance procedures:

1. **Regular Backups**: Backup the blockchain data regularly.
2. **Log Rotation**: Ensure logs don't fill up disk space.
3. **Updates**: Regularly update dependencies and security patches.
4. **Monitoring**: Set up monitoring for the application and server.