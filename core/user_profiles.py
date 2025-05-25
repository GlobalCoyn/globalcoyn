"""
User Profiles Smart Contract for GlobalCoyn
Handles user profile metadata with IPFS integration
"""

import json
import time
import hashlib
from typing import Dict, Any, Optional

class UserProfilesContract:
    def __init__(self):
        self.profiles = {}  # address -> profile data
        self.alias_to_address = {}  # alias -> address mapping
        self.reserved_aliases = set()
        
    def is_alias_available(self, alias: str) -> bool:
        """Check if an alias is available for registration"""
        return alias.lower() not in self.alias_to_address and alias.lower() not in self.reserved_aliases
    
    def set_profile(self, wallet_address: str, alias: str, ipfs_image_hash: str, bio: str = "") -> Dict[str, Any]:
        """
        Set user profile data
        
        Args:
            wallet_address: User's wallet address
            alias: Unique username
            ipfs_image_hash: IPFS hash of profile image
            bio: User biography
            
        Returns:
            Transaction result
        """
        # Validate alias
        if not self.is_alias_available(alias) and self.alias_to_address.get(alias.lower()) != wallet_address:
            return {"success": False, "error": "Alias already taken"}
        
        # Validate IPFS hash format
        if not self._validate_ipfs_hash(ipfs_image_hash):
            return {"success": False, "error": "Invalid IPFS hash format"}
        
        # Remove old alias mapping if user had one
        old_profile = self.profiles.get(wallet_address)
        if old_profile and old_profile.get('alias'):
            old_alias = old_profile['alias'].lower()
            if old_alias in self.alias_to_address:
                del self.alias_to_address[old_alias]
        
        # Create new profile
        profile = {
            "alias": alias,
            "ipfs_image_hash": ipfs_image_hash,
            "bio": bio,
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
            "wallet_address": wallet_address
        }
        
        # Store profile and alias mapping
        self.profiles[wallet_address] = profile
        self.alias_to_address[alias.lower()] = wallet_address
        
        return {
            "success": True,
            "profile": profile,
            "transaction_hash": self._generate_tx_hash(wallet_address, alias)
        }
    
    def get_profile(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        """Get profile by wallet address"""
        return self.profiles.get(wallet_address)
    
    def get_profile_by_alias(self, alias: str) -> Optional[Dict[str, Any]]:
        """Get profile by alias"""
        address = self.alias_to_address.get(alias.lower())
        if address:
            return self.profiles.get(address)
        return None
    
    def update_profile_image(self, wallet_address: str, new_ipfs_hash: str) -> Dict[str, Any]:
        """Update only the profile image"""
        if wallet_address not in self.profiles:
            return {"success": False, "error": "Profile not found"}
        
        if not self._validate_ipfs_hash(new_ipfs_hash):
            return {"success": False, "error": "Invalid IPFS hash format"}
        
        self.profiles[wallet_address]["ipfs_image_hash"] = new_ipfs_hash
        self.profiles[wallet_address]["updated_at"] = int(time.time())
        
        return {
            "success": True,
            "profile": self.profiles[wallet_address]
        }
    
    def search_profiles(self, query: str, limit: int = 10) -> list:
        """Search profiles by alias or bio"""
        results = []
        query_lower = query.lower()
        
        for profile in self.profiles.values():
            if (query_lower in profile.get('alias', '').lower() or 
                query_lower in profile.get('bio', '').lower()):
                results.append(profile)
                
            if len(results) >= limit:
                break
                
        return results
    
    def _validate_ipfs_hash(self, ipfs_hash: str) -> bool:
        """Validate IPFS hash format"""
        if not ipfs_hash:
            return False
        
        # Basic IPFS hash validation (starts with Qm and is 46 characters)
        if ipfs_hash.startswith('Qm') and len(ipfs_hash) == 46:
            return True
        
        # CID v1 format validation (longer hashes)
        if len(ipfs_hash) > 46 and ipfs_hash.startswith(('bafy', 'bafk', 'bafz')):
            return True
            
        return False
    
    def _generate_tx_hash(self, wallet_address: str, alias: str) -> str:
        """Generate a mock transaction hash"""
        data = f"{wallet_address}{alias}{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, int]:
        """Get profile system statistics"""
        return {
            "total_profiles": len(self.profiles),
            "total_aliases": len(self.alias_to_address),
            "profiles_with_images": len([p for p in self.profiles.values() if p.get('ipfs_image_hash')])
        }