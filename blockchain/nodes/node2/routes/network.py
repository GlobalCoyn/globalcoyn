from flask import Blueprint, jsonify, request
import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Import GCN from builtins - it's set globally in app.py
import socket
import time
import builtins
# Access GCN from builtins where it's set in app.py
try:
    GCN = builtins.GCN
except AttributeError:
    print("WARNING: GCN not found in builtins. It should be set in app.py.")
    GCN = None

# Define a dummy token_required decorator that does nothing
def token_required(f):
    def decorated(*args, **kwargs):
        return f(None, *args, **kwargs)
    return decorated

network_bp = Blueprint('network', __name__)

@network_bp.route('/status', methods=['GET'])
def get_network_status():
    """Get the status of the decentralized network"""
    try:
        peers = []
        for node_id, node in GCN.peers.items():
            peers.append({
                'node_id': node_id,
                'address': node.address,
                'port': node.port,
                'last_seen': time.time() - node.last_seen  # seconds since last seen
            })
            
        return jsonify({
            'status': 'online',
            'network_mode': 'decentralized' if not GCN.dev_mode else 'development',
            'this_node': {
                'address': GCN.host,
                'port': GCN.port,
                'blockchain_height': len(GCN.blockchain.chain)
            },
            'connected_peers': peers,
            'peer_count': len(peers),
            'uptime': time.time() - GCN.start_time if hasattr(GCN, 'start_time') else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@network_bp.route('/peers', methods=['GET'])
def get_peers():
    """Get list of connected peers"""
    try:
        peers = []
        for node_id, node in GCN.peers.items():
            peers.append({
                'node_id': node_id,
                'address': node.address,
                'port': node.port,
                'last_seen': time.time() - node.last_seen  # seconds since last seen
            })
            
        return jsonify({
            'peers': peers,
            'count': len(peers)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@network_bp.route('/discover', methods=['POST'])
def discover_network():
    """Process network discovery requests and trigger chain sync if needed"""
    try:
        # Make sure GCN is initialized
        import builtins
        if not hasattr(builtins, 'GCN') or builtins.GCN is None:
            return jsonify({'error': 'Blockchain node is not initialized yet'}), 500
            
        # Get the GCN instance directly from builtins for reliability
        GCN = builtins.GCN
        
        # Make sure GCN has a blockchain
        if not hasattr(GCN, 'blockchain') or GCN.blockchain is None:
            return jsonify({'error': 'Blockchain is not initialized yet'}), 500
            
        # Make sure we have a chain
        if not hasattr(GCN.blockchain, 'chain') or GCN.blockchain.chain is None:
            GCN.blockchain.chain = []
            
        # Get our current blockchain height
        local_chain_length = len(GCN.blockchain.chain)
        
        # Check if this is a notification about another node's chain length
        if request.is_json:
            data = request.get_json()
            if data and 'chain_length' in data:
                remote_chain_length = data.get('chain_length', 0)
                sender_port = data.get('sender_port', 'unknown')
                
                print(f"Received chain notification from {sender_port}: length={remote_chain_length}")
                
                # If the remote chain is longer, trigger a sync
                if remote_chain_length > local_chain_length:
                    print(f"Remote chain is longer ({remote_chain_length} > {local_chain_length}). Triggering sync...")
                    
                    # Run sync in background thread to avoid blocking
                    import threading
                    import requests
                    
                    # Capture the port outside the background function to avoid request context issues
                    port = request.host.split(':')[1] if ':' in request.host else '8002'
                    
                    def background_sync():
                        try:
                            requests.post(
                                f"http://localhost:{port}/api/network/sync",
                                timeout=5
                            )
                        except Exception as e:
                            print(f"Error during background sync: {str(e)}")
                            
                    threading.Thread(target=background_sync, daemon=True).start()
                    
                    return jsonify({
                        'success': True,
                        'action': 'sync_triggered',
                        'local_chain_length': local_chain_length,
                        'remote_chain_length': remote_chain_length
                    })
        
        # Make sure peers is initialized
        if not hasattr(GCN, 'peers') or GCN.peers is None:
            GCN.peers = {}
            
        # Get peer information
        discovered_peers = []
        for node_id, node in GCN.peers.items():
            discovered_peers.append({
                'node_id': node_id,
                'address': node.address,
                'port': node.port
            })
            
        return jsonify({
            'success': True,
            'local_chain_length': local_chain_length,
            'discovered_peers': discovered_peers,
            'peer_count': len(discovered_peers)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@network_bp.route('/sync', methods=['POST'])
def sync_with_network():
    """Synchronize blockchain with other nodes"""
    try:
        # Make sure GCN is initialized
        import builtins
        if not hasattr(builtins, 'GCN') or builtins.GCN is None:
            return jsonify({'error': 'Blockchain node is not initialized yet'}), 500
            
        # Get the GCN instance directly from builtins for reliability
        GCN = builtins.GCN
        
        # Make sure GCN has a blockchain
        if not hasattr(GCN, 'blockchain') or GCN.blockchain is None:
            return jsonify({'error': 'Blockchain is not initialized yet'}), 500
            
        # Make sure we have a chain
        if not hasattr(GCN.blockchain, 'chain') or GCN.blockchain.chain is None:
            GCN.blockchain.chain = []
            
        import requests
        import threading
        
        # Get our current blockchain height
        local_chain_length = len(GCN.blockchain.chain)
        
        # Track discovered peers and their chain lengths
        peers_data = []
        highest_chain = local_chain_length
        highest_chain_peer = None
        
        # Direct HTTP connection to other nodes
        # Hard-coded node addresses for testing reliability
        other_nodes = [
            {"address": "127.0.0.1", "web_port": 8001},
            {"address": "127.0.0.1", "web_port": 8002},
            {"address": "localhost", "web_port": 8001},
            {"address": "localhost", "web_port": 8002}
        ]
        
        print(f"Current blockchain length: {local_chain_length}")
        print(f"Looking for nodes with longer chains...")
        
        # Try direct connections to known node addresses
        for node in other_nodes:
            try:
                peer_url = f"http://{node['address']}:{node['web_port']}/api/blockchain"
                print(f"Checking node at {peer_url}")
                
                response = requests.get(peer_url, timeout=5)
                if response.status_code == 200:
                    peer_data = response.json()
                    peer_chain_length = peer_data.get('chain_length', 0)
                    
                    print(f"Found peer with chain length: {peer_chain_length}")
                    
                    # Track peer data
                    peers_data.append({
                        'address': node['address'],
                        'port': node['web_port'],
                        'chain_length': peer_chain_length
                    })
                    
                    # Skip self-connections
                    if peer_url.endswith(str(request.host)):
                        print(f"Skipping self-connection to {peer_url}")
                        continue
                    
                    # Check if this peer has a longer chain
                    if peer_chain_length > highest_chain:
                        highest_chain = peer_chain_length
                        highest_chain_peer = {
                            'address': node['address'],
                            'port': node['web_port']
                        }
            except Exception as e:
                print(f"Error connecting to node {node['address']}:{node['web_port']}: {str(e)}")
        
        # If we have a peer with a higher chain, fetch their chain
        synced = False
        sync_message = "No peers with longer chains found"
        
        if highest_chain_peer and highest_chain > local_chain_length:
            try:
                # Get the full chain from the peer with the longest chain
                chain_url = f"http://{highest_chain_peer['address']}:{highest_chain_peer['port']}/api/chain"
                print(f"Fetching chain from {chain_url}")
                
                response = requests.get(chain_url, timeout=20)
                
                if response.status_code == 200:
                    chain_data = response.json()
                    
                    if 'chain' in chain_data and len(chain_data['chain']) > local_chain_length:
                        print(f"Received chain with {len(chain_data['chain'])} blocks")
                        
                        # Validate the chain before replacing ours
                        genesis_block = chain_data['chain'][0]
                        valid_chain = True
                        
                        # Check genesis block matches ours
                        if len(GCN.blockchain.chain) > 0:
                            our_genesis = GCN.blockchain.chain[0]
                            if our_genesis.hash != genesis_block['hash']:
                                print(f"Genesis block mismatch: {our_genesis.hash} != {genesis_block['hash']}")
                                valid_chain = False
                        
                        if valid_chain:
                            # Replace our chain with the longer one
                            print(f"Replacing our chain with new chain of length {len(chain_data['chain'])}")
                            
                            # First save the mempool
                            # Make sure mempool exists
                            if not hasattr(GCN.blockchain, 'mempool') or GCN.blockchain.mempool is None:
                                GCN.blockchain.mempool = []
                                
                            saved_mempool = GCN.blockchain.mempool
                            
                            # Clear and rebuild the blockchain
                            GCN.blockchain.chain = []
                            
                            for block_data in chain_data['chain']:
                                from blockchain import Block, Transaction
                                
                                # Convert transactions
                                txs = []
                                for tx_data in block_data.get('transactions', []):
                                    # Create transaction without timestamp first
                                    tx = Transaction(
                                        sender=tx_data.get('sender'),
                                        recipient=tx_data.get('recipient'),
                                        amount=float(tx_data.get('amount')),
                                        fee=float(tx_data.get('fee', 0)),
                                        signature=tx_data.get('signature'),
                                        transaction_type=tx_data.get('transaction_type', 'TRANSFER'),
                                        price=tx_data.get('price') if tx_data.get('price') != "null" else None
                                    )
                                    
                                    # Set timestamp manually after creation
                                    if 'timestamp' in tx_data and tx_data['timestamp'] is not None:
                                        tx.timestamp = tx_data['timestamp']
                                        
                                    txs.append(tx)
                                
                                # Create block object - use difficulty_bits instead of difficulty_target
                                # Check if difficulty_bits is available in the block data
                                if 'difficulty_bits' in block_data:
                                    block = Block(
                                        index=block_data.get('index'),
                                        previous_hash=block_data.get('previous_hash'),
                                        timestamp=block_data.get('timestamp'),
                                        transactions=txs,
                                        nonce=block_data.get('nonce'),
                                        difficulty_bits=block_data.get('difficulty_bits')
                                    )
                                else:
                                    # Fallback to old format - use default difficulty
                                    block = Block(
                                        index=block_data.get('index'),
                                        previous_hash=block_data.get('previous_hash'),
                                        timestamp=block_data.get('timestamp'),
                                        transactions=txs,
                                        nonce=block_data.get('nonce'),
                                        difficulty_bits=0x2000ffff  # Default easy difficulty
                                    )
                                
                                # Manually set hash to ensure it matches
                                block.hash = block_data.get('hash')
                                GCN.blockchain.chain.append(block)
                            
                            # Restore mempool, but remove any transactions already in the chain
                            GCN.blockchain.mempool = []
                            for tx in saved_mempool:
                                # Check if transaction is in the new chain
                                tx_in_chain = False
                                for block in GCN.blockchain.chain:
                                    for chain_tx in block.transactions:
                                        if (chain_tx.sender == tx.sender and
                                            chain_tx.recipient == tx.recipient and
                                            abs(chain_tx.amount - tx.amount) < 0.0001):
                                            tx_in_chain = True
                                            break
                                    if tx_in_chain:
                                        break
                                
                                # Add back to mempool if not in chain
                                if not tx_in_chain:
                                    GCN.blockchain.mempool.append(tx)
                            
                            # Save the blockchain to disk
                            GCN.blockchain.save_chain_to_disk()
                            
                            synced = True
                            sync_message = f"Synchronized with peer at {highest_chain_peer['address']}:{highest_chain_peer['port']}, chain length now {len(GCN.blockchain.chain)}"
                        else:
                            sync_message = "Cannot sync: blockchain validation failed"
                    else:
                        sync_message = "Received chain is not longer than local chain"
            except Exception as e:
                sync_message = f"Failed to sync chain: {str(e)}"
                import traceback
                traceback.print_exc()
        
        # Always broadcast our current chain length to other nodes
        # This helps create a viral sync effect
        for node in other_nodes:
            try:
                # Skip ourselves
                if node['web_port'] == int(request.host.split(':')[1]):
                    continue
                    
                peer_url = f"http://{node['address']}:{node['web_port']}/api/network/discover"
                print(f"Notifying node at {peer_url} about our chain")
                
                requests.post(peer_url, json={
                    "chain_length": len(GCN.blockchain.chain),
                    "sender_port": request.host
                }, timeout=2)
            except Exception as e:
                # Log notification errors but continue
                print(f"Error notifying peer: {str(e)}")
                
        return jsonify({
            'success': True,
            'local_chain_length_before': local_chain_length,
            'local_chain_length_after': len(GCN.blockchain.chain),
            'peers_data': peers_data,
            'highest_chain_found': highest_chain,
            'synchronized': synced,
            'sync_message': sync_message
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@network_bp.route('/block', methods=['POST'])
def receive_block():
    """Receive a block from another node in the network"""
    try:
        # Make sure GCN is initialized
        import builtins
        if not hasattr(builtins, 'GCN') or builtins.GCN is None:
            return jsonify({'error': 'Blockchain node is not initialized yet'}), 500
            
        # Get the GCN instance directly from builtins for reliability
        GCN = builtins.GCN
        
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        block_data = request.get_json()
        if not block_data:
            return jsonify({'error': 'No block data provided'}), 400
            
        print(f"Received block from peer: index={block_data.get('index')}, hash={block_data.get('hash')}")
        
        # Make sure GCN has a blockchain
        if not hasattr(GCN, 'blockchain') or GCN.blockchain is None:
            return jsonify({'error': 'Blockchain is not initialized yet'}), 500
        
        # Reconstruct the block with transactions
        from blockchain import Block, Transaction
        
        # Convert transactions
        txs = []
        for tx_data in block_data.get('transactions', []):
            # Create transaction without timestamp first
            tx = Transaction(
                sender=tx_data.get('sender'),
                recipient=tx_data.get('recipient'),
                amount=float(tx_data.get('amount')),
                fee=float(tx_data.get('fee', 0)),
                signature=tx_data.get('signature'),
                transaction_type=tx_data.get('transaction_type', 'TRANSFER'),
                price=tx_data.get('price') if tx_data.get('price') != "null" else None
            )
            
            # Set timestamp manually after creation
            if 'timestamp' in tx_data and tx_data['timestamp'] is not None:
                tx.timestamp = tx_data['timestamp']
                
            txs.append(tx)
        
        # Create block object - use difficulty_bits instead of difficulty_target
        # Check if difficulty_bits is available in the block data
        if 'difficulty_bits' in block_data:
            block = Block(
                index=block_data.get('index'),
                previous_hash=block_data.get('previous_hash'),
                timestamp=block_data.get('timestamp'),
                transactions=txs,
                nonce=block_data.get('nonce'),
                difficulty_bits=block_data.get('difficulty_bits')
            )
        else:
            # Fallback to old format - use default difficulty
            block = Block(
                index=block_data.get('index'),
                previous_hash=block_data.get('previous_hash'),
                timestamp=block_data.get('timestamp'),
                transactions=txs,
                nonce=block_data.get('nonce'),
                difficulty_bits=0x2000ffff  # Default easy difficulty
            )
        
        # Manually set the hash to match what was sent
        block.hash = block_data.get('hash')
        
        # Check if this block fits in our chain (connects to our latest block)
        can_add = False
        needs_sync = False
        
        # Make sure we have a chain
        if not hasattr(GCN.blockchain, 'chain') or GCN.blockchain.chain is None:
            GCN.blockchain.chain = []
            
        if len(GCN.blockchain.chain) > 0:
            latest_block = GCN.blockchain.chain[-1]
            
            # Block connects directly to our chain
            if block.previous_hash == latest_block.hash:
                can_add = True
            # Block is ahead of our chain - we need to sync
            elif block.index > latest_block.index + 1:
                needs_sync = True
                print(f"Received block is ahead of our chain (index {block.index} vs our {latest_block.index}), triggering sync")
        elif block.index == 0:  # Genesis block
            can_add = True
            
        result = {}
        
        # We can add this block directly
        if can_add:
            # Manually validate the block instead of relying on is_valid_block
            valid_block = True
            
            try:
                # Check if the hash matches
                calculated_hash = block.calculate_hash()
                if calculated_hash != block.hash:
                    print(f"Block hash validation failed: {block.hash} != {calculated_hash}")
                    valid_block = False
                
                # Check if the hash has the right number of leading zeros based on difficulty
                target_prefix = "0" * block.difficulty_target
                if not block.hash.startswith(target_prefix):
                    print(f"Block doesn't meet difficulty target: {block.hash} should start with {target_prefix}")
                    valid_block = False
                
                # If we have a previous block, check if the previous_hash matches
                if len(GCN.blockchain.chain) > 0:
                    previous_block = GCN.blockchain.chain[-1]
                    if block.previous_hash != previous_block.hash:
                        print(f"Previous hash mismatch: {block.previous_hash} != {previous_block.hash}")
                        valid_block = False
                
                # Add any additional validation you need here
            except Exception as validation_error:
                print(f"Block validation error: {str(validation_error)}")
                valid_block = False
            
            # If valid, add to our chain
            if valid_block:
                # Add to our chain
                GCN.blockchain.chain.append(block)
                
                # Make sure mempool exists
                if not hasattr(GCN.blockchain, 'mempool') or GCN.blockchain.mempool is None:
                    GCN.blockchain.mempool = []
                
                # Clean up mempool - remove transactions included in this block
                original_mempool_size = len(GCN.blockchain.mempool)
                new_mempool = []
                
                for mempool_tx in GCN.blockchain.mempool:
                    # Check if this transaction is in the block
                    tx_in_block = False
                    for block_tx in block.transactions:
                        if (mempool_tx.sender == block_tx.sender and 
                            mempool_tx.recipient == block_tx.recipient and 
                            abs(mempool_tx.amount - block_tx.amount) < 0.0001):
                            tx_in_block = True
                            break
                    
                    # Keep transaction in mempool if not in the block
                    if not tx_in_block:
                        new_mempool.append(mempool_tx)
                
                # Update mempool
                GCN.blockchain.mempool = new_mempool
                print(f"Mempool cleaned: {original_mempool_size} -> {len(GCN.blockchain.mempool)} transactions")
                
                # Save to disk
                GCN.blockchain.save_chain_to_disk()
                
                result = {
                    'success': True,
                    'message': f'Block {block.index} added to chain',
                    'chain_length': len(GCN.blockchain.chain)
                }
            else:
                result = {
                    'success': False,
                    'message': f'Block {block.index} failed validation'
                }
        elif needs_sync:
            # Trigger chain sync in background
            import threading
            import requests
            
            # Capture the port outside the background function to avoid request context issues
            port = request.host.split(':')[1] if ':' in request.host else '8002'
            
            def background_sync():
                try:
                    requests.post(
                        f"http://localhost:{port}/api/network/sync",
                        timeout=10
                    )
                except Exception as se:
                    print(f"Error during background sync: {str(se)}")
            
            threading.Thread(target=background_sync, daemon=True).start()
            
            result = {
                'success': False,
                'message': 'Chain sync triggered',
                'action': 'sync_started'
            }
        else:
            result = {
                'success': False,
                'message': f'Block {block.index} does not connect to our chain'
            }
            
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@network_bp.route('/replace_chain', methods=['POST'])
def replace_chain():
    """Replace the current blockchain with a new one if it's valid and longer"""
    try:
        # Get the submitted chain data
        data = request.get_json()
        if not data or 'chain' not in data:
            return jsonify({"success": False, "message": "Missing chain data"}), 400
            
        submitted_chain_data = data['chain']
        
        # Convert the received chain data back to Block objects
        submitted_chain = []
        for block_data in submitted_chain_data:
            # Make sure we have the right imports
            from blockchain import Block, Transaction
            
            # Convert transactions
            txs = []
            for tx_data in block_data.get('transactions', []):
                # Create transaction without timestamp first
                tx = Transaction(
                    sender=tx_data.get('sender'),
                    recipient=tx_data.get('recipient'),
                    amount=float(tx_data.get('amount')),
                    fee=float(tx_data.get('fee', 0)),
                    signature=tx_data.get('signature'),
                    transaction_type=tx_data.get('transaction_type', 'TRANSFER'),
                    price=tx_data.get('price') if tx_data.get('price') != "null" else None
                )
                
                # Set timestamp manually after creation
                if 'timestamp' in tx_data and tx_data['timestamp'] is not None:
                    tx.timestamp = tx_data['timestamp']
                    
                txs.append(tx)
            
            # Create block object - use difficulty_bits instead of difficulty_target
            # Check if difficulty_bits is available in the block data
            if 'difficulty_bits' in block_data:
                block = Block(
                    index=block_data.get('index'),
                    previous_hash=block_data.get('previous_hash'),
                    timestamp=block_data.get('timestamp'),
                    transactions=txs,
                    nonce=block_data.get('nonce'),
                    difficulty_bits=block_data.get('difficulty_bits')
                )
            else:
                # Fallback to old format - use default difficulty
                block = Block(
                    index=block_data.get('index'),
                    previous_hash=block_data.get('previous_hash'),
                    timestamp=block_data.get('timestamp'),
                    transactions=txs,
                    nonce=block_data.get('nonce'),
                    difficulty_bits=0x2000ffff  # Default easy difficulty
                )
            
            # Manually set hash and merkle root to ensure it matches
            block.hash = block_data.get('hash')
            if 'merkle_root' in block_data:
                block.merkle_root = block_data.get('merkle_root')
            
            submitted_chain.append(block)
            
        # Verify the submitted chain is longer than our current chain
        if len(submitted_chain) <= len(GCN.blockchain.chain):
            return jsonify({
                "success": False, 
                "message": f"Submitted chain ({len(submitted_chain)} blocks) is not longer than current chain ({len(GCN.blockchain.chain)} blocks)"
            }), 400
            
        # Validate the submitted chain
        # Use our existing validation logic
        valid_chain = True
        
        # Check genesis block matches ours
        if len(GCN.blockchain.chain) > 0:
            our_genesis = GCN.blockchain.chain[0]
            their_genesis = submitted_chain[0] 
            if our_genesis.hash != their_genesis.hash:
                print(f"Genesis block mismatch: {our_genesis.hash} != {their_genesis.hash}")
                valid_chain = False
                
        # Do additional validation if needed
        for i in range(1, len(submitted_chain)):
            current_block = submitted_chain[i]
            previous_block = submitted_chain[i-1]
            
            # Verify block links
            if current_block.previous_hash != previous_block.hash:
                valid_chain = False
                print(f"Block link broken at index {i}")
                break
        
        if not valid_chain:
            return jsonify({
                "success": False, 
                "message": "Submitted chain is invalid"
            }), 400
            
        # If we get here, the submitted chain is valid and longer, so replace our current chain
        old_chain_length = len(GCN.blockchain.chain)
        
        # First save the mempool
        # Make sure mempool exists
        if not hasattr(GCN.blockchain, 'mempool') or GCN.blockchain.mempool is None:
            GCN.blockchain.mempool = []
            
        saved_mempool = GCN.blockchain.mempool
        
        # Replace our chain
        GCN.blockchain.chain = submitted_chain
        
        # Update mempool - remove transactions that are already in the new chain
        GCN.blockchain.mempool = []
        for tx in saved_mempool:
            # Check if transaction is in the new chain
            tx_in_chain = False
            for block in submitted_chain:
                for chain_tx in block.transactions:
                    if (chain_tx.sender == tx.sender and
                        chain_tx.recipient == tx.recipient and
                        abs(chain_tx.amount - tx.amount) < 0.0001):
                        tx_in_chain = True
                        break
                if tx_in_chain:
                    break
            
            # Add back to mempool if not in chain
            if not tx_in_chain:
                GCN.blockchain.mempool.append(tx)
        
        # Update difficulty target to match the new chain
        GCN.blockchain.difficulty_target = submitted_chain[-1].difficulty_target
        
        # Save the new chain to disk
        GCN.blockchain.save_chain_to_disk()
        
        return jsonify({
            "success": True, 
            "message": f"Chain replaced successfully. Old length: {old_chain_length}, New length: {len(GCN.blockchain.chain)}"
        }), 200
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Error replacing chain: {str(e)}"}), 500

@network_bp.route('/connect', methods=['POST'])
@token_required
def connect_to_peer(current_user):
    """Connect to a specific peer node"""
    try:
        data = request.get_json()
        if not all(k in data for k in ['address', 'port']):
            return jsonify({'error': 'Missing required fields'}), 400
            
        address = data['address']
        port = int(data['port'])
        
        # Attempt to connect to the peer
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5 second timeout
            sock.connect((address, port))
            
            # Perform handshake
            if GCN._perform_handshake(sock):
                node_id = f"{address}:{port}"
                GCN.peers[node_id] = GCN.Node(
                    address=address,
                    port=port,
                    last_seen=time.time()
                )
                
                # Start handler thread
                import threading
                threading.Thread(
                    target=GCN._handle_connection,
                    args=(sock, (address, port)),
                    daemon=True
                ).start()
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully connected to peer {address}:{port}',
                    'node_id': node_id
                })
            else:
                return jsonify({
                    'success': False, 
                    'message': 'Handshake failed'
                }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Failed to connect to peer: {str(e)}'
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500