"""
GlobalCoyn Bootstrap Node Configuration
--------------------------------------
Configuration for bootstrap nodes in the GlobalCoyn network.
These nodes are the entry points for new nodes joining the network.
"""

import os
import json
import logging
import socket
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bootstrap.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gcn_bootstrap")

class BootstrapNodeManager:
    """Manage bootstrap node configuration and operation"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the bootstrap node manager.
        
        Args:
            config_path: Path to configuration file, or None to use default
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        
        # Default bootstrap nodes (production)
        self.bootstrap_nodes = [
            {"host": "node1.globalcoyn.com", "p2p_port": 9000, "web_port": 8001},
            {"host": "node2.globalcoyn.com", "p2p_port": 9000, "web_port": 8001},
        ]
        
        # Development bootstrap nodes
        self.dev_bootstrap_nodes = [
            {"host": "localhost", "p2p_port": 9000, "web_port": 8001},
            {"host": "localhost", "p2p_port": 9001, "web_port": 8002},
        ]
        
        # If we're running as a bootstrap node
        self.is_bootstrap_node = False
        self.node_number = None
        
    def _get_default_config_path(self) -> str:
        """Get the default path for bootstrap configuration."""
        home_dir = str(Path.home())
        config_dir = os.path.join(home_dir, ".globalcoyn")
        
        # Create directory if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        return os.path.join(config_dir, "bootstrap_config.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {str(e)}")
        
        # Return default config if file doesn't exist or has error
        return {
            "production_mode": False,
            "is_bootstrap_node": False,
            "node_number": None,
            "custom_bootstrap_nodes": []
        }
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
    
    def is_production_mode(self) -> bool:
        """Check if we're running in production mode."""
        return self.config.get("production_mode", False)
    
    def get_bootstrap_nodes(self) -> List[Dict[str, Any]]:
        """
        Get the list of bootstrap nodes based on environment.
        
        Returns:
            List of bootstrap node configurations
        """
        # First check for custom bootstrap nodes in config
        custom_nodes = self.config.get("custom_bootstrap_nodes", [])
        if custom_nodes:
            return custom_nodes
        
        # Otherwise use appropriate defaults
        if self.is_production_mode():
            return self.bootstrap_nodes
        else:
            return self.dev_bootstrap_nodes
    
    def configure_as_bootstrap_node(self, node_number: int) -> None:
        """
        Configure this instance as a bootstrap node.
        
        Args:
            node_number: Bootstrap node number (should be 1 or 2)
        """
        if node_number not in [1, 2]:
            raise ValueError("Bootstrap node number must be 1 or 2")
        
        self.is_bootstrap_node = True
        self.node_number = node_number
        
        # Update config
        self.config["is_bootstrap_node"] = True
        self.config["node_number"] = node_number
        self.save_config()
        
        logger.info(f"Configured as bootstrap node #{node_number}")
    
    def setup_bootstrap_node(self, p2p_port: int, web_port: int) -> None:
        """
        Set up the bootstrap node with specific ports.
        
        Args:
            p2p_port: P2P network port
            web_port: Web API port
        """
        if not self.is_bootstrap_node:
            raise RuntimeError("Not configured as a bootstrap node")
        
        # Check if the ports are available
        if not self._is_port_available(p2p_port):
            logger.warning(f"P2P port {p2p_port} is not available")
        
        if not self._is_port_available(web_port):
            logger.warning(f"Web port {web_port} is not available")
        
        # Update config with ports
        self.config["p2p_port"] = p2p_port
        self.config["web_port"] = web_port
        self.save_config()
        
        logger.info(f"Bootstrap node configured with P2P port {p2p_port} and Web port {web_port}")
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', port))
            return result != 0
        finally:
            sock.close()
    
    def register_with_network(self, api_url: str) -> bool:
        """
        Register this bootstrap node with the network registry.
        
        Args:
            api_url: URL of the node's API
            
        Returns:
            bool: Success status
        """
        if not self.is_bootstrap_node:
            return False
            
        try:
            # Only used in production
            if self.is_production_mode():
                registry_url = "https://registry.globalcoyn.com/register_bootstrap"
                data = {
                    "node_number": self.node_number,
                    "p2p_port": self.config.get("p2p_port"),
                    "web_port": self.config.get("web_port"),
                    "api_url": api_url
                }
                
                response = requests.post(registry_url, json=data, timeout=10)
                return response.status_code == 200
            
            # In development, just return success
            return True
        except Exception as e:
            logger.error(f"Error registering bootstrap node: {str(e)}")
            return False
    
    def get_node_info(self) -> Dict[str, Any]:
        """
        Get information about this bootstrap node.
        
        Returns:
            Dict with node information
        """
        if not self.is_bootstrap_node:
            return {"error": "Not a bootstrap node"}
            
        return {
            "is_bootstrap": True,
            "node_number": self.node_number,
            "p2p_port": self.config.get("p2p_port"),
            "web_port": self.config.get("web_port"),
            "production_mode": self.is_production_mode()
        }