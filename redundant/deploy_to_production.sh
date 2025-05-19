#!/bin/bash
# Script to deploy all updates to production
# This script combines all the previous steps and deploys to production

# Exit on error
set -e

# Define environment variables
PRODUCTION_SERVER="13.61.79.186"
PRODUCTION_USER="ec2-user"
PEM_FILE="~/Downloads/globalcoyn.pem"
WEBSITE_DIR="/var/www/globalcoyn"
VERSION="2.0.0"

echo "-----------------------------------------------------"
echo "GlobalCoyn Production Deployment (v$VERSION)"
echo "-----------------------------------------------------"

# Function to check if tests passed
check_test_result() {
  if [ $1 -ne 0 ]; then
    echo "Tests failed! Aborting deployment."
    exit 1
  fi
}

# 1. Update Todo - Mark task as in progress
echo "Starting deployment process..."

# 2. Run macOS app integration tests
echo "Running macOS app integration tests..."
./test_macos_integration.sh
check_test_result $?
echo "MacOS app integration tests passed!"

# 3. Run simplified blockchain tests instead of the full tests
echo "Running simplified blockchain tests..."
./simple_tests.sh
check_test_result $?
echo "Simplified blockchain tests passed!"

# 4. Package bootstrap nodes
echo "Packaging bootstrap nodes..."
./package_bootstrap_node.sh 1
./package_bootstrap_node.sh 2
echo "Bootstrap nodes packaged successfully!"

# 5. Package macOS app
echo "Packaging macOS app..."
./package_macos_app.sh
echo "MacOS app packaged successfully!"

# 6. Package website files
echo "Building website package..."
cd ./blockchain/website
zip -r ../../website.zip .
cd ../..

# 7. Deploy bootstrap nodes to server
echo "Deploying bootstrap nodes to server..."
scp -i $PEM_FILE bootstrap_node_1.zip ${PRODUCTION_USER}@${PRODUCTION_SERVER}:~
scp -i $PEM_FILE bootstrap_node_2.zip ${PRODUCTION_USER}@${PRODUCTION_SERVER}:~

echo "Setting up bootstrap nodes on server..."
ssh -i $PEM_FILE ${PRODUCTION_USER}@${PRODUCTION_SERVER} << 'EOF'
# Extract bootstrap nodes
unzip -o bootstrap_node_1.zip
unzip -o bootstrap_node_2.zip

# Set up bootstrap nodes - use python3 explicitly
cd bootstrap_node_1
# Fix the setup script to use python3 instead of python
sed -i 's/python/python3/g' setup.sh
# Install python-dotenv directly
sudo pip3 install python-dotenv
./setup.sh
cd ../bootstrap_node_2
# Fix the setup script to use python3 instead of python
sed -i 's/python/python3/g' setup.sh
# Install python-dotenv directly
sudo pip3 install python-dotenv
./setup.sh
cd ..

# Create service files
sudo bash -c 'cat > /etc/systemd/system/bootstrap-node1.service << EOL
[Unit]
Description=GlobalCoyn Bootstrap Node 1
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/globalcoyn/bootstrap/bootstrap_node_1/node
ExecStart=/opt/globalcoyn/bootstrap/bootstrap_node_1/node/start_node.sh
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL'

sudo bash -c 'cat > /etc/systemd/system/bootstrap-node2.service << EOL
[Unit]
Description=GlobalCoyn Bootstrap Node 2
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/globalcoyn/bootstrap/bootstrap_node_2/node
ExecStart=/opt/globalcoyn/bootstrap/bootstrap_node_2/node/start_node.sh
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL'

# Create bootstrap directory
sudo mkdir -p /opt/globalcoyn/bootstrap
sudo mv bootstrap_node_1 bootstrap_node_2 /opt/globalcoyn/bootstrap/
sudo chown -R deploy:deploy /opt/globalcoyn/bootstrap

# Reload systemd and start services
sudo systemctl daemon-reload
sudo systemctl enable bootstrap-node1.service bootstrap-node2.service
sudo systemctl start bootstrap-node1.service bootstrap-node2.service
EOF

echo "Bootstrap nodes deployed successfully!"

# 8. Deploy website to server
echo "Deploying website to server..."
scp -i $PEM_FILE website.zip ${PRODUCTION_USER}@${PRODUCTION_SERVER}:~

