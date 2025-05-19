"""
This module contains an improved block explorer with pagination for GlobalCoyn.

It adds pagination to handle very large blockchains (tens of thousands of blocks)
by only loading and displaying a subset of blocks at a time.
"""

def update_explorer_page_with_pagination(self):
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
    if not hasattr(self, 'block_page_number'):
        self.block_page_number = 0
    if not hasattr(self, 'blocks_per_page'):
        self.blocks_per_page = 20  # Default blocks per page
    if not hasattr(self, 'total_blocks'):
        self.total_blocks = 0
                    
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
            
        # Add pagination information to the source label
        source_label = QLabel(f"{source_text} (Showing blocks {start_idx} to {end_idx-1} of {self.total_blocks})")
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
        
        # Page indicator
        page_label = QLabel(f"Page {self.block_page_number + 1} of {total_pages}")
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
        
        # Get current page slice of blocks - use reversed order to show newest first
        page_blocks = full_chain[self.total_blocks - end_idx:self.total_blocks - start_idx]
        page_blocks.reverse()  # Newest first
        
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
            
            # Page indicator
            bottom_page_label = QLabel(f"Page {self.block_page_number + 1} of {total_pages}")
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