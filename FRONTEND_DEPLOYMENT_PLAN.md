# GlobalCoyn Frontend Deployment Plan

This document outlines the steps to build and deploy the GlobalCoyn frontend website to connect with the running API endpoints on the production server.

## 1. Prerequisites

- Local development environment with:
  - Node.js and npm installed
  - Access to the repository codebase
- SSH access to the EC2 server
- The bootstrap nodes are already running with API endpoints accessible

## 2. Update API Configuration

First, let's verify that the API configuration is pointing to the correct production endpoints:

1. Check the config file:
   ```bash
   cat /Users/adamneto/Desktop/blockchain/website/app/src/config.js
   ```

2. Ensure it contains the proper production API URL:
   ```javascript
   // Configuration based on environment
   const isProd = window.location.hostname === 'globalcoyn.com' || process.env.NODE_ENV === 'production';
   
   export const API_URL = isProd 
     ? 'https://globalcoyn.com/api'
     : 'http://localhost:8001/api';
   
   export const EXPLORER_URL = isProd
     ? 'https://globalcoyn.com/explorer'
     : 'http://localhost:8001/explorer';
   ```

3. If needed, update the configuration:
   ```bash
   nano /Users/adamneto/Desktop/blockchain/website/app/src/config.js
   ```

## 3. Build the Frontend

1. Navigate to the frontend app directory:
   ```bash
   cd /Users/adamneto/Desktop/blockchain/website/app
   ```

2. Install dependencies (if not already done):
   ```bash
   npm install
   ```

3. Build the production version:
   ```bash
   npm run build
   ```

   This will create a `build` directory with optimized production files.

## 4. Package the Build

1. Create a deployment zip file:
   ```bash
   cd /Users/adamneto/Desktop/blockchain/website/app
   zip -r frontend-build.zip build
   ```

## 5. Transfer to Server

1. Transfer the build package to the EC2 server:
   ```bash
   scp -i /path/to/your-key.pem frontend-build.zip ec2-user@globalcoyn.com:~
   ```

## 6. Deploy on Server

SSH into the server and deploy the frontend:

```bash
ssh -i /path/to/your-key.pem ec2-user@globalcoyn.com
```

Then run the following commands:

```bash
# Create deployment directory if it doesn't exist
sudo mkdir -p /var/www/globalcoyn/html

# Unzip the build package
unzip ~/frontend-build.zip -d ~/frontend-temp

# Deploy the new build
sudo rm -rf /var/www/globalcoyn/html/*
sudo cp -r ~/frontend-temp/build/* /var/www/globalcoyn/html/

# Set proper permissions
sudo chown -R ec2-user:ec2-user /var/www/globalcoyn/html
sudo chmod -R 755 /var/www/globalcoyn/html

# Clean up
rm -rf ~/frontend-temp
rm ~/frontend-build.zip
```

## 7. Test the Deployment

1. Open a web browser and navigate to your domain:
   ```
   https://globalcoyn.com
   ```

2. Verify the following functionality:
   - Home page loads correctly
   - Navigation works
   - Wallet interface loads
   - Transaction history appears with clickable links
   - Block explorer works
   - API connections are successful

3. Test the transaction links functionality:
   - Click on transaction IDs to ensure they link to the proper transaction detail page
   - Click on wallet addresses to ensure they link to the proper address detail page

## 8. Troubleshooting

If you encounter issues:

1. Check browser console for JavaScript errors
2. Verify Nginx logs:
   ```bash
   sudo tail -n 100 /var/log/nginx/error.log
   ```

3. Verify that the API endpoints are accessible:
   ```bash
   curl -X GET https://globalcoyn.com/api/blockchain -H "Content-Type: application/json"
   ```

4. Check if the frontend is trying to access the correct API URL:
   - Open the browser's network inspector
   - Look for API requests and verify they're going to the right domain

5. Verify CORS configuration on the backend:
   ```bash
   # Check bootstrap node CORS configuration
   cat /home/ec2-user/bootstrap_node_1/cors_setup.py
   ```

## 9. Monitoring

After deployment, monitor the system:

1. Set up basic monitoring:
   ```bash
   # Check server load
   top
   
   # Check disk space
   df -h
   
   # Check NodeJS processes
   ps aux | grep node
   
   # Check Python processes (bootstrap nodes)
   ps aux | grep python
   ```

2. Monitor server logs:
   ```bash
   # Nginx access logs
   sudo tail -f /var/log/nginx/access.log
   
   # Bootstrap node logs
   tail -f /home/ec2-user/bootstrap_node_1/blockchain.log
   ```

## 10. Additional Considerations

1. **CDN Setup (Optional)**: Consider setting up a CDN for static assets
2. **Backup Procedure**: Regularly backup your blockchain data
3. **Auto-scaling**: Consider setting up auto-scaling for your application in the future
4. **Regular Updates**: Plan for regular frontend updates and a proper CI/CD pipeline