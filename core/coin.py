"""
Coin module for the GlobalCoyn blockchain.
Defines the Coin class for managing cryptocurrency units.
"""
from typing import Dict, Any, Optional
import logging

class Coin:
    """
    Represents a GCN coin with amount and owner information.
    """
    def __init__(self, amount: float = 0, owner: Optional[str] = None):
        """
        Initialize a new coin.
        
        Args:
            amount: Initial coin amount
            owner: Wallet address that owns this coin
        """
        self.amount = round(float(amount), 8)  # Store with 8 decimal precision
        self.owner = owner  # Wallet address that owns this coin
        self._validate_amount()
    
    def _validate_amount(self) -> None:
        """
        Validate that coin amount is within acceptable range.
        
        Raises:
            ValueError: If amount is negative or exceeds maximum supply
        """
        if self.amount < 0:
            raise ValueError("Coin amount cannot be negative")
        if self.amount > 1_000_000_000:  # 1 billion max supply
            raise ValueError("Coin amount exceeds maximum supply")
    
    def add(self, amount: float) -> None:
        """
        Add amount to coin.
        
        Args:
            amount: Amount to add
        """
        self.amount = round(self.amount + float(amount), 8)
        self._validate_amount()
    
    def subtract(self, amount: float) -> None:
        """
        Subtract amount from coin.
        
        Args:
            amount: Amount to subtract
        """
        self.amount = round(self.amount - float(amount), 8)
        self._validate_amount()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert coin to dictionary for serialization.
        
        Returns:
            Dictionary representation of the coin
        """
        return {
            "amount": format(self.amount, '.8f'),
            "owner": self.owner
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Coin':
        """
        Create coin from dictionary.
        
        Args:
            data: Dictionary containing coin data
            
        Returns:
            A Coin object
        """
        return cls(float(data.get("amount", 0)), data.get("owner"))
    
    def __str__(self) -> str:
        """String representation of the coin."""
        return f"GCN({self.amount})"
    
    def __repr__(self) -> str:
        """Representation of the coin."""
        return self.__str__()

class CoinManager:
    """
    Manages a collection of coins for a wallet or blockchain.
    """
    def __init__(self):
        """Initialize an empty coin manager."""
        self.coins = []
        self.logger = logging.getLogger("coin_manager")
    
    def add_coin(self, coin: Coin) -> None:
        """
        Add a coin to the collection.
        
        Args:
            coin: Coin to add
        """
        if not coin or coin.amount <= 0:
            return
            
        # Try to combine with existing coins for the same owner
        for existing_coin in self.coins:
            if existing_coin.owner == coin.owner:
                existing_coin.add(coin.amount)
                self.logger.info(f"Added {coin.amount} to existing coin, new total: {existing_coin.amount}")
                return
                
        # If no matching coin found, add as new
        self.coins.append(coin)
        self.logger.info(f"Added new coin with amount {coin.amount} for {coin.owner}")
    
    def get_balance(self, owner: str) -> float:
        """
        Get total balance for a coin owner.
        
        Args:
            owner: Wallet address to check balance for
            
        Returns:
            Total balance for the owner
        """
        return sum(coin.amount for coin in self.coins if coin.owner == owner)
    
    def transfer(self, from_owner: str, to_owner: str, amount: float) -> bool:
        """
        Transfer coins between owners.
        
        Args:
            from_owner: Sender wallet address
            to_owner: Recipient wallet address
            amount: Amount to transfer
            
        Returns:
            True if transfer succeeded, False otherwise
        """
        # Validate amount
        if amount <= 0:
            self.logger.warning("Cannot transfer negative or zero amount")
            return False
            
        # Check sender balance
        sender_balance = self.get_balance(from_owner)
        if sender_balance < amount:
            self.logger.warning(f"Insufficient balance: {sender_balance} < {amount}")
            return False
            
        # Find coins to update
        sender_coins = [coin for coin in self.coins if coin.owner == from_owner]
        
        # Subtract from sender
        remaining = amount
        for coin in sender_coins:
            if remaining <= 0:
                break
                
            if coin.amount <= remaining:
                # Use the entire coin
                remaining -= coin.amount
                coin.amount = 0
            else:
                # Use part of the coin
                coin.subtract(remaining)
                remaining = 0
                
        # Remove any zero-amount coins
        self.coins = [coin for coin in self.coins if coin.amount > 0]
        
        # Add to recipient
        recipient_coin = Coin(amount, to_owner)
        self.add_coin(recipient_coin)
        
        self.logger.info(f"Transferred {amount} from {from_owner} to {to_owner}")
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert coin collection to dictionary for serialization.
        
        Returns:
            Dictionary representation of the coin collection
        """
        return {
            "coins": [coin.to_dict() for coin in self.coins]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoinManager':
        """
        Create coin manager from dictionary.
        
        Args:
            data: Dictionary containing coin manager data
            
        Returns:
            A CoinManager object
        """
        manager = cls()
        for coin_data in data.get("coins", []):
            coin = Coin.from_dict(coin_data)
            manager.add_coin(coin)
            
        return manager