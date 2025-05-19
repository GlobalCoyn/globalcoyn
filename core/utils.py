"""
Utility functions for the GlobalCoyn blockchain.
Includes difficulty calculations, validation, and other helper functions.
"""
import hashlib
import time
import logging
from typing import List, Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("blockchain.log"),
        logging.StreamHandler()
    ]
)

def bits_to_target(bits: int) -> int:
    """
    Convert compact bits representation to target threshold.
    
    Args:
        bits: Compact bits format (like in Bitcoin)
        
    Returns:
        Target value as integer
    """
    # Extract the bytes
    size = bits >> 24
    word = bits & 0x007fffff
    
    # Convert to target
    if size <= 3:
        return word >> (8 * (3 - size))
    else:
        return word << (8 * (size - 3))

def target_to_bits(target: int) -> int:
    """
    Convert a target threshold to compact bits representation.
    
    Args:
        target: Target value as integer
        
    Returns:
        Compact bits format (like in Bitcoin)
    """
    # Find the size (number of bytes)
    size = (target.bit_length() + 7) // 8
    
    # Convert to bits format
    if size <= 3:
        bits = (target & 0xffffff) << (8 * (3 - size))
        return bits | size << 24
    else:
        bits = target >> (8 * (size - 3))
        return bits | size << 24

def calculate_target_adjustment(expected_time: float, actual_time: float, 
                               current_target: int, max_target: int) -> int:
    """
    Calculate a new target value based on time differences.
    
    Args:
        expected_time: Expected time between difficulty adjustments 
        actual_time: Actual time between difficulty adjustments
        current_target: Current target value
        max_target: Maximum target value (minimum difficulty)
        
    Returns:
        New target value
    """
    # Calculate adjustment factor but with gentler changes for development
    # Limit to 1.25x change in either direction
    adjustment_factor = expected_time / max(min(actual_time, expected_time * 1.25), expected_time / 1.25)
    
    # Dampen the adjustment (make changes 50% smaller)
    dampened_adjustment = 1.0 + (adjustment_factor - 1.0) * 0.5
    
    # Adjust difficulty (target is inversely proportional to difficulty)
    new_target = int(current_target / dampened_adjustment)
    
    # Apply upper bound on target (lower bound on difficulty)
    if new_target > max_target:
        new_target = max_target
        
    logging.info(f"Difficulty adjustment: Factor={dampened_adjustment}, "
                f"Old target={current_target}, New target={new_target}")
    
    return new_target

def validate_address_format(address: str) -> bool:
    """
    Validate the format of a wallet address.
    
    Args:
        address: Wallet address to validate
        
    Returns:
        True if the address format is valid, False otherwise
    """
    # Basic format validation
    if not address or len(address) < 26 or len(address) > 35:
        return False
    
    # Special addresses (for mining rewards)
    if address == "0":
        return True
    
    # More detailed validation could be added here:
    # - Base58 character set validation
    # - Checksum validation
    # - Version byte validation
    
    return True

def hash_to_hex(data: bytes) -> str:
    """
    Create a double SHA-256 hash and return as hex string.
    
    Args:
        data: Bytes to hash
        
    Returns:
        Hex string hash
    """
    first_hash = hashlib.sha256(data).digest()
    second_hash = hashlib.sha256(first_hash).hexdigest()
    return second_hash