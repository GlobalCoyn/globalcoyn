#!/bin/bash
# Script to deploy bootstrap nodes to the AWS EC2 server
# Usage: ./deploy_bootstrap_nodes.sh <server_ip> <username> <pem_file>

if [ $# -lt 3 ]; then
  echo "Usage: ./deploy_bootstrap_nodes.sh <server_ip> <username> <pem_file>"
  echo "Example: ./deploy_bootstrap_nodes.sh 13.61.79.186 ec2-user ~/Downloads/globalcoyn.pem"
  exit 1
fi

SERVER_IP=$1
USERNAME=$2
PEM_FILE=$3
SERVER_DIR="/opt/globalcoyn/bootstrap"

echo "Packaging bootstrap nodes..."
./package_bootstrap_node.sh 1
./package_bootstrap_node.sh 2

echo "Uploading bootstrap node packages..."
scp -i ${PEM_FILE} bootstrap_node_1.zip ${USERNAME}@${SERVER_IP}:~
scp -i ${PEM_FILE} bootstrap_node_2.zip ${USERNAME}@${SERVER_IP}:~

echo "Setting up bootstrap nodes on server..."
ssh -i ${PEM_FILE} ${USERNAME}@${SERVER_IP} << EOF
# Extract bootstrap node packages
unzip -o bootstrap_node_1.zip
unzip -o bootstrap_node_2.zip

# Set up bootstrap nodes - use python3 explicitly
cd bootstrap_node_1
# Fix the setup script to use python3 instead of python
sed -i 's/python/python3/g' setup.sh
# Install python-dotenv directly
pip3 install python-dotenv
./setup.sh
cd ../bootstrap_node_2
# Fix the setup script to use python3 instead of python
sed -i 's/python/python3/g' setup.sh
# Install python-dotenv directly
pip3 install python-dotenv
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
sudo mkdir -p ${SERVER_DIR}
sudo mv bootstrap_node_1 bootstrap_node_2 ${SERVER_DIR}/
sudo chown -R deploy:deploy ${SERVER_DIR}

# Reload systemd and start services
sudo systemctl daemon-reload
sudo systemctl enable bootstrap-node1.service bootstrap-node2.service
sudo systemctl start bootstrap-node1.service bootstrap-node2.service
EOF

echo "Checking bootstrap node status..."
ssh -i ${PEM_FILE} ${USERNAME}@${SERVER_IP} "sudo systemctl status bootstrap-node1.service"
ssh -i ${PEM_FILE} ${USERNAME}@${SERVER_IP} "sudo systemctl status bootstrap-node2.service"

echo "Bootstrap nodes deployed successfully!"
echo "You can check the status of the nodes with:"
echo "  ssh -i ${PEM_FILE} ${USERNAME}@${SERVER_IP} sudo systemctl status bootstrap-node1.service"
echo "  ssh -i ${PEM_FILE} ${USERNAME}@${SERVER_IP} sudo systemctl status bootstrap-node2.service"