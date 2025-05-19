"""
Wallet routes for the GlobalCoyn blockchain node.
"""
import os
import json
import logging
from functools import wraps
from flask import Blueprint, request, jsonify
from typing import Dict, Optional, List, Any
import builtins

# Access GCN from builtins where it's set in app.py
try:
    GCN = builtins.GCN
except AttributeError:
    print("WARNING: GCN not found in builtins. It should be set in app.py.")
    GCN = None

# Configure logging
logger = logging.getLogger("wallet_routes")

# Create wallet blueprint
wallet_bp = Blueprint('wallet', __name__)

@wallet_bp.route('/create', methods=['POST'])
def create_wallet():
    """
    Create a new wallet address
    """
    try:
        address = GCN.wallet.create_new_address()
        
        # Save wallet to file
        GCN.wallet.save_to_file()
        
        return jsonify({
            "status": "success",
            "message": "Wallet created successfully",
            "address": address
        }), 201
    except Exception as e:
        logger.error(f"Error creating wallet: {str(e)}")
        return jsonify({"error": str(e)}), 500

@wallet_bp.route('/generate-seed', methods=['GET'])
def generate_seed_phrase():
    """
    Generate a new seed phrase
    """
    try:
        seed_phrase = GCN.wallet.generate_seed_phrase()
        
        return jsonify({
            "seed_phrase": seed_phrase
        })
    except Exception as e:
        logger.error(f"Error generating seed phrase: {str(e)}")
        return jsonify({"error": str(e)}), 500

@wallet_bp.route('/import/seed', methods=['POST'])
def import_seed():
    """
    Import a wallet from seed phrase
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        data = request.get_json()
        
        if 'seed_phrase' not in data:
            return jsonify({"error": "Missing seed_phrase"}), 400
            
        seed_phrase = data['seed_phrase']
        
        try:
            address = GCN.wallet.create_from_seed_phrase(seed_phrase)
            
            # Save wallet to file
            GCN.wallet.save_to_file()
            
            return jsonify({
                "status": "success",
                "message": "Wallet imported successfully",
                "address": address
            })
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error importing seed phrase: {str(e)}")
        return jsonify({"error": str(e)}), 500

@wallet_bp.route('/import/key', methods=['POST'])
def import_private_key():
    """
    Import a wallet from private key
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        data = request.get_json()
        
        if 'private_key' not in data:
            return jsonify({"error": "Missing private_key"}), 400
            
        private_key = data['private_key']
        
        address = GCN.wallet.import_private_key(private_key)
        
        if address:
            # Save wallet to file
            GCN.wallet.save_to_file()
            
            return jsonify({
                "status": "success",
                "message": "Private key imported successfully",
                "address": address
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Invalid private key format"
            }), 400
    except Exception as e:
        logger.error(f"Error importing private key: {str(e)}")
        return jsonify({"error": str(e)}), 500

