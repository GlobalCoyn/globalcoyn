#!/usr/bin/env python3
"""
GlobalCoyn Node Manager
-----------------------
Handles node lifecycle with throttling to prevent excessive network activity
"""

import os
import sys
import subprocess
import time
import signal
import requests
import json
import threading
import logging
from typing import Dict, Any, Optional, Tuple, List

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Import optimized components
try:
    from optimized.rate_limited_logger import RateLimitedLogger
    # Use rate-limited logger for reduced log spam
    logger = RateLimitedLogger("NodeManager")
except ImportError:
    # Fall back to standard logger if optimized version not available
    logger = logging.getLogger("NodeManager")

class NodeManager:
    """
    Manages GlobalCoyn node lifecycle with built-in throttling to prevent
    application freezing due to excessive API requests.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with configuration
        
        Args:
            config: Configuration dictionary with node settings
        """
        self.config = config
        self.node_process = None
        self.node_running = False
        self.log_buffer = []
        self.sync_active = False
        
        # Throttling settings
        self.api_request_interval = 5.0  # Seconds between API status requests
        self.last_api_request = 0
        
        # Node status
        self.node_number = config.get('node_number', 3)
        self.p2p_port = config.get('p2p_port', 9002)
        self.web_port = config.get('web_port', 8003)
        
        # Setup data directory
        self.data_dir = os.path.expanduser(config.get('data_directory', '~/GlobalCoyn'))
        os.makedirs(self.data_dir, exist_ok=True)
    
    def start_node(self, node_number: int, p2p_port: int, web_port: int, callback=None) -> bool:
        """
        Start a blockchain node with the given configuration
        
        Args:
            node_number: The node number to use
            p2p_port: P2P communication port
            web_port: Web API port
            callback: Optional callback function for log updates
            
        Returns:
            bool: True if node started successfully
        """
        self.node_number = node_number
        self.p2p_port = p2p_port
        self.web_port = web_port
        self.log_callback = callback
        
        # Update the configuration for future reference
        self.config['node_number'] = node_number
        self.config['p2p_port'] = p2p_port
        self.config['web_port'] = web_port
        
        # Environment for the node process
        env = os.environ.copy()
        env['GCN_NODE_NUM'] = str(node_number)
        env['GCN_P2P_PORT'] = str(p2p_port)
        env['GCN_WEB_PORT'] = str(web_port)
        
        # Production mode setting
        if self.config.get('production_mode', False):
            env['GCN_PRODUCTION'] = 'true'
            env['GCN_SYNC_THROTTLE'] = 'true'  # Enable sync throttling in production
        else:
            # In development, throttling is even more important
            env['GCN_SYNC_THROTTLE'] = 'true'
            env['GCN_SYNC_INTERVAL'] = '30'  # 30 second intervals between sync attempts
        
        # Add rate limiting environment variables to prevent API spam
        env['GCN_API_RATE_LIMIT'] = 'true'  # Enable API rate limiting
        env['GCN_MAX_REQUESTS_PER_MINUTE'] = '30'  # Limit to 30 requests per minute
        
        # Set PYTHONUNBUFFERED to get real-time logs
        env['PYTHONUNBUFFERED'] = '1'
        
        # Find the app.py location
        app_path = os.path.join(self.data_dir, "app.py")
        
        self.log("Starting node with configuration:")
        self.log(f"- Node Number: {node_number}")
        self.log(f"- P2P Port: {p2p_port}")
        self.log(f"- Web Port: {web_port}")
        self.log(f"- Data Directory: {self.data_dir}")
        
        # Check if app.py exists, run working_node.sh if needed
        if not os.path.exists(app_path):
            self.log("app.py not found, running working_node.sh to set up node")
            self.setup_node_using_script()
            
            # Check again if app.py exists after setup
            if not os.path.exists(app_path):
                self.log("ERROR: Failed to create app.py with working_node.sh")
                return False
        
        # Start the node process with reduced sync frequency
        self.log(f"Launching node process with app.py at {app_path}")
        try:
            self.node_process = subprocess.Popen(
                [sys.executable, app_path],
                cwd=self.data_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Start a thread to read and filter the output
            threading.Thread(target=self._read_filtered_output, daemon=True).start()
            
            # Mark as running
            self.node_running = True
            
            # Start the monitoring thread for controlled API access
            threading.Thread(target=self._throttled_status_monitor, daemon=True).start()
            
            return True
        except Exception as e:
            self.log(f"Error starting node: {str(e)}")
            return False
    
    def _read_filtered_output(self):
        """Read node output with filtering to reduce noise"""
        if not self.node_process:
            return
        
        # Define patterns to filter out spam
        filter_patterns = [
            "Running on",  # Flask startup messages
            "Press CTRL+C to quit",  # Flask startup messages
            "Restarting with stat",  # Flask auto-reload
            "Debugger is active",  # Flask debug messages
            "Debugger PIN",  # Flask debug PIN
            "127.0.0.1 - -",  # Access logs
            "- - [",  # Common log format
            "* Detected change in",  # Flask auto-reload
            "* Restarting with",  # Flask auto-reload
            "/api/blockchain HTTP",  # Status API spam
            "Transaction ",  # Transaction logs during sync
            "Checking block",  # Block checking logs during sync
            "TRANSFER | From:"  # Transaction details during sync
        ]
        
        try:
            for line in iter(self.node_process.stdout.readline, ''):
                # Skip lines that match filter patterns unless in debug mode
                if any(pattern in line for pattern in filter_patterns) and 'debug' not in line.lower():
                    continue
                
                # Skip empty lines
                if not line.strip():
                    continue
                
                # Log the line
                self.log(line.strip())
        except Exception as e:
            self.log(f"Error reading node output: {str(e)}")
    
    def log(self, message: str):
        """Add a log message and call the callback if available"""
        timestamp = time.strftime('%H:%M:%S')
        formatted_msg = f"[{timestamp}] {message}"
        
        # Add to buffer
        self.log_buffer.append(formatted_msg)
        if len(self.log_buffer) > 100:
            self.log_buffer = self.log_buffer[-100:]  # Keep last 100 messages
        
        # Call the callback if available
        if hasattr(self, 'log_callback') and self.log_callback:
            try:
                self.log_callback(formatted_msg)
            except Exception as e:
                logger.error(f"Error in log callback: {str(e)}")
        
        # Also log to standard logger
        logger.info(message)
    
    def _throttled_status_monitor(self):
        """Monitor node status with throttling to prevent API spam"""
        while self.node_running and self.node_process:
            try:
                # Check if enough time has passed since last request
                current_time = time.time()
                if current_time - self.last_api_request < self.api_request_interval:
                    # Not time for a new request yet, sleep for a bit
                    time.sleep(0.5)
                    continue
                
                # Update the last request timestamp
                self.last_api_request = current_time
                
                # Check if the node is still running
                if self.node_process.poll() is not None:
                    self.log(f"Node process exited with code {self.node_process.returncode}")
                    self.node_running = False
                    break
                
                # Make a throttled status check
                self.check_node_status()
                
                # Adaptive sleep - shorter when starting up, longer when stable
                if self.sync_active:
                    # When sync is active, check more frequently
                    time.sleep(self.api_request_interval / 2)
                else:
                    # When stable, wait the full interval
                    time.sleep(self.api_request_interval)
            except Exception as e:
                self.log(f"Error in status monitor: {str(e)}")
                time.sleep(self.api_request_interval)
    
    def check_node_status(self) -> Dict[str, Any]:
        """
        Check the status of the node with throttling built in
        
        Returns:
            Dict[str, Any]: Status information or empty dict if unavailable
        """
        if not self.node_running:
            return {}
        
        try:
            # Use a very short timeout to avoid blocking
            response = requests.get(
                f"http://localhost:{self.web_port}/api/blockchain", 
                timeout=1.0
            )
            
            if response.status_code == 200:
                status_data = response.json()
                
                # Update sync status if we have chain lengths
                if 'chain_length' in status_data:
                    is_syncing = False
                    if 'highest_peer_chain' in status_data and status_data['highest_peer_chain'] > status_data['chain_length']:
                        is_syncing = True
                    
                    self.sync_active = is_syncing
                    
                return status_data
            else:
                self.log(f"Non-200 response from node API: {response.status_code}")
                return {}
        except requests.exceptions.ConnectTimeout:
            # This is normal during startup, don't spam logs
            return {}
        except requests.exceptions.ConnectionError:
            # Connection refused - node is starting up
            return {}
        except Exception as e:
            self.log(f"Error checking node status: {str(e)}")
            return {}
    
    def setup_node_using_script(self) -> bool:
        """
        Use working_node.sh to set up the node environment
        
        Returns:
            bool: True if setup was successful
        """
        self.log("Setting up node environment using working_node.sh")
        
        # Locate the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, "working_node.sh")
        
        if not os.path.exists(script_path):
            self.log(f"ERROR: working_node.sh not found at {script_path}")
            return False
        
        # Make sure the script is executable
        os.chmod(script_path, 0o755)
        
        # Run the script with our node configuration
        cmd = [
            'bash', script_path,
            '--node-num', str(self.node_number),
            '--p2p-port', str(self.p2p_port),
            '--web-port', str(self.web_port),
            '--dir', self.data_dir,
            '--setup-only'  # Only setup, don't start the node
        ]
        
        self.log(f"Running setup command: {' '.join(cmd)}")
        
        try:
            # Run the setup process
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            # Log the output
            for line in process.stdout.splitlines():
                self.log(f"Setup: {line}")
            
            # Check if app.py was created
            app_path = os.path.join(self.data_dir, "app.py")
            if os.path.exists(app_path):
                self.log(f"Setup successful, app.py created at {app_path}")
                return True
            else:
                self.log("Setup script ran but app.py was not created")
                return False
        except subprocess.CalledProcessError as e:
            self.log(f"Setup script failed with code {e.returncode}")
            for line in e.stderr.splitlines():
                self.log(f"Error: {line}")
            return False
        except Exception as e:
            self.log(f"Error running setup script: {str(e)}")
            return False
    
    def stop_node(self) -> bool:
        """
        Stop the running node
        
        Returns:
            bool: True if node was stopped
        """
        if not self.node_running or not self.node_process:
            self.log("No node running to stop")
            return True  # Already stopped
        
        self.log("Stopping GlobalCoyn node...")
        
        try:
            # Try to stop the node gracefully first
            try:
                # Ask the node to shut down via API (in case we implement this)
                requests.post(
                    f"http://localhost:{self.web_port}/api/node/shutdown", 
                    timeout=1.0
                )
            except:
                # Ignore errors - might not be implemented
                pass
            
            # Send SIGTERM for a gentle shutdown
            self.node_process.terminate()
            
            # Wait up to 3 seconds for the process to exit
            for _ in range(6):
                if self.node_process.poll() is not None:
                    self.log(f"Node process exited with code {self.node_process.returncode}")
                    self.node_running = False
                    return True
                time.sleep(0.5)
            
            # If still running, use SIGKILL
            self.log("Node did not exit gracefully, using SIGKILL")
            self.node_process.kill()
            
            # Wait again for the process to exit
            for _ in range(6):
                if self.node_process.poll() is not None:
                    self.log(f"Node process killed with SIGKILL, exit code {self.node_process.returncode}")
                    self.node_running = False
                    return True
                time.sleep(0.5)
            
            self.log("WARNING: Node process did not respond to SIGKILL")
            return False
        except Exception as e:
            self.log(f"Error stopping node: {str(e)}")
            return False
        finally:
            # Regardless of how we got here, mark as not running
            self.node_running = False
    
    def is_running(self) -> bool:
        """
        Check if the node is running
        
        Returns:
            bool: True if node is running
        """
        if not self.node_process:
            return False
        
        # Check if process is still alive
        return self.node_process.poll() is None
    
    def get_node_info(self) -> Dict[str, Any]:
        """
        Get node information
        
        Returns:
            Dict[str, Any]: Node information
        """
        return {
            'running': self.node_running,
            'node_number': self.node_number,
            'p2p_port': self.p2p_port,
            'web_port': self.web_port,
            'data_dir': self.data_dir,
            'pid': self.node_process.pid if self.node_process else None,
            'sync_active': self.sync_active
        }

# Helper function to run a node from command line
def main():
    """Command line entry point for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GlobalCoyn Node Manager')
    parser.add_argument('--node-num', type=int, default=3, help='Node number')
    parser.add_argument('--p2p-port', type=int, default=9002, help='P2P port')
    parser.add_argument('--web-port', type=int, default=8003, help='Web port')
    parser.add_argument('--data-dir', type=str, default='~/GlobalCoyn', help='Data directory')
    parser.add_argument('--production', action='store_true', help='Run in production mode')
    
    args = parser.parse_args()
    
    config = {
        'node_number': args.node_num,
        'p2p_port': args.p2p_port,
        'web_port': args.web_port,
        'data_directory': os.path.expanduser(args.data_dir),
        'production_mode': args.production
    }
    
    node_manager = NodeManager(config)
    
    try:
        print(f"Starting node {args.node_num} on ports P2P:{args.p2p_port}, Web:{args.web_port}")
        success = node_manager.start_node(
            args.node_num, args.p2p_port, args.web_port, 
            callback=lambda msg: print(msg)
        )
        
        if success:
            print("Node started successfully. Press Ctrl+C to stop.")
            while node_manager.is_running():
                time.sleep(1)
        else:
            print("Failed to start node.")
            return 1
    except KeyboardInterrupt:
        print("Stopping node...")
        node_manager.stop_node()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())