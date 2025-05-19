"""
Blockchain Node
--------------
This is a minimal implementation of a blockchain node.
It only handles blockchain operations and P2P networking.

Environment variables:
- GCN_NODE_NUM: Node number (default: 1)
- GCN_P2P_PORT: P2P networking port (default: 9000 for node 1, 9001 for node 2, etc.)
- GCN_WEB_PORT: HTTP API port (default: 8001 for node 1, 8002 for node 2, etc.)
"""

import os
import sys
import json
import time
import socket
import threading
import datetime
from typing import Dict, Any, List, Optional
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Calculate paths
current_dir = os.path.dirname(os.path.abspath(__file__))
nodes_dir = os.path.dirname(current_dir)
blockchain_dir = os.path.dirname(nodes_dir)
core_dir = os.path.join(blockchain_dir, "core")

# Add the directories to Python path
sys.path.append(current_dir)
sys.path.append(core_dir)

from flask import Flask, jsonify, request, abort, make_response
from flask_cors import CORS

# Import directly from core directory with module paths
sys.path.append(os.path.dirname(core_dir))  # Add parent of core to path

# Now import using direct imports
from coin import GlobalCoyn, Coin
from blockchain import Transaction as BlockchainTransaction

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Basic routes for blockchain node operations

@app.route('/api/blockchain', methods=['GET'])
def get_blockchain_info():
    """Get blockchain status"""
    try:
        chain_length = len(GCN.blockchain.chain)
        latest_block = GCN.blockchain.chain[-1] if chain_length > 0 else None
        
        # Get Bitcoin-style difficulty information
        difficulty_bits = GCN.blockchain.bits if hasattr(GCN.blockchain, 'bits') else None
        difficulty_target = GCN.blockchain.target if hasattr(GCN.blockchain, 'target') else None
        
        # Calculate a difficulty metric similar to Bitcoin's difficulty representation
        # Higher number = more difficult
        if difficulty_target:
            difficulty_metric = 0x00000000FFFF0000000000000000000000000000000000000000000000000000 / difficulty_target
        else:
            difficulty_metric = latest_block.difficulty_bits if latest_block else 1
        
        data = {
            "status": "online",
            "chain_length": chain_length,
            "latest_block_hash": latest_block.hash if latest_block else None,
            "latest_block_timestamp": latest_block.timestamp if latest_block else None,
            "difficulty": difficulty_metric,  # More Bitcoin-like difficulty metric
            "difficulty_bits": difficulty_bits,  # Raw bits format
            "difficulty_target": difficulty_target,  # Actual target threshold
            "transactions_in_mempool": len(GCN.blockchain.mempool),
            "node_count": len(GCN.peers) + 1,  # Count of connected nodes plus this node
            "network_mode": "decentralized"
        }
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chain', methods=['GET'])
def get_chain():
    """Get the full blockchain"""
    try:
        chain = []
        
        for block in GCN.blockchain.chain:
            block_data = {
                "index": block.index,
                "hash": block.hash,
                "previous_hash": block.previous_hash,
                "timestamp": block.timestamp,
                "transactions": [tx.to_dict() for tx in block.transactions],
                "nonce": block.nonce,
                "difficulty_bits": block.difficulty_bits
            }
            chain.append(block_data)
        
        return jsonify({"chain": chain}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/mempool', methods=['GET'])
def get_mempool():
    """Get current mempool transactions"""
    try:
        mempool = []
        
        for tx in GCN.blockchain.mempool:
            mempool.append(tx.to_dict())
        
        return jsonify({"mempool": mempool}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/balance/<address>', methods=['GET'])
def get_balance(address):
    """Get balance for a wallet address"""
    try:
        balance = GCN.blockchain.get_balance(address)
        return jsonify({"address": address, "balance": balance}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def validate_json(*required_fields: str):
    """Decorator to validate JSON payload"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400
            
            data = request.get_json()
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return jsonify({
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/api/transaction', methods=['POST'])
@validate_json('sender', 'recipient', 'amount', 'signature')
def add_transaction():
    """Add a transaction to the blockchain"""
    try:
        data = request.get_json()
        
        # Create blockchain transaction
        # Note: timestamp is generated automatically inside the Transaction class
        tx = BlockchainTransaction(
            sender=data['sender'],
            recipient=data['recipient'],
            amount=float(data['amount']),
            signature=data['signature'],
            transaction_type=data.get('transaction_type', 'TRANSFER'),
            fee=float(data.get('fee', 0.001)),
            price=data.get('price')
        )
        
        # Add to mempool
        success = GCN.blockchain.add_transaction_to_mempool(tx)
        
        if success:
            return jsonify({"status": "success", "transaction": tx.to_dict()}), 201
        else:
            return jsonify({"status": "error", "message": "Transaction validation failed"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/mine', methods=['POST'])
def mine_block():
    """Mine a new block with Bitcoin-style proof-of-work"""
    try:
        data = request.get_json() or {}
        miner_address = data.get('miner_address', 'BLOCKCHAIN_REWARD')
        max_nonce_attempts = data.get('max_nonce_attempts', 100000)  # Limit attempts per request
        
        # Log mining attempt
        print(f"Mining attempt started for address: {miner_address}")
        print(f"Current difficulty bits: {hex(GCN.blockchain.bits) if hasattr(GCN.blockchain, 'bits') else 'N/A'}")
        print(f"Current target: {hex(GCN.blockchain.target) if hasattr(GCN.blockchain, 'target') else 'N/A'}")
        
        # Non-blocking variant that attempts a limited number of hashes per request
        start_time = time.time()
        
        # Prepare block transactions
        block_transactions = []
        
        # Add mining reward transaction
        reward = GCN.blockchain.get_mining_reward()
        reward_tx = BlockchainTransaction("0", miner_address, reward, 0)
        block_transactions.append(reward_tx)
        
        # Add transactions from mempool (sorted by fee)
        sorted_transactions = sorted(GCN.blockchain.mempool, key=lambda x: x.fee, reverse=True)
        block_transactions.extend(sorted_transactions[:100])  # Limit to 100 transactions per block
        
        # Create new block with current timestamp
        # Import Block from blockchain module
        from blockchain import Block
        
        new_block = Block(
            index=len(GCN.blockchain.chain),
            previous_hash=GCN.blockchain.chain[-1].hash,
            timestamp=time.time(),
            transactions=block_transactions,
            nonce=0,
            difficulty_bits=GCN.blockchain.bits
        )
        
        # Perform proof of work for a limited number of attempts
        found_valid_hash = False
        hash_attempts = 0
        
        while hash_attempts < max_nonce_attempts:
            new_block.nonce += 1
            hash_attempts += 1
            
            if hash_attempts % 10000 == 0:
                print(f"Mining progress: {hash_attempts} attempts")
            
            # Calculate new hash
            new_block.hash = new_block.calculate_hash()
            
            # Convert hash to integer and compare with target
            hash_int = int(new_block.hash, 16)
            if hash_int <= GCN.blockchain.target:
                # Found a valid hash!
                found_valid_hash = True
                break
        
        mining_time = time.time() - start_time
        
        if found_valid_hash:
            # We found a valid block - add it to the chain
            # Remove mined transactions from mempool
            for tx in block_transactions[1:]:  # Skip reward transaction
                if tx in GCN.blockchain.mempool:
                    GCN.blockchain.mempool.remove(tx)
            
            # Add block to chain
            GCN.blockchain.chain.append(new_block)
            
            # Adjust difficulty for next block
            GCN.blockchain.adjust_difficulty()
            
            # Save blockchain
            GCN.blockchain.save_chain_to_disk()
            
            # Log successful mining
            print(f"Block successfully mined in {mining_time:.2f} seconds after {hash_attempts} attempts!")
            print(f"Block hash: {new_block.hash}")
            print(f"Nonce used: {new_block.nonce}")
            
            block_data = {
                "index": new_block.index,
                "hash": new_block.hash,
                "previous_hash": new_block.previous_hash,
                "timestamp": new_block.timestamp,
                "transactions": [tx.to_dict() for tx in new_block.transactions],
                "nonce": new_block.nonce,
                "difficulty_bits": new_block.difficulty_bits,
                "mining_time_seconds": mining_time,
                "hash_attempts": hash_attempts
            }
            return jsonify({
                "status": "success",
                "message": "Successfully mined a new block",
                "block": block_data
            }), 200
        else:
            # We didn't find a valid hash in this attempt
            return jsonify({
                "status": "in_progress",
                "message": f"No valid hash found after {hash_attempts} attempts",
                "current_nonce": new_block.nonce,
                "elapsed_time": mining_time
            }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
        
# Add a new async mining endpoint that performs a limited amount of work per request
@app.route('/api/mine_async', methods=['POST'])
def mine_async():
    """Mine asynchronously with limited work per request but more efficient"""
    try:
        data = request.get_json() or {}
        miner_address = data.get('miner_address', 'BLOCKCHAIN_REWARD')
        max_attempts = data.get('max_attempts', 50000)  # Default to 50k attempts per call
        # If the client requests a much higher value, respect it for better mining performance
        max_attempts = min(max_attempts, 500000)  # Cap at 500k attempts per call
        
        # Short-circuit if we've reached max supply
        if GCN.blockchain.get_current_supply() >= GCN.blockchain.MAX_SUPPLY:
            return jsonify({"status": "error", "message": "Maximum coin supply reached"}), 400
            
        # Perform limited mining attempts
        start_time = time.time()
        found_hash = False
        new_block = None
        
        try:
            # Create a test block with updated timestamp - use the Block class directly
            # Import Block class from the same module as BlockchainTransaction
            from blockchain import Block
            
            test_block = Block(
                index=len(GCN.blockchain.chain),
                previous_hash=GCN.blockchain.chain[-1].hash,
                timestamp=time.time(),
                transactions=[BlockchainTransaction("0", miner_address, GCN.blockchain.get_mining_reward(), 0)],
                nonce=0,
                difficulty_bits=GCN.blockchain.bits
            )
            
            # Use a more efficient approach for trying nonces
            # - Start with a random nonce to avoid overlap between mining attempts
            # - Try sequential nonces from there
            import random
            starting_nonce = random.randint(0, 1000000)
            test_block.nonce = starting_nonce
            
            # Try different nonces for a limited number of attempts
            for i in range(max_attempts):
                test_block.nonce += 1
                test_hash = test_block.calculate_hash()
                
                # Check if hash is valid
                hash_int = int(test_hash, 16)
                if hash_int <= GCN.blockchain.target:
                    # Found a valid hash! Now create the full block
                    found_hash = True
                    
                    # Create transactions for the block
                    block_transactions = []
                    
                    # Add mining reward transaction
                    reward = GCN.blockchain.get_mining_reward()
                    reward_tx = BlockchainTransaction("0", miner_address, reward, 0)
                    block_transactions.append(reward_tx)
                    
                    # Add transactions from mempool (sorted by fee)
                    sorted_transactions = sorted(GCN.blockchain.mempool, key=lambda x: x.fee, reverse=True)
                    block_transactions.extend(sorted_transactions[:100])  # Limit to 100 transactions per block
                    
                    # Create the new block with the valid nonce we found
                    # We already imported Block from blockchain above
                    new_block = Block(
                        index=len(GCN.blockchain.chain),
                        previous_hash=GCN.blockchain.chain[-1].hash,
                        timestamp=time.time(),
                        transactions=block_transactions,
                        nonce=test_block.nonce,
                        difficulty_bits=GCN.blockchain.bits
                    )
                    
                    # Reuse the hash we already calculated
                    new_block.hash = test_hash
                    
                    # Remove mined transactions from mempool
                    for tx in block_transactions[1:]:  # Skip reward transaction
                        if tx in GCN.blockchain.mempool:
                            GCN.blockchain.mempool.remove(tx)
                    
                    # Add block to chain
                    GCN.blockchain.chain.append(new_block)
                    
                    # Adjust difficulty for next block
                    GCN.blockchain.adjust_difficulty()
                    
                    # Save blockchain
                    GCN.blockchain.save_chain_to_disk()
                    
                    print(f"Block successfully mined in {time.time() - start_time:.2f} seconds after {i} attempts!")
                    print(f"Block hash: {new_block.hash}")
                    print(f"Nonce used: {new_block.nonce}")
                    
                    break
                
                # Log progress periodically to confirm mining is working
                if i > 0 and i % 100000 == 0:
                    print(f"Mining progress: Tried {i} hashes so far...")
                    
        except Exception as mining_error:
            print(f"Mining error: {str(mining_error)}")
            import traceback
            traceback.print_exc()
            
        mining_time = time.time() - start_time
        
        if found_hash and new_block:
            block_data = {
                "index": new_block.index,
                "hash": new_block.hash,
                "previous_hash": new_block.previous_hash,
                "timestamp": new_block.timestamp,
                "transactions": [tx.to_dict() for tx in new_block.transactions],
                "nonce": new_block.nonce,
                "difficulty_bits": new_block.difficulty_bits,
                "mining_time_seconds": mining_time,
                "hash_attempts": max_attempts
            }
            return jsonify({
                "status": "success",
                "message": "Successfully mined a new block",
                "block": block_data
            }), 200
        else:
            # No valid hash found in this batch
            return jsonify({
                "status": "continue",
                "message": f"No valid hash found after {max_attempts} attempts",
                "target": hex(GCN.blockchain.target),
                "difficulty_bits": hex(GCN.blockchain.bits),
                "time_spent": mining_time,
                "starting_nonce": starting_nonce
            }), 200
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Make GCN available to other modules
import builtins
builtins.GCN = None  # Will be set after GCN is initialized

# Import routes after setting up GCN placeholder
from routes.network import network_bp
from routes.transactions import transactions_bp

# Register blueprints
app.register_blueprint(network_bp, url_prefix='/api/network')
app.register_blueprint(transactions_bp, url_prefix='/api')

# Additional endpoints for compatibility with blockchain_client.py in the exchange
@app.route('/api/blocks/latest', methods=['GET'])
def get_latest_block():
    """Get the latest block in the blockchain"""
    try:
        if not GCN.blockchain.chain:
            return jsonify({"error": "Blockchain is empty"}), 404
            
        latest_block = GCN.blockchain.chain[-1]
        block_data = {
            "index": latest_block.index,
            "hash": latest_block.hash,
            "previous_hash": latest_block.previous_hash,
            "timestamp": latest_block.timestamp,
            "transactions": [tx.to_dict() for tx in latest_block.transactions],
            "nonce": latest_block.nonce,
            "difficulty_target": latest_block.difficulty_target
        }
        
        return jsonify(block_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/blocks/<block_hash>', methods=['GET'])
def get_block_by_hash(block_hash):
    """Get a block by its hash"""
    try:
        for block in GCN.blockchain.chain:
            if block.hash == block_hash:
                block_data = {
                    "index": block.index,
                    "hash": block.hash,
                    "previous_hash": block.previous_hash,
                    "timestamp": block.timestamp,
                    "transactions": [tx.to_dict() for tx in block.transactions],
                    "nonce": block.nonce,
                    "difficulty_target": block.difficulty_target
                }
                return jsonify(block_data), 200
                
        return jsonify({"error": "Block not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Main entry point
if __name__ == '__main__':
    # Get configuration from environment variables or use defaults
    node_num = int(os.environ.get('GCN_NODE_NUM', 1))
    p2p_port = int(os.environ.get('GCN_P2P_PORT', 9000 + node_num - 1))
    web_port = int(os.environ.get('GCN_WEB_PORT', 8000 + node_num))
    
    # Configure seed nodes based on node number
    seed_nodes = []
    if node_num == 1:
        # Node 1 connects to Node 2
        seed_nodes = [
            ("127.0.0.1", 9001),  # Node 2 running locally
            ("localhost", 9001)   # Another way to reference Node 2
        ]
    else:
        # Node 2 (or other nodes) connect to Node 1
        seed_nodes = [
            ("127.0.0.1", 9000),  # Node 1 running locally
            ("localhost", 9000)   # Another way to reference Node 1
        ]
    
    # Start blockchain node in decentralized mode
    print(f"Starting Blockchain Node {node_num} in decentralized mode...")
    print(f"P2P Port: {p2p_port}")
    print(f"Web Port: {web_port}")
    print(f"Seed nodes: {seed_nodes}")
    
    # Define Node class if it doesn't exist in GlobalCoyn
    from collections import namedtuple
    
    # Initialize blockchain node
    GCN = GlobalCoyn(port=p2p_port, dev_mode=False)
    
    # Make sure the Node class exists
    if not hasattr(GCN, 'Node'):
        # Create a Node class dynamically if it doesn't exist
        GCN.Node = namedtuple('Node', ['address', 'port', 'socket', 'last_seen'])
        # Add default value for socket and last_seen
        GCN.Node.__new__.__defaults__ = (None, None, None, time.time())
        print("Added Node class to GCN")
    
    GCN.seed_nodes = seed_nodes
    GCN.start()
    
    # Make GCN available to other modules
    builtins.GCN = GCN
    
    # Manual connection to seed nodes
    def connect_to_peers():
        """Manually connect to seed nodes after a delay to ensure everything is running"""
        time.sleep(5)  # Wait for network initialization
        for host, port in seed_nodes:
            try:
                # Try to establish connection using socket
                print(f"Manually connecting to {host}:{port}...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((host, port))
                # Let the GlobalCoyn _handle_connection take over
                node_id = f"{host}:{port}"
                GCN.peers[node_id] = GCN.Node(address=host, port=port, socket=sock)
                threading.Thread(
                    target=GCN._handle_connection,
                    args=(sock, (host, port)),
                    daemon=True
                ).start()
                print(f"Manually connected to {host}:{port}")
            except Exception as e:
                print(f"Error connecting to {host}:{port}: {e}")
    
    # Start manual connection attempt in background thread
    threading.Thread(target=connect_to_peers, daemon=True).start()
    
    # Force immediate blockchain sync after startup
    def force_initial_sync():
        """Force immediate blockchain sync with other nodes"""
        print("Starting initial blockchain sync...")
        time.sleep(10)  # Give some time for node to fully initialize
        try:
            # Import necessary modules here to avoid circular imports
            import requests
            
            # Trigger sync on this node
            sync_url = f"http://localhost:{web_port}/api/network/sync"
            print(f"Triggering sync at {sync_url}")
            response = requests.post(sync_url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"Initial sync result: {result}")
                if result.get('synchronized', False):
                    print(f"Successfully synced with network, chain length: {result.get('local_chain_length_after', 0)}")
                else:
                    print(f"Sync not needed or failed: {result.get('sync_message', 'Unknown')}")
            else:
                print(f"Sync request failed with status {response.status_code}")
        except Exception as e:
            print(f"Error during initial sync: {e}")
            
    # Start initial sync in background thread
    threading.Thread(target=force_initial_sync, daemon=True).start()
    
    print(f"Blockchain Node {node_num} started successfully - P2P networking enabled")
    
    # Start Flask server
    try:
        print(f"Starting web server on port {web_port}")
        app.run(host='0.0.0.0', port=web_port, debug=True)
    except Exception as e:
        print(f"Error starting services: {e}")
        # Cleanup
        try:
            GCN.stop()
        except:
            pass