"""
Blockchain routes for the GlobalCoyn blockchain node.
"""
import os
import json
import logging
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
logger = logging.getLogger("blockchain_routes")

# Create blockchain blueprint
blockchain_bp = Blueprint('blockchain', __name__)

@blockchain_bp.route('/', methods=['GET'])
def get_blockchain_info():
    """Get blockchain status"""
    try:
        chain_length = len(GCN.blockchain.chain)
        latest_block = GCN.blockchain.chain[-1] if chain_length > 0 else None
        
        # Calculate difficulty
        difficulty_info = GCN.blockchain.get_mining_difficulty()
        
        data = {
            "status": "online",
            "chain_length": chain_length,
            "latest_block_hash": latest_block.hash if latest_block else None,
            "latest_block_timestamp": latest_block.timestamp if latest_block else None,
            "difficulty": difficulty_info,
            "transactions_in_mempool": GCN.blockchain.mempool.size(),
            "node_count": len(GCN.peers) + 1,  # Count of connected nodes plus this node
            "network_mode": "decentralized" if not GCN.dev_mode else "development"
        }
        
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error getting blockchain info: {str(e)}")
        return jsonify({"error": str(e)}), 500

@blockchain_bp.route('/chain', methods=['GET'])
def get_chain():
    """Get the full blockchain"""
    try:
        chain = []
        
        for block in GCN.blockchain.chain:
            chain.append(block.to_dict())
        
        return jsonify({"chain": chain}), 200
    except Exception as e:
        logger.error(f"Error getting chain: {str(e)}")
        return jsonify({"error": str(e)}), 500

@blockchain_bp.route('/blocks/latest', methods=['GET'])
def get_latest_block():
    """Get the latest block"""
    try:
        if not GCN.blockchain.chain:
            return jsonify({"error": "Blockchain is empty"}), 404
            
        latest_block = GCN.blockchain.chain[-1]
        return jsonify(latest_block.to_dict()), 200
    except Exception as e:
        logger.error(f"Error getting latest block: {str(e)}")
        return jsonify({"error": str(e)}), 500

@blockchain_bp.route('/blocks/<string:hash>', methods=['GET'])
def get_block_by_hash(hash):
    """Get a specific block by hash"""
    try:
        block = GCN.blockchain.get_block_by_hash(hash)
        
        if block:
            return jsonify(block.to_dict()), 200
        else:
            return jsonify({"error": "Block not found"}), 404
    except Exception as e:
        logger.error(f"Error getting block by hash: {str(e)}")
        return jsonify({"error": str(e)}), 500

@blockchain_bp.route('/blocks/<int:height>', methods=['GET'])
def get_block_by_height(height):
    """Get a specific block by height"""
    try:
        block = GCN.blockchain.get_block_by_height(height)
        
        if block:
            return jsonify(block.to_dict()), 200
        else:
            return jsonify({"error": "Block not found"}), 404
    except Exception as e:
        logger.error(f"Error getting block by height: {str(e)}")
        return jsonify({"error": str(e)}), 500

@blockchain_bp.route('/mempool', methods=['GET'])
def get_mempool():
    """Get current mempool transactions"""
    try:
        mempool = []
        
        for tx in GCN.blockchain.mempool.get_transactions():
            mempool.append(tx.to_dict())
        
        return jsonify({"mempool": mempool}), 200
    except Exception as e:
        logger.error(f"Error getting mempool: {str(e)}")
        return jsonify({"error": str(e)}), 500

@blockchain_bp.route('/stats', methods=['GET'])
def get_blockchain_stats():
    """Get blockchain statistics"""
    try:
        stats = GCN.blockchain.get_blockchain_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting blockchain stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@blockchain_bp.route('/difficulty', methods=['GET'])
def get_difficulty():
    """Get current mining difficulty"""
    try:
        difficulty = GCN.blockchain.get_mining_difficulty()
        return jsonify(difficulty), 200
    except Exception as e:
        logger.error(f"Error getting difficulty: {str(e)}")
        return jsonify({"error": str(e)}), 500

@blockchain_bp.route('/blocks/mine', methods=['POST'])
def mine_block():
    """Mine a new block"""
    try:
        data = request.get_json() or {}
        miner_address = data.get('miner_address', 'BLOCKCHAIN_REWARD')
        
        # Use the utils function from builtins
        validate_address_format = builtins.validate_address_format
        if not validate_address_format(miner_address):
            return jsonify({"error": "Invalid miner address format"}), 400
        
        # Mine a block
        new_block = GCN.blockchain.mine_block(miner_address)
        
        if new_block:
            # Broadcast to network
            GCN.broadcast_block(new_block)
            
            return jsonify({
                "status": "success", 
                "message": f"Block {new_block.index} mined successfully",
                "block": new_block.to_dict()
            }), 201
        else:
            return jsonify({"status": "error", "message": "Mining failed"}), 400
    except Exception as e:
        logger.error(f"Error mining block: {str(e)}")
        return jsonify({"error": str(e)}), 500