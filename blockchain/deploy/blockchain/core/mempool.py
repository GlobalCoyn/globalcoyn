"""
Memory pool (mempool) management for the GlobalCoyn blockchain.
Handles transaction queue for pending transactions not yet included in blocks.
"""
import logging
from typing import List, Dict, Optional, Callable

from transaction import Transaction
from utils import validate_address_format

class Mempool:
    """
    Memory pool for managing pending transactions.
    """
    def __init__(self):
        """Initialize an empty mempool."""
        self.transactions: List[Transaction] = []
        self.logger = logging.getLogger("mempool")
    
    def add_transaction(self, transaction: Transaction, balance_checker: Callable[[str], float]) -> bool:
        """
        Add a transaction to the mempool after validation.
        
        Args:
            transaction: The transaction to add
            balance_checker: Function to check address balance
            
        Returns:
            True if transaction was added, False otherwise
        """
        # Basic transaction validation
        if not transaction.is_valid():
            self.logger.warning(f"Transaction validation failed: invalid transaction format")
            return False
            
        # Skip balance check for coinbase transactions
        if transaction.is_coinbase():
            self.transactions.append(transaction)
            return True
            
        # Address format validation
        if not validate_address_format(transaction.sender) or not validate_address_format(transaction.recipient):
            self.logger.warning(f"Transaction validation failed: invalid address format")
            return False
            
        # Balance validation
        sender_balance = balance_checker(transaction.sender)
        self.logger.info(f"Checking balance for {transaction.sender}: {sender_balance} vs needed {transaction.amount + transaction.fee}")
        
        if sender_balance < (transaction.amount + transaction.fee):
            self.logger.warning(f"Transaction validation failed: insufficient balance. Has: {sender_balance}, Needs: {transaction.amount + transaction.fee}")
            return False
        
        # Check for duplicate transactions
        for existing_tx in self.transactions:
            if (existing_tx.sender == transaction.sender and 
                existing_tx.recipient == transaction.recipient and 
                existing_tx.amount == transaction.amount and
                existing_tx.timestamp == transaction.timestamp):
                self.logger.warning(f"Transaction validation failed: duplicate transaction")
                return False
        
        self.transactions.append(transaction)
        self.logger.info(f"Added transaction to mempool: {transaction.tx_hash} - {transaction.amount} coins from {transaction.sender} to {transaction.recipient}")
        return True
    
    def get_transactions(self, limit: int = None) -> List[Transaction]:
        """
        Get transactions from the mempool, sorted by fee.
        
        Args:
            limit: Maximum number of transactions to return
            
        Returns:
            List of transactions sorted by fee (highest first)
        """
        # Sort by fee, highest first
        sorted_transactions = sorted(self.transactions, key=lambda tx: tx.fee, reverse=True)
        
        # Return limited number if specified
        if limit and limit > 0:
            return sorted_transactions[:limit]
            
        return sorted_transactions
    
    def remove_transaction(self, transaction: Transaction) -> bool:
        """
        Remove a transaction from the mempool.
        
        Args:
            transaction: The transaction to remove
            
        Returns:
            True if transaction was removed, False if not found
        """
        if transaction in self.transactions:
            self.transactions.remove(transaction)
            return True
        return False
    
    def remove_transactions(self, transactions: List[Transaction]) -> int:
        """
        Remove multiple transactions from the mempool.
        
        Args:
            transactions: List of transactions to remove
            
        Returns:
            Number of transactions removed
        """
        removed_count = 0
        for tx in transactions:
            if self.remove_transaction(tx):
                removed_count += 1
                
        return removed_count
    
    def get_transaction_by_hash(self, tx_hash: str) -> Optional[Transaction]:
        """
        Find a transaction in the mempool by its hash.
        
        Args:
            tx_hash: Transaction hash to search for
            
        Returns:
            Transaction if found, None otherwise
        """
        for tx in self.transactions:
            if tx.tx_hash == tx_hash:
                return tx
        return None
    
    def get_address_transactions(self, address: str) -> List[Transaction]:
        """
        Get all transactions in the mempool related to an address.
        
        Args:
            address: Wallet address to get transactions for
            
        Returns:
            List of transactions involving the address
        """
        return [tx for tx in self.transactions 
                if tx.sender == address or tx.recipient == address]
    
    def clear(self) -> None:
        """Clear all transactions from the mempool."""
        self.transactions = []
    
    def size(self) -> int:
        """
        Get the number of transactions in the mempool.
        
        Returns:
            Number of transactions
        """
        return len(self.transactions)