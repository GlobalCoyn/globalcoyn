"""
GlobalCoyn Seed Nodes
--------------------
Hardcoded seed nodes for the GlobalCoyn network.
These nodes serve as a fallback when DNS seeds and bootstrap nodes are unavailable.
"""

import random
from typing import List, Dict, Any, Optional

# Mainnet seed nodes
# These are stable nodes known to be reliable
MAINNET_SEED_NODES = [
    {"host": "node1.globalcoyn.com", "p2p_port": 9000, "web_port": 8001, "node_number": 1},
    {"host": "node2.globalcoyn.com", "p2p_port": 9000, "web_port": 8001, "node_number": 2},
    {"host": "node3.globalcoyn.com", "p2p_port": 9000, "web_port": 8001, "node_number": 3},
    {"host": "node4.globalcoyn.com", "p2p_port": 9000, "web_port": 8001, "node_number": 4},
    {"host": "node5.globalcoyn.com", "p2p_port": 9000, "web_port": 8001, "node_number": 5},
    {"host": "seed1.globalcoyn.net", "p2p_port": 9000, "web_port": 8001, "node_number": 6},
    {"host": "seed2.globalcoyn.net", "p2p_port": 9000, "web_port": 8001, "node_number": 7},
    {"host": "seed.globalcoyn.org", "p2p_port": 9000, "web_port": 8001, "node_number": 8},
]

# Testnet seed nodes
TESTNET_SEED_NODES = [
    {"host": "test1.globalcoyn.com", "p2p_port": 9000, "web_port": 8001, "node_number": 1},
    {"host": "test2.globalcoyn.com", "p2p_port": 9000, "web_port": 8001, "node_number": 2},
]

# Development seed nodes (localhost)
DEVELOPMENT_SEED_NODES = [
    {"host": "localhost", "p2p_port": 9000, "web_port": 8001, "node_number": 1},
    {"host": "localhost", "p2p_port": 9001, "web_port": 8002, "node_number": 2},
    {"host": "127.0.0.1", "p2p_port": 9000, "web_port": 8001, "node_number": 1},
    {"host": "127.0.0.1", "p2p_port": 9001, "web_port": 8002, "node_number": 2},
]

def get_seed_nodes(network: str = "mainnet", count: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get seed nodes for the specified network.
    
    Args:
        network: Network type ('mainnet', 'testnet', or 'development')
        count: Number of seed nodes to return (None for all)
        
    Returns:
        List of seed node information
    """
    if network == "mainnet":
        seeds = MAINNET_SEED_NODES
    elif network == "testnet":
        seeds = TESTNET_SEED_NODES
    elif network == "development":
        seeds = DEVELOPMENT_SEED_NODES
    else:
        raise ValueError(f"Unknown network type: {network}")
    
    if count is not None and count > 0:
        # Shuffle and return requested number (up to available count)
        shuffled = seeds.copy()
        random.shuffle(shuffled)
        return shuffled[:min(count, len(shuffled))]
    
    return seeds

def get_dns_seed_domains(network: str = "mainnet") -> List[str]:
    """
    Get DNS seed domains for the specified network.
    
    Args:
        network: Network type ('mainnet', 'testnet', or 'development')
        
    Returns:
        List of DNS seed domains
    """
    if network == "mainnet":
        return [
            "seed.globalcoyn.com",
            "seed.globalcoyn.net",
            "dnsseed.globalcoyn.org",
        ]
    elif network == "testnet":
        return [
            "testnet-seed.globalcoyn.com",
            "testnet-seed.globalcoyn.net",
        ]
    else:
        return []