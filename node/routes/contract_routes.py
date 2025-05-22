"""
API routes for smart contract operations.
"""
import json
import time
import logging
import importlib
import sys
from typing import Dict, Any, List, Optional
from flask import Blueprint, request, jsonify

# Import from builtins (stored by app.py)
import builtins

# Setup logger
logger = logging.getLogger("contract_routes")

# Verify contract functionality is available
def ensure_contract_functionality():
    """
    Ensure that the contract functionality is available in the Blockchain class.
    If not, attempt to reload the module.
    """
    if not hasattr(builtins.GCN.blockchain, 'deploy_contract'):
        logger.warning("Contract functionality not found in Blockchain class. Attempting to reload modules...")
        
        try:
            # Try to reload the blockchain module
            if 'blockchain' in sys.modules:
                importlib.reload(sys.modules['blockchain'])
            elif 'core.blockchain' in sys.modules:
                importlib.reload(sys.modules['core.blockchain'])
            elif 'blockchain.core.blockchain' in sys.modules:
                importlib.reload(sys.modules['blockchain.core.blockchain'])
                
            # Also try to reload the contract module
            if 'contract' in sys.modules:
                importlib.reload(sys.modules['contract'])
            elif 'core.contract' in sys.modules:
                importlib.reload(sys.modules['core.contract'])
            elif 'blockchain.core.contract' in sys.modules:
                importlib.reload(sys.modules['blockchain.core.contract'])
                
            # Recreate Blockchain instance if possible
            if hasattr(builtins.GCN, 'blockchain'):
                from blockchain import Blockchain
                builtins.GCN.blockchain = Blockchain(builtins.GCN.blockchain.data_file)
                
            logger.info("Modules reloaded. Checking for contract functionality...")
            
            # Check if reload was successful
            has_contract = hasattr(builtins.GCN.blockchain, 'deploy_contract')
            logger.info(f"Contract functionality available: {has_contract}")
            
            return has_contract
        except Exception as e:
            logger.error(f"Error attempting to reload modules: {str(e)}")
            return False
    return True

# Try to ensure contract functionality on module load
contract_functionality_available = ensure_contract_functionality()

# Import Transaction class for contract fee transactions
try:
    from blockchain.core.transaction import Transaction
except ImportError:
    try:
        from transaction import Transaction
    except ImportError:
        # Fallback - define a minimal Transaction class for testing
        class Transaction:
            def __init__(self, sender, recipient, amount, fee, signature=None):
                self.sender = sender
                self.recipient = recipient
                self.amount = float(amount)
                self.fee = float(fee)
                self.signature = signature
                self.tx_hash = None

# Contract deployment constants
CONTRACT_FEE = 100  # Fee in GCN
CONTRACT_FEE_ADDRESS = "1LVkyzYqPBYYhMEjxFm1dLXsFUox2gtdDr"  # Network address that collects fees

# Check if Contract is available from core modules
try:
    from blockchain.core.contract import Contract, ContractError
except ImportError:
    try:
        from contract import Contract, ContractError
    except ImportError:
        # Fallback - define them here for testing
        class ContractError(Exception):
            pass
            
        class Contract:
            # Define contract types
            TYPE_TOKEN = "TOKEN"
            TYPE_CROWDFUND = "CROWDFUND"
            TYPE_VOTING = "VOTING"
            TYPE_EXCHANGE = "EXCHANGE"
            TYPE_GENERAL = "GENERAL"

# Set up logger
logger = logging.getLogger("contract_routes")

# Create blueprint
contract_bp = Blueprint('contract_bp', __name__)

