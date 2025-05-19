"""
Configuration loader for GlobalCoyn blockchain node
"""
import os
import json
import logging

logger = logging.getLogger("config_loader")

class ConfigLoader:
    def __init__(self, config_file=None):
        self.config = {}
        self.env = os.environ.get("GCN_ENV", "development")
        
        # Default config file based on environment
        if config_file is None:
            if self.env == "production":
                config_file = "production_config.json"
            else:
                config_file = "development_config.json"
                
        # Try to load the configuration file
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Loaded configuration from {config_file}")
            else:
                logger.warning(f"Config file {config_file} not found, using environment variables")
                self._load_from_env()
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Node settings
        self.config["node_settings"] = {
            "domain": os.environ.get("GCN_DOMAIN", "localhost"),
            "use_ssl": os.environ.get("GCN_USE_SSL", "false").lower() == "true",
            "node_name": os.environ.get("GCN_NODE_NAME", "GlobalCoyn Node"),
            "version": os.environ.get("GCN_VERSION", "1.0.0"),
            "environment": self.env
        }
        
        # Network settings
        self.config["network"] = {
            "p2p_port": int(os.environ.get("GCN_P2P_PORT", 9000)),
            "web_port": int(os.environ.get("GCN_WEB_PORT", 8001)),
            "max_peers": int(os.environ.get("GCN_MAX_PEERS", 25)),
            "connection_timeout": int(os.environ.get("GCN_CONN_TIMEOUT", 10)),
            "sync_interval": int(os.environ.get("GCN_SYNC_INTERVAL", 300))
        }
        
        # Security settings
        cors_origins = os.environ.get("GCN_CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
        self.config["security"] = {
            "cors_origins": cors_origins.split(","),
            "rate_limit": {
                "enabled": os.environ.get("GCN_RATE_LIMIT", "false").lower() == "true",
                "requests_per_minute": int(os.environ.get("GCN_RPM", 60))
            },
            "api_keys_enabled": os.environ.get("GCN_API_KEYS", "false").lower() == "true"
        }
        
        # Blockchain settings
        self.config["blockchain"] = {
            "difficulty_adjustment_interval": int(os.environ.get("GCN_DIFF_INTERVAL", 2016)),
            "target_block_time": int(os.environ.get("GCN_TARGET_BLOCK_TIME", 600)),
            "max_transactions_per_block": int(os.environ.get("GCN_MAX_TX_PER_BLOCK", 1000)),
            "mempool_size_limit": int(os.environ.get("GCN_MEMPOOL_LIMIT", 5000)),
            "min_fee": float(os.environ.get("GCN_MIN_FEE", 0.00001))
        }
        
        # Storage settings
        self.config["storage"] = {
            "data_file": os.environ.get("GCN_DATA_FILE", "blockchain_data.json"),
            "backup_interval": int(os.environ.get("GCN_BACKUP_INTERVAL", 100)),
            "max_backups": int(os.environ.get("GCN_MAX_BACKUPS", 10))
        }
        
        # Logging settings
        self.config["logging"] = {
            "level": os.environ.get("GCN_LOG_LEVEL", "INFO"),
            "log_file": os.environ.get("GCN_LOG_FILE", "blockchain.log"),
            "max_size_mb": int(os.environ.get("GCN_LOG_MAX_SIZE", 10)),
            "backup_count": int(os.environ.get("GCN_LOG_BACKUPS", 5))
        }
    
    def get(self, section, key=None, default=None):
        """Get configuration value"""
        if section not in self.config:
            return default
            
        if key is None:
            return self.config[section]
            
        return self.config[section].get(key, default)
        
    def is_production(self):
        """Check if running in production mode"""
        return self.env == "production" or self.config.get("node_settings", {}).get("environment") == "production"

# Global configuration instance
config = ConfigLoader()