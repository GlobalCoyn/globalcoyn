from flask import Blueprint, request, jsonify
import logging
import re
import requests
import json
from datetime import datetime

# Note: Wallet service integration can be added later if needed

profile_bp = Blueprint('profile', __name__)
logger = logging.getLogger(__name__)

# IPFS configuration using the provided Pinata credentials
PINATA_JWT = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiJhNTE3MmY4Mi04NTkzLTQ2YjgtOWJhOC1kMDEzOGNhZTNmZTAiLCJlbWFpbCI6ImFkYW1uZXRvZGV2QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJwaW5fcG9saWN5Ijp7InJlZ2lvbnMiOlt7ImRlc2lyZWRSZXBsaWNhdGlvbkNvdW50IjoxLCJpZCI6IkZSQTEifSx7ImRlc2lyZWRSZXBsaWNhdGlvbkNvdW50IjoxLCJpZCI6Ik5ZQzEifV0sInZlcnNpb24iOjF9LCJtZmFfZW5hYmxlZCI6ZmFsc2UsInN0YXR1cyI6IkFDVElWRSJ9.eyJhdXRoZW50aWNhdGlvblR5cGUiOiJzY29wZWRLZXkiLCJzY29wZWRLZXlLZXkiOiIwNTg4MDNiMDM3MTM0MTFmN2JiOCIsInNjb3BlZEtleVNlY3JldCI6IjdiZTczYzNiZWNjM2Y4NmE0YWIzMGY3ODg3NjhiMmMyZjBhODExZTBkMzY5MGEyNTRjNTA0NTIxNDU3YWY3OGMiLCJleHAiOjE3Njc2MTg5MTR9.qd4PTUx5F9hJkRrq8PZsAT3qFh6-xhxSmhAq_VO9EYs'

# Fallback to API key/secret method
PINATA_API_KEY = '058803b03713411f7bb8'
PINATA_SECRET = '7be73c3becc3f86a4ab30f788768b2c2f0a811e0d3690a254c504521457af78c'

# In-memory profile storage (replace with blockchain contract integration)
profiles_db = {}

def is_valid_address(address):
    """Validate wallet address format (GlobalCoyn format)"""
    return bool(re.match(r'^[a-zA-Z0-9]{34,44}$', address))

def is_valid_ipfs_hash(hash_str):
    """Validate IPFS hash format"""
    return bool(re.match(r'^Qm[a-zA-Z0-9]{44}$|^baf[a-zA-Z0-9]{56}$', hash_str))

def is_valid_alias(alias):
    """Validate alias format"""
    return bool(re.match(r'^[a-zA-Z0-9_-]{3,20}$', alias))

