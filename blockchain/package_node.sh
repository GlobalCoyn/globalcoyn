#!/bin/bash
# Script to package the GlobalCoyn node for distribution

echo "Packaging GlobalCoyn Node for Distribution"

# Set base directories
BLOCKCHAIN_DIR="/Users/adamneto/Desktop/blockchain/blockchain"
NODE_DIR="$BLOCKCHAIN_DIR/node"
WORKING_NODE_DIR="$BLOCKCHAIN_DIR/working_nodes/node1"
WEBSITE_DIR="$BLOCKCHAIN_DIR/website"

# Create download directory if it doesn't exist
mkdir -p "$WEBSITE_DIR/downloads"

# Package the node
echo "Creating node package..."

# Create a temp directory for the node package
TEMP_DIR=$(mktemp -d)
NODE_PACKAGE_DIR="$TEMP_DIR/globalcoyn-node"
mkdir -p "$NODE_PACKAGE_DIR"

# Copy files from working node to the package
cp -r "$WORKING_NODE_DIR"/* "$NODE_PACKAGE_DIR/"

# Create a README file
cat > "$NODE_PACKAGE_DIR/README.md" << 'EOF'
# GlobalCoyn Node

This package contains everything you need to run a GlobalCoyn node and participate in the network.

## Requirements
- Python 3.9+
- Required Python packages are listed in requirements.txt

## Quick Start

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Start the node:
```
./start_node.sh
```

## Configuration

By default, the node runs on:
- P2P Port: 9000
- Web Port: 8001

You can modify these settings in start_node.sh or by setting environment variables:
- GCN_NODE_NUM
- GCN_P2P_PORT
- GCN_WEB_PORT

## Support

For support, please visit our website at [globalcoyn.com](https://globalcoyn.com) or join our Discord community.
EOF

# Create the zip file
cd "$TEMP_DIR"
zip -r "$WEBSITE_DIR/downloads/globalcoyn-node.zip" globalcoyn-node

# Clean up
rm -rf "$TEMP_DIR"

echo "Node package created at $WEBSITE_DIR/downloads/globalcoyn-node.zip"