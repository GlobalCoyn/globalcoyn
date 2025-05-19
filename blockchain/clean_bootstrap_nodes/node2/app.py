"""
GlobalCoyn Blockchain Node
--------------------------
This is a minimal implementation of a blockchain node.
It handles blockchain operations and P2P networking.

Environment variables:
- GCN_ENV: Environment (development or production, default: development)
- GCN_NODE_NUM: Node number (default: 1)
- GCN_P2P_PORT: P2P networking port (default: 9000 for node 1, 9001 for node 2, etc.)
- GCN_WEB_PORT: HTTP API port (default: 8001 for node 1, 8002 for node 2, etc.)
- GCN_DOMAIN: Domain name for production (default: localhost)
- GCN_USE_SSL: Whether to use SSL in production (default: false)
"""

import os
import sys
import json
import time
import socket
import logging
import threading
from typing import Dict, Any, List, Optional

# Check if running in production mode
ENV = os.environ.get("GCN_ENV", "development")
PRODUCTION = ENV.lower() == "production"
from functools import wraps
from dataclasses import dataclass
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
sys.path.append(os.path.dirname(blockchain_dir))  # Add parent directory of blockchain to path

# Flask imports
from flask import Flask, jsonify, request, abort, make_response
from flask_cors import CORS

# Import core blockchain modules directly
sys.path.append(core_dir)
try:
    # First try importing directly from the core directory
    from blockchain import Blockchain
    from transaction import Transaction
    from block import Block
    from wallet import Wallet
    from mempool import Mempool
    from mining import Miner
    from utils import bits_to_target, target_to_bits, validate_address_format
    from coin import Coin, CoinManager
    print("Successfully imported core modules directly")
