import hashlib
import time
from typing import List, Optional
import math
from decimal import Decimal
import os
import sys
import json
import logging
# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import price oracle directly from the same directory
from price_oracle import PRICE_ORACLE

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("blockchain.log"),
        logging.StreamHandler()
    ]
)

class Transaction:
    def __init__(self, sender: str, recipient: str, amount: float, fee: float, 
                 signature: Optional[str] = None, transaction_type: str = "TRANSFER", 
                 price: Optional[float] = None):
        self.sender = sender
        self.recipient = recipient  # Buyer's wallet address for purchases
        self.amount = float(amount)  # Store as float
        self.fee = float(fee)  # Store as float
        self.signature = signature
        self.timestamp = time.time()
        self.transaction_type = transaction_type
        self.price = float(price) if price is not None else None  # Store as float
        # Calculate total cost for purchase and sell transactions
        if transaction_type in ["PURCHASE", "SELL"] and price is not None:
            self.total_cost = round(self.amount * self.price, 2)  # Round to 2 decimal places
        else:
            self.total_cost = None

    def to_dict(self):
        return {
            "sender": self.sender,
            "recipient": self.recipient,  # Buyer's wallet address
            "amount": self.amount,  # COON quantity
            "fee": self.fee,
            "signature": self.signature,
            "timestamp": self.timestamp,
            "transaction_type": self.transaction_type,
            "price": self.price,  # Price per COON
            "total_cost": self.total_cost  # Total purchase cost
        }

class Block:
    def __init__(self, index: int, previous_hash: str, timestamp: float, 
                 transactions: List[Transaction], nonce: int, difficulty_bits: int):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions
        self.nonce = nonce
        self.difficulty_bits = difficulty_bits  # Store difficulty in bits format (like Bitcoin)
        # For compatibility with existing code that expects difficulty_target
        self._difficulty_target = difficulty_bits  # Alias for backward compatibility
        self.merkle_root = self.calculate_merkle_root()
        self.hash = self.calculate_hash()
        
    @property
    def difficulty_target(self):
        """Compatibility property for existing code that uses difficulty_target"""
        return self._difficulty_target

    def calculate_merkle_root(self) -> str:
        if not self.transactions:
            return hashlib.sha256("".encode()).hexdigest()
        
        transaction_hashes = [
            hashlib.sha256(str(tx.to_dict()).encode()).hexdigest()
            for tx in self.transactions
        ]
        
        while len(transaction_hashes) > 1:
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

    def to_dict(self) -> dict:
        """Convert block to dictionary for serialization"""
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "difficulty_bits": self.difficulty_bits,
            "difficulty_target": self.difficulty_target,  # Include for backward compatibility
            "merkle_root": self.merkle_root,
            "hash": self.hash
        }

