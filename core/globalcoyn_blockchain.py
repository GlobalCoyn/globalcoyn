"""
Main blockchain implementation for GlobalCoyn.
This is the central module that integrates transactions, blocks, mining, consensus, and smart contracts.
Updated to ensure contract deployment functionality is properly activated on bootstrap nodes.
Production fix: Trigger deployment to restart bootstrap services with correct imports.
"""
import hashlib
import time
import json
import logging
import os
import sys
from typing import List, Dict, Any, Optional, Tuple

# Import our modules
from transaction import Transaction
from block import Block
from mempool import Mempool
from mining import Miner
from utils import bits_to_target, target_to_bits, validate_address_format
from contract import Contract, ContractManager, ContractError

class Blockchain:
    """
    Main blockchain class that integrates all components.
    """
    def __init__(self, data_file: str = "blockchain_data.json"):
        """
        Initialize a new blockchain.
        
        Args:
            data_file: Path to blockchain data file
        """
        # Core components
        self.chain: List[Block] = []
        self.mempool = Mempool()
        self.miner = Miner()
        self.data_file = data_file
        self.contracts = ContractManager()
        
        # Initialize logger
        self.logger = logging.getLogger("blockchain")
        
        # Load blockchain or create genesis block
        if not self.load_chain_from_disk():
            self.create_genesis_block()
            
    def create_genesis_block(self, fixed_timestamp: float = 1619520000.0, fixed_nonce: int = 42) -> None:
        """
        Create the genesis block with no previous hash.
        
        Args:
            fixed_timestamp: Timestamp for genesis block (for reproducibility)
            fixed_nonce: Nonce for genesis block (for reproducibility)
        """
        genesis_block = Block(
            index=0,
            previous_hash="0" * 64,
            timestamp=fixed_timestamp,
            transactions=[],
            nonce=fixed_nonce,
            difficulty_bits=self.miner.bits
        )
        self.chain.append(genesis_block)
        self.logger.info(f"Created genesis block with hash: {genesis_block.hash}")
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Add a new transaction to the mempool.
        
        Args:
            transaction: Transaction to add
            
        Returns:
            True if transaction was added, False otherwise
        """
        # Use mempool to validate and add transaction
        return self.mempool.add_transaction(transaction, self.get_balance)
    
    def mine_block(self, miner_address: str) -> Optional[Block]:
        """
        Mine a new block and add it to the blockchain.
        
        Args:
            miner_address: Address to receive mining reward
            
        Returns:
            Newly mined block if successful, None otherwise
        """
        # First convert chain to dict format for the miner
        chain_data = [block.to_dict() for block in self.chain]
        
        # Mine new block
        new_block = self.miner.mine_block(chain_data, self.mempool, miner_address)
        
        if new_block:
            # Add to chain
            self.chain.append(new_block)
            
            # Adjust difficulty for next block
            blockchain_data = {"chain": [block.to_dict() for block in self.chain]}
            self.miner.adjust_difficulty(blockchain_data)
            
            # Save updated blockchain
            self.save_chain_to_disk()
            
            self.logger.info(f"New block mined and added to chain: {new_block.hash}")
            self.logger.info(f"Chain length: {len(self.chain)}")
            
        return new_block
    
    def get_balance(self, address: str) -> float:
        """
        Calculate the balance of a wallet address.
        
        Args:
            address: Wallet address to check
            
        Returns:
            Current balance of the address
        """
        balance = 0.0
        
        # Check address format
        if not validate_address_format(address):
            self.logger.warning(f"Invalid address format: {address}")
            return balance
        
        # Process all blocks
        for block in self.chain:
            for tx in block.transactions:
                # Credit (receiving)
                if tx.recipient == address:
                    balance += tx.amount
                
                # Debit (sending)
                if tx.sender == address:
                    balance -= (tx.amount + tx.fee)
        
        # Include pending transactions from mempool
        for tx in self.mempool.transactions:
            if tx.recipient == address:
                balance += tx.amount
            if tx.sender == address:
                balance -= (tx.amount + tx.fee)
        
        return max(0.0, balance)  # Ensure balance is never negative
    
    def get_address_transactions(self, address: str) -> List[Dict[str, Any]]:
        """
        Get all transactions for an address.
        
        Args:
            address: Wallet address to get transactions for
            
        Returns:
            List of transactions involving the address
        """
        transactions = []
        
        # Process all blocks
        for block_idx, block in enumerate(self.chain):
            for tx in block.transactions:
                if tx.sender == address or tx.recipient == address:
                    # Add block information to transaction data
                    tx_data = tx.to_dict()
                    tx_data["block_index"] = block_idx
                    tx_data["block_hash"] = block.hash
                    tx_data["confirmed"] = True
                    transactions.append(tx_data)
        
        # Include pending transactions from mempool
        for tx in self.mempool.get_address_transactions(address):
            tx_data = tx.to_dict()
            tx_data["confirmed"] = False
            transactions.append(tx_data)
        
        # Sort by timestamp, newest first
        transactions.sort(key=lambda tx: tx["timestamp"], reverse=True)
        
        return transactions
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """
        Find a block by its hash.
        
        Args:
            block_hash: Hash of the block to find
            
        Returns:
            Block if found, None otherwise
        """
        for block in self.chain:
            if block.hash == block_hash:
                return block
        return None
    
    def get_block_by_height(self, height: int) -> Optional[Block]:
        """
        Get a block by its height in the blockchain.
        
        Args:
            height: Block height (index)
            
        Returns:
            Block if found, None otherwise
        """
        if 0 <= height < len(self.chain):
            return self.chain[height]
        return None
    
    def get_latest_block(self) -> Block:
        """
        Get the latest block in the chain.
        
        Returns:
            The most recent block
        """
        return self.chain[-1]
    
    def get_chain_length(self) -> int:
        """
        Get the current length of the blockchain.
        
        Returns:
            Number of blocks in the chain
        """
        return len(self.chain)
    
    def get_mining_difficulty(self) -> Dict[str, Any]:
        """
        Get current mining difficulty information.
        
        Returns:
            Dictionary with difficulty information
        """
        return self.miner.get_mining_info()
    
    def calculate_total_supply(self) -> float:
        """
        Calculate the current total supply of coins.
        
        Returns:
            Total supply of coins in circulation
        """
        total_supply = 0.0
        
        # Only coinbase (mining reward) transactions create new supply
        for block in self.chain:
            for tx in block.transactions:
                if tx.is_coinbase():
                    total_supply += tx.amount
        
        return total_supply
    
    def get_blockchain_stats(self) -> Dict[str, Any]:
        """
        Get overall blockchain statistics.
        
        Returns:
            Dictionary with blockchain statistics
        """
        total_transactions = sum(len(block.transactions) for block in self.chain)
        
        # Calculate average block time for last 10 blocks
        avg_block_time = 0
        if len(self.chain) > 10:
            total_time = self.chain[-1].timestamp - self.chain[-10].timestamp
            avg_block_time = total_time / 10
        
        return {
            "height": len(self.chain),
            "blocks": len(self.chain),
            "total_supply": self.calculate_total_supply(),
            "total_transactions": total_transactions,
            "total_contracts": len(self.contracts.contracts),
            "difficulty": self.miner.get_mining_info(),
            "pending_transactions": self.mempool.size(),
            "avg_block_time": avg_block_time,
            "last_block_time": self.chain[-1].timestamp if self.chain else 0
        }
    
    def validate_chain(self) -> bool:
        """
        Validate the entire blockchain.
        
        Returns:
            True if chain is valid, False otherwise
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Check block hash
            if current_block.hash != current_block.calculate_hash():
                self.logger.error(f"Invalid block hash at index {i}")
                return False
            
            # Check previous hash reference
            if current_block.previous_hash != previous_block.hash:
                self.logger.error(f"Invalid previous hash at index {i}")
                return False
            
            # Check merkle root
            if current_block.merkle_root != current_block.calculate_merkle_root():
                self.logger.error(f"Invalid merkle root at index {i}")
                return False
            
            # Check proof of work (hash meets difficulty)
            block_target = bits_to_target(current_block.difficulty_bits)
            hash_int = int(current_block.hash, 16)
            if hash_int > block_target:
                self.logger.error(f"Block {i} hash doesn't meet difficulty requirement")
                return False
        
        return True
    
    def save_chain_to_disk(self) -> bool:
        """
        Save the blockchain to disk.
        
        Returns:
            True if save successful, False otherwise
        """
        try:
            data = {
                "chain": [block.to_dict() for block in self.chain],
                "bits": self.miner.bits,
                "target": self.miner.target,
                "contracts": self.contracts.to_dict()
            }
            
            # Create backup of existing file
            if os.path.exists(self.data_file):
                backup_file = f"{self.data_file}.backup.{int(time.time())}"
                try:
                    with open(self.data_file, 'r') as src:
                        with open(backup_file, 'w') as dst:
                            dst.write(src.read())
                    self.logger.info(f"Created backup of blockchain data: {backup_file}")
                except Exception as backup_error:
                    self.logger.warning(f"Failed to create backup: {str(backup_error)}")
            
            # Save current blockchain
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved blockchain with {len(self.chain)} blocks to {self.data_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save blockchain: {str(e)}")
            return False
    
    def load_chain_from_disk(self) -> bool:
        """
        Load the blockchain from disk.
        
        Returns:
            True if load successful, False otherwise
        """
        if not os.path.exists(self.data_file):
            self.logger.warning(f"Blockchain file {self.data_file} not found")
            return False
            
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            # Clear current chain
            self.chain = []
            
            # Load difficulty settings
            self.miner.bits = data.get("bits", self.miner.INITIAL_BITS)
            self.miner.target = data.get("target", bits_to_target(self.miner.bits))
            
            # Reconstruct blocks
            for block_data in data.get("chain", []):
                # Convert transactions back to objects
                transactions = []
                for tx_data in block_data.get("transactions", []):
                    transaction = Transaction.from_dict(tx_data)
                    transactions.append(transaction)
                
                # Create block
                block = Block(
                    index=block_data.get("index"),
                    previous_hash=block_data.get("previous_hash"),
                    timestamp=block_data.get("timestamp"),
                    transactions=transactions,
                    nonce=block_data.get("nonce"),
                    difficulty_bits=block_data.get("difficulty_bits")
                )
                
                # Set hash and merkle root directly
                block.hash = block_data.get("hash")
                block.merkle_root = block_data.get("merkle_root")
                
                # Add to chain
                self.chain.append(block)
            
            # Load contracts if they exist
            contracts_data = data.get("contracts", {})
            if contracts_data:
                self.contracts = ContractManager.from_dict(contracts_data)
                self.logger.info(f"Loaded {len(self.contracts.contracts)} contracts from blockchain data")
            
            self.logger.info(f"Loaded blockchain with {len(self.chain)} blocks from {self.data_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load blockchain: {str(e)}")
            return False
            
    # Smart Contract Methods
    
    def deploy_contract(self, contract_data: Dict[str, Any], creator: str) -> str:
        """
        Deploy a new smart contract to the blockchain.
        
        Args:
            contract_data: Contract data including code, type, name, etc.
            creator: Address of the contract creator
            
        Returns:
            Address of the deployed contract
            
        Raises:
            ContractError: If contract deployment fails
        """
        try:
            # Extract contract parameters
            code = contract_data.get("code", {})
            contract_type = contract_data.get("type", Contract.TYPE_GENERAL)
            name = contract_data.get("name", "")
            symbol = contract_data.get("symbol", "")
            init_data = contract_data.get("init_data", {})
            
            # Validate creator address
            if not validate_address_format(creator):
                raise ContractError(f"Invalid creator address format: {creator}")
            
            # Check if creator has sufficient balance for deployment (minimum 1 GCN)
            min_balance = 1.0
            creator_balance = self.get_balance(creator)
            if creator_balance < min_balance:
                raise ContractError(f"Insufficient balance for contract deployment. Required: {min_balance} GCN, Available: {creator_balance} GCN")
            
            # Create the contract
            if contract_type == Contract.TYPE_TOKEN:
                # Token-specific parameters
                initial_supply = float(contract_data.get("initial_supply", 1000000))
                max_supply = float(contract_data.get("max_supply", 0)) if contract_data.get("max_supply") else None
                decimals = int(contract_data.get("decimals", 8))
                
                # Create token contract
                contract = Contract.create_token_contract(
                    creator=creator,
                    name=name,
                    symbol=symbol,
                    initial_supply=initial_supply,
                    max_supply=max_supply,
                    decimals=decimals
                )
            elif contract_type == Contract.TYPE_CROWDFUND:
                # Crowdfunding-specific parameters
                goal = float(contract_data.get("goal", 1000))
                deadline = float(contract_data.get("deadline", time.time() + 30*24*60*60))  # Default: 30 days
                description = contract_data.get("description", "")
                
                # Create crowdfunding contract
                contract = Contract.create_crowdfunding_contract(
                    creator=creator,
                    name=name,
                    goal=goal,
                    deadline=deadline,
                    description=description
                )
            elif contract_type == Contract.TYPE_VOTING:
                # Voting-specific parameters
                options = contract_data.get("options", [])
                start_time = float(contract_data.get("start_time", time.time()))
                end_time = float(contract_data.get("end_time", time.time() + 7*24*60*60))  # Default: 7 days
                description = contract_data.get("description", "")
                
                # Create voting contract
                contract = Contract.create_voting_contract(
                    creator=creator,
                    name=name,
                    options=options,
                    start_time=start_time,
                    end_time=end_time,
                    description=description
                )
            else:
                # Generic contract
                contract = Contract(
                    code=code,
                    creator=creator,
                    contract_type=contract_type,
                    name=name,
                    symbol=symbol,
                    init_data=init_data
                )
            
            # Add contract to manager
            contract_address = self.contracts.add_contract(contract)
            
            # Save blockchain state to persist contract
            self.save_chain_to_disk()
            
            self.logger.info(f"Deployed contract {name} with address {contract_address}")
            return contract_address
            
        except Exception as e:
            self.logger.error(f"Contract deployment error: {str(e)}")
            raise ContractError(f"Failed to deploy contract: {str(e)}")
    
    def execute_contract(self, contract_address: str, function: str, args: Dict[str, Any], caller: str) -> Dict[str, Any]:
        """
        Execute a function on a smart contract.
        
        Args:
            contract_address: Address of the contract
            function: Name of the function to execute
            args: Arguments to pass to the function
            caller: Address of the function caller
            
        Returns:
            Result of the function execution
            
        Raises:
            ContractError: If execution fails
        """
        try:
            # Validate caller address
            if not validate_address_format(caller):
                raise ContractError(f"Invalid caller address format: {caller}")
            
            # Check if caller has sufficient balance for execution (minimum 0.01 GCN)
            min_balance = 0.01
            caller_balance = self.get_balance(caller)
            if caller_balance < min_balance:
                raise ContractError(f"Insufficient balance for contract execution. Required: {min_balance} GCN, Available: {caller_balance} GCN")
            
            # Execute the contract function
            result = self.contracts.execute_contract(contract_address, function, args, caller)
            
            # Save blockchain state to persist contract state changes
            self.save_chain_to_disk()
            
            self.logger.info(f"Executed function {function} on contract {contract_address}")
            return result
            
        except Exception as e:
            self.logger.error(f"Contract execution error: {str(e)}")
            raise ContractError(f"Failed to execute contract: {str(e)}")
    
    def get_contract(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get a contract by its address.
        
        Args:
            address: Address of the contract
            
        Returns:
            Contract data if found, None otherwise
        """
        contract = self.contracts.get_contract(address)
        if contract:
            return contract.to_dict()
        return None
    
    def get_contract_state(self, address: str, key: str = None) -> Any:
        """
        Get the state of a contract.
        
        Args:
            address: Address of the contract
            key: Optional specific state key to retrieve
            
        Returns:
            Contract state or specific key value
            
        Raises:
            ContractError: If contract not found
        """
        contract = self.contracts.get_contract(address)
        if not contract:
            raise ContractError(f"Contract not found: {address}")
        
        return contract.get_state(key)
    
    def get_all_contracts(self) -> List[Dict[str, Any]]:
        """
        Get all deployed contracts.
        
        Returns:
            List of contract data
        """
        return [c.to_dict() for c in self.contracts.contracts.values()]
    
    def get_contracts_by_creator(self, creator: str) -> List[Dict[str, Any]]:
        """
        Get all contracts created by an address.
        
        Args:
            creator: Address of the creator
            
        Returns:
            List of contract data
        """
        contracts = self.contracts.get_contracts_by_creator(creator)
        return [c.to_dict() for c in contracts]
    
    def get_contracts_by_type(self, contract_type: str) -> List[Dict[str, Any]]:
        """
        Get all contracts of a specific type.
        
        Args:
            contract_type: Type of contracts to retrieve
            
        Returns:
            List of contract data
        """
        contracts = self.contracts.get_contracts_by_type(contract_type)
        return [c.to_dict() for c in contracts]