except ImportError as e:
    print(f"Direct import failed: {e}")
    try:
        # If that fails, try with the blockchain.core prefix
        from blockchain.core.blockchain import Blockchain
        from blockchain.core.transaction import Transaction
        from blockchain.core.block import Block
        from blockchain.core.wallet import Wallet
        from blockchain.core.mempool import Mempool
        from blockchain.core.mining import Miner
        from blockchain.core.utils import bits_to_target, target_to_bits, validate_address_format
        from blockchain.core.coin import Coin, CoinManager
        print("Successfully imported core modules with blockchain.core prefix")
    except ImportError as e:
        print(f"Prefixed import failed: {e}")
        # Last resort, try direct imports from core dir
        sys.path.append(core_dir)
        from blockchain import Blockchain
        from transaction import Transaction
        from block import Block
        from wallet import Wallet
        from mempool import Mempool
        from mining import Miner
        from utils import bits_to_target, target_to_bits, validate_address_format
        from coin import Coin, CoinManager
        print("Successfully imported core modules as last resort")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("blockchain.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("node")

# Node configuration
NODE_NUM = int(os.environ.get('GCN_NODE_NUM', 1))
P2P_PORT = int(os.environ.get('GCN_P2P_PORT', 9000 + NODE_NUM - 1))
WEB_PORT = int(os.environ.get('GCN_WEB_PORT', 8000 + NODE_NUM))
DATA_FILE = os.environ.get('GCN_DATA_FILE', 'blockchain_data.json')

@dataclass
class NodeInfo:
    """Information about a node in the network"""
    address: str
    port: int
    last_seen: float

class BlockchainNode:
    """GlobalCoyn blockchain node implementation"""
    def __init__(self, host: str = "0.0.0.0", port: int = P2P_PORT, dev_mode: bool = False):
        """
        Initialize a blockchain node.
        
        Args:
            host: Host address for P2P networking
            port: Port for P2P networking
            dev_mode: If True, run in development mode
        """
        self.host = host
        self.port = port
        self.blockchain = Blockchain(data_file=DATA_FILE)
        self.wallet = Wallet()
        self.peers: Dict[str, NodeInfo] = {}
        self.mining_address: Optional[str] = None
        self.is_mining = False
        self.is_running = False
        self.dev_mode = dev_mode
        self.start_time = time.time()
        
        if not dev_mode:
            # Initialize network sockets only in production mode
            self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.p2p_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # For development, use local connections
            self.seed_nodes = [
                ("127.0.0.1", 9001),  # Node 2
                ("127.0.0.1", 9002),  # Node 3
                ("localhost", 9001),   # Node 2 (alternate address)
                ("localhost", 9002)    # Node 3 (alternate address)
            ]
            
    def start(self) -> None:
        """Start the blockchain node"""
        self.is_running = True
        self.start_time = time.time()
        logger.info(f"Starting GlobalCoyn blockchain node on port {self.port}")
        
        # Start P2P network listener if not in dev mode
        if not self.dev_mode:
            try:
                # Bind to socket
                self.p2p_socket.bind((self.host, self.port))
                self.p2p_socket.listen(10)
                logger.info(f"P2P network listening on {self.host}:{self.port}")
                
                # Start listener thread
                threading.Thread(target=self._listen_for_connections, daemon=True).start()
                
                # Connect to seed nodes
                for seed_host, seed_port in self.seed_nodes:
                    if seed_port != self.port:  # Don't connect to ourselves
                        threading.Thread(
                            target=self._connect_to_node, 
                            args=(seed_host, seed_port),
                            daemon=True
                        ).start()
            except Exception as e:
                logger.error(f"Error starting P2P network: {str(e)}")
                
    def stop(self) -> None:
        """Stop the blockchain node"""
        self.is_running = False
        logger.info("Stopping blockchain node")
        
        # Close socket
        if not self.dev_mode:
            try:
                self.p2p_socket.close()
            except:
                pass
    
    def _listen_for_connections(self) -> None:
        """Listen for incoming P2P connections"""
        logger.info("Listening for peer connections...")
        
        while self.is_running:
            try:
                client_socket, addr = self.p2p_socket.accept()
                logger.info(f"Received connection from {addr[0]}:{addr[1]}")
                
                # Start a new thread to handle the connection
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, addr),
                    daemon=True
                ).start()
            except Exception as e:
                if self.is_running:
                    logger.error(f"Error accepting connection: {str(e)}")
                time.sleep(1)
    
    def _connect_to_node(self, host: str, port: int) -> bool:
        """
        Connect to another node in the network.
        
        Args:
            host: Host address to connect to
            port: Port to connect to
            
        Returns:
            True if connection successful, False otherwise
        """
        # Don't connect to ourselves
        if host in ["0.0.0.0", "127.0.0.1", "localhost"] and port == self.port:
            return False
            
        # Don't connect if already connected
        node_id = f"{host}:{port}"
        if node_id in self.peers:
            # Update last seen time
            self.peers[node_id].last_seen = time.time()
            return True
            
        logger.info(f"Connecting to node at {host}:{port}")
        
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5 second timeout
            sock.connect((host, port))
            
            # Perform handshake
            if self._perform_handshake(sock):
                # Add to peers
                self.peers[node_id] = NodeInfo(
                    address=host,
                    port=port,
                    last_seen=time.time()
                )
                
                # Start handler thread
                threading.Thread(
                    target=self._handle_connection,
                    args=(sock, (host, port)),
                    daemon=True
                ).start()
                
                logger.info(f"Successfully connected to peer {host}:{port}")
                return True
            else:
                logger.warning(f"Handshake failed with peer {host}:{port}")
                sock.close()
                return False
        except Exception as e:
            logger.error(f"Failed to connect to peer {host}:{port}: {str(e)}")
            return False
    
    def _perform_handshake(self, sock: socket.socket) -> bool:
        """
        Perform handshake with a peer.
        
        Args:
            sock: Socket connected to peer
            
        Returns:
            True if handshake successful, False otherwise
        """
        try:
            # Send handshake message
            handshake = {
                "type": "handshake",
                "version": "1.0.0",
                "node_id": f"{self.host}:{self.port}",
                "chain_length": len(self.blockchain.chain)
            }
            
            sock.sendall(json.dumps(handshake).encode('utf-8') + b'\n')
            
            # Receive response
            sock.settimeout(5)
            response = sock.recv(4096).decode('utf-8').strip()
            
            if not response:
                logger.warning("Empty handshake response")
                return False
                
            # Parse response
            try:
                response_data = json.loads(response)
                if response_data.get("type") == "handshake_ack":
                    logger.info(f"Handshake successful with {response_data.get('node_id')}")
                    
                    # Check if we should sync
                    their_chain_length = response_data.get("chain_length", 0)
                    our_chain_length = len(self.blockchain.chain)
                    
                    if their_chain_length > our_chain_length:
                        logger.info(f"Peer has longer chain ({their_chain_length} > {our_chain_length}). Sync needed.")
                        # Send sync request
                        sock.sendall(json.dumps({
                            "type": "sync_request",
                            "current_length": our_chain_length
                        }).encode('utf-8') + b'\n')
                    
                    return True
                else:
                    logger.warning(f"Invalid handshake response: {response_data}")
                    return False
            except json.JSONDecodeError:
                logger.warning(f"Invalid handshake response format: {response}")
                return False
        except Exception as e:
            logger.error(f"Handshake error: {str(e)}")
            return False
    
    def _handle_connection(self, sock: socket.socket, addr: tuple) -> None:
        """
        Handle a connection with a peer.
        
        Args:
            sock: Socket connected to peer
            addr: (host, port) tuple of the peer
        """
        node_id = f"{addr[0]}:{addr[1]}"
        logger.info(f"Handling connection with peer {node_id}")
        
        try:
            sock.settimeout(60)  # 1 minute timeout for initial handshake
            
            # Wait for handshake message if we initiated the connection
            if node_id not in self.peers:
                data = sock.recv(4096).decode('utf-8').strip()
                if not data:
                    logger.warning(f"Empty message from {node_id}")
                    return
                    
                try:
                    message = json.loads(data)
                    if message.get("type") == "handshake":
                        # Respond with handshake ack
                        sock.sendall(json.dumps({
                            "type": "handshake_ack",
                            "version": "1.0.0",
                            "node_id": f"{self.host}:{self.port}",
                            "chain_length": len(self.blockchain.chain)
                        }).encode('utf-8') + b'\n')
                        
                        # Add to peers
                        self.peers[node_id] = NodeInfo(
                            address=addr[0],
                            port=addr[1],
                            last_seen=time.time()
                        )
                        
                        # Check if we should sync
                        their_chain_length = message.get("chain_length", 0)
                        our_chain_length = len(self.blockchain.chain)
                        
                        if their_chain_length > our_chain_length:
                            # Send sync request
                            sock.sendall(json.dumps({
                                "type": "sync_request",
                                "current_length": our_chain_length
                            }).encode('utf-8') + b'\n')
                    else:
                        logger.warning(f"Unexpected first message from {node_id}: {message}")
                        return
                except json.JSONDecodeError:
                    logger.warning(f"Invalid message format from {node_id}: {data}")
                    return
            
            # Set a longer timeout for normal operation
            sock.settimeout(300)  # 5 minutes
            
            # Main message loop
            while self.is_running:
                try:
                    data = sock.recv(1048576).decode('utf-8')  # 1MB buffer
                    if not data:
                        logger.info(f"Connection closed by peer {node_id}")
                        break
                        
                    # Process the messages (could be multiple messages separated by newlines)
                    for message_str in data.strip().split('\n'):
                        if not message_str:
                            continue
                            
                        try:
                            message = json.loads(message_str)
                            self._process_message(message, sock, node_id)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid message format from {node_id}: {message_str}")
                except socket.timeout:
                    # Send ping to check if connection is still alive
                    try:
                        sock.sendall(json.dumps({
                            "type": "ping",
                            "timestamp": time.time()
                        }).encode('utf-8') + b'\n')
                    except:
                        logger.info(f"Connection lost to peer {node_id}")
                        break
                except Exception as e:
                    logger.error(f"Error handling connection with {node_id}: {str(e)}")
                    break
        finally:
            # Clean up
            try:
                sock.close()
            except:
                pass
                
            # Remove from peers if disconnected
            if node_id in self.peers:
                del self.peers[node_id]
                logger.info(f"Peer {node_id} disconnected")
    
    def _process_message(self, message: Dict[str, Any], sock: socket.socket, node_id: str) -> None:
        """
        Process a message from a peer.
        
        Args:
            message: Message data
            sock: Socket connected to peer
            node_id: Identifier of the peer
        """
        try:
            message_type = message.get("type", "")
            
            if message_type == "ping":
                # Respond with pong
                sock.sendall(json.dumps({
                    "type": "pong",
                    "timestamp": time.time(),
                    "ping_timestamp": message.get("timestamp")
                }).encode('utf-8') + b'\n')
                
                # Update last seen time
                if node_id in self.peers:
                    self.peers[node_id].last_seen = time.time()
            elif message_type == "pong":
                # Update last seen time
                if node_id in self.peers:
                    self.peers[node_id].last_seen = time.time()
            elif message_type == "sync_request":
                # Send our blockchain
                self._send_blockchain(sock, message.get("current_length", 0))
            elif message_type == "sync_response":
                # Process blockchain data
                self._process_blockchain_sync(message.get("chain", []))
            elif message_type == "new_block":
                # Process new block
                self._process_new_block(message.get("block", {}))
            elif message_type == "new_transaction":
                # Process new transaction
                self._process_new_transaction(message.get("transaction", {}))
            else:
                logger.warning(f"Unknown message type from {node_id}: {message_type}")
        except Exception as e:
            logger.error(f"Error processing message from {node_id}: {str(e)}")
    
    def _send_blockchain(self, sock: socket.socket, current_length: int) -> None:
        """
        Send blockchain data to a peer.
        
        Args:
            sock: Socket connected to peer
            current_length: Current blockchain length of the peer
        """
        try:
            # Only send the part of the chain that the peer doesn't have
            if current_length < len(self.blockchain.chain):
                # Convert chain to serializable format
                chain_data = []
                for block in self.blockchain.chain[current_length:]:
                    chain_data.append(block.to_dict())
                
                # Send the chain
                sock.sendall(json.dumps({
                    "type": "sync_response",
                    "chain": chain_data
                }).encode('utf-8') + b'\n')
                
                logger.info(f"Sent {len(chain_data)} blocks to peer")
            else:
                logger.info("Peer already has latest blockchain")
        except Exception as e:
            logger.error(f"Error sending blockchain: {str(e)}")
    
    def _process_blockchain_sync(self, chain_data: List[Dict[str, Any]]) -> bool:
        """
        Process blockchain data received from a peer.
        
        Args:
            chain_data: Serialized blockchain data
            
        Returns:
            True if chain was updated, False otherwise
        """
        if not chain_data:
            logger.warning("Empty chain data received")
            return False
            
        # Chain length check
        if len(chain_data) <= len(self.blockchain.chain):
            logger.info("Received chain is not longer than our chain")
            return False
            
        try:
            # Convert chain data to blocks
            new_chain = []
            for block_data in chain_data:
                # Convert transactions
                transactions = []
                for tx_data in block_data.get("transactions", []):
                    transaction = Transaction.from_dict(tx_data)
                    transactions.append(transaction)
                
                # Create block
                block = Block(
                    index=block_data.get("index"),
                    previous_hash=block_data.get("previous_hash"),
                    timestamp=block_data.get("timestamp"),
                    transactions=transactions,
                    nonce=block_data.get("nonce"),
                    difficulty_bits=block_data.get("difficulty_bits")
                )
                
                # Set hash and merkle root
                block.hash = block_data.get("hash")
                block.merkle_root = block_data.get("merkle_root")
                
                new_chain.append(block)
            
            # Verify chain is valid
            valid_chain = self._is_valid_chain(new_chain)
            
            if valid_chain:
                # Replace our chain with the new one
                self.blockchain.chain = new_chain
                
                # Update mining difficulty
                if hasattr(self.blockchain.miner, 'bits') and hasattr(new_chain[-1], 'difficulty_bits'):
                    self.blockchain.miner.bits = new_chain[-1].difficulty_bits
                    self.blockchain.miner.target = bits_to_target(new_chain[-1].difficulty_bits)
                
                # Save to disk
                self.blockchain.save_chain_to_disk()
                
                logger.info(f"Updated blockchain with {len(new_chain)} blocks")
                return True
            else:
                logger.warning("Received chain is invalid")
                return False
        except Exception as e:
            logger.error(f"Error processing blockchain sync: {str(e)}")
            return False
    
    def _is_valid_chain(self, chain: List[Block]) -> bool:
        """
        Validate a blockchain.
        
        Args:
            chain: List of blocks to validate
            
        Returns:
            True if chain is valid, False otherwise
        """
        # Check if chain is empty
        if not chain:
            return False
            
        # Verify each block
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i-1]
            
            # Verify block hash
            if current_block.hash != current_block.calculate_hash():
                logger.error(f"Invalid block hash at index {i}")
                return False
            
            # Verify block links
            if current_block.previous_hash != previous_block.hash:
                logger.error(f"Invalid block linkage at index {i}")
                return False
            
            # Verify merkle root
            if current_block.merkle_root != current_block.calculate_merkle_root():
                logger.error(f"Invalid merkle root at index {i}")
                return False
        
        return True
    
    def _process_new_block(self, block_data: Dict[str, Any]) -> bool:
        """
        Process a new block received from a peer.
        
        Args:
            block_data: Serialized block data
            
        Returns:
            True if block was added to chain, False otherwise
        """
        try:
            # Convert transactions
            transactions = []
            for tx_data in block_data.get("transactions", []):
                transaction = Transaction.from_dict(tx_data)
                transactions.append(transaction)
            
            # Create block
            block = Block(
                index=block_data.get("index"),
                previous_hash=block_data.get("previous_hash"),
                timestamp=block_data.get("timestamp"),
                transactions=transactions,
                nonce=block_data.get("nonce"),
                difficulty_bits=block_data.get("difficulty_bits")
            )
            
            # Set hash and merkle root
            block.hash = block_data.get("hash")
            block.merkle_root = block_data.get("merkle_root")
            
            # Verify block is valid
            if block.is_valid():
                # Check if block connects to our chain
                if len(self.blockchain.chain) > 0:
                    latest_block = self.blockchain.chain[-1]
                    
                    if block.previous_hash == latest_block.hash:
                        # Block connects to our chain, add it
                        self.blockchain.chain.append(block)
                        
                        # Remove transactions in block from mempool
                        for tx in block.transactions:
                            if tx in self.blockchain.mempool.transactions:
                                self.blockchain.mempool.remove_transaction(tx)
                        
                        # Save to disk
                        self.blockchain.save_chain_to_disk()
                        
                        logger.info(f"Added new block {block.index} to chain")
                        return True
                    elif block.index > latest_block.index + 1:
                        # Block is ahead of our chain, sync needed
                        logger.info(f"Received block is ahead of our chain, sync needed")
                        return False
                elif block.index == 0:  # Genesis block
                    # Add genesis block if chain is empty
                    self.blockchain.chain.append(block)
                    self.blockchain.save_chain_to_disk()
                    logger.info("Added genesis block to chain")
                    return True
            else:
                logger.warning(f"Received invalid block")
            
            return False
        except Exception as e:
            logger.error(f"Error processing new block: {str(e)}")
            return False
    
    def _process_new_transaction(self, tx_data: Dict[str, Any]) -> bool:
        """
        Process a new transaction received from a peer.
        
        Args:
            tx_data: Serialized transaction data
            
        Returns:
            True if transaction was added to mempool, False otherwise
        """
        try:
            # Create transaction
            transaction = Transaction.from_dict(tx_data)
            
            # Add to mempool
            result = self.blockchain.add_transaction(transaction)
            
            if result:
                logger.info(f"Added new transaction to mempool: {transaction.tx_hash}")
            
            return result
        except Exception as e:
            logger.error(f"Error processing new transaction: {str(e)}")
            return False
    
    def broadcast_block(self, block: Block) -> None:
        """
        Broadcast a new block to all peers.
        
        Args:
            block: Block to broadcast
        """
        if self.dev_mode:
            return
            
        # Convert block to serializable format
        block_data = block.to_dict()
        
        # Create message
        message = {
            "type": "new_block",
            "block": block_data
        }
        
        # Broadcast to all peers
        for node_id, node in self.peers.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((node.address, node.port))
                
                # Perform handshake
                if self._perform_handshake(sock):
                    # Send block
                    sock.sendall(json.dumps(message).encode('utf-8') + b'\n')
                    logger.info(f"Broadcasted new block to peer {node_id}")
                
                # Close socket
                sock.close()
            except Exception as e:
                logger.error(f"Failed to broadcast block to peer {node_id}: {str(e)}")
    
    def broadcast_transaction(self, transaction: Transaction) -> None:
        """
        Broadcast a new transaction to all peers.
        
        Args:
            transaction: Transaction to broadcast
        """
        if self.dev_mode:
            return
            
        # Convert transaction to serializable format
        tx_data = transaction.to_dict()
        
        # Create message
        message = {
            "type": "new_transaction",
            "transaction": tx_data
        }
        
        # Broadcast to all peers
        for node_id, node in self.peers.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((node.address, node.port))
                
                # Perform handshake
                if self._perform_handshake(sock):
                    # Send transaction
                    sock.sendall(json.dumps(message).encode('utf-8') + b'\n')
                    logger.info(f"Broadcasted new transaction to peer {node_id}")
                
                # Close socket
                sock.close()
            except Exception as e:
                logger.error(f"Failed to broadcast transaction to peer {node_id}: {str(e)}")
    
    def start_mining(self, mining_address: str) -> None:
        """
        Start mining blocks.
        
        Args:
            mining_address: Address to receive mining rewards
        """
        if self.is_mining:
            logger.warning("Mining already in progress")
            return
            
        # Set mining address and flag
        self.mining_address = mining_address
        self.is_mining = True
        
        # Start mining thread
        threading.Thread(target=self._mining_thread, daemon=True).start()
        logger.info(f"Started mining for address {mining_address}")
    
    def stop_mining(self) -> None:
        """Stop mining blocks."""
        self.is_mining = False
        logger.info("Stopped mining")
    
    def _mining_thread(self) -> None:
        """Mine blocks in a loop."""
        logger.info("Mining thread started")
        
        while self.is_mining and self.is_running:
            try:
                # Mine a block
                new_block = self.blockchain.mine_block(self.mining_address)
                
                if new_block:
                    logger.info(f"Successfully mined block {new_block.index}")
                    
                    # Broadcast to network
                    self.broadcast_block(new_block)
                else:
                    logger.info("No block mined, mempool empty or max supply reached")
                    
                # Small pause to avoid CPU overload
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in mining thread: {str(e)}")
                time.sleep(5)  # Longer pause on error

