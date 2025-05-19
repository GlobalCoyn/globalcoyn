"""
Enhanced node synchronization for GlobalCoyn blockchain
This module adds HTTP-based synchronization for more reliable communication
"""
import time
import threading
import requests
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("node_sync.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gcn_sync")

def enhance_globalcoyn_networking(global_coyn_instance):
    """
    Enhance the networking capabilities of a GlobalCoyn instance with 
    HTTP-based synchronization alongside P2P networking
    """
    # Store reference to original blockchain instance
    original_instance = global_coyn_instance
    
    # Add HTTP broadcast capability
    original_mine_block = global_coyn_instance.blockchain.mine_block
    
    def enhanced_mine_block(miner_address):
        """Enhanced mine_block with HTTP broadcast"""
        # First use the original method to mine the block
        new_block = original_mine_block(miner_address)
        
        if new_block:
            # After successfully mining, broadcast to other nodes via HTTP
            threading.Thread(
                target=broadcast_block_via_http,
                args=(new_block,),
                daemon=True
            ).start()
            
        return new_block
    
    # Override the mine_block method
    global_coyn_instance.blockchain.mine_block = enhanced_mine_block
    
    def broadcast_block_via_http(block):
        """Broadcast newly mined block to other nodes via HTTP"""
        # Known HTTP endpoints (hardcoded for testing)
        http_endpoints = [
            "http://localhost:8001/api/network/block",
            "http://localhost:8002/api/network/block",
            "http://127.0.0.1:8001/api/network/block",
            "http://127.0.0.1:8002/api/network/block",
        ]
        
        # Convert block to dictionary
        # First convert transactions to dictionary format
        tx_dicts = []
        for tx in block.transactions:
            # Make sure to handle any non-serializable attributes properly
            tx_dict = {
                "sender": tx.sender,
                "recipient": tx.recipient,
                "amount": tx.amount,
                "fee": tx.fee,
                "signature": tx.signature,
                "transaction_type": tx.transaction_type,
                "timestamp": tx.timestamp
            }
            
            # Handle price which might be None
            if hasattr(tx, 'price') and tx.price is not None:
                tx_dict["price"] = tx.price
            else:
                tx_dict["price"] = None
                
            tx_dicts.append(tx_dict)
        
        # Create block data dictionary
        block_data = {
            "index": block.index,
            "hash": block.hash,
            "previous_hash": block.previous_hash,
            "timestamp": block.timestamp,
            "transactions": tx_dicts,
            "nonce": block.nonce,
            "difficulty_bits": block.difficulty_bits
        }
        
        # Log block data for debugging
        logger.info(f"Broadcasting block #{block.index} with {len(tx_dicts)} transactions")
        
        # Broadcast to all known endpoints
        for endpoint in http_endpoints:
            try:
                # Skip broadcasting to ourselves
                if (global_coyn_instance.port == 9000 and "8001" in endpoint) or \
                   (global_coyn_instance.port == 9001 and "8002" in endpoint):
                    logger.info(f"Skipping self broadcast to {endpoint}")
                    continue
                    
                logger.info(f"Broadcasting block #{block.index} to {endpoint}")
                response = requests.post(
                    endpoint,
                    json=block_data,  # Send the block data directly, not wrapped in a "block" key
                    timeout=5
                )
                
                logger.info(f"Response from {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    logger.info(f"Successfully broadcast block to {endpoint}: {response_data}")
                else:
                    try:
                        error_data = response.json()
                        logger.warning(f"Failed to broadcast block to {endpoint}: {response.status_code} - {error_data}")
                    except:
                        logger.warning(f"Failed to broadcast block to {endpoint}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error broadcasting block to {endpoint}: {str(e)}")
                import traceback
                traceback.print_exc()
    
    # Add a periodic sync function
    def periodic_sync():
        """Periodically sync with other nodes"""
        while True:
            try:
                # Only sync if we have at least one block
                if len(global_coyn_instance.blockchain.chain) > 0:
                    logger.info("Performing periodic sync...")
                    
                    # Try direct HTTP sync with known nodes
                    sync_via_http()
            except Exception as e:
                logger.error(f"Error in periodic sync: {str(e)}")
                
            # Sleep for 30 seconds before next sync
            time.sleep(30)
    
    def sync_via_http():
        """Synchronize with other nodes via HTTP"""
        # Known HTTP endpoints for blockchain info
        http_endpoints = [
            "http://localhost:8001/api/blockchain",
            "http://localhost:8002/api/blockchain",
            "http://127.0.0.1:8001/api/blockchain",
            "http://127.0.0.1:8002/api/blockchain",
        ]
        
        # Get our current chain length
        our_length = len(global_coyn_instance.blockchain.chain)
        
        # Find node with longest chain
        longest_chain_length = our_length
        longest_chain_endpoint = None
        
        for endpoint in http_endpoints:
            try:
                # Skip checking ourselves
                if (global_coyn_instance.port == 9000 and "8001" in endpoint) or \
                   (global_coyn_instance.port == 9001 and "8002" in endpoint):
                    continue
                
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    chain_length = data.get("chain_length", 0)
                    
                    logger.info(f"Node at {endpoint} has chain length {chain_length}")
                    
                    if chain_length > longest_chain_length:
                        longest_chain_length = chain_length
                        longest_chain_endpoint = endpoint.replace("/blockchain", "/chain")
            except Exception as e:
                logger.error(f"Error checking node at {endpoint}: {str(e)}")
        
        # If we found a longer chain, fetch and use it
        if longest_chain_endpoint and longest_chain_length > our_length:
            logger.info(f"Found longer chain ({longest_chain_length}) at {longest_chain_endpoint}")
            
            try:
                # Get the full chain
                response = requests.get(longest_chain_endpoint, timeout=10)
                if response.status_code == 200:
                    chain_data = response.json()
                    
                    if "chain" in chain_data and len(chain_data["chain"]) > our_length:
                        logger.info(f"Received chain with {len(chain_data['chain'])} blocks")
                        
                        # Save our mempool before replacing the chain
                        saved_mempool = global_coyn_instance.blockchain.mempool.copy()
                        
                        # Replace our chain with the longer one
                        global_coyn_instance.blockchain.chain = []
                        
                        # Convert block dicts to Block objects
                        from blockchain import Block, Transaction
                        
                        for block_data in chain_data["chain"]:
                            # Convert transactions
                            transactions = []
                            for tx_data in block_data.get("transactions", []):
                                # Create transaction without timestamp parameter
                                tx = Transaction(
                                    sender=tx_data.get("sender"),
                                    recipient=tx_data.get("recipient"),
                                    amount=float(tx_data.get("amount")),
                                    fee=float(tx_data.get("fee", 0)),
                                    signature=tx_data.get("signature"),
                                    transaction_type=tx_data.get("transaction_type", "TRANSFER"),
                                    price=tx_data.get("price")
                                )
                                
                                # Manually set timestamp after creation
                                if "timestamp" in tx_data:
                                    tx.timestamp = float(tx_data["timestamp"])
                                    
                                transactions.append(tx)
                            
                            # Create block
                            # Check if difficulty_bits is available in the block data
                            if "difficulty_bits" in block_data:
                                block = Block(
                                    index=block_data.get("index"),
                                    previous_hash=block_data.get("previous_hash"),
                                    timestamp=block_data.get("timestamp"),
                                    transactions=transactions,
                                    nonce=block_data.get("nonce"),
                                    difficulty_bits=block_data.get("difficulty_bits")
                                )
                            else:
                                # Fallback to old format using default difficulty
                                block = Block(
                                    index=block_data.get("index"),
                                    previous_hash=block_data.get("previous_hash"),
                                    timestamp=block_data.get("timestamp"),
                                    transactions=transactions,
                                    nonce=block_data.get("nonce"),
                                    difficulty_bits=0x2000ffff  # Default easy difficulty
                                )
                            
                            # Set the hash directly to match what we received
                            block.hash = block_data.get("hash")
                            global_coyn_instance.blockchain.chain.append(block)
                            
                        logger.info(f"Successfully updated blockchain to length {len(global_coyn_instance.blockchain.chain)}")
                        
                        # Restore mempool but remove transactions already in the chain
                        global_coyn_instance.blockchain.mempool = []
                        for tx in saved_mempool:
                            # Check if transaction is in the new chain
                            tx_in_chain = False
                            for block in global_coyn_instance.blockchain.chain:
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
                                global_coyn_instance.blockchain.mempool.append(tx)
                                
                        logger.info(f"Restored {len(global_coyn_instance.blockchain.mempool)} transactions to mempool")
                        
                        # Save updated chain to disk
                        global_coyn_instance.blockchain.save_chain_to_disk()
            except Exception as e:
                logger.error(f"Error syncing with longer chain: {str(e)}")
                import traceback
                traceback.print_exc()
    
    # Start a background thread for periodic sync
    sync_thread = threading.Thread(target=periodic_sync, daemon=True)
    sync_thread.start()
    
    logger.info("Enhanced networking initialized with HTTP broadcasting")
    return global_coyn_instance