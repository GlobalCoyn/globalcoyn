#!/bin/bash
# Frontend Deployment Script for GlobalCoyn

# Exit on any error
set -e

# Config
WEBSITE_DIR="/Users/adamneto/Desktop/blockchain/blockchain/website/app"
EC2_USER="ec2-user"
EC2_HOST="13.61.79.186"  # IP address instead of domain name
SSH_KEY_PATH="~/Downloads/globalcoyn.pem"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}GlobalCoyn Frontend Deployment Script${NC}"
echo "================================================"

# 1. Check if we can access the website directory
if [ ! -d "$WEBSITE_DIR" ]; then
  echo -e "${RED}Error: Website directory not found at $WEBSITE_DIR${NC}"
  exit 1
fi

# 2. Build the frontend
echo -e "${YELLOW}Building frontend application...${NC}"
cd "$WEBSITE_DIR"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install
fi

# Build the application
echo "Creating production build..."
npm run build

if [ ! -d "build" ]; then
  echo -e "${RED}Error: Build failed, no build directory found${NC}"
  exit 1
fi

echo -e "${GREEN}Build completed successfully!${NC}"

# 3. Package the build
echo -e "${YELLOW}Packaging build for deployment...${NC}"
cd "$WEBSITE_DIR"
rm -f frontend-build.zip
zip -r frontend-build.zip build

echo -e "${GREEN}Package created: frontend-build.zip${NC}"

# 4. Transfer to server
echo -e "${YELLOW}Transferring build to EC2 server...${NC}"
echo "This may take a few minutes depending on your connection speed."

scp -i "$SSH_KEY_PATH" frontend-build.zip "$EC2_USER@$EC2_HOST:~/"

echo -e "${GREEN}Transfer completed!${NC}"

# 5. Deploy on the server
echo -e "${YELLOW}Deploying frontend on the server...${NC}"

# SSH to the server and deploy
ssh -i "$SSH_KEY_PATH" "$EC2_USER@$EC2_HOST" << 'EOF'
set -e

# Create deployment directory if it doesn't exist
sudo mkdir -p /var/www/globalcoyn/html

# Unzip the build package
echo "Extracting frontend build..."
unzip -q ~/frontend-build.zip -d ~/frontend-temp

# Deploy the new build
echo "Deploying new frontend..."
sudo rm -rf /var/www/globalcoyn/html/*
sudo cp -r ~/frontend-temp/build/* /var/www/globalcoyn/html/

# Set proper permissions
sudo chown -R ec2-user:ec2-user /var/www/globalcoyn/html
sudo chmod -R 755 /var/www/globalcoyn/html

# Clean up
echo "Cleaning up temporary files..."
rm -rf ~/frontend-temp
rm ~/frontend-build.zip

echo "Restarting Nginx..."
sudo systemctl restart nginx

echo "Deployment completed successfully!"
EOF

echo -e "${GREEN}Frontend deployment completed!${NC}"
echo "================================================"
echo -e "You can now access your application at: ${YELLOW}https://globalcoyn.com${NC}"
echo -e "Please verify the following functionality:"
echo " - Home page loads correctly"
echo " - Wallet interface loads with transaction links"
echo " - Clicking on transaction IDs navigates to transaction details"
echo " - Clicking on wallet addresses navigates to address details"
echo " - API connections are successful"
echo "================================================"