"""
Wallet balance caching for GlobalCoyn blockchain
Optimizes wallet balance calculations by caching results
"""
import time
import threading
import logging
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logger = logging.getLogger("wallet_cache")

class WalletCache:
    """
    Caches wallet balance information to avoid rescanning the entire blockchain
    every time a balance check is requested.
    """
    
    def __init__(self, blockchain_instance):
        """
        Initialize wallet cache
        
        Args:
            blockchain_instance: The GlobalCoyn blockchain instance
        """
        self.blockchain = blockchain_instance
        self.wallet_data: Dict[str, Dict[str, Any]] = {}
        self.last_scanned_block = 0
        self.cache_lock = threading.RLock()
        
        # Constants
        self.FULL_RESCAN_INTERVAL = 3600  # Perform full rescan every hour
        self.MAX_CACHE_AGE = 30  # Consider cache stale after 30 seconds
        
        # Last full scan timestamp
        self.last_full_scan = 0
        
        # Start background scanning thread
        self.scanner_thread = threading.Thread(target=self._background_scanner, daemon=True)
        self.scanner_thread.start()
    
    def _background_scanner(self):
        """Background thread that keeps the cache updated"""
        while True:
            try:
                # Sleep for a bit to avoid constant scanning
                time.sleep(15)
                
                # Check if we need to update the cache
                now = time.time()
                if now - self.last_full_scan > self.FULL_RESCAN_INTERVAL:
                    # Time for a full rescan
                    logger.info("Performing full wallet cache update")
                    self.update_all_wallets()
                    self.last_full_scan = now
                else:
                    # Incremental update for any blocks we haven't processed
                    self.incremental_update()
            except Exception as e:
                logger.error(f"Error in background scanner: {str(e)}")
    
    def update_all_wallets(self):
        """Perform a full update of all wallet balances"""
        with self.cache_lock:
            # Get a list of all wallets we're currently tracking
            wallet_addresses = list(self.wallet_data.keys())
            
            # Reset cache to start fresh
            self.wallet_data = {}
            self.last_scanned_block = 0
            
            # Scan all addresses we were previously tracking
            for address in wallet_addresses:
                self.get_balance(address)
    
    def incremental_update(self):
        """
        Incrementally update the cache with new blocks
        """
        with self.cache_lock:
            chain_length = len(self.blockchain.chain)
            
            # If we're already up to date, nothing to do
            if self.last_scanned_block >= chain_length:
                return
            
            # Get all addresses we're tracking
            addresses = list(self.wallet_data.keys())
            if not addresses:
                # Nothing to do if we're not tracking any addresses
                self.last_scanned_block = chain_length
                return
            
            # Process only new blocks
            logger.info(f"Updating wallet cache with blocks {self.last_scanned_block+1} to {chain_length}")
            
            # Process each block since the last one we scanned
            for i in range(self.last_scanned_block, chain_length):
                block = self.blockchain.chain[i]
                
                # Scan each transaction in the block for tracked addresses
                for tx in block.transactions:
                    # Check if transaction involves any tracked address
                    if tx.sender in self.wallet_data or tx.recipient in self.wallet_data:
                        # Process this transaction for every tracked address
                        self._process_transaction(tx, addresses)
            
            # Update last scanned block
            self.last_scanned_block = chain_length
            
            # Update last check time for all wallets
            now = time.time()
            for address in self.wallet_data:
                self.wallet_data[address]["last_check"] = now
    
    def _process_transaction(self, tx, addresses: List[str]):
        """
        Process a single transaction for all tracked addresses
        
        Args:
            tx: The transaction to process
            addresses: List of addresses to check against
        """
        # Process for each tracked address
        for address in addresses:
            if address not in self.wallet_data:
                continue
                
            wallet = self.wallet_data[address]
            
            # Update sent amount if this wallet is the sender
            if tx.sender == address:
                wallet["sent"] += tx.amount + tx.fee
                wallet["transactions"].append(tx)
            
            # Update received amount if this wallet is the recipient
            if tx.recipient == address:
                wallet["received"] += tx.amount
                wallet["transactions"].append(tx)
    
    def get_balance(self, address: str) -> Dict[str, Any]:
        """
        Get balance information for a wallet address with caching
        
        Args:
            address: The wallet address to check
            
        Returns:
            Dict[str, Any]: Wallet balance information
        """
        with self.cache_lock:
            now = time.time()
            chain_length = len(self.blockchain.chain)
            
            # Check if we have cached data for this address
            if address in self.wallet_data:
                wallet_info = self.wallet_data[address]
                cache_age = now - wallet_info["last_check"]
                
                # If the cache is fresh and we've scanned all blocks, use it
                if cache_age < self.MAX_CACHE_AGE and self.last_scanned_block >= chain_length:
                    logger.debug(f"Using cached balance for {address}")
                    return {
                        "address": address,
                        "balance": wallet_info["received"] - wallet_info["sent"],
                        "total_received": wallet_info["received"],
                        "total_sent": wallet_info["sent"],
                        "transaction_count": len(wallet_info["transactions"]),
                        "cached": True
                    }
            
            # We need to scan the blockchain for this address
            logger.info(f"Calculating balance for address {address}")
            
            # Initialize wallet data if needed
            if address not in self.wallet_data:
                self.wallet_data[address] = {
                    "received": 0.0,
                    "sent": 0.0,
                    "transactions": [],
                    "last_check": now
                }
            else:
                # Reset the data for a fresh scan
                self.wallet_data[address] = {
                    "received": 0.0,
                    "sent": 0.0,
                    "transactions": [],
                    "last_check": now
                }
            
            # Get a reference to the wallet data
            wallet = self.wallet_data[address]
            
            # Scan the blockchain
            logger.info(f"Scanning {chain_length} blocks for transactions related to {address}")
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    # Add to sent amount if this wallet is the sender
                    if tx.sender == address:
                        wallet["sent"] += tx.amount + tx.fee
                        wallet["transactions"].append(tx)
                    
                    # Add to received amount if this wallet is the recipient
                    if tx.recipient == address:
                        wallet["received"] += tx.amount
                        wallet["transactions"].append(tx)
            
            # Update last scanned block if this is a full scan
            if self.last_scanned_block < chain_length:
                self.last_scanned_block = chain_length
            
            # Return the calculated balance
            return {
                "address": address,
                "balance": wallet["received"] - wallet["sent"],
                "total_received": wallet["received"],
                "total_sent": wallet["sent"],
                "transaction_count": len(wallet["transactions"]),
                "cached": False
            }
    
    def get_transactions(self, address: str) -> List[Dict[str, Any]]:
        """
        Get transactions for a wallet address
        
        Args:
            address: The wallet address to check
            
        Returns:
            List[Dict[str, Any]]: List of transactions
        """
        # Make sure balance is calculated and cached
        self.get_balance(address)
        
        with self.cache_lock:
            if address not in self.wallet_data:
                return []
            
            # Convert transactions to dictionaries
            tx_list = []
            for tx in self.wallet_data[address]["transactions"]:
                tx_dict = {
                    "sender": tx.sender,
                    "recipient": tx.recipient,
                    "amount": tx.amount,
                    "fee": tx.fee,
                    "timestamp": tx.timestamp,
                    "type": tx.transaction_type,
                    "is_outgoing": tx.sender == address
                }
                tx_list.append(tx_dict)
            
            # Sort by timestamp (newest first)
            tx_list.sort(key=lambda x: x["timestamp"], reverse=True)
            return tx_list