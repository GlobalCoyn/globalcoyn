"""
Transaction module for the GlobalCoyn blockchain.
Handles the creation, validation and management of blockchain transactions.
"""
import hashlib
import time
import base64
from typing import Optional, Dict, Any

class Transaction:
    """
    Represents a blockchain transaction for transferring funds between addresses.
    """
    def __init__(self, sender: str, recipient: str, amount: float, fee: float, 
                 signature: Optional[str] = None):
        """
        Initialize a new transaction.
        
        Args:
            sender: The sender's wallet address
            recipient: The recipient's wallet address
            amount: The amount to transfer
            fee: The transaction fee
            signature: Digital signature of the transaction (optional)
        """
        self.sender = sender
        self.recipient = recipient
        self.amount = float(amount)
        self.fee = float(fee)
        self.signature = signature
        self.timestamp = time.time()
        self.tx_hash = None
        self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Calculate the transaction hash using its properties.
        
        Returns:
            A hex string hash of the transaction
        """
        # Create a hash of transaction data
        tx_content = f"{self.sender}{self.recipient}{self.amount}{self.fee}{self.timestamp}"
        self.tx_hash = hashlib.sha256(tx_content.encode()).hexdigest()
        return self.tx_hash

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert transaction to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the transaction
        """
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "fee": self.fee,
            "signature": self.signature,
            "timestamp": self.timestamp,
            "tx_hash": self.tx_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """
        Create a Transaction object from a dictionary.
        
        Args:
            data: Dictionary containing transaction data
            
        Returns:
            A Transaction object
        """
        tx = cls(
            sender=data.get("sender"),
            recipient=data.get("recipient"),
            amount=float(data.get("amount", 0)),
            fee=float(data.get("fee", 0)),
            signature=data.get("signature")
        )
        
        # Set timestamp from data if provided
        if "timestamp" in data:
            tx.timestamp = float(data.get("timestamp"))
            
        # Recalculate hash or use provided hash
        if "tx_hash" in data:
            tx.tx_hash = data.get("tx_hash")
        else:
            tx.calculate_hash()
            
        return tx
    
    def is_coinbase(self) -> bool:
        """
        Check if this is a coinbase transaction (mining reward).
        
        Returns:
            True if this is a coinbase transaction, False otherwise
        """
        return self.sender == "0"
    
    def is_valid(self) -> bool:
        """
        Basic validation of transaction properties.
        Signature verification should be done separately with wallet.
        
        Returns:
            True if the transaction has valid properties, False otherwise
        """
        # Coinbase transactions are always valid
        if self.is_coinbase():
            return True
            
        # Basic validation
        if not self.sender or not self.recipient:
            return False
            
        if self.amount <= 0 or self.fee < 0:
            return False
            
        if not self.signature:
            return False
            
        return True