@profile_bp.route('/profiles/<address>', methods=['GET'])
def get_profile(address):
    """Get profile by wallet address"""
    try:
        if not is_valid_address(address):
            return jsonify({
                'success': False,
                'error': 'Invalid wallet address format'
            }), 400

        # Check if profile exists in our storage
        if address not in profiles_db:
            return jsonify({
                'success': False,
                'error': 'Profile not found'
            }), 404

        profile = profiles_db[address]
        
        return jsonify({
            'success': True,
            'profile': {
                'walletAddress': address,
                'alias': profile['alias'],
                'bio': profile.get('bio', ''),
                'ipfsHash': profile.get('ipfsHash', ''),
                'lastUpdated': profile.get('lastUpdated', int(datetime.now().timestamp()))
            }
        })

    except Exception as e:
        logger.error(f"Error fetching profile for {address}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@profile_bp.route('/profiles', methods=['POST'])
def create_update_profile():
    """Create or update profile"""
    try:
        data = request.get_json()
        
        wallet_address = data.get('walletAddress')
        alias = data.get('alias')
        bio = data.get('bio', '')
        ipfs_hash = data.get('ipfsHash', '')

        # Validate required fields
        if not wallet_address or not alias:
            return jsonify({
                'success': False,
                'error': 'Wallet address and alias are required'
            }), 400

        # Validate wallet address
        if not is_valid_address(wallet_address):
            return jsonify({
                'success': False,
                'error': 'Invalid wallet address format'
            }), 400

        # Validate alias
        if not is_valid_alias(alias):
            return jsonify({
                'success': False,
                'error': 'Alias must be 3-20 characters and contain only letters, numbers, underscores, and hyphens'
            }), 400

        # Validate bio length
        if bio and len(bio) > 500:
            return jsonify({
                'success': False,
                'error': 'Bio must be less than 500 characters'
            }), 400

        # Validate IPFS hash if provided
        if ipfs_hash and not is_valid_ipfs_hash(ipfs_hash):
            return jsonify({
                'success': False,
                'error': 'Invalid IPFS hash format'
            }), 400

        # Check if alias is already taken by another address
        for addr, profile in profiles_db.items():
            if addr != wallet_address and profile.get('alias') == alias:
                return jsonify({
                    'success': False,
                    'error': 'Alias is already taken'
                }), 409

        # Store profile
        profile_data = {
            'alias': alias,
            'bio': bio,
            'ipfsHash': ipfs_hash,
            'lastUpdated': int(datetime.now().timestamp())
        }

        profiles_db[wallet_address] = profile_data

        # TODO: Store on blockchain via smart contract
        # This would integrate with the user_profiles.py contract

        return jsonify({
            'success': True,
            'message': 'Profile saved successfully',
            'profile': {
                'walletAddress': wallet_address,
                **profile_data
            },
            'transactionId': f'profile_tx_{int(datetime.now().timestamp())}'
        })

    except Exception as e:
        logger.error(f"Error saving profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to save profile: {str(e)}'
        }), 500

@profile_bp.route('/profiles/alias/<alias>/available', methods=['GET'])
def check_alias_availability(alias):
    """Check if alias is available"""
    try:
        if not is_valid_alias(alias):
            return jsonify({
                'success': False,
                'error': 'Invalid alias format'
            }), 400

        # Check if alias exists
        is_available = True
        for profile in profiles_db.values():
            if profile.get('alias') == alias:
                is_available = False
                break

        return jsonify({
            'success': True,
            'available': is_available
        })

    except Exception as e:
        logger.error(f"Error checking alias availability for {alias}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to check alias availability'
        }), 500

@profile_bp.route('/profiles/search/<query>', methods=['GET'])
def search_profiles(query):
    """Search profiles by alias"""
    try:
        limit = int(request.args.get('limit', 10))

        if not query or len(query) < 2:
            return jsonify({
                'success': False,
                'error': 'Search query must be at least 2 characters'
            }), 400

        results = []
        query_lower = query.lower()

        for address, profile in profiles_db.items():
            if query_lower in profile.get('alias', '').lower():
                results.append({
                    'walletAddress': address,
                    'alias': profile['alias'],
                    'bio': profile.get('bio', ''),
                    'ipfsHash': profile.get('ipfsHash', ''),
                    'lastUpdated': profile.get('lastUpdated', 0)
                })
                
                if len(results) >= limit:
                    break

        return jsonify({
            'success': True,
            'results': results,
            'total': len(results)
        })

    except Exception as e:
        logger.error(f"Error searching profiles with query {query}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to search profiles'
        }), 500

