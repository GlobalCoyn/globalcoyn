#!/bin/bash
# Script to prepare the GlobalCoyn website for deployment to AWS EC2

echo "Preparing GlobalCoyn Website for Deployment"

# Set base directories
BLOCKCHAIN_DIR="/Users/adamneto/Desktop/blockchain/blockchain"
WEBSITE_DIR="$BLOCKCHAIN_DIR/website"
MACOS_APP_DIR="$BLOCKCHAIN_DIR/apps/macos_app"
DEPLOY_DIR="$BLOCKCHAIN_DIR/deploy"

# Create necessary directories
mkdir -p "$WEBSITE_DIR/downloads"
mkdir -p "$DEPLOY_DIR"

# Copy the DMG file to the website downloads directory
if [ -f "$MACOS_APP_DIR/dist/GlobalCoyn.dmg" ]; then
    echo "Copying DMG to website downloads..."
    cp "$MACOS_APP_DIR/dist/GlobalCoyn.dmg" "$WEBSITE_DIR/downloads/globalcoyn-macos.dmg"
else
    echo "WARNING: DMG file not found at $MACOS_APP_DIR/dist/GlobalCoyn.dmg"
    echo "Please run the create_dmg.sh script first"
    exit 1
fi

# Create a zip file of the website
echo "Creating website deployment package..."
cd "$BLOCKCHAIN_DIR"
zip -r "$DEPLOY_DIR/globalcoyn-website.zip" website

echo "Deployment package created at $DEPLOY_DIR/globalcoyn-website.zip"
echo "You can now upload this to your AWS EC2 server"

# Show deployment instructions
cat << 'EOF'

Deploy to AWS EC2:
-----------------
1. Upload the website package to your server:
   scp -i ~/Downloads/globalcoyn.pem "$DEPLOY_DIR/globalcoyn-website.zip" ec2-user@13.61.79.186:~

2. SSH into your server:
   ssh -i ~/Downloads/globalcoyn.pem ec2-user@13.61.79.186

3. Extract and deploy the website:
   unzip -o globalcoyn-website.zip
   sudo rm -rf /var/www/globalcoyn/frontend/build
   sudo mv website /var/www/globalcoyn/frontend/build
   sudo chown -R deploy:deploy /var/www/globalcoyn/frontend/build

4. Restart services:
   sudo systemctl restart nginx

EOF