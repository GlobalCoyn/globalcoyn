"""
API routes for smart contract operations.
"""
import json
import time
import logging
from typing import Dict, Any, List, Optional
from flask import Blueprint, request, jsonify

# Create blueprint
contract_bp = Blueprint('contract_bp', __name__)

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("contract_routes")

# In-memory contract storage for testing/development
contracts = []
contract_types = [
    {
        "type": "TOKEN",
        "name": "Token Contract",
        "description": "Create a custom token on the GlobalCoyn blockchain"
    },
    {
        "type": "CROWDFUND",
        "name": "Crowdfunding Contract",
        "description": "Start a fundraising campaign with automatic fund distribution"
    },
    {
        "type": "VOTING",
        "name": "Voting Contract",
        "description": "Create a secure voting system for governance or decision-making"
    }
]

@contract_bp.route('/types', methods=['GET'])
def get_contract_types():
    """
    Get all available contract types.
    
    Returns:
        List of contract types
    """
    try:
        return jsonify({
            "status": "success",
            "contract_types": contract_types
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting contract types: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/', methods=['GET'])
def get_all_contracts():
    """
    Get all contracts in the blockchain.
    
    Returns:
        All deployed contracts
    """
    try:
        return jsonify({
            "status": "success",
            "contracts": contracts,
            "count": len(contracts)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting contracts: {str(e)}")
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
        # Filter contracts by creator
        creator_contracts = [c for c in contracts if c.get("creator") == creator]
        
        return jsonify({
            "status": "success",
            "creator": creator,
            "contracts": creator_contracts,
            "count": len(creator_contracts)
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
        # Find contract by address
        contract = next((c for c in contracts if c.get("address") == address), None)
        
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
        # Find contract by address
        contract = next((c for c in contracts if c.get("address") == address), None)
        
        if not contract:
            return jsonify({
                "status": "error",
                "message": f"Contract not found: {address}"
            }), 404
        
        return jsonify({
            "status": "success",
            "address": address,
            "state": contract.get("state", {})
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting contract state: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/templates/token', methods=['POST'])
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
        required_fields = ["creator", "name", "symbol", "initial_supply"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Generate a contract address
        contract_address = f"token_{int(time.time())}_{hash(data['name'] + data['symbol']) % 1000000}"
        
        # Create contract object
        contract = {
            "address": contract_address,
            "type": "TOKEN",
            "name": data["name"],
            "symbol": data["symbol"],
            "creator": data["creator"],
            "creation_time": int(time.time()),
            "state": {
                "name": data["name"],
                "symbol": data["symbol"],
                "decimals": int(data.get("decimals", 8)),
                "total_supply": float(data["initial_supply"]),
                "max_supply": float(data["max_supply"]) if "max_supply" in data else None,
                "balances": {
                    data["creator"]: float(data["initial_supply"])
                },
                "creator": data["creator"]
            }
        }
        
        # Add to contracts list
        contracts.append(contract)
        
        return jsonify({
            "status": "success",
            "message": f"Token contract {data['name']} ({data['symbol']}) deployed successfully",
            "contract_address": contract_address
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating token contract: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/templates/crowdfunding', methods=['POST'])
def create_crowdfunding_contract():
    """
    Create a new crowdfunding contract.
    
    Request body:
        creator: Address of the creator
        name: Campaign name
        goal: Funding goal
        deadline: Campaign end timestamp (optional)
        description: Campaign description (optional)
        
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
        required_fields = ["creator", "name", "goal"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Set default deadline if not provided (30 days from now)
        deadline = data.get("deadline", time.time() + 30*24*60*60)
        
        # Generate a contract address
        contract_address = f"crowdfund_{int(time.time())}_{hash(data['name'] + str(data['goal'])) % 1000000}"
        
        # Create contract object
        contract = {
            "address": contract_address,
            "type": "CROWDFUND",
            "name": data["name"],
            "creator": data["creator"],
            "creation_time": int(time.time()),
            "state": {
                "name": data["name"],
                "goal": float(data["goal"]),
                "deadline": float(deadline),
                "total_raised": 0,
                "contributions": {},
                "creator": data["creator"],
                "description": data.get("description", "")
            }
        }
        
        # Add to contracts list
        contracts.append(contract)
        
        return jsonify({
            "status": "success",
            "message": f"Crowdfunding contract '{data['name']}' deployed successfully",
            "contract_address": contract_address
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating crowdfunding contract: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/templates/voting', methods=['POST'])
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
        required_fields = ["creator", "name", "options"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Set default timestamps if not provided
        start_time = data.get("start_time", time.time())
        end_time = data.get("end_time", time.time() + 7*24*60*60)  # 7 days from now
        
        # Initialize votes object
        votes = {}
        for option in data["options"]:
            votes[option] = 0
        
        # Generate a contract address
        contract_address = f"voting_{int(time.time())}_{hash(data['name'] + ','.join(data['options'])) % 1000000}"
        
        # Create contract object
        contract = {
            "address": contract_address,
            "type": "VOTING",
            "name": data["name"],
            "creator": data["creator"],
            "creation_time": int(time.time()),
            "state": {
                "name": data["name"],
                "options": data["options"],
                "start_time": float(start_time),
                "end_time": float(end_time),
                "votes": votes,
                "voters": {},
                "creator": data["creator"],
                "description": data.get("description", "")
            }
        }
        
        # Add to contracts list
        contracts.append(contract)
        
        return jsonify({
            "status": "success",
            "message": f"Voting contract '{data['name']}' deployed successfully",
            "contract_address": contract_address
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating voting contract: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@contract_bp.route('/<address>/execute', methods=['POST'])
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
        
        # Find contract by address
        contract = next((c for c in contracts if c.get("address") == address), None)
        
        if not contract:
            return jsonify({
                "status": "error",
                "message": f"Contract not found: {address}"
            }), 404
        
        # Execute contract function based on contract type and function name
        function_name = data["function"]
        args = data.get("args", {})
        caller = data["caller"]
        result = {}
        
        # CROWDFUND contract functions
        if contract["type"] == "CROWDFUND":
            if function_name == "contribute":
                amount = float(args.get("amount", 0))
                
                if amount <= 0:
                    return jsonify({
                        "status": "error",
                        "message": "Contribution amount must be positive"
                    }), 400
                
                # Update state
                contract["state"]["total_raised"] = contract["state"].get("total_raised", 0) + amount
                
                if caller not in contract["state"]["contributions"]:
                    contract["state"]["contributions"][caller] = 0
                    
                contract["state"]["contributions"][caller] += amount
                
                result = {
                    "amount": amount,
                    "total_raised": contract["state"]["total_raised"],
                    "contribution": contract["state"]["contributions"][caller]
                }
            else:
                return jsonify({
                    "status": "error",
                    "message": f"Unknown function for crowdfunding contract: {function_name}"
                }), 400
        
        # VOTING contract functions
        elif contract["type"] == "VOTING":
            if function_name == "vote":
                option = args.get("option")
                
                if not option or option not in contract["state"]["options"]:
                    return jsonify({
                        "status": "error",
                        "message": "Invalid voting option"
                    }), 400
                
                # Check if already voted
                if caller in contract["state"]["voters"]:
                    return jsonify({
                        "status": "error",
                        "message": "You have already voted"
                    }), 400
                
                # Check voting period
                now = time.time()
                if now < contract["state"]["start_time"]:
                    return jsonify({
                        "status": "error",
                        "message": "Voting period has not started yet"
                    }), 400
                    
                if now > contract["state"]["end_time"]:
                    return jsonify({
                        "status": "error",
                        "message": "Voting period has ended"
                    }), 400
                
                # Update state
                contract["state"]["votes"][option] += 1
                contract["state"]["voters"][caller] = option
                
                result = {
                    "option": option,
                    "vote_count": contract["state"]["votes"][option]
                }
            else:
                return jsonify({
                    "status": "error",
                    "message": f"Unknown function for voting contract: {function_name}"
                }), 400
        
        # TOKEN contract functions handled separately via /token/:address/transfer endpoint
        elif contract["type"] == "TOKEN":
            return jsonify({
                "status": "error",
                "message": f"Token contract functions should be called through dedicated endpoints"
            }), 400
            
        else:
            return jsonify({
                "status": "error",
                "message": f"Unsupported contract type: {contract['type']}"
            }), 400
        
        return jsonify({
            "status": "success",
            "message": f"Function {function_name} executed successfully",
            "result": result
        }), 200
        
    except Exception as e:
        logger.error(f"Error executing contract: {str(e)}")
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
        
        # Find contract by address
        contract = next((c for c in contracts if c.get("address") == address), None)
        
        if not contract:
            return jsonify({
                "status": "error",
                "message": f"Contract not found: {address}"
            }), 404
        
        # Ensure contract is a token contract
        if contract["type"] != "TOKEN":
            return jsonify({
                "status": "error",
                "message": f"Contract is not a token contract: {address}"
            }), 400
        
        # Extract transfer data
        from_address = data["from_address"]
        to_address = data["to_address"]
        amount = float(data["amount"])
        
        # Validate amount
        if amount <= 0:
            return jsonify({
                "status": "error",
                "message": "Transfer amount must be positive"
            }), 400
        
        # Check balance
        balances = contract["state"]["balances"]
        sender_balance = balances.get(from_address, 0)
        
        if sender_balance < amount:
            return jsonify({
                "status": "error",
                "message": f"Insufficient balance: {sender_balance} < {amount}"
            }), 400
        
        # Update balances
        balances[from_address] = sender_balance - amount
        
        if to_address not in balances:
            balances[to_address] = 0
            
        balances[to_address] += amount
        
        # Generate transaction ID
        transaction_id = f"tx_{int(time.time())}_{hash(from_address + to_address + str(amount)) % 1000000}"
        
        return jsonify({
            "status": "success",
            "message": "Token transfer successful",
            "transaction_id": transaction_id,
            "result": {
                "from": from_address,
                "to": to_address,
                "amount": amount,
                "new_sender_balance": balances[from_address],
                "new_recipient_balance": balances[to_address]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error transferring tokens: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500