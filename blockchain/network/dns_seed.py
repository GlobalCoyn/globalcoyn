"""
GlobalCoyn DNS Seed Resolver
---------------------------
Resolves DNS seed domains to discover GlobalCoyn nodes.
"""

import time
import socket
import random
import logging
import threading
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

# Local imports
try:
    from seed_nodes import get_dns_seed_domains
except ImportError:
    # Handle relative import when used as a module
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from network.seed_nodes import get_dns_seed_domains

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dns_seed.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gcn_dns_seed")

class DNSSeedResolver:
    """DNS seed resolver for GlobalCoyn network"""
    
    def __init__(self, network: str = "mainnet"):
        """
        Initialize the DNS seed resolver.
        
        Args:
            network: Network type ('mainnet', 'testnet', or 'development')
        """
        self.network = network
        self.dns_seeds = get_dns_seed_domains(network)
        self.resolved_nodes: List[Dict[str, Any]] = []
        self.last_resolution_time = 0
        self.resolution_interval = 300  # 5 minutes
        self.max_concurrent_lookups = 4
        self.resolution_lock = threading.RLock()
        
        # Start background thread for periodic resolution
        self.resolution_thread = threading.Thread(target=self._periodic_resolution, daemon=True)
        self.resolution_thread.start()
    
    def resolve_seeds(self, force: bool = False) -> List[Dict[str, Any]]:
        """
        Resolve DNS seeds to IP addresses.
        
        Args:
            force: Force resolution even if cache is fresh
            
        Returns:
            List of node information
        """
        with self.resolution_lock:
            current_time = time.time()
            
            # Check if we need to resolve again
            if self.resolved_nodes and not force and \
               (current_time - self.last_resolution_time) < self.resolution_interval:
                return self.resolved_nodes
            
            logger.info(f"Resolving DNS seeds for {self.network} network...")
            resolved = []
            
            # Randomize order for load balancing
            dns_seeds = self.dns_seeds.copy()
            random.shuffle(dns_seeds)
            
            # Use thread pool for concurrent resolution
            with ThreadPoolExecutor(max_workers=self.max_concurrent_lookups) as executor:
                # Submit all lookup tasks
                futures = [executor.submit(self._resolve_seed, seed) for seed in dns_seeds]
                
                # Collect results as they complete
                for future in futures:
                    try:
                        result = future.result()
                        if result:
                            resolved.extend(result)
                    except Exception as e:
                        logger.error(f"Error in DNS seed resolution: {str(e)}")
            
            # Update cache
            self.resolved_nodes = resolved
            self.last_resolution_time = current_time
            
            logger.info(f"Resolved {len(resolved)} nodes from DNS seeds")
            return resolved
    
    def _resolve_seed(self, seed_domain: str) -> List[Dict[str, Any]]:
        """
        Resolve a single DNS seed domain.
        
        Args:
            seed_domain: DNS seed domain to resolve
            
        Returns:
            List of resolved node information
        """
        try:
            logger.info(f"Resolving DNS seed: {seed_domain}")
            
            # Try to get A records
            addresses = []
            try:
                # First try standard DNS lookup
                info = socket.getaddrinfo(seed_domain, None)
                for family, _, _, _, sockaddr in info:
                    if family == socket.AF_INET:  # IPv4
                        addresses.append(sockaddr[0])
                    elif family == socket.AF_INET6:  # IPv6
                        # Format IPv6 address properly
                        addresses.append(f"[{sockaddr[0]}]")
            except socket.gaierror:
                logger.warning(f"Could not resolve DNS seed: {seed_domain}")
            
            # Convert to node information
            nodes = []
            for addr in addresses:
                # Default ports
                p2p_port = 9000
                web_port = 8001
                
                # Check if this is a special format with ports embedded
                # Format: x1.seed.globalcoyn.com -> web port 8001
                # Format: x2.seed.globalcoyn.com -> web port 8002
                # Format: x9.seed.globalcoyn.com -> web port 8009
                # Similar to Bitcoin's format for service bits
                parts = seed_domain.split('.')
                if len(parts) > 2 and parts[0].startswith('x') and parts[0][1:].isdigit():
                    suffix = int(parts[0][1:])
                    web_port = 8000 + suffix
                    
                    # For consistency, also adjust P2P port
                    p2p_port = 9000 + (suffix - 1)
                
                node = {
                    "host": addr,
                    "p2p_port": p2p_port,
                    "web_port": web_port,
                    "source": "dns_seed",
                    "seed_domain": seed_domain
                }
                nodes.append(node)
            
            logger.info(f"Resolved {len(nodes)} addresses from {seed_domain}")
            return nodes
        except Exception as e:
            logger.error(f"Error resolving DNS seed {seed_domain}: {str(e)}")
            return []
    
    def _periodic_resolution(self) -> None:
        """Background thread for periodic DNS resolution."""
        # Wait initially to avoid immediate resolution at startup
        time.sleep(5)
        
        while True:
            try:
                self.resolve_seeds()
            except Exception as e:
                logger.error(f"Error in periodic DNS resolution: {str(e)}")
            
            # Sleep until next resolution
            time.sleep(self.resolution_interval)
    
    def get_nodes(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get resolved nodes.
        
        Args:
            count: Number of nodes to return (None for all)
            
        Returns:
            List of node information
        """
        # Ensure we have resolved nodes
        nodes = self.resolve_seeds()
        
        if count is not None and count > 0:
            # Shuffle and return requested number
            shuffled = nodes.copy()
            random.shuffle(shuffled)
            return shuffled[:min(count, len(shuffled))]
        
        return nodes