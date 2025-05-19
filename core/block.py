"""
Block module for the GlobalCoyn blockchain.
Handles the creation and validation of blockchain blocks.
"""
import hashlib
import time
from typing import List, Dict, Any

from transaction import Transaction

class Block:
    """
    Represents a block in the blockchain.
    Includes block header and list of transactions.
    """
    def __init__(self, index: int, previous_hash: str, timestamp: float, 
                 transactions: List[Transaction], nonce: int, difficulty_bits: int):
        """
        Initialize a new block.
        
        Args:
            index: Block height in the blockchain
            previous_hash: Hash of the previous block
            timestamp: Block creation time
            transactions: List of transactions included in this block
            nonce: Proof-of-work nonce value
            difficulty_bits: Mining difficulty in compact bits format
        """
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions
        self.nonce = nonce
        self.difficulty_bits = difficulty_bits  # Store difficulty in bits format (like Bitcoin)
        self.merkle_root = self.calculate_merkle_root()
        self.hash = self.calculate_hash()
        
    def calculate_merkle_root(self) -> str:
        """
        Calculate the Merkle root of all transactions in the block.
        
        Returns:
            Hex string representing the Merkle root
        """
        if not self.transactions:
            return hashlib.sha256("".encode()).hexdigest()
        
        transaction_hashes = [
            hashlib.sha256(str(tx.to_dict()).encode()).hexdigest()
            for tx in self.transactions
        ]
        
        # Build the Merkle tree
        while len(transaction_hashes) > 1:
            # If odd number of hashes, duplicate the last one
            if len(transaction_hashes) % 2 != 0:
                transaction_hashes.append(transaction_hashes[-1])
            
            new_hashes = []
            for i in range(0, len(transaction_hashes), 2):
                combined = transaction_hashes[i] + transaction_hashes[i + 1]
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)
            
            transaction_hashes = new_hashes
        
        return transaction_hashes[0]

    def calculate_hash(self) -> str:
        """
        Calculate double SHA-256 hash of the block header.
        This follows Bitcoin's approach of applying SHA-256 twice.
        
        Returns:
            Hex string hash of the block
        """
        # Create block header components
        block_header = (
            f"{self.index}{self.previous_hash}{self.timestamp}"
            f"{self.merkle_root}{self.nonce}{self.difficulty_bits}"
        ).encode()
        
        # Apply SHA-256 twice (double-SHA256)
        first_hash = hashlib.sha256(block_header).digest()  # Get binary digest
        second_hash = hashlib.sha256(first_hash).hexdigest() # Get hex digest
        return second_hash

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert block to dictionary for serialization.
        
        Returns:
            Dictionary representation of the block
        """
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "difficulty_bits": self.difficulty_bits,
            "merkle_root": self.merkle_root,
            "hash": self.hash
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Block':
        """
        Create a Block object from a dictionary.
        
        Args:
            data: Dictionary containing block data
            
        Returns:
            A Block object
        """
        # Convert transaction dictionaries to Transaction objects
        transactions = []
        for tx_data in data.get("transactions", []):
            transaction = Transaction.from_dict(tx_data)
            transactions.append(transaction)
        
        # Create Block object
        block = cls(
            index=data.get("index"),
            previous_hash=data.get("previous_hash"),
            timestamp=data.get("timestamp"),
            transactions=transactions,
            nonce=data.get("nonce"),
            difficulty_bits=data.get("difficulty_bits")
        )
        
        # Override calculated values with stored values if available
        if "merkle_root" in data:
            block.merkle_root = data.get("merkle_root")
            
        if "hash" in data:
            block.hash = data.get("hash")
            
        return block
        
    def is_valid(self) -> bool:
        """
        Verify the block's integrity.
        
        Returns:
            True if the block is valid, False otherwise
        """
        # Verify block hash
        if self.hash != self.calculate_hash():
            return False
            
        # Verify merkle root
        if self.merkle_root != self.calculate_merkle_root():
            return False
            
        # Verify all transactions
        for tx in self.transactions:
            if not tx.is_valid() and not tx.is_coinbase():
                return False
                
        return True