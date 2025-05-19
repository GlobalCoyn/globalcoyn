"""
GlobalCoyn Production Configuration
---------------------------------
Configuration settings for the GlobalCoyn network in production mode.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("production.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gcn_production")

class ProductionConfig:
    """Manages production configuration for GlobalCoyn"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize production configuration.
        
        Args:
            config_path: Path to configuration file (None for default)
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        
        # Production endpoints
        self.api_domain = "api.globalcoyn.com"
        self.explorer_domain = "explorer.globalcoyn.com"
        self.website_domain = "globalcoyn.com"
        
        # Network parameters for production
        self.mainnet_p2p_port = 9000
        self.mainnet_web_port = 8001
        
        # SSL/TLS settings
        self.use_ssl = True
        self.ssl_cert_path = None
        self.ssl_key_path = None
    
    def _get_default_config_path(self) -> str:
        """Get default config path."""
        home_dir = str(Path.home())
        config_dir = os.path.join(home_dir, ".globalcoyn")
        
        # Create directory if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        return os.path.join(config_dir, "production_config.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {str(e)}")
        
        # Return default config
        return {
            "production_mode": True,
            "api_url_base": f"https://{self.api_domain}",
            "explorer_url": f"https://{self.explorer_domain}",
            "website_url": f"https://{self.website_domain}",
            "mainnet_bootstrap_nodes": [
                {"host": "node1.globalcoyn.com", "p2p_port": 9000, "web_port": 8001},
                {"host": "node2.globalcoyn.com", "p2p_port": 9000, "web_port": 8001}
            ],
            "dns_seeds": [
                "seed.globalcoyn.com",
                "seed.globalcoyn.net",
                "dnsseed.globalcoyn.org"
            ],
            "connection_limits": {
                "max_outbound": 8,
                "max_inbound": 64,
                "max_peers": 125
            },
            "mempool_limits": {
                "max_transactions": 5000,
                "max_size_mb": 300,
                "min_fee": 0.00001
            },
            "mining_config": {
                "default_difficulty_bits": "0x1f00ffff",
                "difficulty_adjustment_interval": 2016,
                "target_time_per_block": 600  # 10 minutes (like Bitcoin)
            }
        }
    
    def save_config(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            bool: Success status
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
            return False
    
    def get_api_url(self, endpoint: str = "") -> str:
        """
        Get the API URL for a specific endpoint.
        
        Args:
            endpoint: API endpoint (without leading slash)
            
        Returns:
            Full API URL
        """
        base_url = self.config.get("api_url_base", f"https://{self.api_domain}")
        if endpoint:
            if not endpoint.startswith("/"):
                endpoint = f"/{endpoint}"
            return f"{base_url}{endpoint}"
        return base_url
    
    def get_explorer_url(self, resource_type: str = "", resource_id: str = "") -> str:
        """
        Get the blockchain explorer URL.
        
        Args:
            resource_type: Type of resource ('block', 'tx', 'address')
            resource_id: ID of the resource
            
        Returns:
            Explorer URL
        """
        base_url = self.config.get("explorer_url", f"https://{self.explorer_domain}")
        
        if not resource_type:
            return base_url
            
        if resource_type == "block":
            return f"{base_url}/block/{resource_id}"
        elif resource_type == "tx":
            return f"{base_url}/tx/{resource_id}"
        elif resource_type == "address":
            return f"{base_url}/address/{resource_id}"
        else:
            return f"{base_url}/{resource_type}/{resource_id}"
    
    def get_bootstrap_nodes(self) -> list:
        """Get bootstrap nodes for mainnet."""
        return self.config.get("mainnet_bootstrap_nodes", [])
    
    def get_dns_seeds(self) -> list:
        """Get DNS seeds for mainnet."""
        return self.config.get("dns_seeds", [])
    
    def get_connection_limits(self) -> Dict[str, int]:
        """Get connection limits."""
        return self.config.get("connection_limits", {
            "max_outbound": 8,
            "max_inbound": 64,
            "max_peers": 125
        })
    
    def get_mempool_limits(self) -> Dict[str, Any]:
        """Get mempool limits."""
        return self.config.get("mempool_limits", {
            "max_transactions": 5000,
            "max_size_mb": 300,
            "min_fee": 0.00001
        })
    
    def get_mining_config(self) -> Dict[str, Any]:
        """Get mining configuration."""
        return self.config.get("mining_config", {
            "default_difficulty_bits": "0x1f00ffff",
            "difficulty_adjustment_interval": 2016,
            "target_time_per_block": 600
        })
    
    def generate_node_config(self, node_type: str = "regular", 
                           node_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate node configuration for production.
        
        Args:
            node_type: Type of node ('bootstrap', 'miner', 'regular')
            node_number: Node number (required for bootstrap nodes)
            
        Returns:
            Node configuration
        """
        # Basic configuration
        node_config = {
            "production_mode": True,
            "testnet": False,
            "development": False,
            "node_type": node_type,
            "p2p_port": self.mainnet_p2p_port,
            "web_port": self.mainnet_web_port,
            "log_level": "INFO",
            "connection_limits": self.get_connection_limits(),
            "mempool_limits": self.get_mempool_limits(),
            "mining_config": self.get_mining_config()
        }
        
        # Add node-type specific config
        if node_type == "bootstrap":
            if node_number not in [1, 2]:
                raise ValueError("Bootstrap node number must be 1 or 2")
                
            node_config.update({
                "is_bootstrap_node": True,
                "node_number": node_number,
                "max_connections": 125,  # Higher limit for bootstrap nodes
            })
        elif node_type == "miner":
            node_config.update({
                "is_miner": True,
                "auto_mine": True,
                "mining_threads": 2
            })
        
        return node_config