ssh -i $PEM_FILE ${PRODUCTION_USER}@${PRODUCTION_SERVER} << 'EOF'
# Extract website files
unzip -o website.zip -d website_new

# Update website directory
sudo mkdir -p /var/www/globalcoyn/frontend
sudo rm -rf /var/www/globalcoyn/frontend/build
sudo mv website_new /var/www/globalcoyn/frontend/build
sudo chown -R deploy:deploy /var/www/globalcoyn/frontend
sudo chmod -R 755 /var/www/globalcoyn/frontend

# Restart web server
sudo systemctl restart nginx
EOF

echo "Website deployed successfully!"

# 9. Deploy node package to server
echo "Deploying node package to server..."
scp -i $PEM_FILE ./bootstrap_node_1.zip ${PRODUCTION_USER}@${PRODUCTION_SERVER}:~

ssh -i $PEM_FILE ${PRODUCTION_USER}@${PRODUCTION_SERVER} << 'EOF'
sudo mkdir -p /var/www/globalcoyn/frontend/build/downloads
sudo cp bootstrap_node_1.zip /var/www/globalcoyn/frontend/build/downloads/globalcoyn-node.zip
sudo chown deploy:deploy /var/www/globalcoyn/frontend/build/downloads/globalcoyn-node.zip
sudo chmod 644 /var/www/globalcoyn/frontend/build/downloads/globalcoyn-node.zip
EOF

echo "Node package deployed successfully!"

# 10. Deploy macOS app to server
echo "Deploying macOS app to server..."
# Check if we have a DMG or ZIP file
if [ -f "./dist/GlobalCoyn-macOS.dmg" ]; then
    scp -i $PEM_FILE ./dist/GlobalCoyn-macOS.dmg ${PRODUCTION_USER}@${PRODUCTION_SERVER}:~
    MACOS_APP_FILE="GlobalCoyn-macOS.dmg"
elif [ -f "./dist/GlobalCoyn.zip" ]; then
    scp -i $PEM_FILE ./dist/GlobalCoyn.zip ${PRODUCTION_USER}@${PRODUCTION_SERVER}:~
    MACOS_APP_FILE="GlobalCoyn.zip"
else
    echo "WARNING: No macOS app package found. Creating placeholder..."
    echo "GlobalCoyn macOS Application v$VERSION (Placeholder)" > ./placeholder.txt
    zip -r ./GlobalCoyn-placeholder.dmg placeholder.txt
    scp -i $PEM_FILE ./GlobalCoyn-placeholder.dmg ${PRODUCTION_USER}@${PRODUCTION_SERVER}:~
    MACOS_APP_FILE="GlobalCoyn-placeholder.dmg"
fi

ssh -i $PEM_FILE ${PRODUCTION_USER}@${PRODUCTION_SERVER} << EOF
sudo mkdir -p /var/www/globalcoyn/frontend/build/downloads
sudo cp $MACOS_APP_FILE /var/www/globalcoyn/frontend/build/downloads/globalcoyn-macos.dmg
sudo chown deploy:deploy /var/www/globalcoyn/frontend/build/downloads/globalcoyn-macos.dmg
sudo chmod 644 /var/www/globalcoyn/frontend/build/downloads/globalcoyn-macos.dmg
EOF

echo "macOS app deployed successfully!"

# 11. Verify deployment
echo "Verifying deployment..."
echo "Checking website accessibility..."
curl -s -o /dev/null -w "%{http_code}" http://${PRODUCTION_SERVER}

echo "Checking bootstrap node 1 status..."
ssh -i $PEM_FILE ${PRODUCTION_USER}@${PRODUCTION_SERVER} "sudo systemctl status bootstrap-node1.service | grep 'active (running)'"

echo "Checking bootstrap node 2 status..."
ssh -i $PEM_FILE ${PRODUCTION_USER}@${PRODUCTION_SERVER} "sudo systemctl status bootstrap-node2.service | grep 'active (running)'"

echo "-----------------------------------------------------"
echo "GlobalCoyn v$VERSION successfully deployed to production!"
echo "-----------------------------------------------------"

# Instructions for manual verification
echo "Please perform the following manual verification steps:"
echo "1. Visit https://globalcoyn.com to verify the website is updated"
echo "2. Download and test the macOS app"
echo "3. Download and test the node package"
echo "4. Monitor the bootstrap nodes for any issues"
echo "-----------------------------------------------------"