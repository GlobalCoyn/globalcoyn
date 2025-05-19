"""
GlobalCoyn Node Discovery Module
--------------------------------
Handle dynamic node numbering and peer discovery for the GlobalCoyn network.
"""

import os
import sys
import time
import json
import socket
import random
import requests
from typing import Tuple, List, Dict, Optional, Any

class NodeDiscovery:
    """Handle node discovery and registration in the GlobalCoyn network"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        self.config = config
        self.bootstrap_nodes = config.get('bootstrap_nodes', [
            'node1.globalcoyn.com:8001',
            'node2.globalcoyn.com:8001'
        ])
        # In development mode, use localhost bootstrap nodes
        if not config.get('production_mode', False):
            self.bootstrap_nodes = [
                'localhost:8001',
                'localhost:8002'
            ]
        self.registered_node_number = None
        self.discovered_peers = []
    
    def get_node_number(self) -> int:
        """
        Get a unique node number for this node.
        
        This will either:
        1. Use previously assigned number if available
        2. Request from registry service in production
        3. Query bootstrap nodes for highest node number
        4. Generate based on local parameters as fallback
        
        Returns:
            int: A unique node number (3 or higher, as 1-2 are bootstrap nodes)
        """
        # If we've already registered, use that number
        if self.registered_node_number is not None:
            return self.registered_node_number
            
        # Check config for manually assigned node number
        if self.config.get('node_number', 0) > 2:
            self.registered_node_number = self.config.get('node_number')
            return self.registered_node_number
        
        # Try production registry service
        if self.config.get('production_mode', False):
            try:
                registry_url = "https://registry.globalcoyn.com/register"
                response = requests.get(registry_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'node_number' in data:
                        self.registered_node_number = data['node_number']
                        return self.registered_node_number
            except Exception as e:
                print(f"Error contacting registry service: {str(e)}")
        
        # Try getting highest node number from bootstrap nodes
        highest_node = self.find_highest_node_number()
        if highest_node >= 2:
            # Use next available number
            self.registered_node_number = highest_node + 1
            return self.registered_node_number
        
        # Final fallback: Generate a random high number if all else fails
        # This ensures no conflict with bootstrap nodes (1-2)
        # Use timestamp + random to minimize collision chance
        timestamp = int(time.time()) % 1000
        random_part = random.randint(1000, 9999)
        fallback_node_number = 3000 + timestamp + random_part
        
        self.registered_node_number = fallback_node_number
        return fallback_node_number
    
    def find_highest_node_number(self) -> int:
        """
        Find the highest node number currently in use by querying known peers.
        
        Returns:
            int: The highest node number found, or 2 if none found
        """
        highest = 2  # Start at 2, as bootstrap nodes are 1 and 2
        
        # Try bootstrap nodes first
        for node in self.bootstrap_nodes:
            try:
                host, port = node.split(':')
                url = f"http://{host}:{port}/api/network/status"
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    # Try to get peer data which includes node numbers
                    if 'peers' in data:
                        for peer in data['peers']:
                            if 'node_number' in peer and peer['node_number'] > highest:
                                highest = peer['node_number']
                    # Also check for total node count as a fallback
                    elif 'node_count' in data and data['node_count'] > highest:
                        # Use node count as approximate highest node number
                        highest = data['node_count']
            except Exception as e:
                print(f"Error querying bootstrap node {node}: {str(e)}")
                
        return highest
    
    def find_available_ports(self) -> Tuple[int, int]:
        """
        Find available ports for P2P and Web services.
        
        Returns:
            Tuple[int, int]: A tuple of (p2p_port, web_port)
        """
        # If config already has valid ports, use them
        p2p_port = self.config.get('p2p_port')
        web_port = self.config.get('web_port')
        
        if p2p_port and web_port:
            # Check if these ports are available
            if self.is_port_available(p2p_port) and self.is_port_available(web_port):
                return p2p_port, web_port
        
        # Start from standard base ports
        base_p2p_port = 9000  # P2P starts at 9000
        base_web_port = 8001  # Web starts at 8001
        
        # Try to find available ports, keeping the standard offset
        p2p_port = base_p2p_port
        web_port = base_web_port
        offset = 0
        
        # Try up to 1000 port combinations
        while offset < 1000:
            p2p_port = base_p2p_port + offset
            web_port = base_web_port + offset
            
            if self.is_port_available(p2p_port) and self.is_port_available(web_port):
                return p2p_port, web_port
            
            offset += 1
        
        # If no ports found, raise exception
        raise RuntimeError("No available port pairs found for node services")
    
    def is_port_available(self, port: int) -> bool:
        """
        Check if a port is available for use.
        
        Args:
            port: The port number to check
            
        Returns:
            bool: True if port is available, False otherwise
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Set a short timeout to avoid hanging
            sock.settimeout(0.5)
            # Try to bind to the port
            result = sock.connect_ex(('127.0.0.1', port))
            return result != 0  # If result is not 0, port is available
        finally:
            sock.close()
    
    def discover_peers(self) -> List[Dict[str, Any]]:
        """
        Discover peers in the GlobalCoyn network.
        
        Returns:
            List[Dict[str, Any]]: List of discovered peer information
        """
        discovered = []
        
        # Try bootstrap nodes first
        for node in self.bootstrap_nodes:
            try:
                host, port = node.split(':')
                url = f"http://{host}:{port}/api/network/peers"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    # Add discovered peers to our list
                    if 'peers' in data:
                        for peer in data['peers']:
                            if peer not in discovered:
                                discovered.append(peer)
            except Exception as e:
                print(f"Error discovering peers from {node}: {str(e)}")
        
        # Save discovered peers for future use
        self.discovered_peers = discovered
        return discovered
    
    def connect_to_peers(self, api_base: str) -> List[Dict[str, Any]]:
        """
        Connect to discovered peers.
        
        Args:
            api_base: Base URL for node API
            
        Returns:
            List[Dict[str, Any]]: List of successfully connected peers
        """
        connected = []
        
        # First discover peers if we don't have any
        if not self.discovered_peers:
            self.discover_peers()
        
        # Try to connect to each peer
        for peer in self.discovered_peers:
            try:
                # Extract peer connection details
                address = peer.get('address', peer.get('host', ''))
                port = peer.get('p2p_port', peer.get('port', 9000))
                
                if not address:
                    continue
                
                # Connect to the peer via our node API
                connect_url = f"{api_base}/network/connect"
                response = requests.post(connect_url, 
                                      json={"address": address, "port": port},
                                      timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success', False):
                        connected.append(peer)
            except Exception as e:
                print(f"Error connecting to peer {peer}: {str(e)}")
        
        return connected