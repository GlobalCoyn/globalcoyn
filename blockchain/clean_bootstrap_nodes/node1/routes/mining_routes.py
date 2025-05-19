"""
Mining routes for the GlobalCoyn blockchain node.
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
logger = logging.getLogger("mining_routes")

# Create mining blueprint
mining_bp = Blueprint('mining', __name__)

@mining_bp.route('/start', methods=['POST'])
def start_mining():
    """Start continuous mining process"""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        data = request.get_json()
        
        if 'mining_address' not in data:
            return jsonify({"error": "Missing mining_address"}), 400
            
        mining_address = data['mining_address']
        
        # Use the utils function from builtins
        validate_address_format = builtins.validate_address_format
        if not validate_address_format(mining_address):
            return jsonify({"error": "Invalid mining address format"}), 400
        
        # Start mining
        GCN.start_mining(mining_address)
        
        return jsonify({
            "status": "success", 
            "message": f"Mining started for address {mining_address}"
        }), 200
    except Exception as e:
        logger.error(f"Error starting mining: {str(e)}")
        return jsonify({"error": str(e)}), 500

@mining_bp.route('/stop', methods=['POST'])
def stop_mining():
    """Stop continuous mining process"""
    try:
        # Stop mining
        GCN.stop_mining()
        
        return jsonify({
            "status": "success", 
            "message": "Mining stopped"
        }), 200
    except Exception as e:
        logger.error(f"Error stopping mining: {str(e)}")
        return jsonify({"error": str(e)}), 500

@mining_bp.route('/status', methods=['GET'])
def mining_status():
    """Get current mining status"""
    try:
        status = {
            "is_mining": GCN.is_mining,
            "mining_address": GCN.mining_address if GCN.is_mining else None,
            "difficulty": GCN.blockchain.get_mining_difficulty()
        }
        
        # If mining, add additional information
        if GCN.is_mining:
            # Get mining stats for current address
            blocks_mined = 0
            total_rewards = 0.0
            
            for block in GCN.blockchain.chain:
                for tx in block.transactions:
                    if hasattr(tx, 'is_coinbase') and tx.is_coinbase() and tx.recipient == GCN.mining_address:
                        blocks_mined += 1
                        total_rewards += tx.amount
            
            status.update({
                "blocks_mined": blocks_mined,
                "total_rewards": total_rewards
            })
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting mining status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@mining_bp.route('/hashrate', methods=['GET'])
def get_hashrate():
    """Get estimated mining hashrate"""
    try:
        # In a real implementation, this would track actual hash attempts and time
        # For now, return a simulated hashrate based on difficulty
        difficulty_info = GCN.blockchain.get_mining_difficulty()
        
        # Higher difficulty generally means higher hashrate in the network
        estimated_network_hashrate = difficulty_info.get("current_difficulty", 1) * 1000  # Simulated value
        
        # Node's hashrate would be a fraction of the network
        # For simulation purposes, assume 1-5% of network hashrate
        import random
        node_percentage = random.uniform(0.01, 0.05)  # 1-5%
        node_hashrate = estimated_network_hashrate * node_percentage
        
        return jsonify({
            "node_hashrate": node_hashrate,
            "node_hashrate_readable": f"{node_hashrate/1000:.2f} kH/s",
            "estimated_network_hashrate": estimated_network_hashrate,
            "estimated_network_hashrate_readable": f"{estimated_network_hashrate/1000:.2f} kH/s",
            "is_mining": GCN.is_mining
        })
    except Exception as e:
        logger.error(f"Error getting hashrate: {str(e)}")
        return jsonify({"error": str(e)}), 500

@mining_bp.route('/rewards', methods=['GET'])
def get_mining_rewards():
    """Get mining reward information"""
    try:
        # Calculate current reward
        current_reward = GCN.blockchain.miner.calculate_reward(len(GCN.blockchain.chain))
        
        # Calculate next halving
        halving_interval = GCN.blockchain.miner.HALVING_INTERVAL
        current_block = len(GCN.blockchain.chain)
        next_halving = ((current_block // halving_interval) + 1) * halving_interval
        blocks_until_halving = next_halving - current_block
        
        # Calculate next reward
        next_reward = current_reward / 2
        
        # Calculate total supply from rewards
        total_supply = 0
        for block in GCN.blockchain.chain:
            for tx in block.transactions:
                if hasattr(tx, 'is_coinbase') and tx.is_coinbase():
                    total_supply += tx.amount
        
        reward_info = {
            "current_reward": current_reward,
            "next_halving_block": next_halving,
            "blocks_until_halving": blocks_until_halving,
            "next_reward": next_reward,
            "total_supply_from_mining": total_supply,
            "max_supply": GCN.blockchain.miner.MAX_SUPPLY
        }
        
        return jsonify(reward_info)
    except Exception as e:
        logger.error(f"Error getting mining rewards: {str(e)}")
        return jsonify({"error": str(e)}), 500