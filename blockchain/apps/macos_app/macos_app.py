#!/usr/bin/env python3
"""
GlobalCoyn - macOS Desktop Application
-------------------------------------
A native macOS application for GlobalCoyn using PyQt5.
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
import traceback
from datetime import datetime

# Import optimized components
from optimized.rate_limited_logger import RateLimitedLogger
from optimized.wallet_cache import WalletCache
from optimized.connection_backoff import ConnectionManager
try:
    # Try to import optimized node sync
    from optimized.improved_node_sync_optimized import enhance_globalcoyn_networking as enhanced_networking
    USING_OPTIMIZED = True
except ImportError:
    # Fall back to original if not available
    from network.improved_node_sync import enhance_globalcoyn_networking as enhanced_networking
    USING_OPTIMIZED = False

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
                               QComboBox, QInputDialog, QSlider, QGridLayout, QProgressBar)
    from PyQt5.QtGui import QFont, QIcon, QColor, QDoubleValidator
    from PyQt5.QtCore import Qt, QTimer, QSize
except ImportError:
    print("PyQt5 is not installed. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5"])
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QFrame, QGroupBox, 
                               QStackedWidget, QScrollArea, QTextEdit, QSplitter,
                               QListWidget, QListWidgetItem, QMessageBox, QLineEdit,
                               QComboBox, QInputDialog, QSlider, QGridLayout, QProgressBar)
    from PyQt5.QtGui import QFont, QIcon, QColor, QDoubleValidator
    from PyQt5.QtCore import Qt, QTimer, QSize

class GlobalCoynApp(QMainWindow):
    # Add optimized methods for better performance
    
    def get_wallet_balance(self, address):
        """Get wallet balance using the optimized cache when available"""
        if not address:
            return 0.0
            
        # If wallet cache is available, use it for better performance
        if self.wallet_cache:
            try:
                balance_info = self.wallet_cache.get_balance(address)
                if balance_info:
                    return balance_info["balance"]
            except Exception as e:
                self.logger.warning(f"Error using wallet cache: {str(e)}")
        
        # Fallback to API request if cache is not available
        try:
            response = self.api_request(f"balance/{address}", timeout=3)
            if response and response.status_code == 200:
                data = response.json()
                return data.get('balance', 0.0)
        except Exception as e:
            self.logger.error(f"Error getting wallet balance for {address}: {str(e)}")
            
        return 0.0
    
    def api_request(self, endpoint, method="GET", data=None, timeout=5):
        """Make an API request with connection backoff"""
        # Form the full URL (handling whether endpoint already has leading slash)
        if endpoint.startswith('http'):
            url = endpoint
        elif endpoint.startswith('/'):
            url = f"{self.api_base}{endpoint}"
        else:
            url = f"{self.api_base}/{endpoint}"
        
        # Check if we should attempt the connection based on backoff status
        if not self.connection_manager.should_attempt_connection(url):
            self.logger.debug(f"Skipping request to {url} due to backoff")
            return None
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=timeout)
            else:
                response = requests.post(url, json=data, timeout=timeout)
            
            # Record successful connection
            self.connection_manager.record_success(url)
            return response
        except Exception as e:
            # Record connection failure
            self.connection_manager.record_failure(url, e)
            self.logger.debug(f"Request failed: {url} - {str(e)}")
            return None
    
    def __init__(self):
        super().__init__()
        self.node_running = False
        self.node_process = None
        self.current_page = 0
        self.start_time = time.time()  # Track app start time for uptime display
        
        # Initialize the rate-limited logger
        self.logger = RateLimitedLogger("gcn_macapp")
        self.logger.info("Initializing GlobalCoyn macOS App with optimized components")
        
        # Initialize connection manager for API requests
        self.connection_manager = ConnectionManager()
        
        # Initialize wallet cache (will be properly set up after blockchain is available)
        self.wallet_cache = None
        
        # Load configuration using new ConfigManager
        from config_manager import ConfigManager
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        
        # Import node discovery module
        from node_discovery import NodeDiscovery
        self.node_discovery = NodeDiscovery(self.config)
        
        # Import node manager module
        from node_manager import NodeManager
        self.node_manager = NodeManager(self.config)
        
        # Set web_port consistently across the app
        # Default to port 8003 for compatibility with existing nodes
        self.web_port = self.config.get('web_port', 8003)
        
        # Ensure consistency - update config if needed
        if self.config.get('web_port') != self.web_port:
            self.config['web_port'] = self.web_port
            self.config_manager.save_config()
            self.logger.info(f"Updated web_port in config to {self.web_port}")
            
        # API base URL for node communication
        if self.config.get('production_mode', False):
            self.api_base = f"{self.config.get('api_base_url', 'https://api.globalcoyn.com')}/api"
        else:
            self.api_base = f"http://localhost:{self.web_port}/api"
            
        print(f"Setting API base URL to {self.api_base}")
        
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
        
        # Sync state tracking variables
        self.initial_sync_complete = False
        self.sync_in_progress = False
        self.total_blockchain_length = 0
        self.local_blockchain_length = 0
        self.sync_start_time = None
        
        self.initUI()
        
        # Set up timer to check node status - OPTIMIZED FREQUENCY
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_node_status)
        self.timer.start(45000)  # Check every 45 seconds during initial startup (increased from 30s)
        
        # Data refresh timer with greatly reduced frequency
        self.data_timer = QTimer(self)
        self.data_timer.timeout.connect(self.refresh_data)
        self.data_timer.start(90000)  # Refresh data every 90 seconds initially (increased from 60s)
        
        # Add a new timer for lightweight status check
        self.quick_status_timer = QTimer(self)
        self.quick_status_timer.timeout.connect(self.quick_status_check)
        self.quick_status_timer.start(15000)  # Quick status check every 15 seconds
        
        # Initial status check and data fetch - delayed to prevent UI lag at startup
        QTimer.singleShot(5000, self.check_node_status)
        self.refresh_data()
        
        # Initialize dashboard 
        self.refresh_dashboard()
    
    def save_config(self):
        """Save configuration to file using ConfigManager"""
        return self.config_manager.save_config()
        
    def safe_api_request(self, endpoint, method="GET", json_data=None, timeout=2, default_value=None):
        """
        Make an API request with proper error handling and fallbacks.
        
        Args:
            endpoint (str): API endpoint (without the base URL)
            method (str): HTTP method ("GET" or "POST")
            json_data (dict): JSON data for POST requests
            timeout (int): Timeout in seconds
            default_value: Value to return on error
            
        Returns:
            Response data (JSON) or default_value on error
        """
        if not self.node_running and not self.any_node_running:
            print(f"API request to {endpoint} skipped - no nodes running")
            return default_value
            
        try:
            # Construct the URL
            url = f"{self.api_base}/{endpoint}"
            print(f"Making {method} request to {url}")
            
            # Make the request with the appropriate method
            if method.upper() == "GET":
                response = requests.get(url, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, json=json_data, timeout=timeout)
            else:
                print(f"Unsupported method: {method}")
                return default_value
                
            # Check if the request was successful
            if response.status_code == 200:
                # Reset error counter on success
                self.error_count = 0
                return response.json()
            else:
                print(f"API returned status {response.status_code} for {endpoint}")
                self.error_count += 1
                return default_value
                
        except requests.exceptions.Timeout:
            print(f"Request timeout for {endpoint}")
            self.error_count += 1
            return default_value
        except requests.exceptions.ConnectionError:
            print(f"Connection error for {endpoint} - node may be offline")
            self.error_count += 1
            return default_value
        except Exception as e:
            print(f"Error in API request to {endpoint}: {str(e)}")
            self.error_count += 1
            return default_value
    
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
                    
                # Update sync status display if we have blockchain data
                if hasattr(self, 'blockchain_data') and self.blockchain_data:
                    # Update local chain length based on blockchain data
                    if 'chain_length' in self.blockchain_data:
                        self.local_blockchain_length = self.blockchain_data['chain_length']
                        
                        # If we're in sync mode, update the status
                        if self.sync_in_progress or self.initial_sync_complete:
                            self.update_sync_status()
            
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
                our_port = self.web_port
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
        else:
            # Node is running, check for sync status if we're still syncing
            if self.sync_in_progress and not self.initial_sync_complete:
                try:
                    # Get just the blockchain info to check sync progress
                    our_port = self.web_port
                    response = requests.get(f"http://localhost:{our_port}/api/blockchain", timeout=1)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Update local chain length if we have it
                        if 'chain_length' in data:
                            current_length = data.get('chain_length', 0)
                            
                            # Only update if the length has changed
                            if current_length != self.local_blockchain_length:
                                self.local_blockchain_length = current_length
                                
                                # Update the UI immediately
                                self.update_sync_status()
                                
                except Exception as e:
                    # Silently ignore errors in quick status check
                    pass

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
            # Try to get blockchain status with optimized request
            self.logger.debug(f"Fetching blockchain data from {self.api_base}/blockchain")
            response = self.api_request("blockchain", timeout=2)
            if response and response.status_code == 200:
                self.blockchain_data = response.json()
                print(f"Successfully fetched blockchain data: {self.blockchain_data}")
            else:
                print(f"Failed to fetch blockchain data: Status {response.status_code}")
            
            # Get mempool with optimized request
            response = self.api_request("mempool", timeout=2)
            if response and response.status_code == 200:
                self.mempool_data = response.json()
                self.logger.debug(f"Successfully fetched mempool data")
                
            # Get chain data with optimized request
            response = self.api_request("chain", timeout=5)
            if response and response.status_code == 200:
                self.chain_data = response.json()
                print(f"Successfully fetched chain data with {len(self.chain_data.get('chain', []))} blocks")
                
        except Exception as e:
            print(f"Error fetching blockchain data: {str(e)}")
            
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
                
                # Update network node count
                if 'peer_count' in self.network_data:
                    self.network_nodes = self.network_data['peer_count']
                    print(f"Updated network node count to {self.network_nodes}")
                
            response = requests.get(f"{self.api_base}/network/peers", timeout=2)
            if response.status_code == 200:
                self.peers_data = response.json()
                print(f"Successfully fetched peers data with {len(self.peers_data.get('peers', []))} peers")
                
        except Exception as e:
            print(f"Error fetching network data: {str(e)}")
    
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
    
    def initUI(self):
        self.setWindowTitle('GlobalCoyn Node')
        self.setGeometry(100, 100, 900, 600)
        
        # Set application icon
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "macapplogo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Create sidebar with logo at top
        sidebar_container = QWidget()
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(10)
        sidebar_container.setLayout(sidebar_layout)
        
        # Add logo with text to sidebar
        if os.path.exists(logo_path):
            # Create a horizontal container for logo and text
            logo_container = QWidget()
            logo_h_layout = QHBoxLayout(logo_container)
            logo_container.setLayout(logo_h_layout)
            
            # Logo (smaller size)
            logo_label = QLabel()
            logo_pixmap = QIcon(logo_path).pixmap(QSize(60, 60))
            logo_label.setPixmap(logo_pixmap)
            logo_h_layout.addWidget(logo_label)
            
            # "GlobalCoyn" text beside the logo
            name_label = QLabel("GlobalCoyn")
            name_label.setFont(QFont('Arial', 16, QFont.Bold))
            name_label.setStyleSheet("color: #3b5998;") # Use a nice blue color
            logo_h_layout.addWidget(name_label)
            
            # Add the container to the sidebar
            sidebar_layout.addWidget(logo_container)
        
        # Create sidebar
        self.sidebar = QListWidget()
        self.sidebar.setMaximumWidth(200)
        self.sidebar.setFont(QFont('Arial', 12))
        
        # Add items to sidebar
        sidebar_items = [
            "Dashboard", "Transfer", "Wallet", 
            "Block Explorer", "Network", "Node", "Mining"
        ]
        
        for item in sidebar_items:
            list_item = QListWidgetItem(item)
            list_item.setTextAlignment(Qt.AlignLeft)
            self.sidebar.addItem(list_item)
        
        self.sidebar.currentRowChanged.connect(self.display_page)
        sidebar_layout.addWidget(self.sidebar)
        main_layout.addWidget(sidebar_container)
        
        # Create stacked widget for different pages
        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages)
        
        # Add all pages
        self.setup_dashboard_page()
        self.setup_transfer_page()
        self.setup_wallet_page()
        self.setup_explorer_page()
        self.setup_network_page()
        self.setup_node_page()
        self.setup_mining_page()
        
        # Select first page by default
        self.sidebar.setCurrentRow(0)
    
    def setup_dashboard_page(self):
        """Set up an enhanced dashboard with comprehensive information"""
        dashboard_page = QWidget()
        layout = QVBoxLayout()
        dashboard_page.setLayout(layout)
        
        # Title
        title_label = QLabel('GlobalCoyn Dashboard')
        title_label.setFont(QFont('Arial', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Network statistics section
        network_group = QGroupBox("Network Statistics")
        network_layout = QGridLayout()
        
        self.node_count_label = QLabel("Active Nodes: 0")
        self.block_height_label = QLabel("Block Height: 0")
        self.transaction_count_label = QLabel("Pending Transactions: 0")
        self.difficulty_label = QLabel("Current Difficulty: 0")
        self.last_block_label = QLabel("Last Block: Never")
        self.network_hashrate_label = QLabel("Network Hashrate: 0 H/s")
        
        # Make labels bold
        for label in [self.node_count_label, self.block_height_label, self.transaction_count_label,
                     self.difficulty_label, self.last_block_label, self.network_hashrate_label]:
            font = label.font()
            font.setBold(True)
            label.setFont(font)
        
        network_layout.addWidget(self.node_count_label, 0, 0)
        network_layout.addWidget(self.block_height_label, 0, 1)
        network_layout.addWidget(self.transaction_count_label, 1, 0)
        network_layout.addWidget(self.difficulty_label, 1, 1)
        network_layout.addWidget(self.last_block_label, 2, 0)
        network_layout.addWidget(self.network_hashrate_label, 2, 1)
        
        network_group.setLayout(network_layout)
        layout.addWidget(network_group)
        
        # Wallet balance section
        wallet_group = QGroupBox("Wallet Overview")
        wallet_layout = QVBoxLayout()
        
        # Total balance across all wallets
        self.total_balance_label = QLabel("Total Balance: 0.00 GCN")
        font = self.total_balance_label.font()
        font.setBold(True)
        font.setPointSize(14)
        self.total_balance_label.setFont(font)
        self.total_balance_label.setAlignment(Qt.AlignCenter)
        wallet_layout.addWidget(self.total_balance_label)
        
        # Recent transactions label
        recent_tx_label = QLabel("Recent Transactions")
        font = recent_tx_label.font()
        font.setBold(True)
        recent_tx_label.setFont(font)
        wallet_layout.addWidget(recent_tx_label)
        
        # Recent transactions list
        self.recent_tx_list = QTextEdit()
        self.recent_tx_list.setReadOnly(True)
        self.recent_tx_list.setMaximumHeight(100)
        wallet_layout.addWidget(self.recent_tx_list)
        
        wallet_group.setLayout(wallet_layout)
        layout.addWidget(wallet_group)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Dashboard")
        refresh_btn.clicked.connect(self.refresh_dashboard)
        layout.addWidget(refresh_btn)
        
        # Initialize dashboard data
        self.start_time = time.time()  # Track node uptime
        
        # Add to pages
        self.pages.addWidget(dashboard_page)
        
    def quick_status_check(self):
        """
        Perform a lightweight status check without fetching detailed blockchain data
        This significantly reduces API load while still keeping status information updated
        """
        if not self.node_running:
            return
            
        try:
            # Use a very lightweight HEAD request with short timeout
            # This just checks if the API is responsive without fetching data
            try:
                response = self.api_request("blockchain", method="HEAD", timeout=0.5)
                api_reachable = bool(response and response.status_code == 200)
                
                # Update any status indicators
                if hasattr(self, 'node_status_indicator'):
                    color = QColor(0, 200, 0) if api_reachable else QColor(255, 0, 0)
                    self.thread_safe_update('node_status_indicator', 'setColor', color)
                    
                # We successfully performed a status check, don't need to log anything
                return
            except Exception:
                # Connection failed, but we don't want to log this for quick checks
                # to avoid log spam - it will be logged by the full check if needed
                pass
                
        except Exception as e:
            # Only log critical errors
            self.logger.error(f"Critical error in quick status check: {str(e)}")
    
    def refresh_dashboard(self):
        """Update dashboard with latest information"""
        # Start a background thread to refresh dashboard data
        threading.Thread(target=self._refresh_dashboard_thread, daemon=True).start()
    
    def _refresh_dashboard_thread(self):
        """Background thread for dashboard updates to prevent UI freezing"""
        try:
            # Initialize wallet cache if not already done
            if self.node_running and self.wallet_cache is None:
                try:
                    # Initialize wallet cache for faster balance calculations
                    self.logger.info("Initializing wallet cache for optimized balance calculations")
                    self.wallet_cache = WalletCache(self.node_manager)
                    self.logger.info("Wallet cache initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize wallet cache: {str(e)}")
            
            # Use cached blockchain data if available to avoid redundant API calls
            if hasattr(self, 'blockchain_data') and self.blockchain_data:
                # Update UI elements with blockchain data
                chain_length = self.blockchain_data.get('chain_length', 0)
                difficulty = self.blockchain_data.get('difficulty_target', 0)
                timestamp = self.blockchain_data.get('latest_block_timestamp')
                
                # Update UI elements using thread-safe method
                self.thread_safe_update('block_height_label', 'setText', f"Block Height: {chain_length}")
                self.thread_safe_update('difficulty_label', 'setText', f"Current Difficulty: {difficulty}")
                
                # Format timestamp if available
                if timestamp:
                    formatted_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    self.thread_safe_update('last_block_label', 'setText', f"Last Block: {formatted_time}")
                    
                # Get node count
                node_count = self.blockchain_data.get('node_count', 0)
                peers_count = len(self.peers_data.get('peers', [])) if hasattr(self, 'peers_data') else 0
                active_nodes = max(node_count, peers_count + 1)  # Use higher count
                self.thread_safe_update('node_count_label', 'setText', f"Active Nodes: {active_nodes}")
            
            # Update mempool data
            try:
                if hasattr(self, 'mempool_data') and self.mempool_data:
                    pending_tx = len(self.mempool_data.get('mempool', []))
                    self.thread_safe_update('transaction_count_label', 'setText', f"Pending Transactions: {pending_tx}")
            except Exception as e:
                print(f"Error updating mempool data: {str(e)}")
            
            # Calculate hashrate with a timeout to prevent blocking
            try:
                if hasattr(self, 'chain_data') and 'chain' in self.chain_data and len(self.chain_data.get('chain', [])) > 1:
                    # Use last 10 blocks or however many are available
                    blocks = self.chain_data['chain'][-10:]
                    if len(blocks) > 1:
                        # Calculate average time between blocks
                        total_time = blocks[-1]['timestamp'] - blocks[0]['timestamp']
                        avg_time_per_block = total_time / (len(blocks) - 1) if len(blocks) > 1 else 600
                        
                        # Estimate hashrate based on difficulty and time
                        difficulty = blocks[-1].get('difficulty_target', 4)
                        estimated_hashes = (2 ** (difficulty * 4)) / avg_time_per_block if avg_time_per_block > 0 else 0
                        
                        # Format hashrate with appropriate units
                        if estimated_hashes < 1000:
                            hashrate_str = f"{estimated_hashes:.2f} H/s"
                        elif estimated_hashes < 1000000:
                            hashrate_str = f"{estimated_hashes/1000:.2f} KH/s"
                        else:
                            hashrate_str = f"{estimated_hashes/1000000:.2f} MH/s"
                        
                        # Update UI using thread-safe update
                        self.thread_safe_update('network_hashrate_label', 'setText', f"Network Hashrate: {hashrate_str}")
            except Exception as e:
                print(f"Error calculating hashrate: {str(e)}")
            
            # Update system stats in a separate thread
            threading.Thread(target=self._update_system_stats_thread, daemon=True).start()
            
            # Update wallet balance information in a separate thread
            threading.Thread(target=self._update_wallet_summary_thread, daemon=True).start()
            
        except Exception as e:
            print(f"Error refreshing dashboard: {str(e)}")
    
    def _update_system_stats_thread(self):
        """Thread for updating system stats to prevent UI freezing"""
        try:
            # Calculate uptime
            uptime_seconds = time.time() - self.start_time
            days = int(uptime_seconds // (24 * 3600))
            hours = int((uptime_seconds % (24 * 3600)) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            uptime_text = f"Uptime: {days} days, {hours} hours, {minutes} minutes"
            
            # Use thread-safe update method
            self.thread_safe_update('uptime_display', 'setText', uptime_text)
            
            # Only get system stats if psutil is available
            if HAS_PSUTIL:
                # Get CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)  # Quick sampling
                self.thread_safe_update('cpu_usage_label', 'setText', f"CPU Usage: {cpu_percent}%")
                
                # Get memory usage
                memory = psutil.virtual_memory()
                memory_used_mb = memory.used / (1024 * 1024)
                self.thread_safe_update('memory_usage_label', 'setText', f"Memory Usage: {memory_used_mb:.1f} MB")
                
                # Get disk usage for data directory
                data_dir = self.config.get('data_directory', os.path.expanduser("~/GlobalCoyn"))
                if os.path.exists(data_dir):
                    disk_usage = psutil.disk_usage(data_dir)
                    used_mb = disk_usage.used / (1024 * 1024)
                    self.thread_safe_update('disk_usage_label', 'setText', f"Disk Usage: {used_mb:.1f} MB")
            
            # Check connection quality in a non-blocking way
            try:
                start_time = time.time()
                response = requests.get(f"{self.api_base}/blockchain", timeout=1)
                response_time = time.time() - start_time
                
                if response_time < 0.1:
                    quality = "Excellent"
                    color = "green"
                elif response_time < 0.3:
                    quality = "Good"
                    color = "green"
                elif response_time < 0.7:
                    quality = "Fair"
                    color = "orange"
                else:
                    quality = "Poor"
                    color = "red"
                
                # Update connection quality and style separately using thread-safe methods
                self.thread_safe_update('connection_quality_label', 'setText', 
                                       f"Connection Quality: {quality} ({response_time:.3f}s)")
                self.thread_safe_update('connection_quality_label', 'setStyleSheet', 
                                       f"color: {color}; font-weight: bold;")
                
            except Exception:
                # Update UI to show offline status using thread-safe methods
                self.thread_safe_update('connection_quality_label', 'setText', "Connection Quality: Offline")
                self.thread_safe_update('connection_quality_label', 'setStyleSheet', "color: red; font-weight: bold;")
                
        except Exception as e:
            print(f"Error updating system stats: {str(e)}")
    
    def thread_safe_update(self, widget_name, method_name, *args):
        """
        Thread-safe way to update UI elements from non-GUI threads.
        
        Args:
            widget_name: Name of the widget attribute
            method_name: Method to call on the widget
            *args: Arguments to pass to the method
        """
        # Create a closure that will be executed in the main thread
        def update_widget():
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                if hasattr(widget, method_name):
                    method = getattr(widget, method_name)
                    method(*args)
                    
        # Schedule the update on the main thread
        QTimer.singleShot(0, update_widget)
    
    def _update_wallet_summary_thread(self):
        """Thread for updating wallet summary to prevent UI freezing"""
        try:
            # Check if wallet is loaded
            if not hasattr(self, 'wallet') or not self.wallet:
                self.thread_safe_update('total_balance_label', 'setText', "Total Balance: 0.00 GCN (No wallet loaded)")
                return
            
            # Get addresses from the wallet
            addresses = self.wallet.get_addresses()
            if not addresses:
                self.thread_safe_update('total_balance_label', 'setText', "Total Balance: 0.00 GCN (No addresses)")
                return
            
            # Check if node is running before attempting to get balances
            if not self.check_node_api_available():
                # If node is not available, use cached values or show offline message
                self.thread_safe_update('total_balance_label', 'setText', "Total Balance: (Node offline)")
                
                # Clear and update transaction list
                def update_offline_txs():
                    if hasattr(self, 'recent_tx_list'):
                        self.recent_tx_list.clear()
                        self.recent_tx_list.append("Node offline - Cannot retrieve transactions")
                
                QTimer.singleShot(0, update_offline_txs)
                return
                
            # Get balances for all addresses with a timeout to prevent hanging
            total_balance = 0
            recent_transactions = []
            
            for address in addresses:
                try:
                    response = requests.get(f"{self.api_base}/balance/{address}", timeout=0.75)
                    if response.status_code == 200:
                        data = response.json()
                        balance = float(data.get('balance', 0))
                        total_balance += balance
                        
                        # Try to get recent transactions with a short timeout
                        try:
                            tx_response = requests.get(f"{self.api_base}/transactions/{address}", timeout=0.75)
                            if tx_response.status_code == 200:
                                tx_data = tx_response.json()
                                transactions = tx_data.get('transactions', [])
                                for tx in transactions[:3]:  # Get up to 3 most recent
                                    tx_type = tx.get('transaction_type', 'TRANSFER')
                                    amount = float(tx.get('amount', 0))
                                    timestamp = datetime.fromtimestamp(tx.get('timestamp', 0)).strftime('%m-%d %H:%M')
                                    
                                    # Format transaction based on type
                                    if address == tx.get('recipient'):
                                        direction = "RECEIVED"
                                        color = "green"
                                    else:
                                        direction = "SENT"
                                        color = "red"
                                    
                                    tx_info = {
                                        'timestamp': tx.get('timestamp', 0),
                                        'display': f"[{timestamp}] {direction} {amount:.4f} GCN ({tx_type})",
                                        'color': color
                                    }
                                    recent_transactions.append(tx_info)
                        except Exception as tx_error:
                            print(f"Error getting transactions for {address}: {str(tx_error)}")
                    else:
                        print(f"Non-200 response getting balance for {address}: {response.status_code}")
                except requests.exceptions.ConnectionError:
                    # Connection errors are expected if node is not running
                    pass
                except Exception as e:
                    print(f"Unexpected error getting balance for {address}: {str(e)}")
            
            # Update total balance on main thread using thread-safe method
            final_balance = total_balance
            self.thread_safe_update('total_balance_label', 'setText', f"Total Balance: {final_balance:.8f} GCN")
            
            # Sort transactions and update the list on main thread
            if recent_transactions:
                # Sort transactions by timestamp (newest first)
                recent_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
                
                # Prepare the final list for UI update
                final_transactions = recent_transactions[:5]  # Show 5 most recent
                
                # Update UI on main thread using a dedicated method
                def update_tx_list():
                    if hasattr(self, 'recent_tx_list'):
                        self.recent_tx_list.clear()
                        for tx in final_transactions:
                            self.recent_tx_list.append(f"<span style='color:{tx['color']};'>{tx['display']}</span>")
                
                # Use single shot on main thread to handle QListWidget which can't be updated directly with our generic thread_safe_update
                QTimer.singleShot(0, update_tx_list)
            else:
                # No transactions found - update via separate function
                def update_empty_tx():
                    if hasattr(self, 'recent_tx_list'):
                        self.recent_tx_list.clear()
                        self.recent_tx_list.append("No recent transactions")
                
                # Use single shot for updating list widget which needs special handling
                QTimer.singleShot(0, update_empty_tx)
            
        except Exception as e:
            print(f"Error updating wallet summary: {str(e)}")
    
    def check_node_api_available(self):
        """Check if the node API is available for wallet operations"""
        try:
            # Fast check with short timeout
            response = requests.head(f"{self.api_base}/blockchain", timeout=0.5)
            return 200 <= response.status_code < 500
        except:
            return False
    
    def update_system_stats(self):
        """Update system resource usage statistics - legacy method, use _update_system_stats_thread for threaded updates"""
        # For backward compatibility, start the threaded version
        threading.Thread(target=self._update_system_stats_thread, daemon=True).start()
        return
        
        # The original implementation below is kept for reference but not used
        try:
            # Calculate uptime
            uptime_seconds = time.time() - self.start_time
            days = int(uptime_seconds // (24 * 3600))
            hours = int((uptime_seconds % (24 * 3600)) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            self.uptime_display.setText(f"Uptime: {days} days, {hours} hours, {minutes} minutes")
            
            # Only get system stats if psutil is available
            if HAS_PSUTIL:
                # Get CPU usage
                cpu_percent = psutil.cpu_percent()
                self.cpu_usage_label.setText(f"CPU Usage: {cpu_percent}%")
                
                # Get memory usage
                memory = psutil.virtual_memory()
                memory_used_mb = memory.used / (1024 * 1024)
                self.memory_usage_label.setText(f"Memory Usage: {memory_used_mb:.1f} MB")
                
                # Get disk usage for data directory
                data_dir = self.config.get('data_directory', os.path.expanduser("~/GlobalCoyn"))
                if os.path.exists(data_dir):
                    disk_usage = psutil.disk_usage(data_dir)
                    used_mb = disk_usage.used / (1024 * 1024)
                    self.disk_usage_label.setText(f"Disk Usage: {used_mb:.1f} MB")
            else:
                # Fallback if psutil is not available
                self.cpu_usage_label.setText("CPU Usage: Not available")
                self.memory_usage_label.setText("Memory Usage: Not available")
                self.disk_usage_label.setText("Disk Usage: Not available")
            
            # Check connection quality
            try:
                start_time = time.time()
                requests.get(f"{self.api_base}/blockchain", timeout=1)
                response_time = time.time() - start_time
                
                if response_time < 0.1:
                    quality = "Excellent"
                    color = "green"
                elif response_time < 0.3:
                    quality = "Good"
                    color = "green"
                elif response_time < 0.7:
                    quality = "Fair"
                    color = "orange"
                else:
                    quality = "Poor"
                    color = "red"
                    
                self.connection_quality_label.setText(f"Connection Quality: {quality} ({response_time:.3f}s)")
                self.connection_quality_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            except:
                self.connection_quality_label.setText("Connection Quality: Offline")
                self.connection_quality_label.setStyleSheet("color: red; font-weight: bold;")
                
        except Exception as e:
            print(f"Error updating system stats: {str(e)}")
    
    def update_wallet_summary(self):
        """Update wallet balance summary and recent transactions - legacy method, use _update_wallet_summary_thread for threaded updates"""
        # For backward compatibility, start the threaded version
        threading.Thread(target=self._update_wallet_summary_thread, daemon=True).start()
        return
        
        # The original implementation below is kept for reference but not used
        try:
            # Check if wallet is loaded
            if not hasattr(self, 'wallet') or not self.wallet:
                self.total_balance_label.setText("Total Balance: 0.00 GCN (No wallet loaded)")
                return
            
            # Get addresses from the wallet
            addresses = self.wallet.get_addresses()
            if not addresses:
                self.total_balance_label.setText("Total Balance: 0.00 GCN (No addresses)")
                return
            
            # Get balances for all addresses
            total_balance = 0
            recent_transactions = []
            
            for address in addresses:
                try:
                    response = requests.get(f"{self.api_base}/balance/{address}", timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        balance = float(data.get('balance', 0))
                        total_balance += balance
                        
                        # Get recent transactions for this address
                        tx_response = requests.get(f"{self.api_base}/transactions/{address}", timeout=2)
                        if tx_response.status_code == 200:
                            tx_data = tx_response.json()
                            transactions = tx_data.get('transactions', [])
                            for tx in transactions[:3]:  # Get up to 3 most recent
                                tx_type = tx.get('transaction_type', 'TRANSFER')
                                amount = float(tx.get('amount', 0))
                                timestamp = datetime.fromtimestamp(tx.get('timestamp', 0)).strftime('%m-%d %H:%M')
                                
                                # Format transaction based on type
                                if address == tx.get('recipient'):
                                    direction = "RECEIVED"
                                    color = "green"
                                else:
                                    direction = "SENT"
                                    color = "red"
                                
                                tx_info = {
                                    'timestamp': tx.get('timestamp', 0),
                                    'display': f"[{timestamp}] {direction} {amount:.4f} GCN ({tx_type})",
                                    'color': color
                                }
                                recent_transactions.append(tx_info)
                except Exception as e:
                    print(f"Error getting balance for {address}: {str(e)}")
            
            # Update total balance
            self.total_balance_label.setText(f"Total Balance: {total_balance:.8f} GCN")
            
            # Sort transactions by timestamp (newest first) and update the list
            recent_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
            self.recent_tx_list.clear()
            
            for tx in recent_transactions[:5]:  # Show 5 most recent
                self.recent_tx_list.append(f"<span style='color:{tx['color']};'>{tx['display']}</span>")
            
            if not recent_transactions:
                self.recent_tx_list.append("No recent transactions")
            
        except Exception as e:
            print(f"Error updating wallet summary: {str(e)}")
    
    def setup_transfer_page(self):
        transfer_page = QWidget()
        layout = QVBoxLayout()
        transfer_page.setLayout(layout)
        
        title_label = QLabel('Transfer GCN')
        title_label.setFont(QFont('Arial', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Account selection
        account_group = QGroupBox('From Account')
        account_layout = QVBoxLayout()
        account_group.setLayout(account_layout)
        
        # Address selection
        address_layout = QHBoxLayout()
        address_layout.addWidget(QLabel('From Address:'))
        
        self.sender_address_combo = QComboBox()
        self.sender_address_combo.setFont(QFont('Monospace', 10))
        self.sender_address_combo.currentIndexChanged.connect(self.update_sender_balance)
        address_layout.addWidget(self.sender_address_combo)
        
        account_layout.addLayout(address_layout)
        
        # Balance display
        balance_layout = QHBoxLayout()
        balance_layout.addWidget(QLabel('Available Balance:'))
        
        self.transfer_balance_label = QLabel('0.00 GCN')
        self.transfer_balance_label.setFont(QFont('Arial', 14, QFont.Bold))
        balance_layout.addWidget(self.transfer_balance_label)
        
        # Refresh button
        refresh_balance_btn = QPushButton('Refresh')
        refresh_balance_btn.clicked.connect(self.update_sender_balance)
        balance_layout.addWidget(refresh_balance_btn)
        
        account_layout.addLayout(balance_layout)
        layout.addWidget(account_group)
        
        # Transfer details
        transfer_group = QGroupBox('Transfer Details')
        transfer_layout = QVBoxLayout()
        transfer_group.setLayout(transfer_layout)
        
        # Recipient address
        recipient_layout = QHBoxLayout()
        recipient_layout.addWidget(QLabel('To Address:'))
        
        self.recipient_address_input = QLineEdit()
        self.recipient_address_input.setPlaceholderText('Enter recipient wallet address')
        recipient_layout.addWidget(self.recipient_address_input)
        
        # Paste button
        paste_btn = QPushButton('Paste')
        paste_btn.clicked.connect(self.paste_recipient_address)
        recipient_layout.addWidget(paste_btn)
        
        transfer_layout.addLayout(recipient_layout)
        
        # Amount
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel('Amount:'))
        
        self.transfer_amount_input = QLineEdit()
        self.transfer_amount_input.setPlaceholderText('Enter amount to send')
        self.transfer_amount_input.setValidator(QDoubleValidator(0, 1000000, 8))
        amount_layout.addWidget(self.transfer_amount_input)
        
        amount_layout.addWidget(QLabel('GCN'))
        
        transfer_layout.addLayout(amount_layout)
        
        # Fee
        fee_layout = QHBoxLayout()
        fee_layout.addWidget(QLabel('Transaction Fee:'))
        
        self.fee_input = QLineEdit('0.001')
        self.fee_input.setValidator(QDoubleValidator(0, 1, 8))
        fee_layout.addWidget(self.fee_input)
        
        fee_layout.addWidget(QLabel('GCN'))
        
        transfer_layout.addLayout(fee_layout)
        
        # Total
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel('Total Amount (with fee):'))
        
        self.total_amount_label = QLabel('0.000 GCN')
        self.total_amount_label.setFont(QFont('Arial', 12, QFont.Bold))
        total_layout.addWidget(self.total_amount_label)
        
        transfer_layout.addLayout(total_layout)
        
        # Connect amount and fee inputs to update total
        self.transfer_amount_input.textChanged.connect(self.update_total_amount)
        self.fee_input.textChanged.connect(self.update_total_amount)
        
        layout.addWidget(transfer_group)
        
        # Send button
        send_btn = QPushButton('Send Transaction')
        send_btn.setMinimumHeight(40)
        send_btn.setFont(QFont('Arial', 12, QFont.Bold))
        send_btn.clicked.connect(self.send_transaction)
        layout.addWidget(send_btn)
        
        # Status message
        self.transfer_status = QLabel('Ready to send')
        self.transfer_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.transfer_status)
        
        # Transaction log
        log_group = QGroupBox("Transaction Log")
        log_layout = QVBoxLayout()
        
        self.transfer_log = QTextEdit()
        self.transfer_log.setReadOnly(True)
        self.transfer_log.setMinimumHeight(150)
        self.transfer_log.setFont(QFont('Monospace', 10))
        log_layout.addWidget(self.transfer_log)
        
        # Add an initial message
        self.transfer_log.append("[System] Transaction log initialized - ready to send transactions")
        
        # Add clear log button
        clear_log_btn = QPushButton('Clear Log')
        clear_log_btn.clicked.connect(lambda: self.transfer_log.clear())
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        self.pages.addWidget(transfer_page)
    
    def update_total_amount(self):
        """Update the total amount display including fee"""
        try:
            amount = float(self.transfer_amount_input.text() or 0)
            fee = float(self.fee_input.text() or 0)
            total = amount + fee
            self.total_amount_label.setText(f"{total:.8f} GCN")
            
            # Check if total exceeds balance
            try:
                balance = float(self.transfer_balance_label.text().replace(' GCN', ''))
                if total > balance:
                    self.total_amount_label.setStyleSheet("color: red")
                else:
                    self.total_amount_label.setStyleSheet("color: black")
            except:
                pass
        except ValueError:
            self.total_amount_label.setText("Invalid input")
    
    def update_transfer_addresses(self):
        """Update the sender address dropdown with available wallet addresses"""
        if not hasattr(self, 'wallet') or not self.wallet:
            try:
                # Update Python path to include GlobalCoyn directory
                sys.path.append(os.path.expanduser("~/GlobalCoyn"))
                
                # Try to load wallet if it exists
                try:
                    from core.wallet import Wallet
                except ImportError:
                    # If that fails, try to copy wallet.py if needed
                    wallet_src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core", "wallet.py")
                    wallet_dest_dir = os.path.join(os.path.expanduser("~/GlobalCoyn"), "core")
                    
                    if os.path.exists(wallet_src) and os.path.exists(wallet_dest_dir):
                        import shutil
                        shutil.copy(wallet_src, os.path.join(wallet_dest_dir, "wallet.py"))
                        self.transfer_status.setText("Copied wallet module - retrying import")
                        
                    # Second attempt after copying
                    from core.wallet import Wallet
                
                wallet_dir = os.path.join(os.path.expanduser("~/GlobalCoyn"), "wallet")
                os.makedirs(wallet_dir, exist_ok=True)
                wallet_path = os.path.join(wallet_dir, "wallet.enc")
                
                if os.path.exists(wallet_path):
                    self.wallet = Wallet(encrypted_storage_path=wallet_path)
                    if not self.wallet.load_from_file():
                        return
                else:
                    return
            except Exception as e:
                self.transfer_status.setText(f"Error loading wallet: {str(e)}")
                self.transfer_status.setStyleSheet("color: red")
                return
        
        # Save current selection
        current_selection = self.sender_address_combo.currentText()
        
        # Update address dropdown
        self.sender_address_combo.clear()
        addresses = self.wallet.get_addresses()
        
        if not addresses:
            self.transfer_status.setText("No wallet addresses available. Create or import a wallet first.")
            self.transfer_status.setStyleSheet("color: red")
            return
        
        for address in addresses:
            self.sender_address_combo.addItem(address)
        
        # Restore previous selection if it exists
        if current_selection in addresses:
            index = self.sender_address_combo.findText(current_selection)
            self.sender_address_combo.setCurrentIndex(index)
        
        self.update_sender_balance()
    
    def update_sender_balance(self):
        """Update the balance display for the selected sender address"""
        sender_address = self.sender_address_combo.currentText()
        
        if not sender_address or not self.node_running:
            self.transfer_balance_label.setText("0.00 GCN")
            return
        
        try:
            # Use optimized wallet balance with caching
            balance = self.get_wallet_balance(sender_address)
            
            # Get current displayed balance
            old_balance_text = self.transfer_balance_label.text()
            old_balance = 0
            try:
                old_balance = float(old_balance_text.replace(' GCN', ''))
            except:
                pass
            
            # Update balance label
            self.transfer_balance_label.setText(f"{balance:.8f} GCN")
            
            # Log success but only if balance changed
            if abs(balance - old_balance) > 0.00000001:
                self.logger.debug(f"Updated sender balance: {balance:.8f} GCN")
                
                # Update total amount to check if it exceeds balance
                self.update_total_amount()
                
                # Update status
                self.transfer_status.setText("Balance updated")
                self.transfer_status.setStyleSheet("color: green")
                
                # Log balance update if it changed
                if hasattr(self, 'transfer_log') and abs(balance - old_balance) > 0.00001:
                    change = balance - old_balance
                    if change > 0:
                        self.add_transfer_log(f"💰 Balance increased by {change:.8f} GCN")
                    else:
                        self.add_transfer_log(f"💸 Balance decreased by {abs(change):.8f} GCN")
                    self.add_transfer_log(f"Current balance: {balance:.8f} GCN")
                    
            else:
                self.transfer_status.setText(f"Error getting balance: {response.status_code}")
                self.transfer_status.setStyleSheet("color: red")
                if hasattr(self, 'transfer_log'):
                    self.add_transfer_log(f"⚠️ Error getting balance: {response.status_code}")
        except Exception as e:
            self.transfer_status.setText(f"Error getting balance: {str(e)}")
            self.transfer_status.setStyleSheet("color: red")
            if hasattr(self, 'transfer_log'):
                self.add_transfer_log(f"⚠️ Error getting balance: {str(e)}")
    
    def paste_recipient_address(self):
        """Paste address from clipboard"""
        clipboard = QApplication.clipboard()
        self.recipient_address_input.setText(clipboard.text())
    
    def transaction_worker(self, sender_address, tx_data):
        """Background worker to process transaction and mine block"""
        try:
            # Get original transaction amount for accurate accounting
            original_amount = float(tx_data.get('amount', 0))
            original_fee = float(tx_data.get('fee', 0))
            recipient_address = tx_data.get('recipient', '')
            
            # First, submit the transaction to the mempool
            self.add_transfer_log(f"Sending transaction from {sender_address} to {recipient_address}")
            self.add_transfer_log(f"Amount: {original_amount} GCN, Fee: {original_fee} GCN")
            
            response = requests.post(
                f"{self.api_base}/transaction", 
                json=tx_data,
                timeout=10
            )
            
            if response.status_code == 201:
                # Transaction was accepted into the mempool
                self.add_transfer_log(f"Transaction accepted into mempool successfully!")
                
                # Mine a block to confirm the transaction
                self.add_transfer_log(f"Mining a block to confirm the transaction...")
                
                # Get a snapshot of the balance before mining
                pre_mining_balance = 0
                try:
                    balance_response = requests.get(f"{self.api_base}/balance/{sender_address}", timeout=5)
                    if balance_response.status_code == 200:
                        pre_mining_balance = float(balance_response.json().get('balance', 0))
                        self.add_transfer_log(f"Balance before mining: {pre_mining_balance} GCN")
                except Exception as be:
                    self.add_transfer_log(f"⚠️ Could not retrieve pre-mining balance: {str(be)}")
                
                # Use the recipient address as the miner if it's a different address
                # This prevents the "50 GCN less" issue by not having the sender get mining rewards
                if sender_address != recipient_address:
                    # For regular transfers to other users, use recipient as miner
                    mining_data = {"miner_address": recipient_address}
                    self.add_transfer_log(f"Using recipient address as miner to avoid balance discrepancy")
                else:
                    # If sending to yourself (circular transfer), use sender as miner
                    mining_data = {"miner_address": sender_address}
                    self.add_transfer_log(f"Self-transfer detected, using sender as miner")
                
                mining_response = requests.post(
                    f"{self.api_base}/mine",
                    json=mining_data,
                    timeout=30  # Mining might take longer
                )
                
                if mining_response.status_code == 200:
                    mining_result = mining_response.json()
                    if mining_result.get('status') == 'success':
                        # Extract mining reward info from the response if available
                        mining_reward = 50.0  # Default if not provided in response
                        
                        # Block was mined successfully
                        block_data = mining_result.get('block', {})
                        block_index = block_data.get('index', 'unknown')
                        self.add_transfer_log(f"✅ Block #{block_index} mined successfully!")
                        
                        # Check for coinbase transaction (mining reward)
                        transactions = block_data.get('transactions', [])
                        for tx in transactions:
                            if tx.get('sender') == '0':  # Coinbase/mining reward
                                mining_reward = float(tx.get('amount', 50.0))
                                mining_recipient = tx.get('recipient')
                                self.add_transfer_log(f"💰 Mining reward of {mining_reward} GCN sent to {mining_recipient}")
                        
                        # Wait briefly for the blockchain to update
                        time.sleep(1)
                        
                        # Check updated balance
                        balance_response = requests.get(f"{self.api_base}/balance/{sender_address}", timeout=5)
                        if balance_response.status_code == 200:
                            new_balance = float(balance_response.json().get('balance', 0))
                            self.add_transfer_log(f"Updated sender wallet balance: {new_balance} GCN")
                            
                            # Calculate expected balance change for clarity
                            if sender_address == recipient_address:
                                # Self-transfer: should only lose the fee but gain mining reward
                                expected_balance = pre_mining_balance - original_fee + mining_reward
                                self.add_transfer_log(f"Expected balance: {expected_balance} GCN (Original - Fee + Mining Reward)")
                            else:
                                # Regular transfer to another address: lose amount + fee
                                expected_balance = pre_mining_balance - original_amount - original_fee
                                self.add_transfer_log(f"Expected balance: {expected_balance} GCN (Original - Amount - Fee)")
                                
                                # Also check recipient balance if different address
                                try:
                                    recipient_response = requests.get(f"{self.api_base}/balance/{recipient_address}", timeout=5)
                                    if recipient_response.status_code == 200:
                                        recipient_balance = float(recipient_response.json().get('balance', 0))
                                        self.add_transfer_log(f"Recipient balance: {recipient_balance} GCN (includes received amount + mining reward)")
                                except:
                                    self.add_transfer_log(f"⚠️ Could not retrieve recipient balance")
                            
                            # Update balance in UI thread
                            QTimer.singleShot(0, lambda: self.update_sender_balance())
                            QTimer.singleShot(0, lambda: self.transfer_status.setText("Transaction completed and confirmed!"))
                            QTimer.singleShot(0, lambda: self.transfer_status.setStyleSheet("color: green"))
                        else:
                            self.add_transfer_log(f"⚠️ Could not retrieve updated balance")
                    else:
                        self.add_transfer_log(f"⚠️ Block mining failed: {mining_result.get('message', 'Unknown error')}")
                        QTimer.singleShot(0, lambda: self.transfer_status.setText("Transaction sent but not yet confirmed"))
                        QTimer.singleShot(0, lambda: self.transfer_status.setStyleSheet("color: orange"))
                else:
                    self.add_transfer_log(f"⚠️ Block mining failed: Status code {mining_response.status_code}")
                    QTimer.singleShot(0, lambda: self.transfer_status.setText("Transaction sent but not yet confirmed"))
                    QTimer.singleShot(0, lambda: self.transfer_status.setStyleSheet("color: orange"))
            else:
                try:
                    error_msg = response.json().get('error', 'Unknown error')
                    self.add_transfer_log(f"❌ Transaction failed: {error_msg}")
                    QTimer.singleShot(0, lambda: self.transfer_status.setText(f"Error: {error_msg}"))
                    QTimer.singleShot(0, lambda: self.transfer_status.setStyleSheet("color: red"))
                except:
                    self.add_transfer_log(f"❌ Transaction failed: Status code {response.status_code}")
                    QTimer.singleShot(0, lambda: self.transfer_status.setText(f"Error: Status code {response.status_code}"))
                    QTimer.singleShot(0, lambda: self.transfer_status.setStyleSheet("color: red"))
        
        except Exception as e:
            self.add_transfer_log(f"❌ Error in transaction worker: {str(e)}")
            QTimer.singleShot(0, lambda: self.transfer_status.setText(f"Error: {str(e)}"))
            QTimer.singleShot(0, lambda: self.transfer_status.setStyleSheet("color: red"))
    
    def add_transfer_log(self, message):
        """Add message to transfer log (safely across threads)"""
        timestamp = time.strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        
        # Use QTimer to safely update UI from any thread
        QTimer.singleShot(0, lambda msg=log_message: self._update_transfer_log(msg))
    
    def _update_transfer_log(self, message):
        """Update transfer log in UI thread"""
        if hasattr(self, 'transfer_log'):
            self.transfer_log.append(message)
            # Auto-scroll to bottom
            scrollbar = self.transfer_log.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def send_transaction(self):
        """Create and send a transaction"""
        if not self.node_running:
            QMessageBox.warning(self, "Node Not Running", "Your node must be running to send transactions.")
            return
        
        # Validate inputs
        sender_address = self.sender_address_combo.currentText()
        recipient_address = self.recipient_address_input.text().strip()
        
        try:
            amount = float(self.transfer_amount_input.text())
            fee = float(self.fee_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numeric values for amount and fee.")
            return
        
        # Check if wallet is loaded
        if not hasattr(self, 'wallet') or not self.wallet:
            QMessageBox.warning(self, "No Wallet", "Please create or import a wallet first.")
            return
        
        # Validate recipient address
        if not recipient_address or len(recipient_address) < 26:
            QMessageBox.warning(self, "Invalid Address", "Please enter a valid recipient address.")
            return
        
        # Validate amount
        if amount <= 0:
            QMessageBox.warning(self, "Invalid Amount", "Amount must be greater than zero.")
            return
        
        # Validate fee
        if fee <= 0:
            QMessageBox.warning(self, "Invalid Fee", "Fee must be greater than zero.")
            return
        
        # Check balance
        try:
            response = requests.get(f"{self.api_base}/balance/{sender_address}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                balance = data.get('balance', 0)
                
                if balance < (amount + fee):
                    QMessageBox.warning(
                        self, "Insufficient Balance", 
                        f"Your balance ({balance:.8f} GCN) is insufficient to send this transaction with fee ({amount + fee:.8f} GCN)."
                    )
                    return
            else:
                QMessageBox.warning(self, "Balance Error", "Could not verify balance. Please try again.")
                return
        except Exception as e:
            QMessageBox.warning(self, "Balance Error", f"Error checking balance: {str(e)}")
            return
        
        # Ask for confirmation
        confirm = QMessageBox.question(
            self, "Confirm Transaction", 
            f"Send {amount:.8f} GCN to {recipient_address}?\n"
            f"Fee: {fee:.8f} GCN\n"
            f"Total: {amount + fee:.8f} GCN",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
        
        try:
            # Add a separator line in the transaction log
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            self.add_transfer_log("---------------------------------------------")
            self.add_transfer_log(f"New transaction initiated at {timestamp}")
            self.add_transfer_log(f"From: {sender_address}")
            self.add_transfer_log(f"To: {recipient_address}")
            self.add_transfer_log(f"Amount: {amount:.8f} GCN")
            self.add_transfer_log(f"Fee: {fee:.8f} GCN")
            self.add_transfer_log("---------------------------------------------")
            
            # Sign the transaction with the wallet
            self.transfer_status.setText("Signing transaction...")
            self.transfer_status.setStyleSheet("color: blue")
            QApplication.processEvents()  # Update UI
            
            self.add_transfer_log("Signing transaction with wallet...")
            
            transaction = self.wallet.sign_transaction(
                sender_address=sender_address,
                recipient_address=recipient_address,
                amount=amount,
                fee=fee
            )
            
            if not transaction:
                self.add_transfer_log("❌ Failed to sign transaction!")
                QMessageBox.critical(self, "Signing Error", "Failed to sign transaction. Please check your wallet.")
                return
            
            self.add_transfer_log("✅ Transaction signed successfully")
            
            # Submit the transaction to the node
            self.transfer_status.setText("Submitting transaction and mining block...")
            self.transfer_status.setStyleSheet("color: blue")
            QApplication.processEvents()  # Update UI
            
            # Convert transaction to dictionary for API
            tx_data = {
                "sender": transaction.sender,
                "recipient": transaction.recipient,
                "amount": transaction.amount,
                "fee": transaction.fee,
                "signature": transaction.signature,
                "transaction_type": "TRANSFER"
            }
            
            # Start a worker thread to handle the transaction and mining
            tx_thread = threading.Thread(
                target=self.transaction_worker,
                args=(sender_address, tx_data),
                daemon=True
            )
            tx_thread.start()
            
            # Show initial message to user
            QMessageBox.information(
                self, "Transaction Processing", 
                f"Transaction is being processed!\n"
                f"Amount: {amount:.8f} GCN\n"
                f"Recipient: {recipient_address}\n\n"
                f"The transaction will be mined into a block to confirm it.\n"
                f"Please wait while processing completes."
            )
            
            # Clear inputs
            self.recipient_address_input.clear()
            self.transfer_amount_input.clear()
        
        except Exception as e:
            self.add_transfer_log(f"❌ Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Transaction error: {str(e)}")
            self.transfer_status.setText(f"Error: {str(e)}")
            self.transfer_status.setStyleSheet("color: red")
    
    def setup_wallet_page(self):
        wallet_page = QWidget()
        layout = QVBoxLayout()
        wallet_page.setLayout(layout)
        
        title_label = QLabel('GlobalCoyn Wallet')
        title_label.setFont(QFont('Arial', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Wallet object (initialized when needed)
        self.wallet = None
        self.selected_address = None
        
        # Wallet controls
        control_layout = QHBoxLayout()
        
        # Create Wallet button
        create_wallet_btn = QPushButton('Create New Wallet')
        create_wallet_btn.clicked.connect(self.create_new_wallet)
        control_layout.addWidget(create_wallet_btn)
        
        # Import Wallet button
        import_wallet_btn = QPushButton('Import Wallet')
        import_wallet_btn.clicked.connect(self.import_wallet)
        control_layout.addWidget(import_wallet_btn)
        
        # Backup Wallet button
        backup_wallet_btn = QPushButton('Backup Wallet')
        backup_wallet_btn.clicked.connect(self.backup_wallet)
        control_layout.addWidget(backup_wallet_btn)
        
        layout.addLayout(control_layout)
        
        # Address container
        address_group = QGroupBox('Your Addresses')
        address_layout = QVBoxLayout()
        address_group.setLayout(address_layout)
        
        # Address list
        self.address_list = QListWidget()
        self.address_list.setFont(QFont('Monospace', 10))
        self.address_list.setSelectionMode(QListWidget.SingleSelection)
        self.address_list.itemClicked.connect(self.select_address)
        address_layout.addWidget(self.address_list)
        
        # Address controls
        address_controls = QHBoxLayout()
        
        # Create new address button
        new_address_btn = QPushButton('Create New Address')
        new_address_btn.clicked.connect(self.create_new_address)
        address_controls.addWidget(new_address_btn)
        
        # Copy address button
        copy_address_btn = QPushButton('Copy Address')
        copy_address_btn.clicked.connect(self.copy_selected_address)
        address_controls.addWidget(copy_address_btn)
        
        address_layout.addLayout(address_controls)
        layout.addWidget(address_group)
        
        # Wallet details
        details_group = QGroupBox('Wallet Details')
        details_layout = QVBoxLayout()
        details_group.setLayout(details_layout)
        
        # Balance display
        balance_layout = QHBoxLayout()
        balance_layout.addWidget(QLabel('Balance:'))
        
        self.balance_label = QLabel('0.00 GCN')
        self.balance_label.setFont(QFont('Arial', 16, QFont.Bold))
        balance_layout.addWidget(self.balance_label)
        
        # Refresh button
        refresh_btn = QPushButton('Refresh')
        refresh_btn.clicked.connect(self.refresh_wallet_data)
        balance_layout.addWidget(refresh_btn)
        
        details_layout.addLayout(balance_layout)
        
        # Transaction history label
        history_label = QLabel('Transaction History:')
        details_layout.addWidget(history_label)
        
        # Transaction history table
        self.transaction_list = QTextEdit()
        self.transaction_list.setReadOnly(True)
        self.transaction_list.setFont(QFont('Monospace', 10))
        details_layout.addWidget(self.transaction_list)
        
        layout.addWidget(details_group)
        
        # Status message area
        self.wallet_status = QLabel('Wallet not loaded')
        self.wallet_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.wallet_status)
        
        self.pages.addWidget(wallet_page)
        
    def create_new_wallet(self):
        """Create a new wallet"""
        try:
            # Update Python path to include GlobalCoyn directory
            sys.path.append(os.path.expanduser("~/GlobalCoyn"))
            
            # Import the Wallet class - use direct import
            try:
                from core.wallet import Wallet
            except ImportError:
                # If that fails, try to copy wallet.py if needed
                wallet_src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core", "wallet.py")
                wallet_dest_dir = os.path.join(os.path.expanduser("~/GlobalCoyn"), "core")
                
                if os.path.exists(wallet_src) and os.path.exists(wallet_dest_dir):
                    import shutil
                    shutil.copy(wallet_src, os.path.join(wallet_dest_dir, "wallet.py"))
                    self.wallet_status.setText("Copied wallet module - retrying import")
                    
                # Second attempt after copying
                from core.wallet import Wallet
            
            # Initialize wallet
            wallet_dir = os.path.join(os.path.expanduser("~/GlobalCoyn"), "wallet")
            os.makedirs(wallet_dir, exist_ok=True)
            wallet_path = os.path.join(wallet_dir, "wallet.enc")
            
            self.wallet = Wallet(encrypted_storage_path=wallet_path)
            
            # Generate a new address
            new_address = self.wallet.create_new_address()
            self.selected_address = new_address
            
            # Generate a seed phrase (recovery phrase)
            seed_phrase = self.wallet.generate_seed_phrase()
            
            # Save the wallet
            self.wallet.save_to_file()
            
            # Show the seed phrase to the user
            seed_dialog = QMessageBox(self)
            seed_dialog.setWindowTitle("Wallet Created")
            seed_dialog.setText("Your new wallet has been created!")
            seed_dialog.setInformativeText(
                f"Your wallet address:\n{new_address}\n\n"
                f"IMPORTANT: Please write down your recovery seed phrase and keep it safe.\n"
                f"This is the ONLY way to recover your wallet if you lose access:\n\n"
                f"{seed_phrase}\n\n"
                f"Never share this seed phrase with anyone!"
            )
            seed_dialog.setIcon(QMessageBox.Information)
            seed_dialog.exec_()
            
            # Update the UI
            self.refresh_wallet_data()
            self.wallet_status.setText(f"Wallet created successfully")
            self.wallet_status.setStyleSheet("color: green")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create wallet: {str(e)}")
            self.wallet_status.setText(f"Error: {str(e)}")
            self.wallet_status.setStyleSheet("color: red")
    
    def import_wallet(self):
        """Import a wallet from seed phrase or private key"""
        try:
            # Update Python path to include GlobalCoyn directory
            sys.path.append(os.path.expanduser("~/GlobalCoyn"))
            
            # Check if wallet is already loaded
            if not self.wallet:
                # Import the Wallet class - use direct import
                try:
                    from core.wallet import Wallet
                except ImportError:
                    # If that fails, try to copy wallet.py if needed
                    wallet_src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core", "wallet.py")
                    wallet_dest_dir = os.path.join(os.path.expanduser("~/GlobalCoyn"), "core")
                    
                    if os.path.exists(wallet_src) and os.path.exists(wallet_dest_dir):
                        import shutil
                        shutil.copy(wallet_src, os.path.join(wallet_dest_dir, "wallet.py"))
                        self.wallet_status.setText("Copied wallet module - retrying import")
                        
                    # Second attempt after copying
                    from core.wallet import Wallet
                
                # Initialize wallet
                wallet_dir = os.path.join(os.path.expanduser("~/GlobalCoyn"), "wallet")
                os.makedirs(wallet_dir, exist_ok=True)
                wallet_path = os.path.join(wallet_dir, "wallet.enc")
                
                self.wallet = Wallet(encrypted_storage_path=wallet_path)
                
                # Try to load existing wallet
                if self.wallet.load_from_file():
                    self.refresh_wallet_data()
                    self.wallet_status.setText("Wallet loaded from file")
                    self.wallet_status.setStyleSheet("color: green")
                    return
            
            # Ask user for import method
            import_dialog = QMessageBox(self)
            import_dialog.setWindowTitle("Import Wallet")
            import_dialog.setText("How would you like to import your wallet?")
            import_dialog.setIcon(QMessageBox.Question)
            
            seed_btn = import_dialog.addButton("Seed Phrase", QMessageBox.ActionRole)
            key_btn = import_dialog.addButton("Private Key", QMessageBox.ActionRole)
            cancel_btn = import_dialog.addButton("Cancel", QMessageBox.RejectRole)
            
            import_dialog.exec_()
            
            if import_dialog.clickedButton() == seed_btn:
                # Import from seed phrase
                seed_phrase, ok = QInputDialog.getText(
                    self, "Import Wallet", "Enter your 12-word seed phrase:", 
                    QLineEdit.Normal
                )
                
                if ok and seed_phrase:
                    new_address = self.wallet.create_from_seed_phrase(seed_phrase)
                    self.selected_address = new_address
                    self.wallet.save_to_file()
                    self.refresh_wallet_data()
                    
                    QMessageBox.information(
                        self, "Wallet Imported", 
                        f"Wallet successfully imported!\nYour address: {new_address}"
                    )
                    
                    self.wallet_status.setText("Wallet imported successfully")
                    self.wallet_status.setStyleSheet("color: green")
            
            elif import_dialog.clickedButton() == key_btn:
                # Import from private key
                private_key, ok = QInputDialog.getText(
                    self, "Import Wallet", "Enter your private key (WIF format):", 
                    QLineEdit.Normal
                )
                
                if ok and private_key:
                    new_address = self.wallet.import_private_key(private_key)
                    
                    if new_address:
                        self.selected_address = new_address
                        self.wallet.save_to_file()
                        self.refresh_wallet_data()
                        
                        QMessageBox.information(
                            self, "Wallet Imported", 
                            f"Wallet successfully imported!\nYour address: {new_address}"
                        )
                        
                        self.wallet_status.setText("Wallet imported successfully")
                        self.wallet_status.setStyleSheet("color: green")
                    else:
                        QMessageBox.critical(
                            self, "Import Failed", 
                            "Invalid private key format. Please check and try again."
                        )
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import wallet: {str(e)}")
            self.wallet_status.setText(f"Error: {str(e)}")
            self.wallet_status.setStyleSheet("color: red")
    
    def backup_wallet(self):
        """Backup wallet by exporting private key or seed phrase"""
        if not self.wallet or not self.selected_address:
            QMessageBox.warning(self, "No Wallet", "Please create or import a wallet first.")
            return
            
        try:
            # Get private key for selected address
            private_key = self.wallet.export_private_key(self.selected_address)
            
            if private_key:
                # Show private key to user
                backup_dialog = QMessageBox(self)
                backup_dialog.setWindowTitle("Wallet Backup")
                backup_dialog.setText("Your Private Key (Keep it safe!)")
                backup_dialog.setInformativeText(
                    f"Address: {self.selected_address}\n\n"
                    f"Private Key (WIF format):\n{private_key}\n\n"
                    f"IMPORTANT: Never share your private key with anyone!\n"
                    f"Keep this information in a secure location."
                )
                backup_dialog.setIcon(QMessageBox.Warning)
                backup_dialog.exec_()
                
                self.wallet_status.setText("Private key exported successfully")
            else:
                QMessageBox.warning(
                    self, "Backup Failed", 
                    "Could not export private key for the selected address."
                )
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to backup wallet: {str(e)}")
            self.wallet_status.setText(f"Error: {str(e)}")
            self.wallet_status.setStyleSheet("color: red")
    
    def create_new_address(self):
        """Create a new address in the existing wallet"""
        if not self.wallet:
            QMessageBox.warning(self, "No Wallet", "Please create or import a wallet first.")
            return
            
        try:
            # Generate a new address
            new_address = self.wallet.create_new_address()
            self.selected_address = new_address
            
            # Save the wallet
            self.wallet.save_to_file()
            
            # Update UI
            self.refresh_wallet_data()
            
            # Show the new address to the user
            QMessageBox.information(
                self, "New Address Created", 
                f"Your new address:\n{new_address}"
            )
            
            self.wallet_status.setText("New address created successfully")
            self.wallet_status.setStyleSheet("color: green")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create new address: {str(e)}")
            self.wallet_status.setText(f"Error: {str(e)}")
            self.wallet_status.setStyleSheet("color: red")
    
    def select_address(self, item):
        """Select an address from the list"""
        if not self.wallet:
            return
            
        self.selected_address = item.text()
        self.refresh_wallet_data()
        self.wallet_status.setText(f"Selected address: {self.selected_address}")
    
    def copy_selected_address(self):
        """Copy the selected address to clipboard"""
        if not self.selected_address:
            QMessageBox.warning(self, "No Address", "Please select an address first.")
            return
            
        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(self.selected_address)
        
        self.wallet_status.setText("Address copied to clipboard")
        self.wallet_status.setStyleSheet("color: green")
    
    def refresh_wallet_data(self):
        """Refresh wallet data display"""
        if not self.wallet:
            try:
                # Update Python path to include GlobalCoyn directory
                gcn_dir = os.path.expanduser("~/GlobalCoyn")
                sys.path.append(gcn_dir)
                
                # Ensure the core directory exists
                core_dir = os.path.join(gcn_dir, "core")
                os.makedirs(core_dir, exist_ok=True)
                
                # Create __init__.py if it doesn't exist to make core a proper module
                init_path = os.path.join(core_dir, "__init__.py")
                if not os.path.exists(init_path):
                    with open(init_path, 'w') as f:
                        f.write("# Core module initialization\n")
                
                # Try to load wallet module
                try:
                    # First try to import from current directory structure
                    from core.wallet import Wallet
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Successfully imported Wallet from core module")
                except ImportError as e:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error importing Wallet: {str(e)}")
                    
                    # Try to find the wallet module in our app directory structure
                    wallet_src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core", "wallet.py")
                    
                    if os.path.exists(wallet_src):
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Found wallet.py at {wallet_src}")
                        import shutil
                        # Copy wallet.py to the core directory
                        shutil.copy(wallet_src, os.path.join(core_dir, "wallet.py"))
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Copied wallet module to {core_dir}")
                        
                        # Try importing again
                        try:
                            # Need to reload to pick up the new module
                            import importlib
                            if 'core.wallet' in sys.modules:
                                importlib.reload(sys.modules['core.wallet'])
                            else:
                                from core.wallet import Wallet
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Successfully imported Wallet after copying")
                        except ImportError as e2:
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Failed to import Wallet after copying: {str(e2)}")
                            # Try a direct import
                            sys.path.append(core_dir)
                            try:
                                from wallet import Wallet
                                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Imported Wallet directly from {core_dir}")
                            except ImportError as e3:
                                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] All import attempts failed: {str(e3)}")
                                raise ImportError(f"Could not import Wallet module: {str(e)}")
                    else:
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Could not find wallet.py at {wallet_src}")
                        # Try to find wallet.py anywhere in project
                        blockchain_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        for root, dirs, files in os.walk(blockchain_dir):
                            if "wallet.py" in files:
                                wallet_src = os.path.join(root, "wallet.py")
                                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Found wallet.py at {wallet_src}")
                                import shutil
                                shutil.copy(wallet_src, os.path.join(core_dir, "wallet.py"))
                                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Copied wallet module from {wallet_src}")
                                try:
                                    # Need to reload to pick up the new module
                                    import importlib
                                    if 'core.wallet' in sys.modules:
                                        importlib.reload(sys.modules['core.wallet'])
                                    from core.wallet import Wallet
                                    break
                                except ImportError:
                                    continue
                        else:
                            raise ImportError("Could not find wallet.py anywhere in the project")
                
                # Create wallet directory if it doesn't exist
                wallet_dir = os.path.join(gcn_dir, "wallet")
                os.makedirs(wallet_dir, exist_ok=True)
                wallet_path = os.path.join(wallet_dir, "wallet.enc")
                
                # Initialize and load wallet
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Initializing wallet at {wallet_path}")
                try:
                    self.wallet = Wallet(encrypted_storage_path=wallet_path)
                    
                    if os.path.exists(wallet_path):
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Found existing wallet file, loading...")
                        if self.wallet.load_from_file():
                            self.wallet_status.setText("Wallet loaded from file")
                            self.wallet_status.setStyleSheet("color: green")
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Wallet loaded successfully")
                            return
                        else:
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Failed to load wallet file")
                    else:
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] No existing wallet file found at {wallet_path}")
                        return
                except Exception as e:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error initializing wallet: {str(e)}")
                    return
            except Exception as e:
                self.wallet_status.setText(f"Error loading wallet: {str(e)}")
                self.wallet_status.setStyleSheet("color: red")
                return
        
        # Update address list
        self.address_list.clear()
        addresses = self.wallet.get_addresses()
        
        for address in addresses:
            self.address_list.addItem(address)
            
            # Select the first address if none is selected
            if not self.selected_address and addresses:
                self.selected_address = addresses[0]
        
        # Update selected address in list
        if self.selected_address:
            for i in range(self.address_list.count()):
                if self.address_list.item(i).text() == self.selected_address:
                    self.address_list.setCurrentItem(self.address_list.item(i))
                    break
        
        # Get balance for selected address
        if self.selected_address and self.node_running:
            try:
                # Query blockchain for balance
                response = requests.get(f"{self.api_base}/balance/{self.selected_address}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    balance = data.get('balance', 0)
                    self.balance_label.setText(f"{balance:.8f} GCN")
                    
                    # Get transaction history
                    self.update_transaction_history()
            except Exception as e:
                self.wallet_status.setText(f"Error getting balance: {str(e)}")
                self.wallet_status.setStyleSheet("color: red")
    
    def update_transaction_history(self):
        """Update transaction history for selected address"""
        if not self.selected_address or not self.node_running:
            return
            
        try:
            # Get transactions from blockchain
            response = requests.get(f"{self.api_base}/transactions/history/{self.selected_address}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                transactions = data.get('transactions', [])
                
                if transactions:
                    # Clear current history
                    self.transaction_list.clear()
                    
                    # Display transactions
                    for tx in transactions:
                        # Format timestamp
                        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tx.get('timestamp', 0)))
                        
                        # Format amount with + or - prefix
                        amount = tx.get('amount', 0)
                        if tx.get('sender') == self.selected_address:
                            amount_str = f"-{amount:.8f} GCN"
                            amount_color = "red"
                        else:
                            amount_str = f"+{amount:.8f} GCN"
                            amount_color = "green"
                        
                        # Format transaction type
                        tx_type = tx.get('transaction_type', 'TRANSFER')
                        
                        # Format status
                        if tx.get('confirmed', False):
                            status = "Confirmed"
                        else:
                            status = "Pending"
                        
                        # Build HTML entry
                        tx_html = f"""
                        <div style="margin-bottom: 10px; border-bottom: 1px solid #ddd; padding-bottom: 5px;">
                            <div><b>Date:</b> {timestamp} | <b>Type:</b> {tx_type} | <b>Status:</b> {status}</div>
                            <div><b>Amount:</b> <span style="color: {amount_color};">{amount_str}</span></div>
                            <div><b>From:</b> {tx.get('sender', 'Unknown')}</div>
                            <div><b>To:</b> {tx.get('recipient', 'Unknown')}</div>
                        </div>
                        """
                        
                        # Add to transaction list
                        self.transaction_list.insertHtml(tx_html)
                else:
                    self.transaction_list.setText("No transactions found for this address.")
        except Exception as e:
            self.transaction_list.setText(f"Error loading transactions: {str(e)}")
            self.wallet_status.setText(f"Error: {str(e)}")
            self.wallet_status.setStyleSheet("color: red")
    
    def setup_explorer_page(self):
        explorer_page = QWidget()
        layout = QVBoxLayout()
        explorer_page.setLayout(layout)
        
        title_label = QLabel('Block Explorer')
        title_label.setFont(QFont('Arial', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Block list
        blocks_group = QGroupBox('Latest Blocks')
        blocks_group.setObjectName("blocks_group")  # Set object name for later lookup
        blocks_layout = QVBoxLayout()
        blocks_group.setLayout(blocks_layout)
        
        # Loading indicator
        loading_label = QLabel("Loading blockchain data...")
        loading_label.setAlignment(Qt.AlignCenter)
        blocks_layout.addWidget(loading_label)
        
        # Make the blocks scrollable
        scroll_area = QScrollArea()
        scroll_area.setWidget(blocks_group)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        self.pages.addWidget(explorer_page)
    
    def setup_network_page(self):
        network_page = QWidget()
        layout = QVBoxLayout()
        network_page.setLayout(layout)
        
        title_label = QLabel('Network Status')
        title_label.setFont(QFont('Arial', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Network stats
        stats_group = QGroupBox('Network Statistics')
        stats_group.setObjectName("network_stats")  # Set object name for later lookup
        stats_layout = QVBoxLayout()
        stats_group.setLayout(stats_layout)
        
        # Node status indicator
        self.network_status_label = QLabel("Checking node status...")
        self.network_status_label.setFont(QFont('Arial', 12))
        stats_layout.addWidget(self.network_status_label)
        
        # Total connected nodes
        self.nodes_label = QLabel(f"Total Nodes: {self.network_nodes}")
        self.nodes_label.setFont(QFont('Arial', 12))
        stats_layout.addWidget(self.nodes_label)
        
        # Blockchain height info
        self.blockchain_height_label = QLabel("Blockchain Height: Unknown")
        self.blockchain_height_label.setFont(QFont('Arial', 12))
        stats_layout.addWidget(self.blockchain_height_label)
        
        layout.addWidget(stats_group)
        
        # Peer discovery section
        discovery_group = QGroupBox('Node Discovery')
        discovery_layout = QVBoxLayout()
        discovery_group.setLayout(discovery_layout)
        
        # Quick connect buttons for existing nodes
        quick_connect_layout = QHBoxLayout()
        discovery_layout.addLayout(quick_connect_layout)
        
        quick_connect_layout.addWidget(QLabel("Quick Connect:"))
        
        connect_node1_btn = QPushButton("Connect to Node 1")
        connect_node1_btn.clicked.connect(lambda: self.quick_connect_to_node(1))
        quick_connect_layout.addWidget(connect_node1_btn)
        
        connect_node2_btn = QPushButton("Connect to Node 2")
        connect_node2_btn.clicked.connect(lambda: self.quick_connect_to_node(2))
        quick_connect_layout.addWidget(connect_node2_btn)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        discovery_layout.addWidget(line)
        
        # Manual connection form
        connect_layout = QHBoxLayout()
        discovery_layout.addLayout(connect_layout)
        
        connect_layout.addWidget(QLabel("Connect to Node:"))
        
        self.node_address_entry = QLineEdit()
        self.node_address_entry.setText("127.0.0.1")
        connect_layout.addWidget(self.node_address_entry)
        
        connect_layout.addWidget(QLabel("Port:"))
        
        self.node_port_entry = QLineEdit()
        self.node_port_entry.setText("9001")
        self.node_port_entry.setMaximumWidth(80)
        connect_layout.addWidget(self.node_port_entry)
        
        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.connect_to_node)
        connect_layout.addWidget(connect_button)
        
        discover_button = QPushButton("Discover Network")
        discover_button.clicked.connect(self.discover_network)
        discovery_layout.addWidget(discover_button)
        
        layout.addWidget(discovery_group)
        
        # Connected peers section
        peers_group = QGroupBox('Connected Peers')
        peers_layout = QVBoxLayout()
        peers_group.setLayout(peers_layout)
        
        # Peer list will be populated when data is available
        self.peers_text = QTextEdit()
        self.peers_text.setReadOnly(True)
        self.peers_text.setFont(QFont('Monospace', 10))
        self.peers_text.setText("No peers connected")
        peers_layout.addWidget(self.peers_text)
        
        layout.addWidget(peers_group)
        
        self.pages.addWidget(network_page)
    
    def quick_connect_to_node(self, node_number):
        """Quickly connect to a predefined node"""
        if not self.node_running:
            QMessageBox.warning(self, 'Node Not Running', 'Your node must be running to connect to other nodes.')
            return
            
        port = 9000 if node_number == 1 else 9001  # Node 1 uses 9000, Node 2 uses 9001
        
        try:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Connecting to Node {node_number} (127.0.0.1:{port})...")
            
            response = requests.post(f"{self.api_base}/network/connect", 
                                  json={"address": "127.0.0.1", "port": port},
                                  timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Successfully connected to Node {node_number}")
                    QMessageBox.information(self, 'Connection Successful', f"Connected to Node {node_number}")
                    
                    # Trigger sync after connection
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Triggering blockchain synchronization...")
                    sync_response = requests.post(f"{self.api_base}/network/sync", timeout=10)
                    
                    # Refresh data
                    self.refresh_data()
                else:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Failed to connect: {data.get('message', 'Unknown error')}")
                    QMessageBox.warning(self, 'Connection Failed', f"Failed to connect: {data.get('message', 'Unknown error')}")
            else:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Connection request failed: {response.status_code}")
                QMessageBox.warning(self, 'Connection Failed', f"Request failed with status: {response.status_code}")
        
        except Exception as e:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error connecting: {str(e)}")
            QMessageBox.critical(self, 'Connection Error', f"Error: {str(e)}")
    
    def setup_node_page(self):
        node_page = QWidget()
        layout = QVBoxLayout()
        node_page.setLayout(layout)
        
        title_label = QLabel('Node Management')
        title_label.setFont(QFont('Arial', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Status Group
        status_group = QGroupBox('Node Status')
        status_layout = QVBoxLayout()
        status_group.setLayout(status_layout)
        
        self.status_label = QLabel('⚫ Node Offline')
        self.status_label.setFont(QFont('Arial', 14))
        self.status_label.setStyleSheet('color: red')
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)
        
        # Node health section
        health_group = QGroupBox("Node Health")
        health_layout = QGridLayout()
        
        self.uptime_display = QLabel("Uptime: 0 days, 0 hours, 0 minutes")
        self.cpu_usage_label = QLabel("CPU Usage: 0%")
        self.memory_usage_label = QLabel("Memory Usage: 0 MB")
        self.disk_usage_label = QLabel("Disk Usage: 0 MB")
        self.connection_quality_label = QLabel("Connection Quality: Unknown")
        
        # Make labels bold
        for label in [self.uptime_display, self.cpu_usage_label, self.memory_usage_label,
                     self.disk_usage_label, self.connection_quality_label]:
            font = label.font()
            font.setBold(True)
            label.setFont(font)
        
        health_layout.addWidget(self.uptime_display, 0, 0)
        health_layout.addWidget(self.cpu_usage_label, 0, 1)
        health_layout.addWidget(self.memory_usage_label, 1, 0)
        health_layout.addWidget(self.disk_usage_label, 1, 1)
        health_layout.addWidget(self.connection_quality_label, 2, 0, 1, 2)
        
        health_group.setLayout(health_layout)
        layout.addWidget(health_group)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton('Start Node')
        self.start_button.clicked.connect(self.start_node)
        self.start_button.setMinimumHeight(40)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton('Stop Node')
        self.stop_button.clicked.connect(self.stop_node)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumHeight(40)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        # Sync status section
        sync_group = QGroupBox("Blockchain Synchronization")
        sync_layout = QGridLayout()
        
        self.sync_status_label = QLabel("Sync Status: Not started")
        self.sync_progress_label = QLabel("Blockchain: 0 / 0 blocks (0%)")
        self.sync_time_label = QLabel("Sync Time: 0 seconds")
        
        # Make labels bold
        for label in [self.sync_status_label, self.sync_progress_label, self.sync_time_label]:
            font = label.font()
            font.setBold(True)
            label.setFont(font)
        
        # Add progress bar for sync
        self.sync_progress_bar = QProgressBar()
        self.sync_progress_bar.setMinimum(0)
        self.sync_progress_bar.setMaximum(100)
        self.sync_progress_bar.setValue(0)
        self.sync_progress_bar.setFormat("%p% synchronized")
        
        sync_layout.addWidget(self.sync_status_label, 0, 0)
        sync_layout.addWidget(self.sync_progress_label, 0, 1)
        sync_layout.addWidget(self.sync_time_label, 1, 0)
        sync_layout.addWidget(self.sync_progress_bar, 2, 0, 1, 2)  # Span 2 columns
        
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)
        
        # Log viewer
        log_group = QGroupBox('Node Logs')
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont('Monospace', 10))
        self.log_display.setText("Node logs will appear here when the node is running...")
        log_layout.addWidget(self.log_display)
        
        layout.addWidget(log_group)
        
        self.pages.addWidget(node_page)
    
    def display_page(self, index):
        """Switch to the selected page"""
        self.current_page = index
        self.pages.setCurrentIndex(index)
        
        # Update page content with real data when switching
        if index == 1:  # Transfer page
            self.update_transfer_addresses()
        elif index == 2:  # Wallet page
            self.refresh_wallet_data()
        elif index == 3:  # Block Explorer
            self.update_explorer_page()
        elif index == 4:  # Network page
            self.update_network_page()
        elif index == 6:  # Mining page 
            self.update_mining_page()
            
    def update_explorer_page(self):
        """Update the block explorer page with real blockchain data and pagination for large blockchains"""
        # Clear existing blocks
        blocks_group = self.findChild(QGroupBox, "blocks_group")
        if not blocks_group:
            print("Warning: blocks_group not found")
            return
            
        # Clear existing layout
        layout = blocks_group.layout()
        if not layout:
            print("Warning: layout not found in blocks_group")
            return
            
        # Clear the layout
        while layout.count():
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        
        # Create a container for status messages
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_container.setLayout(status_layout)
        
        # Add an initial "checking" status
        checking_label = QLabel("Checking blockchain data availability...")
        checking_label.setAlignment(Qt.AlignCenter)
        checking_label.setStyleSheet("color: #555; font-size: 14px;")
        status_layout.addWidget(checking_label)
        
        # Add the status container to the main layout
        layout.addWidget(status_container)
        QApplication.processEvents()  # Update UI immediately
        
        # Get chain data with pagination
        chain_data = None
        
        # Initialize pagination variables if they don't exist
        if not hasattr(self, 'blocks_per_page'):
            self.blocks_per_page = 20  # Default blocks per page
        if not hasattr(self, 'total_blocks'):
            self.total_blocks = 0
        
        # We want to start from the latest blocks (last page) 
        # This will be properly set after we have the chain data
                        
        # First check if our node is running and has data
        if self.node_running and self.chain_data and 'chain' in self.chain_data:
            # Data available from our node
            chain_data = self.chain_data
            source_type = "current"
        else:
            # Try alternative data sources
            checking_label.setText("Local node not available. Checking other nodes...")
            QApplication.processEvents()
            
            # Try node1 data
            node1_data = self.safe_api_request("chain", timeout=3, default_value=None)
            if not node1_data:
                # Try direct request to node1
                try:
                    response = requests.get("http://localhost:8001/api/chain", timeout=3)
                    if response.status_code == 200:
                        node1_data = response.json()
                except:
                    node1_data = None
            
            if node1_data and 'chain' in node1_data:
                chain_data = node1_data
                source_type = "node1"
            else:
                # Try node2 data
                node2_data = self.safe_api_request("chain", timeout=3, default_value=None)
                if not node2_data:
                    # Try direct request to node2
                    try:
                        response = requests.get("http://localhost:8002/api/chain", timeout=3)
                        if response.status_code == 200:
                            node2_data = response.json()
                    except:
                        node2_data = None
                        
                if node2_data and 'chain' in node2_data:
                    chain_data = node2_data
                    source_type = "node2"
        
        # Now that we have the data source, implement pagination
        if chain_data and 'chain' in chain_data:
            # Clear status container
            status_container.deleteLater()
            
            # Update total blocks count
            full_chain = chain_data['chain']
            self.total_blocks = len(full_chain)
            
            # Calculate total pages
            total_pages = (self.total_blocks + self.blocks_per_page - 1) // self.blocks_per_page
            
            # Initialize block_page_number if it doesn't exist or if we're loading data for the first time
            # Start from the last page to show newest blocks first
            if not hasattr(self, 'block_page_number') or self.block_page_number >= total_pages:
                self.block_page_number = max(0, total_pages - 1)  # Last page (newest blocks)
            
            # Ensure page number is within bounds
            if self.block_page_number < 0:
                self.block_page_number = 0
            if self.block_page_number >= total_pages:
                self.block_page_number = total_pages - 1
                
            # Get the subset of blocks for the current page
            start_idx = self.block_page_number * self.blocks_per_page
            end_idx = min(start_idx + self.blocks_per_page, self.total_blocks)
            
            # Add source label with pagination info
            if source_type == "current":
                source_text = f"Data from Node {self.config.get('node_number', 3)}"
            elif source_type == "node1":
                source_text = "Data from Node 1"
            else:
                source_text = "Data from Node 2"
                
            # Calculate actual block numbers (newest to oldest)
            newest_block_num = self.total_blocks - 1 - start_idx
            oldest_block_num = self.total_blocks - end_idx
            
            # Add pagination information to the source label with actual block numbers
            source_label = QLabel(f"{source_text} (Showing blocks #{newest_block_num} to #{oldest_block_num} of {self.total_blocks} total blocks)")
            source_label.setAlignment(Qt.AlignCenter)
            source_label.setStyleSheet("color: green; font-weight: bold;")
            layout.addWidget(source_label)
            
            # Add pagination controls
            page_control = QHBoxLayout()
            
            # Previous page button
            prev_btn = QPushButton("◀ Previous Page")
            prev_btn.setEnabled(self.block_page_number > 0)
            prev_btn.clicked.connect(lambda: self.change_block_page(-1))
            page_control.addWidget(prev_btn)
            
            # Page indicator - make it clear that lower page numbers show newer blocks
            page_label = QLabel(f"Page {self.block_page_number + 1} of {total_pages} (Latest blocks first)")
            page_label.setAlignment(Qt.AlignCenter)
            page_control.addWidget(page_label)
            
            # Next page button
            next_btn = QPushButton("Next Page ▶")
            next_btn.setEnabled(self.block_page_number < total_pages - 1)
            next_btn.clicked.connect(lambda: self.change_block_page(1))
            page_control.addWidget(next_btn)
            
            # Add a combo box for page size selection
            page_size_layout = QHBoxLayout()
            page_size_layout.addWidget(QLabel("Blocks per page:"))
            page_size_combo = QComboBox()
            for size in [10, 20, 50, 100]:
                page_size_combo.addItem(str(size))
            
            # Set current value
            index = page_size_combo.findText(str(self.blocks_per_page))
            if index >= 0:
                page_size_combo.setCurrentIndex(index)
                
            page_size_combo.currentTextChanged.connect(self.change_blocks_per_page)
            page_size_layout.addWidget(page_size_combo)
            page_size_layout.addStretch()
            
            # Create container for pagination controls
            page_control_widget = QWidget()
            page_control_widget.setLayout(page_control)
            layout.addWidget(page_control_widget)
            
            # Create container for page size controls
            page_size_widget = QWidget()
            page_size_widget.setLayout(page_size_layout)
            layout.addWidget(page_size_widget)
            
            # Get current page slice of blocks
            # We want newest blocks first, so:
            # 1. Take slice from the end of the chain (newest blocks)
            # 2. Reverse the order since blockchain naturally has oldest first
            page_blocks = full_chain[self.total_blocks - end_idx:self.total_blocks - start_idx]
            # Ensure newest blocks appear at the top
            page_blocks.reverse()
            
            # Show blocks for current page
            self.display_blocks(page_blocks, layout)
            
            # Add pagination controls at the bottom too for large pages
            if self.blocks_per_page > 10:
                # Clone the pagination controls
                bottom_page_control = QHBoxLayout()
                
                # Previous page button
                bottom_prev_btn = QPushButton("◀ Previous Page")
                bottom_prev_btn.setEnabled(self.block_page_number > 0)
                bottom_prev_btn.clicked.connect(lambda: self.change_block_page(-1))
                bottom_page_control.addWidget(bottom_prev_btn)
                
                # Page indicator - make it clear that lower page numbers show newer blocks
                bottom_page_label = QLabel(f"Page {self.block_page_number + 1} of {total_pages} (Latest blocks first)")
                bottom_page_label.setAlignment(Qt.AlignCenter)
                bottom_page_control.addWidget(bottom_page_label)
                
                # Next page button
                bottom_next_btn = QPushButton("Next Page ▶")
                bottom_next_btn.setEnabled(self.block_page_number < total_pages - 1)
                bottom_next_btn.clicked.connect(lambda: self.change_block_page(1))
                bottom_page_control.addWidget(bottom_next_btn)
                
                # Add to layout
                bottom_control_widget = QWidget()
                bottom_control_widget.setLayout(bottom_page_control)
                layout.addWidget(bottom_control_widget)
        else:
            # No data available - use the existing error handling code
            checking_label.setText("No blockchain data available")
            checking_label.setStyleSheet("color: #d9534f; font-size: 16px; font-weight: bold;")
            
            # Add more detailed information
            info_label = QLabel()
            info_label.setWordWrap(True)
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet("color: #555;")
            
            # Create a helpful message based on node status
            if not self.node_running and not self.any_node_running:
                message = """
                <p>No blockchain nodes are currently running. To view blockchain data:</p>
                <ol>
                    <li>Go to the <b>Node</b> tab using the sidebar</li>
                    <li>Click the <b>Start Node</b> button</li>
                    <li>Wait for the node to connect to the network</li>
                    <li>Return to this Block Explorer</li>
                </ol>
                <p>You can also try starting Node 1 or Node 2 if they are configured.</p>
                """
            elif self.node_running and (not hasattr(self, 'chain_data') or not self.chain_data.get('chain')):
                message = """
                <p>Your node is running but no blockchain data is available yet. This could be because:</p>
                <ul>
                    <li>The node is still starting up</li>
                    <li>The blockchain is empty (no blocks mined yet)</li>
                    <li>There may be a synchronization issue</li>
                </ul>
                <p>Try waiting a few moments, then click <b>Refresh</b> below.</p>
                """
            else:
                message = """
                <p>Could not connect to any blockchain nodes to retrieve data.</p>
                <p>Please check your network connection and ensure at least one node is running.</p>
                <p>You can start a node from the <b>Node</b> tab.</p>
                """
            
            info_label.setText(message)
            status_layout.addWidget(info_label)
            
            # Add a refresh button
            refresh_btn = QPushButton("Refresh Block Explorer")
            refresh_btn.clicked.connect(self.update_explorer_page)
            refresh_btn.setStyleSheet("margin-top: 20px;")
            status_layout.addWidget(refresh_btn)
            
            # Add some extra space at the bottom
            spacer = QLabel("")
            spacer.setFixedHeight(30)
            status_layout.addWidget(spacer)
            
    def change_block_page(self, delta):
        """Change the current page of blocks in the explorer"""
        self.block_page_number += delta
        self.update_explorer_page()
    
    def change_blocks_per_page(self, new_size_text):
        """Change the number of blocks shown per page"""
        try:
            new_size = int(new_size_text)
            if new_size != self.blocks_per_page and new_size > 0:
                self.blocks_per_page = new_size
                # Reset to first page when changing page size
                self.block_page_number = 0
                self.update_explorer_page()
        except:
            pass
    
    def display_blocks(self, blocks, layout):
        """Helper method to display blocks in the explorer"""
        if not blocks:
            # Empty blockchain
            empty_label = QLabel("Blockchain is empty. No blocks found.")
            empty_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty_label)
            return
        
        # Add blocks - already in reverse order to show latest first
        for block in blocks:
            # Calculate total GCN in the block
            total_gcn = sum(float(tx.get('amount', 0)) for tx in block.get('transactions', []))
            tx_count = len(block.get('transactions', []))
            
            # Block number and type
            block_index = block['index']
            block_type = "Genesis" if block_index == 0 else "Regular"
            
            # Determine block type from transactions
            for tx in block.get('transactions', []):
                tx_type = tx.get('transaction_type', '')
                if tx.get('sender') == "0" and not tx_type:
                    block_type = "Mining Reward"
                elif tx_type == "PURCHASE":
                    block_type = "Market Purchase"
                elif tx_type == "SELL":
                    block_type = "Market Sell"
                elif tx_type == "TRANSFER":
                    block_type = "Transfer"
            
            # Create a container widget to hold both summary and details
            block_container = QWidget()
            container_layout = QVBoxLayout()
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)  # No spacing between summary and details
            block_container.setLayout(container_layout)
            
            # Create a clickable block summary widget
            block_summary = QPushButton()
            block_summary.setCursor(Qt.PointingHandCursor)  # Show hand cursor on hover
            block_summary.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    background-color: transparent;
                    border: 1px solid #ccc;
                    border-radius: 4px 4px 0 0;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 0, 0, 0.05);
                }
            """)
            
            # Get block timestamp
            timestamp = datetime.fromtimestamp(block['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            
            # Get shortened hash
            short_hash = block['hash'][:10] + "..." + block['hash'][-10:]
            
            # Set the text of the summary button
            summary_text = f"Block #{block_index} | Type: {block_type} | {timestamp}\n"
            summary_text += f"Hash: {short_hash} | GCN: {total_gcn:.8f} | Transactions: {tx_count}"
            block_summary.setText(summary_text)
            
            # Create detailed block content widget (initially hidden)
            block_details = QWidget()
            block_details.setVisible(False)
            block_details.setStyleSheet("""
                background-color: transparent;
                border: 1px solid #ccc;
                border-top: none;
                border-radius: 0 0 4px 4px;
                padding: 10px;
            """)
            
            # Add summary to container
            container_layout.addWidget(block_summary)
            
            details_layout = QVBoxLayout()
            block_details.setLayout(details_layout)
            
            # Add detailed block information
            
            # Block header section
            header_layout = QHBoxLayout()
            
            header_label = QLabel(f"Block #{block_index}")
            header_label.setFont(QFont('Arial', 14, QFont.Bold))
            header_layout.addWidget(header_label)
            
            # Add block type
            type_label = QLabel(f"Type: {block_type}")
            type_label.setStyleSheet("color: blue; font-weight: bold;")
            header_layout.addWidget(type_label)
            
            # Add spacer to push timestamp to the right
            header_layout.addStretch()
            
            # Block timestamp
            time_label = QLabel(f"Created: {timestamp}")
            time_label.setStyleSheet("color: gray;")
            header_layout.addWidget(time_label)
            
            details_layout.addLayout(header_layout)
            
            # Add separator line
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            details_layout.addWidget(line)
            
            # Block hash and other metadata
            meta_layout = QHBoxLayout()
            
            # Block hash with tooltip for full hash
            hash_label = QLabel(f"Hash: {short_hash}")
            hash_label.setToolTip(block['hash'])
            hash_label.setFont(QFont('Monospace', 9))
            meta_layout.addWidget(hash_label)
            
            meta_layout.addStretch()
            
            # Previous hash reference if not genesis
            if block_index > 0:
                prev_hash = block.get('previous_hash', '')
                if prev_hash:
                    short_prev = prev_hash[:8] + "..." + prev_hash[-8:]
                    prev_label = QLabel(f"Previous: {short_prev}")
                    prev_label.setToolTip(prev_hash)
                    prev_label.setFont(QFont('Monospace', 9))
                    meta_layout.addWidget(prev_label)
            
            # Difficulty
            difficulty = block.get('difficulty_target', 0)
            difficulty_label = QLabel(f"Difficulty: {difficulty}")
            meta_layout.addWidget(difficulty_label)
            
            details_layout.addLayout(meta_layout)
            
            # Add separator before transactions
            line2 = QFrame()
            line2.setFrameShape(QFrame.HLine)
            line2.setFrameShadow(QFrame.Sunken)
            details_layout.addWidget(line2)
            
            # Transactions section header
            tx_header_layout = QHBoxLayout()
            
            tx_header = QLabel(f"Transactions: {tx_count}")
            tx_header.setFont(QFont('Arial', 10, QFont.Bold))
            tx_header_layout.addWidget(tx_header)
            
            tx_header_layout.addStretch()
            
            # Total GCN in block
            gcn_label = QLabel(f"Total GCN: {total_gcn:.8f}")
            gcn_label.setStyleSheet("color: green; font-weight: bold;")
            tx_header_layout.addWidget(gcn_label)
            
            details_layout.addLayout(tx_header_layout)
            
            # Display transactions
            if tx_count > 0:
                # Add each transaction
                for i, tx in enumerate(block.get('transactions', [])):
                    tx_frame = QFrame()
                    tx_frame.setFrameShape(QFrame.Box)
                    tx_frame.setLineWidth(1)
                    tx_frame.setStyleSheet("background-color: transparent; border-radius: 3px; border: 1px solid #ddd;")
                    
                    tx_item_layout = QVBoxLayout()
                    tx_frame.setLayout(tx_item_layout)
                    
                    # Transaction header
                    tx_header_row = QHBoxLayout()
                    
                    # Transaction type - Fix to properly distinguish between transfers and mining rewards
                    tx_type = tx.get('transaction_type', 'TRANSFER')
                    # Only set as mining reward if sender is "0" AND there's no specific transaction_type set
                    if tx.get('sender') == "0" and not tx.get('transaction_type'):
                        tx_type = "MINING REWARD"
                    
                    tx_type_label = QLabel(f"Type: {tx_type}")
                    tx_type_label.setStyleSheet("font-weight: bold;")
                    tx_header_row.addWidget(tx_type_label)
                    
                    tx_header_row.addStretch()
                    
                    # Transaction amount
                    amount = float(tx.get('amount', 0))
                    amount_label = QLabel(f"Amount: {amount:.8f} GCN")
                    amount_label.setStyleSheet("color: green;")
                    tx_header_row.addWidget(amount_label)
                    
                    tx_item_layout.addLayout(tx_header_row)
                    
                    # Address information
                    address_layout = QHBoxLayout()
                    
                    # From address
                    sender = tx.get('sender', '---')
                    if sender == "0":
                        sender = "COINBASE (New coins)"
                    from_label = QLabel(f"From: {sender}")
                    from_label.setFont(QFont('Monospace', 8))
                    address_layout.addWidget(from_label)
                    
                    # Arrow
                    arrow_label = QLabel(" → ")
                    address_layout.addWidget(arrow_label)
                    
                    # To address
                    recipient = tx.get('recipient', '---')
                    to_label = QLabel(f"To: {recipient}")
                    to_label.setFont(QFont('Monospace', 8))
                    address_layout.addWidget(to_label)
                    
                    tx_item_layout.addLayout(address_layout)
                    
                    # Fee if present
                    fee = tx.get('fee', 0)
                    if fee > 0:
                        fee_label = QLabel(f"Fee: {fee:.8f} GCN")
                        fee_label.setStyleSheet("color: #888; font-size: 8pt;")
                        tx_item_layout.addWidget(fee_label)
                    
                    # Add to transaction list
                    details_layout.addWidget(tx_frame)
            else:
                # No transactions
                no_tx_label = QLabel("No transactions in this block")
                no_tx_label.setAlignment(Qt.AlignCenter)
                no_tx_label.setStyleSheet("color: #888; font-style: italic;")
                details_layout.addWidget(no_tx_label)
            
            # Add details widget to container
            container_layout.addWidget(block_details)
            
            # Store details widget as a property of the button
            block_summary.details_widget = block_details
            
            # Create a proper method for this specific button instance
            def make_toggle_function(btn, details, block_hash):
                def toggle():
                    # Toggle visibility
                    is_visible = not details.isVisible()
                    details.setVisible(is_visible)
                    
                    # Update the tracking set based on visibility state
                    if is_visible:
                        self.expanded_blocks.add(block_hash)
                    else:
                        self.expanded_blocks.discard(block_hash)
                    
                    # Update button border radius when details are shown/hidden
                    if is_visible:
                        btn.setStyleSheet("""
                            QPushButton {
                                text-align: left;
                                background-color: transparent;
                                border: 1px solid #ccc;
                                border-bottom: none;
                                border-radius: 4px 4px 0 0;
                                padding: 10px;
                            }
                            QPushButton:hover {
                                background-color: rgba(0, 0, 0, 0.05);
                            }
                        """)
                    else:
                        btn.setStyleSheet("""
                            QPushButton {
                                text-align: left;
                                background-color: transparent;
                                border: 1px solid #ccc;
                                border-radius: 4px;
                                padding: 10px;
                            }
                            QPushButton:hover {
                                background-color: rgba(0, 0, 0, 0.05);
                            }
                        """)
                return toggle
            
            # Connect with a function that has proper closure over both objects
            block_hash = block['hash']
            toggle_func = make_toggle_function(block_summary, block_details, block_hash)
            block_summary.clicked.connect(toggle_func)
            
            # Check if this block was previously expanded and restore that state
            if block_hash in self.expanded_blocks:
                # Set initial state to expanded
                block_details.setVisible(True)
                block_summary.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        background-color: transparent;
                        border: 1px solid #ccc;
                        border-bottom: none;
                        border-radius: 4px 4px 0 0;
                        padding: 10px;
                    }
                    QPushButton:hover {
                        background-color: rgba(0, 0, 0, 0.05);
                    }
                """)
            
            # Add the block container to main layout
            layout.addWidget(block_container)
            
            # Add spacer between blocks
            spacer = QLabel("")
            spacer.setFixedHeight(10)
            layout.addWidget(spacer)
            
    def try_fetch_chain_data(self, node_number, api_url):
        """Safely try to fetch chain data from a node with proper error handling"""
        try:
            # Use a short timeout to prevent UI freezing
            response = requests.get(api_url, timeout=3)
            if response.status_code == 200:
                node_data = response.json()
                if node_data and 'chain' in node_data and node_data['chain']:
                    print(f"Successfully fetched data from node{node_number}")
                    return node_data['chain']
        except requests.exceptions.ConnectTimeout:
            print(f"Connection timeout when connecting to node{node_number}")
        except requests.exceptions.ConnectionError:
            print(f"Connection error: node{node_number} is not running")
        except Exception as e:
            print(f"Error fetching from node{node_number}: {str(e)}")
        
        # Return None if we failed to get data
        return None
        
    def update_network_page(self):
        """Update the network page with real network data"""
        # Count active nodes
        active_node_count = 0
        node1_running = False
        node2_running = False
        node3_running = self.node_running
        
        try:
            # Check node1
            response = requests.get("http://localhost:8001/api/blockchain", timeout=1)
            if response.status_code == 200:
                node1_running = True
                active_node_count += 1
                print("Node 1 is running (added to node count)")
        except Exception as e:
            print(f"Node 1 check error: {str(e)}")
            
        try:
            # Check node2
            response = requests.get("http://localhost:8002/api/blockchain", timeout=1)
            if response.status_code == 200:
                node2_running = True
                active_node_count += 1
                print("Node 2 is running (added to node count)")
        except Exception as e:
            print(f"Node 2 check error: {str(e)}")
            
        # Add our node if it's running
        if node3_running:
            active_node_count += 1
            print("Node 3 (our node) is running (added to node count)")
            
        # Update the nodes count label with the real count
        print(f"Setting total nodes count to {active_node_count}")
        self.nodes_label.setText(f"Total Nodes: {active_node_count}")
        
        # Update node status label
        if hasattr(self, 'network_status_label'):
            status_text = []
            if node1_running:
                status_text.append("Node 1")
            if node2_running:
                status_text.append("Node 2")
            if node3_running:
                status_text.append("Node 3")
                
            if status_text:
                self.network_status_label.setText(f"Running nodes: {', '.join(status_text)}")
                self.network_status_label.setStyleSheet("color: green")
            else:
                self.network_status_label.setText("No nodes running")
                self.network_status_label.setStyleSheet("color: red")
        
        # Update blockchain height info
        if hasattr(self, 'blockchain_height_label'):
            chain_length = 'Unknown'
            
            # Try to get blockchain height from our node first
            if self.blockchain_data and 'chain_length' in self.blockchain_data:
                chain_length = str(self.blockchain_data['chain_length'])
                self.blockchain_height_label.setText(f"Blockchain Height: {chain_length}")
            else:
                # Try to get data from existing nodes
                try:
                    # Try node1
                    response = requests.get("http://localhost:8001/api/blockchain", timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        if 'chain_length' in data:
                            chain_length = str(data['chain_length'])
                except:
                    try:
                        # Try node2
                        response = requests.get("http://localhost:8002/api/blockchain", timeout=2)
                        if response.status_code == 200:
                            data = response.json()
                            if 'chain_length' in data:
                                chain_length = str(data['chain_length'])
                    except:
                        pass
                
                self.blockchain_height_label.setText(f"Blockchain Height: {chain_length}")
        
        # Update the peer list
        if hasattr(self, 'peers_text'):
            # Clear the current text
            self.peers_text.clear()
            
            # Check if we have peer data from our node
            if self.peers_data and 'peers' in self.peers_data and self.peers_data['peers']:
                peers = self.peers_data['peers']
                
                # Format and add each peer
                for peer in peers:
                    node_id = peer.get('node_id', 'Unknown')
                    address = peer.get('address', 'Unknown')
                    port = peer.get('port', 'Unknown')
                    last_seen = peer.get('last_seen', 0)
                    
                    # Format last seen time
                    if last_seen == 0:
                        last_seen_str = "Unknown"
                    elif last_seen < 60:
                        last_seen_str = f"{int(last_seen)} seconds ago"
                    else:
                        minutes = int(last_seen / 60)
                        last_seen_str = f"{minutes} minutes ago"
                    
                    # Add the peer to the text display
                    self.peers_text.append(f"Node {node_id} - {address}:{port} - Last seen: {last_seen_str}")
            else:
                # No peers data from our node, check if other nodes are running
                other_nodes_running = False
                
                try:
                    # Check node1
                    response = requests.get("http://localhost:8001/api/network/peers", timeout=2)
                    if response.status_code == 200:
                        other_nodes_running = True
                        data = response.json()
                        if 'peers' in data and data['peers']:
                            self.peers_text.append("Peers connected to Node 1:")
                            for peer in data['peers']:
                                self.peers_text.append(f"Node {peer.get('node_id', 'Unknown')} - {peer.get('address', 'Unknown')}:{peer.get('port', 'Unknown')}")
                except:
                    pass
                    
                try:
                    # Check node2
                    response = requests.get("http://localhost:8002/api/network/peers", timeout=2)
                    if response.status_code == 200:
                        other_nodes_running = True
                        data = response.json()
                        if 'peers' in data and data['peers']:
                            self.peers_text.append("Peers connected to Node 2:")
                            for peer in data['peers']:
                                self.peers_text.append(f"Node {peer.get('node_id', 'Unknown')} - {peer.get('address', 'Unknown')}:{peer.get('port', 'Unknown')}")
                except:
                    pass
                
                if not other_nodes_running:
                    # No peers connected to any node
                    self.peers_text.setText("No peers connected")
                
            # Make sure the updates are visible
            self.peers_text.repaint()
    
    def check_node_status(self):
        """Check if the node is running and reachable via API"""
        was_running = self.node_running
        process_running = False
        api_reachable = False
        
        # Track this status check for logging
        check_time = time.strftime('%H:%M:%S')
        
        # Check 1: Is the process running?
        if self.node_process and self.node_process.poll() is None:
            process_running = True
            print(f"Process is running with PID: {self.node_process.pid}")
            # Only log this once when the process starts
            if not was_running:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node process is running with PID: {self.node_process.pid}")
        else:
            # Check if the NodeManager reports the node as running (it may be managed by NodeManager now)
            node_manager_running = False
            if hasattr(self, 'node_manager'):
                node_manager_running = self.node_manager.is_running()
                
            # If NodeManager has a running node, update our status
            if node_manager_running:
                process_running = True
                print(f"Process is running through NodeManager")
                # Only log this once
                if not was_running:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node running through NodeManager")
            else:
                print("Process is not running or has terminated")
                # If we had a process before but it's gone now, and NodeManager doesn't have it, try to restart it
                if was_running and not node_manager_running:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] ⚠️ Node process terminated unexpectedly, attempting restart...")
                    self.start_node()
                    return
            
        # Check 2: Is the API reachable?
        try:
            print(f"Checking API reachability at {self.api_base}/blockchain")
            # Reduce timeout for faster feedback and recovery
            response = requests.get(f"{self.api_base}/blockchain", timeout=4)
            
            # Handle both 200 and other successful status codes
            if response.status_code == 200 or (response.status_code >= 200 and response.status_code < 300):
                api_reachable = True
                print("API is reachable")
                
                # Debug info
                try:
                    data = response.json()
                    print(f"API response: {data}")
                    # Update local data with the response
                    self.blockchain_data = data
                    
                    # Update node status in the UI once we have API access
                    if data.get("status") == "online" and not was_running:
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] ✅ Node is fully operational - API accessible!")
                        
                        # Check if we need to start blockchain sync
                        if not self.initial_sync_complete and not self.sync_in_progress:
                            # Start background sync
                            self.start_background_sync()
                        
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
        except Exception as e:
            api_reachable = False
            print(f"API connection error: {str(e)}")
        
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
            
            # Allow up to 6 API failures before marking node as down (more lenient)
            if self.api_fail_count <= 6:
                self.node_running = True
                if self.api_fail_count == 1:  # Only log once
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] ⚠️ API temporarily unavailable, will retry...")
            else:
                # Too many consecutive failures
                self.node_running = False
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] ❌ API connection failed repeatedly, node may need restart")
        else:
            # If process is running, always consider the node running
            # This is more lenient and fixes the "Node Offline" display issue
            if process_running:
                self.node_running = True
                
                # Only reset API fail count if we actually reached the API
                if api_reachable:
                    self.api_fail_count = 0
                
                # Schedule another check soon
                QTimer.singleShot(2000, self.check_node_status)
            else:
                # No process running, definitely offline
                self.node_running = False
        
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
                
            # Always refresh data when API becomes available
            self.refresh_data()
                
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
    
    def connect_to_node(self):
        """Connect to a remote node"""
        try:
            # Get address and port from input fields
            address = self.node_address_entry.text()
            port = int(self.node_port_entry.text())
            
            if not address:
                QMessageBox.warning(self, 'Missing Address', 'Please enter a node address.')
                return
            
            # Try to connect to the node
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Connecting to node: {address}:{port}...")
            
            # Call the API to connect to this peer
            response = requests.post(f"{self.api_base}/network/connect", 
                                   json={"address": address, "port": port},
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Successfully connected to node: {address}:{port}")
                    QMessageBox.information(self, 'Connection Successful', f"Connected to node at {address}:{port}")
                    
                    # Refresh peer data
                    self.fetch_network_status()
                    self.update_network_page()
                else:
                    error = data.get('message', 'Unknown error')
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Failed to connect: {error}")
                    QMessageBox.warning(self, 'Connection Failed', f"Failed to connect: {error}")
            else:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Connection request failed: {response.status_code}")
                QMessageBox.warning(self, 'Connection Failed', f"Request failed with status: {response.status_code}")
        
        except ValueError:
            QMessageBox.warning(self, 'Invalid Port', 'Please enter a valid port number.')
        except Exception as e:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error connecting: {str(e)}")
            QMessageBox.critical(self, 'Connection Error', f"Error: {str(e)}")
    
    def discover_network(self):
        """Discover nodes in the network"""
        try:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Discovering network peers...")
            
            # Call the API to discover peers
            response = requests.post(f"{self.api_base}/network/discover", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    discovered = data.get('discovered_peers', [])
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Discovered {len(discovered)} peer(s)")
                    QMessageBox.information(self, 'Discovery Successful', f"Discovered {len(discovered)} peer(s)")
                    
                    # Refresh peer data
                    self.fetch_network_status()
                    self.update_network_page()
                else:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] No new peers discovered")
                    QMessageBox.information(self, 'Discovery', "No new peers discovered")
            else:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Discovery request failed: {response.status_code}")
                QMessageBox.warning(self, 'Discovery Failed', f"Request failed with status: {response.status_code}")
        
        except Exception as e:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error discovering peers: {str(e)}")
            QMessageBox.critical(self, 'Discovery Error', f"Error: {str(e)}")
    
    def start_background_sync(self):
        """Start blockchain synchronization in a background thread"""
        if self.sync_in_progress:
            print("Sync already in progress, skipping")
            return
            
        self.sync_in_progress = True
        self.sync_start_time = time.time()
        
        # Create and start a background thread for sync
        import threading
        
        def sync_worker():
            try:
                print("Starting background blockchain sync...")
                if hasattr(self, 'log_display'):
                    QTimer.singleShot(0, lambda: self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Starting background blockchain synchronization..."))
                
                # Give the node some time to initialize
                time.sleep(3)
                
                # Get network status to check for total blockchain length
                max_blockchain_length = 0
                local_blockchain_length = 0
                
                try:
                    # Try node 1 and 2 to find longest chain
                    for port in [8001, 8002]:
                        try:
                            url = f"http://localhost:{port}/api/blockchain"
                            response = requests.get(url, timeout=2)
                            if response.status_code == 200:
                                data = response.json()
                                if 'chain_length' in data and data['chain_length'] > max_blockchain_length:
                                    max_blockchain_length = data['chain_length']
                        except:
                            pass
                            
                    # Also check our node
                    our_port = self.config.get('web_port', 8003)
                    url = f"http://localhost:{our_port}/api/blockchain"
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        if 'chain_length' in data:
                            local_blockchain_length = data['chain_length']
                            
                            # Update our tracking variables
                            self.total_blockchain_length = max(max_blockchain_length, local_blockchain_length)
                            self.local_blockchain_length = local_blockchain_length
                            
                            # Update the sync status display
                            QTimer.singleShot(0, self.update_sync_status)
                            
                            # If the local chain is already the longest, we're done
                            if local_blockchain_length >= max_blockchain_length and max_blockchain_length > 0:
                                QTimer.singleShot(0, lambda: self.log_display.append(
                                    f"[{time.strftime('%H:%M:%S')}] Node already has the longest blockchain ({local_blockchain_length} blocks)"))
                                self.initial_sync_complete = True
                                self.sync_in_progress = False
                                # Speed up UI refresh once sync is done
                                QTimer.singleShot(0, self.adjust_timers_after_sync)
                                return
                                
                            if max_blockchain_length > 0:
                                QTimer.singleShot(0, lambda length=max_blockchain_length, local=local_blockchain_length: 
                                                   self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Network blockchain length: {length} blocks, Local: {local} blocks"))
                                
                except Exception as e:
                    print(f"Error checking blockchain lengths: {str(e)}")
                    
                # Trigger sync (similar to how node1/node2 do it)
                try:
                    our_port = self.config.get('web_port', 8003)
                    sync_url = f"http://localhost:{our_port}/api/network/sync"
                    
                    QTimer.singleShot(0, lambda: self.log_display.append(
                        f"[{time.strftime('%H:%M:%S')}] Triggering blockchain sync at {sync_url}..."))
                    
                    response = requests.post(sync_url, timeout=30)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Update UI with sync result
                        if result.get('synchronized', False):
                            QTimer.singleShot(0, lambda: self.log_display.append(
                                f"[{time.strftime('%H:%M:%S')}] ✅ Blockchain sync complete! Chain length: {result.get('local_chain_length_after', 0)} blocks"))
                            
                            self.initial_sync_complete = True
                            
                            # Update our tracking variables
                            self.local_blockchain_length = result.get('local_chain_length_after', 0)
                            
                            # Update the sync status display
                            QTimer.singleShot(0, self.update_sync_status)
                        else:
                            QTimer.singleShot(0, lambda: self.log_display.append(
                                f"[{time.strftime('%H:%M:%S')}] Sync not needed or failed: {result.get('sync_message', 'Unknown')}"))
                    else:
                        QTimer.singleShot(0, lambda: self.log_display.append(
                            f"[{time.strftime('%H:%M:%S')}] Sync request failed with status {response.status_code}"))
                except Exception as e:
                    QTimer.singleShot(0, lambda: self.log_display.append(
                        f"[{time.strftime('%H:%M:%S')}] Error during blockchain sync: {str(e)}"))
                
                # Sync is done
                self.sync_in_progress = False
                
                # Speed up UI refresh now that sync is complete
                QTimer.singleShot(0, self.adjust_timers_after_sync)
                
            except Exception as e:
                print(f"Error in sync worker thread: {str(e)}")
                self.sync_in_progress = False
                
        # Start the sync thread
        sync_thread = threading.Thread(target=sync_worker, daemon=True)
        sync_thread.start()
        
    def update_sync_status(self):
        """Update the synchronization status display"""
        # Only update if we have the necessary UI elements
        if not hasattr(self, 'sync_status_label') or not hasattr(self, 'sync_progress_label'):
            return
            
        if self.initial_sync_complete:
            self.sync_status_label.setText("Sync Status: Complete")
            self.sync_status_label.setStyleSheet("color: green")
            self.sync_progress_bar.setValue(100)
            
            # Calculate percentage
            if self.total_blockchain_length > 0:
                percentage = 100
                self.sync_progress_label.setText(f"Blockchain: {self.local_blockchain_length} / {self.total_blockchain_length} blocks (100%)")
            else:
                self.sync_progress_label.setText("Blockchain: Synchronized")
                
            # Calculate sync time if we have it
            if self.sync_start_time:
                sync_time = time.time() - self.sync_start_time
                self.sync_time_label.setText(f"Sync Time: {sync_time:.1f} seconds")
                
        elif self.sync_in_progress:
            self.sync_status_label.setText("Sync Status: In Progress")
            self.sync_status_label.setStyleSheet("color: orange")
            
            # Calculate percentage
            if self.total_blockchain_length > 0:
                percentage = min(100, int((self.local_blockchain_length / self.total_blockchain_length) * 100))
                self.sync_progress_bar.setValue(percentage)
                self.sync_progress_label.setText(f"Blockchain: {self.local_blockchain_length} / {self.total_blockchain_length} blocks ({percentage}%)")
            else:
                self.sync_progress_label.setText("Blockchain: Calculating...")
                self.sync_progress_bar.setValue(0)
                
            # Calculate sync time if we have it
            if self.sync_start_time:
                sync_time = time.time() - self.sync_start_time
                self.sync_time_label.setText(f"Sync Time: {sync_time:.1f} seconds")
        else:
            self.sync_status_label.setText("Sync Status: Not Started")
            self.sync_status_label.setStyleSheet("")
            self.sync_progress_bar.setValue(0)
            self.sync_progress_label.setText("Blockchain: 0 / 0 blocks (0%)")
            self.sync_time_label.setText("Sync Time: 0 seconds")
    
    def adjust_timers_after_sync(self):
        """Adjust timer frequencies after sync is complete"""
        if self.initial_sync_complete:
            # Restore normal timer frequencies after sync is complete
            self.timer.start(15000)  # Check every 15 seconds 
            self.data_timer.start(30000)  # Refresh data every 30 seconds
            self.quick_status_timer.start(5000)  # Quick status check every 5 seconds
            
            # Update sync status display
            self.update_sync_status()
            
            # Refresh UI immediately
            self.refresh_data()
        
    def start_node(self):
        """Start the blockchain node with dynamic configuration using the new NodeManager"""
        try:
            # Show message
            QMessageBox.information(self, 'Node Starting', 'Starting GlobalCoyn node...')
            
            # Get a unique node number and available ports using the node discovery service
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Obtaining node configuration...")
            
            # Get dynamic node number first
            node_number = self.node_discovery.get_node_number()
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Assigned node number: {node_number}")
            
            # Find available ports
            p2p_port, web_port = self.node_discovery.find_available_ports()
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Using ports: P2P={p2p_port}, Web={web_port}")
            
            # Update configuration and class member
            self.config['node_number'] = node_number
            self.config['p2p_port'] = p2p_port
            self.config['web_port'] = web_port
            self.web_port = web_port  # Update the member variable
            
            # Update API base URL if needed
            if not self.config.get('production_mode', False):
                self.api_base = f"http://localhost:{self.web_port}/api"
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Updated API base URL to {self.api_base}")
            
            # Save the updated configuration
            self.config_manager.save_config()
            
            # Display configuration info
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Starting node with configuration:")
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] - Node Number: {node_number}")
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] - P2P Port: {p2p_port}")
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] - Web Port: {web_port}")
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] - Data Directory: {self.config.get('data_directory', os.path.expanduser('~/GlobalCoyn'))}")
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] - Production Mode: {'Yes' if self.config.get('production_mode', False) else 'No'}")
            
            # Use our new NodeManager to start the node with throttling
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Starting node with managed throttling to prevent app freezing...")
            
            # Define the log callback function to display node output
            def log_callback(msg):
                self.log_display.append(msg)
            
            # Start the node using NodeManager
            success = self.node_manager.start_node(
                node_number=node_number,
                p2p_port=p2p_port,
                web_port=web_port,
                callback=log_callback
            )
            
            if success:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node started successfully with throttled API access")
                
                # Update start/stop button states
                self.node_running = True
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.status_label.setText('🟢 Node Online')
                self.status_label.setStyleSheet('color: green')
                
                # After starting node, try to discover peers
                if self.config.get('production_mode', False):
                    # Wait a bit for the node to initialize
                    QTimer.singleShot(10000, self.discover_network_peers)
                else:
                    # In development mode, connect to local nodes after a short delay
                    QTimer.singleShot(5000, self.connect_to_local_nodes)
            else:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Failed to start node")
                QMessageBox.critical(self, 'Error', 'Failed to start node. Please check the logs for details.')
        
        except Exception as e:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error starting node: {str(e)}")
            QMessageBox.critical(self, 'Error', f'Error starting node: {str(e)}')
            traceback.print_exc()
            
            # Define script_dir if not already defined
            script_dir = os.path.dirname(os.path.abspath(__file__))
            blockchain_dir = os.path.dirname(os.path.dirname(script_dir))
            node2_dir = os.path.join(blockchain_dir, "nodes", "node2")
            
            if os.path.exists(os.path.join(node2_dir, "app.py")):
                # Copy necessary files
                try:
                    # Create core directory if it doesn't exist
                    core_dir = os.path.join(data_dir, "core")
                    os.makedirs(core_dir, exist_ok=True)
                    
                    # Create a modified app.py with correct imports
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Creating modified app.py with correct import paths")
                    
                    # Find the original app.py to use as a template
                    source_app_path = os.path.join(node2_dir, "app.py")
                    
                    # Read the template
                    with open(source_app_path, 'r') as src:
                        app_content = src.read()
                        
                    # Modify the content to fix the import paths
                    # Add these lines near the top after the imports but before the Flask setup
                    import_fix = """
# Calculate paths
current_dir = os.path.dirname(os.path.abspath(__file__))
nodes_dir = os.path.dirname(current_dir)
blockchain_dir = os.path.dirname(nodes_dir)
core_dir = os.path.join(blockchain_dir, "core")

# Add the directories to Python path
sys.path.append(current_dir)
sys.path.append(core_dir)

# Import directly from core directory with module paths
sys.path.append(os.path.dirname(core_dir))  # Add parent of core to path

# Now import using direct imports
from coin import GlobalCoyn, Coin
from blockchain import Transaction as BlockchainTransaction
"""
                    
                    # Replace the problematic import line
                    app_content = app_content.replace(
                        "from core.coin import GlobalCoyn, Coin", 
                        "# Import will be handled below"
                    )
                    
                    # Ensure correct seed nodes for Node 3
                    if self.config.get('node_number', 3) == 3:
                        # Replace seed node configuration to connect to both Node 1 and Node 2
                        seed_node_pattern = """    # Configure seed nodes based on node number
    seed_nodes = []
    if node_num == 1:
        # Node 1 connects to Node 2
        seed_nodes = [
            ("127.0.0.1", 9001),  # Node 2 running locally
            ("localhost", 9001)   # Another way to reference Node 2
        ]
    else:
        # Node 2 (or other nodes) connect to Node 1
        seed_nodes = [
            ("127.0.0.1", 9000),  # Node 1 running locally
            ("localhost", 9000)   # Another way to reference Node 1
        ]"""
                        
                        node3_seed_config = """    # Configure seed nodes for Node 3 to connect to both Node 1 and Node 2
    seed_nodes = [
        ("127.0.0.1", 9000),  # Node 1 running locally
        ("127.0.0.1", 9001)   # Node 2 running locally
    ]"""
                        
                        app_content = app_content.replace(seed_node_pattern, node3_seed_config)
                    
                    # Find the right position to insert our path fix
                    # After the initial imports but before Flask setup
                    import_section_end = app_content.find("# Initialize Flask app")
                    if import_section_end == -1:  # Fallback if not found
                        import_section_end = app_content.find("app = Flask")
                    
                    if import_section_end != -1:
                        # Insert our import fix
                        app_content = app_content[:import_section_end] + import_fix + app_content[import_section_end:]
                    else:
                        # If we can't find the right position, just add it at the top after the docstring
                        docstring_end = app_content.find('"""', app_content.find('"""') + 3)
                        if docstring_end != -1:
                            app_content = app_content[:docstring_end+4] + import_fix + app_content[docstring_end+4:]
                        
                    # Write the modified app.py
                    with open(os.path.join(data_dir, "app.py"), 'w') as dest:
                        dest.write(app_content)
                        
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Modified app.py created with fixed import paths")
                    
                    # Set up the node properly following the node template structure
                    blockchain_dir = os.path.dirname(os.path.dirname(script_dir))
                    
                    # 1. Create routes directory
                    routes_dir = os.path.join(data_dir, "routes")
                    os.makedirs(routes_dir, exist_ok=True)
                    
                    # 2. Copy the core module files
                    core_source_dir = os.path.join(blockchain_dir, "core")
                    if os.path.exists(core_source_dir):
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Setting up core module")
                        
                        # Instead of copying core files directly, we'll set up PYTHONPATH
                        # Create a symlink to the core directory
                        try:
                            # Create a symlink for the core directory
                            core_target = os.path.join(data_dir, "core")
                            if os.path.exists(core_target):
                                if os.path.islink(core_target):
                                    os.unlink(core_target)
                                else:
                                    import shutil
                                    shutil.rmtree(core_target)
                            
                            # Create the symlink
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Creating symlink to core directory")
                            os.symlink(core_source_dir, core_target)
                            
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Core directory linked successfully")
                        except Exception as e:
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Warning: Could not create symlink: {str(e)}")
                            
                            # Fall back to copying files
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Falling back to copying core files")
                            
                            # Create the core directory
                            os.makedirs(core_target, exist_ok=True)
                            
                            # Copy each file from the core directory
                            core_files = ["blockchain.py", "coin.py", "wallet.py", "price_oracle.py", "improved_node_sync.py"]
                            for filename in core_files:
                                source_file = os.path.join(core_source_dir, filename)
                                if os.path.exists(source_file):
                                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Copying {filename}")
                                    with open(source_file, 'r') as src:
                                        with open(os.path.join(core_target, filename), 'w') as dest:
                                            dest.write(src.read())
                            
                            # Create __init__.py file in core directory
                            with open(os.path.join(core_target, "__init__.py"), 'w') as f:
                                f.write("# Core package initialization\n")
                    else:
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] WARNING: Core directory not found at {core_source_dir}")
                    
                    # 3. Copy routes files from template or node2
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Setting up routes")
                    template_dir = os.path.join(blockchain_dir, "node_template")
                    
                    # Try template directory first, then node2
                    source_routes_dir = os.path.join(template_dir, "routes")
                    if not os.path.exists(source_routes_dir):
                        source_routes_dir = os.path.join(node2_dir, "routes")
                    
                    if os.path.exists(source_routes_dir):
                        # Copy routes files
                        for filename in ["__init__.py", "network.py", "transactions.py"]:
                            source_file = os.path.join(source_routes_dir, filename)
                            if os.path.exists(source_file):
                                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Copying routes/{filename}")
                                with open(source_file, 'r') as src:
                                            with open(os.path.join(routes_dir, filename), 'w') as dest:
                                                dest.write(src.read())
                            else:
                                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] WARNING: Routes directory not found")
                                
                                # Create minimal routes files
                                with open(os.path.join(routes_dir, "__init__.py"), 'w') as f:
                                    f.write("# Routes package\n")
                                
                                # Create empty files for the missing ones
                                for filename in ["network.py", "transactions.py"]:
                                    with open(os.path.join(routes_dir, filename), 'w') as f:
                                        f.write(f"# {filename} - Created by GlobalCoyn app\n")
                            
                            # 4. Copy requirements.txt
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Setting up requirements.txt")
                            source_req = os.path.join(template_dir, "requirements.txt")
                            if not os.path.exists(source_req):
                                source_req = os.path.join(node2_dir, "requirements.txt")
                            
                            if os.path.exists(source_req):
                                with open(source_req, 'r') as src:
                                    with open(os.path.join(data_dir, "requirements.txt"), 'w') as dest:
                                        dest.write(src.read())
                            else:
                                # Create minimal requirements.txt
                                with open(os.path.join(data_dir, "requirements.txt"), 'w') as f:
                                    f.write("Flask==2.0.1\nFlask-Cors==3.0.10\npython-dotenv==0.19.0\ncryptography==3.4.8\nrequests==2.26.0\nwerkzeug==2.0.2\n")
                                    
                            # 5. Create proper start_node.sh script
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Setting up start_node.sh")
                            
                            # Create a proper start_node.sh script
                            start_script_content = f"""#!/bin/bash
# GlobalCoyn Node Startup Script

# Node configuration
NODE_NUM={self.config.get('node_number', 3)}
P2P_PORT={self.config.get('p2p_port', 9002)}
WEB_PORT={self.config.get('web_port', 8003)}

echo "Starting GlobalCoyn Node $NODE_NUM"
echo "P2P Port: $P2P_PORT"
echo "Web Port: $WEB_PORT"

# Kill any existing processes using the ports
echo "Checking for existing processes on ports $WEB_PORT and $P2P_PORT..."
PID_WEB=$(lsof -ti:$WEB_PORT)
if [ -n "$PID_WEB" ]; then
  echo "Killing existing process on port $WEB_PORT (PID: $PID_WEB)"
  kill -9 $PID_WEB
fi

PID_P2P=$(lsof -ti:$P2P_PORT)
if [ -n "$PID_P2P" ]; then
  echo "Killing existing process on port $P2P_PORT (PID: $PID_P2P)"
  kill -9 $PID_P2P
fi

# Wait a moment for ports to be released
sleep 1

# Set environment variables
export GCN_NODE_NUM=$NODE_NUM
export GCN_P2P_PORT=$P2P_PORT
export GCN_WEB_PORT=$WEB_PORT

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Calculate paths
CURRENT_DIR=$(pwd)
NODES_DIR=$(dirname $CURRENT_DIR)
BLOCKCHAIN_DIR=$(dirname $NODES_DIR)
CORE_DIR="$BLOCKCHAIN_DIR/core"

echo "Setting Python paths:"
echo " - Current Dir: $CURRENT_DIR"
echo " - Nodes Dir: $NODES_DIR"
echo " - Blockchain Dir: $BLOCKCHAIN_DIR"
echo " - Core Dir: $CORE_DIR"

# Set Python path to include core directory
export PYTHONPATH=$CURRENT_DIR:$CORE_DIR:$BLOCKCHAIN_DIR:$PYTHONPATH

# Start the node
python app.py
"""
                            
                            with open(os.path.join(data_dir, "start_node.sh"), 'w') as f:
                                f.write(start_script_content)
                            
                            # Make the script executable
                            os.chmod(os.path.join(data_dir, "start_node.sh"), 0o755)
                            
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node setup completed successfully")
                                
                            # Now try to run it
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Starting node with copied app.py")
                            
                            # Start the node process
                            self.node_process = subprocess.Popen([python_executable, os.path.join(data_dir, "app.py")], 
                                                              cwd=data_dir,
                                                              env=env,
                                                              stdout=subprocess.PIPE, 
                                                              stderr=subprocess.STDOUT,
                                                              text=True,
                                                              bufsize=1)  # Line buffered
                            
                            # Set up a thread to read and display the output
                            def read_output():
                                try:
                                    # Use binary mode to handle non-UTF8 characters safely
                                    for line_bytes in iter(lambda: self.node_process.stdout.buffer.readline(), b''):
                                        try:
                                            # Decode with error handling
                                            line = line_bytes.decode('utf-8', errors='replace')
                                            timestamp = time.strftime('%H:%M:%S')
                                            self.log_display.append(f"[{timestamp}] {line.strip()}")
                                        except Exception as e:
                                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] [Error reading output: {str(e)}]")
                                            time.sleep(0.1)
                                except Exception as e:
                                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] [Error in output thread: {str(e)}]")
                            
                            # Start the output reader thread
                            threading.Thread(target=read_output, daemon=True).start()
                
                except Exception as e:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error copying/running app.py: {str(e)}")
                    QMessageBox.critical(self, 'Error', f'Failed to copy/run app.py: {str(e)}')
                    return
            else:
                # No app.py found, show error
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] ERROR: Cannot find app.py to start the node")
                QMessageBox.critical(self, 'Error', 'Cannot find the node application (app.py)')
                return
            
            # Update the API base URL to match the running node
            self.api_base = f"http://localhost:{self.config.get('web_port', 8003)}/api"
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Set API base URL to {self.api_base}")
            
            # Record start time for status tracking
            self.start_time = time.time()
            
            # Wait a bit for the node to start
            QTimer.singleShot(2000, self.check_node_status)
            
            # Schedule first data refresh after a short delay
            QTimer.singleShot(5000, self.refresh_data)
            
            # Add ability to connect to existing nodes
            QTimer.singleShot(10000, self.connect_to_existing_nodes)
            
        except Exception as e:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] ERROR: {str(e)}")
            QMessageBox.critical(self, 'Error', f'Failed to start node: {str(e)}')
    
    def connect_to_existing_nodes(self):
        """Connect to existing nodes in the network"""
        if not self.node_running:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Not connecting to existing nodes - node is not running")
            return
            
        try:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Connecting to existing nodes...")
            
            # Wait for the node to fully initialize before attempting connections
            time.sleep(5)
            
            # Check node 1 availability first
            node1_available = False
            try:
                check_response = requests.get("http://localhost:8001/api/blockchain", timeout=1)
                if check_response.status_code == 200:
                    node1_available = True
            except:
                pass
                
            # Check node 2 availability first
            node2_available = False
            try:
                check_response = requests.get("http://localhost:8002/api/blockchain", timeout=1)
                if check_response.status_code == 200:
                    node2_available = True
            except:
                pass
            
            # Connect to node1 if it's available
            if node1_available:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Connecting to node1 (127.0.0.1:9000)...")
                try:
                    response = requests.post(f"{self.api_base}/network/connect", 
                                          json={"address": "127.0.0.1", "port": 9000},
                                          timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success'):
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Successfully connected to node1")
                        else:
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Failed to connect to node1: {data.get('message', 'Unknown error')}")
                    else:
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Failed to connect to node1: Status {response.status_code}")
                except Exception as e:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error connecting to node1: {str(e)}")
            else:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node1 is not available, skipping connection")
            
            # Connect to node2 if it's available
            if node2_available:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Connecting to node2 (127.0.0.1:9001)...")
                try:
                    response = requests.post(f"{self.api_base}/network/connect", 
                                          json={"address": "127.0.0.1", "port": 9001},
                                          timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success'):
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Successfully connected to node2")
                        else:
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Failed to connect to node2: {data.get('message', 'Unknown error')}")
                    else:
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Failed to connect to node2: Status {response.status_code}")
                except Exception as e:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error connecting to node2: {str(e)}")
            else:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node2 is not available, skipping connection")
            
            # Trigger a blockchain sync only if at least one node is available
            if node1_available or node2_available:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Triggering blockchain synchronization...")
                try:
                    response = requests.post(f"{self.api_base}/network/sync", timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success'):
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Blockchain synchronization successful")
                        else:
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Blockchain synchronization message: {data.get('sync_message', 'Unknown')}")
                    else:
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Blockchain synchronization failed: Status {response.status_code}")
                except Exception as e:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error synchronizing blockchain: {str(e)}")
            else:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] No other nodes available for synchronization")
                
            # Refresh data after synchronization
            self.refresh_data()
            
        except Exception as e:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error connecting to existing nodes: {str(e)}")
    
    def stop_node(self):
        """Stop the running blockchain node"""
        try:
            # Show message
            QMessageBox.information(self, 'Node Stopping', 'Stopping GlobalCoyn node...')
            
            # Log before stopping
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Stopping GlobalCoyn node...")
            
            # Actually stop the process
            if self.node_process:
                # First try graceful termination (SIGTERM)
                self.node_process.terminate()
                
                # Wait a moment to let the process terminate gracefully
                try:
                    self.node_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # If it doesn't terminate in time, force kill it
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node not responding, force killing...")
                    self.node_process.kill()
                
                self.node_process = None
                
                # Log successful stop
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node stopped successfully")
            else:
                # No process running
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] No node process was running")
            
            # Show message
            QMessageBox.information(self, 'Node Stopped', 'GlobalCoyn node has been stopped.')
            
            # Update status
            self.check_node_status()
            
        except Exception as e:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] ERROR: {str(e)}")
            QMessageBox.critical(self, 'Error', f'Failed to stop node: {str(e)}')
    
    def open_dashboard(self):
        """Open the dashboard in a web browser"""
        try:
            import webbrowser
            
            # Get the web port from the configuration
            web_port = self.config.get('web_port', 8001)
            
            # Construct the dashboard URL
            dashboard_url = f"http://localhost:{web_port}"
            
            # Try to open the dashboard
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Opening dashboard at {dashboard_url}")
            
            # Open in default web browser
            webbrowser.open(dashboard_url)
            
        except Exception as e:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error opening dashboard: {str(e)}")
            QMessageBox.critical(self, 'Error', f'Failed to open dashboard: {str(e)}')
    
    def view_log(self):
        """View node log"""
        # Switch to Node page
        self.sidebar.setCurrentRow(5)
    
    def setup_mining_page(self):
        """Set up the mining tab in the application"""
        mining_page = QWidget()
        layout = QVBoxLayout()
        mining_page.setLayout(layout)
        
        # Title
        title_label = QLabel('GlobalCoyn Mining')
        title_label.setFont(QFont('Arial', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Mining configuration group
        config_group = QGroupBox("Mining Configuration")
        config_layout = QVBoxLayout()
        
        # Wallet selection for mining rewards
        wallet_layout = QHBoxLayout()
        wallet_layout.addWidget(QLabel("Mining Reward Address:"))
        self.mining_wallet_selector = QComboBox()
        wallet_layout.addWidget(self.mining_wallet_selector, 1)
        config_layout.addLayout(wallet_layout)
        
        # We'll populate wallet addresses when the page is shown
        self.load_wallet_addresses_for_mining()
        
        # CPU usage slider
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU Usage:"))
        self.cpu_slider = QSlider(Qt.Horizontal)
        self.cpu_slider.setMinimum(10)
        self.cpu_slider.setMaximum(100)
        self.cpu_slider.setValue(50)
        self.cpu_slider.setTickPosition(QSlider.TicksBelow)
        self.cpu_slider.setTickInterval(10)
        cpu_layout.addWidget(self.cpu_slider, 1)
        self.cpu_value_label = QLabel("50%")
        self.cpu_slider.valueChanged.connect(lambda v: self.cpu_value_label.setText(f"{v}%"))
        cpu_layout.addWidget(self.cpu_value_label)
        config_layout.addLayout(cpu_layout)
        
        # Mining controls
        control_layout = QHBoxLayout()
        self.start_mining_btn = QPushButton("Start Mining")
        self.start_mining_btn.clicked.connect(self.start_mining)
        control_layout.addWidget(self.start_mining_btn)
        
        self.stop_mining_btn = QPushButton("Stop Mining")
        self.stop_mining_btn.clicked.connect(self.stop_mining)
        self.stop_mining_btn.setEnabled(False)
        control_layout.addWidget(self.stop_mining_btn)
        
        # About mining button
        self.about_mining_btn = QPushButton("About GCN Mining")
        self.about_mining_btn.clicked.connect(self.show_mining_info)
        control_layout.addWidget(self.about_mining_btn)
        
        config_layout.addLayout(control_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Mining statistics group
        stats_group = QGroupBox("Mining Statistics")
        stats_layout = QGridLayout()
        
        self.mining_status_label = QLabel("Status: Not Mining")
        self.hashrate_label = QLabel("Hashrate: 0 H/s")
        self.blocks_mined_label = QLabel("Blocks Mined: 0")
        self.mining_rewards_label = QLabel("Total Mining Rewards: 0 GCN")
        self.last_block_mined_label = QLabel("Last Block Mined: Never")
        self.current_difficulty_label = QLabel("Current Difficulty: 0")
        
        stats_layout.addWidget(self.mining_status_label, 0, 0)
        stats_layout.addWidget(self.hashrate_label, 0, 1)
        stats_layout.addWidget(self.blocks_mined_label, 1, 0)
        stats_layout.addWidget(self.mining_rewards_label, 1, 1)
        stats_layout.addWidget(self.last_block_mined_label, 2, 0)
        stats_layout.addWidget(self.current_difficulty_label, 2, 1)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Mining log display
        log_group = QGroupBox("Mining Activity Log")
        log_layout = QVBoxLayout()
        
        # This is the actual log widget
        self.mining_log_text = QTextEdit()
        self.mining_log_text.setReadOnly(True)
        log_layout.addWidget(self.mining_log_text)
        
        # Also maintain a list for history
        self.mining_log = []
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Add to pages
        self.pages.addWidget(mining_page)
        
        # Initialize mining variables
        self.is_mining = False
        self.mining_thread = None
        self.mining_process = None
        self.blocks_mined = 0
        self.total_rewards = 0
        
    def load_wallet_addresses_for_mining(self, preserve_selection=True):
        """
        Load wallet addresses into the mining wallet selector
        
        Args:
            preserve_selection: If True, attempt to preserve the currently selected address
        """
        try:
            # Save current selection if needed
            current_address = None
            if preserve_selection and self.mining_wallet_selector.count() > 0:
                current_address = self.mining_wallet_selector.currentText()
                if current_address in ["Please create a wallet first", "Error loading wallets"]:
                    current_address = None
            
            # Clear existing items
            self.mining_wallet_selector.clear()
            
            # Try to get wallet addresses
            if hasattr(self, 'wallet') and self.wallet is not None:
                # Get addresses from existing wallet
                addresses = self.wallet.get_addresses()
                for address in addresses:
                    self.mining_wallet_selector.addItem(address)
                
                # Restore previous selection if possible, otherwise select first address
                if preserve_selection and current_address is not None:
                    # Find index of previously selected address
                    index = self.mining_wallet_selector.findText(current_address)
                    if index >= 0:
                        self.mining_wallet_selector.setCurrentIndex(index)
                    elif self.mining_wallet_selector.count() > 0:
                        self.mining_wallet_selector.setCurrentIndex(0)
                elif self.mining_wallet_selector.count() > 0:
                    self.mining_wallet_selector.setCurrentIndex(0)
            else:
                # Attempt to load wallet dynamically
                try:
                    # Update Python path to include GlobalCoyn directory
                    sys.path.append(os.path.expanduser("~/GlobalCoyn"))
                    
                    # Try to load wallet if it exists
                    try:
                        from core.wallet import Wallet
                    except ImportError:
                        # If that fails, try to copy wallet.py if needed
                        wallet_src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core", "wallet.py")
                        wallet_dest_dir = os.path.join(os.path.expanduser("~/GlobalCoyn"), "core")
                        
                        if os.path.exists(wallet_src) and os.path.exists(wallet_dest_dir):
                            import shutil
                            shutil.copy(wallet_src, os.path.join(wallet_dest_dir, "wallet.py"))
                            print("Copied wallet module - retrying import")
                            
                        # Second attempt after copying
                        from core.wallet import Wallet
                    
                    wallet_dir = os.path.join(os.path.expanduser("~/GlobalCoyn"), "wallet")
                    os.makedirs(wallet_dir, exist_ok=True)
                    wallet_path = os.path.join(wallet_dir, "wallet.enc")
                    
                    if os.path.exists(wallet_path):
                        self.wallet = Wallet(encrypted_storage_path=wallet_path)
                        if self.wallet.load_from_file():
                            # Get addresses from loaded wallet
                            addresses = self.wallet.get_addresses()
                            for address in addresses:
                                self.mining_wallet_selector.addItem(address)
                            
                            # Restore previous selection if possible
                            if preserve_selection and current_address is not None:
                                index = self.mining_wallet_selector.findText(current_address)
                                if index >= 0:
                                    self.mining_wallet_selector.setCurrentIndex(index)
                                elif self.mining_wallet_selector.count() > 0:
                                    self.mining_wallet_selector.setCurrentIndex(0)
                            elif self.mining_wallet_selector.count() > 0:
                                self.mining_wallet_selector.setCurrentIndex(0)
                            
                            # Update UI with wallet info
                            self.update_mining_wallet_balance()
                            return
                except Exception as e:
                    print(f"Error dynamically loading wallet: {str(e)}")
                
                # If we get here, no wallet was loaded
                self.mining_wallet_selector.addItem("Please create a wallet first")
                
        except Exception as e:
            print(f"Error loading wallet addresses for mining: {str(e)}")
            self.mining_wallet_selector.addItem("Error loading wallets")
        
        # Connect the selection change event if not already connected
        # Disconnect first to avoid multiple connections
        try:
            self.mining_wallet_selector.currentIndexChanged.disconnect()
        except:
            pass
        
        self.mining_wallet_selector.currentIndexChanged.connect(self.on_mining_wallet_changed)
    
    def on_mining_wallet_changed(self, index):
        """Handle wallet address selection change in mining tab"""
        if index >= 0 and self.mining_wallet_selector.count() > 0:
            wallet_address = self.mining_wallet_selector.currentText()
            
            # Skip invalid selections
            if wallet_address in ["Please create a wallet first", "Error loading wallets"]:
                return
                
            # Clear mining log to prepare for fresh info
            if hasattr(self, 'mining_log'):
                timestamp = time.strftime('%H:%M:%S')
                self.mining_log.clear()
                self.add_mining_log(f"[{timestamp}] Selected mining wallet: {wallet_address}")
                
            # Update the wallet balance display
            self.update_mining_wallet_balance()
            
            # Refresh the blockchain data
            try:
                response = requests.get(f"{self.api_base}/blockchain", timeout=3)
                if response.status_code == 200:
                    blockchain_data = response.json()
                    chain_length = blockchain_data.get('chain_length', 0)
                    difficulty = blockchain_data.get('difficulty', 4)
                    
                    # Update log with blockchain info
                    self.add_mining_log(f"[{timestamp}] Current blockchain height: {chain_length} blocks")
                    self.add_mining_log(f"[{timestamp}] Current difficulty: {difficulty}")
                    
                    # Check transaction history for this address to count mining rewards
                    try:
                        tx_response = requests.get(f"{self.api_base}/transactions/address/{wallet_address}", timeout=3)
                        if tx_response.status_code == 200:
                            tx_data = tx_response.json()
                            transactions = tx_data.get('transactions', [])
                            
                            # Count mining rewards
                            mining_rewards = 0
                            blocks_mined = 0
                            
                            for tx in transactions:
                                if tx.get('sender') == "0" and tx.get('recipient') == wallet_address:
                                    # This is a mining reward transaction
                                    blocks_mined += 1
                                    mining_rewards += float(tx.get('amount', 0))
                            
                            # Update UI counters
                            self.blocks_mined = blocks_mined
                            self.total_rewards = mining_rewards
                            
                            # Update labels
                            if hasattr(self, 'blocks_mined_label'):
                                self.blocks_mined_label.setText(f"Blocks Mined: {blocks_mined}")
                            if hasattr(self, 'mining_rewards_label'):
                                self.mining_rewards_label.setText(f"Total Mining Rewards: {mining_rewards:.2f} GCN")
                                
                            # Log mining history
                            self.add_mining_log(f"[{timestamp}] Mining history: {blocks_mined} blocks mined")
                            self.add_mining_log(f"[{timestamp}] Total mining rewards: {mining_rewards:.2f} GCN")
                    except Exception as tx_err:
                        print(f"Error loading transaction history: {str(tx_err)}")
            except Exception as e:
                print(f"Error loading blockchain data: {str(e)}")
    
    def update_mining_wallet_balance(self):
        """Update the wallet balance display and mining statistics in the mining page"""
        try:
            if self.mining_wallet_selector.count() > 0 and self.mining_wallet_selector.currentText() != "Please create a wallet first":
                wallet_address = self.mining_wallet_selector.currentText()
                
                # Get updated balance using optimized wallet balance cache
                balance = self.get_wallet_balance(wallet_address)
                
                # Log the updated balance (less frequently to reduce spam)
                timestamp = time.strftime('%H:%M:%S')
                self.add_mining_log(f"[{timestamp}] Updated wallet balance: {balance} GCN")
                
                # Update any UI elements that might display balance
                if hasattr(self, 'wallet_balance_label'):
                    QTimer.singleShot(0, lambda bal=balance: self.wallet_balance_label.setText(f"Wallet Balance: {bal} GCN"))
                
                # Also update mining statistics (with optimized request)
                try:
                    tx_response = self.api_request(f"transactions/address/{wallet_address}", timeout=3)
                    if tx_response and tx_response.status_code == 200:
                        tx_data = tx_response.json()
                        transactions = tx_data.get('transactions', [])
                        
                        # Count mining rewards
                        mining_rewards = 0
                        blocks_mined = 0
                        latest_mining_tx = None
                        latest_mining_timestamp = 0
                        
                        for tx in transactions:
                            if tx.get('sender') == "0" and tx.get('recipient') == wallet_address:
                                # This is a mining reward transaction
                                blocks_mined += 1
                                mining_rewards += float(tx.get('amount', 0))
                                
                                # Track latest mining transaction
                                tx_timestamp = tx.get('timestamp', 0)
                                if tx_timestamp > latest_mining_timestamp:
                                    latest_mining_timestamp = tx_timestamp
                                    latest_mining_tx = tx
                        
                        # Update UI counters
                        self.blocks_mined = blocks_mined
                        self.total_rewards = mining_rewards
                        
                        # Update labels safely via QTimer
                        QTimer.singleShot(0, lambda count=blocks_mined: self.blocks_mined_label.setText(f"Blocks Mined: {count}"))
                        QTimer.singleShot(0, lambda rewards=mining_rewards: self.mining_rewards_label.setText(f"Total Mining Rewards: {rewards:.2f} GCN"))
                        
                        # Update last block mined info if available
                        if latest_mining_timestamp > 0:
                            from datetime import datetime
                            last_mined_time = datetime.fromtimestamp(latest_mining_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                            QTimer.singleShot(0, lambda time=last_mined_time: self.last_block_mined_label.setText(f"Last Block Mined: {time}"))
                except Exception as tx_err:
                    print(f"Error updating mining stats: {str(tx_err)}")
        except Exception as e:
            # Log errors but continue - this is just for UI updates
            print(f"Error updating mining wallet balance: {str(e)}")

    def update_mining_page(self):
        """Update the mining page with latest data"""
        if not self.node_running:
            self.mining_status_label.setText("Status: Node Not Running")
            self.start_mining_btn.setEnabled(False)
            return
        
        # Load wallet addresses again in case they've changed, but preserve the current selection
        self.load_wallet_addresses_for_mining(preserve_selection=True)
        
        # Update blockchain info
        try:
            # Get blockchain status
            response = requests.get(f"{self.api_base}/blockchain", timeout=2)
            if response.status_code == 200:
                blockchain_data = response.json()
                chain_length = blockchain_data.get('chain_length', 0)
                
                # Extract difficulty information
                difficulty_bits = blockchain_data.get('difficulty_bits', 0x1d00ffff)  # Use Bitcoin's default if not available
                difficulty_target = blockchain_data.get('difficulty_target', 0)
                # Calculate estimated hashes needed
                estimated_hashes = 2**256 / difficulty_target if difficulty_target > 0 else 0
                
                # Update difficulty label with more detailed information
                if hasattr(self, 'current_difficulty_label'):
                    diff_text = f"Current Difficulty: {blockchain_data.get('difficulty', 'N/A')}"
                    
                    # Add more technical details for mining enthusiasts
                    if difficulty_bits and difficulty_target:
                        diff_text += f"\nTarget: {difficulty_target:x}"
                        diff_text += f"\nEstimated hashes per block: {estimated_hashes:.2e}"
                    
                    self.current_difficulty_label.setText(diff_text)
                
                # Update the mining log with blockchain info
                if hasattr(self, 'mining_log') and not self.is_mining:
                    timestamp = time.strftime('%H:%M:%S')
                    self.mining_log.clear()
                    self.add_mining_log(f"[{timestamp}] Connected to GlobalCoyn node running on port {self.config.get('web_port', 8003)}")
                    self.add_mining_log(f"[{timestamp}] Current blockchain height: {chain_length} blocks")
                    
                    # Enhanced difficulty logging with Bitcoin-style info
                    difficulty_info = blockchain_data.get('difficulty', 'N/A')
                    self.add_mining_log(f"[{timestamp}] Current difficulty: {difficulty_info}")
                    if difficulty_bits:
                        self.add_mining_log(f"[{timestamp}] Difficulty bits: {hex(difficulty_bits)}")
                    if difficulty_target:
                        self.add_mining_log(f"[{timestamp}] Target threshold: {hex(difficulty_target)}")
                        self.add_mining_log(f"[{timestamp}] Estimated hashes needed: {estimated_hashes:.2e}")
                    
                    self.add_mining_log(f"[{timestamp}] Mempool size: {blockchain_data.get('transactions_in_mempool', 0)} transactions")
                    self.add_mining_log(f"[{timestamp}] Network nodes: {blockchain_data.get('node_count', 0)}")
                    
                # Get selected wallet address - we need this even if mining is running
                wallet_address = ""
                if self.mining_wallet_selector.count() > 0 and self.mining_wallet_selector.currentText() != "Please create a wallet first":
                    wallet_address = self.mining_wallet_selector.currentText()
                    
                    if not self.is_mining:
                        self.add_mining_log(f"[{timestamp}] Mining wallet selected: {wallet_address}")
                    
                    # If we have a wallet address, check its balance
                    try:
                        balance_response = requests.get(f"{self.api_base}/balance/{wallet_address}", timeout=2)
                        if balance_response.status_code == 200:
                            balance_data = balance_response.json()
                            balance = balance_data.get('balance', 0)
                            
                            if not self.is_mining:
                                self.add_mining_log(f"[{timestamp}] Wallet balance: {balance} GCN")
                            
                            # Add a wallet balance label to the mining statistics if it doesn't exist
                            if not hasattr(self, 'wallet_balance_label'):
                                # Find the statistics group
                                stats_group = None
                                for i in range(self.pages.count()):
                                    page = self.pages.widget(i)
                                    for child in page.findChildren(QGroupBox):
                                        if "Mining Statistics" in child.title():
                                            stats_group = child
                                            break
                                
                                if stats_group:
                                    # Add wallet balance label
                                    layout = stats_group.layout()
                                    self.wallet_balance_label = QLabel(f"Wallet Balance: {balance} GCN")
                                    layout.addWidget(self.wallet_balance_label, 3, 0)
                            else:
                                # Update existing label
                                self.wallet_balance_label.setText(f"Wallet Balance: {balance} GCN")
                                
                        # Check transaction history for this address to count mining rewards
                        # IMPORTANT: We do this regardless of mining state to ensure stats are always updated
                        try:
                            tx_response = requests.get(f"{self.api_base}/transactions/address/{wallet_address}", timeout=3)
                            if tx_response.status_code == 200:
                                tx_data = tx_response.json()
                                transactions = tx_data.get('transactions', [])
                                
                                # Count mining rewards
                                mining_rewards = 0
                                blocks_mined = 0
                                latest_mining_tx = None
                                latest_mining_timestamp = 0
                                
                                for tx in transactions:
                                    if tx.get('sender') == "0" and tx.get('recipient') == wallet_address:
                                        # This is a mining reward transaction
                                        blocks_mined += 1
                                        mining_rewards += float(tx.get('amount', 0))
                                        
                                        # Track latest mining transaction
                                        tx_timestamp = tx.get('timestamp', 0)
                                        if tx_timestamp > latest_mining_timestamp:
                                            latest_mining_timestamp = tx_timestamp
                                            latest_mining_tx = tx
                                
                                # Update UI counters - always update regardless of mining state
                                self.blocks_mined = blocks_mined
                                self.total_rewards = mining_rewards
                                
                                # Update labels - always update these to ensure they display correctly
                                self.blocks_mined_label.setText(f"Blocks Mined: {blocks_mined}")
                                self.mining_rewards_label.setText(f"Total Mining Rewards: {mining_rewards:.2f} GCN")
                                
                                # Update hashrate label too if not mining (to ensure it's not stuck at previous value)
                                if not self.is_mining:
                                    self.hashrate_label.setText("Hashrate: 0 H/s")
                                
                                # Add mining history to log
                                if blocks_mined > 0 and not self.is_mining:
                                    self.add_mining_log(f"[{timestamp}] Mining history: {blocks_mined} blocks mined")
                                    self.add_mining_log(f"[{timestamp}] Total mining rewards: {mining_rewards:.2f} GCN")
                                
                                # Always update the last block mined info if we have mining history
                                if latest_mining_timestamp > 0:
                                    # Format the timestamp for display
                                    from datetime import datetime
                                    last_mined_time = datetime.fromtimestamp(latest_mining_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                                    
                                    # Update last block mined label
                                    self.last_block_mined_label.setText(f"Last Block Mined: {last_mined_time}")
                                else:
                                    # No blocks mined yet
                                    self.last_block_mined_label.setText("Last Block Mined: Never")
                        except Exception as tx_err:
                            print(f"Error loading transaction history: {str(tx_err)}")
                            # On error, make sure we at least show something
                            if hasattr(self, 'blocks_mined') and self.blocks_mined > 0:
                                self.blocks_mined_label.setText(f"Blocks Mined: {self.blocks_mined}")
                                self.mining_rewards_label.setText(f"Total Mining Rewards: {self.total_rewards:.2f} GCN")
                            
                    except Exception as balance_err:
                        print(f"Error checking wallet balance: {str(balance_err)}")
                elif not self.is_mining:
                    self.add_mining_log(f"[{timestamp}] No mining wallet selected - please create a wallet first")
                
                if not self.is_mining:
                    self.add_mining_log(f"[{timestamp}] Ready to start mining. Use the controls above to begin.")
        except Exception as e:
            print(f"Error updating mining page: {str(e)}")
        
        # Enable/disable buttons based on mining status
        self.start_mining_btn.setEnabled(not self.is_mining and self.node_running and 
                                         self.mining_wallet_selector.count() > 0 and 
                                         self.mining_wallet_selector.currentText() != "Please create a wallet first" and
                                         self.mining_wallet_selector.currentText() != "Error loading wallets")
        self.stop_mining_btn.setEnabled(self.is_mining and self.node_running)
        
        # Setup periodic balance updates during mining
        if not hasattr(self, 'balance_timer'):
            self.balance_timer = QTimer(self)
            self.balance_timer.timeout.connect(self.update_mining_wallet_balance)
            self.balance_timer.start(30000)  # Update balance every 30 seconds
        
    def start_mining(self):
        """Start the mining process"""
        if not self.node_running:
            QMessageBox.warning(self, "Warning", "Node must be running to start mining")
            return
            
        try:
            # Get the selected wallet address for rewards
            if self.mining_wallet_selector.count() > 0 and self.mining_wallet_selector.currentText() != "Please create a wallet first" and self.mining_wallet_selector.currentText() != "Error loading wallets":
                mining_address = self.mining_wallet_selector.currentText()
            else:
                QMessageBox.warning(self, "Warning", "Please create a wallet and select an address for mining rewards")
                return
            cpu_percentage = self.cpu_slider.value()
            
            # Update UI
            self.mining_status_label.setText("Status: Mining")
            self.start_mining_btn.setEnabled(False)
            self.stop_mining_btn.setEnabled(True)
            self.is_mining = True
            
            # Start wallet balance update timer if not already started
            if hasattr(self, 'balance_timer'):
                if not self.balance_timer.isActive():
                    self.balance_timer.start(30000)  # Update every 30 seconds
            else:
                self.balance_timer = QTimer(self)
                self.balance_timer.timeout.connect(self.update_mining_wallet_balance)
                self.balance_timer.start(30000)  # Update every 30 seconds
            
            # Check initial balance
            self.update_mining_wallet_balance()
            
            # Make request to start mining
            request_data = {
                "miner_address": mining_address,
                "cpu_percentage": cpu_percentage
            }
            
            # Start mining thread
            self.mining_thread = threading.Thread(target=self.mining_worker, args=(mining_address, cpu_percentage))
            self.mining_thread.daemon = True
            self.mining_thread.start()
            
            # Add to log
            timestamp = time.strftime('%H:%M:%S')
            self.add_mining_log(f"[{timestamp}] Mining started with {cpu_percentage}% CPU power")
            self.add_mining_log(f"[{timestamp}] Mining rewards will be sent to {mining_address}")
            self.add_mining_log(f"[{timestamp}] Wallet balance will be updated every 30 seconds")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start mining: {str(e)}")
            self.is_mining = False
            self.mining_status_label.setText("Status: Error")
            self.start_mining_btn.setEnabled(True)
            self.stop_mining_btn.setEnabled(False)
    
    def mining_worker(self, mining_address, cpu_percentage):
        """Background worker that mines blocks using Bitcoin-style proof-of-work"""
        try:
            # Set variables for mining
            target_sleep = 0.001 * (100 - cpu_percentage) / 10  # Adjust CPU usage via sleep time
            start_time = time.time()
            hashes = 0
            last_update = start_time
            
            # Initialize mining session
            session_blocks_mined = 0
            session_rewards = 0.0
            mining_stats_interval = 60  # Only update full stats every 60 seconds to avoid UI lag
            
            # Initialize stats
            self.add_mining_log(f"[{time.strftime('%H:%M:%S')}] ⛏️ Bitcoin-style mining started on address: {mining_address}")
            self.add_mining_log(f"[{time.strftime('%H:%M:%S')}] 💻 CPU usage set to {cpu_percentage}%")
            
            # Quick blockchain status check
            try:
                blockchain_response = requests.get(f"{self.api_base}/blockchain", timeout=2)
                if blockchain_response.status_code == 200:
                    local_chain_length = blockchain_response.json().get('chain_length', 0)
                    self.add_mining_log(f"[{time.strftime('%H:%M:%S')}] Current blockchain height: {local_chain_length}")
                    
                # Register with primary node quickly
                connect_url = f"http://127.0.0.1:8001/api/network/connect"
                requests.post(connect_url, json={
                    "address": "127.0.0.1", 
                    "port": self.config.get('p2p_port', 9002)
                }, timeout=1)
                
                # Start sync in background without waiting
                requests.post(f"{self.api_base}/network/sync", timeout=1)
                self.add_mining_log(f"[{time.strftime('%H:%M:%S')}] 🔄 Connected to network, starting mining...")
                
            except Exception as e:
                self.add_mining_log(f"[{time.strftime('%H:%M:%S')}] Will mine as standalone node")
            
            # Start the actual mining process
            self.add_mining_log(f"[{time.strftime('%H:%M:%S')}] ⛏️ Beginning mining process...")
            
            # Mining loop
            while self.is_mining:
                try:
                    # Update log occasionally
                    current_time = time.time()
                    if current_time - last_update > 5:
                        self.add_mining_log(f"[{time.strftime('%H:%M:%S')}] Mining in progress...")
                        last_update = current_time
                    
                    # Mine a block with short timeout
                    response = requests.post(
                        f"{self.api_base}/mine", 
                        json={"miner_address": mining_address}, 
                        timeout=5
                    )
                    
                    # Process successful mining
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') == 'success':
                            block_data = data.get('block', {})
                            
                            # Get reward amount
                            reward = 0
                            for tx in block_data.get('transactions', []):
                                if tx.get('sender') == '0' and tx.get('recipient') == mining_address:
                                    reward = float(tx.get('amount', 0))
                                    break
                            
                            if reward == 0:
                                reward = 50.0  # Default reward
                            
                            # Update session totals
                            session_blocks_mined += 1
                            session_rewards += reward
                            
                            # Get block details
                            block_index = block_data.get('index', 'unknown')
                            mining_time = block_data.get('mining_time_seconds', 0)
                            
                            # Log success with minimal info to keep UI responsive
                            success_msg = f"[{time.strftime('%H:%M:%S')}] 🎉 BLOCK #{block_index} MINED! (+{reward} GCN, {mining_time:.1f}s)"
                            
                            # Make sure mining success is prominently displayed
                            self.add_mining_log("\n" + "="*50)
                            self.add_mining_log(success_msg)
                            self.add_mining_log("="*50 + "\n")
                            
                            # Force UI update to show the message
                            QApplication.processEvents()
                            
                            # Update UI stats using QTimer for thread safety
                            QTimer.singleShot(0, lambda count=session_blocks_mined: 
                                self.blocks_mined_label.setText(f"Blocks Mined: {count}"))
                            QTimer.singleShot(0, lambda rewards=session_rewards: 
                                self.mining_rewards_label.setText(f"Mining Rewards: {rewards:.2f} GCN"))
                            
                            # Only do full update occasionally to avoid UI lag
                            if time.time() - last_update > mining_stats_interval:
                                # Update using a separate thread
                                threading.Thread(target=self.update_mining_wallet_balance, daemon=True).start()
                                last_update = time.time()
                
                except requests.exceptions.Timeout:
                    # Timeouts are normal during mining - just continue
                    pass
                    
                except Exception as e:
                    # Log error but continue mining
                    if time.time() - last_update > 30:  # Only log occasionally
                        self.add_mining_log(f"[{time.strftime('%H:%M:%S')}] ⚠️ Error: {str(e)[:50]}")
                        last_update = time.time()
                
                # Sleep briefly to prevent CPU overuse and allow UI updates
                time.sleep(0.1)
                
                # Process queued UI events to keep app responsive
                QApplication.processEvents()
                
        except Exception as e:
            # Handle major exceptions
            self.add_mining_log(f"[{time.strftime('%H:%M:%S')}] ❌ Mining stopped: {str(e)}")
            
        finally:
            # Always reset mining status
            QTimer.singleShot(0, lambda: self.mining_status_label.setText("Status: Not Mining"))
            QTimer.singleShot(0, lambda: self.start_mining_btn.setEnabled(True))
            QTimer.singleShot(0, lambda: self.stop_mining_btn.setEnabled(False))
            self.add_mining_log(f"[{time.strftime('%H:%M:%S')}] Mining stopped")
            
    def stop_mining(self):
        """Stop the mining process"""
        self.is_mining = False
        # These UI updates are already in the main thread, so no need for QTimer
        self.mining_status_label.setText("Status: Stopping...")
        self.stop_mining_btn.setEnabled(False)
        timestamp = time.strftime('%H:%M:%S')
        self.add_mining_log(f"[{timestamp}] Stopping mining...")
    
    def update_hashrate(self, hashrate):
        """Update the displayed hashrate"""
        if hashrate < 1000:
            label_text = f"Hashrate: {hashrate:.2f} H/s"
        elif hashrate < 1000000:
            label_text = f"Hashrate: {hashrate/1000:.2f} KH/s"
        else:
            label_text = f"Hashrate: {hashrate/1000000:.2f} MH/s"
        
        # Use QTimer to safely update UI from any thread
        QTimer.singleShot(0, lambda text=label_text: self.hashrate_label.setText(text))
    
    def add_mining_log(self, message):
        """Add message to mining log with improved visibility for important messages"""
        # Add timestamp if not already present
        if not message.startswith('['):
            message = f"[{time.strftime('%H:%M:%S')}] {message}"
            
        # Make sure we have the mining_log list
        if not hasattr(self, 'mining_log'):
            self.mining_log = []
            
        # Check if mining_log_text exists before using it
        has_mining_log_text = hasattr(self, 'mining_log_text') and self.mining_log_text is not None
            
        # Make success messages more visible
        if "BLOCK" in message and "MINED" in message:
            # Add extra spacing and highlighting for successful mining
            highlighted_message = f"\n{'=' * 40}\n{message}\n{'=' * 40}\n"
            self.mining_log.append(highlighted_message)
            
            # Force scroll to bottom to show the message if the text widget exists
            if has_mining_log_text:
                self.mining_log_text.append(highlighted_message)
                try:
                    self.mining_log_text.verticalScrollBar().setValue(
                        self.mining_log_text.verticalScrollBar().maximum()
                    )
                except Exception as e:
                    print(f"Error scrolling: {e}")
            
            # Also show a system notification if possible
            try:
                # For macOS notifications
                if os.name == 'posix':
                    os.system(f'osascript -e \'display notification "{message}" with title "Block Mined!"\'')
            except Exception as e:
                print(f"Error showing notification: {e}")
        else:
            # Regular message
            self.mining_log.append(message)
            if has_mining_log_text:
                self.mining_log_text.append(message)
            
        # Only keep the latest 100 messages for performance
        if len(self.mining_log) > 100:
            self.mining_log.pop(0)
        
    def show_mining_info(self):
        """Show information about mining on the GlobalCoyn network"""
        info_text = """
<h2>GlobalCoyn Mining Explained</h2>

<h3>What is Mining?</h3>
<p>Mining is the process of creating new blocks on the GlobalCoyn blockchain. As a miner, you dedicate your computer's processing power to solve complex mathematical puzzles. When you successfully solve a puzzle, you get to create a new block of transactions and receive newly created GCN as a reward.</p>

<h3>How Mining Works on GlobalCoyn</h3>
<p>GlobalCoyn uses a Proof-of-Work consensus mechanism similar to Bitcoin's original approach. When you mine:</p>
<ol>
    <li>Your computer collects pending transactions from the network</li>
    <li>It creates a candidate block with these transactions</li>
    <li>It searches for a valid "nonce" value that, when combined with other block data, produces a block hash that meets the network's difficulty requirements</li>
    <li>If successful, your block is submitted to the network and you receive the mining reward</li>
</ol>

<h3>Difficulty Calculation</h3>
<p>The GlobalCoyn network adjusts mining difficulty every 2,016 blocks (approximately every two weeks at 10-minute block intervals). The algorithm compares the actual time taken to mine these blocks with the expected time (2,016 × 10 minutes). If blocks were mined too quickly, difficulty increases; if too slowly, difficulty decreases.</p>

<p>The difficulty target determines how many leading zeros a valid block hash must have. The more zeros required, the more difficult it is to find a valid hash.</p>

<h3>Block Rewards and Halving</h3>
<p>When you mine a block, you receive a reward of newly created GCN. The initial block reward is 50 GCN. However, this reward is cut in half every 210,000 blocks (approximately every four years), in an event called "halving".</p>

<p>Reward schedule:</p>
<ul>
    <li>Blocks 0-209,999: 50 GCN per block</li>
    <li>Blocks 210,000-419,999: 25 GCN per block</li>
    <li>Blocks 420,000-629,999: 12.5 GCN per block</li>
    <li>And so on, halving every 210,000 blocks</li>
</ul>

<p>This halving mechanism ensures that the total supply of GCN is limited to 21 million, creating scarcity similar to Bitcoin.</p>

<h3>Transaction Fees</h3>
<p>In addition to the block reward, miners also collect transaction fees from the transactions included in their blocks. As block rewards decrease over time due to halvings, transaction fees will become an increasingly important source of income for miners.</p>

<h3>Mining with the GlobalCoyn App</h3>
<p>The GlobalCoyn desktop application allows you to mine directly with your computer's CPU, similar to how Bitcoin mining worked in its early days. You can adjust your CPU usage with the slider to balance mining performance with system responsiveness.</p>

<p>Happy mining!</p>
"""
        
        # Create and display the info dialog
        info_dialog = QMessageBox(self)
        info_dialog.setWindowTitle("About GlobalCoyn Mining")
        info_dialog.setTextFormat(Qt.RichText)
        info_dialog.setText(info_text)
        info_dialog.setIcon(QMessageBox.Information)
        info_dialog.exec_()
    
    def discover_network_peers(self):
        """
        Discover and connect to peers in the GlobalCoyn network.
        
        Uses the node_discovery module to find peers and connect to them.
        This method is called automatically in production mode after the node starts.
        """
        try:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Starting discovery of network peers...")
            
            # First, ensure node is properly initialized
            if not self.wait_for_node_ready(max_attempts=5):
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Warning: Node may not be fully ready, but continuing with peer discovery")
                
            # Get peers using the node discovery module
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Finding GlobalCoyn network peers...")
            peers = self.node_discovery.discover_peers()
            
            if peers:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Found {len(peers)} potential peers in the network")
                
                # Connect to discovered peers via our node's API
                connected = self.node_discovery.connect_to_peers(self.api_base)
                
                if connected:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Successfully connected to {len(connected)} peers")
                    for peer in connected:
                        address = peer.get('address', peer.get('host', ''))
                        port = peer.get('p2p_port', peer.get('port', 9000))
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Connected to peer: {address}:{port}")
                else:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Could not connect to any discovered peers")
                    # Fall back to bootstrap nodes
                    self.connect_to_bootstrap_nodes()
            else:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] No peers found during discovery")
                # Fall back to bootstrap nodes
                self.connect_to_bootstrap_nodes()
                
            # After discovery, try to sync with the network
            self.start_blockchain_sync()
                
        except Exception as e:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error discovering network peers: {str(e)}")
            # Fall back to bootstrap nodes
            self.connect_to_bootstrap_nodes()
    
    def connect_to_bootstrap_nodes(self):
        """
        Connect directly to bootstrap nodes in production mode.
        
        This is a fallback method when peer discovery fails.
        """
        try:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Connecting to GlobalCoyn bootstrap nodes...")
            
            # Get bootstrap nodes from config
            bootstrap_nodes = self.config.get('bootstrap_nodes', [])
            
            if not bootstrap_nodes:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] No bootstrap nodes configured")
                return
                
            connected_count = 0
            
            # Connect to each bootstrap node
            for node in bootstrap_nodes:
                try:
                    host, port_str = node.split(':')
                    p2p_port = 9000  # Default P2P port
                    
                    # P2P port is typically 1000 more than web port in our setup
                    # If they provided web port in config, convert to P2P port
                    web_port = int(port_str)
                    if web_port < 9000:  # If it's a web port (8001-8999)
                        p2p_port = web_port + 1000  # Convert to P2P port (9001-9999)
                    else:
                        p2p_port = web_port  # Already a P2P port
                    
                    # Connect via API
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Connecting to bootstrap node: {host}:{p2p_port}")
                    connect_url = f"{self.api_base}/network/connect"
                    
                    response = requests.post(connect_url, 
                                           json={"address": host, "port": p2p_port},
                                           timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success', False):
                            connected_count += 1
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Successfully connected to bootstrap node: {host}:{p2p_port}")
                        else:
                            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Failed to connect to bootstrap node: {host}:{p2p_port}")
                    else:
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error connecting to bootstrap node: {response.status_code}")
                        
                except Exception as e:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error connecting to bootstrap node {node}: {str(e)}")
            
            # Report results
            if connected_count > 0:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Connected to {connected_count} bootstrap nodes")
                # Sync blockchain after connecting
                self.start_blockchain_sync()
            else:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Could not connect to any bootstrap nodes")
                
        except Exception as e:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error connecting to bootstrap nodes: {str(e)}")
    
    def connect_to_local_nodes(self):
        """
        Connect to local development nodes (Node 1 and Node 2).
        
        This method is used in development mode to connect to other locally running nodes.
        """
        try:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Connecting to local GlobalCoyn nodes...")
            
            # First, ensure node is properly initialized
            if not self.wait_for_node_ready(max_attempts=3):
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Warning: Node may not be fully ready, but continuing with local connection")
            
            # Connect to Node 1 (localhost:9000)
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Attempting to connect to Node 1 (localhost:9000)...")
            try:
                connect_url = f"{self.api_base}/network/connect"
                response = requests.post(connect_url, 
                                       json={"address": "localhost", "port": 9000},
                                       timeout=3)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success', False):
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Successfully connected to Node 1")
                    else:
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Failed to connect to Node 1: {data.get('message', 'Unknown error')}")
                else:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error connecting to Node 1: {response.status_code}")
            except Exception as e:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error connecting to Node 1: {str(e)}")
            
            # Connect to Node 2 (localhost:9001)
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Attempting to connect to Node 2 (localhost:9001)...")
            try:
                connect_url = f"{self.api_base}/network/connect"
                response = requests.post(connect_url, 
                                       json={"address": "localhost", "port": 9001},
                                       timeout=3)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success', False):
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Successfully connected to Node 2")
                    else:
                        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Failed to connect to Node 2: {data.get('message', 'Unknown error')}")
                else:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error connecting to Node 2: {response.status_code}")
            except Exception as e:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error connecting to Node 2: {str(e)}")
            
            # Trigger blockchain sync after connecting
            self.start_blockchain_sync()
                
        except Exception as e:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error connecting to local nodes: {str(e)}")
    
    def wait_for_node_ready(self, max_attempts=5, delay=2):
        """
        Wait for the node to be fully initialized before connecting to peers.
        
        Args:
            max_attempts (int): Maximum number of attempts to check node readiness
            delay (int): Delay in seconds between attempts
            
        Returns:
            bool: True if node is ready, False otherwise
        """
        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Waiting for node to initialize...")
        
        for attempt in range(max_attempts):
            try:
                # Check if node API is responding
                response = requests.get(f"{self.api_base}/blockchain", timeout=delay)
                
                if response.status_code == 200:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node is ready (attempt {attempt+1}/{max_attempts})")
                    return True
                    
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node not ready yet (attempt {attempt+1}/{max_attempts}): Status {response.status_code}")
            except Exception as e:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node not ready yet (attempt {attempt+1}/{max_attempts}): {str(e)}")
                
            # Wait before next attempt
            time.sleep(delay)
            
        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Node readiness check timed out after {max_attempts} attempts")
        return False
    
    def start_blockchain_sync(self):
        """
        Start blockchain synchronization after connecting to peers.
        """
        try:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Starting blockchain synchronization...")
            
            # Mark sync as in progress
            self.sync_in_progress = True
            self.sync_start_time = time.time()
            
            # Trigger a sync via API
            response = requests.get(f"{self.api_base}/network/sync", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Blockchain synchronization started successfully")
                    # Update UI to show sync in progress
                    if hasattr(self, 'sync_status_label'):
                        self.sync_status_label.setText("Sync Status: In Progress")
                        self.sync_status_label.setStyleSheet("color: orange; font-weight: bold;")
                else:
                    self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Blockchain synchronization failed to start: {data.get('message', 'Unknown error')}")
            else:
                self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error starting blockchain synchronization: {response.status_code}")
                
        except Exception as e:
            self.log_display.append(f"[{time.strftime('%H:%M:%S')}] Error starting blockchain synchronization: {str(e)}")
            self.sync_in_progress = False

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