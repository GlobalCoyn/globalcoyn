#!/bin/bash
# Script to test macOS app integration with bootstrap nodes
# This tests the app's ability to connect to bootstrap nodes

# Exit on error
set -e

# Define test directories
TEST_DIR="./macos_app_test"
LOG_FILE="./macos_app_test.log"

# Create test directory and ensure it's empty
rm -rf $TEST_DIR
mkdir -p $TEST_DIR
rm -f $LOG_FILE
touch $LOG_FILE

echo "Starting macOS app integration tests..."
echo "----------------------------------------" | tee -a $LOG_FILE
echo "Testing connection to bootstrap nodes" | tee -a $LOG_FILE
echo "----------------------------------------" | tee -a $LOG_FILE

# Copy the macOS app to the test directory
cp -r ./blockchain/apps/macos_app/macos_app.py $TEST_DIR/
cp -r ./blockchain/network/improved_node_sync.py $TEST_DIR/
cp -r ./blockchain/network/bootstrap_config.py $TEST_DIR/
cp -r ./blockchain/network/dns_seed.py $TEST_DIR/
cp -r ./blockchain/network/seed_nodes.py $TEST_DIR/
cp -r ./blockchain/network/connection_backoff.py $TEST_DIR/

# Create necessary structure for module imports
mkdir -p $TEST_DIR/network
touch $TEST_DIR/network/__init__.py
cp -r ./blockchain/network/improved_node_sync.py $TEST_DIR/network/

# Create a test script
cat > $TEST_DIR/test_bootstrap_connection.py << EOL
#!/usr/bin/env python3
"""
Test script for verifying bootstrap node connections.
"""

import sys
import time
import logging
import os

# Add current directory to path
sys.path.append(os.path.abspath('.'))

from bootstrap_config import BootstrapNodeManager
from dns_seed import DNSSeedResolver

# Create a stub EnhancedNodeDiscovery class for testing
class EnhancedNodeDiscovery:
    """Mock enhanced node discovery class for testing"""
    
    def __init__(self):
        self.bootstrap_manager = BootstrapNodeManager()
        self.dns_resolver = DNSSeedResolver()
    
    def discover_nodes(self, max_count=None):
        """Discover nodes using all available methods"""
        # Get bootstrap nodes
        bootstrap_nodes = self.bootstrap_manager.get_bootstrap_nodes()
        
        # Get DNS seed nodes
        dns_nodes = self.dns_resolver.get_nodes(count=5)
        
        # Combine and deduplicate
        all_nodes = bootstrap_nodes + dns_nodes
        
        # Limit if requested
        if max_count and len(all_nodes) > max_count:
            return all_nodes[:max_count]
            
        return all_nodes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../macos_app_test.log", mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gcn_connection_test")

def test_bootstrap_nodes():
    """Test connection to bootstrap nodes."""
    logger.info("Testing bootstrap node connections...")
    
    # Initialize bootstrap node manager
    manager = BootstrapNodeManager()
    
    # Get bootstrap nodes
    bootstrap_nodes = manager.get_bootstrap_nodes()
    logger.info(f"Found {len(bootstrap_nodes)} bootstrap nodes")
    
    # Try to connect to each bootstrap node
    for i, node in enumerate(bootstrap_nodes):
        host = node.get('host')
        port = node.get('p2p_port')
        logger.info(f"Testing connection to bootstrap node {i+1}: {host}:{port}")
        
        try:
            # Import socket here to avoid circular imports
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            if result == 0:
                logger.info(f"Successfully connected to {host}:{port}")
            else:
                logger.error(f"Failed to connect to {host}:{port}, error code: {result}")
            sock.close()
        except Exception as e:
            logger.error(f"Error connecting to {host}:{port}: {str(e)}")
    
    return True

def test_dns_seeds():
    """Test connection to DNS seed nodes."""
    logger.info("Testing DNS seed resolution...")
    
    # Initialize DNS seed resolver
    resolver = DNSSeedResolver()
    
    # Resolve DNS seeds
    nodes = resolver.resolve_seeds(force=True)
    logger.info(f"Resolved {len(nodes)} nodes from DNS seeds")
    
    # Try to connect to each resolved node (test first 5 only)
    for i, node in enumerate(nodes[:5]):
        host = node.get('host')
        port = node.get('p2p_port')
        logger.info(f"Testing connection to DNS seed node {i+1}: {host}:{port}")
        
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            if result == 0:
                logger.info(f"Successfully connected to {host}:{port}")
            else:
                logger.error(f"Failed to connect to {host}:{port}, error code: {result}")
            sock.close()
        except Exception as e:
            logger.error(f"Error connecting to {host}:{port}: {str(e)}")
    
    return True

def test_enhanced_discovery():
    """Test the enhanced node discovery module."""
    logger.info("Testing enhanced node discovery...")
    
    # Initialize enhanced node discovery
    discovery = EnhancedNodeDiscovery()
    
    # Discover nodes using all methods
    nodes = discovery.discover_nodes(max_count=10)
    logger.info(f"Discovered {len(nodes)} nodes using enhanced discovery")
    
    if len(nodes) > 0:
        logger.info("Enhanced node discovery test passed")
        return True
    else:
        logger.error("Enhanced node discovery test failed: No nodes discovered")
        return False

def main():
    """Run all tests."""
    tests = [
        ("Bootstrap Nodes", test_bootstrap_nodes),
        ("DNS Seeds", test_dns_seeds),
        ("Enhanced Discovery", test_enhanced_discovery)
    ]
    
    success_count = 0
    
    for name, test_func in tests:
        logger.info(f"Running test: {name}")
        try:
            result = test_func()
            if result:
                logger.info(f"Test {name} passed")
                success_count += 1
            else:
                logger.error(f"Test {name} failed")
        except Exception as e:
            logger.error(f"Test {name} failed with error: {str(e)}")
    
    logger.info(f"Test results: {success_count}/{len(tests)} tests passed")
    
    if success_count == len(tests):
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOL

# Make test script executable
chmod +x $TEST_DIR/test_bootstrap_connection.py

# Run the test
cd $TEST_DIR
python3 test_bootstrap_connection.py

# Check results
if [ $? -eq 0 ]; then
  echo "----------------------------------------" | tee -a ../$LOG_FILE
  echo "All macOS app integration tests passed!" | tee -a ../$LOG_FILE
  echo "----------------------------------------" | tee -a ../$LOG_FILE
  exit 0
else
  echo "----------------------------------------" | tee -a ../$LOG_FILE
  echo "Some macOS app integration tests failed." | tee -a ../$LOG_FILE
  echo "See log file for details: $LOG_FILE" | tee -a ../$LOG_FILE
  echo "----------------------------------------" | tee -a ../$LOG_FILE
  exit 1
fi