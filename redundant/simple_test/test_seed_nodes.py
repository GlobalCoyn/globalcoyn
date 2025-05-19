#!/usr/bin/env python3
"""
Test script for seed nodes
"""
import sys
import os

# Add the blockchain directory to the path
sys.path.insert(0, os.path.abspath('../blockchain'))

# Try to import the seed_nodes module
try:
    from network.seed_nodes import get_seed_nodes, get_dns_seed_domains
    print("✓ Successfully imported seed_nodes functions")
    
    # Get seed nodes for each network
    for network in ['mainnet', 'testnet', 'development']:
        nodes = get_seed_nodes(network)
        print(f"✓ Found {len(nodes)} seed nodes for {network}")
    
    # Get DNS seed domains
    domains = get_dns_seed_domains('mainnet')
    print(f"✓ Found {len(domains)} DNS seed domains for mainnet")
    for domain in domains:
        print(f"  Domain: {domain}")
    
    print("Seed nodes test passed!")
    sys.exit(0)
except Exception as e:
    print(f"✗ Error testing seed nodes: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