# Initialize Flask app
# Initialize Flask app
app = Flask(__name__)

# Import and apply CORS if in production mode
if PRODUCTION:
    try:
        from cors_setup import setup_cors
        setup_cors(app)
        print("CORS configured for production environment")
    except ImportError:
        print("Warning: cors_setup module not found. CORS not configured.")
        from flask_cors import CORS
        CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configure CORS
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Initialize blockchain node
GCN = BlockchainNode(dev_mode=False)

# Store GCN and utility functions in builtins for access from other modules
import builtins
builtins.GCN = GCN
builtins.Transaction = Transaction
builtins.Block = Block
builtins.Wallet = Wallet
builtins.Mempool = Mempool
builtins.Miner = Miner
builtins.bits_to_target = bits_to_target
builtins.target_to_bits = target_to_bits
builtins.validate_address_format = validate_address_format
builtins.Coin = Coin
builtins.CoinManager = CoinManager

# Import route blueprints
from routes import network_bp, transactions_bp, blockchain_bp, wallet_bp, mining_bp

# Configure Flask to not redirect to trailing slashes
app.url_map.strict_slashes = False

# Register blueprints
app.register_blueprint(network_bp, url_prefix='/api/network')
app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
app.register_blueprint(blockchain_bp, url_prefix='/api/blockchain')
app.register_blueprint(wallet_bp, url_prefix='/api/wallet')
app.register_blueprint(mining_bp, url_prefix='/api/mining')

