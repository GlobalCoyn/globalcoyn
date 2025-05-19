"""
Enhanced Node Discovery for GlobalCoyn macOS App
---------------------------------------------
Integrates the improved node discovery for the macOS app.
"""

import os
import sys
import time
import json
import logging
from typing import List, Dict, Any, Optional, Tuple

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Import from network package
try:
    from network.improved_node_discovery import ImprovedNodeDiscovery
    from network.dns_seed import DNSSeedResolver
    from network.seed_nodes import get_seed_nodes
    from network.connection_backoff import ConnectionBackoff
except ImportError:
    # Fallback paths
    sys.path.append(os.path.join(parent_dir, "network"))
    from improved_node_discovery import ImprovedNodeDiscovery
    from dns_seed import DNSSeedResolver
    from seed_nodes import get_seed_nodes
    from connection_backoff import ConnectionBackoff

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("macos_node_discovery.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gcn_macos_discovery")

class EnhancedNodeDiscovery:
    """Enhanced node discovery for the macOS app"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the enhanced node discovery.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Determine network type
        if config.get("production_mode", False):
            self.network = "mainnet"
        elif config.get("testnet", False):
            self.network = "testnet"
        else:
            self.network = "development"
        
        # Initialize components
        self.improved_discovery = ImprovedNodeDiscovery(config)
        self.dns_resolver = DNSSeedResolver(self.network)
        self.connection_backoff = ConnectionBackoff()
        
        # Node identity
        self.node_number = None
        self.p2p_port = config.get("p2p_port")
        self.web_port = config.get("web_port")
        
        # Initialize component parameters
        self._init_ports()
        
        # Log configuration
        logger.info(f"Enhanced node discovery initialized for {self.network} network")
        logger.info(f"P2P port: {self.p2p_port}, Web port: {self.web_port}")
    
    def _init_ports(self):
        """Initialize ports if not set in config."""
        if not self.p2p_port or not self.web_port:
            p2p, web = self.improved_discovery.find_available_ports()
            self.p2p_port = p2p
            self.web_port = web
            
            # Update our config
            self.config["p2p_port"] = p2p
            self.config["web_port"] = web
            
            # Also update the underlying discovery module
            self.improved_discovery.p2p_port = p2p
            self.improved_discovery.web_port = web
    
    def get_node_number(self) -> int:
        """
        Get node number for this instance.
        
        Returns:
            Unique node number
        """
        if self.node_number is None:
            self.node_number = self.improved_discovery.get_node_number()
        return self.node_number
    
    def discover_peers(self, use_dns: bool = True, 
                      use_hardcoded: bool = True) -> List[Dict[str, Any]]:
        """
        Discover peers using multiple methods.
        
        Args:
            use_dns: Whether to use DNS seeds
            use_hardcoded: Whether to use hardcoded seeds
            
        Returns:
            List of discovered peers
        """
        discovered = []
        
        # First try improved discovery (bootstrap nodes)
        bootstrap_peers = self.improved_discovery.discover_peers()
        for peer in bootstrap_peers:
            peer_id = f"{peer.get('host')}:{peer.get('p2p_port')}"
            if peer_id not in [f"{p.get('host')}:{p.get('p2p_port')}" for p in discovered]:
                discovered.append(peer)
        
        # If we didn't find enough peers, try DNS seeds
        if use_dns and len(discovered) < 8:
            try:
                dns_peers = self.dns_resolver.get_nodes(count=10)
                for peer in dns_peers:
                    peer_id = f"{peer.get('host')}:{peer.get('p2p_port')}"
                    if peer_id not in [f"{p.get('host')}:{p.get('p2p_port')}" for p in discovered]:
                        discovered.append(peer)
            except Exception as e:
                logger.warning(f"Error resolving DNS seeds: {str(e)}")
        
        # If still not enough peers, try hardcoded seeds
        if use_hardcoded and len(discovered) < 4:
            seed_peers = get_seed_nodes(self.network)
            for peer in seed_peers:
                peer_id = f"{peer.get('host')}:{peer.get('p2p_port')}"
                if peer_id not in [f"{p.get('host')}:{p.get('p2p_port')}" for p in discovered]:
                    discovered.append(peer)
        
        logger.info(f"Discovered {len(discovered)} peers in total")
        return discovered
    
    def connect_to_peers(self, api_base: str, max_connections: int = 8) -> List[Dict[str, Any]]:
        """
        Connect to discovered peers.
        
        Args:
            api_base: Base URL for node API
            max_connections: Maximum number of connections to establish
            
        Returns:
            List of successfully connected peers
        """
        # First discover peers
        all_peers = self.discover_peers()
        
        # Sort peers by preference:
        # 1. Bootstrap nodes
        # 2. DNS seed nodes
        # 3. Hardcoded seeds
        # 4. Other discovered peers
        def peer_priority(peer):
            if peer.get('node_number', 0) <= 2:  # Bootstrap node
                return 0
            elif peer.get('source') == 'dns_seed':  # DNS seed
                return 1
            elif peer.get('source') == 'seed_node':  # Hardcoded seed
                return 2
            else:  # Other peer
                return 3
                
        all_peers.sort(key=peer_priority)
        
        # Limit to max attempts
        max_attempts = min(len(all_peers), max_connections * 2)
        peers_to_try = all_peers[:max_attempts]
        
        # Try connecting with backoff strategy
        connected = []
        for peer in peers_to_try:
            # Stop if we've reached max connections
            if len(connected) >= max_connections:
                break
                
            host = peer.get('host')
            port = peer.get('p2p_port', 9000)
            
            if not host:
                continue
                
            connection_id = f"{host}:{port}"
            
            def connect_func():
                """Connection function for this peer."""
                response = self._connect_to_peer(api_base, host, port)
                if response.get('success', False):
                    return peer
                else:
                    raise Exception(f"Connection failed: {response.get('message', 'Unknown error')}")
            
            def on_success(result):
                """Called on successful connection."""
                if result:
                    connected.append(result)
                    self.improved_discovery.register_connection_status(host, port, True)
            
            def on_failure(e):
                """Called on connection failure."""
                self.improved_discovery.register_connection_status(host, port, False)
            
            # Execute connection with retry logic
            self.connection_backoff.with_retry(
                connection_id, 
                connect_func, 
                on_success, 
                on_failure
            )
        
        logger.info(f"Connected to {len(connected)} peers")
        return connected
    
    def _connect_to_peer(self, api_base: str, host: str, port: int) -> Dict[str, Any]:
        """
        Connect to a peer via API.
        
        Args:
            api_base: Base URL for node API
            host: Peer host address
            port: Peer P2P port
            
        Returns:
            Response from the connection attempt
        """
        import requests
        
        try:
            connect_url = f"{api_base}/network/connect"
            response = requests.post(
                connect_url,
                json={"address": host, "port": port},
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def find_available_ports(self) -> Tuple[int, int]:
        """
        Find available ports for P2P and Web services.
        
        Returns:
            Tuple of (p2p_port, web_port)
        """
        return self.improved_discovery.find_available_ports()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status information.
        
        Returns:
            Status information dictionary
        """
        return {
            "node_number": self.get_node_number(),
            "p2p_port": self.p2p_port,
            "web_port": self.web_port,
            "network": self.network,
            "production_mode": self.config.get("production_mode", False),
            "discovery_status": self.improved_discovery.get_connection_status()
        }