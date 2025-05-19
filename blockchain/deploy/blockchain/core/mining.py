"""
Mining functionality for the GlobalCoyn blockchain.
Handles proof-of-work mining, reward calculations, and difficulty adjustments.
"""
import time
import logging
from typing import List, Optional, Dict, Any, Tuple

from transaction import Transaction
from block import Block
from mempool import Mempool
from utils import bits_to_target, target_to_bits, calculate_target_adjustment

class Miner:
    """
    Handles blockchain mining operations including proof-of-work and reward calculations.
    """
    # Mining constants
    MAX_SUPPLY = 21_000_000  # Maximum supply of GCN
    INITIAL_REWARD = 50  # Initial mining reward
    HALVING_INTERVAL = 210_000  # Number of blocks between reward halvings
    TARGET_BLOCK_TIME = 600  # Target time between blocks in seconds (10 minutes)
    DIFFICULTY_ADJUSTMENT_INTERVAL = 2016  # Number of blocks between difficulty adjustments
    DEVELOPMENT_ADJUSTMENT_INTERVAL = 50  # More frequent adjustments for development
    
    # Easier mining difficulty for development
    INITIAL_BITS = 0x2000ffff  # Much easier initial difficulty
    MAX_TARGET = 0x00007FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # Very easy target
    
    def __init__(self):
        """Initialize the miner with default settings."""
        self.logger = logging.getLogger("miner")
        self.bits = self.INITIAL_BITS
        self.target = bits_to_target(self.bits)
        
    def calculate_reward(self, chain_length: int) -> float:
        """
        Calculate the current mining reward based on halving schedule.
        
        Args:
            chain_length: Current blockchain length
            
        Returns:
            Current mining reward amount
        """
        halvings = chain_length // self.HALVING_INTERVAL
        return self.INITIAL_REWARD / (2 ** halvings)
        
    def adjust_difficulty(self, blockchain_data: Dict[str, Any]) -> None:
        """
        Adjust mining difficulty based on block time history.
        
        Args:
            blockchain_data: Dict containing chain and other info
        """
        chain = blockchain_data.get("chain", [])
        
        # For initial mining - keep difficulty very low for the first 100 blocks
        if len(chain) < 100:
            # Ensure we're using the easiest setting for the first 100 blocks
            if self.target < self.MAX_TARGET:
                self.logger.info(f"First 100 blocks: Setting to easiest difficulty for development")
                self.target = self.MAX_TARGET
                self.bits = target_to_bits(self.target)
            return
        
        # Regular difficulty adjustment for development
        blocks_since_adjustment = len(chain) % self.DEVELOPMENT_ADJUSTMENT_INTERVAL
        
        if blocks_since_adjustment == 0 and len(chain) > self.DEVELOPMENT_ADJUSTMENT_INTERVAL:
            # Get last adjustment block and calculate time difference
            last_adjustment_block = chain[-self.DEVELOPMENT_ADJUSTMENT_INTERVAL]
            expected_time = self.TARGET_BLOCK_TIME * self.DEVELOPMENT_ADJUSTMENT_INTERVAL
            actual_time = chain[-1].get("timestamp") - last_adjustment_block.get("timestamp")
            
            # Calculate new target value
            new_target = calculate_target_adjustment(
                expected_time, 
                actual_time, 
                self.target, 
                self.MAX_TARGET
            )
            
            # Update difficulty
            self.target = new_target
            self.bits = target_to_bits(new_target)
        
        # Handle difficulty at halving events
        halvings = len(chain) // self.HALVING_INTERVAL
        if len(chain) % self.HALVING_INTERVAL == 0 and len(chain) > 0 and halvings > 0:
            # Very small increase for development - only 10% harder per halving
            difficulty_multiplier = 1.1  
            new_target = int(self.target / difficulty_multiplier)
            
            self.logger.info(f"Halving event! Small difficulty increase by {difficulty_multiplier}x")
            self.logger.info(f"Halving adjustment: Old target={self.target}, New target={new_target}")
            
            # Update difficulty
            self.target = new_target
            self.bits = target_to_bits(new_target)
    
    def mine_block(self, chain: List[Dict[str, Any]], mempool: Mempool, 
                  miner_address: str, max_tx: int = 100) -> Optional[Block]:
        """
        Mine a new block with proof-of-work.
        
        Args:
            chain: Current blockchain
            mempool: Transaction mempool
            miner_address: Address to receive mining reward
            max_tx: Maximum transactions to include
            
        Returns:
            Newly mined block if successful, None otherwise
        """
        # Check if we've reached max supply
        # This is a simplified check, actual implementation would need to calculate total supply
        if len(chain) >= self.MAX_SUPPLY:
            self.logger.info("Maximum supply reached, no more mining rewards")
            return None
        
        # Prepare block transactions
        block_transactions = []
        
        # Add mining reward transaction
        reward = self.calculate_reward(len(chain))
        reward_tx = Transaction("0", miner_address, reward, 0)
        block_transactions.append(reward_tx)
        
        # Add transactions from mempool (sorted by fee)
        mempool_txs = mempool.get_transactions(max_tx)
        block_transactions.extend(mempool_txs)
        
        # Create new block with current timestamp
        new_block = Block(
            index=len(chain),
            previous_hash=chain[-1].get("hash") if chain else "0" * 64,
            timestamp=time.time(),
            transactions=block_transactions,
            nonce=0,
            difficulty_bits=self.bits
        )
        
        # Log mining attempt
        self.logger.info(f"Starting mining with difficulty bits: {hex(self.bits)}, target: {hex(self.target)}")
        
        # Proof of work - increment nonce until hash meets difficulty
        mining_start = time.time()
        while True:
            new_block.nonce += 1
            if new_block.nonce % 100000 == 0:  # Log progress
                self.logger.info(f"Mining in progress: tried {new_block.nonce} nonces so far...")
                
            # Calculate new hash
            new_block.hash = new_block.calculate_hash()
            
            # Check if hash meets difficulty requirement
            hash_int = int(new_block.hash, 16)
            if hash_int <= self.target:
                # Found valid hash
                mining_duration = time.time() - mining_start
                self.logger.info(f"Found valid hash after {new_block.nonce} attempts in {mining_duration:.2f} seconds")
                self.logger.info(f"Block hash: {new_block.hash}")
                break
        
        # Remove mined transactions from mempool
        for tx in mempool_txs:
            mempool.remove_transaction(tx)
        
        # Block successfully mined
        return new_block
    
    def get_mining_info(self) -> Dict[str, Any]:
        """
        Get current mining information and statistics.
        
        Returns:
            Dictionary with mining statistics
        """
        return {
            "difficulty_bits": self.bits,
            "target": self.target,
            "max_target": self.MAX_TARGET,
            "current_difficulty": self.MAX_TARGET / self.target,  # Relative difficulty
            "next_halving": self.HALVING_INTERVAL,
            "target_block_time": self.TARGET_BLOCK_TIME
        }