class Blockchain:
    MAX_SUPPLY = 21_000_000  # Maximum supply of GCN
    INITIAL_REWARD = 50  # Initial mining reward
    HALVING_INTERVAL = 210_000  # Number of blocks between reward halvings
    TARGET_BLOCK_TIME = 600  # Target time between blocks in seconds (10 minutes)
    DIFFICULTY_ADJUSTMENT_INTERVAL = 2016  # Number of blocks between difficulty adjustments
    
    # Modified difficulty constants for development - MUCH easier than Bitcoin
    # This makes mining feasible on laptops for development and testing
    INITIAL_BITS = 0x2000ffff  # Much easier initial difficulty (more leading zeros allowed in target)
    MAX_TARGET = 0x00007FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # Very easy target for development
    
    def __init__(self):
        self.chain: List[Block] = []
        self.mempool: List[Transaction] = []
        self.bits = self.INITIAL_BITS  # Current difficulty in bits format
        self.target = self.bits_to_target(self.bits)  # Current difficulty as target
        self.create_genesis_block()
        
    def bits_to_target(self, bits: int) -> int:
        """Convert compact bits representation to target threshold"""
        # Extract the bytes
        size = bits >> 24
        word = bits & 0x007fffff
        
        # Convert to target
        if size <= 3:
            return word >> (8 * (3 - size))
        else:
            return word << (8 * (size - 3))
    
    def target_to_bits(self, target: int) -> int:
        """Convert a target threshold to compact bits representation"""
        # Find the size (number of bytes)
        size = (target.bit_length() + 7) // 8
        
        # Convert to bits format
        if size <= 3:
            bits = (target & 0xffffff) << (8 * (3 - size))
            return bits | size << 24
        else:
            bits = target >> (8 * (size - 3))
            return bits | size << 24

    def create_genesis_block(self, fixed_timestamp=1619520000.0, fixed_nonce=42):
        """Create the genesis block with no previous hash"""
        genesis_block = Block(
            index=0,
            previous_hash="0" * 64,
            timestamp=fixed_timestamp,
            transactions=[],
            nonce=fixed_nonce,
            difficulty_bits=self.bits
        )
        self.chain.append(genesis_block)

    def get_mining_reward(self) -> float:
        """Calculate the current mining reward based on halving schedule"""
        halvings = len(self.chain) // self.HALVING_INTERVAL
        return self.INITIAL_REWARD / (2 ** halvings)

    def get_current_supply(self) -> float:
        """Calculate the current total supply of COON"""
        mined_supply = 0
        purchased_supply = 0
        sold_supply = 0
        
        # Detailed transaction tracking - count each transaction type
        mining_tx_count = 0
        purchase_tx_count = 0
        sell_tx_count = 0
        
        # Analyze all blocks to count supply
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == "0":  # Mining reward transaction
                    mined_supply += tx.amount
                    mining_tx_count += 1
                elif tx.transaction_type == "PURCHASE":
                    # Count purchase transactions (market sells to user)
                    purchased_supply += tx.amount
                    purchase_tx_count += 1
                elif tx.transaction_type == "SELL":
                    # Count sell transactions (user sells back to market)
                    sold_supply += tx.amount
                    sell_tx_count += 1
        
        # Calculate total supply as sum of mined and purchased coins, minus sold coins
        # This correctly accounts for coins added via mining and purchases, and removed via sells
        total_supply = mined_supply + purchased_supply - sold_supply
        
        # Output detailed supply statistics
        print(f"Supply statistics:")
        print(f"- Total blocks in chain: {len(self.chain)}")
        print(f"- Mining transactions: {mining_tx_count} (total: {mined_supply})")
        print(f"- Purchase transactions: {purchase_tx_count} (total: {purchased_supply})")
        print(f"- Sell transactions: {sell_tx_count} (total: {sold_supply})")
        print(f"- Total circulating supply: {total_supply}")
        
        # IMPORTANT: If blockchain has no transactions yet (empty or only genesis block),
        # but we know there are transactions in mempool, use a minimum supply amount.
        # This ensures UI displays something reasonable during development.
        if total_supply <= 0 and len(self.mempool) > 0:
            # Count mempool transactions that would increase supply
            mempool_purchase_amount = sum(tx.amount for tx in self.mempool if tx.transaction_type == "PURCHASE")
            if mempool_purchase_amount > 0:
                total_supply = mempool_purchase_amount
                print(f"Using mempool purchase amount for supply: {total_supply}")
            else:
                # Fallback minimum supply to ensure market data displays properly
                total_supply = 1000
                print(f"Using fallback minimum supply: {total_supply}")
        
        # Manually track from app launch if there are still issues with supply calculation
        # Minimum amount should be at least 100 for UI development 
        if total_supply <= 0:
            from datetime import datetime
            now = datetime.now()
            # Generate increasing supply based on time since launch
            # (for development purposes only)
            minutes_since_midnight = (now.hour * 60) + now.minute
            dev_supply = 100 + (minutes_since_midnight * 10)  # 100 base + 10 per minute
            total_supply = dev_supply
            print(f"Using time-based development supply: {total_supply}")
        
        return total_supply

    def add_transaction_to_mempool(self, transaction: Transaction) -> bool:
        """Add a new transaction to the mempool"""
        # Basic transaction validation
        if transaction.amount <= 0:
            print(f"Transaction validation failed: amount must be positive (got {transaction.amount})")
            return False
            
        # Allow transactions from special addresses without balance check
        # - "0": mining rewards or system adjustments
        # - "MARKET": market operations (e.g. PURCHASE transactions)
        if transaction.sender not in ["0", "MARKET"]:
            # ALL transaction types require balance validation except ADJUSTMENT
            # Even SELL transactions must have sufficient balance
            if transaction.transaction_type != "ADJUSTMENT":
                sender_balance = self.get_balance(transaction.sender)
                print(f"Checking balance for {transaction.sender}: {sender_balance} vs needed {transaction.amount + transaction.fee}")
                print(f"Transaction type: {transaction.transaction_type}")
                
                if sender_balance < (transaction.amount + transaction.fee):
                    print(f"Transaction validation failed: insufficient balance. Has: {sender_balance}, Needs: {transaction.amount + transaction.fee}")
                    return False
            else:
                # Only ADJUSTMENT transactions bypass balance check
                print(f"BYPASS: Allowing ADJUSTMENT transaction without balance check")
        else:
            print(f"Special address {transaction.sender} - bypassing balance check")
        
        # Additional validation for purchase and sell transactions
        if transaction.transaction_type in ["PURCHASE", "SELL"]:
            # Get current dynamic market price
            current_price = float(PRICE_ORACLE.calculate_market_price(self))
            transaction_price = transaction.price  # Already float from property

            # Allow a small price tolerance (1%) to account for price changes during submission
            price_tolerance = current_price * 0.01
            
            # Compare prices as floats with tolerance
            if transaction_price is None or abs(transaction_price - current_price) > price_tolerance:
                print(f"Transaction price mismatch: {transaction_price} vs {current_price}")
                # Update the transaction price to match current price
                transaction.price = current_price
                if transaction.transaction_type == "PURCHASE":
                    transaction.total_cost = round(transaction.amount * current_price, 2)
                elif transaction.transaction_type == "SELL":
                    # For sell transactions, calculate the total fiat value
                    transaction.total_cost = round(transaction.amount * current_price, 2)
            
            # Additional validation based on transaction type
            if transaction.transaction_type == "PURCHASE":
                # For purchases, sender must be MARKET
                if transaction.sender != "MARKET":
                    print(f"Invalid purchase: sender {transaction.sender} is not MARKET")
                    return False
                    
                # Add order to price oracle for market tracking as a sell (market sells to user)
                PRICE_ORACLE.add_order(
                    float(current_price),  # Ensure price is float
                    float(transaction.amount),  # Ensure amount is float
                    "SELL"  # Market sells to user
                )
            elif transaction.transaction_type == "SELL":
                # For sells, recipient must be MARKET
                if transaction.recipient != "MARKET":
                    print(f"Invalid sell: recipient {transaction.recipient} is not MARKET")
                    return False
                    
                # For sells, we need to verify the sender has enough balance
                sender_balance = self.get_balance(transaction.sender)
                if sender_balance < transaction.amount:
                    print(f"Insufficient balance for sell: {sender_balance} < {transaction.amount}")
                    return False
                    
                # Add order to price oracle for market tracking as a buy (market buys from user)
                PRICE_ORACLE.add_order(
                    float(current_price),  # Ensure price is float
                    float(transaction.amount),  # Ensure amount is float
                    "BUY"  # Market buys from user
                )
            else:
                # Unknown transaction type
                print(f"Unknown transaction type: {transaction.transaction_type}")
                return False
        
        self.mempool.append(transaction)
        return True

    def get_address_transactions(self, address: str) -> list:
        """Get all transactions for a given address"""
        import traceback
        try:
            transactions = []
            
            # Check address format
            if not address or len(address) < 26 or len(address) > 35:
                print(f"WARNING: Address format may be invalid: {address}")
            
            # Loop through all blocks and transactions for this address
            for block_idx, block in enumerate(self.chain):
                for tx_idx, tx in enumerate(block.transactions):
                    try:
                        # Include transaction if address is sender or recipient
                        if tx.sender == address or tx.recipient == address:
                            # Include metadata about which block this transaction is in
                            tx_info = tx.to_dict()
                            tx_info['block_index'] = block_idx
                            tx_info['block_hash'] = block.hash
                            transactions.append(tx)
                    except Exception as tx_error:
                        print(f"Error processing transaction in block {block_idx}, tx {tx_idx}: {str(tx_error)}")
            
            # Also include pending transactions from mempool
            for tx in self.mempool:
                if tx.sender == address or tx.recipient == address:
                    transactions.append(tx)
            
            return transactions
        except Exception as e:
            print(f"Error getting address transactions: {str(e)}")
            traceback.print_exc()
            return []  # Return empty list on error
            
    def get_balance(self, address: str) -> float:
        """Get the balance of a given address"""
        import traceback
        try:
            print(f"Calculating balance for {address}")
            balance = 0
            tx_count = 0
            
            # Check address format
            if not address or len(address) < 26 or len(address) > 35:
                print(f"WARNING: Address format may be invalid: {address}")
            
            # Loop through all blocks and transactions for this address
            print(f"Checking {len(self.chain)} blocks for transactions related to {address}")
            
            # First, check how many transactions are on the blockchain in total
            total_tx_count = sum(len(block.transactions) for block in self.chain)
            print(f"Total transactions in the entire blockchain: {total_tx_count}")
            
            # Track specific transaction types for debugging
            transfer_credits = 0  # TRANSFER transactions where this address receives
            transfer_debits = 0   # TRANSFER transactions where this address sends
            adjustment_credits = 0  # ADJUSTMENT transactions where this address receives
            adjustment_debits = 0   # ADJUSTMENT transactions where this address sends
            
            for block_idx, block in enumerate(self.chain):
                print(f"Checking block {block_idx} with {len(block.transactions)} transactions")
                
                for tx_idx, tx in enumerate(block.transactions):
                    try:
                        # Print transaction details to help debug
                        print(f"  Transaction {tx_idx}: {tx.transaction_type} | From: {tx.sender} | To: {tx.recipient} | Amount: {tx.amount}")
                        
                        # Credit - when address receives coins
                        if tx.recipient == address:
                            balance += tx.amount
                            tx_count += 1
                            
                            # Track specific transaction types
                            if tx.transaction_type == "TRANSFER":
                                transfer_credits += 1
                                print(f"    TRANSFER CREDIT: Block {block_idx}, Tx {tx_idx}: +{tx.amount} → {balance}")
                            elif tx.transaction_type == "ADJUSTMENT":
                                adjustment_credits += 1
                                print(f"    ADJUSTMENT CREDIT: Block {block_idx}, Tx {tx_idx}: +{tx.amount} → {balance}")
                            else:
                                print(f"    CREDIT: Block {block_idx}, Tx {tx_idx}: +{tx.amount} ({tx.transaction_type}) → {balance}")
                        
                        # Debit - when address sends coins
                        if tx.sender == address:
                            debit_amount = tx.amount + tx.fee
                            balance -= debit_amount
                            tx_count += 1
                            
                            # Track specific transaction types
                            if tx.transaction_type == "TRANSFER":
                                transfer_debits += 1
                                print(f"    TRANSFER DEBIT: Block {block_idx}, Tx {tx_idx}: -{debit_amount} → {balance}")
                            elif tx.transaction_type == "ADJUSTMENT":
                                adjustment_debits += 1
                                print(f"    ADJUSTMENT DEBIT: Block {block_idx}, Tx {tx_idx}: -{debit_amount} → {balance}")
                            else:
                                print(f"    DEBIT: Block {block_idx}, Tx {tx_idx}: -{debit_amount} ({tx.transaction_type}) → {balance}")
                    except Exception as tx_error:
                        print(f"Error processing transaction in block {block_idx}, tx {tx_idx}: {str(tx_error)}")
            
            # Provide detailed breakdown of transaction types for debugging
            print(f"Transaction type breakdown for {address}:")
            print(f"  - Transfer credits: {transfer_credits}")
            print(f"  - Transfer debits: {transfer_debits}")
            print(f"  - Adjustment credits: {adjustment_credits}")
            print(f"  - Adjustment debits: {adjustment_debits}")
            print(f"  - Total transactions: {tx_count}")
            
            # Also check mempool for pending transactions
            pending_credits = 0
            pending_debits = 0
            for pending_tx in self.mempool:
                if pending_tx.recipient == address:
                    pending_credits += pending_tx.amount
                if pending_tx.sender == address:
                    pending_debits += (pending_tx.amount + pending_tx.fee)
            
            if pending_credits > 0 or pending_debits > 0:
                print(f"Pending mempool transactions:")
                print(f"  - Pending credits: +{pending_credits}")
                print(f"  - Pending debits: -{pending_debits}")
                print(f"  - Net effect: {pending_credits - pending_debits}")
                
            print(f"Balance calculation complete for {address}: {balance} (from {tx_count} transactions)")
            return balance
        except Exception as e:
            print(f"Error calculating balance: {str(e)}")
            traceback.print_exc()
            return 0.0  # Return 0 balance on error for safety

    def adjust_difficulty(self) -> None:
        """
        Adjust the mining difficulty to maintain target block time.
        Modified for laptop development - much more gradual changes to make mining feasible.
        """
        # For development, adjust difficulty more frequently but with gentler changes
        DEVELOPMENT_ADJUSTMENT_INTERVAL = 50  # Adjust every 50 blocks for development
        blocks_since_last_adjustment = len(self.chain) % DEVELOPMENT_ADJUSTMENT_INTERVAL
        
        # Special case for initial mining - keep difficulty very low for the first 100 blocks
        if len(self.chain) < 100:
            # Ensure we're using the easiest setting for the first 100 blocks
            if self.target < self.MAX_TARGET:
                logging.info(f"First 100 blocks: Setting to easiest difficulty for development")
                self.target = self.MAX_TARGET
                self.bits = self.target_to_bits(self.target)
            return
            
        # Adjust difficulty every DEVELOPMENT_ADJUSTMENT_INTERVAL blocks
        if blocks_since_last_adjustment == 0 and len(self.chain) > DEVELOPMENT_ADJUSTMENT_INTERVAL:
            # Get last adjustment block
            last_adjustment_block = self.chain[-DEVELOPMENT_ADJUSTMENT_INTERVAL]
            expected_time = self.TARGET_BLOCK_TIME * DEVELOPMENT_ADJUSTMENT_INTERVAL
            actual_time = self.chain[-1].timestamp - last_adjustment_block.timestamp
            
            logging.info(f"Difficulty adjustment: Expected time={expected_time}s, Actual time={actual_time}s")
            
            # Calculate adjustment factor but with much gentler changes for development
            # Limit to only 1.25x change in either direction
            adjustment_factor = expected_time / max(min(actual_time, expected_time * 1.25), expected_time / 1.25)
            
            # Further dampen the adjustment for development (make changes 50% smaller)
            dampened_adjustment = 1.0 + (adjustment_factor - 1.0) * 0.5
            
            # Adjust difficulty (target is inversely proportional to difficulty)
            new_target = int(self.target / dampened_adjustment)
            
            # Apply upper bound on target (lower bound on difficulty)
            if new_target > self.MAX_TARGET:
                new_target = self.MAX_TARGET
                
            logging.info(f"Difficulty adjustment: Factor={dampened_adjustment}, Old target={self.target}, New target={new_target}")
            
            # Update difficulty
            self.target = new_target
            self.bits = self.target_to_bits(new_target)
            
        # Much gentler difficulty increase at halving events 
        halvings = len(self.chain) // self.HALVING_INTERVAL
        
        if len(self.chain) % self.HALVING_INTERVAL == 0 and len(self.chain) > 0 and halvings > 0:
            # Very small increase for development - only 10% harder per halving
            difficulty_multiplier = 1.1  
            new_target = int(self.target / difficulty_multiplier)
            
            logging.info(f"Halving event! Small difficulty increase by {difficulty_multiplier}x for development")
            logging.info(f"Halving adjustment: Old target={self.target}, New target={new_target}")
            
            # Update difficulty
            self.target = new_target
            self.bits = self.target_to_bits(new_target)

    def mine_block(self, miner_address: str) -> Optional[Block]:
        """
        Mine a new block with proof-of-work using Bitcoin's approach.
        This implements a proper proof-of-work algorithm requiring a 
        double-SHA256 hash below a specific target value.
        """
        if self.get_current_supply() >= self.MAX_SUPPLY:
            return None

        # Prepare block transactions
        block_transactions = []
        
        # Add mining reward transaction
        reward = self.get_mining_reward()
        reward_tx = Transaction("0", miner_address, reward, 0)
        block_transactions.append(reward_tx)
        
        # Add transactions from mempool (sorted by fee)
        sorted_transactions = sorted(self.mempool, key=lambda x: x.fee, reverse=True)
        block_transactions.extend(sorted_transactions[:100])  # Limit to 100 transactions per block
        
        # Calculate total transaction value for price impact
        block_value = sum(tx.amount for tx in sorted_transactions if tx.transaction_type == "PURCHASE")
        
        # Create new block with current timestamp
        new_block = Block(
            index=len(self.chain),
            previous_hash=self.chain[-1].hash,
            timestamp=time.time(),  # Use current timestamp for regular blocks
            transactions=block_transactions,
            nonce=0,  # Start with nonce=0 and increment during mining
            difficulty_bits=self.bits
        )
        
        # Log current mining task
        logging.info(f"Starting mining with difficulty bits: {hex(self.bits)}, target: {hex(self.target)}")
        
        # Proof of work - Bitcoin style
        # Instead of counting leading zeros, we check if the hash interpreted as a number
        # is less than the target value (which is inversely proportional to difficulty)
        while True:
            new_block.nonce += 1
            if new_block.nonce % 100000 == 0:  # Log progress every 100k attempts
                logging.info(f"Mining in progress: tried {new_block.nonce} nonces so far...")
                
            # Calculate new hash
            new_block.hash = new_block.calculate_hash()
            
            # Convert hash to integer and compare with target
            hash_int = int(new_block.hash, 16)
            if hash_int <= self.target:
                # We found a valid hash!
                logging.info(f"Found valid hash after {new_block.nonce} attempts: {new_block.hash}")
                break
        
        # Remove mined transactions from mempool
        for tx in block_transactions[1:]:  # Skip reward transaction
            if tx in self.mempool:
                self.mempool.remove(tx)
        
        # Add block to chain
        self.chain.append(new_block)
        
        # Adjust difficulty for next block
        self.adjust_difficulty()
        
        # Update market price based on new block metrics
        market_price = PRICE_ORACLE.calculate_market_price(self)
        
        # Add mining activity to order book if significant value
        if block_value > 0:
            PRICE_ORACLE.add_order(
                market_price,
                Decimal(str(block_value)),
                "SELL"  # Mining increases supply, so it's like a sell order
            )
        
        return new_block
        
    def mine_pending_transactions(self, miner_address: str) -> Optional[Block]:
        """Mine a new block including pending transactions"""
        logging.info(f"Mining pending transactions for {miner_address}")
        try:
            # Check if there are any pending transactions
            if not self.mempool:
                logging.info("No pending transactions to mine")
                return None
                
            # First log how many transactions are pending
            logging.info(f"Mining {len(self.mempool)} pending transactions")
            logging.info(f"Current difficulty bits: {hex(self.bits)}, target: {hex(self.target)}")
            
            # Use the existing mine_block function with Bitcoin-style proof-of-work
            return self.mine_block(miner_address)
        except Exception as e:
            logging.error(f"Error mining pending transactions: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def validate_chain(self) -> bool:
        """
        Validate the entire blockchain using Bitcoin's approach.
        Checks that each block's hash meets the difficulty target and
        that blocks are properly linked.
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Verify block hash
            if current_block.hash != current_block.calculate_hash():
                logging.error(f"Invalid block hash at index {i}")
                return False
            
            # Verify block links
            if current_block.previous_hash != previous_block.hash:
                logging.error(f"Invalid block chain linkage at index {i}")
                return False
            
            # Verify proof of work - Bitcoin style
            # Convert hash to integer
            hash_int = int(current_block.hash, 16)
            
            # Get target from bits
            block_target = self.bits_to_target(current_block.difficulty_bits)
            
            # Check if hash is below target
            if hash_int > block_target:
                logging.error(f"Block {i} hash {current_block.hash} doesn't meet difficulty target")
                return False
            
            # Verify merkle root
            if current_block.merkle_root != current_block.calculate_merkle_root():
                logging.error(f"Invalid merkle root at index {i}")
                return False
        
        return True

    def get_last_block(self) -> Block:
        """Get the most recent block in the chain"""
        return self.chain[-1]
        
    def save_chain_to_disk(self, filename="blockchain_data.json"):
        """Save the blockchain to disk for persistence"""
        try:
            data = {
                "chain": [block.to_dict() for block in self.chain],
                "bits": self.bits,  # Save difficulty in bits format
                "target": self.target  # Also save calculated target for reference
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            logging.info(f"Saved blockchain with {len(self.chain)} blocks to {filename}")
            logging.info(f"Current difficulty: bits={hex(self.bits)}, target={hex(self.target)}")
            return True
        except Exception as e:
            logging.error(f"Error saving blockchain: {str(e)}")
            return False

    def load_chain_from_disk(self, filename="blockchain_data.json"):
        """Load the blockchain from disk"""
        if not os.path.exists(filename):
            logging.warning(f"Blockchain file {filename} not found, using genesis block")
            return False
            
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Clear current chain
            self.chain = []
            
            # Load difficulty in bits format
            self.bits = data.get("bits", self.INITIAL_BITS)
            self.target = data.get("target", self.bits_to_target(self.bits))
            
            logging.info(f"Loaded difficulty: bits={hex(self.bits)}, target={hex(self.target)}")
            
            # Recreate blocks from saved data
            for block_data in data.get("chain", []):
                block = self._dict_to_block(block_data)
                self.chain.append(block)
            
            logging.info(f"Loaded blockchain with {len(self.chain)} blocks from {filename}")
            return True
        except Exception as e:
            logging.error(f"Error loading blockchain: {str(e)}")
            return False
            
    def _dict_to_block(self, block_data):
        """Convert a dictionary to a Block object"""
        # Convert transaction dictionaries to Transaction objects
        transactions = []
        for tx_data in block_data.get("transactions", []):
            transaction = Transaction(
                sender=tx_data.get("sender"),
                recipient=tx_data.get("recipient"),
                amount=float(tx_data.get("amount")),
                fee=float(tx_data.get("fee", 0)),
                signature=tx_data.get("signature"),
                transaction_type=tx_data.get("transaction_type", "TRANSFER"),
                price=tx_data.get("price")
            )
            transaction.timestamp = tx_data.get("timestamp")
            transactions.append(transaction)
        
        # Handle both old difficulty_target and new difficulty_bits for backward compatibility
        difficulty_bits = block_data.get("difficulty_bits")
        if difficulty_bits is None:
            # Convert old difficulty_target to bits format for backward compatibility
            old_difficulty = block_data.get("difficulty_target", 4)
            # Simple conversion - create a target with 'old_difficulty' leading zeros
            converted_target = int("1" + "0" * (64 - old_difficulty * 2), 16)
            difficulty_bits = self.target_to_bits(converted_target)
            logging.info(f"Converting old difficulty {old_difficulty} to bits: {hex(difficulty_bits)}")
        
        # Create Block object
        block = Block(
            index=block_data.get("index"),
            previous_hash=block_data.get("previous_hash"),
            timestamp=block_data.get("timestamp"),
            transactions=transactions,
            nonce=block_data.get("nonce"),
            difficulty_bits=difficulty_bits
        )
        
        # Set merkle root and hash directly to match what we received
        block.merkle_root = block_data.get("merkle_root")
        block.hash = block_data.get("hash")
        
        return block

    def add_block(self, block):
        """Add a validated block to the chain and save to disk"""
        self.chain.append(block)
        self.save_chain_to_disk()
        return True