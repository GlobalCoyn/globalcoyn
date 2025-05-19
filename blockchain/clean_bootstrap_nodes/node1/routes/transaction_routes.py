"""
Transaction routes for the GlobalCoyn blockchain node.
"""
import os
import json
import sys
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
logger = logging.getLogger("transaction_routes")

# Create transactions blueprint
transactions_bp = Blueprint('transactions', __name__)

# Define a dummy decorator for compatibility
def transaction_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        return f(None, *args, **kwargs)
    return decorated

@transactions_bp.route('/history', methods=['GET'])
def get_transaction_history():
    """
    Get transaction history from the blockchain
    """
    try:
        # Optional address filter
        address = request.args.get('address')
        limit = int(request.args.get('limit', 50))
        
        transactions = []
        
        if address:
            # Get transactions for specific address
            transactions = GCN.blockchain.get_address_transactions(address)
            
            # Apply limit
            if limit > 0:
                transactions = transactions[:limit]
                
            return jsonify({
                "address": address,
                "transactions": transactions,
                "count": len(transactions)
            })
        else:
            # Get all transactions from the blockchain
            for block in GCN.blockchain.chain:
                for tx in block.transactions:
                    tx_data = tx.to_dict()
                    tx_data['block_index'] = block.index
                    tx_data['block_hash'] = block.hash
                    tx_data['confirmed'] = True
                    transactions.append(tx_data)
                    
                    # Apply limit
                    if limit > 0 and len(transactions) >= limit:
                        break
                        
                if limit > 0 and len(transactions) >= limit:
                    break
            
            # Also include mempool transactions
            mempool_count = 0
            if len(transactions) < limit or limit <= 0:
                remaining = limit - len(transactions) if limit > 0 else 0
                
                for tx in GCN.blockchain.mempool.get_transactions(remaining if remaining > 0 else None):
                    tx_data = tx.to_dict()
                    tx_data['confirmed'] = False
                    transactions.append(tx_data)
                    mempool_count += 1
            
            # Sort by timestamp, newest first
            transactions.sort(key=lambda tx: tx.get('timestamp', 0), reverse=True)
            
            return jsonify({
                "transactions": transactions,
                "count": len(transactions),
                "mempool_count": mempool_count,
                "blockchain_count": len(transactions) - mempool_count
            })
    except Exception as e:
        logger.error(f"Error getting transaction history: {str(e)}")
        return jsonify({"error": str(e)}), 500

@transactions_bp.route('/mempool', methods=['GET'])
def get_mempool():
    """
    Get transactions in the mempool
    """
    try:
        transactions = []
        
        for tx in GCN.blockchain.mempool.get_transactions():
            transactions.append(tx.to_dict())
        
        return jsonify({
            "mempool": transactions,
            "count": len(transactions)
        })
    except Exception as e:
        logger.error(f"Error getting mempool: {str(e)}")
        return jsonify({"error": str(e)}), 500

@transactions_bp.route('/verify/<tx_hash>', methods=['GET'])
def verify_transaction(tx_hash):
    """
    Verify a transaction's validity
    """
    try:
        # Check mempool first
        tx = GCN.blockchain.mempool.get_transaction_by_hash(tx_hash)
        
        if tx:
            # Transaction is in mempool
            return jsonify({
                "transaction": tx.to_dict(),
                "status": "pending",
                "is_valid": tx.is_valid()
            })
        
        # Check blockchain
        for block in GCN.blockchain.chain:
            for tx in block.transactions:
                if tx.tx_hash == tx_hash:
                    return jsonify({
                        "transaction": tx.to_dict(),
                        "status": "confirmed",
                        "block_index": block.index,
                        "block_hash": block.hash,
                        "is_valid": tx.is_valid()
                    })
        
        # Transaction not found
        return jsonify({
            "error": "Transaction not found",
            "tx_hash": tx_hash
        }), 404
    except Exception as e:
        logger.error(f"Error verifying transaction: {str(e)}")
        return jsonify({"error": str(e)}), 500

@transactions_bp.route('/fees', methods=['GET'])
def get_transaction_fees():
    """
    Get recommended transaction fees
    """
    try:
        # Calculate average fee from recent transactions
        fee_data = {
            "low": 0.001,      # Minimum fee
            "medium": 0.005,   # Standard fee
            "high": 0.01       # Priority fee
        }
        
        # If we have blocks, calculate from actual transactions
        if GCN.blockchain.chain:
            fees = []
            
            # Get fees from last 100 blocks
            block_count = min(100, len(GCN.blockchain.chain))
            for i in range(len(GCN.blockchain.chain) - block_count, len(GCN.blockchain.chain)):
                block = GCN.blockchain.chain[i]
                for tx in block.transactions:
                    if tx.fee > 0 and not tx.is_coinbase():
                        fees.append(tx.fee)
            
            if fees:
                # Sort fees
                fees.sort()
                
                # Calculate percentiles
                if len(fees) >= 3:
                    fee_data["low"] = fees[int(len(fees) * 0.1)]
                    fee_data["medium"] = fees[int(len(fees) * 0.5)]
                    fee_data["high"] = fees[int(len(fees) * 0.9)]
        
        return jsonify(fee_data)
    except Exception as e:
        logger.error(f"Error getting transaction fees: {str(e)}")
        return jsonify({"error": str(e)}), 500

@transactions_bp.route('', methods=['POST'])
def submit_transaction():
    """
    Submit a new transaction to the blockchain
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['sender', 'recipient', 'amount', 'signature']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Create transaction using Transaction from builtins
        Transaction = builtins.Transaction
        
        tx = Transaction(
            sender=data['sender'],
            recipient=data['recipient'],
            amount=float(data['amount']),
            fee=float(data.get('fee', 0.001)),
            signature=data['signature']
        )
        
        # Set transaction hash
        tx.calculate_hash()
        
        # Add to mempool
        success = GCN.blockchain.add_transaction(tx)
        
        if success:
            # Broadcast to network
            GCN.broadcast_transaction(tx)
            
            return jsonify({
                "status": "success",
                "message": "Transaction added to mempool",
                "transaction": tx.to_dict(),
                "tx_hash": tx.tx_hash
            }), 201
        else:
            return jsonify({
                "status": "error",
                "message": "Transaction validation failed"
            }), 400
    except Exception as e:
        logger.error(f"Error submitting transaction: {str(e)}")
        return jsonify({"error": str(e)}), 500

@transactions_bp.route('/<tx_hash>', methods=['GET'])
def get_transaction(tx_hash):
    """
    Get details of a specific transaction
    """
    try:
        # Check mempool first
        tx = GCN.blockchain.mempool.get_transaction_by_hash(tx_hash)
        
        if tx:
            # Transaction is in mempool
            return jsonify({
                "transaction": tx.to_dict(),
                "status": "pending"
            })
        
        # Check blockchain
        for block in GCN.blockchain.chain:
            for tx in block.transactions:
                if tx.tx_hash == tx_hash:
                    return jsonify({
                        "transaction": tx.to_dict(),
                        "status": "confirmed",
                        "block_index": block.index,
                        "block_hash": block.hash,
                        "confirmations": len(GCN.blockchain.chain) - block.index
                    })
        
        # Transaction not found
        return jsonify({
            "error": "Transaction not found",
            "tx_hash": tx_hash
        }), 404
    except Exception as e:
        logger.error(f"Error getting transaction: {str(e)}")
        return jsonify({"error": str(e)}), 500