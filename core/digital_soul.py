"""
Digital Soul Smart Contract - GlobalCoyn Blockchain
Creates and manages autonomous AI entities on the blockchain
"""

import hashlib
import json
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from soul_ai import SoulAI

class DigitalSoulContract:
    """
    Smart contract for managing Digital Souls on the blockchain.
    Each Digital Soul is an autonomous AI entity with its own wallet and personality.
    """
    
    def __init__(self, blockchain_instance):
        self.blockchain = blockchain_instance
        self.souls = {}  # soul_id -> soul_data
        self.creator_souls = {}  # creator_wallet -> [soul_ids]
        self.soul_interactions = {}  # soul_id -> [interaction_records]
        self.soul_usernames = {}  # username -> soul_id (for unique username lookup)
        self.username_souls = {}  # soul_id -> username (reverse lookup)
        
        # Initialize AI engine for personality generation and interactions
        self.ai_engine = SoulAI()
        
    def create_soul(self, creator_wallet: str, soul_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new Digital Soul on the blockchain
        
        Args:
            creator_wallet: Wallet address of the soul creator
            soul_data: Dictionary containing soul information
                - name: Soul's name
                - username: Unique username for the soul
                - description: Soul description
                - personality_traits: List of personality traits
                - training_data_hash: IPFS hash of training data
                - avatar_preferences: Avatar generation preferences
                - interaction_price: GCN cost per minute of interaction
                - privacy_setting: 'public', 'friends', 'private'
                
        Returns:
            Dictionary with soul creation result
        """
        
        # Validate and check username uniqueness
        username = soul_data.get('username', '').lower().strip()
        if not username:
            return {
                'success': False,
                'error': 'Username is required',
                'soul_id': None
            }
        
        if not self._is_valid_username(username):
            return {
                'success': False,
                'error': 'Username must be 3-20 characters, alphanumeric and underscores only',
                'soul_id': None
            }
        
        if username in self.soul_usernames:
            return {
                'success': False,
                'error': 'Username already taken',
                'soul_id': None
            }
        
        # Generate unique soul ID
        soul_id = self._generate_soul_id(creator_wallet, soul_data['name'])
        
        # Validate soul data
        validation_result = self._validate_soul_data(soul_data)
        if not validation_result['valid']:
            return {
                'success': False,
                'error': validation_result['error'],
                'soul_id': None
            }
        
        # Check if creator has sufficient GCN for creation
        creation_cost = self._calculate_creation_cost(soul_data)
        creator_balance = self.blockchain.get_balance(creator_wallet)
        
        if creator_balance < creation_cost:
            return {
                'success': False,
                'error': f'Insufficient balance. Need {creation_cost} GCN, have {creator_balance} GCN',
                'soul_id': None
            }
        
        # Create soul record
        soul_record = {
            'soul_id': soul_id,
            'creator_wallet': creator_wallet,
            'name': soul_data['name'],
            'username': username,
            'description': soul_data['description'],
            'personality_traits': soul_data['personality_traits'],
            'training_data_hash': soul_data['training_data_hash'],
            'avatar_model_hash': None,  # Set after 3D generation
            'voice_model_hash': None,   # Set after voice training
            'interaction_price': soul_data['interaction_price'],
            'privacy_setting': soul_data['privacy_setting'],
            'creation_timestamp': int(time.time()),
            'status': 'training',  # training -> ready -> active -> paused
            'total_interactions': 0,
            'total_earnings': 0,
            'reputation_score': 0,
            'autonomy_level': 'moderate',  # low, moderate, high
            'last_activity': int(time.time()),
            'ai_model_version': '1.0',
            'creation_cost': creation_cost
        }
        
        # Store soul data
        self.souls[soul_id] = soul_record
        
        # Store username mappings
        self.soul_usernames[username] = soul_id
        self.username_souls[soul_id] = username
        
        # Update creator's souls list
        if creator_wallet not in self.creator_souls:
            self.creator_souls[creator_wallet] = []
        self.creator_souls[creator_wallet].append(soul_id)
        
        # Initialize interaction history
        self.soul_interactions[soul_id] = []
        
        # Record payment requirement for soul creation cost
        platform_address = "1LVkyzYqPBYYhMEjxFm1dLXsFUox2gtdDr"  # Platform wallet
        
        # Store payment information for later processing
        # The actual payment will be handled by the frontend using the wallet service
        payment_requirement = {
            'sender': creator_wallet,
            'recipient': platform_address,
            'amount': creation_cost,
            'fee': 0.001,
            'purpose': 'soul_creation_payment',
            'soul_id': soul_id,
            'status': 'required'
        }
        
        # Create blockchain transaction for soul creation
        transaction_data = {
            'type': 'SOUL_CREATE',
            'soul_id': soul_id,
            'creator': creator_wallet,
            'creation_cost': creation_cost,
            'training_data_hash': soul_data['training_data_hash'],
            'interaction_price': soul_data['interaction_price'],
            'timestamp': int(time.time())
        }
        
        # Start AI training in background (async in real implementation)
        self._start_ai_training(soul_id, soul_data)
        
        return {
            'success': True,
            'soul_id': soul_id,
            'creator_wallet': creator_wallet,
            'creation_cost': creation_cost,
            'payment_requirement': payment_requirement,
            'transaction_data': transaction_data,
            'soul_record': soul_record
        }
    
    def update_soul_models(self, soul_id: str, model_updates: Dict[str, str]) -> Dict[str, Any]:
        """
        Update soul's AI models after training completion
        
        Args:
            soul_id: Soul identifier
            model_updates: Dictionary containing model hashes
                - avatar_model_hash: IPFS hash of 3D avatar
                - voice_model_hash: IPFS hash of voice model
                - ai_model_hash: IPFS hash of personality AI model
        """
        
        if soul_id not in self.souls:
            return {'success': False, 'error': 'Soul not found'}
        
        soul = self.souls[soul_id]
        
        # Update model hashes
        if 'avatar_model_hash' in model_updates:
            soul['avatar_model_hash'] = model_updates['avatar_model_hash']
        
        if 'voice_model_hash' in model_updates:
            soul['voice_model_hash'] = model_updates['voice_model_hash']
        
        if 'ai_model_hash' in model_updates:
            soul['ai_model_hash'] = model_updates['ai_model_hash']
        
        # Update status to ready if all models are available
        if (soul['avatar_model_hash'] and 
            soul['voice_model_hash'] and 
            soul.get('ai_model_hash')):
            soul['status'] = 'ready'
        
        soul['last_activity'] = int(time.time())
        
        # Create blockchain transaction for model update
        transaction_data = {
            'type': 'SOUL_UPDATE',
            'soul_id': soul_id,
            'model_updates': model_updates,
            'new_status': soul['status'],
            'timestamp': int(time.time())
        }
        
        return {
            'success': True,
            'soul_id': soul_id,
            'new_status': soul['status'],
            'transaction_data': transaction_data
        }
    
    def interact_with_soul(self, user_wallet: str, soul_id: str, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record an interaction with a Digital Soul
        
        Args:
            user_wallet: Wallet of the user interacting
            soul_id: Soul being interacted with
            interaction_data: Interaction details
                - conversation_hash: IPFS hash of conversation
                - duration_minutes: Length of interaction
                - interaction_type: 'chat', 'consultation', 'collaboration'
                - payment_amount: GCN paid for interaction
        """
        
        if soul_id not in self.souls:
            return {'success': False, 'error': 'Soul not found'}
        
        soul = self.souls[soul_id]
        
        if soul['status'] != 'ready' and soul['status'] != 'active':
            return {'success': False, 'error': 'Soul is not available for interactions'}
        
        # Calculate interaction cost
        expected_cost = soul['interaction_price'] * interaction_data['duration_minutes']
        
        if interaction_data['payment_amount'] < expected_cost:
            return {
                'success': False, 
                'error': f'Insufficient payment. Expected {expected_cost} GCN'
            }
        
        # Check user balance
        user_balance = self.blockchain.get_balance(user_wallet)
        if user_balance < interaction_data['payment_amount']:
            return {'success': False, 'error': 'Insufficient user balance'}
        
        # Process payment - all goes to creator's wallet
        creator_wallet = soul['creator_wallet']
        payment_amount = interaction_data['payment_amount']
        
        # Platform takes a small fee (5%), rest goes to creator
        platform_fee = int(payment_amount * 0.05)
        creator_payment = payment_amount - platform_fee
        
        # Transfer payment to creator
        self.blockchain.transfer_funds(user_wallet, creator_wallet, creator_payment)
        
        # Transfer platform fee to platform wallet
        if platform_fee > 0:
            platform_address = "1LVkyzYqPBYYhMEjxFm1dLXsFUox2gtdDr"  # Platform wallet
            self.blockchain.transfer_funds(user_wallet, platform_address, platform_fee)
        
        # Record interaction
        interaction_record = {
            'interaction_id': str(uuid.uuid4()),
            'user_wallet': user_wallet,
            'soul_id': soul_id,
            'conversation_hash': interaction_data['conversation_hash'],
            'duration_minutes': interaction_data['duration_minutes'],
            'interaction_type': interaction_data['interaction_type'],
            'payment_amount': interaction_data['payment_amount'],
            'timestamp': int(time.time())
        }
        
        # Update soul statistics
        soul['total_interactions'] += 1
        soul['total_earnings'] += creator_payment
        soul['last_activity'] = int(time.time())
        soul['status'] = 'active'
        
        # Update reputation based on interaction
        self._update_soul_reputation(soul_id, interaction_data)
        
        # Store interaction
        self.soul_interactions[soul_id].append(interaction_record)
        
        # Create blockchain transaction
        transaction_data = {
            'type': 'SOUL_INTERACTION',
            'soul_id': soul_id,
            'user_wallet': user_wallet,
            'conversation_hash': interaction_data['conversation_hash'],
            'payment_amount': interaction_data['payment_amount'],
            'duration_minutes': interaction_data['duration_minutes'],
            'timestamp': int(time.time())
        }
        
        return {
            'success': True,
            'interaction_id': interaction_record['interaction_id'],
            'creator_payment': creator_payment,
            'platform_fee': platform_fee,
            'transaction_data': transaction_data
        }
    
    def autonomous_soul_action(self, soul_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an autonomous action by a Digital Soul
        
        Args:
            soul_id: Soul performing the action
            action_data: Action details
                - action_type: 'transfer', 'interact', 'create_content', 'invest'
                - target: Target of the action (wallet, soul_id, etc.)
                - amount: GCN amount (if applicable)
                - data_hash: IPFS hash of action data
        """
        
        if soul_id not in self.souls:
            return {'success': False, 'error': 'Soul not found'}
        
        soul = self.souls[soul_id]
        
        if soul['status'] != 'active':
            return {'success': False, 'error': 'Soul is not active'}
        
        # Validate soul has sufficient autonomy level
        if not self._validate_autonomy_action(soul, action_data):
            return {'success': False, 'error': 'Action not permitted with current autonomy level'}
        
        # Check creator balance if action requires payment
        creator_wallet = soul['creator_wallet']
        if 'amount' in action_data and action_data['amount'] > 0:
            creator_balance = self.blockchain.get_balance(creator_wallet)
            if creator_balance < action_data['amount']:
                return {'success': False, 'error': 'Insufficient creator balance for autonomous action'}
        
        # Process different action types
        result = self._process_autonomous_action(soul_id, action_data)
        
        if result['success']:
            # Update soul activity
            soul['last_activity'] = int(time.time())
            
            # Create blockchain transaction
            transaction_data = {
                'type': 'SOUL_AUTONOMOUS_ACTION',
                'soul_id': soul_id,
                'action_type': action_data['action_type'],
                'target': action_data.get('target'),
                'amount': action_data.get('amount', 0),
                'data_hash': action_data.get('data_hash'),
                'timestamp': int(time.time())
            }
            
            result['transaction_data'] = transaction_data
        
        return result
    
    def get_soul_data(self, soul_id: str) -> Optional[Dict[str, Any]]:
        """Get complete soul data"""
        return self.souls.get(soul_id)
    
    def get_souls_by_creator(self, creator_wallet: str) -> List[Dict[str, Any]]:
        """Get all souls created by a specific wallet"""
        soul_ids = self.creator_souls.get(creator_wallet, [])
        return [self.souls[soul_id] for soul_id in soul_ids if soul_id in self.souls]
    
    def get_public_souls(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get public souls available for interaction"""
        public_souls = []
        for soul in self.souls.values():
            if soul['privacy_setting'] == 'public' and soul['status'] in ['training', 'ready', 'active']:
                # Remove sensitive data for public view
                public_soul = {
                    'soul_id': soul['soul_id'],
                    'name': soul['name'],
                    'username': soul['username'],
                    'description': soul['description'],
                    'personality_traits': soul['personality_traits'],
                    'interaction_price': soul['interaction_price'],
                    'total_interactions': soul['total_interactions'],
                    'reputation_score': soul['reputation_score'],
                    'avatar_model_hash': soul['avatar_model_hash'],
                    'creation_timestamp': soul['creation_timestamp'],
                    'last_activity': soul['last_activity'],
                    'status': soul['status'],
                    'creator_wallet': soul['creator_wallet']
                }
                public_souls.append(public_soul)
        
        # Sort by reputation and recent activity
        public_souls.sort(key=lambda x: (x['reputation_score'], x['last_activity']), reverse=True)
        return public_souls[:limit]
    
    def get_soul_interactions(self, soul_id: str) -> List[Dict[str, Any]]:
        """Get interaction history for a soul"""
        return self.soul_interactions.get(soul_id, [])
    
    # Private helper methods
    
    def _generate_soul_id(self, creator_wallet: str, soul_name: str) -> str:
        """Generate unique soul ID"""
        data = f"{creator_wallet}{soul_name}{time.time()}{uuid.uuid4()}"
        return f"soul_{hashlib.sha256(data.encode()).hexdigest()[:16]}"
    
    
    def _validate_soul_data(self, soul_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate soul creation data"""
        required_fields = ['name', 'description', 'personality_traits', 'training_data_hash', 'interaction_price']
        
        for field in required_fields:
            if field not in soul_data:
                return {'valid': False, 'error': f'Missing required field: {field}'}
        
        if not soul_data['name'].strip():
            return {'valid': False, 'error': 'Soul name cannot be empty'}
        
        if len(soul_data['personality_traits']) < 3:
            return {'valid': False, 'error': 'At least 3 personality traits required'}
        
        if soul_data['interaction_price'] < 1:
            return {'valid': False, 'error': 'Interaction price must be at least 1 GCN'}
        
        return {'valid': True}
    
    def _calculate_creation_cost(self, soul_data: Dict[str, Any]) -> int:
        """Calculate GCN cost for soul creation"""
        base_cost = 300  # AI training
        voice_cost = 150  # Voice cloning
        avatar_cost = 100  # 3D avatar
        storage_cost = 50  # Blockchain storage
        
        # Additional costs based on features
        premium_traits = len([t for t in soul_data['personality_traits'] if t in ['Creative', 'Analytical', 'Technical']])
        premium_cost = premium_traits * 25
        
        return base_cost + voice_cost + avatar_cost + storage_cost + premium_cost
    
    def _update_soul_reputation(self, soul_id: str, interaction_data: Dict[str, Any]) -> None:
        """Update soul reputation based on interaction"""
        soul = self.souls[soul_id]
        
        # Simple reputation algorithm based on interaction length and payment
        base_points = min(interaction_data['duration_minutes'], 30)  # Cap at 30 minutes
        payment_bonus = min(interaction_data['payment_amount'] // 10, 20)  # Bonus for higher payments
        
        reputation_gain = base_points + payment_bonus
        
        # Apply reputation with diminishing returns
        current_rep = soul['reputation_score']
        decay_factor = max(0.5, 1.0 - (current_rep / 1000))  # Slower growth at higher reputation
        
        soul['reputation_score'] += int(reputation_gain * decay_factor)
    
    # AI Integration Methods
    
    def _start_ai_training(self, soul_id: str, soul_data: Dict[str, Any]) -> None:
        """
        Start AI training process for a newly created soul
        """
        try:
            # In a real implementation, this would be async
            # For now, we'll do synchronous training
            training_data = {
                'text_samples': [],  # Will be loaded from IPFS hash
                'personality_traits': soul_data.get('personality_traits', []),
                'description': soul_data.get('description', ''),
                'name': soul_data.get('name', '')
            }
            
            # Generate AI personality and living preferences
            result = self.ai_engine.generate_personality(soul_id, training_data)
            living_preferences = self.analyze_living_preferences(soul_data)
            
            if result['success']:
                # Update soul status to ready
                self.souls[soul_id]['status'] = 'ready'
                self.souls[soul_id]['ai_training_completed'] = int(time.time())
                self.souls[soul_id]['personality_quality_score'] = result['quality_score']
                self.souls[soul_id]['living_preferences'] = living_preferences
            else:
                self.souls[soul_id]['status'] = 'training_failed'
                self.souls[soul_id]['training_error'] = result.get('error', 'Unknown error')
                
        except Exception as e:
            self.souls[soul_id]['status'] = 'training_failed'
            self.souls[soul_id]['training_error'] = str(e)
    
    def chat_with_soul(self, soul_id: str, user_address: str, message: str) -> Dict[str, Any]:
        """
        Interact with a Digital Soul's AI
        
        Args:
            soul_id: Soul to chat with
            user_address: User's wallet address
            message: User's message
            
        Returns:
            Soul's AI response
        """
        if soul_id not in self.souls:
            return {'success': False, 'error': 'Soul not found'}
        
        soul = self.souls[soul_id]
        if soul['status'] != 'ready' and soul['status'] != 'active':
            return {'success': False, 'error': 'Soul is not ready for interactions'}
        
        # Use AI engine to generate response
        result = self.ai_engine.chat_with_soul(soul_id, message, user_address)
        
        if result['success']:
            # Update soul activity
            soul['last_activity'] = int(time.time())
            soul['status'] = 'active'
        
        return result
    
    def get_soul_ai_stats(self, soul_id: str) -> Dict[str, Any]:
        """
        Get AI statistics for a soul
        """
        if soul_id not in self.souls:
            return {'error': 'Soul not found'}
        
        soul_stats = self.ai_engine.get_soul_stats(soul_id)
        blockchain_stats = {
            'creation_date': self.souls[soul_id]['creation_timestamp'],
            'creator_wallet': self.souls[soul_id]['creator_wallet'],
            'total_earnings': self.souls[soul_id]['total_earnings'],
            'reputation_score': self.souls[soul_id]['reputation_score'],
            'interaction_price': self.souls[soul_id]['interaction_price']
        }
        
        return {**soul_stats, **blockchain_stats}
    
    def analyze_living_preferences(self, soul_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze living preferences from training data to generate world/environment
        
        Args:
            soul_data: Soul creation data including training data
            
        Returns:
            Dictionary containing living preferences for world generation
        """
        preferences = {
            'living_style': 'modern',  # modern, vintage, minimalist, artistic, rustic
            'color_preferences': {
                'primary': '#3B82F6',    # Blue
                'secondary': '#EF4444',  # Red
                'accent': '#10B981'      # Green
            },
            'activity_preferences': [],
            'social_level': 0.5,  # 0.0 = very introverted, 1.0 = very extroverted
            'wealth_level': 0.5,  # 0.0 = modest, 1.0 = luxurious
            'room_layout': 'studio',  # studio, one_bedroom, two_bedroom
            'furniture_style': 'modern',
            'hobbies': [],
            'work_environment': 'home_office'
        }
        
        # Extract from personality traits
        personality_traits = soul_data.get('personality_traits', [])
        description = soul_data.get('description', '').lower()
        
        # Analyze personality traits for living preferences
        for trait in personality_traits:
            trait_lower = trait.lower()
            
            # Living style preferences
            if trait_lower in ['creative', 'artistic']:
                preferences['living_style'] = 'artistic'
                preferences['furniture_style'] = 'eclectic'
                preferences['hobbies'].extend(['painting', 'music', 'writing'])
                preferences['color_preferences']['primary'] = '#8B5CF6'  # Purple
                
            elif trait_lower in ['organized', 'methodical', 'analytical']:
                preferences['living_style'] = 'minimalist'
                preferences['furniture_style'] = 'modern'
                preferences['work_environment'] = 'organized_office'
                preferences['color_preferences']['primary'] = '#6B7280'  # Gray
                
            elif trait_lower in ['adventurous', 'outdoorsy']:
                preferences['living_style'] = 'rustic'
                preferences['hobbies'].extend(['hiking', 'camping', 'sports'])
                preferences['color_preferences']['primary'] = '#059669'  # Green
                
            elif trait_lower in ['social', 'outgoing', 'friendly']:
                preferences['social_level'] = min(1.0, preferences['social_level'] + 0.3)
                preferences['room_layout'] = 'one_bedroom'  # Space for entertaining
                preferences['hobbies'].extend(['socializing', 'parties'])
                
            elif trait_lower in ['introverted', 'quiet', 'thoughtful']:
                preferences['social_level'] = max(0.0, preferences['social_level'] - 0.3)
                preferences['hobbies'].extend(['reading', 'meditation'])
                
            elif trait_lower in ['technical', 'geeky', 'programmer']:
                preferences['work_environment'] = 'tech_setup'
                preferences['hobbies'].extend(['gaming', 'coding', 'tech'])
                preferences['furniture_style'] = 'modern'
                
            elif trait_lower in ['luxurious', 'sophisticated', 'elegant']:
                preferences['wealth_level'] = min(1.0, preferences['wealth_level'] + 0.4)
                preferences['living_style'] = 'modern'
                preferences['room_layout'] = 'two_bedroom'
                
        # Analyze description for additional preferences
        if 'music' in description:
            preferences['hobbies'].append('music')
        if 'book' in description or 'read' in description:
            preferences['hobbies'].append('reading')
        if 'cook' in description or 'food' in description:
            preferences['hobbies'].append('cooking')
        if 'travel' in description:
            preferences['hobbies'].append('travel')
        if 'fitness' in description or 'gym' in description:
            preferences['hobbies'].append('fitness')
        if 'game' in description:
            preferences['hobbies'].append('gaming')
        
        # Color preferences based on description
        if 'blue' in description:
            preferences['color_preferences']['primary'] = '#3B82F6'
        elif 'red' in description:
            preferences['color_preferences']['primary'] = '#EF4444'
        elif 'green' in description:
            preferences['color_preferences']['primary'] = '#10B981'
        elif 'purple' in description:
            preferences['color_preferences']['primary'] = '#8B5CF6'
        elif 'pink' in description:
            preferences['color_preferences']['primary'] = '#EC4899'
        
        # Determine wealth level from interaction price
        interaction_price = soul_data.get('interaction_price', 5)
        if interaction_price >= 20:
            preferences['wealth_level'] = min(1.0, preferences['wealth_level'] + 0.3)
        elif interaction_price <= 3:
            preferences['wealth_level'] = max(0.0, preferences['wealth_level'] - 0.2)
        
        # Remove duplicates from hobbies
        preferences['hobbies'] = list(set(preferences['hobbies']))
        
        return preferences
    
    # Username Management Methods
    
    def get_soul_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get soul data by username"""
        username = username.lower().strip()
        if username in self.soul_usernames:
            soul_id = self.soul_usernames[username]
            return self.souls.get(soul_id)
        return None
    
    def get_username_by_soul_id(self, soul_id: str) -> Optional[str]:
        """Get username by soul ID"""
        return self.username_souls.get(soul_id)
    
    def is_username_available(self, username: str) -> bool:
        """Check if username is available"""
        username = username.lower().strip()
        return username not in self.soul_usernames
    
    def _is_valid_username(self, username: str) -> bool:
        """Validate username format"""
        import re
        if not username or len(username) < 3 or len(username) > 20:
            return False
        # Only allow alphanumeric characters and underscores
        return re.match(r'^[a-zA-Z0-9_]+$', username) is not None
    
    def _validate_autonomy_action(self, soul: Dict[str, Any], action_data: Dict[str, Any]) -> bool:
        """Validate if soul can perform autonomous action based on autonomy level"""
        autonomy_level = soul['autonomy_level']
        action_type = action_data['action_type']
        
        # Define action permissions by autonomy level
        permissions = {
            'low': ['interact'],
            'moderate': ['interact', 'transfer', 'create_content'],
            'high': ['interact', 'transfer', 'create_content', 'invest', 'collaborate']
        }
        
        return action_type in permissions.get(autonomy_level, [])
    
    def _process_autonomous_action(self, soul_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process specific autonomous action types"""
        soul = self.souls[soul_id]
        action_type = action_data['action_type']
        
        if action_type == 'transfer':
            # Soul transfers GCN from creator's wallet to another wallet
            target_wallet = action_data['target']
            amount = action_data['amount']
            creator_wallet = soul['creator_wallet']
            
            creator_balance = self.blockchain.get_balance(creator_wallet)
            if creator_balance >= amount:
                self.blockchain.transfer_funds(creator_wallet, target_wallet, amount)
                return {'success': True, 'message': f'Transferred {amount} GCN to {target_wallet}'}
            else:
                return {'success': False, 'error': 'Insufficient creator balance'}
        
        elif action_type == 'interact':
            # Soul initiates interaction with another soul
            target_soul_id = action_data['target']
            if target_soul_id in self.souls:
                # This would trigger an AI-to-AI conversation
                return {'success': True, 'message': f'Initiated interaction with {target_soul_id}'}
            else:
                return {'success': False, 'error': 'Target soul not found'}
        
        elif action_type == 'create_content':
            # Soul creates digital content
            content_hash = action_data['data_hash']
            return {'success': True, 'message': f'Created content: {content_hash}'}
        
        else:
            return {'success': False, 'error': f'Unknown action type: {action_type}'}
    
    def get_contract_state(self) -> Dict[str, Any]:
        """Get current state of the Digital Soul contract"""
        return {
            'total_souls': len(self.souls),
            'active_souls': len([s for s in self.souls.values() if s['status'] == 'active']),
            'total_interactions': sum(len(interactions) for interactions in self.soul_interactions.values()),
            'total_earnings': sum(soul['total_earnings'] for soul in self.souls.values()),
            'souls_by_status': {
                status: len([s for s in self.souls.values() if s['status'] == status])
                for status in ['training', 'ready', 'active', 'paused']
            }
        }