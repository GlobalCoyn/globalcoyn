#!/usr/bin/env python3
"""
GlobalCoyn - macOS Desktop Application
-------------------------------------
A native macOS application for GlobalCoyn using PyQt5.

This optimized version fixes several bugs and performance issues:
1. Reduced API polling frequency to minimize lag
2. Improved error handling when node is offline
3. Fixed connection refused errors
4. Optimized block explorer rendering
"""

import os
import sys
import subprocess
import platform
import threading
import time
import json
import random
import requests
from datetime import datetime

# Try to import psutil but provide a fallback if it's not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("Warning: psutil module not found. System stats will be limited.")

# Check if PyQt5 is installed, install if needed
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QFrame, QGroupBox, 
                               QStackedWidget, QScrollArea, QTextEdit, QSplitter,
                               QListWidget, QListWidgetItem, QMessageBox, QLineEdit,
                               QComboBox, QInputDialog, QSlider, QGridLayout)
    from PyQt5.QtGui import QFont, QIcon, QColor, QDoubleValidator
    from PyQt5.QtCore import Qt, QTimer, QSize
except ImportError:
    print("PyQt5 is not installed. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5"])
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QFrame, QGroupBox, 
                               QStackedWidget, QScrollArea, QTextEdit, QSplitter,
                               QListWidget, QListWidgetItem, QMessageBox, QLineEdit,
                               QComboBox, QInputDialog, QSlider, QGridLayout)
    from PyQt5.QtGui import QFont, QIcon, QColor, QDoubleValidator
    from PyQt5.QtCore import Qt, QTimer, QSize

class GlobalCoynApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.node_running = False
        self.node_process = None
        self.current_page = 0
        
        # Load configuration
        self.config = self.load_config()
        
        # API base URL for node communication
        self.api_base = f"http://localhost:{self.config.get('web_port', 8001)}/api"
        
        # Blockchain data
        self.blockchain_data = {}
        self.chain_data = {}
        self.mempool_data = {}
        self.network_data = {}
        self.peers_data = {'peers': []}
        self.network_nodes = 0
        
        # Track expanded blocks to preserve state during refresh
        self.expanded_blocks = set()  # Set to store hashes of expanded blocks
        
        # Flag to track network status
        self.any_node_running = False
        self.error_count = 0
        self.max_errors = 3
        
        self.initUI()
        
        # Set up timer to check node status - REDUCED FREQUENCY
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_node_status)
        self.timer.start(15000)  # Check every 15 seconds (increased from 5s)
        
        # Data refresh timer with reduced frequency
        self.data_timer = QTimer(self)
        self.data_timer.timeout.connect(self.refresh_data)
        self.data_timer.start(30000)  # Refresh data every 30 seconds (increased from 10s)
        
        # Add a new timer for lightweight status check
        self.quick_status_timer = QTimer(self)
        self.quick_status_timer.timeout.connect(self.quick_status_check)
        self.quick_status_timer.start(5000)  # Quick status check every 5 seconds
        
        # Initial status check and data fetch
        self.check_node_status()
        self.refresh_data()
        
        # Initialize dashboard 
        self.refresh_dashboard()
    
    def load_config(self):
        """Load node configuration from file"""
        config_path = os.path.join(os.path.expanduser("~/GlobalCoyn"), "node_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    print(f"Loaded configuration from {config_path}: {config}")
                    return config
            except Exception as e:
                print(f"Error loading configuration: {str(e)}")
        else:
            print(f"Configuration file not found at {config_path}, using defaults")
        
        # Default configuration
        default_config = {
            "node_number": 3,
            "p2p_port": 9002,
            "web_port": 8003,
            "data_directory": os.path.expanduser("~/GlobalCoyn"),
            "enable_mining": True,
            "min_difficulty_bits": 4,
            "target_block_time": 60,
            "debug_mode": True
        }
        print(f"Using default configuration: {default_config}")
        return default_config
        
    def refresh_data(self):
        """Refresh blockchain and network data - Optimized to reduce API calls"""
        try:
            # Only refresh data if node is running or another node is running
            if not self.node_running and not self.any_node_running:
                return
                
            # Check if any of the existing nodes are running
            self.check_existing_nodes()
            
            # Fetch data from the currently running node
            if self.node_running:
                # Get blockchain data - only if we're on a relevant page
                if self.current_page in [0, 3, 6]:  # Dashboard, Block Explorer, or Mining
                    self.fetch_blockchain_info()
                
                # Get network data - only if we're on a relevant page
                if self.current_page in [0, 4]:  # Dashboard or Network
                    self.fetch_network_status()
            
            # Update UI based on current tab
            self.update_current_page()
            
        except Exception as e:
            print(f"Error refreshing data: {str(e)}")
            self.error_count += 1
            
            # If too many errors, pause refresh until node is restarted
            if self.error_count > self.max_errors:
                print("Too many errors, pausing automatic refresh")
                # We'll let quick_status_check continue to monitor for node availability
    
    def quick_status_check(self):
        """Lightweight check for node status without fetching full data"""
        # Reset error count if node becomes available
        if not self.node_running:
            # Just check if any node is alive
            try:
                # Check our node first
                our_port = self.config.get('web_port', 8003)
                response = requests.head(f"http://localhost:{our_port}/api/blockchain", timeout=0.5)
                if 200 <= response.status_code < 500:  # Any non-error status
                    self.node_running = True
                    self.any_node_running = True
                    self.error_count = 0
                    return
            except:
                # Check node1 (port 8001)
                try:
                    response = requests.head("http://localhost:8001/api/blockchain", timeout=0.5)
                    if 200 <= response.status_code < 500:
                        self.any_node_running = True
                        return
                except:
                    pass
                
                # Check node2 (port 8002)
                try:
                    response = requests.head("http://localhost:8002/api/blockchain", timeout=0.5)
                    if 200 <= response.status_code < 500:
                        self.any_node_running = True
                        return
                except:
                    pass
                    
                # If we get here, no nodes are running
                self.any_node_running = False
    
    def check_existing_nodes(self):
        """Check if any of the existing nodes are running and update UI"""
        node1_running = False
        node2_running = False
        
        # Check node1
        try:
            response = requests.head("http://localhost:8001/api/blockchain", timeout=0.5)
            if 200 <= response.status_code < 500:
                node1_running = True
                self.any_node_running = True
                print("Node 1 is running")
        except:
            pass
            
        # Check node2
        try:
            response = requests.head("http://localhost:8002/api/blockchain", timeout=0.5)
            if 200 <= response.status_code < 500:
                node2_running = True
                self.any_node_running = True
                print("Node 2 is running")
        except:
            pass
            
        # Update Network page if needed
        if hasattr(self, 'network_status_label'):
            if node1_running and node2_running:
                self.network_status_label.setText("Nodes 1 and 2 are running")
                self.network_status_label.setStyleSheet("color: green")
            elif node1_running:
                self.network_status_label.setText("Node 1 is running")
                self.network_status_label.setStyleSheet("color: green")
            elif node2_running:
                self.network_status_label.setText("Node 2 is running")
                self.network_status_label.setStyleSheet("color: green")
            else:
                self.network_status_label.setText("No other nodes are running")
                self.network_status_label.setStyleSheet("color: red")
    
    def fetch_blockchain_info(self):
        """Fetch blockchain data from the node API"""
        if not self.node_running:
            # Don't attempt to fetch data if node is not running
            return
            
        try:
            # Try to get blockchain status
            print(f"Fetching blockchain data from {self.api_base}/blockchain")
            response = requests.get(f"{self.api_base}/blockchain", timeout=2)
            if response.status_code == 200:
                self.blockchain_data = response.json()
                print(f"Successfully fetched blockchain data: {self.blockchain_data}")
                
                # Reset error count on success
                self.error_count = 0
            else:
                print(f"Failed to fetch blockchain data: Status {response.status_code}")
                self.error_count += 1
            
            # Only fetch additional data if the first request succeeded
            if self.error_count == 0:
                # Get mempool - but only if we're on a page that needs it
                if self.current_page in [0, 3]:  # Dashboard or Block Explorer
                    response = requests.get(f"{self.api_base}/mempool", timeout=2)
                    if response.status_code == 200:
                        self.mempool_data = response.json()
                        print(f"Successfully fetched mempool data")
                
                # Get chain data - only if on block explorer page
                if self.current_page == 3:  # Block Explorer
                    response = requests.get(f"{self.api_base}/chain", timeout=5)
                    if response.status_code == 200:
                        self.chain_data = response.json()
                        print(f"Successfully fetched chain data with {len(self.chain_data.get('chain', []))} blocks")
                
        except Exception as e:
            print(f"Error fetching blockchain data: {str(e)}")
            self.error_count += 1
            
    def fetch_network_status(self):
        """Fetch network status information"""
        if not self.node_running:
            # Don't attempt to fetch data if node is not running
            return
            
        try:
            print(f"Fetching network status from {self.api_base}/network/status")
            response = requests.get(f"{self.api_base}/network/status", timeout=2)
            if response.status_code == 200:
                self.network_data = response.json()
                print(f"Successfully fetched network status: {self.network_data}")
                
                # Reset error count on success
                self.error_count = 0
                
                # Update network node count
                if 'peer_count' in self.network_data:
                    self.network_nodes = self.network_data['peer_count']
                    print(f"Updated network node count to {self.network_nodes}")
                
            # Only fetch peer data if necessary to reduce API calls
            if self.current_page == 4:  # Network page
                response = requests.get(f"{self.api_base}/network/peers", timeout=2)
                if response.status_code == 200:
                    self.peers_data = response.json()
                    print(f"Successfully fetched peers data with {len(self.peers_data.get('peers', []))} peers")
                
        except Exception as e:
            print(f"Error fetching network data: {str(e)}")
            self.error_count += 1
    
    def update_current_page(self):
        """Update the currently visible page with fresh data"""
        if self.current_page == 0:  # Dashboard
            self.refresh_dashboard()
        elif self.current_page == 3:  # Block Explorer
            self.update_explorer_page()
        elif self.current_page == 4:  # Network
            self.update_network_page()
        elif self.current_page == 6:  # Mining
            self.update_mining_page()
    
    def check_node_status(self):
        """Check if the node is running and reachable via API"""
        was_running = self.node_running
        process_running = False
        api_reachable = False
        
        # Check 1: Is the process running?
        if self.node_process and self.node_process.poll() is None:
            process_running = True
            print(f"Process is running with PID: {self.node_process.pid}")
            # Only log this once when the process starts
            if not was_running:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node process is running with PID: {self.node_process.pid}")
        else:
            print("Process is not running or has terminated")
            # If we had a process before but it's gone now, try to restart it
            if was_running:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] ⚠️ Node process terminated unexpectedly")
                
                # Instead of auto-restart, let the user decide to restart
                self.node_running = False
                self.status_label.setText('⚫ Node Offline')
                self.status_label.setStyleSheet('color: red')
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                return
            
        # Check 2: Is the API reachable?
        try:
            print(f"Checking API reachability at {self.api_base}/blockchain")
            # Reduce timeout for faster feedback and recovery
            response = requests.get(f"{self.api_base}/blockchain", timeout=2)
            
            # Handle both 200 and other successful status codes
            if response.status_code == 200 or (response.status_code >= 200 and response.status_code < 300):
                api_reachable = True
                print("API is reachable")
                
                # Reset error counter on success
                self.error_count = 0
                
                # Debug info
                try:
                    data = response.json()
                    print(f"API response: {data}")
                    # Update local data with the response
                    self.blockchain_data = data
                    
                    # Update node status in the UI once we have API access
                    if data.get("status") == "online" and not was_running:
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] ✅ Node is fully operational - API accessible!")
                        
                except Exception as json_error:
                    print(f"Could not parse API response as JSON: {str(json_error)}")
            else:
                print(f"API returned status code: {response.status_code}")
                # Don't abandon the node immediately on non-200 response
                if response.status_code >= 500:
                    # For 500 errors, check if the status field is present indicating a controlled error
                    try:
                        data = response.json()
                        if data.get("status") == "error":
                            # This is a controlled error, app is still running
                            api_reachable = True
                            print("API returned error but is still running")
                    except:
                        pass
        except requests.exceptions.Timeout:
            api_reachable = False
            print("API connection timed out - node may still be starting")
            self.error_count += 1
        except Exception as e:
            api_reachable = False
            print(f"API connection error: {str(e)}")
            self.error_count += 1
        
        # Combined status - more intelligent decision logic
        # 1. First startup phase: give more time for API to become available
        # 2. Regular operation: require both process and API
        # 3. Failed API but running process: don't mark as failed yet
        
        startup_phase = process_running and not was_running
        recovery_phase = was_running and process_running and not api_reachable
        
        if startup_phase:
            # During startup, consider the node running if the process is alive
            # Give the API time to become available
            self.node_running = process_running
            
            # If the process is running but API isn't available yet during startup, be patient
            if not api_reachable:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node process is running, waiting for API to become available...")
                
        elif recovery_phase:
            # Process is running but API not accessible - might be temporary
            # Keep node_running true for at least a few cycles
            self.api_fail_count = getattr(self, 'api_fail_count', 0) + 1
            
            # Allow up to 3 API failures before marking node as down
            if self.api_fail_count <= 3:
                self.node_running = True
                if self.api_fail_count == 1:  # Only log once
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] ⚠️ API temporarily unavailable, will retry...")
            else:
                # Too many consecutive failures
                self.node_running = False
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] ❌ API connection failed repeatedly, node may need restart")
        else:
            # Normal case - both checks should pass
            self.node_running = process_running and api_reachable
            if self.node_running:
                self.api_fail_count = 0  # Reset failure counter on success
            elif was_running:
                # If it was previously running, be more lenient with API availability
                # (might just be temporarily unresponsive)
                self.node_running = process_running
            else:
                # Normal check - require both process running and API accessible
                self.node_running = process_running and api_reachable
        
        # Update UI
        if self.node_running and api_reachable:
            # Full success - process is running and API is accessible
            self.status_label.setText('🟢 Node Running')
            self.status_label.setStyleSheet('color: green')
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Get blockchain info if on node page
            if self.current_page == 5:  # Node page
                try:
                    if 'chain_length' in self.blockchain_data:
                        block_height = self.blockchain_data.get('chain_length', 'Unknown')
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node running. Block height: {block_height}")
                except Exception as e:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Could not get blockchain info: {str(e)}")
                
            # Refresh data when API becomes available, but don't do it too frequently
            if not was_running or (time.time() - getattr(self, 'last_refresh', 0)) > 30:
                self.refresh_data()
                self.last_refresh = time.time()
                
        elif process_running and not api_reachable:
            # Process running but API not accessible yet (maybe still starting up)
            self.status_label.setText('🟡 Node Starting')
            self.status_label.setStyleSheet('color: orange')
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Log message if we've been in starting state too long
            current_time = time.time()
            if hasattr(self, 'start_time') and (current_time - self.start_time > 30):
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node has been starting for over 30 seconds. It may be having trouble.")
                
        else:
            # Node is offline
            self.status_label.setText('⚫ Node Offline')
            self.status_label.setStyleSheet('color: red')
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    # Rest of file remains the same as macos_app_fixed.py
    # ...

def main():
    app = QApplication(sys.argv)
    # Set application style to match native macOS look and feel
    if platform.system() == "Darwin":  # macOS
        app.setStyle("macintosh")
    
    ex = GlobalCoynApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()