# Add route decorator to check contract functionality
def check_contract_functionality(f):
    """Decorator to check if contract functionality is available"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Ensure contract functionality is available
        if not ensure_contract_functionality():
            return jsonify({
                "status": "error",
                "message": "Contract functionality is not available on this node. The server has not been correctly updated."
            }), 500
        return f(*args, **kwargs)
    return decorated_function

@contract_bp.route('/', methods=['GET'])
@contract_bp.route('/all', methods=['GET'])
def get_all_contracts():
    """
    Get all contracts in the blockchain.
    
    Returns:
        All deployed contracts
    """
    try:
        # Get all contracts if implemented, otherwise return empty list
        try:
            contracts = builtins.GCN.blockchain.get_all_contracts()
        except (AttributeError, NotImplementedError):
            logger.warning("get_all_contracts not implemented in blockchain, returning empty list")
            contracts = []
        
        return jsonify({
            "status": "success",
            "contracts": contracts,
            "count": len(contracts)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting contracts: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/types', methods=['GET'])
def get_contract_types():
    """
    Get all available contract types.
    
    Returns:
        List of contract types
    """
    try:
        # Define contract types with descriptions
        contract_types = [
            {
                "type": Contract.TYPE_TOKEN,
                "name": "Token Contract",
                "description": "Create a custom token on the GlobalCoyn blockchain"
            },
            {
                "type": Contract.TYPE_CROWDFUND,
                "name": "Crowdfunding Contract",
                "description": "Start a fundraising campaign with automatic fund distribution"
            },
            {
                "type": Contract.TYPE_VOTING,
                "name": "Voting Contract",
                "description": "Create a secure voting system for governance or decision-making"
            },
            {
                "type": Contract.TYPE_EXCHANGE,
                "name": "Exchange Contract",
                "description": "Create a decentralized exchange for trading tokens"
            },
            {
                "type": Contract.TYPE_GENERAL,
                "name": "General Contract",
                "description": "Create a custom contract with your own functionality"
            }
        ]
        
        return jsonify({
            "status": "success",
            "contract_types": contract_types
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting contract types: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/byType/<contract_type>', methods=['GET'])
def get_contracts_by_type(contract_type):
    """
    Get all contracts of a specific type.
    
    Args:
        contract_type: Type of contracts to retrieve
        
    Returns:
        Contracts of the specified type
    """
    try:
        # Get contracts by type if implemented, otherwise return empty list
        try:
            contracts = builtins.GCN.blockchain.get_contracts_by_type(contract_type)
        except (AttributeError, NotImplementedError):
            logger.warning(f"get_contracts_by_type not implemented in blockchain, returning empty list")
            contracts = []
        
        return jsonify({
            "status": "success",
            "type": contract_type,
            "contracts": contracts,
            "count": len(contracts)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting contracts by type: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/byCreator/<creator>', methods=['GET'])
def get_contracts_by_creator(creator):
    """
    Get all contracts created by an address.
    
    Args:
        creator: Address of the creator
        
    Returns:
        Contracts created by the specified address
    """
    try:
        # Get contracts by creator if implemented, otherwise return empty list
        try:
            contracts = builtins.GCN.blockchain.get_contracts_by_creator(creator)
        except (AttributeError, NotImplementedError):
            logger.warning(f"get_contracts_by_creator not implemented in blockchain, returning empty list")
            contracts = []
        
        return jsonify({
            "status": "success",
            "creator": creator,
            "contracts": contracts,
            "count": len(contracts)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting contracts by creator: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/<address>', methods=['GET'])
def get_contract(address):
    """
    Get a contract by its address.
    
    Args:
        address: Address of the contract
        
    Returns:
        Contract data
    """
    try:
        # Get contract
        contract = builtins.GCN.blockchain.get_contract(address)
        
        if not contract:
            return jsonify({
                "status": "error",
                "message": f"Contract not found: {address}"
            }), 404
        
        return jsonify({
            "status": "success",
            "contract": contract
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting contract: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/<address>/state', methods=['GET'])
def get_contract_state(address):
    """
    Get the state of a contract.
    
    Args:
        address: Address of the contract
        
    Returns:
        Contract state
    """
    try:
        # Get contract state if implemented, otherwise return empty dict
        try:
            state = builtins.GCN.blockchain.get_contract_state(address)
        except (AttributeError, NotImplementedError):
            logger.warning(f"get_contract_state not implemented in blockchain, returning empty dict")
            state = {}
        
        return jsonify({
            "status": "success",
            "address": address,
            "state": state
        }), 200
        
    except ContractError as e:
        logger.error(f"Contract error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 404
        
    except Exception as e:
        logger.error(f"Error getting contract state: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/<address>/state/<key>', methods=['GET'])
def get_contract_state_key(address, key):
    """
    Get a specific key from the state of a contract.
    
    Args:
        address: Address of the contract
        key: State key to retrieve
        
    Returns:
        Value of the state key
    """
    try:
        # Get contract state key
        value = builtins.GCN.blockchain.get_contract_state(address, key)
        
        return jsonify({
            "status": "success",
            "address": address,
            "key": key,
            "value": value
        }), 200
        
    except ContractError as e:
        logger.error(f"Contract error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 404
        
    except Exception as e:
        logger.error(f"Error getting contract state key: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/deploy', methods=['POST'])
@check_contract_functionality
def deploy_contract():
    """
    Deploy a new smart contract.
    
    Request body:
        contract_data: Contract data
        creator: Address of the creator
        
    Returns:
        Address of the deployed contract
    """
    try:
        # Get request data
        data = request.json
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        # Required fields
        required_fields = ["contract_data", "creator"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Check if deploy_contract method exists
        if not hasattr(builtins.GCN.blockchain, 'deploy_contract'):
            logger.error("CRITICAL ERROR: Blockchain object does not have deploy_contract method!")
            return jsonify({
                "status": "error",
                "message": "Contract deployment is not available on this node. The server has not been correctly updated with contract functionality."
            }), 500
            
        # Deploy contract
        contract_address = builtins.GCN.blockchain.deploy_contract(
            contract_data=data["contract_data"],
            creator=data["creator"]
        )
        
        return jsonify({
            "status": "success",
            "message": "Contract deployed successfully",
            "contract_address": contract_address
        }), 201
        
    except ContractError as e:
        logger.error(f"Contract deployment error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400
        
    except Exception as e:
        logger.error(f"Error deploying contract: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/<address>/execute', methods=['POST'])
@check_contract_functionality
def execute_contract(address):
    """
    Execute a function on a smart contract.
    
    Args:
        address: Address of the contract
        
    Request body:
        function: Name of the function to execute
        args: Arguments for the function
        caller: Address of the caller
        
    Returns:
        Result of the function execution
    """
    try:
        # Get request data
        data = request.json
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        # Required fields
        required_fields = ["function", "caller"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Check if execute_contract method exists
        if not hasattr(builtins.GCN.blockchain, 'execute_contract'):
            logger.error("CRITICAL ERROR: Blockchain object does not have execute_contract method!")
            return jsonify({
                "status": "error",
                "message": "Contract execution is not available on this node. The server has not been correctly updated with contract functionality."
            }), 500
            
        # Execute contract function
        result = builtins.GCN.blockchain.execute_contract(
            contract_address=address,
            function=data["function"],
            args=data.get("args", {}),
            caller=data["caller"]
        )
        
        return jsonify({
            "status": "success",
            "message": f"Function {data['function']} executed successfully",
            "result": result
        }), 200
        
    except ContractError as e:
        logger.error(f"Contract execution error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400
        
    except Exception as e:
        logger.error(f"Error executing contract: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Token-specific endpoints

@contract_bp.route('/token/<address>/balance/<wallet_address>', methods=['GET'])
def get_token_balance(address, wallet_address):
    """
    Get the balance of a specific token for a wallet address.
    
    Args:
        address: Address of the token contract
        wallet_address: Address of the wallet
        
    Returns:
        Token balance
    """
    try:
        # Get contract
        contract = builtins.GCN.blockchain.get_contract(address)
        
        if not contract:
            return jsonify({
                "status": "error",
                "message": f"Token contract not found: {address}"
            }), 404
        
        # Check contract type
        if contract["type"] != Contract.TYPE_TOKEN:
            return jsonify({
                "status": "error",
                "message": f"Contract is not a token contract: {address}"
            }), 400
        
        # Get balances from state
        balances = builtins.GCN.blockchain.get_contract_state(address, "balances") or {}
        
        # Get balance for wallet
        balance = balances.get(wallet_address, 0)
        
        return jsonify({
            "status": "success",
            "token_address": address,
            "token_name": contract["name"],
            "token_symbol": contract["symbol"],
            "wallet_address": wallet_address,
            "balance": balance
        }), 200
        
    except ContractError as e:
        logger.error(f"Contract error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400
        
    except Exception as e:
        logger.error(f"Error getting token balance: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/token/<address>/transfer', methods=['POST'])
def transfer_tokens(address):
    """
    Transfer tokens from one address to another.
    
    Args:
        address: Address of the token contract
        
    Request body:
        from_address: Address of the sender
        to_address: Address of the recipient
        amount: Amount to transfer
        
    Returns:
        Result of the transfer
    """
    try:
        # Get request data
        data = request.json
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        # Required fields
        required_fields = ["from_address", "to_address", "amount"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Execute token transfer
        result = builtins.GCN.blockchain.execute_contract(
            contract_address=address,
            function="transfer",
            args={
                "to": data["to_address"],
                "amount": float(data["amount"])
            },
            caller=data["from_address"]
        )
        
        return jsonify({
            "status": "success",
            "message": "Token transfer successful",
            "result": result
        }), 200
        
    except ContractError as e:
        logger.error(f"Token transfer error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400
        
    except Exception as e:
        logger.error(f"Error transferring tokens: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Template endpoints for specific contract types

@contract_bp.route('/templates/token', methods=['POST'])
@check_contract_functionality
def create_token_contract():
    """
    Create a new token contract.
    
    Request body:
        creator: Address of the creator
        name: Token name
        symbol: Token symbol
        initial_supply: Initial token supply
        max_supply: Maximum token supply (optional)
        decimals: Number of decimal places (optional)
        fee: Contract deployment fee in GCN (required)
        
    Returns:
        Address of the deployed contract
    """
    try:
        # Get request data
        data = request.json
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        # Required fields
        required_fields = ["creator", "name", "symbol", "initial_supply", "fee"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Check if fee is 100 GCN
        contract_fee = float(data.get("fee", 0))
        if contract_fee < 100:
            return jsonify({
                "status": "error",
                "message": f"Contract deployment requires a fee of 100 GCN. Provided fee: {contract_fee} GCN."
            }), 400
            
        # Check creator's wallet balance
        try:
            wallet_balance = builtins.GCN.blockchain.get_balance(data["creator"])
            if wallet_balance < contract_fee:
                return jsonify({
                    "status": "error",
                    "message": f"Insufficient balance. Contract deployment requires a fee of 100 GCN. Current balance: {wallet_balance} GCN."
                }), 400
        except Exception as e:
            logger.error(f"Error checking wallet balance: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Failed to verify wallet balance: {str(e)}"
            }), 500
            
        # Process the fee by creating a transaction to the network fee address
        try:
            # Use the fee collector address defined as a constant
            fee_address = CONTRACT_FEE_ADDRESS
            
            # Instead of requiring a fee transaction here, change the contract deployment process
            # to use a two-step verification approach:
            
            # 1. First, verify that the creator has enough balance
            creator_balance = builtins.GCN.blockchain.get_balance(data["creator"])
            if creator_balance < contract_fee:
                return jsonify({
                    "status": "error",
                    "message": f"Insufficient balance for contract deployment. Required: {contract_fee} GCN, Available: {creator_balance} GCN."
                }), 400
                
            # 2. Log that we're proceeding with contract deployment
            logger.info(f"Contract deployment authorized for {data['creator']} - Fee: {contract_fee} GCN")
            
            # Note: The actual fee transaction will be handled by the frontend using the wallet service
            # The contract will be deployed now, and the frontend is responsible for sending the fee
            # to the CONTRACT_FEE_ADDRESS after a successful deployment
        except Exception as e:
            logger.error(f"Error processing contract fee: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Failed to process contract fee: {str(e)}"
            }), 500
        
        # Prepare contract data
        contract_data = {
            "type": Contract.TYPE_TOKEN,
            "name": data["name"],
            "symbol": data["symbol"],
            "initial_supply": float(data["initial_supply"]),
            "decimals": int(data.get("decimals", 8))
        }
        
        # Add max supply if provided
        if "max_supply" in data:
            contract_data["max_supply"] = float(data["max_supply"])
        
        # Deploy contract
        contract_address = builtins.GCN.blockchain.deploy_contract(
            contract_data=contract_data,
            creator=data["creator"]
        )
        
        return jsonify({
            "status": "success",
            "message": f"Token contract {data['name']} ({data['symbol']}) deployed successfully",
            "contract_address": contract_address
        }), 201
        
    except ContractError as e:
        logger.error(f"Token contract creation error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400
        
    except Exception as e:
        logger.error(f"Error creating token contract: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/templates/crowdfunding', methods=['POST'])
@check_contract_functionality
def create_crowdfunding_contract():
    """
    Create a new crowdfunding contract.
    
    Request body:
        creator: Address of the creator
        name: Campaign name
        goal: Funding goal
        deadline: Campaign end timestamp (optional)
        description: Campaign description (optional)
        fee: Contract deployment fee in GCN (required)
        
    Returns:
        Address of the deployed contract
    """
    try:
        # Get request data
        data = request.json
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        # Required fields
        required_fields = ["creator", "name", "goal", "fee"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Check if fee is 100 GCN
        contract_fee = float(data.get("fee", 0))
        if contract_fee < 100:
            return jsonify({
                "status": "error",
                "message": f"Contract deployment requires a fee of 100 GCN. Provided fee: {contract_fee} GCN."
            }), 400
            
        # Check creator's wallet balance
        try:
            wallet_balance = builtins.GCN.blockchain.get_balance(data["creator"])
            if wallet_balance < contract_fee:
                return jsonify({
                    "status": "error",
                    "message": f"Insufficient balance. Contract deployment requires a fee of 100 GCN. Current balance: {wallet_balance} GCN."
                }), 400
        except Exception as e:
            logger.error(f"Error checking wallet balance: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Failed to verify wallet balance: {str(e)}"
            }), 500
            
        # Process the fee by creating a transaction to the network fee address
        try:
            # Use the fee collector address defined as a constant
            fee_address = CONTRACT_FEE_ADDRESS
            
            # Instead of requiring a fee transaction here, change the contract deployment process
            # to use a two-step verification approach:
            
            # 1. First, verify that the creator has enough balance
            creator_balance = builtins.GCN.blockchain.get_balance(data["creator"])
            if creator_balance < contract_fee:
                return jsonify({
                    "status": "error",
                    "message": f"Insufficient balance for contract deployment. Required: {contract_fee} GCN, Available: {creator_balance} GCN."
                }), 400
                
            # 2. Log that we're proceeding with contract deployment
            logger.info(f"Contract deployment authorized for {data['creator']} - Fee: {contract_fee} GCN")
            
            # Note: The actual fee transaction will be handled by the frontend using the wallet service
            # The contract will be deployed now, and the frontend is responsible for sending the fee
            # to the CONTRACT_FEE_ADDRESS after a successful deployment
        except Exception as e:
            logger.error(f"Error processing contract fee: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Failed to process contract fee: {str(e)}"
            }), 500
        
        # Set default deadline if not provided (30 days from now)
        deadline = data.get("deadline", time.time() + 30*24*60*60)
        
        # Prepare contract data
        contract_data = {
            "type": Contract.TYPE_CROWDFUND,
            "name": data["name"],
            "goal": float(data["goal"]),
            "deadline": float(deadline),
            "description": data.get("description", "")
        }
        
        # Deploy contract
        contract_address = builtins.GCN.blockchain.deploy_contract(
            contract_data=contract_data,
            creator=data["creator"]
        )
        
        return jsonify({
            "status": "success",
            "message": f"Crowdfunding contract '{data['name']}' deployed successfully",
            "contract_address": contract_address
        }), 201
        
    except ContractError as e:
        logger.error(f"Crowdfunding contract creation error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400
        
    except Exception as e:
        logger.error(f"Error creating crowdfunding contract: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/templates/voting', methods=['POST'])
@check_contract_functionality
def create_voting_contract():
    """
    Create a new voting contract.
    
    Request body:
        creator: Address of the creator
        name: Vote name
        options: List of voting options
        start_time: Voting start timestamp (optional)
        end_time: Voting end timestamp (optional)
        description: Vote description (optional)
        fee: Contract deployment fee in GCN (required)
        
    Returns:
        Address of the deployed contract
    """
    try:
        # Get request data
        data = request.json
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        # Required fields
        required_fields = ["creator", "name", "options", "fee"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Check if fee is 100 GCN
        contract_fee = float(data.get("fee", 0))
        if contract_fee < 100:
            return jsonify({
                "status": "error",
                "message": f"Contract deployment requires a fee of 100 GCN. Provided fee: {contract_fee} GCN."
            }), 400
            
        # Check creator's wallet balance
        try:
            wallet_balance = builtins.GCN.blockchain.get_balance(data["creator"])
            if wallet_balance < contract_fee:
                return jsonify({
                    "status": "error",
                    "message": f"Insufficient balance. Contract deployment requires a fee of 100 GCN. Current balance: {wallet_balance} GCN."
                }), 400
        except Exception as e:
            logger.error(f"Error checking wallet balance: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Failed to verify wallet balance: {str(e)}"
            }), 500
            
        # Process the fee by creating a transaction to the network fee address
        try:
            # Use the fee collector address defined as a constant
            fee_address = CONTRACT_FEE_ADDRESS
            
            # Instead of requiring a fee transaction here, change the contract deployment process
            # to use a two-step verification approach:
            
            # 1. First, verify that the creator has enough balance
            creator_balance = builtins.GCN.blockchain.get_balance(data["creator"])
            if creator_balance < contract_fee:
                return jsonify({
                    "status": "error",
                    "message": f"Insufficient balance for contract deployment. Required: {contract_fee} GCN, Available: {creator_balance} GCN."
                }), 400
                
            # 2. Log that we're proceeding with contract deployment
            logger.info(f"Contract deployment authorized for {data['creator']} - Fee: {contract_fee} GCN")
            
            # Note: The actual fee transaction will be handled by the frontend using the wallet service
            # The contract will be deployed now, and the frontend is responsible for sending the fee
            # to the CONTRACT_FEE_ADDRESS after a successful deployment
        except Exception as e:
            logger.error(f"Error processing contract fee: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Failed to process contract fee: {str(e)}"
            }), 500
        
        # Set default timestamps if not provided
        start_time = data.get("start_time", time.time())
        end_time = data.get("end_time", time.time() + 7*24*60*60)  # 7 days from now
        
        # Prepare contract data
        contract_data = {
            "type": Contract.TYPE_VOTING,
            "name": data["name"],
            "options": data["options"],
            "start_time": float(start_time),
            "end_time": float(end_time),
            "description": data.get("description", "")
        }
        
        # Deploy contract
        contract_address = builtins.GCN.blockchain.deploy_contract(
            contract_data=contract_data,
            creator=data["creator"]
        )
        
        return jsonify({
            "status": "success",
            "message": f"Voting contract '{data['name']}' deployed successfully",
            "contract_address": contract_address
        }), 201
        
    except ContractError as e:
        logger.error(f"Voting contract creation error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400
        
    except Exception as e:
        logger.error(f"Error creating voting contract: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500