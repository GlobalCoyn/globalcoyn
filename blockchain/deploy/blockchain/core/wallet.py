"""
Wallet module for the GlobalCoyn blockchain.
Handles wallet creation, key management, and transaction signing.
"""
import hashlib
import json
import os
import base64
import time
import logging
from typing import List, Dict, Tuple, Optional, Any, Union
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from ecdsa.util import sigencode_der, sigdecode_der
import base58
import secrets
from mnemonic import Mnemonic
from cryptography.fernet import Fernet

# Import our modules
from transaction import Transaction
from coin import Coin, CoinManager

class WalletAddress:
    """
    Represents a wallet address with its associated keys.
    """
    def __init__(self, private_key: SigningKey, public_key: VerifyingKey, address: str):
        """
        Initialize a wallet address.
        
        Args:
            private_key: ECDSA signing key
            public_key: ECDSA verifying key
            address: Base58 encoded wallet address
        """
        self.private_key = private_key
        self.public_key = public_key
        self.address = address
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert wallet address to dictionary for serialization.
        
        Returns:
            Dictionary representation of the wallet address
        """
        return {
            "private_key": base64.b64encode(self.private_key.to_string()).decode('utf-8'),
            "public_key": base64.b64encode(self.public_key.to_string()).decode('utf-8'),
            "address": self.address
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WalletAddress':
        """
        Create wallet address from dictionary.
        
        Args:
            data: Dictionary containing wallet address data
            
        Returns:
            A WalletAddress object
        """
        private_key = SigningKey.from_string(
            base64.b64decode(data["private_key"]),
            curve=SECP256k1
        )
        public_key = VerifyingKey.from_string(
            base64.b64decode(data["public_key"]),
            curve=SECP256k1
        )
        return cls(private_key, public_key, data["address"])

class Wallet:
    """
    Manages cryptocurrency wallet functionality including addresses, keys, and signing.
    """
    def __init__(self, encrypted_storage_path: str = "wallet.enc"):
        """
        Initialize wallet with optional encrypted storage path.
        
        Args:
            encrypted_storage_path: Path to the encrypted wallet file
        """
        self.addresses: Dict[str, WalletAddress] = {}
        self.storage_path = encrypted_storage_path
        self.encryption_key = self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self.mnemo = Mnemonic("english")
        self.coin_manager = CoinManager()
        self.logger = logging.getLogger("wallet")

    def _generate_encryption_key(self) -> bytes:
        """
        Generate or load encryption key for wallet storage.
        
        Returns:
            Encryption key as bytes
        """
        key_file = "wallet.key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            return key

    def generate_seed_phrase(self) -> str:
        """
        Generate a new BIP-39 seed phrase.
        
        Returns:
            BIP-39 seed phrase
        """
        return self.mnemo.generate()

    def create_from_seed_phrase(self, seed_phrase: str) -> str:
        """
        Create a new wallet address from a seed phrase.
        
        Args:
            seed_phrase: BIP-39 seed phrase
            
        Returns:
            New wallet address
            
        Raises:
            ValueError: If seed phrase is invalid
        """
        if not self.mnemo.check(seed_phrase):
            raise ValueError("Invalid seed phrase")

        seed = self.mnemo.to_seed(seed_phrase)
        private_key = SigningKey.from_string(seed[:32], curve=SECP256k1)
        return self._add_key_pair(private_key)

    def create_new_address(self) -> str:
        """
        Generate a new random address.
        
        Returns:
            New wallet address
        """
        private_key = SigningKey.generate(curve=SECP256k1)
        return self._add_key_pair(private_key)

    def _add_key_pair(self, private_key: SigningKey) -> str:
        """
        Add a key pair to the wallet and return the address.
        
        Args:
            private_key: ECDSA signing key
            
        Returns:
            Generated wallet address
        """
        public_key = private_key.get_verifying_key()
        
        # Generate address from public key
        pub_hash = hashlib.sha256(public_key.to_string()).digest()
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(pub_hash)
        pub_hash = ripemd160.digest()
        
        # Add version byte (0x00 for mainnet)
        version_pub_hash = b'\x00' + pub_hash
        
        # Double SHA256 for checksum
        checksum = hashlib.sha256(hashlib.sha256(version_pub_hash).digest()).digest()[:4]
        
        # Combine and encode to base58
        binary_address = version_pub_hash + checksum
        address = base58.b58encode(binary_address).decode('utf-8')
        
        # Store the address and keys
        self.addresses[address] = WalletAddress(private_key, public_key, address)
        self.logger.info(f"Added new wallet address: {address}")
        
        return address

    def get_addresses(self) -> List[str]:
        """
        Get list of all addresses in the wallet.
        
        Returns:
            List of wallet addresses
        """
        return list(self.addresses.keys())

    def sign_transaction(self, sender_address: str, recipient_address: str, 
                       amount: float, fee: float) -> Optional[Transaction]:
        """
        Create and sign a new transaction.
        
        Args:
            sender_address: Sender's wallet address
            recipient_address: Recipient's wallet address
            amount: Amount to transfer
            fee: Transaction fee
            
        Returns:
            Signed Transaction object or None if signing fails
        """
        if sender_address not in self.addresses:
            self.logger.warning(f"Cannot sign transaction: address {sender_address} not in wallet")
            return None
        
        wallet_address = self.addresses[sender_address]
        
        # Create transaction data
        tx_data = {
            "sender": sender_address,
            "recipient": recipient_address,
            "amount": amount,
            "fee": fee,
            "timestamp": time.time()
        }
        
        # Sign transaction data
        tx_hash = hashlib.sha256(json.dumps(tx_data, sort_keys=True).encode()).digest()
        signature = wallet_address.private_key.sign(
            tx_hash,
            sigencode=sigencode_der
        )
        
        self.logger.info(f"Created and signed transaction: {amount} from {sender_address} to {recipient_address}")
        
        # Create and return signed transaction
        return Transaction(
            sender=sender_address,
            recipient=recipient_address,
            amount=amount,
            fee=fee,
            signature=base64.b64encode(signature).decode('utf-8')
        )

    def verify_transaction(self, transaction: Transaction) -> bool:
        """
        Verify a transaction's signature.
        
        Args:
            transaction: Transaction to verify
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Recreate transaction data for verification
            tx_data = {
                "sender": transaction.sender,
                "recipient": transaction.recipient,
                "amount": transaction.amount,
                "fee": transaction.fee,
                "timestamp": transaction.timestamp
            }
            
            tx_hash = hashlib.sha256(json.dumps(tx_data, sort_keys=True).encode()).digest()
            signature = base64.b64decode(transaction.signature)
            
            # Get public key from sender's address
            if transaction.sender in self.addresses:
                public_key = self.addresses[transaction.sender].public_key
                result = public_key.verify(
                    signature,
                    tx_hash,
                    sigdecode=sigdecode_der
                )
                return result
        except Exception as e:
            self.logger.error(f"Verification error: {str(e)}")
        return False

    def save_to_file(self) -> bool:
        """
        Save encrypted wallet data to file.
        
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Build wallet data with addresses and coins
            wallet_data = {
                "addresses": {
                    addr: addr_data.to_dict()
                    for addr, addr_data in self.addresses.items()
                },
                "coins": self.coin_manager.to_dict().get("coins", [])
            }
            
            self.logger.info(f"Saving wallet with {len(self.addresses)} addresses and {len(wallet_data['coins'])} coins")
            
            # Encrypt and save
            encrypted_data = self.fernet.encrypt(json.dumps(wallet_data).encode())
            with open(self.storage_path, "wb") as f:
                f.write(encrypted_data)
                
            return True
        except Exception as e:
            self.logger.error(f"Failed to save wallet: {str(e)}")
            return False

    def load_from_file(self) -> bool:
        """
        Load encrypted wallet data from file.
        
        Returns:
            True if load successful, False otherwise
        """
        try:
            if not os.path.exists(self.storage_path):
                self.logger.warning(f"Wallet file not found: {self.storage_path}")
                return False
            
            with open(self.storage_path, "rb") as f:
                encrypted_data = f.read()
            
            wallet_data = json.loads(self.fernet.decrypt(encrypted_data))
            
            # Load addresses
            self.addresses = {}
            if "addresses" in wallet_data:
                for addr, data in wallet_data["addresses"].items():
                    wallet_address = WalletAddress.from_dict(data)
                    self.addresses[addr] = wallet_address
            
            # Load coins
            if "coins" in wallet_data:
                coin_data = {"coins": wallet_data["coins"]}
                self.coin_manager = CoinManager.from_dict(coin_data)
            
            self.logger.info(f"Loaded wallet with {len(self.addresses)} addresses and {len(wallet_data.get('coins', []))} coins")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load wallet: {str(e)}")
            return False

    def export_private_key(self, address: str) -> Optional[str]:
        """
        Export private key for an address in WIF format.
        
        Args:
            address: Wallet address to export key for
            
        Returns:
            WIF-formatted private key or None if address not found
        """
        if address not in self.addresses:
            self.logger.warning(f"Cannot export key: address {address} not in wallet")
            return None
        
        private_key_bytes = self.addresses[address].private_key.to_string()
        
        # Add version byte and compression flag
        version_key = b'\x80' + private_key_bytes + b'\x01'
        
        # Add checksum
        checksum = hashlib.sha256(hashlib.sha256(version_key).digest()).digest()[:4]
        final_key = version_key + checksum
        
        # Encode to base58
        return base58.b58encode(final_key).decode('utf-8')

    def import_private_key(self, wif_key: str) -> Optional[str]:
        """
        Import a private key in WIF format.
        
        Args:
            wif_key: WIF-formatted private key
            
        Returns:
            Imported wallet address or None if import fails
        """
        try:
            # Decode WIF key
            decoded = base58.b58decode(wif_key)
            
            # Remove version byte, compression flag, and checksum
            private_key_bytes = decoded[1:-5]
            
            # Create key pair and add to wallet
            private_key = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
            address = self._add_key_pair(private_key)
            self.logger.info(f"Imported private key with address: {address}")
            return address
        except Exception as e:
            self.logger.error(f"Failed to import private key: {str(e)}")
            return None
            
    def delete_wallet(self, address: str) -> bool:
        """
        Securely delete a wallet address.
        
        Args:
            address: Address to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        if address not in self.addresses:
            self.logger.warning(f"Cannot delete wallet: address {address} not in wallet")
            return False
            
        # Remove address
        del self.addresses[address]
        
        # Save changes
        result = self.save_to_file()
        if result:
            self.logger.info(f"Deleted wallet address: {address}")
        return result
        
    def validate_address(self, address: str) -> bool:
        """
        Validate a wallet address format.
        
        Args:
            address: Address to validate
            
        Returns:
            True if address format is valid, False otherwise
        """
        try:
            # Basic format check
            if not address or len(address) < 26 or len(address) > 35:
                return False
                
            # Decode base58
            decoded = base58.b58decode(address)
            
            # Check length (1 byte version + 20 bytes hash + 4 bytes checksum)
            if len(decoded) != 25:
                return False
                
            # Extract parts
            version_hash = decoded[:-4]
            checksum = decoded[-4:]
            
            # Verify checksum
            calculated_checksum = hashlib.sha256(hashlib.sha256(version_hash).digest()).digest()[:4]
            
            return checksum == calculated_checksum
        except:
            return False
            
    def get_mining_stats(self, address: str) -> Dict[str, Any]:
        """
        Get mining statistics for a wallet address.
        
        Args:
            address: Wallet address to get stats for
            
        Returns:
            Dictionary of mining statistics
        """
        # This would typically query the blockchain for mining-related data
        # For now, return a basic structure
        return {
            "address": address,
            "is_mining_wallet": address in self.addresses,
            "total_rewards": 0.0,  # Would be calculated from blockchain data
            "blocks_mined": 0      # Would be calculated from blockchain data
        }