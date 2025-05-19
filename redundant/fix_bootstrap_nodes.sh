#!/bin/bash
# Script to fix bootstrap nodes on AWS EC2 server
# Usage: ./fix_bootstrap_nodes.sh <server_ip> <username> <pem_file>

if [ $# -lt 3 ]; then
  echo "Usage: ./fix_bootstrap_nodes.sh <server_ip> <username> <pem_file>"
  echo "Example: ./fix_bootstrap_nodes.sh 13.61.79.186 ec2-user ~/Downloads/globalcoyn.pem"
  exit 1
fi

SERVER_IP=$1
USERNAME=$2
PEM_FILE=$3

echo "Connecting to server and fixing bootstrap nodes..."
ssh -i ${PEM_FILE} ${USERNAME}@${SERVER_IP} << 'EOF'
# Create deploy user if it doesn't exist
if ! id -u deploy &>/dev/null; then
  echo "Creating deploy user..."
  sudo useradd -m deploy
  sudo usermod -aG wheel deploy
fi

# Modify start_node.sh for both bootstrap nodes to run in background
for node_num in 1 2; do
  node_dir="/opt/globalcoyn/bootstrap/bootstrap_node_${node_num}/node"
  
  if [ -d "$node_dir" ]; then
    echo "Updating start_node.sh for bootstrap_node_${node_num}..."
    
    # Fix the start_node.sh script to run in the background with nohup
    sudo bash -c "cat > ${node_dir}/start_node.sh << 'SCRIPT'
#!/bin/bash
# Blockchain Node Startup Script

# Fixed configuration for Node ${node_num}
NODE_NUM=${node_num}
P2P_PORT=9000
WEB_PORT=800${node_num}

echo \"Starting Blockchain Node \$NODE_NUM\" >> \${PWD}/bootstrap.log
echo \"P2P Port: \$P2P_PORT\" >> \${PWD}/bootstrap.log
echo \"Web Port: \$WEB_PORT\" >> \${PWD}/bootstrap.log
date >> \${PWD}/bootstrap.log

# Set environment variables
export GCN_NODE_NUM=\$NODE_NUM
export GCN_P2P_PORT=\$P2P_PORT
export GCN_WEB_PORT=\$WEB_PORT

# Start the node and keep it running
nohup python3 app.py >> \${PWD}/bootstrap.log 2>&1 &
echo \$! > \${PWD}/node.pid
echo \"Node started with PID: \$(cat \${PWD}/node.pid)\" >> \${PWD}/bootstrap.log
SCRIPT"
    
    # Make it executable
    sudo chmod +x ${node_dir}/start_node.sh
    
    # Ensure proper ownership
    sudo chown -R ec2-user:ec2-user ${node_dir}
  else
    echo "Warning: Node directory ${node_dir} not found"
  fi
done

# Update systemd service files to use ec2-user instead of deploy
for node_num in 1 2; do
  service_file="/etc/systemd/system/bootstrap-node${node_num}.service"
  
  echo "Updating service file for bootstrap-node${node_num}..."
  sudo bash -c "cat > ${service_file} << EOL
[Unit]
Description=GlobalCoyn Bootstrap Node ${node_num}
After=network.target

[Service]
Type=forking
User=ec2-user
Group=ec2-user
WorkingDirectory=/opt/globalcoyn/bootstrap/bootstrap_node_${node_num}/node
ExecStart=/opt/globalcoyn/bootstrap/bootstrap_node_${node_num}/node/start_node.sh
PIDFile=/opt/globalcoyn/bootstrap/bootstrap_node_${node_num}/node/node.pid
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL"
done

# Fix app.py to ensure it doesn't exit immediately
for node_num in 1 2; do
  app_file="/opt/globalcoyn/bootstrap/bootstrap_node_${node_num}/node/app.py"
  
  if [ -f "$app_file" ]; then
    echo "Checking app.py to ensure it runs as a persistent service..."
    
    # Check if it has a '__main__' block at the end
    if grep -q "__name__ == \"__main__\"" "$app_file"; then
      # Make a backup
      sudo cp "$app_file" "${app_file}.backup"
      
      # Add or update run command to ensure it's persistent
      if grep -q "app.run(host='0.0.0.0'" "$app_file"; then
        # Already has a run command, make sure it's set to run indefinitely
        sudo sed -i "s/app.run(host='0.0.0.0'.*/app.run(host='0.0.0.0', port=int(os.environ.get('GCN_WEB_PORT', 8001)), debug=False, threaded=True)/g" "$app_file"
      else
        # Add the run command at the end of the __main__ block
        sudo bash -c "cat >> ${app_file} << 'APP_CODE'
    # Ensure the app runs indefinitely
    app.run(host='0.0.0.0', port=int(os.environ.get('GCN_WEB_PORT', 8001)), debug=False, threaded=True)
APP_CODE"
      fi
    fi
  else
    echo "Warning: App file ${app_file} not found"
  fi
done

# Reload systemd and restart services
sudo systemctl daemon-reload
sudo systemctl restart bootstrap-node1.service bootstrap-node2.service

# Check status
echo -e "\nChecking bootstrap node status:"
sudo systemctl status bootstrap-node1.service | head -20
sudo systemctl status bootstrap-node2.service | head -20

# Check process
echo -e "\nChecking for running python processes:"
ps aux | grep python | grep -v grep

# Check logs
echo -e "\nChecking bootstrap node logs:"
for node_num in 1 2; do
  log_file="/opt/globalcoyn/bootstrap/bootstrap_node_${node_num}/node/bootstrap.log"
  if [ -f "$log_file" ]; then
    echo -e "\nLast 10 lines of bootstrap_node_${node_num} log:"
    tail -10 "$log_file"
  fi
done
EOF

echo -e "\nBootstrap node fix script completed!"
echo "You can check the status of the nodes with:"
echo "  ssh -i ${PEM_FILE} ${USERNAME}@${SERVER_IP} sudo systemctl status bootstrap-node1.service"
echo "  ssh -i ${PEM_FILE} ${USERNAME}@${SERVER_IP} sudo systemctl status bootstrap-node2.service"