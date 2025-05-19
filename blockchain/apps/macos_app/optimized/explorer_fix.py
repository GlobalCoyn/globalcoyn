"""
This module contains improved code for the Block Explorer functionality
in the GlobalCoyn macOS app.

Usage:
1. Copy the update_explorer_page and try_fetch_chain_data methods into macos_app_fixed.py
2. These methods provide better error handling when nodes are offline
"""

def update_explorer_page(self):
    """Update the block explorer page with real blockchain data - with improved error handling"""
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
    
    # Create a container for status messages that can be styled
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
                
    # First check if our node is running and has data
    if self.node_running and self.chain_data and 'chain' in self.chain_data and self.chain_data['chain']:
        # Data available from our node
        print(f"Found {len(self.chain_data['chain'])} blocks in chain data")
        
        # Clear status container
        status_container.deleteLater()
        
        # Get all blocks from the chain
        blocks = self.chain_data['chain']
        
        # Add a source label
        source_label = QLabel(f"Data from Node {self.config.get('node_number', 3)}")
        source_label.setAlignment(Qt.AlignCenter)
        source_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(source_label)
        
        # Show blocks
        self.display_blocks(blocks, layout)
    else:
        # Try alternative data sources with better error handling
        
        # Update the checking label
        checking_label.setText("Local node not available. Checking other nodes...")
        QApplication.processEvents()  # Update UI immediately
        
        # Track if we successfully get data
        data_found = False
        
        # Try to get data from existing node1 (with better error handling)
        node1_data = self.try_fetch_chain_data(1, "http://localhost:8001/api/chain")
        if node1_data:
            # Clear status container
            status_container.deleteLater()
            
            # Add source label
            source_label = QLabel("Data from Node 1")
            source_label.setAlignment(Qt.AlignCenter)
            source_label.setStyleSheet("color: blue; font-weight: bold;")
            layout.addWidget(source_label)
            
            # Show blocks
            self.display_blocks(node1_data, layout)
            data_found = True
        
        # If node1 didn't work, try node2
        elif not data_found:
            node2_data = self.try_fetch_chain_data(2, "http://localhost:8002/api/chain")
            if node2_data:
                # Clear status container
                status_container.deleteLater()
                
                # Add source label
                source_label = QLabel("Data from Node 2")
                source_label.setAlignment(Qt.AlignCenter)
                source_label.setStyleSheet("color: blue; font-weight: bold;")
                layout.addWidget(source_label)
                
                # Show blocks
                self.display_blocks(node2_data, layout)
                data_found = True
        
        # If we still don't have data, show a helpful error message
        if not data_found:
            # Update the status container with more helpful information
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
            elif self.node_running and not self.chain_data.get('chain'):
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