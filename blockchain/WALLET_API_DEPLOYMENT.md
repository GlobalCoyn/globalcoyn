# GlobalCoyn Wallet API Deployment Guide

This document outlines the changes made to implement wallet functionality in the GlobalCoyn blockchain network, and provides instructions for deploying these changes to the bootstrap nodes.

## Implementation Overview

1. **Wallet Routes API**: Created `wallet_routes.py` which implements various wallet-related API endpoints:
   - `/api/wallet/create` - Create a new wallet address
   - `/api/wallet/generate-seed` - Generate a new BIP-39 seed phrase
   - `/api/wallet/import/seed` - Import wallet using seed phrase
   - `/api/wallet/import/key` - Import wallet using private key
   - `/api/wallet/export-key` - Export private key for a wallet address
   - `/api/wallet/list` - List all wallet addresses
   - `/api/wallet/balance/<address>` - Get balance for a specific wallet address
   - `/api/wallet/transactions/<address>` - Get transactions for a wallet address
   - `/api/wallet/fee-estimate` - Get fee estimate for transactions
   - `/api/wallet/sign-transaction` - Sign a transaction with the wallet's private key

2. **Frontend Integration**: Updated the `walletService.js` file to use the new wallet API endpoints:
   - Updated `createWallet()` to use the wallet API
   - Updated `importWalletFromSeed()` to use the wallet API
   - Updated `importWalletFromPrivateKey()` to use the wallet API
   - Updated `getBalance()` to use the wallet API
   - Updated `getTransactions()` to use the wallet API

3. **Deployment Script**: Created a deployment script to streamline the installation of the wallet routes on the bootstrap nodes.

## Deployment Instructions

### Step 1: Copy Deployment Files to EC2 Instance

First, copy the deployment script to your Downloads folder where the PEM file is located:

```bash
cp /Users/adamneto/Desktop/blockchain/blockchain/scripts/deploy_wallet_routes.sh ~/Downloads/
```

Navigate to the Downloads folder and copy the deployment script to the EC2 instance using the PEM file:

```bash
cd ~/Downloads
scp -i your-key-file.pem deploy_wallet_routes.sh ec2-user@13.61.79.186:~/
```

Replace `your-key-file.pem` with the actual name of your PEM file.

### Step 2: Execute the Deployment Script

SSH to the EC2 instance using the PEM file:

```bash
ssh -i globalcoyn.pem ec2-user@13.61.79.186
chmod +x deploy_wallet_routes.sh
sudo ./deploy_wallet_routes.sh
```

This script will:
- Create the routes directory in both bootstrap nodes if it doesn't exist
- Copy the wallet_routes.py file to both bootstrap nodes
- Update the app.py files to import and register the wallet routes blueprint
- Create __init__.py files in the routes directories
- Restart both bootstrap nodes to apply the changes

### Step 3: Verify Deployment

Test the wallet API endpoints after deployment:

```bash
# Check if the wallet API is responding
curl -s http://13.61.79.186:8001/api/wallet/fee-estimate | python3 -m json.tool

# Generate a new seed phrase
curl -s http://13.61.79.186:8001/api/wallet/generate-seed | python -m json.tool
```

Expected output for the fee estimate:
```json
{
  "success": true,
  "feeEstimate": 0.001
}
```

Expected output for the seed phrase generation:
```json
{
  "success": true,
  "seedPhrase": "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12"
}
```

### Step 4: Deploy Frontend Changes

The frontend `walletService.js` file has been updated to use the new wallet API endpoints. 
First, copy the file to your Downloads folder:

```bash
cp /Users/adamneto/Desktop/blockchain/blockchain/website/app/src/services/walletService.js ~/Downloads/
```

Then, from your Downloads folder, deploy the updated file to the web server using the PEM file:

```bash
cd ~/Downloads
scp -i your-key-file.pem walletService.js ec2-user@13.61.79.186:~/website/app/src/services/
```

Then SSH to the EC2 instance and restart the web server:

```bash
ssh -i your-key-file.pem ec2-user@13.61.79.186
cd ~/website
npm run build
```

## Troubleshooting

If you encounter issues after deployment:

1. **Check Bootstrap Node Logs**:
   ```bash
   sudo systemctl status globalcoyn-bootstrap1
   sudo systemctl status globalcoyn-bootstrap2
   
   # View logs
   sudo journalctl -u globalcoyn-bootstrap1 -n 50
   sudo journalctl -u globalcoyn-bootstrap2 -n 50
   ```

2. **Check Module Imports**:
   If there are import errors, ensure the PYTHONPATH is correctly set in the systemd service files:
   ```bash
   sudo cat /etc/systemd/system/globalcoyn-bootstrap1.service
   sudo cat /etc/systemd/system/globalcoyn-bootstrap2.service
   ```

3. **Check API Accessibility**:
   Test if the API endpoints are accessible from the EC2 instance:
   ```bash
   curl -s http://localhost:8001/api/wallet/fee-estimate | python -m json.tool
   curl -s http://localhost:8002/api/wallet/fee-estimate | python -m json.tool
   ```

4. **Check Nginx Configuration**:
   Ensure Nginx is correctly configured to proxy requests to the bootstrap nodes:
   ```bash
   sudo cat /etc/nginx/conf.d/globalcoyn.conf
   sudo nginx -t  # Test Nginx configuration
   sudo systemctl restart nginx  # Restart Nginx if needed
   ```

## Additional Notes

- The wallet API uses the core `wallet.py` module from the GlobalCoyn blockchain project
- All wallet operations are performed on the bootstrap nodes, ensuring proper integration with the blockchain
- Frontend changes maintain compatibility with the existing UI components
- Error handling and fallback mechanisms are implemented to ensure robustness