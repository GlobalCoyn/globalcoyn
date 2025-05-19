import json
import socket
import threading
import time
from typing import List, Dict, Optional, Set, Union
from decimal import Decimal
import requests
from dataclasses import dataclass
import os
import sys
import logging
# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from blockchain import Blockchain, Transaction, Block
from wallet import Wallet
# Import the improved node sync module with fallback
try:
    from improved_node_sync import enhance_globalcoyn_networking
except ImportError:
    # Define a fallback if the module is not available
    def enhance_globalcoyn_networking(global_coyn_instance):
        """Fallback function that just returns the instance unchanged"""
        print("Using fallback networking (module not found)")
        return global_coyn_instance

class Coin:
    """Represents a GCN coin with amount and metadata"""
    def __init__(self, amount: float = 0, owner: str = None):
        self.amount = round(float(amount), 8)  # Store with 8 decimal precision
        self.owner = owner  # Wallet address that owns this coin
        self._validate_amount()
    
    def _validate_amount(self) -> None:
        """Validate coin amount"""
        if self.amount < 0:
            raise ValueError("Coin amount cannot be negative")
        if self.amount > 1_000_000_000:  # 1 billion max supply
            raise ValueError("Coin amount exceeds maximum supply")
    
    def add(self, amount: float) -> None:
        """Add amount to coin"""
        self.amount = round(self.amount + float(amount), 8)
        self._validate_amount()
    
    def subtract(self, amount: float) -> None:
        """Subtract amount from coin"""
        self.amount = round(self.amount - float(amount), 8)
        self._validate_amount()
    
    def to_dict(self) -> Dict:
        """Convert coin to dictionary for serialization"""
        return {
            "amount": format(self.amount, '.8f'),
            "owner": self.owner
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Coin':
        """Create coin from dictionary"""
        return cls(float(data["amount"]), data.get("owner"))
    
    def __str__(self) -> str:
        return f"GCN({self.amount})"
    
    def __repr__(self) -> str:
        return self.__str__()

@dataclass
class Node:
    address: str
    port: int
    last_seen: float

class GlobalCoyn:
    def __init__(self, host: str = "0.0.0.0", port: int = 9000, dev_mode: bool = False):
        self.host = host
        self.port = port
        self.blockchain = Blockchain()
        self.peers: Dict[str, Node] = {}
        self.mining_address: Optional[str] = None
        self.is_mining = False
        self.is_running = False
        self.dev_mode = dev_mode
        
        if not dev_mode:
            # Initialize network sockets only in production mode
            self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.p2p_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # For development, use only local connections to Node 2
            self.seed_nodes = [
                ("127.0.0.1", 9001),  # Node 2 running locally
                ("localhost", 9001)   # Another way to reference Node 2
            ]

    def start(self) -> None:
        """Start the GlobalCoyn node"""
        self.is_running = True
        self.start_time = time.time()  # Track node uptime
        
        # Load blockchain from disk if available
        self.blockchain.load_chain_from_disk()
        logging.info(f"Loaded blockchain with {len(self.blockchain.chain)} blocks")
        
        if not self.dev_mode:
            try:
                # Start P2P server only in production mode
                try:
                    self.p2p_socket.bind((self.host, self.port))
                    self.p2p_socket.listen(10)
                    print(f"P2P server listening on {self.host}:{self.port}")
                except OSError as bind_error:
                    if bind_error.errno == 48:  # Address already in use
                        print(f"P2P port {self.port} already in use, continuing with existing socket")
                    else:
                        raise
                
                # Start network threads
                threading.Thread(target=self._accept_connections, daemon=True).start()
                threading.Thread(target=self._maintain_connections, daemon=True).start()
                
                # Enable enhanced blockchain synchronization
                self.block_sync = enhance_globalcoyn_networking(self)
                logging.info("Enhanced blockchain synchronization enabled")
                
                # Connect to seed nodes
                self._connect_to_seed_nodes()
            except OSError as e:
                print(f"Network error (expected in dev mode): {e}")
                # Continue without network in dev mode

    def stop(self) -> None:
        """Stop the GlobalCoyn node"""
        self.is_running = False
        self.is_mining = False
        
        # Save blockchain state before shutting down
        self.blockchain.save_chain_to_disk()
        logging.info("Blockchain state saved")
        
        if not self.dev_mode:
            try:
                self.p2p_socket.close()
            except:
                pass

    def _accept_connections(self) -> None:
        """Accept incoming P2P connections"""
        while self.is_running:
            try:
                client_socket, address = self.p2p_socket.accept()
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except:
                if self.is_running:
                    time.sleep(1)

    def _handle_connection(self, client_socket: socket.socket, address: tuple) -> None:
        """Handle incoming P2P connection"""
        node_id = f"{address[0]}:{address[1]}"
        print(f"Handling connection from {node_id}")
        
        try:
            # Perform handshake
            if not self._perform_handshake(client_socket):
                print(f"Handshake failed with {node_id}, closing connection")
                client_socket.close()
                return
            
            print(f"Adding new peer: {node_id}")
            
            # Add to peers
            self.peers[node_id] = Node(
                address=address[0],
                port=address[1],
                last_seen=time.time()
            )
            
            # Send our blockchain height to trigger sync if needed
            height_message = {
                "type": "height",
                "height": len(self.blockchain.chain)
            }
            self._send_message(client_socket, height_message)
            
            # Handle messages in a loop
            print(f"Entering message handling loop for {node_id}")
            message_count = 0
            
            while self.is_running:
                try:
                    message = self._receive_message(client_socket)
                    if not message:
                        print(f"Connection closed by {node_id}")
                        break
                    
                    message_count += 1
                    print(f"Received message #{message_count} from {node_id}: {message.get('type')}")
                    self._handle_message(message, node_id)
                    
                except socket.timeout:
                    # Just a timeout, continue
                    continue
                except Exception as msg_error:
                    print(f"Error handling message from {node_id}: {str(msg_error)}")
                    break
            
        except Exception as e:
            print(f"Error in connection handler for {node_id}: {str(e)}")
        finally:
            print(f"Closing connection with {node_id}")
            client_socket.close()
            if node_id in self.peers:
                print(f"Removing peer {node_id}")
                del self.peers[node_id]

    def _handle_message(self, message: dict, node_id: str) -> None:
        """Handle incoming P2P message"""
        message_type = message.get("type")
        
        if message_type == "get_blocks":
            # Send our blockchain
            self._send_blockchain(node_id)
        
        elif message_type == "new_block":
            # Validate and add new block
            block_data = message.get("data")
            if block_data:
                self._handle_new_block(block_data)
    def _handle_new_block(self, block_data: dict) -> bool:
        """Handle a new block from another node"""
        try:
            # Print block info for debugging
            print(f"Received new block: index={block_data.get('index')}, hash={block_data.get('hash')}")
            
            # Convert dict to Block object
            new_block = self._dict_to_block(block_data)
            
            # Validate block hash
            calculated_hash = new_block.calculate_hash()
            if new_block.hash != calculated_hash:
                print(f"Block hash validation failed: received={new_block.hash}, calculated={calculated_hash}")
                return False
            
            # Check if we already have this block by hash
            for existing_block in self.blockchain.chain:
                if existing_block.hash == new_block.hash:
                    print(f"Block already in our chain (#{new_block.index}), ignoring")
                    return True
            
            # Check block index
            current_last_block = self.blockchain.chain[-1] if self.blockchain.chain else None
            if not current_last_block:
                print(f"No blocks in our chain yet, cannot add block #{new_block.index}")
                return False
                
            # If this is the next block in sequence, validate the previous hash
            if new_block.index == current_last_block.index + 1:
                if new_block.previous_hash != current_last_block.hash:
                    print(f"Block #{new_block.index} previous_hash doesn't match our last block hash")
                    print(f"Our last block: hash={current_last_block.hash}")
                    print(f"New block prev_hash: {new_block.previous_hash}")
                    return False
                    
                # This block is valid and next in sequence
                print(f"Adding valid block #{new_block.index} to our chain")
                self.blockchain.chain.append(new_block)
                
                # Remove transactions in this block from our mempool
                mempool_before = len(self.blockchain.mempool)
                for tx in new_block.transactions:
                    # Find matching transactions in mempool by key attributes
                    for mempool_tx in list(self.blockchain.mempool):
                        if (mempool_tx.sender == tx.sender and 
                            mempool_tx.recipient == tx.recipient and
                            abs(mempool_tx.amount - tx.amount) < 0.0001 and
                            mempool_tx.transaction_type == tx.transaction_type):
                            self.blockchain.mempool.remove(mempool_tx)
                            break
                
                mempool_after = len(self.blockchain.mempool)
                print(f"Removed {mempool_before - mempool_after} transactions from mempool")
                print(f"Successfully added new block #{new_block.index} to chain")
                
                # If we're mining, adjust difficulty based on new chain
                if self.is_mining:
                    self.blockchain.adjust_difficulty()
                
                return True
            
            # If the block is ahead of our chain, we might need to sync the missing blocks
            if new_block.index > current_last_block.index + 1:
                print(f"Received block #{new_block.index} but our last block is #{current_last_block.index}")
                print(f"Need to synchronize missing blocks")
                
                # Trigger blockchain sync to get missing blocks
                threading.Thread(target=self._sync_blockchain).start()
                return False
                
            # If the block is behind our chain, ignore it (we're ahead)
            if new_block.index <= current_last_block.index:
                print(f"Received block #{new_block.index} but we already have {current_last_block.index + 1} blocks")
                return False
                
        except Exception as e:
            print(f"Error handling new block from network: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    def add(self, amount: float) -> None:
        """Add amount to coin"""
        self.amount = round(self.amount + float(amount), 8)
        self._validate_amount()
    
    def subtract(self, amount: float) -> None:
        """Subtract amount from coin"""
        self.amount = round(self.amount - float(amount), 8)
        self._validate_amount()
    
    def to_dict(self) -> Dict:
        """Convert coin to dictionary for serialization"""
        return {
            "amount": format(self.amount, '.8f'),
            "owner": self.owner
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Coin':
        """Create coin from dictionary"""
        return cls(float(data["amount"]), data.get("owner"))
    
    def __str__(self) -> str:
        return f"GCN({self.amount})"
    
    def __repr__(self) -> str:
        return self.__str__()

@dataclass
class Node:
    address: str
    port: int
    last_seen: float

class GlobalCoyn:
    def __init__(self, host: str = "0.0.0.0", port: int = 9000, dev_mode: bool = False):
        self.host = host
        self.port = port
        self.blockchain = Blockchain()
        self.peers: Dict[str, Node] = {}
        self.mining_address: Optional[str] = None
        self.is_mining = False
        self.is_running = False
        self.dev_mode = dev_mode
        
        if not dev_mode:
            # Initialize network sockets only in production mode
            self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.p2p_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # For development, use only local connections to Node 2
            self.seed_nodes = [
                ("127.0.0.1", 9001),  # Node 2 running locally
                ("localhost", 9001)   # Another way to reference Node 2
            ]

    def start(self) -> None:
        """Start the GlobalCoyn node"""
        self.is_running = True
        self.start_time = time.time()  # Track node uptime
        
        # Load blockchain from disk if available
        self.blockchain.load_chain_from_disk()
        logging.info(f"Loaded blockchain with {len(self.blockchain.chain)} blocks")
        
        if not self.dev_mode:
            try:
                # Start P2P server only in production mode
                try:
                    self.p2p_socket.bind((self.host, self.port))
                    self.p2p_socket.listen(10)
                    print(f"P2P server listening on {self.host}:{self.port}")
                except OSError as bind_error:
                    if bind_error.errno == 48:  # Address already in use
                        print(f"P2P port {self.port} already in use, continuing with existing socket")
                    else:
                        raise
                
                # Start network threads
                threading.Thread(target=self._accept_connections, daemon=True).start()
                threading.Thread(target=self._maintain_connections, daemon=True).start()
                
                # Enable enhanced blockchain synchronization
                self.block_sync = enhance_globalcoyn_networking(self)
                logging.info("Enhanced blockchain synchronization enabled")
                
                # Connect to seed nodes
                self._connect_to_seed_nodes()
            except OSError as e:
                print(f"Network error (expected in dev mode): {e}")
                # Continue without network in dev mode

    def stop(self) -> None:
        """Stop the GlobalCoyn node"""
        self.is_running = False
        self.is_mining = False
        
        # Save blockchain state before shutting down
        self.blockchain.save_chain_to_disk()
        logging.info("Blockchain state saved")
        
        if not self.dev_mode:
            try:
                self.p2p_socket.close()
            except:
                pass

    def _accept_connections(self) -> None:
        """Accept incoming P2P connections"""
        while self.is_running:
            try:
                client_socket, address = self.p2p_socket.accept()
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except:
                if self.is_running:
                    time.sleep(1)

    def _handle_connection(self, client_socket: socket.socket, address: tuple) -> None:
        """Handle incoming P2P connection"""
        node_id = f"{address[0]}:{address[1]}"
        print(f"Handling connection from {node_id}")
        
        try:
            # Perform handshake
            if not self._perform_handshake(client_socket):
                print(f"Handshake failed with {node_id}, closing connection")
                client_socket.close()
                return
            
            print(f"Adding new peer: {node_id}")
            
            # Add to peers
            self.peers[node_id] = Node(
                address=address[0],
                port=address[1],
                last_seen=time.time()
            )
            
            # Send our blockchain height to trigger sync if needed
            height_message = {
                "type": "height",
                "height": len(self.blockchain.chain)
            }
            self._send_message(client_socket, height_message)
            
            # Handle messages in a loop
            print(f"Entering message handling loop for {node_id}")
            message_count = 0
            
            while self.is_running:
                try:
                    message = self._receive_message(client_socket)
                    if not message:
                        print(f"Connection closed by {node_id}")
                        break
                    
                    message_count += 1
                    print(f"Received message #{message_count} from {node_id}: {message.get('type')}")
                    self._handle_message(message, node_id)
                    
                except socket.timeout:
                    # Just a timeout, continue
                    continue
                except Exception as msg_error:
                    print(f"Error handling message from {node_id}: {str(msg_error)}")
                    break
            
        except Exception as e:
            print(f"Error in connection handler for {node_id}: {str(e)}")
        finally:
            print(f"Closing connection with {node_id}")
            client_socket.close()
            if node_id in self.peers:
                print(f"Removing peer {node_id}")
                del self.peers[node_id]

    def _handle_message(self, message: dict, node_id: str) -> None:
        """Handle incoming P2P message"""
        message_type = message.get("type")
        
        if message_type == "get_blocks":
            # Send our blockchain
            self._send_blockchain(node_id)
        
        elif message_type == "new_block":
            # Validate and add new block
            block_data = message.get("data")
            if block_data:
                self._handle_new_block(block_data)
    def _handle_new_block(self, block_data: dict) -> bool:
        """Handle a new block from another node"""
        try:
            # Print block info for debugging
            print(f"Received new block: index={block_data.get('index')}, hash={block_data.get('hash')}")
            
            # Convert dict to Block object
            new_block = self._dict_to_block(block_data)
            
            # Validate block hash
            calculated_hash = new_block.calculate_hash()
            if new_block.hash != calculated_hash:
                print(f"Block hash validation failed: received={new_block.hash}, calculated={calculated_hash}")
                return False
            
            # Check if we already have this block by hash
            for existing_block in self.blockchain.chain:
                if existing_block.hash == new_block.hash:
                    print(f"Block already in our chain (#{new_block.index}), ignoring")
                    return True
            
            # Check block index
            current_last_block = self.blockchain.chain[-1] if self.blockchain.chain else None
            if not current_last_block:
                print(f"No blocks in our chain yet, cannot add block #{new_block.index}")
                return False
                
            # If this is the next block in sequence, validate the previous hash
            if new_block.index == current_last_block.index + 1:
                if new_block.previous_hash != current_last_block.hash:
                    print(f"Block #{new_block.index} previous_hash doesn't match our last block hash")
                    print(f"Our last block: hash={current_last_block.hash}")
                    print(f"New block prev_hash: {new_block.previous_hash}")
                    return False
                    
                # This block is valid and next in sequence
                print(f"Adding valid block #{new_block.index} to our chain")
                self.blockchain.chain.append(new_block)
                
                # Remove transactions in this block from our mempool
                mempool_before = len(self.blockchain.mempool)
                for tx in new_block.transactions:
                    # Find matching transactions in mempool by key attributes
                    for mempool_tx in list(self.blockchain.mempool):
                        if (mempool_tx.sender == tx.sender and 
                            mempool_tx.recipient == tx.recipient and
                            abs(mempool_tx.amount - tx.amount) < 0.0001 and
                            mempool_tx.transaction_type == tx.transaction_type):
                            self.blockchain.mempool.remove(mempool_tx)
                            break
                
                mempool_after = len(self.blockchain.mempool)
                print(f"Removed {mempool_before - mempool_after} transactions from mempool")
                print(f"Successfully added new block #{new_block.index} to chain")
                
                # If we're mining, adjust difficulty based on new chain
                if self.is_mining:
                    self.blockchain.adjust_difficulty()
                
                return True
            
            # If the block is ahead of our chain, we might need to sync the missing blocks
            if new_block.index > current_last_block.index + 1:
                print(f"Received block #{new_block.index} but our last block is #{current_last_block.index}")
                print(f"Need to synchronize missing blocks")
                
                # Trigger blockchain sync to get missing blocks
                threading.Thread(target=self._sync_blockchain).start()
                return False
                
            # If the block is behind our chain, ignore it (we're ahead)
            if new_block.index <= current_last_block.index:
                print(f"Received block #{new_block.index} but we already have {current_last_block.index + 1} blocks")
                return False
                
        except Exception as e:
            print(f"Error handling new block from network: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    def add(self, amount: float) -> None:
        """Add amount to coin"""
        self.amount = round(self.amount + float(amount), 8)
        self._validate_amount()
    
    def subtract(self, amount: float) -> None:
        """Subtract amount from coin"""
        self.amount = round(self.amount - float(amount), 8)
        self._validate_amount()
    
    def to_dict(self) -> Dict:
        """Convert coin to dictionary for serialization"""
        return {
            "amount": format(self.amount, '.8f'),
            "owner": self.owner
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Coin':
        """Create coin from dictionary"""
        return cls(float(data["amount"]), data.get("owner"))
    
    def __str__(self) -> str:
        return f"GCN({self.amount})"
    
    def __repr__(self) -> str:
        return self.__str__()

@dataclass
class Node:
    address: str
    port: int
    last_seen: float

class GlobalCoyn:
    def __init__(self, host: str = "0.0.0.0", port: int = 9000, dev_mode: bool = False):
        self.host = host
        self.port = port
        self.blockchain = Blockchain()
        self.peers: Dict[str, Node] = {}
        self.mining_address: Optional[str] = None
        self.is_mining = False
        self.is_running = False
        self.dev_mode = dev_mode
        
        if not dev_mode:
            # Initialize network sockets only in production mode
            self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.p2p_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # For development, use only local connections to Node 2
            self.seed_nodes = [
                ("127.0.0.1", 9001),  # Node 2 running locally
                ("localhost", 9001)   # Another way to reference Node 2
            ]

    def start(self) -> None:
        """Start the GlobalCoyn node"""
        self.is_running = True
        self.start_time = time.time()  # Track node uptime
        
        # Load blockchain from disk if available
        self.blockchain.load_chain_from_disk()
        logging.info(f"Loaded blockchain with {len(self.blockchain.chain)} blocks")
        
        if not self.dev_mode:
            try:
                # Start P2P server only in production mode
                try:
                    self.p2p_socket.bind((self.host, self.port))
                    self.p2p_socket.listen(10)
                    print(f"P2P server listening on {self.host}:{self.port}")
                except OSError as bind_error:
                    if bind_error.errno == 48:  # Address already in use
                        print(f"P2P port {self.port} already in use, continuing with existing socket")
                    else:
                        raise
                
                # Start network threads
                threading.Thread(target=self._accept_connections, daemon=True).start()
                threading.Thread(target=self._maintain_connections, daemon=True).start()
                
                # Enable enhanced blockchain synchronization
                self.block_sync = enhance_globalcoyn_networking(self)
                logging.info("Enhanced blockchain synchronization enabled")
                
                # Connect to seed nodes
                self._connect_to_seed_nodes()
            except OSError as e:
                print(f"Network error (expected in dev mode): {e}")
                # Continue without network in dev mode

    def stop(self) -> None:
        """Stop the GlobalCoyn node"""
        self.is_running = False
        self.is_mining = False
        
        # Save blockchain state before shutting down
        self.blockchain.save_chain_to_disk()
        logging.info("Blockchain state saved")
        
        if not self.dev_mode:
            try:
                self.p2p_socket.close()
            except:
                pass

    def _accept_connections(self) -> None:
        """Accept incoming P2P connections"""
        while self.is_running:
            try:
                client_socket, address = self.p2p_socket.accept()
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except:
                if self.is_running:
                    time.sleep(1)

    def _handle_connection(self, client_socket: socket.socket, address: tuple) -> None:
        """Handle incoming P2P connection"""
        node_id = f"{address[0]}:{address[1]}"
        print(f"Handling connection from {node_id}")
        
        try:
            # Perform handshake
            if not self._perform_handshake(client_socket):
                print(f"Handshake failed with {node_id}, closing connection")
                client_socket.close()
                return
            
            print(f"Adding new peer: {node_id}")
            
            # Add to peers
            self.peers[node_id] = Node(
                address=address[0],
                port=address[1],
                last_seen=time.time()
            )
            
            # Send our blockchain height to trigger sync if needed
            height_message = {
                "type": "height",
                "height": len(self.blockchain.chain)
            }
            self._send_message(client_socket, height_message)
            
            # Handle messages in a loop
            print(f"Entering message handling loop for {node_id}")
            message_count = 0
            
            while self.is_running:
                try:
                    message = self._receive_message(client_socket)
                    if not message:
                        print(f"Connection closed by {node_id}")
                        break
                    
                    message_count += 1
                    print(f"Received message #{message_count} from {node_id}: {message.get('type')}")
                    self._handle_message(message, node_id)
                    
                except socket.timeout:
                    # Just a timeout, continue
                    continue
                except Exception as msg_error:
                    print(f"Error handling message from {node_id}: {str(msg_error)}")
                    break
            
        except Exception as e:
            print(f"Error in connection handler for {node_id}: {str(e)}")
        finally:
            print(f"Closing connection with {node_id}")
            client_socket.close()
            if node_id in self.peers:
                print(f"Removing peer {node_id}")
                del self.peers[node_id]

    def _handle_message(self, message: dict, node_id: str) -> None:
        """Handle incoming P2P message"""
        message_type = message.get("type")
        
        if message_type == "get_blocks":
            # Send our blockchain
            self._send_blockchain(node_id)
        
        elif message_type == "new_block":
            # Validate and add new block
            block_data = message.get("data")
            if block_data:
                self._handle_new_block(block_data)
    def _handle_new_block(self, block_data: dict) -> bool:
        """Handle a new block from another node"""
        try:
            # Print block info for debugging
            print(f"Received new block: index={block_data.get('index')}, hash={block_data.get('hash')}")
            
            # Convert dict to Block object
            new_block = self._dict_to_block(block_data)
            
            # Validate block hash
            calculated_hash = new_block.calculate_hash()
            if new_block.hash != calculated_hash:
                print(f"Block hash validation failed: received={new_block.hash}, calculated={calculated_hash}")
                return False
            
            # Check if we already have this block by hash
            for existing_block in self.blockchain.chain:
                if existing_block.hash == new_block.hash:
                    print(f"Block already in our chain (#{new_block.index}), ignoring")
                    return True
            
            # Check block index
            current_last_block = self.blockchain.chain[-1] if self.blockchain.chain else None
            if not current_last_block:
                print(f"No blocks in our chain yet, cannot add block #{new_block.index}")
                return False
                
            # If this is the next block in sequence, validate the previous hash
            if new_block.index == current_last_block.index + 1:
                if new_block.previous_hash != current_last_block.hash:
                    print(f"Block #{new_block.index} previous_hash doesn't match our last block hash")
                    print(f"Our last block: hash={current_last_block.hash}")
                    print(f"New block prev_hash: {new_block.previous_hash}")
                    return False
                    
                # This block is valid and next in sequence
                print(f"Adding valid block #{new_block.index} to our chain")
                self.blockchain.add_block(new_block)  # Use add_block method which saves chain to disk
                
                # Remove transactions in this block from our mempool
                mempool_before = len(self.blockchain.mempool)
                for tx in new_block.transactions:
                    # Find matching transactions in mempool by key attributes
                    for mempool_tx in list(self.blockchain.mempool):
                        if (mempool_tx.sender == tx.sender and 
                            mempool_tx.recipient == tx.recipient and
                            abs(mempool_tx.amount - tx.amount) < 0.0001 and
                            mempool_tx.transaction_type == tx.transaction_type):
                            self.blockchain.mempool.remove(mempool_tx)
                            break
                
                mempool_after = len(self.blockchain.mempool)
                print(f"Removed {mempool_before - mempool_after} transactions from mempool")
                print(f"Successfully added new block #{new_block.index} to chain")
                
                # If we're mining, adjust difficulty based on new chain
                if self.is_mining:
                    self.blockchain.adjust_difficulty()
                
                return True
            
            # If the block is ahead of our chain, we might need to sync the missing blocks
            if new_block.index > current_last_block.index + 1:
                print(f"Received block #{new_block.index} but our last block is #{current_last_block.index}")
                print(f"Need to synchronize missing blocks")
                
                # Block sync will handle this automatically with the enhanced networking
                return False
                
            # If the block is behind our chain, ignore it (we're ahead)
            if new_block.index <= current_last_block.index:
                print(f"Received block #{new_block.index} but we already have {current_last_block.index + 1} blocks")
                return False
                
        except Exception as e:
            print(f"Error handling new block from network: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    def add(self, amount: float) -> None:
        """Add amount to coin"""
        self.amount = round(self.amount + float(amount), 8)
        self._validate_amount()
    
    def subtract(self, amount: float) -> None:
        """Subtract amount from coin"""
        self.amount = round(self.amount - float(amount), 8)
        self._validate_amount()
    
    def to_dict(self) -> Dict:
        """Convert coin to dictionary for serialization"""
        return {
            "amount": format(self.amount, '.8f'),
            "owner": self.owner
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Coin':
        """Create coin from dictionary"""
        return cls(float(data["amount"]), data.get("owner"))
    
    def __str__(self) -> str:
        return f"GCN({self.amount})"
    
    def __repr__(self) -> str:
        return self.__str__()

@dataclass
class Node:
    address: str
    port: int
    last_seen: float

class GlobalCoyn:
    def __init__(self, host: str = "0.0.0.0", port: int = 9000, dev_mode: bool = False):
        self.host = host
        self.port = port
        self.blockchain = Blockchain()
        self.peers: Dict[str, Node] = {}
        self.mining_address: Optional[str] = None
        self.is_mining = False
        self.is_running = False
        self.dev_mode = dev_mode
        
        if not dev_mode:
            # Initialize network sockets only in production mode
            self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.p2p_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # For development, use only local connections to Node 2
            self.seed_nodes = [
                ("127.0.0.1", 9001),  # Node 2 running locally
                ("localhost", 9001)   # Another way to reference Node 2
            ]

    def start(self) -> None:
        """Start the GlobalCoyn node"""
        self.is_running = True
        self.start_time = time.time()  # Track node uptime
        
        # Load blockchain from disk if available
        self.blockchain.load_chain_from_disk()
        logging.info(f"Loaded blockchain with {len(self.blockchain.chain)} blocks")
        
        if not self.dev_mode:
            try:
                # Start P2P server only in production mode
                try:
                    self.p2p_socket.bind((self.host, self.port))
                    self.p2p_socket.listen(10)
                    print(f"P2P server listening on {self.host}:{self.port}")
                except OSError as bind_error:
                    if bind_error.errno == 48:  # Address already in use
                        print(f"P2P port {self.port} already in use, continuing with existing socket")
                    else:
                        raise
                
                # Start network threads
                threading.Thread(target=self._accept_connections, daemon=True).start()
                threading.Thread(target=self._maintain_connections, daemon=True).start()
                
                # Enable enhanced blockchain synchronization
                self.block_sync = enhance_globalcoyn_networking(self)
                logging.info("Enhanced blockchain synchronization enabled")
                
                # Connect to seed nodes
                self._connect_to_seed_nodes()
            except OSError as e:
                print(f"Network error (expected in dev mode): {e}")
                # Continue without network in dev mode

    def stop(self) -> None:
        """Stop the GlobalCoyn node"""
        self.is_running = False
        self.is_mining = False
        
        # Save blockchain state before shutting down
        self.blockchain.save_chain_to_disk()
        logging.info("Blockchain state saved")
        
        if not self.dev_mode:
            try:
                self.p2p_socket.close()
            except:
                pass

    def _accept_connections(self) -> None:
        """Accept incoming P2P connections"""
        while self.is_running:
            try:
                client_socket, address = self.p2p_socket.accept()
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except:
                if self.is_running:
                    time.sleep(1)

    def _handle_connection(self, client_socket: socket.socket, address: tuple) -> None:
        """Handle incoming P2P connection"""
        node_id = f"{address[0]}:{address[1]}"
        print(f"Handling connection from {node_id}")
        
        try:
            # Perform handshake
            if not self._perform_handshake(client_socket):
                print(f"Handshake failed with {node_id}, closing connection")
                client_socket.close()
                return
            
            print(f"Adding new peer: {node_id}")
            
            # Add to peers
            self.peers[node_id] = Node(
                address=address[0],
                port=address[1],
                last_seen=time.time()
            )
            
            # Send our blockchain height to trigger sync if needed
            height_message = {
                "type": "height",
                "height": len(self.blockchain.chain)
            }
            self._send_message(client_socket, height_message)
            
            # Handle messages in a loop
            print(f"Entering message handling loop for {node_id}")
            message_count = 0
            
            while self.is_running:
                try:
                    message = self._receive_message(client_socket)
                    if not message:
                        print(f"Connection closed by {node_id}")
                        break
                    
                    message_count += 1
                    print(f"Received message #{message_count} from {node_id}: {message.get('type')}")
                    self._handle_message(message, node_id)
                    
                except socket.timeout:
                    # Just a timeout, continue
                    continue
                except Exception as msg_error:
                    print(f"Error handling message from {node_id}: {str(msg_error)}")
                    break
            
        except Exception as e:
            print(f"Error in connection handler for {node_id}: {str(e)}")
        finally:
            print(f"Closing connection with {node_id}")
            client_socket.close()
            if node_id in self.peers:
                print(f"Removing peer {node_id}")
                del self.peers[node_id]

    def _handle_message(self, message: dict, node_id: str) -> None:
        """Handle incoming P2P message"""
        message_type = message.get("type")
        
        if message_type == "get_blocks":
            # Send our blockchain
            self._send_blockchain(node_id)
        
        elif message_type == "new_block":
            # Validate and add new block
            block_data = message.get("data")
            if block_data:
                self._handle_new_block(block_data)
        
        elif message_type == "new_transaction":
            # Add transaction to mempool
            tx_data = message.get("data")
            if tx_data:
                self._handle_new_transaction(tx_data)
        
        elif message_type == "get_block_range":
            # Handle request for a range of blocks
            start_height = message.get("start_height", 0)
            end_height = message.get("end_height", len(self.blockchain.chain))
            self._handle_block_range_request(node_id, start_height, end_height)

        elif message_type == "block_range":
            # Process received block range
            blocks_data = message.get("blocks", [])
            if blocks_data:
                self._process_block_range(blocks_data)

        elif message_type == "get_peers":
            # Share our peer list
            self._send_peer_list(node_id)
            
        elif message_type == "get_height":
            # Send our blockchain height
            self._send_blockchain_height(node_id)
            
        elif message_type == "peers":
            # Process received peer list
            self._handle_peer_list(message.get("peers", []), node_id)

    def _connect_to_seed_nodes(self) -> None:
        """Connect to seed nodes for initial network connection"""
        print(f"Attempting to connect to {len(self.seed_nodes)} seed nodes...")
        
        for seed_host, seed_port in self.seed_nodes:
            try:
                print(f"Connecting to seed node {seed_host}:{seed_port}...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)  # Add a timeout for the connection
                
                # Try to connect to the seed node
                try:
                    sock.connect((seed_host, seed_port))
                    print(f"Connected to seed node {seed_host}:{seed_port}")
                except ConnectionRefusedError:
                    print(f"Connection refused to {seed_host}:{seed_port}")
                    continue
                except socket.timeout:
                    print(f"Connection timeout to {seed_host}:{seed_port}")
                    continue
                except Exception as e:
                    print(f"Failed to connect to {seed_host}:{seed_port}: {str(e)}")
                    continue
                
                # Perform handshake
                if self._perform_handshake(sock):
                    print(f"Handshake successful with {seed_host}:{seed_port}")
                    node_id = f"{seed_host}:{seed_port}"
                    self.peers[node_id] = Node(
                        address=seed_host,
                        port=seed_port,
                        last_seen=time.time()
                    )
                    
                    # Start handler thread
                    threading.Thread(
                        target=self._handle_connection,
                        args=(sock, (seed_host, seed_port)),
                        daemon=True
                    ).start()
                    print(f"Started connection handler thread for {node_id}")
                else:
                    print(f"Handshake failed with {seed_host}:{seed_port}")
                    sock.close()
            except Exception as e:
                print(f"Error connecting to seed node {seed_host}:{seed_port}: {str(e)}")
                continue
                
        print(f"Connected to {len(self.peers)} seed nodes")

    def _maintain_connections(self) -> None:
        """Maintain network connections and remove stale peers"""
        while self.is_running:
            current_time = time.time()
            stale_peers = []
            
            # Check for stale connections
            for node_id, node in self.peers.items():
                if current_time - node.last_seen > 300:  # 5 minutes timeout
                    stale_peers.append(node_id)
            
            # Remove stale peers
            for node_id in stale_peers:
                del self.peers[node_id]
            
            # Try to maintain minimum peer connections
            if len(self.peers) < 8:
                self._connect_to_seed_nodes()
            
            time.sleep(60)

    def _sync_blockchain(self) -> None:
        """Synchronize blockchain with network"""
        print("Starting blockchain synchronization thread")
        
        sync_interval = 30  # Check for sync every 30 seconds initially
        
        while self.is_running:
            try:
                if not self.peers:
                    print("No peers connected, skipping blockchain sync")
                    time.sleep(sync_interval)
                    continue
                    
                # Check if our blockchain needs syncing
                our_height = len(self.blockchain.chain)
                
                print(f"Checking if we need to sync blockchain (current height: {our_height})")
                
                # Request heights from all peers to find the longest chain
                max_height = our_height
                max_height_peer = None
                peer_heights = {}
                
                for peer_id, peer in list(self.peers.items()):  # Use list() to avoid modification during iteration
                    try:
                        print(f"Requesting blockchain height from peer {peer_id}")
                        
                        # Get peer's blockchain height
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(10)  # 10 second timeout
                        
                        try:
                            sock.connect((peer.address, peer.port))
                        except ConnectionRefusedError:
                            print(f"Connection refused by peer {peer_id}")
                            if peer_id in self.peers:
                                del self.peers[peer_id]
                            continue
                        except Exception as conn_err:
                            print(f"Failed to connect to peer {peer_id}: {str(conn_err)}")
                            continue
                        
                        # Send get_height message
                        message = {"type": "get_height"}
                        if not self._send_message(sock, message):
                            print(f"Failed to send height request to peer {peer_id}")
                            sock.close()
                            continue
                        
                        # Receive response
                        response = self._receive_message(sock)
                        sock.close()
                        
                        if response and "height" in response:
                            peer_height = response["height"]
                            peer_heights[peer_id] = peer_height
                            print(f"Peer {peer_id} has {peer_height} blocks")
                            
                            if peer_height > max_height:
                                max_height = peer_height
                                max_height_peer = peer_id
                        else:
                            print(f"Invalid height response from peer {peer_id}: {response}")
                    except socket.timeout:
                        print(f"Timeout while requesting height from peer {peer_id}")
                        continue
                    except Exception as e:
                        print(f"Error requesting height from peer {peer_id}: {str(e)}")
                        continue
                
                print(f"Peer heights: {peer_heights}")
                print(f"Highest blockchain: {max_height} blocks from peer {max_height_peer}")
                
                # If we found a longer chain, sync with that peer
                if max_height_peer and max_height > our_height:
                    print(f"Found longer blockchain ({max_height} blocks) from peer {max_height_peer}. Syncing...")
                    success = self._request_blockchain(max_height_peer)
                    
                    if success:
                        print(f"Successfully synced blockchain to height {len(self.blockchain.chain)}")
                        
                        # After successful sync, broadcast our height to all peers
                        height_message = {
                            "type": "height",
                            "height": len(self.blockchain.chain)
                        }
                        self._broadcast_message(height_message)
                        
                        # Reduce sync interval as we're in sync
                        sync_interval = 60  # Check every minute when in sync
                    else:
                        print(f"Failed to sync blockchain from peer {max_height_peer}")
                        # Make sync more frequent after failure
                        sync_interval = 15  # Check more frequently after failure
                else:
                    print(f"Our blockchain is up to date (height: {our_height})")
                    # If we're in sync with the network, reduce sync frequency
                    sync_interval = 60  # Check every minute when in sync
                
            except Exception as e:
                print(f"Error in blockchain sync: {str(e)}")
                import traceback
                traceback.print_exc()
                
                # Reduced interval after error
                sync_interval = 15
                
            time.sleep(sync_interval)

    def start_mining(self, miner_address: str) -> None:
        """Start mining blocks"""
        if self.is_mining:
            return
        
        self.mining_address = miner_address
        self.is_mining = True
        
        threading.Thread(target=self._mining_loop, daemon=True).start()

    def stop_mining(self) -> None:
        """Stop mining blocks"""
        self.is_mining = False
        self.mining_address = None

    def _mining_loop(self) -> None:
        """Main mining loop"""
        while self.is_mining and self.is_running:
            # Mine a new block
            new_block = self.mine_block(self.mining_address)
            
            if new_block and not self.dev_mode:
                # Broadcast new block to network only in production mode
                self._broadcast_block(new_block)
    def _broadcast_block(self, block: Block) -> None:
        print(f"Broadcasting block #{block.index} to {len(self.peers)} peers")
        print(f"Block hash: {block.hash}")
                
        print(f"Broadcasting block #{block.index} (hash: {block.hash}) to peers...")
        
        message = {
            "type": "new_block",
            "data": self._block_to_dict(block)
        }
        
        successful_broadcasts = 0
        for node_id, node in list(self.peers.items()):  # Use list() to avoid modification during iteration
            try:
                print(f"Sending block to peer {node_id}...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)  # 10 second timeout for block broadcast
                
                try:
                    sock.connect((node.address, node.port))
                except ConnectionRefusedError:
                    print(f"Connection refused by peer {node_id}")
                    continue
                except Exception as conn_err:
                    print(f"Failed to connect to peer {node_id}: {str(conn_err)}")
                    continue
                
                # Send the block message
                if self._send_message(sock, message):
                    print(f"Successfully sent block to peer {node_id}")
                    successful_broadcasts += 1
                else:
                    print(f"Failed to send block message to peer {node_id}")
                
                sock.close()
            except Exception as e:
                print(f"Error broadcasting block to peer {node_id}: {str(e)}")
                continue
        
        print(f"Block broadcast complete. Sent to {successful_broadcasts}/{len(self.peers)} peers")
    def __init__(self, amount: float = 0, owner: str = None):
        self.amount = round(float(amount), 8)  # Store with 8 decimal precision
        self.owner = owner  # Wallet address that owns this coin
        self._validate_amount()
    
    def _validate_amount(self) -> None:
        """Validate coin amount"""
        if self.amount < 0:
            raise ValueError("Coin amount cannot be negative")
        if self.amount > 1_000_000_000:  # 1 billion max supply
            raise ValueError("Coin amount exceeds maximum supply")
    
    def add(self, amount: float) -> None:
        """Add amount to coin"""
        self.amount = round(self.amount + float(amount), 8)
        self._validate_amount()
    
    def subtract(self, amount: float) -> None:
        """Subtract amount from coin"""
        self.amount = round(self.amount - float(amount), 8)
        self._validate_amount()
    
    def to_dict(self) -> Dict:
        """Convert coin to dictionary for serialization"""
        return {
            "amount": format(self.amount, '.8f'),
            "owner": self.owner
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Coin':
        """Create coin from dictionary"""
        return cls(float(data["amount"]), data.get("owner"))
    
    def __str__(self) -> str:
        return f"GCN({self.amount})"
    
    def __repr__(self) -> str:
        return self.__str__()

@dataclass
class Node:
    address: str
    port: int
    last_seen: float

class GlobalCoyn:
    def __init__(self, host: str = "0.0.0.0", port: int = 9000, dev_mode: bool = False):
        self.host = host
        self.port = port
        self.blockchain = Blockchain()
        self.peers: Dict[str, Node] = {}
        self.mining_address: Optional[str] = None
        self.is_mining = False
        self.is_running = False
        self.dev_mode = dev_mode
        
        if not dev_mode:
            # Initialize network sockets only in production mode
            self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.p2p_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # For development, use only local connections to Node 2
            self.seed_nodes = [
                ("127.0.0.1", 9001),  # Node 2 running locally
                ("localhost", 9001)   # Another way to reference Node 2
            ]

    def start(self) -> None:
        """Start the GlobalCoyn node"""
        self.is_running = True
        self.start_time = time.time()  # Track node uptime
        
        # Load blockchain from disk if available
        self.blockchain.load_chain_from_disk()
        logging.info(f"Loaded blockchain with {len(self.blockchain.chain)} blocks")
        
        if not self.dev_mode:
            try:
                # Start P2P server only in production mode
                try:
                    self.p2p_socket.bind((self.host, self.port))
                    self.p2p_socket.listen(10)
                    print(f"P2P server listening on {self.host}:{self.port}")
                except OSError as bind_error:
                    if bind_error.errno == 48:  # Address already in use
                        print(f"P2P port {self.port} already in use, continuing with existing socket")
                    else:
                        raise
                
                # Start network threads
                threading.Thread(target=self._accept_connections, daemon=True).start()
                threading.Thread(target=self._maintain_connections, daemon=True).start()
                
                # Enable enhanced blockchain synchronization
                self.block_sync = enhance_globalcoyn_networking(self)
                logging.info("Enhanced blockchain synchronization enabled")
                
                # Connect to seed nodes
                self._connect_to_seed_nodes()
            except OSError as e:
                print(f"Network error (expected in dev mode): {e}")
                # Continue without network in dev mode

    def stop(self) -> None:
        """Stop the GlobalCoyn node"""
        self.is_running = False
        self.is_mining = False
        
        # Save blockchain state before shutting down
        self.blockchain.save_chain_to_disk()
        logging.info("Blockchain state saved")
        
        if not self.dev_mode:
            try:
                self.p2p_socket.close()
            except:
                pass

    def _accept_connections(self) -> None:
        """Accept incoming P2P connections"""
        while self.is_running:
            try:
                client_socket, address = self.p2p_socket.accept()
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except:
                if self.is_running:
                    time.sleep(1)

    def _handle_connection(self, client_socket: socket.socket, address: tuple) -> None:
        """Handle incoming P2P connection"""
        node_id = f"{address[0]}:{address[1]}"
        print(f"Handling connection from {node_id}")
        
        try:
            # Perform handshake
            if not self._perform_handshake(client_socket):
                print(f"Handshake failed with {node_id}, closing connection")
                client_socket.close()
                return
            
            print(f"Adding new peer: {node_id}")
            
            # Add to peers
            self.peers[node_id] = Node(
                address=address[0],
                port=address[1],
                last_seen=time.time()
            )
            
            # Send our blockchain height to trigger sync if needed
            height_message = {
                "type": "height",
                "height": len(self.blockchain.chain)
            }
            self._send_message(client_socket, height_message)
            
            # Handle messages in a loop
            print(f"Entering message handling loop for {node_id}")
            message_count = 0
            
            while self.is_running:
                try:
                    message = self._receive_message(client_socket)
                    if not message:
                        print(f"Connection closed by {node_id}")
                        break
                    
                    message_count += 1
                    print(f"Received message #{message_count} from {node_id}: {message.get('type')}")
                    self._handle_message(message, node_id)
                    
                except socket.timeout:
                    # Just a timeout, continue
                    continue
                except Exception as msg_error:
                    print(f"Error handling message from {node_id}: {str(msg_error)}")
                    break
            
        except Exception as e:
            print(f"Error in connection handler for {node_id}: {str(e)}")
        finally:
            print(f"Closing connection with {node_id}")
            client_socket.close()
            if node_id in self.peers:
                print(f"Removing peer {node_id}")
                del self.peers[node_id]

    def _handle_message(self, message: dict, node_id: str) -> None:
        """Handle incoming P2P message"""
        message_type = message.get("type")
        
        if message_type == "get_blocks":
            # Send our blockchain
            self._send_blockchain(node_id)
        
        elif message_type == "new_block":
            # Validate and add new block
            block_data = message.get("data")
            if block_data:
                self._handle_new_block(block_data)
    def _handle_new_block(self, block_data: dict) -> bool:
        """Handle a new block from another node"""
        try:
            # Print block info for debugging
            print(f"Received new block: index={block_data.get('index')}, hash={block_data.get('hash')}")
            
            # Convert dict to Block object
            new_block = self._dict_to_block(block_data)
            
            # Validate block hash
            calculated_hash = new_block.calculate_hash()
            if new_block.hash != calculated_hash:
                print(f"Block hash validation failed: received={new_block.hash}, calculated={calculated_hash}")
                return False
            
            # Check if we already have this block by hash
            for existing_block in self.blockchain.chain:
                if existing_block.hash == new_block.hash:
                    print(f"Block already in our chain (#{new_block.index}), ignoring")
                    return True
            
            # Check block index
            current_last_block = self.blockchain.chain[-1] if self.blockchain.chain else None
            if not current_last_block:
                print(f"No blocks in our chain yet, cannot add block #{new_block.index}")
                return False
                
            # If this is the next block in sequence, validate the previous hash
            if new_block.index == current_last_block.index + 1:
                if new_block.previous_hash != current_last_block.hash:
                    print(f"Block #{new_block.index} previous_hash doesn't match our last block hash")
                    print(f"Our last block: hash={current_last_block.hash}")
                    print(f"New block prev_hash: {new_block.previous_hash}")
                    return False
                    
                # This block is valid and next in sequence
                print(f"Adding valid block #{new_block.index} to our chain")
                self.blockchain.chain.append(new_block)
                
                # Remove transactions in this block from our mempool
                mempool_before = len(self.blockchain.mempool)
                for tx in new_block.transactions:
                    # Find matching transactions in mempool by key attributes
                    for mempool_tx in list(self.blockchain.mempool):
                        if (mempool_tx.sender == tx.sender and 
                            mempool_tx.recipient == tx.recipient and
                            abs(mempool_tx.amount - tx.amount) < 0.0001 and
                            mempool_tx.transaction_type == tx.transaction_type):
                            self.blockchain.mempool.remove(mempool_tx)
                            break
                
                mempool_after = len(self.blockchain.mempool)
                print(f"Removed {mempool_before - mempool_after} transactions from mempool")
                print(f"Successfully added new block #{new_block.index} to chain")
                
                # If we're mining, adjust difficulty based on new chain
                if self.is_mining:
                    self.blockchain.adjust_difficulty()
                
                return True
            
            # If the block is ahead of our chain, we might need to sync the missing blocks
            if new_block.index > current_last_block.index + 1:
                print(f"Received block #{new_block.index} but our last block is #{current_last_block.index}")
                print(f"Need to synchronize missing blocks")
                
                # Trigger blockchain sync to get missing blocks
                threading.Thread(target=self._sync_blockchain).start()
                return False
                
            # If the block is behind our chain, ignore it (we're ahead)
            if new_block.index <= current_last_block.index:
                print(f"Received block #{new_block.index} but we already have {current_last_block.index + 1} blocks")
                return False
                
        except Exception as e:
            print(f"Error handling new block from network: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    def add(self, amount: float) -> None:
        """Add amount to coin"""
        self.amount = round(self.amount + float(amount), 8)
        self._validate_amount()
    
    def subtract(self, amount: float) -> None:
        """Subtract amount from coin"""
        self.amount = round(self.amount - float(amount), 8)
        self._validate_amount()
    
    def to_dict(self) -> Dict:
        """Convert coin to dictionary for serialization"""
        return {
            "amount": format(self.amount, '.8f'),
            "owner": self.owner
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Coin':
        """Create coin from dictionary"""
        return cls(float(data["amount"]), data.get("owner"))
    
    def __str__(self) -> str:
        return f"GCN({self.amount})"
    
    def __repr__(self) -> str:
        return self.__str__()

@dataclass
class Node:
    address: str
    port: int
    last_seen: float

class GlobalCoyn:
    def __init__(self, host: str = "0.0.0.0", port: int = 9000, dev_mode: bool = False):
        self.host = host
        self.port = port
        self.blockchain = Blockchain()
        self.peers: Dict[str, Node] = {}
        self.mining_address: Optional[str] = None
        self.is_mining = False
        self.is_running = False
        self.dev_mode = dev_mode
        
        if not dev_mode:
            # Initialize network sockets only in production mode
            self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.p2p_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # For development, use only local connections to Node 2
            self.seed_nodes = [
                ("127.0.0.1", 9001),  # Node 2 running locally
                ("localhost", 9001)   # Another way to reference Node 2
            ]

    def start(self) -> None:
        """Start the GlobalCoyn node"""
        self.is_running = True
        self.start_time = time.time()  # Track node uptime
        
        # Load blockchain from disk if available
        self.blockchain.load_chain_from_disk()
        logging.info(f"Loaded blockchain with {len(self.blockchain.chain)} blocks")
        
        if not self.dev_mode:
            try:
                # Start P2P server only in production mode
                try:
                    self.p2p_socket.bind((self.host, self.port))
                    self.p2p_socket.listen(10)
                    print(f"P2P server listening on {self.host}:{self.port}")
                except OSError as bind_error:
                    if bind_error.errno == 48:  # Address already in use
                        print(f"P2P port {self.port} already in use, continuing with existing socket")
                    else:
                        raise
                
                # Start network threads
                threading.Thread(target=self._accept_connections, daemon=True).start()
                threading.Thread(target=self._maintain_connections, daemon=True).start()
                
                # Enable enhanced blockchain synchronization
                self.block_sync = enhance_globalcoyn_networking(self)
                logging.info("Enhanced blockchain synchronization enabled")
                
                # Connect to seed nodes
                self._connect_to_seed_nodes()
            except OSError as e:
                print(f"Network error (expected in dev mode): {e}")
                # Continue without network in dev mode

    def stop(self) -> None:
        """Stop the GlobalCoyn node"""
        self.is_running = False
        self.is_mining = False
        
        # Save blockchain state before shutting down
        self.blockchain.save_chain_to_disk()
        logging.info("Blockchain state saved")
        
        if not self.dev_mode:
            try:
                self.p2p_socket.close()
            except:
                pass

    def _accept_connections(self) -> None:
        """Accept incoming P2P connections"""
        while self.is_running:
            try:
                client_socket, address = self.p2p_socket.accept()
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except:
                if self.is_running:
                    time.sleep(1)

    def _handle_connection(self, client_socket: socket.socket, address: tuple) -> None:
        """Handle incoming P2P connection"""
        node_id = f"{address[0]}:{address[1]}"
        print(f"Handling connection from {node_id}")
        
        try:
            # Perform handshake
            if not self._perform_handshake(client_socket):
                print(f"Handshake failed with {node_id}, closing connection")
                client_socket.close()
                return
            
            print(f"Adding new peer: {node_id}")
            
            # Add to peers
            self.peers[node_id] = Node(
                address=address[0],
                port=address[1],
                last_seen=time.time()
            )
            
            # Send our blockchain height to trigger sync if needed
            height_message = {
                "type": "height",
                "height": len(self.blockchain.chain)
            }
            self._send_message(client_socket, height_message)
            
            # Handle messages in a loop
            print(f"Entering message handling loop for {node_id}")
            message_count = 0
            
            while self.is_running:
                try:
                    message = self._receive_message(client_socket)
                    if not message:
                        print(f"Connection closed by {node_id}")
                        break
                    
                    message_count += 1
                    print(f"Received message #{message_count} from {node_id}: {message.get('type')}")
                    self._handle_message(message, node_id)
                    
                except socket.timeout:
                    # Just a timeout, continue
                    continue
                except Exception as msg_error:
                    print(f"Error handling message from {node_id}: {str(msg_error)}")
                    break
            
        except Exception as e:
            print(f"Error in connection handler for {node_id}: {str(e)}")
        finally:
            print(f"Closing connection with {node_id}")
            client_socket.close()
            if node_id in self.peers:
                print(f"Removing peer {node_id}")
                del self.peers[node_id]

    def _handle_message(self, message: dict, node_id: str) -> None:
        """Handle incoming P2P message"""
        message_type = message.get("type")
        
        if message_type == "get_blocks":
            # Send our blockchain
            self._send_blockchain(node_id)
        
        elif message_type == "new_block":
            # Validate and add new block
            block_data = message.get("data")
            if block_data:
                self._handle_new_block(block_data)
    def _handle_new_block(self, block_data: dict) -> bool:
        """Handle a new block from another node"""
        try:
            # Print block info for debugging
            print(f"Received new block: index={block_data.get('index')}, hash={block_data.get('hash')}")
            
            # Convert dict to Block object
            new_block = self._dict_to_block(block_data)
            
            # Validate block hash
            calculated_hash = new_block.calculate_hash()
            if new_block.hash != calculated_hash:
                print(f"Block hash validation failed: received={new_block.hash}, calculated={calculated_hash}")
                return False
            
            # Check if we already have this block by hash
            for existing_block in self.blockchain.chain:
                if existing_block.hash == new_block.hash:
                    print(f"Block already in our chain (#{new_block.index}), ignoring")
                    return True
            
            # Check block index
            current_last_block = self.blockchain.chain[-1] if self.blockchain.chain else None
            if not current_last_block:
                print(f"No blocks in our chain yet, cannot add block #{new_block.index}")
                return False
                
            # If this is the next block in sequence, validate the previous hash
            if new_block.index == current_last_block.index + 1:
                if new_block.previous_hash != current_last_block.hash:
                    print(f"Block #{new_block.index} previous_hash doesn't match our last block hash")
                    print(f"Our last block: hash={current_last_block.hash}")
                    print(f"New block prev_hash: {new_block.previous_hash}")
                    return False
                    
                # This block is valid and next in sequence
                print(f"Adding valid block #{new_block.index} to our chain")
                self.blockchain.add_block(new_block)  # Use add_block method which saves chain to disk
                
                # Remove transactions in this block from our mempool
                mempool_before = len(self.blockchain.mempool)
                for tx in new_block.transactions:
                    # Find matching transactions in mempool by key attributes
                    for mempool_tx in list(self.blockchain.mempool):
                        if (mempool_tx.sender == tx.sender and 
                            mempool_tx.recipient == tx.recipient and
                            abs(mempool_tx.amount - tx.amount) < 0.0001 and
                            mempool_tx.transaction_type == tx.transaction_type):
                            self.blockchain.mempool.remove(mempool_tx)
                            break
                
                mempool_after = len(self.blockchain.mempool)
                print(f"Removed {mempool_before - mempool_after} transactions from mempool")
                print(f"Successfully added new block #{new_block.index} to chain")
                
                # If we're mining, adjust difficulty based on new chain
                if self.is_mining:
                    self.blockchain.adjust_difficulty()
                
                return True
            
            # If the block is ahead of our chain, we might need to sync the missing blocks
            if new_block.index > current_last_block.index + 1:
                print(f"Received block #{new_block.index} but our last block is #{current_last_block.index}")
                print(f"Need to synchronize missing blocks")
                
                # Block sync will handle this automatically with the enhanced networking
                return False
                
            # If the block is behind our chain, ignore it (we're ahead)
            if new_block.index <= current_last_block.index:
                print(f"Received block #{new_block.index} but we already have {current_last_block.index + 1} blocks")
                return False
                
        except Exception as e:
            print(f"Error handling new block from network: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    def add(self, amount: float) -> None:
        """Add amount to coin"""
        self.amount = round(self.amount + float(amount), 8)
        self._validate_amount()
    
    def subtract(self, amount: float) -> None:
        """Subtract amount from coin"""
        self.amount = round(self.amount - float(amount), 8)
        self._validate_amount()
    
    def to_dict(self) -> Dict:
        """Convert coin to dictionary for serialization"""
        return {
            "amount": format(self.amount, '.8f'),
            "owner": self.owner
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Coin':
        """Create coin from dictionary"""
        return cls(float(data["amount"]), data.get("owner"))
    
    def __str__(self) -> str:
        return f"GCN({self.amount})"
    
    def __repr__(self) -> str:
        return self.__str__()

@dataclass
class Node:
    address: str
    port: int
    last_seen: float

class GlobalCoyn:
    def __init__(self, host: str = "0.0.0.0", port: int = 9000, dev_mode: bool = False):
        self.host = host
        self.port = port
        self.blockchain = Blockchain()
        self.peers: Dict[str, Node] = {}
        self.mining_address: Optional[str] = None
        self.is_mining = False
        self.is_running = False
        self.dev_mode = dev_mode
        
        if not dev_mode:
            # Initialize network sockets only in production mode
            self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.p2p_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # For development, use only local connections to Node 2
            self.seed_nodes = [
                ("127.0.0.1", 9001),  # Node 2 running locally
                ("localhost", 9001)   # Another way to reference Node 2
            ]

    def start(self) -> None:
        """Start the GlobalCoyn node"""
        self.is_running = True
        self.start_time = time.time()  # Track node uptime
        
        # Load blockchain from disk if available
        self.blockchain.load_chain_from_disk()
        logging.info(f"Loaded blockchain with {len(self.blockchain.chain)} blocks")
        
        if not self.dev_mode:
            try:
                # Start P2P server only in production mode
                try:
                    self.p2p_socket.bind((self.host, self.port))
                    self.p2p_socket.listen(10)
                    print(f"P2P server listening on {self.host}:{self.port}")
                except OSError as bind_error:
                    if bind_error.errno == 48:  # Address already in use
                        print(f"P2P port {self.port} already in use, continuing with existing socket")
                    else:
                        raise
                
                # Start network threads
                threading.Thread(target=self._accept_connections, daemon=True).start()
                threading.Thread(target=self._maintain_connections, daemon=True).start()
                
                # Enable enhanced blockchain synchronization
                self.block_sync = enhance_globalcoyn_networking(self)
                logging.info("Enhanced blockchain synchronization enabled")
                
                # Connect to seed nodes
                self._connect_to_seed_nodes()
            except OSError as e:
                print(f"Network error (expected in dev mode): {e}")
                # Continue without network in dev mode

    def stop(self) -> None:
        """Stop the GlobalCoyn node"""
        self.is_running = False
        self.is_mining = False
        
        # Save blockchain state before shutting down
        self.blockchain.save_chain_to_disk()
        logging.info("Blockchain state saved")
        
        if not self.dev_mode:
            try:
                self.p2p_socket.close()
            except:
                pass

    def _accept_connections(self) -> None:
        """Accept incoming P2P connections"""
        while self.is_running:
            try:
                client_socket, address = self.p2p_socket.accept()
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except:
                if self.is_running:
                    time.sleep(1)

    def _handle_connection(self, client_socket: socket.socket, address: tuple) -> None:
        """Handle incoming P2P connection"""
        node_id = f"{address[0]}:{address[1]}"
        print(f"Handling connection from {node_id}")
        
        try:
            # Perform handshake
            if not self._perform_handshake(client_socket):
                print(f"Handshake failed with {node_id}, closing connection")
                client_socket.close()
                return
            
            print(f"Adding new peer: {node_id}")
            
            # Add to peers
            self.peers[node_id] = Node(
                address=address[0],
                port=address[1],
                last_seen=time.time()
            )
            
            # Send our blockchain height to trigger sync if needed
            height_message = {
                "type": "height",
                "height": len(self.blockchain.chain)
            }
            self._send_message(client_socket, height_message)
            
            # Handle messages in a loop
            print(f"Entering message handling loop for {node_id}")
            message_count = 0
            
            while self.is_running:
                try:
                    message = self._receive_message(client_socket)
                    if not message:
                        print(f"Connection closed by {node_id}")
                        break
                    
                    message_count += 1
                    print(f"Received message #{message_count} from {node_id}: {message.get('type')}")
                    self._handle_message(message, node_id)
                    
                except socket.timeout:
                    # Just a timeout, continue
                    continue
                except Exception as msg_error:
                    print(f"Error handling message from {node_id}: {str(msg_error)}")
                    break
            
        except Exception as e:
            print(f"Error in connection handler for {node_id}: {str(e)}")
        finally:
            print(f"Closing connection with {node_id}")
            client_socket.close()
            if node_id in self.peers:
                print(f"Removing peer {node_id}")
                del self.peers[node_id]

    def _handle_message(self, message: dict, node_id: str) -> None:
        """Handle incoming P2P message"""
        message_type = message.get("type")
        
        if message_type == "get_blocks":
            # Send our blockchain
            self._send_blockchain(node_id)
        
        elif message_type == "new_block":
            # Validate and add new block
            block_data = message.get("data")
            if block_data:
                self._handle_new_block(block_data)
        
        elif message_type == "new_transaction":
            # Add transaction to mempool
            tx_data = message.get("data")
            if tx_data:
                self._handle_new_transaction(tx_data)
        
        elif message_type == "get_block_range":
            # Handle request for a range of blocks
            start_height = message.get("start_height", 0)
            end_height = message.get("end_height", len(self.blockchain.chain))
            self._handle_block_range_request(node_id, start_height, end_height)

        elif message_type == "block_range":
            # Process received block range
            blocks_data = message.get("blocks", [])
            if blocks_data:
                self._process_block_range(blocks_data)

        elif message_type == "get_peers":
            # Share our peer list
            self._send_peer_list(node_id)
            
        elif message_type == "get_height":
            # Send our blockchain height
            self._send_blockchain_height(node_id)
            
        elif message_type == "peers":
            # Process received peer list
            self._handle_peer_list(message.get("peers", []), node_id)

    def _connect_to_seed_nodes(self) -> None:
        """Connect to seed nodes for initial network connection"""
        print(f"Attempting to connect to {len(self.seed_nodes)} seed nodes...")
        
        for seed_host, seed_port in self.seed_nodes:
            try:
                print(f"Connecting to seed node {seed_host}:{seed_port}...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)  # Add a timeout for the connection
                
                # Try to connect to the seed node
                try:
                    sock.connect((seed_host, seed_port))
                    print(f"Connected to seed node {seed_host}:{seed_port}")
                except ConnectionRefusedError:
                    print(f"Connection refused to {seed_host}:{seed_port}")
                    continue
                except socket.timeout:
                    print(f"Connection timeout to {seed_host}:{seed_port}")
                    continue
                except Exception as e:
                    print(f"Failed to connect to {seed_host}:{seed_port}: {str(e)}")
                    continue
                
                # Perform handshake
                if self._perform_handshake(sock):
                    print(f"Handshake successful with {seed_host}:{seed_port}")
                    node_id = f"{seed_host}:{seed_port}"
                    self.peers[node_id] = Node(
                        address=seed_host,
                        port=seed_port,
                        last_seen=time.time()
                    )
                    
                    # Start handler thread
                    threading.Thread(
                        target=self._handle_connection,
                        args=(sock, (seed_host, seed_port)),
                        daemon=True
                    ).start()
                    print(f"Started connection handler thread for {node_id}")
                else:
                    print(f"Handshake failed with {seed_host}:{seed_port}")
                    sock.close()
            except Exception as e:
                print(f"Error connecting to seed node {seed_host}:{seed_port}: {str(e)}")
                continue
                
        print(f"Connected to {len(self.peers)} seed nodes")

    def _maintain_connections(self) -> None:
        """Maintain network connections and remove stale peers"""
        while self.is_running:
            current_time = time.time()
            stale_peers = []
            
            # Check for stale connections
            for node_id, node in self.peers.items():
                if current_time - node.last_seen > 300:  # 5 minutes timeout
                    stale_peers.append(node_id)
            
            # Remove stale peers
            for node_id in stale_peers:
                del self.peers[node_id]
            
            # Try to maintain minimum peer connections
            if len(self.peers) < 8:
                self._connect_to_seed_nodes()
            
            time.sleep(60)

    def _sync_blockchain(self) -> None:
        """Synchronize blockchain with network"""
        print("Starting blockchain synchronization thread")
        
        sync_interval = 30  # Check for sync every 30 seconds initially
        
        while self.is_running:
            try:
                if not self.peers:
                    print("No peers connected, skipping blockchain sync")
                    time.sleep(sync_interval)
                    continue
                    
                # Check if our blockchain needs syncing
                our_height = len(self.blockchain.chain)
                
                print(f"Checking if we need to sync blockchain (current height: {our_height})")
                
                # Request heights from all peers to find the longest chain
                max_height = our_height
                max_height_peer = None
                peer_heights = {}
                
                for peer_id, peer in list(self.peers.items()):  # Use list() to avoid modification during iteration
                    try:
                        print(f"Requesting blockchain height from peer {peer_id}")
                        
                        # Get peer's blockchain height
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(10)  # 10 second timeout
                        
                        try:
                            sock.connect((peer.address, peer.port))
                        except ConnectionRefusedError:
                            print(f"Connection refused by peer {peer_id}")
                            if peer_id in self.peers:
                                del self.peers[peer_id]
                            continue
                        except Exception as conn_err:
                            print(f"Failed to connect to peer {peer_id}: {str(conn_err)}")
                            continue
                        
                        # Send get_height message
                        message = {"type": "get_height"}
                        if not self._send_message(sock, message):
                            print(f"Failed to send height request to peer {peer_id}")
                            sock.close()
                            continue
                        
                        # Receive response
                        response = self._receive_message(sock)
                        sock.close()
                        
                        if response and "height" in response:
                            peer_height = response["height"]
                            peer_heights[peer_id] = peer_height
                            print(f"Peer {peer_id} has {peer_height} blocks")
                            
                            if peer_height > max_height:
                                max_height = peer_height
                                max_height_peer = peer_id
                        else:
                            print(f"Invalid height response from peer {peer_id}: {response}")
                    except socket.timeout:
                        print(f"Timeout while requesting height from peer {peer_id}")
                        continue
                    except Exception as e:
                        print(f"Error requesting height from peer {peer_id}: {str(e)}")
                        continue
                
                print(f"Peer heights: {peer_heights}")
                print(f"Highest blockchain: {max_height} blocks from peer {max_height_peer}")
                
                # If we found a longer chain, sync with that peer
                if max_height_peer and max_height > our_height:
                    print(f"Found longer blockchain ({max_height} blocks) from peer {max_height_peer}. Syncing...")
                    success = self._request_blockchain(max_height_peer)
                    
                    if success:
                        print(f"Successfully synced blockchain to height {len(self.blockchain.chain)}")
                        
                        # After successful sync, broadcast our height to all peers
                        height_message = {
                            "type": "height",
                            "height": len(self.blockchain.chain)
                        }
                        self._broadcast_message(height_message)
                        
                        # Reduce sync interval as we're in sync
                        sync_interval = 60  # Check every minute when in sync
                    else:
                        print(f"Failed to sync blockchain from peer {max_height_peer}")
                        # Make sync more frequent after failure
                        sync_interval = 15  # Check more frequently after failure
                else:
                    print(f"Our blockchain is up to date (height: {our_height})")
                    # If we're in sync with the network, reduce sync frequency
                    sync_interval = 60  # Check every minute when in sync
                
            except Exception as e:
                print(f"Error in blockchain sync: {str(e)}")
                import traceback
                traceback.print_exc()
                
                # Reduced interval after error
                sync_interval = 15
                
            time.sleep(sync_interval)

    def start_mining(self, miner_address: str) -> None:
        """Start mining blocks"""
        if self.is_mining:
            return
        
        self.mining_address = miner_address
        self.is_mining = True
        
        threading.Thread(target=self._mining_loop, daemon=True).start()

    def stop_mining(self) -> None:
        """Stop mining blocks"""
        self.is_mining = False
        self.mining_address = None

    def _mining_loop(self) -> None:
        """Main mining loop"""
        while self.is_mining and self.is_running:
            # Mine a new block
            new_block = self.mine_block(self.mining_address)
            
            if new_block and not self.dev_mode:
                # Broadcast new block to network only in production mode
                self._broadcast_block(new_block)
    def _broadcast_block(self, block: Block) -> None:
        """Broadcast a new block to all peers"""
        print(f"Broadcasting block #{block.index} (hash: {block.hash}) to peers...")
        
        message = {
            "type": "new_block",
            "data": self._block_to_dict(block)
        }
        
        successful_broadcasts = 0
        for node_id, node in list(self.peers.items()):  # Use list() to avoid modification during iteration
            try:
                print(f"Sending block to peer {node_id}...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)  # 10 second timeout for block broadcast
                
                try:
                    sock.connect((node.address, node.port))
                except ConnectionRefusedError:
                    print(f"Connection refused by peer {node_id}")
                    continue
                except Exception as conn_err:
                    print(f"Failed to connect to peer {node_id}: {str(conn_err)}")
                    continue
                
                # Send the block message
                if self._send_message(sock, message):
                    print(f"Successfully sent block to peer {node_id}")
                    successful_broadcasts += 1
                else:
                    print(f"Failed to send block message to peer {node_id}")
                
                sock.close()
            except Exception as e:
                print(f"Error broadcasting block to peer {node_id}: {str(e)}")
                continue
        
        print(f"Block broadcast complete. Sent to {successful_broadcasts}/{len(self.peers)} peers")
    def start(self) -> None:
        """Start the GlobalCoyn node"""
        self.is_running = True
        self.start_time = time.time()  # Track node uptime
        
        # Load blockchain from disk if available
        self.blockchain.load_chain_from_disk()
        logging.info(f"Loaded blockchain with {len(self.blockchain.chain)} blocks")
        
        if not self.dev_mode:
            try:
                # Start P2P server only in production mode
                try:
                    self.p2p_socket.bind((self.host, self.port))
                    self.p2p_socket.listen(10)
                    print(f"P2P server listening on {self.host}:{self.port}")
                except OSError as bind_error:
                    if bind_error.errno == 48:  # Address already in use
                        print(f"P2P port {self.port} already in use, continuing with existing socket")
                    else:
                        raise
                
                # Start network threads
                threading.Thread(target=self._accept_connections, daemon=True).start()
                threading.Thread(target=self._maintain_connections, daemon=True).start()
                
                # Enable enhanced blockchain synchronization
                self.block_sync = enhance_globalcoyn_networking(self)
                logging.info("Enhanced blockchain synchronization enabled")
                
                # Connect to seed nodes
                self._connect_to_seed_nodes()
            except OSError as e:
                print(f"Network error (expected in dev mode): {e}")
                # Continue without network in dev mode

    def stop(self) -> None:
        """Stop the GlobalCoyn node"""
        self.is_running = False
        self.is_mining = False
        
        # Save blockchain state before shutting down
        self.blockchain.save_chain_to_disk()
        logging.info("Blockchain state saved")
        
        if not self.dev_mode:
            try:
                self.p2p_socket.close()
            except:
                pass

    def _accept_connections(self) -> None:
        """Accept incoming P2P connections"""
        while self.is_running:
            try:
                client_socket, address = self.p2p_socket.accept()
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except:
                if self.is_running:
                    time.sleep(1)

    def _handle_connection(self, client_socket: socket.socket, address: tuple) -> None:
        """Handle incoming P2P connection"""
        node_id = f"{address[0]}:{address[1]}"
        print(f"Handling connection from {node_id}")
        
        try:
            # Perform handshake
            if not self._perform_handshake(client_socket):
                print(f"Handshake failed with {node_id}, closing connection")
                client_socket.close()
                return
            
            print(f"Adding new peer: {node_id}")
            
            # Add to peers
            self.peers[node_id] = Node(
                address=address[0],
                port=address[1],
                last_seen=time.time()
            )
            
            # Send our blockchain height to trigger sync if needed
            height_message = {
                "type": "height",
                "height": len(self.blockchain.chain)
            }
            self._send_message(client_socket, height_message)
            
            # Handle messages in a loop
            print(f"Entering message handling loop for {node_id}")
            message_count = 0
            
            while self.is_running:
                try:
                    message = self._receive_message(client_socket)
                    if not message:
                        print(f"Connection closed by {node_id}")
                        break
                    
                    message_count += 1
                    print(f"Received message #{message_count} from {node_id}: {message.get('type')}")
                    self._handle_message(message, node_id)
                    
                except socket.timeout:
                    # Just a timeout, continue
                    continue
                except Exception as msg_error:
                    print(f"Error handling message from {node_id}: {str(msg_error)}")
                    break
            
        except Exception as e:
            print(f"Error in connection handler for {node_id}: {str(e)}")
        finally:
            print(f"Closing connection with {node_id}")
            client_socket.close()
            if node_id in self.peers:
                print(f"Removing peer {node_id}")
                del self.peers[node_id]

    def _handle_message(self, message: dict, node_id: str) -> None:
        """Handle incoming P2P message"""
        message_type = message.get("type")
        
        if message_type == "get_blocks":
            # Send our blockchain
            self._send_blockchain(node_id)
        
        elif message_type == "new_block":
            # Validate and add new block
            block_data = message.get("data")
            if block_data:
                self._handle_new_block(block_data)
    def _handle_new_block(self, block_data: dict) -> bool:
        """Handle a new block from another node"""
        try:
            # Print block info for debugging
            print(f"Received new block: index={block_data.get('index')}, hash={block_data.get('hash')}")
            
            # Convert dict to Block object
            new_block = self._dict_to_block(block_data)
            
            # Validate block hash
            calculated_hash = new_block.calculate_hash()
            if new_block.hash != calculated_hash:
                print(f"Block hash validation failed: received={new_block.hash}, calculated={calculated_hash}")
                return False
            
            # Check if we already have this block by hash
            for existing_block in self.blockchain.chain:
                if existing_block.hash == new_block.hash:
                    print(f"Block already in our chain (#{new_block.index}), ignoring")
                    return True
            
            # Check block index
            current_last_block = self.blockchain.chain[-1] if self.blockchain.chain else None
            if not current_last_block:
                print(f"No blocks in our chain yet, cannot add block #{new_block.index}")
                return False
                
            # If this is the next block in sequence, validate the previous hash
            if new_block.index == current_last_block.index + 1:
                if new_block.previous_hash != current_last_block.hash:
                    print(f"Block #{new_block.index} previous_hash doesn't match our last block hash")
                    print(f"Our last block: hash={current_last_block.hash}")
                    print(f"New block prev_hash: {new_block.previous_hash}")
                    return False
                    
                # This block is valid and next in sequence
                print(f"Adding valid block #{new_block.index} to our chain")
                self.blockchain.add_block(new_block)  # Use add_block method which saves chain to disk
                
                # Remove transactions in this block from our mempool
                mempool_before = len(self.blockchain.mempool)
                for tx in new_block.transactions:
                    # Find matching transactions in mempool by key attributes
                    for mempool_tx in list(self.blockchain.mempool):
                        if (mempool_tx.sender == tx.sender and 
                            mempool_tx.recipient == tx.recipient and
                            abs(mempool_tx.amount - tx.amount) < 0.0001 and
                            mempool_tx.transaction_type == tx.transaction_type):
                            self.blockchain.mempool.remove(mempool_tx)
                            break
                
                mempool_after = len(self.blockchain.mempool)
                print(f"Removed {mempool_before - mempool_after} transactions from mempool")
                print(f"Successfully added new block #{new_block.index} to chain")
                
                # If we're mining, adjust difficulty based on new chain
                if self.is_mining:
                    self.blockchain.adjust_difficulty()
                
                return True
            
            # If the block is ahead of our chain, we might need to sync the missing blocks
            if new_block.index > current_last_block.index + 1:
                print(f"Received block #{new_block.index} but our last block is #{current_last_block.index}")
                print(f"Need to synchronize missing blocks")
                
                # Block sync will handle this automatically with the enhanced networking
                return False
                
            # If the block is behind our chain, ignore it (we're ahead)
            if new_block.index <= current_last_block.index:
                print(f"Received block #{new_block.index} but we already have {current_last_block.index + 1} blocks")
                return False
                
        except Exception as e:
            print(f"Error handling new block from network: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    def add(self, amount: float) -> None:
        """Add amount to coin"""
        self.amount = round(self.amount + float(amount), 8)
        self._validate_amount()
    
    def subtract(self, amount: float) -> None:
        """Subtract amount from coin"""
        self.amount = round(self.amount - float(amount), 8)
        self._validate_amount()
    
    def to_dict(self) -> Dict:
        """Convert coin to dictionary for serialization"""
        return {
            "amount": format(self.amount, '.8f'),
            "owner": self.owner
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Coin':
        """Create coin from dictionary"""
        return cls(float(data["amount"]), data.get("owner"))
    
    def __str__(self) -> str:
        return f"GCN({self.amount})"
    
    def __repr__(self) -> str:
        return self.__str__()

@dataclass
class Node:
    address: str
    port: int
    last_seen: float

class GlobalCoyn:
    def __init__(self, host: str = "0.0.0.0", port: int = 9000, dev_mode: bool = False):
        self.host = host
        self.port = port
        self.blockchain = Blockchain()
        self.peers: Dict[str, Node] = {}
        self.mining_address: Optional[str] = None
        self.is_mining = False
        self.is_running = False
        self.dev_mode = dev_mode
        
        if not dev_mode:
            # Initialize network sockets only in production mode
            self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.p2p_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # For development, use only local connections to Node 2
            self.seed_nodes = [
                ("127.0.0.1", 9001),  # Node 2 running locally
                ("localhost", 9001)   # Another way to reference Node 2
            ]

    def start(self) -> None:
        """Start the GlobalCoyn node"""
        self.is_running = True
        self.start_time = time.time()  # Track node uptime
        
        # Load blockchain from disk if available
        self.blockchain.load_chain_from_disk()
        logging.info(f"Loaded blockchain with {len(self.blockchain.chain)} blocks")
        
        if not self.dev_mode:
            try:
                # Start P2P server only in production mode
                try:
                    self.p2p_socket.bind((self.host, self.port))
                    self.p2p_socket.listen(10)
                    print(f"P2P server listening on {self.host}:{self.port}")
                except OSError as bind_error:
                    if bind_error.errno == 48:  # Address already in use
                        print(f"P2P port {self.port} already in use, continuing with existing socket")
                    else:
                        raise
                
                # Start network threads
                threading.Thread(target=self._accept_connections, daemon=True).start()
                threading.Thread(target=self._maintain_connections, daemon=True).start()
                
                # Enable enhanced blockchain synchronization
                self.block_sync = enhance_globalcoyn_networking(self)
                logging.info("Enhanced blockchain synchronization enabled")
                
                # Connect to seed nodes
                self._connect_to_seed_nodes()
            except OSError as e:
                print(f"Network error (expected in dev mode): {e}")
                # Continue without network in dev mode

    def stop(self) -> None:
        """Stop the GlobalCoyn node"""
        self.is_running = False
        self.is_mining = False
        
        # Save blockchain state before shutting down
        self.blockchain.save_chain_to_disk()
        logging.info("Blockchain state saved")
        
        if not self.dev_mode:
            try:
                self.p2p_socket.close()
            except:
                pass

    def _accept_connections(self) -> None:
        """Accept incoming P2P connections"""
        while self.is_running:
            try:
                client_socket, address = self.p2p_socket.accept()
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except:
                if self.is_running:
                    time.sleep(1)

    def _handle_connection(self, client_socket: socket.socket, address: tuple) -> None:
        """Handle incoming P2P connection"""
        node_id = f"{address[0]}:{address[1]}"
        print(f"Handling connection from {node_id}")
        
        try:
            # Perform handshake
            if not self._perform_handshake(client_socket):
                print(f"Handshake failed with {node_id}, closing connection")
                client_socket.close()
                return
            
            print(f"Adding new peer: {node_id}")
            
            # Add to peers
            self.peers[node_id] = Node(
                address=address[0],
                port=address[1],
                last_seen=time.time()
            )
            
            # Send our blockchain height to trigger sync if needed
            height_message = {
                "type": "height",
                "height": len(self.blockchain.chain)
            }
            self._send_message(client_socket, height_message)
            
            # Handle messages in a loop
            print(f"Entering message handling loop for {node_id}")
            message_count = 0
            
            while self.is_running:
                try:
                    message = self._receive_message(client_socket)
                    if not message:
                        print(f"Connection closed by {node_id}")
                        break
                    
                    message_count += 1
                    print(f"Received message #{message_count} from {node_id}: {message.get('type')}")
                    self._handle_message(message, node_id)
                    
                except socket.timeout:
                    # Just a timeout, continue
                    continue
                except Exception as msg_error:
                    print(f"Error handling message from {node_id}: {str(msg_error)}")
                    break
            
        except Exception as e:
            print(f"Error in connection handler for {node_id}: {str(e)}")
        finally:
            print(f"Closing connection with {node_id}")
            client_socket.close()
            if node_id in self.peers:
                print(f"Removing peer {node_id}")
                del self.peers[node_id]

    def _handle_message(self, message: dict, node_id: str) -> None:
        """Handle incoming P2P message"""
        message_type = message.get("type")
        
        if message_type == "get_blocks":
            # Send our blockchain
            self._send_blockchain(node_id)
        
        elif message_type == "new_block":
            # Validate and add new block
            block_data = message.get("data")
            if block_data:
                self._handle_new_block(block_data)
        
        elif message_type == "new_transaction":
            # Add transaction to mempool
            tx_data = message.get("data")
            if tx_data:
                self._handle_new_transaction(tx_data)
        
        elif message_type == "get_block_range":
            # Handle request for a range of blocks
            start_height = message.get("start_height", 0)
            end_height = message.get("end_height", len(self.blockchain.chain))
            self._handle_block_range_request(node_id, start_height, end_height)

        elif message_type == "block_range":
            # Process received block range
            blocks_data = message.get("blocks", [])
            if blocks_data:
                self._process_block_range(blocks_data)

        elif message_type == "get_peers":
            # Share our peer list
            self._send_peer_list(node_id)
            
        elif message_type == "get_height":
            # Send our blockchain height
            self._send_blockchain_height(node_id)
            
        elif message_type == "peers":
            # Process received peer list
            self._handle_peer_list(message.get("peers", []), node_id)

    def _connect_to_seed_nodes(self) -> None:
        """Connect to seed nodes for initial network connection"""
        print(f"Attempting to connect to {len(self.seed_nodes)} seed nodes...")
        
        for seed_host, seed_port in self.seed_nodes:
            try:
                print(f"Connecting to seed node {seed_host}:{seed_port}...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)  # Add a timeout for the connection
                
                # Try to connect to the seed node
                try:
                    sock.connect((seed_host, seed_port))
                    print(f"Connected to seed node {seed_host}:{seed_port}")
                except ConnectionRefusedError:
                    print(f"Connection refused to {seed_host}:{seed_port}")
                    continue
                except socket.timeout:
                    print(f"Connection timeout to {seed_host}:{seed_port}")
                    continue
                except Exception as e:
                    print(f"Failed to connect to {seed_host}:{seed_port}: {str(e)}")
                    continue
                
                # Perform handshake
                if self._perform_handshake(sock):
                    print(f"Handshake successful with {seed_host}:{seed_port}")
                    node_id = f"{seed_host}:{seed_port}"
                    self.peers[node_id] = Node(
                        address=seed_host,
                        port=seed_port,
                        last_seen=time.time()
                    )
                    
                    # Start handler thread
                    threading.Thread(
                        target=self._handle_connection,
                        args=(sock, (seed_host, seed_port)),
                        daemon=True
                    ).start()
                    print(f"Started connection handler thread for {node_id}")
                else:
                    print(f"Handshake failed with {seed_host}:{seed_port}")
                    sock.close()
            except Exception as e:
                print(f"Error connecting to seed node {seed_host}:{seed_port}: {str(e)}")
                continue
                
        print(f"Connected to {len(self.peers)} seed nodes")

    def _maintain_connections(self) -> None:
        """Maintain network connections and remove stale peers"""
        while self.is_running:
            current_time = time.time()
            stale_peers = []
            
            # Check for stale connections
            for node_id, node in self.peers.items():
                if current_time - node.last_seen > 300:  # 5 minutes timeout
                    stale_peers.append(node_id)
            
            # Remove stale peers
            for node_id in stale_peers:
                del self.peers[node_id]
            
            # Try to maintain minimum peer connections
            if len(self.peers) < 8:
                self._connect_to_seed_nodes()
            
            time.sleep(60)

    def _sync_blockchain(self) -> None:
        """Synchronize blockchain with network"""
        print("Starting blockchain synchronization thread")
        
        sync_interval = 30  # Check for sync every 30 seconds initially
        
        while self.is_running:
            try:
                if not self.peers:
                    print("No peers connected, skipping blockchain sync")
                    time.sleep(sync_interval)
                    continue
                    
                # Check if our blockchain needs syncing
                our_height = len(self.blockchain.chain)
                
                print(f"Checking if we need to sync blockchain (current height: {our_height})")
                
                # Request heights from all peers to find the longest chain
                max_height = our_height
                max_height_peer = None
                peer_heights = {}
                
                for peer_id, peer in list(self.peers.items()):  # Use list() to avoid modification during iteration
                    try:
                        print(f"Requesting blockchain height from peer {peer_id}")
                        
                        # Get peer's blockchain height
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(10)  # 10 second timeout
                        
                        try:
                            sock.connect((peer.address, peer.port))
                        except ConnectionRefusedError:
                            print(f"Connection refused by peer {peer_id}")
                            if peer_id in self.peers:
                                del self.peers[peer_id]
                            continue
                        except Exception as conn_err:
                            print(f"Failed to connect to peer {peer_id}: {str(conn_err)}")
                            continue
                        
                        # Send get_height message
                        message = {"type": "get_height"}
                        if not self._send_message(sock, message):
                            print(f"Failed to send height request to peer {peer_id}")
                            sock.close()
                            continue
                        
                        # Receive response
                        response = self._receive_message(sock)
                        sock.close()
                        
                        if response and "height" in response:
                            peer_height = response["height"]
                            peer_heights[peer_id] = peer_height
                            print(f"Peer {peer_id} has {peer_height} blocks")
                            
                            if peer_height > max_height:
                                max_height = peer_height
                                max_height_peer = peer_id
                        else:
                            print(f"Invalid height response from peer {peer_id}: {response}")
                    except socket.timeout:
                        print(f"Timeout while requesting height from peer {peer_id}")
                        continue
                    except Exception as e:
                        print(f"Error requesting height from peer {peer_id}: {str(e)}")
                        continue
                
                print(f"Peer heights: {peer_heights}")
                print(f"Highest blockchain: {max_height} blocks from peer {max_height_peer}")
                
                # If we found a longer chain, sync with that peer
                if max_height_peer and max_height > our_height:
                    print(f"Found longer blockchain ({max_height} blocks) from peer {max_height_peer}. Syncing...")
                    success = self._request_blockchain(max_height_peer)
                    
                    if success:
                        print(f"Successfully synced blockchain to height {len(self.blockchain.chain)}")
                        
                        # After successful sync, broadcast our height to all peers
                        height_message = {
                            "type": "height",
                            "height": len(self.blockchain.chain)
                        }
                        self._broadcast_message(height_message)
                        
                        # Reduce sync interval as we're in sync
                        sync_interval = 60  # Check every minute when in sync
                    else:
                        print(f"Failed to sync blockchain from peer {max_height_peer}")
                        # Make sync more frequent after failure
                        sync_interval = 15  # Check more frequently after failure
                else:
                    print(f"Our blockchain is up to date (height: {our_height})")
                    # If we're in sync with the network, reduce sync frequency
                    sync_interval = 60  # Check every minute when in sync
                
            except Exception as e:
                print(f"Error in blockchain sync: {str(e)}")
                import traceback
                traceback.print_exc()
                
                # Reduced interval after error
                sync_interval = 15
                
            time.sleep(sync_interval)

    def start_mining(self, miner_address: str) -> None:
        """Start mining blocks"""
        if self.is_mining:
            return
        
        self.mining_address = miner_address
        self.is_mining = True
        
        threading.Thread(target=self._mining_loop, daemon=True).start()

    def stop_mining(self) -> None:
        """Stop mining blocks"""
        self.is_mining = False
        self.mining_address = None

    def _mining_loop(self) -> None:
        """Main mining loop"""
        while self.is_mining and self.is_running:
            # Mine a new block
            new_block = self.mine_block(self.mining_address)
            
            if new_block and not self.dev_mode:
                # Broadcast new block to network only in production mode
                self._broadcast_block(new_block)
    def _broadcast_block(self, block: Block) -> None:
        """Broadcast a new block to all peers"""
        print(f"Broadcasting block #{block.index} (hash: {block.hash}) to peers...")
        
        message = {
            "type": "new_block",
            "data": self._block_to_dict(block)
        }
        
        successful_broadcasts = 0
        for node_id, node in list(self.peers.items()):  # Use list() to avoid modification during iteration
            try:
                print(f"Sending block to peer {node_id}...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)  # 10 second timeout for block broadcast
                
                try:
                    sock.connect((node.address, node.port))
                except ConnectionRefusedError:
                    print(f"Connection refused by peer {node_id}")
                    continue
                except Exception as conn_err:
                    print(f"Failed to connect to peer {node_id}: {str(conn_err)}")
                    continue
                
                # Send the block message
                if self._send_message(sock, message):
                    print(f"Successfully sent block to peer {node_id}")
                    successful_broadcasts += 1
                else:
                    print(f"Failed to send block message to peer {node_id}")
                
                sock.close()
            except Exception as e:
                print(f"Error broadcasting block to peer {node_id}: {str(e)}")
                continue
        
        print(f"Block broadcast complete. Sent to {successful_broadcasts}/{len(self.peers)} peers")
    def from_dict(cls, data: Dict) -> 'Coin':
        """Create coin from dictionary"""
        return cls(float(data["amount"]), data.get("owner"))
    
    def __str__(self) -> str:
        return f"GCN({self.amount})"
    
    def __repr__(self) -> str:
        return self.__str__()

@dataclass
class Node:
    address: str
    port: int
    last_seen: float

class GlobalCoyn:
    def __init__(self, host: str = "0.0.0.0", port: int = 9000, dev_mode: bool = False):
        self.host = host
        self.port = port
        self.blockchain = Blockchain()
        self.peers: Dict[str, Node] = {}
        self.mining_address: Optional[str] = None
        self.is_mining = False
        self.is_running = False
        self.dev_mode = dev_mode
        
        if not dev_mode:
            # Initialize network sockets only in production mode
            self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.p2p_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # For development, use only local connections to Node 2
            self.seed_nodes = [
                ("127.0.0.1", 9001),  # Node 2 running locally
                ("localhost", 9001)   # Another way to reference Node 2
            ]

    def start(self) -> None:
        """Start the GlobalCoyn node"""
        self.is_running = True
        self.start_time = time.time()  # Track node uptime
        
        # Load blockchain from disk if available
        self.blockchain.load_chain_from_disk()
        logging.info(f"Loaded blockchain with {len(self.blockchain.chain)} blocks")
        
        if not self.dev_mode:
            try:
                # Start P2P server only in production mode
                try:
                    self.p2p_socket.bind((self.host, self.port))
                    self.p2p_socket.listen(10)
                    print(f"P2P server listening on {self.host}:{self.port}")
                except OSError as bind_error:
                    if bind_error.errno == 48:  # Address already in use
                        print(f"P2P port {self.port} already in use, continuing with existing socket")
                    else:
                        raise
                
                # Start network threads
                threading.Thread(target=self._accept_connections, daemon=True).start()
                threading.Thread(target=self._maintain_connections, daemon=True).start()
                
                # Enable enhanced blockchain synchronization
                self.block_sync = enhance_globalcoyn_networking(self)
                logging.info("Enhanced blockchain synchronization enabled")
                
                # Connect to seed nodes
                self._connect_to_seed_nodes()
            except OSError as e:
                print(f"Network error (expected in dev mode): {e}")
                # Continue without network in dev mode

    def stop(self) -> None:
        """Stop the GlobalCoyn node"""
        self.is_running = False
        self.is_mining = False
        
        # Save blockchain state before shutting down
        self.blockchain.save_chain_to_disk()
        logging.info("Blockchain state saved")
        
        if not self.dev_mode:
            try:
                self.p2p_socket.close()
            except:
                pass

    def _accept_connections(self) -> None:
        """Accept incoming P2P connections"""
        while self.is_running:
            try:
                client_socket, address = self.p2p_socket.accept()
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except:
                if self.is_running:
                    time.sleep(1)

    def _handle_connection(self, client_socket: socket.socket, address: tuple) -> None:
        """Handle incoming P2P connection"""
        node_id = f"{address[0]}:{address[1]}"
        print(f"Handling connection from {node_id}")
        
        try:
            # Perform handshake
            if not self._perform_handshake(client_socket):
                print(f"Handshake failed with {node_id}, closing connection")
                client_socket.close()
                return
            
            print(f"Adding new peer: {node_id}")
            
            # Add to peers
            self.peers[node_id] = Node(
                address=address[0],
                port=address[1],
                last_seen=time.time()
            )
            
            # Send our blockchain height to trigger sync if needed
            height_message = {
                "type": "height",
                "height": len(self.blockchain.chain)
            }
            self._send_message(client_socket, height_message)
            
            # Handle messages in a loop
            print(f"Entering message handling loop for {node_id}")
            message_count = 0
            
            while self.is_running:
                try:
                    message = self._receive_message(client_socket)
                    if not message:
                        print(f"Connection closed by {node_id}")
                        break
                    
                    message_count += 1
                    print(f"Received message #{message_count} from {node_id}: {message.get('type')}")
                    self._handle_message(message, node_id)
                    
                except socket.timeout:
                    # Just a timeout, continue
                    continue
                except Exception as msg_error:
                    print(f"Error handling message from {node_id}: {str(msg_error)}")
                    break
            
        except Exception as e:
            print(f"Error in connection handler for {node_id}: {str(e)}")
        finally:
            print(f"Closing connection with {node_id}")
            client_socket.close()
            if node_id in self.peers:
                print(f"Removing peer {node_id}")
                del self.peers[node_id]

    def _handle_message(self, message: dict, node_id: str) -> None:
        """Handle incoming P2P message"""
        message_type = message.get("type")
        
        if message_type == "get_blocks":
            # Send our blockchain
            self._send_blockchain(node_id)
        
        elif message_type == "new_block":
            # Validate and add new block
            block_data = message.get("data")
            if block_data:
                self._handle_new_block(block_data)
        
        elif message_type == "new_transaction":
            # Add transaction to mempool
            tx_data = message.get("data")
            if tx_data:
                self._handle_new_transaction(tx_data)
        
        elif message_type == "get_block_range":
            # Handle request for a range of blocks
            start_height = message.get("start_height", 0)
            end_height = message.get("end_height", len(self.blockchain.chain))
            self._handle_block_range_request(node_id, start_height, end_height)

        elif message_type == "block_range":
            # Process received block range
            blocks_data = message.get("blocks", [])
            if blocks_data:
                self._process_block_range(blocks_data)

        elif message_type == "get_peers":
            # Share our peer list
            self._send_peer_list(node_id)
            
        elif message_type == "get_height":
            # Send our blockchain height
            self._send_blockchain_height(node_id)
            
        elif message_type == "peers":
            # Process received peer list
            self._handle_peer_list(message.get("peers", []), node_id)

    def _connect_to_seed_nodes(self) -> None:
        """Connect to seed nodes for initial network connection"""
        print(f"Attempting to connect to {len(self.seed_nodes)} seed nodes...")
        
        for seed_host, seed_port in self.seed_nodes:
            try:
                print(f"Connecting to seed node {seed_host}:{seed_port}...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)  # Add a timeout for the connection
                
                # Try to connect to the seed node
                try:
                    sock.connect((seed_host, seed_port))
                    print(f"Connected to seed node {seed_host}:{seed_port}")
                except ConnectionRefusedError:
                    print(f"Connection refused to {seed_host}:{seed_port}")
                    continue
                except socket.timeout:
                    print(f"Connection timeout to {seed_host}:{seed_port}")
                    continue
                except Exception as e:
                    print(f"Failed to connect to {seed_host}:{seed_port}: {str(e)}")
                    continue
                
                # Perform handshake
                if self._perform_handshake(sock):
                    print(f"Handshake successful with {seed_host}:{seed_port}")
                    node_id = f"{seed_host}:{seed_port}"
                    self.peers[node_id] = Node(
                        address=seed_host,
                        port=seed_port,
                        last_seen=time.time()
                    )
                    
                    # Start handler thread
                    threading.Thread(
                        target=self._handle_connection,
                        args=(sock, (seed_host, seed_port)),
                        daemon=True
                    ).start()
                    print(f"Started connection handler thread for {node_id}")
                else:
                    print(f"Handshake failed with {seed_host}:{seed_port}")
                    sock.close()
            except Exception as e:
                print(f"Error connecting to seed node {seed_host}:{seed_port}: {str(e)}")
                continue
                
        print(f"Connected to {len(self.peers)} seed nodes")

    def _maintain_connections(self) -> None:
        """Maintain network connections and remove stale peers"""
        while self.is_running:
            current_time = time.time()
            stale_peers = []
            
            # Check for stale connections
            for node_id, node in self.peers.items():
                if current_time - node.last_seen > 300:  # 5 minutes timeout
                    stale_peers.append(node_id)
            
            # Remove stale peers
            for node_id in stale_peers:
                del self.peers[node_id]
            
            # Try to maintain minimum peer connections
            if len(self.peers) < 8:
                self._connect_to_seed_nodes()
            
            time.sleep(60)

    def _sync_blockchain(self) -> None:
        """Synchronize blockchain with network"""
        print("Starting blockchain synchronization thread")
        
        sync_interval = 30  # Check for sync every 30 seconds initially
        
        while self.is_running:
            try:
                if not self.peers:
                    print("No peers connected, skipping blockchain sync")
                    time.sleep(sync_interval)
                    continue
                    
                # Check if our blockchain needs syncing
                our_height = len(self.blockchain.chain)
                
                print(f"Checking if we need to sync blockchain (current height: {our_height})")
                
                # Request heights from all peers to find the longest chain
                max_height = our_height
                max_height_peer = None
                peer_heights = {}
                
                for peer_id, peer in list(self.peers.items()):  # Use list() to avoid modification during iteration
                    try:
                        print(f"Requesting blockchain height from peer {peer_id}")
                        
                        # Get peer's blockchain height
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(10)  # 10 second timeout
                        
                        try:
                            sock.connect((peer.address, peer.port))
                        except ConnectionRefusedError:
                            print(f"Connection refused by peer {peer_id}")
                            if peer_id in self.peers:
                                del self.peers[peer_id]
                            continue
                        except Exception as conn_err:
                            print(f"Failed to connect to peer {peer_id}: {str(conn_err)}")
                            continue
                        
                        # Send get_height message
                        message = {"type": "get_height"}
                        if not self._send_message(sock, message):
                            print(f"Failed to send height request to peer {peer_id}")
                            sock.close()
                            continue
                        
                        # Receive response
                        response = self._receive_message(sock)
                        sock.close()
                        
                        if response and "height" in response:
                            peer_height = response["height"]
                            peer_heights[peer_id] = peer_height
                            print(f"Peer {peer_id} has {peer_height} blocks")
                            
                            if peer_height > max_height:
                                max_height = peer_height
                                max_height_peer = peer_id
                        else:
                            print(f"Invalid height response from peer {peer_id}: {response}")
                    except socket.timeout:
                        print(f"Timeout while requesting height from peer {peer_id}")
                        continue
                    except Exception as e:
                        print(f"Error requesting height from peer {peer_id}: {str(e)}")
                        continue
                
                print(f"Peer heights: {peer_heights}")
                print(f"Highest blockchain: {max_height} blocks from peer {max_height_peer}")
                
                # If we found a longer chain, sync with that peer
                if max_height_peer and max_height > our_height:
                    print(f"Found longer blockchain ({max_height} blocks) from peer {max_height_peer}. Syncing...")
                    success = self._request_blockchain(max_height_peer)
                    
                    if success:
                        print(f"Successfully synced blockchain to height {len(self.blockchain.chain)}")
                        
                        # After successful sync, broadcast our height to all peers
                        height_message = {
                            "type": "height",
                            "height": len(self.blockchain.chain)
                        }
                        self._broadcast_message(height_message)
                        
                        # Reduce sync interval as we're in sync
                        sync_interval = 60  # Check every minute when in sync
                    else:
                        print(f"Failed to sync blockchain from peer {max_height_peer}")
                        # Make sync more frequent after failure
                        sync_interval = 15  # Check more frequently after failure
                else:
                    print(f"Our blockchain is up to date (height: {our_height})")
                    # If we're in sync with the network, reduce sync frequency
                    sync_interval = 60  # Check every minute when in sync
                
            except Exception as e:
                print(f"Error in blockchain sync: {str(e)}")
                import traceback
                traceback.print_exc()
                
                # Reduced interval after error
                sync_interval = 15
                
            time.sleep(sync_interval)

    def start_mining(self, miner_address: str) -> None:
        """Start mining blocks"""
        if self.is_mining:
            return
        
        self.mining_address = miner_address
        self.is_mining = True
        
        threading.Thread(target=self._mining_loop, daemon=True).start()

    def stop_mining(self) -> None:
        """Stop mining blocks"""
        self.is_mining = False
        self.mining_address = None

    def _mining_loop(self) -> None:
        """Main mining loop"""
        while self.is_mining and self.is_running:
            # Mine a new block
            new_block = self.mine_block(self.mining_address)
            
            if new_block and not self.dev_mode:
                # Broadcast new block to network only in production mode
                self._broadcast_block(new_block)
            
            time.sleep(1)

    def mine_block(self, miner_address: str) -> Optional[Block]:
        """Mine a new block and add it to the blockchain"""
        try:
            # Use blockchain's mine_block method
            new_block = self.blockchain.mine_block(miner_address)
            
            if new_block and not self.dev_mode:
                # Broadcast new block in production mode
                self._broadcast_block(new_block)
            
            return new_block
        except Exception as e:
            print(f"Mining error: {str(e)}")
            return None

    def add_transaction_to_mempool(self, transaction: Transaction) -> bool:
        """Add a transaction to the blockchain mempool"""
        return self.blockchain.add_transaction_to_mempool(transaction)
        
    def create_transfer(self, sender: str, recipient: str, amount: float) -> bool:
        """
        Create a direct transfer transaction between two addresses
        
        This is a helper method to simplify transfers with proper validation and mining
        
        Args:
            sender: The sender's wallet address
            recipient: The recipient's wallet address
            amount: Amount of COON to transfer
            
        Returns:
            bool: True if transfer was successfully added to blockchain, False otherwise
        """
        try:
            # Basic validation
            if amount <= 0:
                print(f"Invalid transfer amount: {amount}")
                return False
                
            # Create transfer transaction
            transaction = Transaction(
                sender=sender,
                recipient=recipient,
                amount=amount,
                fee=0,  # No fee for internal transfers
                transaction_type="TRANSFER"
            )
            
            # Add to mempool
            if not self.blockchain.add_transaction_to_mempool(transaction):
                print(f"Failed to add transfer transaction to mempool")
                return False
                
            # Mine the transaction
            new_block = self.mine_block(sender)
            if not new_block:
                print(f"Warning: Failed to mine transfer transaction, but it's in mempool")
                # Continue anyway - frontend will handle balance updates
                
            print(f"Transfer processed successfully: {sender} -> {recipient}, amount: {amount}")
            return True
            
        except Exception as e:
            print(f"Transfer creation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def get_balance(self, address: str) -> float:
        """
        Get balance for an address including pending transactions
        
        This uses the blockchain as the single source of truth for all balances.
        The method includes both confirmed transactions from blocks and pending
        transactions from the mempool.
        
        Args:
            address: The wallet address to check
            
        Returns:
            float: The current balance for the address
        """
        print(f"🔍 Getting balance for {address} from blockchain")
        
        # Get confirmed balance from blockchain (source of truth)
        blockchain_balance = self.blockchain.get_balance(address)
        
        # Add effect of pending transactions from mempool for a complete picture
        pending_balance_effect = 0
        mempool_transactions_found = 0
        
        for tx in self.blockchain.mempool:
            # Track any transactions that might affect this address's balance
            if tx.recipient == address or tx.sender == address:
                mempool_transactions_found += 1
            
            # Credit when address receives coins
            if tx.recipient == address:
                pending_balance_effect += tx.amount
                
            # Debit when address sends coins
            if tx.sender == address:
                pending_balance_effect -= (tx.amount + tx.fee)
        
        # Only log if we found pending transactions for this address
        if mempool_transactions_found > 0:
            print(f"Found {mempool_transactions_found} pending transactions for {address}")
            print(f"Pending balance effect: {pending_balance_effect}")
            print(f"Balance before pending: {blockchain_balance}, after: {blockchain_balance + pending_balance_effect}")
            
        # Return total balance (blockchain + pending)
        return blockchain_balance + pending_balance_effect

    def create_transaction(self, wallet: Wallet, sender: str, recipient: str, 
                         amount: float, fee: float) -> bool:
        """Create and broadcast a new transaction"""
        # Create and sign transaction
        transaction = wallet.sign_transaction(sender, recipient, amount, fee)
        if not transaction:
            return False
        
        # Add to mempool and broadcast
        if self.blockchain.add_transaction_to_mempool(transaction):
            self._broadcast_transaction(transaction)
            return True
        
        return False

    def _broadcast_block(self, block: Block) -> None:
        """Broadcast a new block to all peers"""
        message = {
            "type": "new_block",
            "data": self._block_to_dict(block)
        }
        
        self._broadcast_message(message)

    def _broadcast_transaction(self, transaction: Transaction) -> None:
        """Broadcast a new transaction to all peers"""
        message = {
            "type": "new_transaction",
            "data": transaction.to_dict()
        }
        
        self._broadcast_message(message)

    def _broadcast_message(self, message: dict) -> None:
        """Broadcast a message to all peers"""
        for node_id, node in self.peers.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((node.address, node.port))
                self._send_message(sock, message)
                sock.close()
            except:
                continue

    def _block_to_dict(self, block: Block) -> dict:
        """Convert a Block object to dictionary for network transmission"""
        return {
            "index": block.index,
            "previous_hash": block.previous_hash,
            "timestamp": block.timestamp,
            "transactions": [tx.to_dict() for tx in block.transactions],
            "nonce": block.nonce,
            "difficulty_target": block.difficulty_target,
            "merkle_root": block.merkle_root,
            "hash": block.hash
        }

    def _perform_handshake(self, sock: socket.socket) -> bool:
        """Perform simplified handshake for development"""
        try:
            # Use a simplified handshake for development - no need for complex verification
            # This simplifies the process and avoids timeouts during testing
            print("Using simplified handshake for development environment")
            
            # Add the peer directly and return success
            # For development/testing purposes only
            
            # Reset socket timeout for normal operation
            sock.settimeout(None)
            
            print("Development handshake successful")
            return True
            
        except Exception as e:
            print(f"Handshake error: {str(e)}")
            return False

    def _send_message(self, sock: socket.socket, message: dict) -> bool:
        """Send a message over the network"""
        try:
            # Add timestamp to message
            if "timestamp" not in message:
                message["timestamp"] = time.time()
                
            # Convert message to JSON and encode
            data = json.dumps(message).encode()
            length = len(data).to_bytes(4, byteorder='big')
            
            # Send length and data
            sock.sendall(length + data)
            return True
        except socket.error as e:
            print(f"Socket error when sending message: {str(e)}")
            return False
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            return False

    def _receive_message(self, sock: socket.socket) -> Optional[dict]:
        """Receive a message from the network"""
        try:
            # Set a timeout for receiving
            sock.settimeout(10)
            
            # Read message length
            length_bytes = sock.recv(4)
            if not length_bytes or len(length_bytes) < 4:
                print(f"Received incomplete length header: {length_bytes}")
                return None
            
            length = int.from_bytes(length_bytes, byteorder='big')
            
            # Sanity check the length
            if length <= 0 or length > 10_000_000:  # 10MB max message size
                print(f"Invalid message length: {length} bytes")
                return None
                
            print(f"Receiving message of {length} bytes")
            
            # Read message data with timeout
            data = b""
            start_time = time.time()
            while len(data) < length:
                # Check for timeout
                if time.time() - start_time > 30:  # 30 seconds max to receive message
                    print(f"Timeout receiving message: got {len(data)}/{length} bytes")
                    return None
                    
                # Receive data chunk
                chunk = sock.recv(min(length - len(data), 4096))
                if not chunk:
                    print(f"Connection closed while receiving data, got {len(data)}/{length} bytes")
                    return None
                data += chunk
            
            # Parse JSON
            try:
                message = json.loads(data.decode())
                return message
            except json.JSONDecodeError:
                print(f"Failed to decode JSON from message")
                return None
                
        except socket.timeout:
            print(f"Socket timeout while receiving message")
            return None
        except socket.error as e:
            print(f"Socket error when receiving message: {str(e)}")
            return None
        except Exception as e:
            print(f"Error receiving message: {str(e)}")
            return None
        finally:
            # Reset timeout
            sock.settimeout(None)
    
    def _handle_new_block(self, block_data: dict) -> bool:
        """Handle a new block from another node"""
        try:
            print(f"Received new block: index={block_data.get('index')}, hash={block_data.get('hash')}")
            
            # Convert dict to Block object
            new_block = self._dict_to_block(block_data)
            
            # Validate block hash
            calculated_hash = new_block.calculate_hash()
            if new_block.hash != calculated_hash:
                print(f"Block hash validation failed: received={new_block.hash}, calculated={calculated_hash}")
                return False
            
            # Check if we already have this block by hash
            for existing_block in self.blockchain.chain:
                if existing_block.hash == new_block.hash:
                    print(f"Block already in our chain (#{new_block.index}), ignoring")
                    return True
            
            # Check block index
            if new_block.index < len(self.blockchain.chain):
                print(f"Received block #{new_block.index} but we already have {len(self.blockchain.chain)} blocks")
                return False
            
            # Validate previous hash (linked to our last block)
            current_last_block = self.blockchain.chain[-1] if self.blockchain.chain else None
            
            if current_last_block and new_block.previous_hash != current_last_block.hash:
                # This could be a fork - handle it properly
                print(f"Received block doesn't link to our last block - potential fork detected")
                print(f"Our last block: #{current_last_block.index}, hash={current_last_block.hash}")
                print(f"New block prev_hash: {new_block.previous_hash}")
                
                # If the new block has a higher index, it might be part of a longer chain
                # We should request the missing blocks from this node
                if new_block.index > current_last_block.index + 1:
                    print(f"Received block is ahead of our chain ({new_block.index} > {current_last_block.index + 1})")
                    print(f"Need to synchronize missing blocks")
                    return False
                
                # If our chain is longer, stick with it
                return False
                
            # If this is the next block in sequence, add it
            if current_last_block and new_block.index != current_last_block.index + 1:
                print(f"Block index mismatch: expected {current_last_block.index + 1}, got {new_block.index}")
                return False
                
            # Add block to our blockchain
            print(f"Adding block #{new_block.index} to our chain")
            self.blockchain.chain.append(new_block)
            
            # Remove transactions in this block from our mempool
            mempool_before = len(self.blockchain.mempool)
            for tx in new_block.transactions:
                # Find matching transactions in mempool
                for mempool_tx in list(self.blockchain.mempool):
                    if (mempool_tx.sender == tx.sender and 
                        mempool_tx.recipient == tx.recipient and
                        abs(mempool_tx.amount - tx.amount) < 0.0001):
                        self.blockchain.mempool.remove(mempool_tx)
                        break
            
            mempool_after = len(self.blockchain.mempool)
            print(f"Removed {mempool_before - mempool_after} transactions from mempool")
            
            # Broadcast to other peers
            self._broadcast_block(new_block)
            
            print(f"Successfully added new block #{new_block.index} (hash: {new_block.hash}) from network")
            return True
            
        except Exception as e:
            print(f"Error handling new block from network: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    def _dict_to_block(self, block_data: dict) -> 'Block':
        """Convert a block dictionary to a Block object"""
        from blockchain import Block, Transaction
        
        # Convert transaction dictionaries to Transaction objects
        transactions = []
        for tx_data in block_data.get("transactions", []):
            transaction = Transaction(
                sender=tx_data.get("sender"),
                recipient=tx_data.get("recipient"),
                amount=float(tx_data.get("amount")),
                fee=float(tx_data.get("fee")),
                signature=tx_data.get("signature"),
                transaction_type=tx_data.get("transaction_type", "TRANSFER"),
                price=tx_data.get("price")
            )
            transaction.timestamp = tx_data.get("timestamp")
            transactions.append(transaction)
        
        # Create Block object
        block = Block(
            index=block_data.get("index"),
            previous_hash=block_data.get("previous_hash"),
            timestamp=block_data.get("timestamp"),
            transactions=transactions,
            nonce=block_data.get("nonce"),
            difficulty_target=block_data.get("difficulty_target")
        )
        
        # Set merkle root and hash directly to match what we received
        block.merkle_root = block_data.get("merkle_root")
        block.hash = block_data.get("hash")
        
        return block
    
    def _handle_new_transaction(self, tx_data: dict) -> bool:
        """Handle a new transaction from another node"""
        try:
            # Log the incoming transaction details
            tx_type = tx_data.get("transaction_type", "TRANSFER")
            tx_sender = tx_data.get("sender")
            tx_recipient = tx_data.get("recipient")
            tx_amount = tx_data.get("amount")
            
            print(f"Received new {tx_type} transaction: {tx_sender} -> {tx_recipient} ({tx_amount})")
            
            # Check if we already have this transaction in the mempool
            for existing_tx in self.blockchain.mempool:
                # Match on key fields to avoid duplicates
                if (existing_tx.sender == tx_sender and 
                    existing_tx.recipient == tx_recipient and 
                    abs(existing_tx.amount - float(tx_amount)) < 0.0001 and
                    existing_tx.transaction_type == tx_type):
                    
                    print(f"Transaction already in mempool, ignoring duplicate")
                    return True
            
            # Convert dict to Transaction object
            from blockchain import Transaction
            
            transaction = Transaction(
                sender=tx_sender,
                recipient=tx_recipient,
                amount=float(tx_amount),
                fee=float(tx_data.get("fee", 0)),
                signature=tx_data.get("signature"),
                transaction_type=tx_type,
                price=tx_data.get("price")
            )
            
            # Set timestamp if provided
            if "timestamp" in tx_data:
                transaction.timestamp = tx_data.get("timestamp")
            
            # Check if this transaction is already in a block in our chain
            for block in self.blockchain.chain:
                for block_tx in block.transactions:
                    if (block_tx.sender == transaction.sender and 
                        block_tx.recipient == transaction.recipient and 
                        abs(block_tx.amount - transaction.amount) < 0.0001 and
                        block_tx.transaction_type == transaction.transaction_type):
                        
                        print(f"Transaction already in blockchain, ignoring")
                        return True
                
            # Add transaction to mempool
            success = self.blockchain.add_transaction_to_mempool(transaction)
            
            if success:
                print(f"✅ Added transaction to mempool: {transaction.sender} -> {transaction.recipient}, amount: {transaction.amount}")
                
                # Relay transaction to other peers
                # Don't relay to the peer that sent it to us to avoid loops
                print(f"Relaying transaction to other peers")
                self._relay_transaction(transaction)
                
                return True
            else:
                print(f"❌ Failed to add transaction to mempool - validation failed")
                return False
                
        except ValueError as e:
            print(f"Validation error handling transaction: {str(e)}")
            return False
        except Exception as e:
            print(f"Error handling new transaction from network: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _relay_transaction(self, transaction):
        """Relay a transaction to all peers"""
        # Convert transaction to dict
        tx_data = transaction.to_dict()
        
        # Create message
        message = {
            "type": "new_transaction",
            "data": tx_data
        }
        
        # Send to all peers
        for node_id, node in self.peers.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((node.address, node.port))
                self._send_message(sock, message)
                sock.close()
            except:
                continue
            
    def _send_blockchain_height(self, node_id: str) -> None:
        """Send our blockchain height to a peer"""
        if node_id not in self.peers:
            return
            
        try:
            node = self.peers[node_id]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((node.address, node.port))
            
            # Send height message
            message = {
                "type": "height",
                "height": len(self.blockchain.chain)
            }
            self._send_message(sock, message)
            sock.close()
        except:
            # Connection failed, node might be offline
            pass
    
    def _request_blockchain(self, node_id: str) -> bool:
        """Request blockchain from a peer"""
        if node_id not in self.peers:
            print(f"Peer {node_id} not found in peers list, cannot request blockchain")
            return False
            
        try:
            print(f"Requesting blockchain from peer {node_id}")
            node = self.peers[node_id]
            
            # Create a socket with timeout
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)  # 30 second timeout for blockchain sync
            
            try:
                print(f"Connecting to peer {node_id} at {node.address}:{node.port}")
                sock.connect((node.address, node.port))
            except ConnectionRefusedError:
                print(f"Connection refused by peer {node_id}")
                if node_id in self.peers:
                    del self.peers[node_id]
                return False
            except Exception as e:
                print(f"Failed to connect to peer {node_id}: {str(e)}")
                return False
            
            # Send get_blocks message with our current chain height
            message = {
                "type": "get_blocks",
                "current_height": len(self.blockchain.chain),
                "from_index": 0  # Request all blocks
            }
            
            print(f"Sending get_blocks request to peer {node_id}")
            if not self._send_message(sock, message):
                print(f"Failed to send get_blocks request to peer {node_id}")
                sock.close()
                return False
            
            # Receive blockchain response (with timeout)
            print(f"Waiting for blockchain data from peer {node_id}")
            response = self._receive_message(sock)
            sock.close()
            
            if not response:
                print(f"No response received from peer {node_id}")
                return False
                
            if response.get("type") != "blocks":
                print(f"Unexpected response type from peer {node_id}: {response.get('type')}")
                return False
                
            # Process blocks
            blocks_data = response.get("blocks", [])
            print(f"Received {len(blocks_data)} blocks from peer {node_id}")
            
            if not blocks_data:
                print(f"Peer {node_id} sent an empty blockchain")
                return False
                
            # Basic sanity check on received data
            if len(blocks_data) <= len(self.blockchain.chain):
                print(f"Our chain ({len(self.blockchain.chain)} blocks) is already longer than peer's chain ({len(blocks_data)} blocks)")
                return False
            
            print(f"Converting blocks from peer {node_id} to internal format")
            
            # Convert blocks from dict to Block objects and create a new chain
            new_chain = []
            for block_data in blocks_data:
                try:
                    block = self._dict_to_block(block_data)
                    new_chain.append(block)
                except Exception as block_err:
                    print(f"Error processing block: {str(block_err)}")
                    return False
            
            # Validate new chain - At minimum, check genesis block and chain continuity
            print(f"Validating blockchain received from peer {node_id}")
            
            # Check genesis block index
            if new_chain[0].index != 0:
                print(f"First block from peer {node_id} is not a genesis block (index={new_chain[0].index})")
                return False
            
            # Check chain continuity (each block points to previous one)
            for i in range(1, len(new_chain)):
                if new_chain[i].previous_hash != new_chain[i-1].hash:
                    print(f"Chain continuity error at block {i}: previous_hash {new_chain[i].previous_hash} doesn't match previous block hash {new_chain[i-1].hash}")
                    return False
            
            # Check block indices are sequential
            for i in range(1, len(new_chain)):
                if new_chain[i].index != new_chain[i-1].index + 1:
                    print(f"Block indices not sequential: block {i-1} has index {new_chain[i-1].index}, block {i} has index {new_chain[i].index}")
                    return False
                    
            # Check difficulty targets make sense
            for block in new_chain:
                if block.difficulty_target < 1 or block.difficulty_target > 64:
                    print(f"Block {block.index} has invalid difficulty target: {block.difficulty_target}")
                    return False
                    
            # Check proof of work on all blocks
            for block in new_chain:
                target = "0" * block.difficulty_target
                if not block.hash.startswith(target):
                    print(f"Block {block.index} fails proof of work validation: {block.hash} should start with {target}")
                    return False
            
            print(f"Blockchain from peer {node_id} passed validation checks")
            
            # Backup our current chain before replacing
            old_chain = self.blockchain.chain
            
            # Replace our chain with the new one
            print(f"Replacing our blockchain ({len(old_chain)} blocks) with peer's chain ({len(new_chain)} blocks)")
            self.blockchain.chain = new_chain
            
            # Clear and update mempool based on the new chain
            print(f"Updating mempool based on new blockchain")
            self._update_mempool_after_sync()
            
            print(f"Successfully synced blockchain from peer {node_id}. New chain length: {len(new_chain)}")
            return True
            
        except socket.timeout:
            print(f"Timeout while syncing blockchain from peer {node_id}")
            return False
        except Exception as e:
            print(f"Error requesting blockchain from peer {node_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    def _update_mempool_after_sync(self):
        """Update mempool after blockchain sync to remove transactions already in blocks"""
        try:
            # Make a copy of the current mempool
            old_mempool = list(self.blockchain.mempool)
            tx_count = len(old_mempool)
            
            # Clear the mempool
            self.blockchain.mempool = []
            
            # Check each transaction to see if it's already in the blockchain
            added_back = 0
            for tx in old_mempool:
                tx_in_chain = False
                
                # Check if transaction is already included in a block
                for block in self.blockchain.chain:
                    for block_tx in block.transactions:
                        # Match on key transaction properties
                        if (block_tx.sender == tx.sender and 
                            block_tx.recipient == tx.recipient and 
                            abs(block_tx.amount - tx.amount) < 0.0001 and
                            block_tx.transaction_type == tx.transaction_type):
                            tx_in_chain = True
                            break
                    if tx_in_chain:
                        break
                        
                # If not in chain, add it back to mempool
                if not tx_in_chain:
                    self.blockchain.mempool.append(tx)
                    added_back += 1
                    
            print(f"Mempool update: started with {tx_count} transactions, re-added {added_back}")
            
        except Exception as e:
            print(f"Error updating mempool after sync: {str(e)}")
            # In case of error, reset to empty mempool for safety
            self.blockchain.mempool = []
            
    def _send_blockchain(self, node_id: str) -> None:
        """Send our blockchain to a peer"""
        if node_id not in self.peers:
            return
            
        try:
            node = self.peers[node_id]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((node.address, node.port))
            
            # Convert blocks to dict
            blocks_data = []
            for block in self.blockchain.chain:
                block_dict = {
                    "index": block.index,
                    "previous_hash": block.previous_hash,
                    "timestamp": block.timestamp,
                    "transactions": [tx.to_dict() for tx in block.transactions],
                    "nonce": block.nonce,
                    "difficulty_target": block.difficulty_target,
                    "merkle_root": block.merkle_root,
                    "hash": block.hash
                }
                blocks_data.append(block_dict)
                
            # Send blocks message
            message = {
                "type": "blocks",
                "blocks": blocks_data
            }
            self._send_message(sock, message)
            sock.close()
            
        except Exception as e:
            print(f"Error sending blockchain: {str(e)}")
            
    def _handle_block_range_request(self, node_id: str, start_height: int, end_height: int) -> None:
        """Send a range of blocks to a peer"""
        if node_id not in self.peers:
            return
            
        try:
            node = self.peers[node_id]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)  # 30 second timeout for large block transfers
            
            try:
                sock.connect((node.address, node.port))
            except (ConnectionRefusedError, socket.timeout):
                print(f"Failed to connect to peer {node_id} for block range request")
                return
            
            print(f"Sending block range {start_height}-{end_height} to peer {node_id}")
            
            # Limit the range to avoid excessive data (max 100 blocks)
            if end_height - start_height > 100:
                end_height = start_height + 100
                
            # Ensure valid range
            start_height = max(0, min(start_height, len(self.blockchain.chain) - 1))
            end_height = max(start_height + 1, min(end_height, len(self.blockchain.chain)))
            
            # Gather blocks in the range
            blocks_data = []
            for i in range(start_height, end_height):
                if i < len(self.blockchain.chain):
                    block = self.blockchain.chain[i]
                    block_data = self._block_to_dict(block)
                    blocks_data.append(block_data)
            
            # Send blocks
            message = {
                "type": "block_range",
                "blocks": blocks_data
            }
            
            print(f"Sending {len(blocks_data)} blocks to peer {node_id}")
            if self._send_message(sock, message):
                print(f"Successfully sent block range to peer {node_id}")
            else:
                print(f"Failed to send block range to peer {node_id}")
                
            sock.close()
            
        except Exception as e:
            print(f"Error sending block range to peer {node_id}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _process_block_range(self, blocks_data: list) -> bool:
        """Process a received range of blocks"""
        try:
            if not blocks_data:
                print("Received empty block range")
                return False
                
            print(f"Processing {len(blocks_data)} blocks from peer")
            
            # Convert blocks from dict to Block objects
            blocks = []
            for block_data in blocks_data:
                try:
                    block = self._dict_to_block(block_data)
                    blocks.append(block)
                except Exception as e:
                    print(f"Error processing block data: {str(e)}")
                    return False
            
            # Check that blocks form a valid chain
            for i in range(1, len(blocks)):
                if blocks[i].previous_hash != blocks[i-1].hash:
                    print(f"Invalid block chain: block {i} does not reference previous block")
                    return False
            
            # Check that first block connects to our chain
            if len(self.blockchain.chain) > 0:
                first_block = blocks[0]
                
                # If this is supposed to be the next block in our chain
                if first_block.index == len(self.blockchain.chain):
                    if first_block.previous_hash != self.blockchain.chain[-1].hash:
                        print(f"First block doesn't connect to our chain")
                        return False
                        
                # If this is replacing our chain at some point (fork resolution)
                elif first_block.index < len(self.blockchain.chain):
                    # Verify that it connects properly to our chain at that point
                    if first_block.index > 0:
                        if first_block.previous_hash != self.blockchain.chain[first_block.index - 1].hash:
                            print(f"Block at index {first_block.index} doesn't connect properly to our chain")
                            return False
                else:
                    print(f"Received block range doesn't connect to our chain")
                    return False
            
            # Apply blocks to our chain
            for block in blocks:
                if block.index < len(self.blockchain.chain):
                    # Replace existing block (fork resolution)
                    self.blockchain.chain[block.index] = block
                    print(f"Replaced block at index {block.index}")
                elif block.index == len(self.blockchain.chain):
                    # Add as next block
                    self.blockchain.chain.append(block)
                    print(f"Added block #{block.index} to chain")
                    
                    # Process transactions (remove from mempool)
                    for tx in block.transactions:
                        for mempool_tx in list(self.blockchain.mempool):
                            if (mempool_tx.sender == tx.sender and 
                                mempool_tx.recipient == tx.recipient and 
                                abs(mempool_tx.amount - tx.amount) < 0.0001):
                                self.blockchain.mempool.remove(mempool_tx)
                                break
                else:
                    print(f"Unexpected block index: {block.index} (chain length: {len(self.blockchain.chain)})")
                    return False
            
            # Save chain to disk
            self.blockchain.save_chain_to_disk()
            
            print(f"Successfully processed {len(blocks)} blocks. New chain length: {len(self.blockchain.chain)}")
            return True
            
        except Exception as e:
            print(f"Error processing block range: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _send_peer_list(self, node_id: str) -> None:
        """Send our peer list to a requesting peer"""
        if node_id not in self.peers:
            return
            
        try:
            node = self.peers[node_id]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((node.address, node.port))
            
            # Prepare peer list - convert Node objects to dict
            peers_data = []
            for peer_id, peer in self.peers.items():
                # Don't include the requesting node in the list
                if peer_id != node_id:
                    peers_data.append({
                        "node_id": peer_id,
                        "address": peer.address,
                        "port": peer.port
                    })
            
            # Send peers message
            message = {
                "type": "peers",
                "peers": peers_data
            }
            self._send_message(sock, message)
            sock.close()
            
        except Exception as e:
            print(f"Error sending peer list: {str(e)}")
            
    def _handle_peer_list(self, peers: list, source_node_id: str) -> None:
        """Process a received peer list and connect to new peers"""
        for peer_data in peers:
            try:
                # Extract peer details
                if not all(k in peer_data for k in ["address", "port"]):
                    continue
                    
                address = peer_data["address"]
                port = peer_data["port"]
                node_id = peer_data.get("node_id", f"{address}:{port}")
                
                # Skip if we already know this peer
                if node_id in self.peers:
                    continue
                    
                # Skip if it's ourselves
                if address == self.host and port == self.port:
                    continue
                
                # Try to connect to the new peer
                print(f"Discovered new peer {address}:{port} from {source_node_id}")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)  # 5 second timeout
                sock.connect((address, port))
                
                # Perform handshake
                if self._perform_handshake(sock):
                    # Add to peers
                    self.peers[node_id] = Node(
                        address=address,
                        port=port,
                        last_seen=time.time()
                    )
                    
                    # Start handler thread
                    threading.Thread(
                        target=self._handle_connection,
                        args=(sock, (address, port)),
                        daemon=True
                    ).start()
                    
                    print(f"Successfully connected to new peer {node_id}")
                else:
                    sock.close()
                    
            except Exception as e:
                print(f"Error connecting to new peer: {str(e)}")

# Create global instance in development mode
GCN = GlobalCoyn(dev_mode=False)  # Set to dev_mode=False to enable P2P networking