# Validator decorator for JSON request data
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

# API Routes for the blockchain node
@app.route('/api/blockchain', methods=['GET'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/blockchain/chain', methods=['GET'])
def get_chain():
    """Get the full blockchain"""
    try:
        chain = []
        
        for block in GCN.blockchain.chain:
            chain.append(block.to_dict())
        
        return jsonify({"chain": chain}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/blockchain/blocks/latest', methods=['GET'])
def get_latest_block():
    """Get the latest block"""
    try:
        if not GCN.blockchain.chain:
            return jsonify({"error": "Blockchain is empty"}), 404
            
        latest_block = GCN.blockchain.chain[-1]
        return jsonify(latest_block.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/blockchain/blocks/<string:hash>', methods=['GET'])
def get_block_by_hash(hash):
    """Get a specific block by hash"""
    try:
        block = GCN.blockchain.get_block_by_hash(hash)
        
        if block:
            return jsonify(block.to_dict()), 200
        else:
            return jsonify({"error": "Block not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/blockchain/blocks/<int:height>', methods=['GET'])
def get_block_by_height(height):
    """Get a specific block by height"""
    try:
        block = GCN.blockchain.get_block_by_height(height)
        
        if block:
            return jsonify(block.to_dict()), 200
        else:
            return jsonify({"error": "Block not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/blockchain/mempool', methods=['GET'])
def get_mempool():
    """Get current mempool transactions"""
    try:
        mempool = []
        
        for tx in GCN.blockchain.mempool.get_transactions():
            mempool.append(tx.to_dict())
        
        return jsonify({"mempool": mempool}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/blockchain/stats', methods=['GET'])
def get_blockchain_stats():
    """Get blockchain statistics"""
    try:
        stats = GCN.blockchain.get_blockchain_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/blockchain/difficulty', methods=['GET'])
def get_difficulty():
    """Get current mining difficulty"""
    try:
        difficulty = GCN.blockchain.get_mining_difficulty()
        return jsonify(difficulty), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/balance/<string:address>', methods=['GET'])
def get_balance(address):
    """Get balance for a wallet address"""
    try:
        if not validate_address_format(address):
            return jsonify({"error": "Invalid wallet address format"}), 400
            
        balance = GCN.blockchain.get_balance(address)
        return jsonify({"address": address, "balance": balance}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/transactions/<string:address>', methods=['GET'])
def get_address_transactions(address):
    """Get transactions for a wallet address"""
    try:
        if not validate_address_format(address):
            return jsonify({"error": "Invalid wallet address format"}), 400
            
        transactions = GCN.blockchain.get_address_transactions(address)
        return jsonify({"address": address, "transactions": transactions}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/validate/<string:address>', methods=['GET'])
def validate_address(address):
    """Validate a wallet address format"""
    is_valid = validate_address_format(address)
    return jsonify({"address": address, "is_valid": is_valid}), 200

@app.route('/api/wallet/mining-stats/<string:address>', methods=['GET'])
def get_mining_stats(address):
    """Get mining statistics for a wallet address"""
    try:
        if not validate_address_format(address):
            return jsonify({"error": "Invalid wallet address format"}), 400
            
        # Calculate number of blocks mined by this address
        blocks_mined = 0
        total_rewards = 0.0
        
        for block in GCN.blockchain.chain:
            for tx in block.transactions:
                if tx.is_coinbase() and tx.recipient == address:
                    blocks_mined += 1
                    total_rewards += tx.amount
        
        stats = {
            "address": address,
            "blocks_mined": blocks_mined,
            "total_rewards": total_rewards,
            "is_currently_mining": GCN.is_mining and GCN.mining_address == address
        }
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transactions', methods=['POST'])
@validate_json('sender', 'recipient', 'amount', 'signature')
def add_transaction():
    """Add a transaction to the blockchain"""
    try:
        data = request.get_json()
        
        # Create transaction
        tx = Transaction(
            sender=data['sender'],
            recipient=data['recipient'],
            amount=float(data['amount']),
            fee=float(data.get('fee', 0.001)),
            signature=data['signature']
        )
        
        # Add to mempool
        success = GCN.blockchain.add_transaction(tx)
        
        if success:
            # Broadcast to network
            GCN.broadcast_transaction(tx)
            
            return jsonify({"status": "success", "transaction": tx.to_dict()}), 201
        else:
            return jsonify({"status": "error", "message": "Transaction validation failed"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/blockchain/blocks/mine', methods=['POST'])
def mine_block():
    """Mine a new block"""
    try:
        data = request.get_json() or {}
        miner_address = data.get('miner_address', 'BLOCKCHAIN_REWARD')
        
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/mining/start', methods=['POST'])
@validate_json('mining_address')
def start_mining():
    """Start continuous mining process"""
    try:
        data = request.get_json()
        mining_address = data['mining_address']
        
        if not validate_address_format(mining_address):
            return jsonify({"error": "Invalid mining address format"}), 400
        
        # Start mining
        GCN.start_mining(mining_address)
        
        return jsonify({
            "status": "success", 
            "message": f"Mining started for address {mining_address}"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/mining/stop', methods=['POST'])
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
        return jsonify({"error": str(e)}), 500

# Default route
@app.route('/')
def home():
    """Home page"""
    node_info = {
        "name": "GlobalCoyn Blockchain Node",
        "version": "1.0.0",
        "node_number": NODE_NUM,
        "p2p_port": P2P_PORT,
        "api_port": WEB_PORT,
        "blockchain_height": len(GCN.blockchain.chain) if hasattr(GCN, 'blockchain') else 0,
        "connected_peers": len(GCN.peers) if hasattr(GCN, 'peers') else 0,
    }
    return jsonify(node_info)

# Startup events
@app.before_first_request
def before_first_request():
    """Start blockchain node before first request"""
    if not GCN.is_running:
        GCN.start()
        logger.info("Blockchain node started")

# Main entry point for standalone execution
if __name__ == '__main__':
    # Start blockchain node
    GCN.start()
    
    # Run Flask app
    try:
        app.run(host='0.0.0.0', port=WEB_PORT, debug=False)
    finally:
        # Stop blockchain node
        GCN.stop()