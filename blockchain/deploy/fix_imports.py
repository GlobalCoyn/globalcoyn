#!/usr/bin/env python3
"""
Quick fix script for GlobalCoyn blockchain node imports
"""
import os
import sys
import shutil

print("GlobalCoyn Blockchain Import Fix Script")
print("======================================")

# Determine paths
install_dir = "/var/www/globalcoyn/blockchain"
core_dir = os.path.join(install_dir, "core")
node_dir = os.path.join(install_dir, "node")

print(f"Core directory: {core_dir}")
print(f"Node directory: {node_dir}")

# Ensure __init__.py files exist
for path in [
    os.path.join(install_dir, "__init__.py"),
    os.path.join(core_dir, "__init__.py"),
    os.path.join(node_dir, "__init__.py"),
    os.path.join(node_dir, "routes", "__init__.py")
]:
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)
        print(f"Created directory: {dirname}")
    
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("# Auto-generated __init__.py\n")
        print(f"Created: {path}")

# Create direct import wrapper for app.py
wrapper_path = os.path.join(node_dir, "direct_import_app.py")
with open(wrapper_path, "w") as f:
    f.write('''#!/usr/bin/env python3
"""
Direct import wrapper for GlobalCoyn blockchain node app.py
"""
import os
import sys

# Get directories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
core_dir = os.path.join(parent_dir, "core")

# Add to path
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, core_dir)

# Import core modules directly
try:
    # Try direct imports
    sys.path.insert(0, core_dir)
    from blockchain import Blockchain
    from transaction import Transaction
    from block import Block
    from wallet import Wallet
    from mempool import Mempool
    from mining import Miner
    from utils import bits_to_target, target_to_bits, validate_address_format
    from coin import Coin, CoinManager
    
    print("Successfully imported core modules directly")
    
    # Execute the original app.py
    with open(os.path.join(current_dir, "app.py")) as f:
        exec(f.read())
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
''')
print(f"Created wrapper script: {wrapper_path}")
os.chmod(wrapper_path, 0o755)
print(f"Made wrapper executable")

# Update service file
service_file = "/etc/systemd/system/globalcoyn-node.service"
service_content = '''[Unit]
Description=GlobalCoyn Blockchain Node
After=network.target

[Service]
User=deploy
Group=deploy
WorkingDirectory=/var/www/globalcoyn/blockchain/node
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/var/www/globalcoyn/blockchain:/var/www/globalcoyn/blockchain/core"
Environment="GCN_ENV=production"
Environment="GCN_NODE_NUM=1"
Environment="GCN_P2P_PORT=9000"
Environment="GCN_WEB_PORT=8001"
Environment="GCN_DOMAIN=globalcoyn.com"
Environment="GCN_USE_SSL=true"
Type=simple
ExecStart=/usr/bin/python3 /var/www/globalcoyn/blockchain/node/direct_import_app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
'''

print(f"Updating service file: {service_file}")
with open("temp_service", "w") as f:
    f.write(service_content)

print("Done! To apply the changes:")
print("1. Copy this service file to systemd:")
print("   sudo cp temp_service /etc/systemd/system/globalcoyn-node.service")
print("2. Set proper permissions:")
print("   sudo chown -R deploy:deploy /var/www/globalcoyn/blockchain")
print("3. Reload systemd and restart the service:")
print("   sudo systemctl daemon-reload")
print("   sudo systemctl start globalcoyn-node")
print("4. Check service status:")
print("   sudo systemctl status globalcoyn-node")