#!/usr/bin/env python3
"""
Test script for bootstrap node configuration
"""
import sys
import os
import json

# Add the blockchain directory to the path
sys.path.insert(0, os.path.abspath('../blockchain'))

# Try to import the bootstrap_config module
try:
    from network.bootstrap_config import BootstrapNodeManager
    print("✓ Successfully imported BootstrapNodeManager")
    
    # Create bootstrap node manager
    manager = BootstrapNodeManager()
    print("✓ Successfully created BootstrapNodeManager instance")
    
    # Get bootstrap nodes
    bootstrap_nodes = manager.get_bootstrap_nodes()
    print(f"✓ Found {len(bootstrap_nodes)} bootstrap nodes")
    
    # Print bootstrap nodes
    for i, node in enumerate(bootstrap_nodes):
        print(f"  Node {i+1}: {node.get('host')}:{node.get('p2p_port')}")
    
    print("Bootstrap node configuration test passed!")
    sys.exit(0)
except Exception as e:
    print(f"✗ Error testing bootstrap node configuration: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
