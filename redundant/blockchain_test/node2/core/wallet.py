import hashlib
import json
import os
import base64
import time
import datetime
from typing import List, Dict, Tuple, Optional, Any
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from ecdsa.util import sigencode_der, sigdecode_der
import base58
import secrets
from mnemonic import Mnemonic
from cryptography.fernet import Fernet
import os
import sys
# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from blockchain import Transaction

# Global cache for wallet balances - used to ensure frontend consistency during sell operations
WALLET_BALANCE_CACHE: Dict[str, Dict[str, Any]] = {}

class WalletAddress:
    def __init__(self, private_key: SigningKey, public_key: VerifyingKey, address: str):
        self.private_key = private_key
        self.public_key = public_key
        self.address = address

class Wallet:
    def __init__(self, encrypted_storage_path: str = "wallet.enc"):
        """Initialize wallet with optional encrypted storage path"""
        self.addresses: Dict[str, WalletAddress] = {}
        self.storage_path = encrypted_storage_path
        self.encryption_key = self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self.mnemo = Mnemonic("english")

    def _generate_encryption_key(self) -> bytes:
        """Generate or load encryption key for wallet storage"""
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
        """Generate a new BIP-39 seed phrase"""
        return self.mnemo.generate()

    def create_from_seed_phrase(self, seed_phrase: str) -> str:
        """Create a new wallet address from a seed phrase"""
        if not self.mnemo.check(seed_phrase):
            raise ValueError("Invalid seed phrase")

        seed = self.mnemo.to_seed(seed_phrase)
        private_key = SigningKey.from_string(seed[:32], curve=SECP256k1)
        return self._add_key_pair(private_key)

    def create_new_address(self) -> str:
        """Generate a new random address"""
        private_key = SigningKey.generate(curve=SECP256k1)
        return self._add_key_pair(private_key)

    def _add_key_pair(self, private_key: SigningKey) -> str:
        """Add a key pair to the wallet and return the address"""
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
        
        return address

    def get_addresses(self) -> List[str]:
        """Get list of all addresses in the wallet"""
        return list(self.addresses.keys())

    def sign_transaction(self, sender_address: str, recipient_address: str, 
                        amount: float, fee: float) -> Optional[Transaction]:
        """Create and sign a new transaction"""
        if sender_address not in self.addresses:
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
        
        # Create and return signed transaction
        return Transaction(
            sender=sender_address,
            recipient=recipient_address,
            amount=amount,
            fee=fee,
            signature=base64.b64encode(signature).decode('utf-8')
        )

    def verify_transaction(self, transaction: Transaction) -> bool:
        """Verify a transaction's signature"""
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
                return public_key.verify(
                    signature,
                    tx_hash,
                    sigdecode=sigdecode_der
                )
        except:
            pass
        return False

    def save_to_file(self) -> None:
        """Save encrypted wallet data to file"""
        # Get coins data to save
        coins_data = []
        for coin in getattr(self, '_coins', []):
            try:
                coins_data.append({
                    "amount": coin.amount,
                    "owner": coin.owner
                })
            except:
                pass  # Skip if coin can't be serialized
        
        # Build wallet data with coins
        wallet_data = {
            "addresses": {
                addr: {
                    "private_key": base64.b64encode(addr_data.private_key.to_string()).decode('utf-8'),
                    "public_key": base64.b64encode(addr_data.public_key.to_string()).decode('utf-8'),
                    "address": addr_data.address
                }
                for addr, addr_data in self.addresses.items()
            },
            "coins": coins_data
        }
        
        # Debug info
        print(f"Saving wallet with {len(coins_data)} coins entries")
        if coins_data:
            print(f"Coins to save: {coins_data}")
        
        encrypted_data = self.fernet.encrypt(json.dumps(wallet_data).encode())
        with open(self.storage_path, "wb") as f:
            f.write(encrypted_data)

    def load_from_file(self) -> bool:
        """Load encrypted wallet data from file"""
        try:
            if not os.path.exists(self.storage_path):
                return False
            
            with open(self.storage_path, "rb") as f:
                encrypted_data = f.read()
            
            wallet_data = json.loads(self.fernet.decrypt(encrypted_data))
            
            # Handle the new format (with addresses and coins)
            if isinstance(wallet_data, dict) and "addresses" in wallet_data:
                # New format
                self.addresses = {}
                address_data = wallet_data["addresses"]
                for addr, data in address_data.items():
                    private_key = SigningKey.from_string(
                        base64.b64decode(data["private_key"]),
                        curve=SECP256k1
                    )
                    public_key = VerifyingKey.from_string(
                        base64.b64decode(data["public_key"]),
                        curve=SECP256k1
                    )
                    self.addresses[addr] = WalletAddress(private_key, public_key, data["address"])
                
                # Load coins if they exist
                if "coins" in wallet_data and wallet_data["coins"]:
                    try:
                        # Import Coin class here to avoid circular imports
                        from backend.coin import Coin
                        
                        # Reset existing coins
                        self._coins = []
                        
                        # Load all coins
                        for coin_data in wallet_data["coins"]:
                            # Check if amount is present and valid
                            if "amount" in coin_data:
                                amount = float(coin_data["amount"])
                                # Only add valid positive amounts
                                if amount > 0:
                                    owner = coin_data.get("owner")
                                    coin = Coin(amount, owner)
                                    self._coins.append(coin)
                        
                        print(f"Loaded {len(self._coins)} coins from wallet file")
                    except Exception as e:
                        print(f"Error loading coins: {str(e)}")
                        # Initialize with empty coins if loading fails
                        self._coins = []
            else:
                # Old format - only addresses, no coins
                self.addresses = {}
                for addr, data in wallet_data.items():
                    private_key = SigningKey.from_string(
                        base64.b64decode(data["private_key"]),
                        curve=SECP256k1
                    )
                    public_key = VerifyingKey.from_string(
                        base64.b64decode(data["public_key"]),
                        curve=SECP256k1
                    )
                    self.addresses[addr] = WalletAddress(private_key, public_key, data["address"])
            
            return True
        except Exception as e:
            print(f"Failed to load wallet file: {str(e)}")
            return False

    def export_private_key(self, address: str) -> Optional[str]:
        """Export private key for an address in WIF format"""
        if address not in self.addresses:
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
        """Import a private key in WIF format"""
        try:
            # Decode WIF key
            decoded = base58.b58decode(wif_key)
            
            # Remove version byte, compression flag, and checksum
            private_key_bytes = decoded[1:-5]
            
            # Create key pair and add to wallet
            private_key = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
            return self._add_key_pair(private_key)
        except:
            return None

    def load_from_address(self, address: str, force_reload: bool = False) -> bool:
        """
        Load wallet data for a specific address
        
        Args:
            address: The wallet address to load
            force_reload: If True, always reload from file even if wallet is already loaded
        """
        try:
            # Track which address we're currently working with
            self._current_address = address
            
            # Always reload from file if force_reload is True
            if force_reload and os.path.exists(self.storage_path):
                print(f"🔄 FORCE RELOADING wallet from file for address: {address}")
                self.load_from_file()
                print(f"🔄 Force reloaded wallet with {len(getattr(self, '_coins', []))} coins")
            # Otherwise, load from file if wallet is empty or if we don't have this address
            elif (not self.addresses or address not in self.addresses) and os.path.exists(self.storage_path):
                # Reload from file to ensure we have the latest coin balances
                self.load_from_file()
                print(f"Loaded wallet from file with {len(getattr(self, '_coins', []))} coins")
            
            # Check if address exists in loaded wallet
            if address in self.addresses:
                # Verify we have the coins loaded
                coins = getattr(self, '_coins', [])
                total_balance = sum([c.amount for c in coins]) if coins else 0
                print(f"Wallet has {len(coins)} coins with total balance: {total_balance}")
                return True
            
            return False
        except Exception as e:
            print(f"Error loading wallet for address {address}: {str(e)}")
            return False

    def add_coins(self, coin) -> None:
        """Add coins to the wallet"""
        # This is used to update the wallet after mining or purchasing COON
        # Get any existing coins to update them
        self._coins = getattr(self, '_coins', [])
        
        # If we have existing coins, update them
        if self._coins:
            current_amount = self._coins[0].amount
            self._coins[0].add(coin.amount)
            print(f"Updated coin amount: {current_amount} → {self._coins[0].amount}")
        else:
            # No existing coins, add the new one
            self._coins.append(coin)
            print(f"Added new coin with amount: {coin.amount}")
            
        print(f"Added {coin.amount} coins to wallet, total: {self._coins[0].amount}")
        
        # Save the wallet to ensure the coin balance persists
        try:
            self.save_to_file()
            print("Wallet saved after adding coins")
        except Exception as e:
            print(f"WARNING: Failed to save wallet after adding coins: {str(e)}")
    
    def remove_coins(self, amount: float) -> bool:
        """Remove coins from the wallet when selling"""
        # Make sure amount is a float
        amount = float(amount)
        
        # Get existing coins
        self._coins = getattr(self, '_coins', [])
        
        # Check if we have any coins
        if not self._coins:
            print("No coins in wallet to remove")
            # Try to initialize with a coin for easier management
            from backend.coin import Coin
            self._coins = [Coin(0)]
            print("Initialized empty coin collection")
            return False
            
        # Check if we have enough coins
        if self._coins[0].amount < amount:
            print(f"Insufficient coins: have {self._coins[0].amount}, need {amount}")
            return False
            
        # Subtract coins
        current_amount = self._coins[0].amount
        self._coins[0].subtract(amount)
        
        # Verify amount was correctly subtracted
        new_amount = self._coins[0].amount
        expected_amount = round(current_amount - amount, 8)
        
        if abs(new_amount - expected_amount) > 0.00000001:
            print(f"WARNING: Coin subtraction resulted in unexpected amount: {new_amount} (expected {expected_amount})")
            # Force the correct amount
            self._coins[0].amount = expected_amount
            new_amount = expected_amount
        
        print(f"Removed {amount} coins from wallet: {current_amount} → {new_amount}")
        
        # Make sure we save the wallet to preserve this change
        try:
            self.save_to_file()
            print("Wallet saved after removing coins")
        except Exception as e:
            print(f"WARNING: Failed to save wallet after removing coins: {str(e)}")
        
        return True
    
    def get_coins(self):
        """Get all coins in the wallet"""
        self._coins = getattr(self, '_coins', [])
        if not self._coins:
            # Initialize with zero coins if none exist
            from backend.coin import Coin
            self._coins = [Coin(0)]
        return self._coins
    
    def set_balance(self, balance: float) -> None:
        """
        Set the wallet balance to a specific value
        
        This is used to force the wallet to have a specific balance, particularly
        after sell operations to ensure consistency with the blockchain.
        
        Args:
            balance: The new balance to set
        """
        if not hasattr(self, '_coins'):
            from backend.coin import Coin
            self._coins = []
        
        # Clear existing coins
        self._coins = []
        
        # Add new coin with specified amount if balance > 0
        if balance > 0:
            from backend.coin import Coin
            self._coins = [Coin(balance)]
            print(f"Set wallet balance to {balance} COON")
        else:
            print("Set wallet balance to 0 COON (empty wallet)")
            
        # Save to file to persist change
        self.save_to_file()
        
        # Update global balance cache for this address
        if hasattr(self, '_current_address') and self._current_address:
            WALLET_BALANCE_CACHE[self._current_address] = {
                'balance': balance,
                'timestamp': datetime.datetime.now()
            }
            print(f"Updated global balance cache for {self._current_address}: {balance}")
    
    def get_balance(self) -> float:
        """
        Get the total balance of all coins in the wallet
        
        This method now checks the global balance cache first before calculating from coins.
        This ensures consistent balance reporting between sell operations and balance checks.
        """
        # Get current address being used (if any)
        current_address = None
        if hasattr(self, '_current_address') and self._current_address:
            current_address = self._current_address
        elif self.addresses and len(self.addresses) > 0:
            # Just take the first address as a fallback
            current_address = list(self.addresses.keys())[0]
            
        # Check if we have a cached balance for this address
        if current_address and current_address in WALLET_BALANCE_CACHE:
            cache_entry = WALLET_BALANCE_CACHE[current_address]
            cache_age = (datetime.datetime.now() - cache_entry['timestamp']).total_seconds()
            
            # Use cached value if it's less than 30 seconds old
            if cache_age < 30:
                cached_balance = cache_entry['balance']
                print(f"🔵 Using cached wallet balance: {cached_balance} (age: {cache_age:.1f}s)")
                return cached_balance
            else:
                # Clean up old cache entries
                del WALLET_BALANCE_CACHE[current_address]
                print(f"🧹 Cleared old balance cache (age: {cache_age:.1f}s)")
        
        # Fall back to calculating from coins
        coins = self.get_coins()
        if not coins:
            return 0.0
        total = sum(coin.amount for coin in coins)
        print(f"Wallet balance calculation: {total} COON from {len(coins)} coin entries")
        return total