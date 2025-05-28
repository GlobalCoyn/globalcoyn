"""
Digital Soul API Routes for GlobalCoyn Node
Provides REST API endpoints for Digital Soul functionality
"""

from flask import Blueprint, request, jsonify
import logging
import time
import os
import hashlib
import json
from typing import Dict, Any, List
import requests
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
digital_soul_bp = Blueprint('digital_soul', __name__)

@digital_soul_bp.route('/status', methods=['GET'])
def get_status():
    """Simple status check for Digital Soul API"""
    return jsonify({
        "success": True, 
        "message": "Digital Soul API is running",
        "blockchain_available": get_blockchain() is not None
    }), 200

@digital_soul_bp.route('/check-username/<username>', methods=['GET'])
def check_username_availability(username):
    """Check if a username is available for Digital Soul creation"""
    try:
        blockchain = get_blockchain()
        if not blockchain:
            return jsonify({"error": "Blockchain not available"}), 500
        
        is_available = blockchain.digital_souls.is_username_available(username)
        is_valid = blockchain.digital_souls._is_valid_username(username)
        
        return jsonify({
            "success": True,
            "username": username,
            "available": is_available,
            "valid": is_valid,
            "message": "Username is available" if (is_available and is_valid) else 
                      "Username is invalid" if not is_valid else "Username is already taken"
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking username availability: {str(e)}")
        return jsonify({"error": str(e)}), 500

# IPFS configuration for soul data storage
PINATA_API_KEY = "058803b03713411f7bb8"
PINATA_SECRET_KEY = "7be73c3becc3f86a4ab30f788768b2c2f0a811e0d3690a254c504521457af78c"

def get_blockchain():
    """Get the blockchain instance from builtins"""
    import builtins
    try:
        return builtins.GCN.blockchain
    except AttributeError:
        logger.error("GCN not found in builtins. Digital Soul functionality not available.")
        return None

def upload_to_ipfs(data: bytes, filename: str) -> str:
    """
    Upload data to IPFS using Pinata service
    
    Args:
        data: File data as bytes
        filename: Name of the file
        
    Returns:
        IPFS hash of uploaded data
    """
    try:
        files = {
            'file': (filename, data, 'application/json')
        }
        
        metadata = {
            'name': filename,
            'keyvalues': {
                'type': 'digital-soul-training-data',
                'uploadedAt': time.strftime('%Y-%m-%dT%H:%M:%S')
            }
        }
        
        data_payload = {
            'pinataMetadata': json.dumps(metadata),
            'pinataOptions': json.dumps({'cidVersion': 1})
        }

        # Use API key/secret authentication (more reliable than JWT)
        headers_api_key = {
            'pinata_api_key': PINATA_API_KEY,
            'pinata_secret_api_key': PINATA_SECRET_KEY
        }
        
        logger.info("Attempting IPFS upload with API key method")
        response = requests.post(
            'https://api.pinata.cloud/pinning/pinFileToIPFS',
            files=files,
            data=data_payload,
            headers=headers_api_key,
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"IPFS upload successful: {result['IpfsHash']}")
            return result['IpfsHash']
        else:
            logger.error(f"IPFS upload failed: {response.status_code} - {response.text}")
            raise Exception(f"IPFS upload failed: {response.status_code} - {response.text}")
                
    except Exception as e:
        logger.error(f"Error uploading to IPFS: {str(e)}")
        raise

@digital_soul_bp.route('/create', methods=['POST'])
def create_digital_soul():
    """
    Create a new Digital Soul on the blockchain
    
    Expected JSON payload:
    {
        "creator_wallet": "wallet_address",
        "name": "Soul Name",
        "username": "unique_username",
        "description": "Soul description",
        "personality_traits": ["trait1", "trait2", "trait3"],
        "interaction_price": 5,
        "privacy_setting": "public",
        "training_data": {
            "text_samples": "base64_encoded_text_data",
            "audio_files": "base64_encoded_audio_data", 
            "photos": "base64_encoded_image_data"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        required_fields = ["creator_wallet", "name", "username", "description", "personality_traits"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create default training data (no file uploads required)
        logger.info("Creating default training data...")
        
        training_package = {
            "metadata": {
                "soul_name": data["name"],
                "description": data["description"],
                "personality_traits": data["personality_traits"],
                "creation_timestamp": int(time.time()),
                "creator": data["creator_wallet"]
            }
        }
        
        # Convert training package to JSON bytes
        training_json = json.dumps(training_package).encode('utf-8')
        training_filename = f"soul_{data['name']}_{int(time.time())}_metadata.json"
        
        try:
            training_data_hash = upload_to_ipfs(training_json, training_filename)
            logger.info(f"Training metadata uploaded to IPFS: {training_data_hash}")
        except Exception as e:
            logger.error(f"Failed to upload training metadata to IPFS: {str(e)}")
            return jsonify({"error": "Failed to upload training metadata to IPFS"}), 500
        
        # Prepare soul data for blockchain
        soul_data = {
            "name": data["name"],
            "username": data["username"],
            "description": data["description"],
            "personality_traits": data["personality_traits"],
            "training_data_hash": training_data_hash,
            "interaction_price": data.get("interaction_price", 5),
            "privacy_setting": data.get("privacy_setting", "public"),
            "creator_wallet": data["creator_wallet"]
        }
        
        # Create Digital Soul on blockchain
        blockchain = get_blockchain()
        if not blockchain:
            return jsonify({"error": "Blockchain not available"}), 500
            
        result = blockchain.digital_souls.create_soul(data["creator_wallet"], soul_data)
        
        if result["success"]:
            logger.info(f"Digital Soul created successfully: {result['soul_id']}")
            
            return jsonify({
                "success": True,
                "soul_id": result["soul_id"],
                "creator_wallet": result["creator_wallet"],
                "creation_cost": result["creation_cost"],
                "payment_requirement": result["payment_requirement"],
                "training_data_hash": training_data_hash,
                "status": "training",
                "message": "Digital Soul created successfully. Please complete payment to activate."
            }), 201
        else:
            logger.error(f"Failed to create Digital Soul: {result['error']}")
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        logger.error(f"Error creating Digital Soul: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@digital_soul_bp.route('/souls', methods=['GET'])
def get_all_souls():
    """Get all public Digital Souls available for interaction"""
    try:
        blockchain = get_blockchain()
        if not blockchain:
            return jsonify({"error": "Blockchain not available"}), 500
            
        public_souls = blockchain.digital_souls.get_public_souls()
        
        return jsonify({
            "success": True,
            "souls": public_souls,
            "count": len(public_souls)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting public souls: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@digital_soul_bp.route('/souls/creator/<creator_wallet>', methods=['GET'])
def get_souls_by_creator(creator_wallet):
    """Get all Digital Souls created by a specific wallet"""
    try:
        blockchain = get_blockchain()
        souls = blockchain.digital_souls.get_souls_by_creator(creator_wallet)
        
        return jsonify({
            "success": True,
            "souls": souls,
            "count": len(souls)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting souls by creator: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@digital_soul_bp.route('/soul/<username>', methods=['GET'])
def get_soul_by_username(username):
    """Get Digital Soul by username"""
    try:
        blockchain = get_blockchain()
        if not blockchain:
            return jsonify({"error": "Blockchain not available"}), 500
            
        soul_data = blockchain.digital_souls.get_soul_by_username(username)
        
        if not soul_data:
            return jsonify({
                "success": False,
                "error": "Soul not found"
            }), 404
        
        # Remove sensitive data for public API
        public_soul_data = {
            "soul_id": soul_data["soul_id"],
            "name": soul_data["name"],
            "username": soul_data["username"],
            "description": soul_data["description"],
            "personality_traits": soul_data["personality_traits"],
            "interaction_price": soul_data["interaction_price"],
            "status": soul_data["status"],
            "total_interactions": soul_data["total_interactions"],
            "reputation_score": soul_data["reputation_score"],
            "creation_timestamp": soul_data["creation_timestamp"],
            "last_activity": soul_data["last_activity"],
            "avatar_model_hash": soul_data.get("avatar_model_hash"),
            "privacy_setting": soul_data["privacy_setting"],
            "creator_wallet": soul_data["creator_wallet"]
        }
        
        return jsonify({
            "success": True,
            "soul": public_soul_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting soul by username {username}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@digital_soul_bp.route('/souls/<soul_id>', methods=['GET'])
def get_soul_details(soul_id):
    """Get detailed information about a specific Digital Soul"""
    try:
        blockchain = get_blockchain()
        soul_data = blockchain.digital_souls.get_soul_data(soul_id)
        
        if not soul_data:
            return jsonify({"error": "Soul not found"}), 404
        
        # Remove sensitive data for public API
        public_soul_data = {
            "soul_id": soul_data["soul_id"],
            "name": soul_data["name"],
            "description": soul_data["description"],
            "personality_traits": soul_data["personality_traits"],
            "interaction_price": soul_data["interaction_price"],
            "status": soul_data["status"],
            "total_interactions": soul_data["total_interactions"],
            "reputation_score": soul_data["reputation_score"],
            "creation_timestamp": soul_data["creation_timestamp"],
            "last_activity": soul_data["last_activity"],
            "avatar_model_hash": soul_data.get("avatar_model_hash"),
            "privacy_setting": soul_data["privacy_setting"]
        }
        
        return jsonify({
            "success": True,
            "soul": public_soul_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting soul details: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@digital_soul_bp.route('/souls/<soul_id>/interact', methods=['POST'])
def interact_with_soul(soul_id):
    """
    Interact with a Digital Soul
    
    Expected JSON payload:
    {
        "user_wallet": "wallet_address",
        "conversation_data": {
            "messages": [...],
            "ai_responses": [...]
        },
        "duration_minutes": 5,
        "interaction_type": "chat",
        "payment_amount": 25
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        required_fields = ["user_wallet", "conversation_data", "duration_minutes", "payment_amount"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Upload conversation data to IPFS
        logger.info("Uploading conversation data to IPFS...")
        
        conversation_package = {
            "soul_id": soul_id,
            "user_wallet": data["user_wallet"],
            "conversation_data": data["conversation_data"],
            "duration_minutes": data["duration_minutes"],
            "interaction_type": data.get("interaction_type", "chat"),
            "timestamp": int(time.time())
        }
        
        conversation_json = json.dumps(conversation_package).encode('utf-8')
        conversation_filename = f"conversation_{soul_id}_{int(time.time())}.json"
        
        try:
            conversation_hash = upload_to_ipfs(conversation_json, conversation_filename)
            logger.info(f"Conversation uploaded to IPFS: {conversation_hash}")
        except Exception as e:
            logger.error(f"Failed to upload conversation to IPFS: {str(e)}")
            return jsonify({"error": "Failed to upload conversation data"}), 500
        
        # Prepare interaction data
        interaction_data = {
            "conversation_hash": conversation_hash,
            "duration_minutes": data["duration_minutes"],
            "interaction_type": data.get("interaction_type", "chat"),
            "payment_amount": data["payment_amount"]
        }
        
        # Process interaction on blockchain
        blockchain = get_blockchain()
        result = blockchain.digital_souls.interact_with_soul(
            data["user_wallet"], 
            soul_id, 
            interaction_data
        )
        
        if result["success"]:
            logger.info(f"Soul interaction completed: {result['interaction_id']}")
            
            return jsonify({
                "success": True,
                "interaction_id": result["interaction_id"],
                "creator_payment": result["creator_payment"],
                "platform_fee": result["platform_fee"],
                "conversation_hash": conversation_hash,
                "message": "Interaction completed successfully"
            }), 200
        else:
            logger.error(f"Soul interaction failed: {result['error']}")
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        logger.error(f"Error processing soul interaction: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@digital_soul_bp.route('/souls/<soul_id>/update-models', methods=['POST'])
def update_soul_models(soul_id):
    """
    Update Digital Soul AI models after training completion
    
    Expected JSON payload:
    {
        "avatar_model_hash": "ipfs_hash",
        "voice_model_hash": "ipfs_hash", 
        "ai_model_hash": "ipfs_hash"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate at least one model hash is provided
        valid_models = ["avatar_model_hash", "voice_model_hash", "ai_model_hash"]
        model_updates = {k: v for k, v in data.items() if k in valid_models and v}
        
        if not model_updates:
            return jsonify({"error": "No valid model hashes provided"}), 400
        
        # Update models on blockchain
        blockchain = get_blockchain()
        result = blockchain.digital_souls.update_soul_models(soul_id, model_updates)
        
        if result["success"]:
            logger.info(f"Soul models updated: {soul_id}")
            
            return jsonify({
                "success": True,
                "soul_id": soul_id,
                "updated_models": list(model_updates.keys()),
                "new_status": result["new_status"],
                "message": "Soul models updated successfully"
            }), 200
        else:
            logger.error(f"Failed to update soul models: {result['error']}")
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        logger.error(f"Error updating soul models: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@digital_soul_bp.route('/souls/<soul_id>/autonomous-action', methods=['POST'])
def process_autonomous_action(soul_id):
    """
    Process an autonomous action by a Digital Soul
    
    Expected JSON payload:
    {
        "action_type": "transfer|interact|create_content",
        "target": "target_wallet_or_soul_id",
        "amount": 10,
        "data_hash": "ipfs_hash_of_action_data"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        if "action_type" not in data:
            return jsonify({"error": "Missing required field: action_type"}), 400
        
        # Process autonomous action
        blockchain = get_blockchain()
        result = blockchain.digital_souls.autonomous_soul_action(soul_id, data)
        
        if result["success"]:
            logger.info(f"Autonomous action completed: {soul_id} - {data['action_type']}")
            
            return jsonify({
                "success": True,
                "soul_id": soul_id,
                "action_type": data["action_type"],
                "message": result.get("message", "Autonomous action completed")
            }), 200
        else:
            logger.error(f"Autonomous action failed: {result['error']}")
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        logger.error(f"Error processing autonomous action: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@digital_soul_bp.route('/souls/<soul_id>/interactions', methods=['GET'])
def get_soul_interactions(soul_id):
    """Get interaction history for a Digital Soul"""
    try:
        blockchain = get_blockchain()
        interactions = blockchain.digital_souls.get_soul_interactions(soul_id)
        
        # Remove sensitive data from interactions
        public_interactions = []
        for interaction in interactions:
            public_interaction = {
                "interaction_id": interaction["interaction_id"],
                "duration_minutes": interaction["duration_minutes"],
                "interaction_type": interaction["interaction_type"],
                "payment_amount": interaction["payment_amount"],
                "timestamp": interaction["timestamp"]
            }
            public_interactions.append(public_interaction)
        
        return jsonify({
            "success": True,
            "soul_id": soul_id,
            "interactions": public_interactions,
            "count": len(public_interactions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting soul interactions: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@digital_soul_bp.route('/stats', methods=['GET'])
def get_digital_soul_stats():
    """Get overall Digital Soul platform statistics"""
    try:
        blockchain = get_blockchain()
        stats = blockchain.digital_souls.get_contract_state()
        
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting digital soul stats: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@digital_soul_bp.route('/ipfs/upload', methods=['POST'])
def upload_file_to_ipfs():
    """
    Upload a file directly to IPFS
    
    Expected: multipart/form-data with 'file' field
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Read file data
        file_data = file.read()
        
        # Upload to IPFS
        ipfs_hash = upload_to_ipfs(file_data, file.filename)
        
        return jsonify({
            "success": True,
            "ipfs_hash": ipfs_hash,
            "filename": file.filename,
            "size": len(file_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading file to IPFS: {str(e)}")
        return jsonify({"error": "Failed to upload file to IPFS"}), 500

# Payment Processing Route

@digital_soul_bp.route('/souls/<soul_id>/process-payment', methods=['POST'])
def process_soul_payment(soul_id):
    """Process payment for Digital Soul creation"""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        data = request.get_json()
        
        required_fields = ['transaction_id', 'payment_amount']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        blockchain = get_blockchain()
        if not blockchain:
            return jsonify({"error": "Blockchain not available"}), 500
        
        # Verify payment transaction exists and amount is correct
        # This would check the actual blockchain transaction
        # For now, we'll mark the soul as payment_complete
        
        soul = blockchain.digital_souls.get_soul_data(soul_id)
        if not soul:
            return jsonify({"error": "Soul not found"}), 404
        
        # Update soul status to indicate payment completed
        soul['payment_status'] = 'completed'
        soul['payment_transaction_id'] = data['transaction_id']
        soul['status'] = 'ready'  # Soul is now ready for interactions
        
        logger.info(f"Payment processed for soul {soul_id}: {data['transaction_id']}")
        
        return jsonify({
            "success": True,
            "soul_id": soul_id,
            "payment_status": "completed",
            "transaction_id": data['transaction_id'],
            "message": "Payment processed successfully. Soul is now active."
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing payment for soul {soul_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# World Generation Routes

@digital_soul_bp.route('/souls/<soul_id>/create-world', methods=['POST'])
def create_soul_world(soul_id):
    """Generate a minimal 3D world for a Digital Soul"""
    try:
        blockchain = get_blockchain()
        if not blockchain:
            return jsonify({"error": "Blockchain not available"}), 500
        
        # Get soul data
        soul = blockchain.digital_souls.get_soul_data(soul_id)
        if not soul:
            return jsonify({"error": "Soul not found"}), 404
        
        # Check if request wants neighborhood instead of single room
        try:
            data = request.get_json() or {}
        except Exception as json_error:
            logger.warning(f"Failed to parse JSON, using defaults: {str(json_error)}")
            data = {}
        
        world_type = data.get('world_type', 'room')  # 'room' or 'neighborhood'
        
        # Import world generator
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))
        
        if world_type == 'neighborhood':
            from neighborhood_generator import NeighborhoodGenerator
            
            # Generate neighborhood
            neighborhood_config = {
                'size': data.get('size', (2, 2)),  # Smaller for testing
                'district_type': data.get('district_type', 'mixed'),
                'population_density': data.get('population_density', 5)
            }
            
            neighborhood_generator = NeighborhoodGenerator()
            world_data = neighborhood_generator.create_neighborhood(neighborhood_config)
            filename = f"neighborhood_{soul_id}.json"
        else:
            from world_generator import MinimalWorldGenerator
            
            # Generate single room world
            world_generator = MinimalWorldGenerator()
            world_data = world_generator.create_basic_world(soul)
            filename = f"world_{soul_id}.json"
        
        # Store world data in IPFS
        world_json = json.dumps(world_data, indent=2)
        world_hash = upload_to_ipfs(world_json.encode(), filename)
        
        # Update soul with world reference
        soul['world_hash'] = world_hash
        soul['world_generated'] = True
        soul['world_generation_timestamp'] = int(time.time())
        soul['world_type'] = world_type
        
        logger.info(f"{world_type.title()} generated for soul {soul_id}: {world_hash}")
        
        return jsonify({
            "success": True,
            "soul_id": soul_id,
            "world_hash": world_hash,
            "world_data": world_data,
            "world_type": world_type,
            "message": f"{world_type.title()} generated successfully"
        }), 200
        
    except Exception as e:
        world_type = getattr(locals(), 'data', {}).get('world_type', 'world')
        logger.error(f"Error generating {world_type} for soul {soul_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@digital_soul_bp.route('/souls/<soul_id>/world', methods=['GET'])
def get_soul_world(soul_id):
    """Get the 3D world data for a Digital Soul"""
    try:
        blockchain = get_blockchain()
        if not blockchain:
            return jsonify({"error": "Blockchain not available"}), 500
        
        # Get soul data
        soul = blockchain.digital_souls.get_soul_data(soul_id)
        if not soul:
            return jsonify({"error": "Soul not found"}), 404
        
        # Check if world exists
        if not soul.get('world_hash'):
            return jsonify({
                "success": False,
                "error": "World not generated yet",
                "world_exists": False
            }), 404
        
        # Fetch world data from IPFS
        world_hash = soul['world_hash']
        try:
            world_data_response = requests.get(f"https://gateway.pinata.cloud/ipfs/{world_hash}")
            if world_data_response.status_code == 200:
                world_data = world_data_response.json()
            else:
                return jsonify({"error": "Could not fetch world data from IPFS"}), 500
        except Exception as e:
            logger.error(f"Error fetching world data from IPFS: {str(e)}")
            return jsonify({"error": "Could not load world data"}), 500
        
        return jsonify({
            "success": True,
            "soul_id": soul_id,
            "world_hash": world_hash,
            "world_data": world_data,
            "world_exists": True
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting world for soul {soul_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@digital_soul_bp.route('/souls/<soul_id>/world/behavior', methods=['GET'])
def get_soul_behavior(soul_id):
    """Get current autonomous behavior state of a Digital Soul"""
    try:
        blockchain = get_blockchain()
        if not blockchain:
            return jsonify({"error": "Blockchain not available"}), 500
        
        # Get soul and world data
        soul = blockchain.digital_souls.get_soul_data(soul_id)
        if not soul:
            return jsonify({"error": "Soul not found"}), 404
        
        if not soul.get('world_hash'):
            return jsonify({"error": "Soul has no world generated"}), 404
        
        # Get world data
        world_hash = soul['world_hash']
        world_data_response = requests.get(f"https://gateway.pinata.cloud/ipfs/{world_hash}")
        if world_data_response.status_code != 200:
            return jsonify({"error": "Could not fetch world data"}), 500
        
        world_data = world_data_response.json()
        
        # Initialize or get existing behavior system
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))
        from world_generator import BasicSoulBehavior
        
        # Create behavior system
        behavior_system = BasicSoulBehavior(soul, world_data)
        
        # Get next action
        next_action = behavior_system.get_next_action()
        current_state = behavior_system.get_current_state()
        
        return jsonify({
            "success": True,
            "soul_id": soul_id,
            "current_state": current_state,
            "next_action": next_action,
            "timestamp": int(time.time())
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting soul behavior {soul_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


@digital_soul_bp.route('/neighborhood/create', methods=['POST'])
def create_neighborhood():
    """Generate a new neighborhood with multiple buildings and streets"""
    try:
        data = request.get_json() or {}
        
        # Import neighborhood generator
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))
        from neighborhood_generator import NeighborhoodGenerator
        
        # Default neighborhood configuration
        neighborhood_config = {
            'size': data.get('size', (3, 3)),  # 3x3 blocks
            'district_type': data.get('district_type', 'mixed'),
            'population_density': data.get('population_density', 10),
            'real_world_location': data.get('real_world_location')
        }
        
        # Generate neighborhood
        neighborhood_generator = NeighborhoodGenerator()
        neighborhood_data = neighborhood_generator.create_neighborhood(neighborhood_config)
        
        # Store neighborhood data in IPFS
        neighborhood_json = json.dumps(neighborhood_data, indent=2)
        neighborhood_hash = upload_to_ipfs(neighborhood_json.encode(), 
                                         f"neighborhood_{neighborhood_data['neighborhood_id']}.json")
        
        logger.info(f"Neighborhood generated: {neighborhood_data['neighborhood_id']}")
        
        return jsonify({
            "success": True,
            "neighborhood_id": neighborhood_data['neighborhood_id'],
            "neighborhood_hash": neighborhood_hash,
            "neighborhood_data": neighborhood_data,
            "message": "Neighborhood generated successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating neighborhood: {str(e)}")
        return jsonify({"error": str(e)}), 500

@digital_soul_bp.route('/neighborhood/<neighborhood_id>', methods=['GET'])
def get_neighborhood(neighborhood_id):
    """Get neighborhood data by ID"""
    try:
        # In a real implementation, this would query a database
        # For now, return error since we don't have persistence
        return jsonify({
            "success": False,
            "error": "Neighborhood persistence not implemented yet",
            "neighborhood_id": neighborhood_id
        }), 404
        
    except Exception as e:
        logger.error(f"Error getting neighborhood {neighborhood_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@digital_soul_bp.route('/souls/username/<username>/world', methods=['GET'])
def get_soul_world_by_username(username):
    """Get the 3D world data for a Digital Soul by username"""
    try:
        blockchain = get_blockchain()
        if not blockchain:
            return jsonify({"error": "Blockchain not available"}), 500
        
        # Get soul by username
        soul = blockchain.digital_souls.get_soul_by_username(username)
        if not soul:
            return jsonify({"error": "Soul not found"}), 404
        
        # Get world data using soul_id
        return get_soul_world(soul['soul_id'])
        
    except Exception as e:
        logger.error(f"Error getting world for soul username {username}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# AI Interaction Routes

@digital_soul_bp.route('/souls/<soul_id>/chat', methods=['POST'])
def chat_with_soul(soul_id):
    """Chat with a Digital Soul's AI"""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        data = request.get_json()
        
        required_fields = ['user_address', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        blockchain = get_blockchain()
        if not blockchain:
            return jsonify({"error": "Blockchain not available"}), 500
        
        # Chat with the soul's AI
        result = blockchain.digital_souls.chat_with_soul(
            soul_id=soul_id,
            user_address=data['user_address'],
            message=data['message']
        )
        
        if result['success']:
            return jsonify({
                "success": True,
                "response": result['response'],
                "interaction_id": result['interaction_id'],
                "timestamp": result['timestamp']
            })
        else:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Error chatting with soul {soul_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@digital_soul_bp.route('/souls/<soul_id>/ai-stats', methods=['GET'])
def get_soul_ai_stats(soul_id):
    """Get AI statistics for a Digital Soul"""
    try:
        blockchain = get_blockchain()
        if not blockchain:
            return jsonify({"error": "Blockchain not available"}), 500
        
        stats = blockchain.digital_souls.get_soul_ai_stats(soul_id)
        
        if 'error' in stats:
            return jsonify({
                "success": False,
                "error": stats['error']
            }), 404
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Error getting soul AI stats {soul_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Error handlers
@digital_soul_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@digital_soul_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@digital_soul_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500