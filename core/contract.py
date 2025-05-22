"""
Smart Contract implementation for GlobalCoyn.
Provides a simple, secure environment for executing user-defined contracts.
Deployed and updated by GitHub Actions workflow for bootstrap nodes via SCP.
Updated with improved deployment script to handle different directory structures.
Now includes app.py deployment to ensure contract API routes are registered.
"""
import hashlib
import time
import json
import logging
from typing import Dict, List, Any, Optional, Callable

# Setup logging
logger = logging.getLogger("contract")

class ContractError(Exception):
    """Exception raised for contract-related errors."""
    pass

class ContractState:
    """Manages the state of a contract."""
    def __init__(self, initial_state: Dict[str, Any] = None):
        """Initialize contract state with optional initial values."""
        self.state = initial_state or {}
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the state."""
        return self.state.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """Set a value in the state."""
        self.state[key] = value
        
    def delete(self, key: str) -> None:
        """Delete a key from the state."""
        if key in self.state:
            del self.state[key]
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to a serializable dictionary."""
        return self.state
        
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ContractState':
        """Create a ContractState instance from a dictionary."""
        return ContractState(data)


class Contract:
    """
    Implementation of a simple smart contract.
    """
    
    # Contract types
    TYPE_TOKEN = "TOKEN"        # Fungible token contract
    TYPE_NFT = "NFT"            # Non-fungible token contract
    TYPE_EXCHANGE = "EXCHANGE"  # Exchange/marketplace contract
    TYPE_CROWDFUND = "CROWDFUND"  # Crowdfunding contract
    TYPE_VOTING = "VOTING"      # Voting/governance contract
    TYPE_GENERAL = "GENERAL"    # General purpose contract
    
    def __init__(self, 
                 code: Dict[str, Any],
                 creator: str,
                 contract_type: str = "GENERAL",
                 name: str = "",
                 symbol: str = "",
                 init_data: Dict[str, Any] = None):
        """
        Initialize a new contract.
        
        Args:
            code: JSON representation of contract logic
            creator: Address of contract creator
            contract_type: Type of contract
            name: Human-readable name for the contract
            symbol: Symbol (for token contracts)
            init_data: Initial state data for the contract
        """
        self.code = code
        self.creator = creator
        self.contract_type = contract_type
        self.name = name
        self.symbol = symbol
        self.state = ContractState(init_data)
        self.creation_time = time.time()
        self.address = self._generate_address()
        
        # Verify contract code format
        self._verify_code()
        
    def _generate_address(self) -> str:
        """
        Generate a deterministic contract address.
        
        Returns:
            Contract address string
        """
        data = f"{self.creator}:{self.name}:{self.creation_time}"
        return "ct_" + hashlib.sha256(data.encode()).hexdigest()[:40]
        
    def _verify_code(self) -> None:
        """
        Verify that contract code has the required format.
        
        Raises:
            ContractError: If code format is invalid
        """
        if not isinstance(self.code, dict):
            raise ContractError("Contract code must be a dictionary")
            
        # Verify functions exist
        if "functions" not in self.code:
            raise ContractError("Contract must define 'functions'")
            
        if not isinstance(self.code["functions"], dict):
            raise ContractError("Contract functions must be a dictionary")
            
        # Verify each function
        for func_name, func_def in self.code["functions"].items():
            if not isinstance(func_def, dict):
                raise ContractError(f"Function '{func_name}' definition must be a dictionary")
                
            if "type" not in func_def:
                raise ContractError(f"Function '{func_name}' must specify a type")
                
    def execute(self, function: str, args: Dict[str, Any], caller: str) -> Dict[str, Any]:
        """
        Execute a contract function.
        
        Args:
            function: Name of the function to execute
            args: Arguments for the function
            caller: Address of the caller
            
        Returns:
            Result of the function execution
            
        Raises:
            ContractError: If function execution fails
        """
        # Check if function exists
        if function not in self.code["functions"]:
            raise ContractError(f"Function '{function}' not found in contract")
            
        func_def = self.code["functions"][function]
        
        # Check if function is callable by this address
        if func_def.get("onlyCreator", False) and caller != self.creator:
            raise ContractError(f"Function '{function}' can only be called by the contract creator")
            
        # Execute function based on type
        function_type = func_def.get("type")
        result = None
        
        try:
            if function_type == "token_transfer":
                result = self._execute_token_transfer(func_def, args, caller)
            elif function_type == "token_mint":
                result = self._execute_token_mint(func_def, args, caller)
            elif function_type == "token_burn":
                result = self._execute_token_burn(func_def, args, caller)
            elif function_type == "state_update":
                result = self._execute_state_update(func_def, args, caller)
            elif function_type == "crowdfund_contribute":
                result = self._execute_crowdfund_contribute(func_def, args, caller)
            elif function_type == "crowdfund_withdraw":
                result = self._execute_crowdfund_withdraw(func_def, args, caller)
            elif function_type == "vote_cast":
                result = self._execute_vote_cast(func_def, args, caller)
            else:
                raise ContractError(f"Unknown function type: {function_type}")
        except Exception as e:
            # Log the detailed exception
            logger.error(f"Contract execution error in {function}: {str(e)}")
            # Re-raise as ContractError
            raise ContractError(f"Error executing function '{function}': {str(e)}")
            
        return result
        
    def _execute_token_transfer(self, func_def: Dict[str, Any], args: Dict[str, Any], caller: str) -> Dict[str, Any]:
        """
        Execute a token transfer operation.
        
        Args:
            func_def: Function definition
            args: Function arguments (must include 'to' and 'amount')
            caller: Address initiating the transfer
            
        Returns:
            Result of the operation
        """
        if "to" not in args:
            raise ContractError("Token transfer requires 'to' argument")
            
        if "amount" not in args:
            raise ContractError("Token transfer requires 'amount' argument")
            
        to_address = args["to"]
        amount = float(args["amount"])
        
        if amount <= 0:
            raise ContractError("Transfer amount must be greater than zero")
            
        # Get balances
        balances = self.state.get("balances", {})
        sender_balance = balances.get(caller, 0)
        
        # Check balance
        if sender_balance < amount:
            raise ContractError(f"Insufficient balance: {sender_balance} < {amount}")
        
        # Update balances
        balances[caller] = sender_balance - amount
        balances[to_address] = balances.get(to_address, 0) + amount
        
        # Update state
        self.state.set("balances", balances)
        
        # Return updated balance info
        return {
            "success": True,
            "operation": "transfer",
            "from": caller,
            "to": to_address,
            "amount": amount,
            "new_sender_balance": balances[caller],
            "new_recipient_balance": balances[to_address]
        }
        
    def _execute_token_mint(self, func_def: Dict[str, Any], args: Dict[str, Any], caller: str) -> Dict[str, Any]:
        """
        Execute a token minting operation.
        
        Args:
            func_def: Function definition
            args: Function arguments (must include 'to' and 'amount')
            caller: Address initiating the mint
            
        Returns:
            Result of the operation
        """
        # Only creator can mint tokens
        if caller != self.creator:
            raise ContractError("Only contract creator can mint tokens")
            
        if "to" not in args:
            raise ContractError("Token mint requires 'to' argument")
            
        if "amount" not in args:
            raise ContractError("Token mint requires 'amount' argument")
            
        to_address = args["to"]
        amount = float(args["amount"])
        
        if amount <= 0:
            raise ContractError("Mint amount must be greater than zero")
            
        # Get current supply and cap
        balances = self.state.get("balances", {})
        total_supply = self.state.get("total_supply", 0)
        max_supply = self.state.get("max_supply", float('inf'))
        
        # Check max supply
        if total_supply + amount > max_supply:
            raise ContractError(f"Mint would exceed max supply: {total_supply} + {amount} > {max_supply}")
        
        # Update balances
        balances[to_address] = balances.get(to_address, 0) + amount
        
        # Update state
        self.state.set("balances", balances)
        self.state.set("total_supply", total_supply + amount)
        
        # Return updated info
        return {
            "success": True,
            "operation": "mint",
            "to": to_address,
            "amount": amount,
            "new_balance": balances[to_address],
            "new_total_supply": total_supply + amount
        }
        
    def _execute_token_burn(self, func_def: Dict[str, Any], args: Dict[str, Any], caller: str) -> Dict[str, Any]:
        """
        Execute a token burning operation.
        
        Args:
            func_def: Function definition
            args: Function arguments (must include 'amount')
            caller: Address initiating the burn
            
        Returns:
            Result of the operation
        """
        if "amount" not in args:
            raise ContractError("Token burn requires 'amount' argument")
            
        amount = float(args["amount"])
        
        if amount <= 0:
            raise ContractError("Burn amount must be greater than zero")
            
        # Get balances
        balances = self.state.get("balances", {})
        caller_balance = balances.get(caller, 0)
        
        # Check balance
        if caller_balance < amount:
            raise ContractError(f"Insufficient balance: {caller_balance} < {amount}")
        
        # Update balances
        balances[caller] = caller_balance - amount
        
        # Update state
        total_supply = self.state.get("total_supply", 0)
        self.state.set("balances", balances)
        self.state.set("total_supply", total_supply - amount)
        
        # Return updated info
        return {
            "success": True,
            "operation": "burn",
            "from": caller,
            "amount": amount,
            "new_balance": balances[caller],
            "new_total_supply": total_supply - amount
        }
        
    def _execute_state_update(self, func_def: Dict[str, Any], args: Dict[str, Any], caller: str) -> Dict[str, Any]:
        """
        Execute a general state update operation.
        
        Args:
            func_def: Function definition
            args: Function arguments (must include 'key' and 'value')
            caller: Address initiating the update
            
        Returns:
            Result of the operation
        """
        # Check if only creator can update
        if func_def.get("onlyCreator", True) and caller != self.creator:
            raise ContractError("Only contract creator can update state")
            
        if "key" not in args:
            raise ContractError("State update requires 'key' argument")
            
        if "value" not in args:
            raise ContractError("State update requires 'value' argument")
            
        key = args["key"]
        value = args["value"]
        
        # Protect special state keys
        protected_keys = ["balances", "total_supply", "max_supply"]
        if key in protected_keys:
            raise ContractError(f"Cannot directly update protected state key: {key}")
        
        # Update state
        self.state.set(key, value)
        
        # Return updated info
        return {
            "success": True,
            "operation": "state_update",
            "key": key,
            "value": value
        }
    
    def _execute_crowdfund_contribute(self, func_def: Dict[str, Any], args: Dict[str, Any], caller: str) -> Dict[str, Any]:
        """
        Execute a crowdfunding contribution.
        
        Args:
            func_def: Function definition
            args: Function arguments (must include 'amount')
            caller: Address making the contribution
            
        Returns:
            Result of the operation
        """
        if "amount" not in args:
            raise ContractError("Contribution requires 'amount' argument")
            
        amount = float(args["amount"])
        
        if amount <= 0:
            raise ContractError("Contribution amount must be greater than zero")
            
        # Check if campaign is active
        deadline = self.state.get("deadline", 0)
        if deadline < time.time():
            raise ContractError("Campaign has ended")
            
        # Update contributions
        contributions = self.state.get("contributions", {})
        contributions[caller] = contributions.get(caller, 0) + amount
        
        # Update total raised
        total_raised = self.state.get("total_raised", 0)
        self.state.set("total_raised", total_raised + amount)
        self.state.set("contributions", contributions)
        
        # Return updated info
        return {
            "success": True,
            "operation": "contribute",
            "contributor": caller,
            "amount": amount,
            "total_contributed": contributions[caller],
            "total_raised": total_raised + amount
        }
        
    def _execute_crowdfund_withdraw(self, func_def: Dict[str, Any], args: Dict[str, Any], caller: str) -> Dict[str, Any]:
        """
        Execute a crowdfunding withdrawal.
        
        Args:
            func_def: Function definition
            args: Function arguments
            caller: Address requesting withdrawal
            
        Returns:
            Result of the operation
        """
        # Get campaign state
        deadline = self.state.get("deadline", 0)
        goal = self.state.get("goal", 0)
        total_raised = self.state.get("total_raised", 0)
        
        # Check if campaign has ended
        if time.time() < deadline:
            raise ContractError("Campaign has not ended yet")
            
        # Check if caller is creator
        if caller == self.creator:
            # Creator can withdraw only if goal was met
            if total_raised < goal:
                raise ContractError("Cannot withdraw: goal not reached")
                
            # Record withdrawal
            self.state.set("withdrawn", True)
            self.state.set("withdrawn_amount", total_raised)
            
            return {
                "success": True,
                "operation": "creator_withdraw",
                "amount": total_raised,
                "goal_reached": True
            }
        else:
            # Contributor can refund only if goal was not met
            if total_raised >= goal:
                raise ContractError("Cannot refund: goal was reached")
                
            # Get contribution
            contributions = self.state.get("contributions", {})
            contribution = contributions.get(caller, 0)
            
            if contribution <= 0:
                raise ContractError("No contribution to refund")
                
            # Record refund
            contributions[caller] = 0
            self.state.set("contributions", contributions)
            
            return {
                "success": True,
                "operation": "refund",
                "amount": contribution,
                "goal_reached": False
            }
            
    def _execute_vote_cast(self, func_def: Dict[str, Any], args: Dict[str, Any], caller: str) -> Dict[str, Any]:
        """
        Execute a vote cast operation.
        
        Args:
            func_def: Function definition
            args: Function arguments (must include 'option')
            caller: Address casting the vote
            
        Returns:
            Result of the operation
        """
        if "option" not in args:
            raise ContractError("Vote cast requires 'option' argument")
            
        option = args["option"]
        
        # Check if voting is open
        start_time = self.state.get("start_time", 0)
        end_time = self.state.get("end_time", float('inf'))
        current_time = time.time()
        
        if current_time < start_time:
            raise ContractError("Voting has not started yet")
            
        if current_time > end_time:
            raise ContractError("Voting has ended")
            
        # Check if already voted
        voters = self.state.get("voters", {})
        if caller in voters and voters[caller]:
            raise ContractError("Address has already voted")
            
        # Check if option is valid
        options = self.state.get("options", [])
        if options and option not in options:
            raise ContractError(f"Invalid option: {option}")
            
        # Record vote
        votes = self.state.get("votes", {})
        votes[option] = votes.get(option, 0) + 1
        voters[caller] = option
        
        # Update state
        self.state.set("votes", votes)
        self.state.set("voters", voters)
        
        # Return updated info
        return {
            "success": True,
            "operation": "vote_cast",
            "voter": caller,
            "option": option,
            "vote_count": votes[option]
        }
        
    def get_info(self) -> Dict[str, Any]:
        """
        Get general information about the contract.
        
        Returns:
            Contract information
        """
        info = {
            "address": self.address,
            "creator": self.creator,
            "type": self.contract_type,
            "name": self.name,
            "symbol": self.symbol,
            "creation_time": self.creation_time
        }
        
        # Add type-specific info
        if self.contract_type == self.TYPE_TOKEN:
            info["total_supply"] = self.state.get("total_supply", 0)
            info["max_supply"] = self.state.get("max_supply", 0)
            
        elif self.contract_type == self.TYPE_CROWDFUND:
            info["goal"] = self.state.get("goal", 0)
            info["deadline"] = self.state.get("deadline", 0)
            info["total_raised"] = self.state.get("total_raised", 0)
            
        elif self.contract_type == self.TYPE_VOTING:
            info["start_time"] = self.state.get("start_time", 0)
            info["end_time"] = self.state.get("end_time", 0)
            info["options"] = self.state.get("options", [])
            
        return info
        
    def get_state(self, key: str = None) -> Any:
        """
        Get contract state.
        
        Args:
            key: Optional specific state key to retrieve
            
        Returns:
            Contract state or specific key value
        """
        if key:
            return self.state.get(key)
        
        return self.state.to_dict()
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert contract to a serializable dictionary.
        
        Returns:
            Dictionary representation of the contract
        """
        return {
            "address": self.address,
            "creator": self.creator,
            "type": self.contract_type,
            "name": self.name,
            "symbol": self.symbol,
            "code": self.code,
            "state": self.state.to_dict(),
            "creation_time": self.creation_time
        }
        
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Contract':
        """
        Create a Contract instance from a dictionary.
        
        Args:
            data: Dictionary representation of a contract
            
        Returns:
            Contract instance
        """
        contract = Contract(
            code=data["code"],
            creator=data["creator"],
            contract_type=data["type"],
            name=data["name"],
            symbol=data["symbol"],
            init_data=data["state"]
        )
        
        # Restore creation time and address
        contract.creation_time = data["creation_time"]
        contract.address = data["address"]
        
        return contract
        
    @staticmethod
    def create_token_contract(
        creator: str,
        name: str,
        symbol: str,
        initial_supply: float,
        max_supply: float = None,
        decimals: int = 8
    ) -> 'Contract':
        """
        Create a standard token contract.
        
        Args:
            creator: Address of contract creator
            name: Token name
            symbol: Token symbol
            initial_supply: Initial token supply
            max_supply: Maximum token supply (None for unlimited)
            decimals: Number of decimal places
            
        Returns:
            Token contract
        """
        code = {
            "functions": {
                "transfer": {
                    "type": "token_transfer",
                    "params": ["to", "amount"],
                    "description": "Transfer tokens to another address"
                },
                "mint": {
                    "type": "token_mint",
                    "params": ["to", "amount"],
                    "onlyCreator": True,
                    "description": "Mint new tokens (creator only)"
                },
                "burn": {
                    "type": "token_burn",
                    "params": ["amount"],
                    "description": "Burn tokens from your balance"
                }
            }
        }
        
        # Set up initial state
        init_data = {
            "balances": {creator: initial_supply},
            "total_supply": initial_supply,
            "decimals": decimals
        }
        
        if max_supply is not None:
            init_data["max_supply"] = max_supply
        
        # Create the contract
        return Contract(
            code=code,
            creator=creator,
            contract_type=Contract.TYPE_TOKEN,
            name=name,
            symbol=symbol,
            init_data=init_data
        )
        
    @staticmethod
    def create_crowdfunding_contract(
        creator: str,
        name: str,
        goal: float,
        deadline: float,
        description: str = ""
    ) -> 'Contract':
        """
        Create a crowdfunding contract.
        
        Args:
            creator: Address of contract creator
            name: Campaign name
            goal: Funding goal
            deadline: Campaign end timestamp
            description: Campaign description
            
        Returns:
            Crowdfunding contract
        """
        code = {
            "functions": {
                "contribute": {
                    "type": "crowdfund_contribute",
                    "params": ["amount"],
                    "description": "Contribute to the campaign"
                },
                "withdraw": {
                    "type": "crowdfund_withdraw",
                    "params": [],
                    "description": "Withdraw funds (creator) or refund (contributor)"
                }
            }
        }
        
        # Set up initial state
        init_data = {
            "goal": goal,
            "deadline": deadline,
            "description": description,
            "total_raised": 0,
            "contributions": {},
            "withdrawn": False
        }
        
        # Create the contract
        return Contract(
            code=code,
            creator=creator,
            contract_type=Contract.TYPE_CROWDFUND,
            name=name,
            init_data=init_data
        )
        
    @staticmethod
    def create_voting_contract(
        creator: str,
        name: str,
        options: List[str],
        start_time: float,
        end_time: float,
        description: str = ""
    ) -> 'Contract':
        """
        Create a voting contract.
        
        Args:
            creator: Address of contract creator
            name: Vote name
            options: List of voting options
            start_time: Voting start timestamp
            end_time: Voting end timestamp
            description: Vote description
            
        Returns:
            Voting contract
        """
        code = {
            "functions": {
                "vote": {
                    "type": "vote_cast",
                    "params": ["option"],
                    "description": "Cast a vote"
                },
                "add_option": {
                    "type": "state_update",
                    "params": ["key", "value"],
                    "onlyCreator": True,
                    "description": "Add a voting option (creator only)"
                }
            }
        }
        
        # Set up initial state
        init_data = {
            "options": options,
            "start_time": start_time,
            "end_time": end_time,
            "description": description,
            "votes": {},
            "voters": {}
        }
        
        # Create the contract
        return Contract(
            code=code,
            creator=creator,
            contract_type=Contract.TYPE_VOTING,
            name=name,
            init_data=init_data
        )


# Contract Manager
class ContractManager:
    """
    Manages all contracts in the blockchain.
    """
    
    def __init__(self):
        """Initialize an empty contract collection."""
        self.contracts: Dict[str, Contract] = {}
        
    def add_contract(self, contract: Contract) -> str:
        """
        Add a contract to the collection.
        
        Args:
            contract: Contract to add
            
        Returns:
            Address of the added contract
        """
        self.contracts[contract.address] = contract
        return contract.address
        
    def get_contract(self, address: str) -> Optional[Contract]:
        """
        Get a contract by address.
        
        Args:
            address: Contract address
            
        Returns:
            Contract if found, None otherwise
        """
        return self.contracts.get(address)
        
    def get_contracts_by_creator(self, creator: str) -> List[Contract]:
        """
        Get all contracts created by an address.
        
        Args:
            creator: Creator address
            
        Returns:
            List of contracts
        """
        return [c for c in self.contracts.values() if c.creator == creator]
        
    def get_contracts_by_type(self, contract_type: str) -> List[Contract]:
        """
        Get all contracts of a specific type.
        
        Args:
            contract_type: Contract type
            
        Returns:
            List of contracts
        """
        return [c for c in self.contracts.values() if c.contract_type == contract_type]
        
    def execute_contract(self, address: str, function: str, args: Dict[str, Any], caller: str) -> Dict[str, Any]:
        """
        Execute a function on a contract.
        
        Args:
            address: Contract address
            function: Function to execute
            args: Function arguments
            caller: Caller address
            
        Returns:
            Function result
            
        Raises:
            ContractError: If contract not found or execution fails
        """
        contract = self.get_contract(address)
        
        if not contract:
            raise ContractError(f"Contract not found: {address}")
            
        return contract.execute(function, args, caller)
        
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Convert all contracts to a serializable dictionary.
        
        Returns:
            Dictionary of contract data
        """
        return {addr: contract.to_dict() for addr, contract in self.contracts.items()}
        
    @staticmethod
    def from_dict(data: Dict[str, Dict[str, Any]]) -> 'ContractManager':
        """
        Create a ContractManager instance from a dictionary.
        
        Args:
            data: Dictionary of contract data
            
        Returns:
            ContractManager instance
        """
        manager = ContractManager()
        
        for addr, contract_data in data.items():
            contract = Contract.from_dict(contract_data)
            manager.contracts[addr] = contract
            
        return manager