@wallet_bp.route('/export-key', methods=['POST'])
def export_private_key():
    """
    Export private key for a wallet address
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        data = request.get_json()
        
        if 'address' not in data:
            return jsonify({"error": "Missing address"}), 400
            
        address = data['address']
        
        private_key = GCN.wallet.export_private_key(address)
        
        if private_key:
            return jsonify({
                "address": address,
                "private_key": private_key
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Address {address} not found in wallet"
            }), 404
    except Exception as e:
        logger.error(f"Error exporting private key: {str(e)}")
        return jsonify({"error": str(e)}), 500

@wallet_bp.route('/list', methods=['GET'])
def list_addresses():
    """
    List all wallet addresses
    """
    try:
        addresses = GCN.wallet.get_addresses()
        
        # Get balances for each address
        address_data = []
        for addr in addresses:
            balance = GCN.blockchain.get_balance(addr)
            address_data.append({
                "address": addr,
                "balance": balance
            })
        
        return jsonify({
            "addresses": address_data,
            "count": len(addresses)
        })
    except Exception as e:
        logger.error(f"Error listing addresses: {str(e)}")
        return jsonify({"error": str(e)}), 500

@wallet_bp.route('/balance/<address>', methods=['GET'])
def get_balance(address):
    """
    Get balance for a wallet address
    """
    try:
        # Use the utils function from builtins
        validate_address_format = builtins.validate_address_format
        
        if not validate_address_format(address):
            return jsonify({"error": "Invalid wallet address format"}), 400
            
        balance = GCN.blockchain.get_balance(address)
        
        return jsonify({
            "address": address,
            "balance": balance
        })
    except Exception as e:
        logger.error(f"Error getting balance: {str(e)}")
        return jsonify({"error": str(e)}), 500

@wallet_bp.route('/transactions/<address>', methods=['GET'])
def get_transactions(address):
    """
    Get transactions for a wallet address
    """
    try:
        # Use the utils function from builtins
        validate_address_format = builtins.validate_address_format
        
        if not validate_address_format(address):
            return jsonify({"error": "Invalid wallet address format"}), 400
            
        transactions = GCN.blockchain.get_address_transactions(address)
        
        return jsonify({
            "address": address,
            "transactions": transactions
        })
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
        return jsonify({"error": str(e)}), 500

@wallet_bp.route('/fee-estimate', methods=['GET'])
def get_fee_estimate():
    """
    Get transaction fee estimate
    """
    try:
        # For now, return static fee estimates
        # In a more advanced implementation, this would calculate based on blockchain state
        return jsonify({
            "low_priority": 0.001,
            "medium_priority": 0.005,
            "high_priority": 0.01
        })
    except Exception as e:
        logger.error(f"Error getting fee estimate: {str(e)}")
        return jsonify({"error": str(e)}), 500

@wallet_bp.route('/sign-transaction', methods=['POST'])
def sign_transaction():
    """
    Sign a transaction
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['sender', 'recipient', 'amount']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Get fields from request
        sender = data['sender']
        recipient = data['recipient']
        amount = float(data['amount'])
        fee = float(data.get('fee', 0.001))
        
        # Get wallet addresses
        wallet_addresses = GCN.wallet.get_addresses()
        
        # Check if we have the sender's address in our wallet (enforce address check)
        if sender not in wallet_addresses:
            logger.warning(f"Transaction signing attempted for address not in wallet: {sender}")
            return jsonify({
                "error": f"Address {sender} not found in wallet",
                "available_addresses": wallet_addresses
            }), 404
        
        # Sign transaction
        tx = GCN.wallet.sign_transaction(sender, recipient, amount, fee)
        
        if tx:
            # Calculate transaction hash
            tx.calculate_hash()
            
            return jsonify({
                "status": "success",
                "message": "Transaction signed successfully",
                "transaction": tx.to_dict(),
                "tx_hash": tx.tx_hash
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to sign transaction"
            }), 400
    except Exception as e:
        logger.error(f"Error signing transaction: {str(e)}")
        return jsonify({"error": str(e)}), 500

@wallet_bp.route('/validate/<address>', methods=['GET'])
def validate_address(address):
    """
    Validate a wallet address format
    """
    try:
        # Use the utils function from builtins
        validate_address_format = builtins.validate_address_format
        
        is_valid = validate_address_format(address)
        
        return jsonify({
            "address": address,
            "is_valid": is_valid
        })
    except Exception as e:
        logger.error(f"Error validating address: {str(e)}")
        return jsonify({"error": str(e)}), 500

@wallet_bp.route('/delete', methods=['DELETE'])
def delete_wallet():
    """
    Delete a wallet address
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        data = request.get_json()
        
        if 'address' not in data:
            return jsonify({"error": "Missing address"}), 400
            
        address = data['address']
        
        result = GCN.wallet.delete_wallet(address)
        
        if result:
            return jsonify({
                "status": "success",
                "message": f"Wallet address {address} deleted successfully"
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Address {address} not found in wallet"
            }), 404
    except Exception as e:
        logger.error(f"Error deleting wallet: {str(e)}")
        return jsonify({"error": str(e)}), 500

@wallet_bp.route('/mining-stats/<address>', methods=['GET'])
def get_mining_stats(address):
    """
    Get mining statistics for a wallet address
    """
    try:
        # Use the utils function from builtins
        validate_address_format = builtins.validate_address_format
        
        if not validate_address_format(address):
            return jsonify({"error": "Invalid wallet address format"}), 400
            
        # Calculate number of blocks mined by this address
        blocks_mined = 0
        total_rewards = 0.0
        
        for block in GCN.blockchain.chain:
            for tx in block.transactions:
                if hasattr(tx, 'is_coinbase') and tx.is_coinbase() and tx.recipient == address:
                    blocks_mined += 1
                    total_rewards += tx.amount
        
        stats = {
            "address": address,
            "blocks_mined": blocks_mined,
            "total_rewards": total_rewards,
            "is_currently_mining": GCN.is_mining and GCN.mining_address == address
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting mining stats: {str(e)}")
        return jsonify({"error": str(e)}), 500