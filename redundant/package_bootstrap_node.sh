#!/bin/bash
# Script to package a bootstrap node for deployment
# Usage: ./package_bootstrap_node.sh <node_number>

if [ -z "$1" ]; then
  echo "Usage: ./package_bootstrap_node.sh <node_number>"
  echo "Example: ./package_bootstrap_node.sh 1"
  exit 1
fi

NODE_NUMBER=$1
PACKAGE_NAME="bootstrap_node_${NODE_NUMBER}"
TEMP_DIR="/tmp/${PACKAGE_NAME}"
TARGET_FILE="${PACKAGE_NAME}.zip"

echo "Packaging bootstrap node ${NODE_NUMBER}..."

# Create temp directory
mkdir -p $TEMP_DIR

# Copy necessary files
cp -r blockchain/network/bootstrap_config.py $TEMP_DIR/
cp -r blockchain/network/dns_seed.py $TEMP_DIR/
cp -r blockchain/network/seed_nodes.py $TEMP_DIR/
cp -r blockchain/network/setup_bootstrap_node.py $TEMP_DIR/
cp -r blockchain/network/connection_backoff.py $TEMP_DIR/
cp -r blockchain/network/improved_node_sync.py $TEMP_DIR/
cp -r blockchain/core/blockchain.py $TEMP_DIR/
cp -r blockchain/core/coin.py $TEMP_DIR/
cp -r blockchain/core/wallet.py $TEMP_DIR/
cp -r blockchain/core/price_oracle.py $TEMP_DIR/

# Create node template
mkdir -p $TEMP_DIR/node
cp -r blockchain/nodes/node1/app.py $TEMP_DIR/node/
cp -r blockchain/nodes/node1/routes $TEMP_DIR/node/
cp -r blockchain/nodes/node1/requirements.txt $TEMP_DIR/node/
cp -r blockchain/nodes/node1/start_node.sh $TEMP_DIR/node/
chmod +x $TEMP_DIR/node/start_node.sh

# Create production configuration file
cat > $TEMP_DIR/node/node_config.json << EOL
{
  "is_bootstrap_node": true,
  "node_number": ${NODE_NUMBER},
  "production_mode": true,
  "p2p_port": 9000,
  "web_port": 8001,
  "max_peers": 100,
  "max_inbound": 80,
  "max_outbound": 20,
  "db_cache_size": 500
}
EOL

# Create setup script
cat > $TEMP_DIR/setup.sh << EOL
#!/bin/bash
# Setup script for bootstrap node ${NODE_NUMBER}

# Install dependencies
pip install -r node/requirements.txt

# Configure the node
python -c "
import sys
sys.path.append('.')
from bootstrap_config import BootstrapNodeManager
manager = BootstrapNodeManager('node/node_config.json')
manager.configure_as_bootstrap_node(${NODE_NUMBER})
manager.setup_bootstrap_node(9000, 8001)
print('Bootstrap node ${NODE_NUMBER} configured successfully')
"

echo "Setup complete. To start the node, run:"
echo "cd node && ./start_node.sh"
EOL

chmod +x $TEMP_DIR/setup.sh

# Create README file
cat > $TEMP_DIR/README.md << EOL
# GlobalCoyn Bootstrap Node ${NODE_NUMBER}

This package contains all the necessary files to run a GlobalCoyn bootstrap node.

## Installation

1. Extract the package
2. Run the setup script: \`./setup.sh\`
3. Start the node: \`cd node && ./start_node.sh\`

## Configuration

The node is pre-configured as bootstrap node ${NODE_NUMBER}. Configuration can be modified in \`node/node_config.json\`.

## Monitoring

Logs are stored in:
- \`node/blockchain.log\`: General blockchain operations
- \`node/node_sync.log\`: Synchronization activities
- \`node/bootstrap.log\`: Bootstrap node specific logs

## Support

For assistance, contact support@globalcoyn.com.
EOL

# Package everything into a zip file
cd /tmp
zip -r $TARGET_FILE $PACKAGE_NAME
mv $TARGET_FILE /Users/adamneto/Desktop/blockchain/

# Clean up
rm -rf $TEMP_DIR

echo "Bootstrap node ${NODE_NUMBER} packaged successfully: /Users/adamneto/Desktop/blockchain/${TARGET_FILE}"