"""
GlobalCoyn Blockchain Core Module.
This package contains the core implementations of the GlobalCoyn blockchain.
"""

from .transaction import Transaction
from .block import Block
from .blockchain import Blockchain
from .mempool import Mempool
from .mining import Miner
from .wallet import Wallet, WalletAddress
from .coin import Coin, CoinManager
from .contract import Contract, ContractManager, ContractError, ContractState
from .utils import bits_to_target, target_to_bits, validate_address_format

# Version
__version__ = '1.0.1'