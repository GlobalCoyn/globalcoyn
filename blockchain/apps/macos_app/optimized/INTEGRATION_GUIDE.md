# GlobalCoyn macOS App - Integration Guide

This guide describes how to integrate the optimized components into the main application.

## 1. Replace the Main Application File

The simplest approach is to directly replace the original `macos_app_fixed.py` with our optimized version:

```bash
cp macos_app_optimized.py ../macos_app_fixed.py
```

## 2. Selective Integration

If you prefer to selectively integrate only specific fixes, follow these steps:

### Connection Backoff Implementation

1. Import and use the connection backoff mechanism:
   ```python
   # Import at the top of macos_app.py
   from optimized.connection_backoff import ConnectionManager
   
   # Initialize it near the beginning of the class
   def __init__(self, ...):
       # Existing initialization code
       # ...
       
       # Initialize connection manager for API requests
       self.connection_manager = ConnectionManager()
   ```

2. Modify API requests to use backoff logic:
   ```python
   def api_request(self, endpoint, method="GET", data=None, timeout=5):
       """Make an API request with connection backoff"""
       url = f"http://localhost:{self.node_web_port}/{endpoint}"
       
       # Check if we should attempt the connection based on backoff status
       if not self.connection_manager.should_attempt_connection(url):
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
           return None
   ```

3. Replace direct API calls with the new `api_request` method throughout the codebase

### Optimized Wallet Balance Calculation

1. Import and initialize the wallet cache:
   ```python
   # Import at the top of macos_app.py
   from optimized.wallet_cache import WalletCache
   
   # Initialize in __init__ after blockchain is set up
   def __init__(self, ...):
       # After blockchain initialization
       # ...
       
       # Initialize wallet cache for faster balance calculations
       self.wallet_cache = None
       if hasattr(self, 'blockchain') and self.blockchain:
           self.wallet_cache = WalletCache(self.blockchain)
   ```

2. Modify balance calculation methods:
   ```python
   def get_wallet_balance(self, address):
       """Get wallet balance using the optimized cache"""
       if not self.wallet_cache:
           # Fall back to standard calculation
           return self._original_get_wallet_balance(address)
       
       # Use the cache for better performance
       balance_info = self.wallet_cache.get_balance(address)
       return balance_info["balance"]
   
   # Rename the original method to use as fallback
   def _original_get_wallet_balance(self, address):
       # Original balance calculation code here
       pass
   ```

### Rate-Limited Logging

1. Import and use the rate-limited logger:
   ```python
   # Import at the top of file
   from optimized.rate_limited_logger import RateLimitedLogger
   
   # Replace the standard logger initialization
   # logger = logging.getLogger("gcn_macapp")
   logger = RateLimitedLogger("gcn_macapp")
   ```

2. Update the NodeManager to use rate-limited logging too:
   ```python
   # In node_manager.py
   from optimized.rate_limited_logger import RateLimitedLogger
   
   # Replace
   # logger = logging.getLogger("NodeManager")
   logger = RateLimitedLogger("NodeManager")
   ```

### Enhanced Node Synchronization

1. Import the optimized sync module:
   ```python
   # At the top of the file
   try:
       # Try to import optimized node sync
       from optimized.improved_node_sync_optimized import enhance_globalcoyn_networking as enhanced_networking
       USING_OPTIMIZED = True
   except ImportError:
       # Fall back to original if not available
       from network.improved_node_sync import enhance_globalcoyn_networking as enhanced_networking
       USING_OPTIMIZED = False
   ```

2. Use the enhanced networking module when initializing blockchain:
   ```python
   # After initializing the GlobalCoyn instance
   if hasattr(self, 'blockchain') and self.blockchain:
       # Apply enhanced networking with backoff
       self.blockchain = enhanced_networking(self.blockchain)
       
       # Log which version we're using
       if USING_OPTIMIZED:
           logger.info("Using optimized networking with connection backoff")
       else:
           logger.warning("Using standard networking (optimized version not found)")
   ```

### Block Explorer Improvements

1. Open `macos_app_fixed.py` in your editor
2. Find the `update_explorer_page` method
3. Replace it with the version from `explorer_fix.py`
4. Add the new `try_fetch_chain_data` method from `explorer_fix.py`

### API Connection Fixes

1. Open `macos_app_fixed.py` in your editor
2. Add the helper methods from `api_connection_fix.py`
3. Replace API calls in the following methods:
   - `update_mining_wallet_balance`
   - `refresh_dashboard`
   - `update_sender_balance`
   - `send_transaction`
   - `refresh_wallet_data`

4. Replace direct error-prone API calls with the `safe_api_request` function

### Timer Optimization

1. In the `__init__` method, modify the timer intervals:
   ```python
   # Set up timer to check node status - REDUCED FREQUENCY
   self.timer = QTimer(self)
   self.timer.timeout.connect(self.check_node_status)
   self.timer.start(15000)  # Check every 15 seconds (increased from 5s)
   
   # Data refresh timer with reduced frequency
   self.data_timer = QTimer(self)
   self.data_timer.timeout.connect(self.refresh_data)
   self.data_timer.start(30000)  # Refresh data every 30 seconds (increased from 10s)
   ```

2. Add the lightweight status check timer:
   ```python
   # Add a new timer for lightweight status check
   self.quick_status_timer = QTimer(self)
   self.quick_status_timer.timeout.connect(self.quick_status_check)
   self.quick_status_timer.start(5000)  # Quick status check every 5 seconds
   ```

3. Add the `quick_status_check` method from `macos_app_optimized.py`

## 3. Testing

After integrating the changes, test the application thoroughly:

1. Test the application when nodes are offline
2. Test the Block Explorer with and without nodes running
3. Test wallet balance retrieval with repeated checks (verify caching works)
4. Test starting and stopping nodes
5. Monitor logs to verify reduced error messages 
6. Check that connection retries have proper backoff (node 2 on port 8002 errors should be reduced)
7. Verify the application doesn't lag when running for extended periods
8. Test sync functionality with multiple nodes

## 4. Troubleshooting

If you encounter issues after integration:

### Connection Issues
- Check that the connection backoff isn't too aggressive
- Verify endpoint URLs are correctly formatted
- Temporarily set `connection_manager.max_retry_interval` to a lower value

### Wallet Cache Issues
- Clear the cache with `self.wallet_cache = WalletCache(self.blockchain)` if balances seem incorrect
- Enable debug logging to see cache hits/misses
- Check that all transaction types are handled correctly

### Logging Issues
- If important logs are being suppressed, adjust thresholds in `rate_limited_logger.py`
- Change log levels temporarily to DEBUG for more visibility
- Check log file permissions

## 5. Performance Monitoring

To verify the optimizations are working correctly, monitor:

1. Log file size - Should grow much more slowly
2. CPU usage - Should be lower, especially during idle periods
3. Memory usage - May increase slightly due to caching
4. UI responsiveness - Should remain responsive during sync
5. Time to calculate balances - Should be significantly faster for repeat checks