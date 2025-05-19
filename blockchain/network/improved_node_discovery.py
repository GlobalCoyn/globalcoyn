"""
Improved Node Discovery for GlobalCoyn
-------------------------------------
Enhanced peer discovery and connection management for GlobalCoyn network.
"""

import os
import sys
import time
import json
import socket
import random
import logging
import requests
import threading
from typing import List, Dict, Tuple, Any, Optional, Set
from pathlib import Path

# Import bootstrap configuration
try:
    from bootstrap_config import BootstrapNodeManager
except ImportError:
    # Handle relative import when used as a module
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from network.bootstrap_config import BootstrapNodeManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("node_discovery.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gcn_discovery")

class ImprovedNodeDiscovery:
    """Enhanced node discovery with better peer management and resilience"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the node discovery system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.bootstrap_manager = BootstrapNodeManager()
        
        # Override production mode from config
        if "production_mode" in config:
            self.bootstrap_manager.config["production_mode"] = config["production_mode"]
            self.bootstrap_manager.save_config()
            
        # Get bootstrap nodes
        self.bootstrap_nodes = self.bootstrap_manager.get_bootstrap_nodes()
        
        # Node identity
        self.node_number = None
        self.p2p_port = config.get("p2p_port")
        self.web_port = config.get("web_port")
        
        # Connection tracking
        self.connected_peers: Set[str] = set()  # Format: "host:port"
        self.failed_connections: Dict[str, Dict] = {}  # Format: "host:port" -> {"failures": int, "last_attempt": timestamp}
        self.peer_db_path = self._get_peer_db_path()
        
        # Load persisted peers
        self.known_peers = self._load_known_peers()
        
        # Connection management
        self.max_connections = config.get("max_connections", 8)
        self.connection_retry_delay = config.get("connection_retry_delay", 60)  # Seconds
        self.peer_refresh_interval = config.get("peer_refresh_interval", 300)  # 5 minutes
        
        # Start background thread for periodic peer refresh
        self.refresh_thread = threading.Thread(target=self._periodic_peer_refresh, daemon=True)
        self.refresh_thread.start()
    
    def _get_peer_db_path(self) -> str:
        """Get the path for storing known peers."""
        home_dir = str(Path.home())
        data_dir = os.path.join(home_dir, ".globalcoyn")
        
        # Create directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        return os.path.join(data_dir, "known_peers.json")
    
    def _load_known_peers(self) -> List[Dict[str, Any]]:
        """Load known peers from persistent storage."""
        if os.path.exists(self.peer_db_path):
            try:
                with open(self.peer_db_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading known peers: {str(e)}")
        
        return []
    
    def _save_known_peers(self) -> None:
        """Save known peers to persistent storage."""
        try:
            with open(self.peer_db_path, 'w') as f:
                json.dump(self.known_peers, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving known peers: {str(e)}")
    
    def get_node_number(self) -> int:
        """
        Get a unique node number for this node.
        
        Returns:
            int: Node number (3 or higher, as 1-2 are bootstrap nodes)
        """
        # Return cached node number if available
        if self.node_number is not None:
            return self.node_number
            
        # Check if we're configured as a bootstrap node
        if self.bootstrap_manager.is_bootstrap_node:
            self.node_number = self.bootstrap_manager.node_number
            return self.node_number
            
        # Check config for manually assigned node number
        if self.config.get('node_number', 0) > 2:
            self.node_number = self.config.get('node_number')
            return self.node_number
        
        # Try production registry service
        if self.bootstrap_manager.is_production_mode():
            try:
                registry_url = "https://registry.globalcoyn.com/register"
                response = requests.get(registry_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'node_number' in data:
                        self.node_number = data['node_number']
                        return self.node_number
            except Exception as e:
                logger.error(f"Error contacting registry service: {str(e)}")
        
        # Try getting highest node number from bootstrap nodes
        highest_node = self.find_highest_node_number()
        if highest_node >= 2:
            # Use next available number
            self.node_number = highest_node + 1
            return self.node_number
        
        # Final fallback: Generate a random high number if all else fails
        timestamp = int(time.time()) % 1000
        random_part = random.randint(1000, 9999)
        fallback_node_number = 3000 + timestamp + random_part
        
        self.node_number = fallback_node_number
        return fallback_node_number
    
    def find_highest_node_number(self) -> int:
        """
        Find the highest node number in use.
        
        Returns:
            int: Highest node number found, or 2 if none found
        """
        highest = 2  # Bootstrap nodes are 1 and 2
        
        # Try bootstrap nodes first
        for node in self.bootstrap_nodes:
            try:
                host = node.get("host")
                port = node.get("web_port", 8001)
                url = f"http://{host}:{port}/api/network/status"
                
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    # Try to get peer data which includes node numbers
                    if 'peers' in data:
                        for peer in data['peers']:
                            if 'node_number' in peer and peer['node_number'] > highest:
                                highest = peer['node_number']
                    # Also check for total node count as a fallback
                    elif 'node_count' in data and data['node_count'] > highest:
                        highest = data['node_count']
            except Exception as e:
                logger.warning(f"Error querying bootstrap node {host}:{port}: {str(e)}")
        
        # Also check known peers
        for peer in self.known_peers:
            if peer.get('node_number', 0) > highest:
                highest = peer['node_number']
                
        return highest
    
    def find_available_ports(self) -> Tuple[int, int]:
        """
        Find available ports for P2P and Web services.
        
        Returns:
            Tuple[int, int]: (p2p_port, web_port)
        """
        # If config already has valid ports, use them
        p2p_port = self.config.get('p2p_port')
        web_port = self.config.get('web_port')
        
        if p2p_port and web_port:
            # Check if these ports are available
            if self._is_port_available(p2p_port) and self._is_port_available(web_port):
                return p2p_port, web_port
        
        # Start from standard base ports
        base_p2p_port = 9000
        base_web_port = 8001
        
        # Try to find available ports, keeping the standard offset
        offset = 0
        
        # Try up to 1000 port combinations
        while offset < 1000:
            p2p_port = base_p2p_port + offset
            web_port = base_web_port + offset
            
            if self._is_port_available(p2p_port) and self._is_port_available(web_port):
                return p2p_port, web_port
            
            offset += 1
        
        # If no ports found, raise exception
        raise RuntimeError("No available port pairs found for node services")
    
    def _is_port_available(self, port: int) -> bool:
        """
        Check if a port is available.
        
        Args:
            port: Port to check
            
        Returns:
            bool: True if available, False otherwise
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', port))
            return result != 0
        finally:
            sock.close()
    
    def discover_peers(self) -> List[Dict[str, Any]]:
        """
        Discover peers in the network.
        
        Returns:
            List[Dict[str, Any]]: List of discovered peers
        """
        discovered = []
        
        # Try bootstrap nodes first
        for node in self.bootstrap_nodes:
            try:
                host = node.get("host")
                port = node.get("web_port", 8001)
                url = f"http://{host}:{port}/api/network/peers"
                
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'peers' in data:
                        for peer in data['peers']:
                            peer_id = f"{peer.get('host')}:{peer.get('p2p_port')}"
                            # Check if this peer is already known
                            if peer_id not in [f"{p.get('host')}:{p.get('p2p_port')}" for p in discovered]:
                                discovered.append(peer)
                                
                                # Add to known peers if new
                                if peer_id not in [f"{p.get('host')}:{p.get('p2p_port')}" for p in self.known_peers]:
                                    self.known_peers.append(peer)
            except Exception as e:
                logger.warning(f"Error discovering peers from {host}:{port}: {str(e)}")
        
        # If we're low on discovered nodes, try asking known peers
        if len(discovered) < 5 and self.known_peers:
            for peer in self.known_peers:
                # Skip peers we already tried via bootstrap nodes
                peer_id = f"{peer.get('host')}:{peer.get('p2p_port')}"
                if peer_id in [f"{p.get('host')}:{p.get('p2p_port')}" for p in discovered]:
                    continue
                    
                # Skip bootstrap nodes (already queried)
                if peer.get('node_number', 0) <= 2:
                    continue
                    
                # Skip recently failed connections
                if peer_id in self.failed_connections:
                    last_attempt = self.failed_connections[peer_id]["last_attempt"]
                    failures = self.failed_connections[peer_id]["failures"]
                    # Exponential backoff: wait longer after more failures
                    backoff_time = self.connection_retry_delay * (2 ** (failures - 1))
                    if time.time() - last_attempt < backoff_time:
                        continue
                
                try:
                    host = peer.get("host")
                    port = peer.get("web_port", 8001)
                    url = f"http://{host}:{port}/api/network/peers"
                    
                    response = requests.get(url, timeout=3)  # Shorter timeout for non-bootstrap peers
                    if response.status_code == 200:
                        data = response.json()
                        if 'peers' in data:
                            for new_peer in data['peers']:
                                new_peer_id = f"{new_peer.get('host')}:{new_peer.get('p2p_port')}"
                                if new_peer_id not in [f"{p.get('host')}:{p.get('p2p_port')}" for p in discovered]:
                                    discovered.append(new_peer)
                                    
                                    # Add to known peers if new
                                    if new_peer_id not in [f"{p.get('host')}:{p.get('p2p_port')}" for p in self.known_peers]:
                                        self.known_peers.append(new_peer)
                                        
                            # This peer responded successfully, remove from failed_connections if present
                            if peer_id in self.failed_connections:
                                del self.failed_connections[peer_id]
                except Exception as e:
                    # Record connection failure
                    if peer_id not in self.failed_connections:
                        self.failed_connections[peer_id] = {"failures": 1, "last_attempt": time.time()}
                    else:
                        self.failed_connections[peer_id]["failures"] += 1
                        self.failed_connections[peer_id]["last_attempt"] = time.time()
                        
                    logger.warning(f"Error discovering peers from known peer {host}:{port}: {str(e)}")
        
        # Save discovered peers
        self._save_known_peers()
        
        return discovered
    
    def connect_to_peers(self, api_base: str) -> List[Dict[str, Any]]:
        """
        Connect to discovered peers.
        
        Args:
            api_base: Base URL for local node API
            
        Returns:
            List[Dict[str, Any]]: Successfully connected peers
        """
        connected = []
        
        # First discover peers if needed
        peers = self.discover_peers()
        
        # Sort peers by priority:
        # 1. Bootstrap nodes first
        # 2. Then known good peers (those not in failed_connections)
        # 3. Then recently failed peers
        def peer_priority(peer):
            peer_id = f"{peer.get('host')}:{peer.get('p2p_port')}"
            if peer.get('node_number', 0) <= 2:  # Bootstrap node
                return 0
            elif peer_id not in self.failed_connections:  # Known good peer
                return 1
            else:  # Failed peer
                return 2 + self.failed_connections[peer_id]["failures"]
                
        peers.sort(key=peer_priority)
        
        # Limit number of connection attempts based on max_connections
        connection_attempts = 0
        max_attempts = min(len(peers), self.max_connections * 2)  # Try up to 2x max_connections
        
        # Try to connect to peers
        for peer in peers:
            # Stop if we've reached max_connections successful connections
            if len(connected) >= self.max_connections:
                break
                
            # Stop if we've made too many attempts
            if connection_attempts >= max_attempts:
                break
                
            connection_attempts += 1
            
            try:
                # Extract peer details
                host = peer.get("host")
                p2p_port = peer.get("p2p_port", 9000)
                
                if not host:
                    continue
                
                peer_id = f"{host}:{p2p_port}"
                
                # Skip if already connected
                if peer_id in self.connected_peers:
                    connected.append(peer)
                    continue
                
                # Connect via our node API
                connect_url = f"{api_base}/network/connect"
                response = requests.post(
                    connect_url, 
                    json={"address": host, "port": p2p_port},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success', False):
                        connected.append(peer)
                        
                        # Record successful connection
                        self.connected_peers.add(peer_id)
                        
                        # Remove from failed connections if present
                        if peer_id in self.failed_connections:
                            del self.failed_connections[peer_id]
                else:
                    # Record connection failure
                    if peer_id not in self.failed_connections:
                        self.failed_connections[peer_id] = {"failures": 1, "last_attempt": time.time()}
                    else:
                        self.failed_connections[peer_id]["failures"] += 1
                        self.failed_connections[peer_id]["last_attempt"] = time.time()
            except Exception as e:
                # Record connection failure
                peer_id = f"{peer.get('host')}:{peer.get('p2p_port')}"
                if peer_id not in self.failed_connections:
                    self.failed_connections[peer_id] = {"failures": 1, "last_attempt": time.time()}
                else:
                    self.failed_connections[peer_id]["failures"] += 1
                    self.failed_connections[peer_id]["last_attempt"] = time.time()
                    
                logger.warning(f"Error connecting to peer {peer.get('host')}:{peer.get('p2p_port')}: {str(e)}")
        
        return connected
    
    def _periodic_peer_refresh(self) -> None:
        """Background thread for periodic peer discovery and cleanup."""
        while True:
            try:
                # Sleep first to avoid immediate refresh after startup
                time.sleep(self.peer_refresh_interval)
                
                # Only do peer refresh if we have a port configuration
                if self.p2p_port and self.web_port:
                    # Discover new peers
                    self.discover_peers()
                    
                    # Cleanup stale peers (not used currently, left for future implementation)
                    # We could check if peers are still reachable
                    
                    # Log status
                    logger.info(f"Peer refresh: {len(self.known_peers)} known peers, "
                               f"{len(self.connected_peers)} connected peers, "
                               f"{len(self.failed_connections)} failed connections")
            except Exception as e:
                logger.error(f"Error in periodic peer refresh: {str(e)}")
    
    def register_connection_status(self, peer_host: str, peer_port: int, connected: bool) -> None:
        """
        Update the connection status for a peer.
        
        Args:
            peer_host: Peer host address
            peer_port: Peer P2P port
            connected: True if connected, False if disconnected
        """
        peer_id = f"{peer_host}:{peer_port}"
        
        if connected:
            self.connected_peers.add(peer_id)
            
            # Remove from failed connections if present
            if peer_id in self.failed_connections:
                del self.failed_connections[peer_id]
        else:
            # Remove from connected peers
            self.connected_peers.discard(peer_id)
            
            # Don't add to failed connections here - let the connect_to_peers method handle that
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get the current connection status.
        
        Returns:
            Dict with connection status information
        """
        return {
            "node_number": self.node_number,
            "p2p_port": self.p2p_port,
            "web_port": self.web_port,
            "known_peers": len(self.known_peers),
            "connected_peers": len(self.connected_peers),
            "failed_connections": len(self.failed_connections),
            "is_bootstrap": self.bootstrap_manager.is_bootstrap_node,
            "production_mode": self.bootstrap_manager.is_production_mode()
        }