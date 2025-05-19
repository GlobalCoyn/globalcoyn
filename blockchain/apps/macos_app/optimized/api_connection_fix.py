"""
This module contains improved code for API connection handling 
in the GlobalCoyn macOS app.

These functions handle common connection issues and provide better
error handling for balance and blockchain API requests.
"""

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

def get_wallet_balance(self, address, fallback=True):
    """
    Get wallet balance with proper error handling and fallbacks.
    
    Args:
        address (str): Wallet address to check
        fallback (bool): Whether to try alternative nodes on failure
        
    Returns:
        float: Wallet balance or 0 on error
    """
    if not address:
        return 0
        
    # First try the primary node
    result = self.safe_api_request(f"balance/{address}")
    if result is not None and 'balance' in result:
        return float(result.get('balance', 0))
        
    # If primary node failed and fallbacks are enabled, try alternative nodes
    if fallback and self.error_count > 0:
        # Try node 1
        try:
            response = requests.get(f"http://localhost:8001/api/balance/{address}", timeout=1)
            if response.status_code == 200:
                data = response.json()
                if 'balance' in data:
                    return float(data.get('balance', 0))
        except:
            pass
            
        # Try node 2
        try:
            response = requests.get(f"http://localhost:8002/api/balance/{address}", timeout=1)
            if response.status_code == 200:
                data = response.json()
                if 'balance' in data:
                    return float(data.get('balance', 0))
        except:
            pass
    
    # If all attempts failed, return 0
    return 0

def update_mining_wallet_balance_improved(self):
    """
    Update the wallet balance display with proper error handling.
    This is an improved version of the update_mining_wallet_balance method.
    """
    try:
        if self.mining_wallet_selector.count() > 0 and self.mining_wallet_selector.currentText() != "Please create a wallet first":
            wallet_address = self.mining_wallet_selector.currentText()
            
            # Get balance using the improved method
            balance = self.get_wallet_balance(wallet_address)
            timestamp = time.strftime('%H:%M:%S')
            
            # Log with appropriate message based on whether we got a valid balance
            if balance > 0:
                self.add_mining_log(f"[{timestamp}] Updated wallet balance: {balance} GCN")
            else:
                self.add_mining_log(f"[{timestamp}] Wallet balance: {balance} GCN (may be zero or unavailable)")
            
            # Update any UI elements that might display balance
            if hasattr(self, 'wallet_balance_label'):
                QTimer.singleShot(0, lambda bal=balance: self.wallet_balance_label.setText(f"Wallet Balance: {bal} GCN"))
            
            # Get transaction history with fallbacks
            tx_data = self.safe_api_request(f"transactions/address/{wallet_address}", timeout=3)
            if tx_data and 'transactions' in tx_data:
                transactions = tx_data.get('transactions', [])
                
                # Process mining rewards as before
                # (The rest of the original function remains the same)
                
    except Exception as e:
        # Log errors but continue - this is just for UI updates
        print(f"Error updating mining wallet balance: {str(e)}")
        # Don't crash - just display what we can
        if hasattr(self, 'wallet_balance_label'):
            self.wallet_balance_label.setText("Wallet Balance: Unavailable")