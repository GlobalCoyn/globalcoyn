#!/usr/bin/env python3
"""
GlobalCoyn Bootstrap Node Setup
------------------------------
Sets up and launches a bootstrap node for the GlobalCoyn network.
"""

import os
import sys
import json
import time
import argparse
import subprocess
import logging
from pathlib import Path

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import bootstrap configuration
from network.bootstrap_config import BootstrapNodeManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bootstrap_setup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gcn_bootstrap_setup")

def setup_bootstrap_node():
    """Set up and launch a bootstrap node."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Set up a GlobalCoyn bootstrap node")
    parser.add_argument("--node-number", type=int, choices=[1, 2], required=True,
                        help="Bootstrap node number (1 or 2)")
    parser.add_argument("--p2p-port", type=int, default=9000,
                        help="P2P network port (default: 9000)")
    parser.add_argument("--web-port", type=int, default=8001,
                        help="Web API port (default: 8001)")
    parser.add_argument("--production", action="store_true",
                        help="Run in production mode")
    parser.add_argument("--data-dir", type=str,
                        help="Directory for blockchain data (default: ~/.globalcoyn)")
    
    args = parser.parse_args()
    
    # Initialize bootstrap manager
    bootstrap_manager = BootstrapNodeManager()
    
    # Set production mode
    bootstrap_manager.config["production_mode"] = args.production
    bootstrap_manager.save_config()
    
    # Configure as bootstrap node
    bootstrap_manager.configure_as_bootstrap_node(args.node_number)
    bootstrap_manager.setup_bootstrap_node(args.p2p_port, args.web_port)
    
    # Set up data directory
    data_dir = args.data_dir
    if not data_dir:
        home_dir = str(Path.home())
        data_dir = os.path.join(home_dir, ".globalcoyn", f"bootstrap{args.node_number}")
    
    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Create node configuration file
    node_config = {
        "node_number": args.node_number,
        "p2p_port": args.p2p_port,
        "web_port": args.web_port,
        "production_mode": args.production,
        "is_bootstrap_node": True,
        "data_dir": data_dir,
        "max_connections": 50,  # Bootstrap nodes accept more connections
        "log_level": "INFO"
    }
    
    config_path = os.path.join(data_dir, "node_config.json")
    with open(config_path, 'w') as f:
        json.dump(node_config, f, indent=2)
    
    logger.info(f"Created bootstrap node configuration at {config_path}")
    
    # Generate a wallet for the bootstrap node if not exists
    wallet_path = os.path.join(data_dir, "wallet.key")
    if not os.path.exists(wallet_path):
        logger.info("Generating wallet for bootstrap node...")
        try:
            # Look for wallet.py in various locations
            wallet_script = None
            possible_paths = [
                os.path.join(parent_dir, "core", "wallet.py"),
                os.path.join(parent_dir, "wallet.py")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    wallet_script = path
                    break
            
            if wallet_script:
                cmd = [sys.executable, wallet_script, "--generate", "--output", wallet_path]
                subprocess.run(cmd, check=True)
                logger.info(f"Generated wallet at {wallet_path}")
            else:
                logger.warning("Could not find wallet.py script, skipping wallet generation")
        except Exception as e:
            logger.error(f"Error generating wallet: {str(e)}")
    
    # Check for blockchain data file, create if not exists
    blockchain_data_path = os.path.join(data_dir, "blockchain_data.json")
    if not os.path.exists(blockchain_data_path):
        logger.info("Initializing blockchain data...")
        # Create empty blockchain data
        empty_blockchain = {
            "chain": [],
            "mempool": []
        }
        with open(blockchain_data_path, 'w') as f:
            json.dump(empty_blockchain, f, indent=2)
    
    # Launch the node
    logger.info("Starting bootstrap node...")
    try:
        # Look for the app.py script
        app_script = None
        possible_paths = [
            os.path.join(parent_dir, "nodes", "node1", "app.py"),
            os.path.join(parent_dir, "node", "app.py"),
            os.path.join(parent_dir, "app.py")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                app_script = path
                break
        
        if app_script:
            # Launch the node with the configuration file
            cmd = [
                sys.executable, 
                app_script, 
                "--config", config_path
            ]
            
            # Use subprocess.Popen to run in background
            logger.info(f"Launching node with command: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=parent_dir
            )
            
            # Wait briefly to see if the node starts successfully
            time.sleep(3)
            if process.poll() is None:
                logger.info(f"Bootstrap node started successfully (PID: {process.pid})")
                
                # Create a PID file to track the node
                pid_path = os.path.join(data_dir, "node.pid")
                with open(pid_path, 'w') as f:
                    f.write(str(process.pid))
                
                logger.info(f"Bootstrap node running with PID {process.pid}")
                logger.info(f"PID file created at {pid_path}")
                
                # Try to register with the network (for production mode)
                if args.production:
                    logger.info("Waiting for node to fully start before registering...")
                    time.sleep(5)  # Give the node a little more time to start
                    
                    api_url = f"http://localhost:{args.web_port}"
                    if bootstrap_manager.register_with_network(api_url):
                        logger.info("Successfully registered bootstrap node with network")
                    else:
                        logger.warning("Failed to register bootstrap node with network")
                
                logger.info(f"Bootstrap node #{args.node_number} setup complete")
                logger.info(f"P2P port: {args.p2p_port}")
                logger.info(f"Web port: {args.web_port}")
                logger.info(f"API URL: http://localhost:{args.web_port}")
                
                return 0
            else:
                stdout, stderr = process.communicate()
                logger.error(f"Node failed to start. Exit code: {process.returncode}")
                logger.error(f"STDOUT: {stdout.decode()}")
                logger.error(f"STDERR: {stderr.decode()}")
                return 1
        else:
            logger.error("Could not find app.py script")
            return 1
    except Exception as e:
        logger.error(f"Error launching bootstrap node: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(setup_bootstrap_node())