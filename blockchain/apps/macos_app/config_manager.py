"""
GlobalCoyn Configuration Manager
-------------------------------
Manage configuration settings for the GlobalCoyn application.
"""

import os
import json
import socket
import platform
from typing import Dict, Any, Optional

class ConfigManager:
    """Manage GlobalCoyn application configuration with environment awareness"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager"""
        # Default configuration path
        if config_path is None:
            self.config_path = os.path.join(os.path.expanduser("~/GlobalCoyn"), "node_config.json")
        else:
            self.config_path = config_path
            
        # Set up configuration directory
        config_dir = os.path.dirname(self.config_path)
        os.makedirs(config_dir, exist_ok=True)
        
        # Load or create configuration
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration with environment awareness.
        
        Returns:
            Dict[str, Any]: The configuration dictionary
        """
        # Check if we're in production mode (from environment or saved config)
        env_production = os.environ.get('GCN_PRODUCTION', 'false').lower() == 'true'
        
        # Create default configuration
        hostname = socket.gethostname()
        default_config = {
            "node_number": 3,  # Default to node 3 (1-2 are bootstrap nodes)
            "p2p_port": 9002,  # Default to port 9002 for node 3
            "web_port": 8003,  # Default to port 8003 for node 3
            "data_directory": os.path.expanduser("~/GlobalCoyn"),
            "enable_mining": True,
            "production_mode": env_production,
            "hostname": hostname,
            "platform": platform.system(),
            "version": "1.0.0"
        }
        
        # Try to load existing configuration if available
        config = default_config.copy()
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    saved_config = json.load(f)
                    # Update config with saved values, preserving defaults for missing keys
                    config.update(saved_config)
                    print(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                print(f"Error loading configuration from {self.config_path}: {str(e)}")
        
        # Override from environment variables if provided
        if 'GCN_NODE_NUM' in os.environ:
            try:
                config['node_number'] = int(os.environ['GCN_NODE_NUM'])
            except:
                pass
                
        if 'GCN_P2P_PORT' in os.environ:
            try:
                config['p2p_port'] = int(os.environ['GCN_P2P_PORT'])
            except:
                pass
                
        if 'GCN_WEB_PORT' in os.environ:
            try:
                config['web_port'] = int(os.environ['GCN_WEB_PORT'])
            except:
                pass
        
        # Override production mode from environment if specified
        if 'GCN_PRODUCTION' in os.environ:
            config['production_mode'] = env_production
        
        # Set API endpoints based on environment
        if config.get('production_mode', False):
            config["api_base_url"] = "https://api.globalcoyn.com"
            config["bootstrap_nodes"] = [
                "node1.globalcoyn.com:8001",
                "node2.globalcoyn.com:8001",
                "node3.globalcoyn.com:8001",
                "node4.globalcoyn.com:8001",
                "node5.globalcoyn.com:8001"
            ]
            config["registry_url"] = "https://registry.globalcoyn.com"
        else:
            config["api_base_url"] = f"http://localhost:{config['web_port']}"
            config["bootstrap_nodes"] = [
                "localhost:8001",
                "localhost:8002"
            ]
            config["registry_url"] = "http://localhost:8001/api/node/register"
        
        return config
    
    def save_config(self) -> bool:
        """
        Save the current configuration to disk.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Write to file
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
            
            print(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            print(f"Error saving configuration to {self.config_path}: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key
            default: Default value if key not found
            
        Returns:
            Any: The configuration value or default
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key
            value: The value to set
        """
        self.config[key] = value
    
    def toggle_production_mode(self) -> bool:
        """
        Toggle between production and development mode.
        
        Returns:
            bool: New production mode state
        """
        current_mode = self.config.get('production_mode', False)
        new_mode = not current_mode
        
        # Update the configuration
        self.config['production_mode'] = new_mode
        
        # Update dependent settings
        if new_mode:
            self.config["api_base_url"] = "https://api.globalcoyn.com"
            self.config["bootstrap_nodes"] = [
                "node1.globalcoyn.com:8001",
                "node2.globalcoyn.com:8001",
                "node3.globalcoyn.com:8001",
                "node4.globalcoyn.com:8001",
                "node5.globalcoyn.com:8001"
            ]
            self.config["registry_url"] = "https://registry.globalcoyn.com"
        else:
            web_port = self.config.get('web_port', 8001)
            self.config["api_base_url"] = f"http://localhost:{web_port}"
            self.config["bootstrap_nodes"] = [
                "localhost:8001",
                "localhost:8002"
            ]
            self.config["registry_url"] = f"http://localhost:8001/api/node/register"
        
        # Save the updated configuration
        self.save_config()
        
        return new_mode