@profile_bp.route('/profiles/ipfs/upload', methods=['POST'])
def upload_to_ipfs():
    """Upload image to IPFS using Pinata"""
    try:
        data = request.get_json()
        image_data = data.get('imageData')
        file_name = data.get('fileName', 'profile-image.jpg')

        if not image_data:
            return jsonify({
                'success': False,
                'error': 'Image data is required'
            }), 400

        # Convert base64 to bytes
        import base64
        if image_data.startswith('data:'):
            base64_data = image_data.split(',')[1]
        else:
            base64_data = image_data
            
        image_bytes = base64.b64decode(base64_data)

        # Upload to Pinata IPFS
        files = {
            'file': (file_name, image_bytes, 'image/jpeg')
        }
        
        metadata = {
            'name': file_name,
            'keyvalues': {
                'type': 'profile-image',
                'uploadedAt': datetime.now().isoformat()
            }
        }
        
        data_payload = {
            'pinataMetadata': json.dumps(metadata),
            'pinataOptions': json.dumps({'cidVersion': 1})
        }

        # Try JWT first, then fallback to API key/secret
        headers_jwt = {
            'Authorization': f'Bearer {PINATA_JWT}'
        }
        
        headers_api_key = {
            'pinata_api_key': PINATA_API_KEY,
            'pinata_secret_api_key': PINATA_SECRET
        }

        # Try multiple upload methods with retry logic
        response = None
        last_error = None
        
        # Method 1: Try with API key/secret (more reliable)
        try:
            logger.info("Attempting IPFS upload with API key method")
            response = requests.post(
                'https://api.pinata.cloud/pinning/pinFileToIPFS',
                files=files,
                data=data_payload,
                headers=headers_api_key,
                timeout=45
            )
            
            if response.status_code == 200:
                logger.info("API key upload successful")
            else:
                logger.warning(f"API key upload failed with {response.status_code}: {response.text}")
                last_error = f"API key method failed: {response.status_code} - {response.text}"
                
        except Exception as api_error:
            logger.warning(f"API key upload failed: {api_error}")
            last_error = f"API key method error: {str(api_error)}"
            
        # Method 2: If API key failed, try JWT
        if not response or response.status_code != 200:
            try:
                logger.info("Attempting IPFS upload with JWT method")
                response = requests.post(
                    'https://api.pinata.cloud/pinning/pinFileToIPFS',
                    files=files,
                    data=data_payload,
                    headers=headers_jwt,
                    timeout=45
                )
                
                if response.status_code == 200:
                    logger.info("JWT upload successful")
                else:
                    logger.error(f"JWT upload also failed with {response.status_code}: {response.text}")
                    last_error = f"Both methods failed. JWT: {response.status_code} - {response.text}"
                    
            except Exception as jwt_error:
                logger.error(f"JWT upload also failed: {jwt_error}")
                last_error = f"Both methods failed. JWT error: {str(jwt_error)}"

        if response and response.status_code == 200:
            result = response.json()
            ipfs_hash = result['IpfsHash']
            image_url = f'https://gateway.pinata.cloud/ipfs/{ipfs_hash}'

            logger.info(f"IPFS upload successful: {ipfs_hash}")
            return jsonify({
                'success': True,
                'hash': ipfs_hash,
                'url': image_url
            })
        else:
            error_msg = last_error or f"Upload failed with status {response.status_code if response else 'None'}"
            logger.error(f"All IPFS upload methods failed: {error_msg}")
            return jsonify({
                'success': False,
                'error': f'Failed to upload image to IPFS: {error_msg}'
            }), 500

    except Exception as e:
        logger.error(f"Error uploading to IPFS: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to upload image to IPFS: {str(e)}'
        }), 500

@profile_bp.route('/profiles/<address>', methods=['DELETE'])
def delete_profile(address):
    """Delete profile"""
    try:
        if not is_valid_address(address):
            return jsonify({
                'success': False,
                'error': 'Invalid wallet address format'
            }), 400

        existed = address in profiles_db
        if existed:
            del profiles_db[address]

        # TODO: Delete from blockchain via smart contract

        return jsonify({
            'success': True,
            'message': 'Profile deleted successfully' if existed else 'Profile did not exist',
            'transactionId': f'delete_tx_{int(datetime.now().timestamp())}'
        })

    except Exception as e:
        logger.error(f"Error deleting profile for {address}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete profile: {str(e)}'
        }), 500