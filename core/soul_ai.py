"""
AI Integration module for Digital Souls
Handles personality generation, training, and interactions with Claude API
"""
import json
import time
import hashlib
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

class SoulAI:
    """
    AI engine for Digital Souls - handles personality generation and interactions
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Soul AI engine
        
        Args:
            api_key: Claude API key for AI interactions (optional for testing)
        """
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-sonnet-20240229"
        
        # In-memory storage for AI personalities and chat histories
        self.personalities = {}  # soul_id -> personality_data
        self.chat_histories = {}  # soul_id -> list of conversations
        self.training_status = {}  # soul_id -> training status
        
    def generate_personality(self, soul_id: str, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI personality from training data
        
        Args:
            soul_id: Unique soul identifier
            training_data: Dictionary containing text samples, personality traits, etc.
            
        Returns:
            Generated personality profile
        """
        try:
            # Extract training information
            text_samples = training_data.get('text_samples', [])
            personality_traits = training_data.get('personality_traits', [])
            creator_description = training_data.get('description', '')
            
            # Analyze text samples to extract personality patterns
            personality_analysis = self._analyze_text_patterns(text_samples)
            
            # Generate comprehensive personality profile
            personality_profile = {
                'soul_id': soul_id,
                'created_at': int(time.time()),
                'personality_traits': personality_traits,
                'communication_style': personality_analysis.get('communication_style', 'friendly'),
                'interests': personality_analysis.get('interests', []),
                'knowledge_domains': personality_analysis.get('knowledge_domains', []),
                'response_patterns': personality_analysis.get('response_patterns', {}),
                'emotional_tendencies': personality_analysis.get('emotional_tendencies', 'balanced'),
                'interaction_preferences': {
                    'formality_level': personality_analysis.get('formality_level', 'casual'),
                    'humor_style': personality_analysis.get('humor_style', 'light'),
                    'conversation_depth': personality_analysis.get('conversation_depth', 'moderate')
                },
                'training_quality_score': self._calculate_training_quality(training_data),
                'autonomy_settings': {
                    'can_initiate_conversations': True,
                    'can_learn_from_interactions': True,
                    'response_delay_range': [1, 5],  # seconds
                    'personality_drift_rate': 0.01  # how much personality can evolve
                }
            }
            
            # Store personality
            self.personalities[soul_id] = personality_profile
            self.chat_histories[soul_id] = []
            self.training_status[soul_id] = 'completed'
            
            logger.info(f"Generated personality for soul {soul_id} with quality score {personality_profile['training_quality_score']}")
            
            return {
                'success': True,
                'personality_profile': personality_profile,
                'training_status': 'completed',
                'quality_score': personality_profile['training_quality_score']
            }
            
        except Exception as e:
            logger.error(f"Error generating personality for soul {soul_id}: {str(e)}")
            self.training_status[soul_id] = 'failed'
            return {
                'success': False,
                'error': str(e),
                'training_status': 'failed'
            }
    
    def chat_with_soul(self, soul_id: str, user_message: str, user_address: str) -> Dict[str, Any]:
        """
        Have a conversation with a digital soul
        
        Args:
            soul_id: Soul to chat with
            user_message: Message from user
            user_address: Wallet address of user
            
        Returns:
            Soul's response and interaction data
        """
        try:
            if soul_id not in self.personalities:
                return {
                    'success': False,
                    'error': 'Soul not found or not trained yet'
                }
            
            personality = self.personalities[soul_id]
            
            # Get chat history for context
            chat_history = self.chat_histories.get(soul_id, [])
            
            # Generate AI response based on personality
            ai_response = self._generate_ai_response(personality, user_message, chat_history)
            
            # Record interaction
            interaction = {
                'timestamp': int(time.time()),
                'user_address': user_address,
                'user_message': user_message,
                'soul_response': ai_response,
                'interaction_id': hashlib.sha256(f"{soul_id}{user_address}{time.time()}".encode()).hexdigest()[:16]
            }
            
            # Add to chat history (keep last 50 interactions)
            self.chat_histories[soul_id].append(interaction)
            if len(self.chat_histories[soul_id]) > 50:
                self.chat_histories[soul_id] = self.chat_histories[soul_id][-50:]
            
            logger.info(f"Soul {soul_id} interacted with user {user_address}")
            
            return {
                'success': True,
                'response': ai_response,
                'interaction_id': interaction['interaction_id'],
                'soul_id': soul_id,
                'timestamp': interaction['timestamp']
            }
            
        except Exception as e:
            logger.error(f"Error in soul chat {soul_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_soul_stats(self, soul_id: str) -> Dict[str, Any]:
        """
        Get interaction statistics for a soul
        
        Args:
            soul_id: Soul identifier
            
        Returns:
            Soul statistics and status
        """
        if soul_id not in self.personalities:
            return {'error': 'Soul not found'}
        
        personality = self.personalities[soul_id]
        chat_history = self.chat_histories.get(soul_id, [])
        
        # Calculate statistics
        total_interactions = len(chat_history)
        unique_users = len(set(interaction['user_address'] for interaction in chat_history))
        
        # Recent activity (last 24 hours)
        yesterday = int(time.time()) - 86400
        recent_interactions = [i for i in chat_history if i['timestamp'] > yesterday]
        
        return {
            'soul_id': soul_id,
            'personality_created': personality['created_at'],
            'training_status': self.training_status.get(soul_id, 'unknown'),
            'training_quality_score': personality['training_quality_score'],
            'total_interactions': total_interactions,
            'unique_users': unique_users,
            'recent_interactions_24h': len(recent_interactions),
            'last_interaction': chat_history[-1]['timestamp'] if chat_history else None,
            'personality_traits': personality['personality_traits'],
            'communication_style': personality['communication_style'],
            'status': 'active' if recent_interactions else 'idle'
        }
    
    def _analyze_text_patterns(self, text_samples: List[str]) -> Dict[str, Any]:
        """
        Analyze text samples to extract personality patterns
        
        Args:
            text_samples: List of text samples from user
            
        Returns:
            Analyzed personality patterns
        """
        if not text_samples:
            return {
                'communication_style': 'friendly',
                'formality_level': 'casual',
                'interests': [],
                'knowledge_domains': [],
                'response_patterns': {},
                'emotional_tendencies': 'balanced',
                'humor_style': 'light',
                'conversation_depth': 'moderate'
            }
        
        # Combine all text samples
        combined_text = ' '.join(text_samples).lower()
        
        # Simple pattern analysis (in production, would use more sophisticated NLP)
        word_count = len(combined_text.split())
        
        # Determine communication style
        formal_indicators = ['however', 'furthermore', 'therefore', 'consequently']
        casual_indicators = ['yeah', 'cool', 'awesome', 'lol', 'hey']
        
        formal_score = sum(1 for word in formal_indicators if word in combined_text)
        casual_score = sum(1 for word in casual_indicators if word in combined_text)
        
        communication_style = 'formal' if formal_score > casual_score else 'casual'
        formality_level = 'formal' if formal_score > casual_score else 'casual'
        
        # Detect interests and knowledge domains
        tech_keywords = ['technology', 'programming', 'software', 'computer', 'ai', 'blockchain']
        art_keywords = ['art', 'music', 'painting', 'creative', 'design']
        science_keywords = ['science', 'research', 'experiment', 'theory', 'analysis']
        
        interests = []
        knowledge_domains = []
        
        if any(keyword in combined_text for keyword in tech_keywords):
            interests.append('technology')
            knowledge_domains.append('technology')
        if any(keyword in combined_text for keyword in art_keywords):
            interests.append('arts')
            knowledge_domains.append('creative_arts')
        if any(keyword in combined_text for keyword in science_keywords):
            interests.append('science')
            knowledge_domains.append('scientific_research')
        
        # Emotional tendencies
        positive_words = ['happy', 'excited', 'love', 'great', 'awesome', 'wonderful']
        negative_words = ['sad', 'angry', 'frustrated', 'disappointed', 'terrible']
        
        positive_score = sum(1 for word in positive_words if word in combined_text)
        negative_score = sum(1 for word in negative_words if word in combined_text)
        
        if positive_score > negative_score * 1.5:
            emotional_tendencies = 'optimistic'
        elif negative_score > positive_score * 1.5:
            emotional_tendencies = 'cautious'
        else:
            emotional_tendencies = 'balanced'
        
        return {
            'communication_style': communication_style,
            'formality_level': formality_level,
            'interests': interests,
            'knowledge_domains': knowledge_domains,
            'response_patterns': {
                'avg_response_length': word_count // max(len(text_samples), 1),
                'uses_questions': '?' in combined_text,
                'uses_exclamations': '!' in combined_text
            },
            'emotional_tendencies': emotional_tendencies,
            'humor_style': 'witty' if any(word in combined_text for word in ['funny', 'joke', 'humor']) else 'light',
            'conversation_depth': 'deep' if word_count > 500 else 'moderate'
        }
    
    def _calculate_training_quality(self, training_data: Dict[str, Any]) -> float:
        """
        Calculate quality score for training data
        
        Args:
            training_data: Training data dictionary
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0
        max_score = 1.0
        
        # Text samples quality
        text_samples = training_data.get('text_samples', [])
        if text_samples:
            total_words = sum(len(sample.split()) for sample in text_samples)
            sample_count = len(text_samples)
            
            # Score based on quantity and variety
            word_score = min(total_words / 1000, 0.4)  # Up to 0.4 for word count
            variety_score = min(sample_count / 10, 0.2)  # Up to 0.2 for variety
            score += word_score + variety_score
        
        # Personality traits provided
        traits = training_data.get('personality_traits', [])
        if traits:
            score += min(len(traits) / 10, 0.2)  # Up to 0.2 for traits
        
        # Description quality
        description = training_data.get('description', '')
        if description:
            score += min(len(description.split()) / 50, 0.2)  # Up to 0.2 for description
        
        return min(score, max_score)
    
    def _generate_ai_response(self, personality: Dict[str, Any], user_message: str, chat_history: List[Dict]) -> str:
        """
        Generate AI response based on personality and context
        
        Args:
            personality: Soul's personality profile
            user_message: User's message
            chat_history: Previous conversation history
            
        Returns:
            Generated response from the soul
        """
        # For now, generate rule-based responses
        # In production, this would use Claude API with personality context
        
        traits = personality.get('personality_traits', [])
        style = personality.get('communication_style', 'friendly')
        interests = personality.get('interests', [])
        
        # Simple response generation based on personality
        response_templates = {
            'greeting': [
                f"Hey there! As someone who's {', '.join(traits[:2])}, I'm excited to chat!",
                f"Hello! I'd love to talk with you about {', '.join(interests) if interests else 'whatever interests you'}!",
                "Hi! How are you doing today?"
            ],
            'question': [
                f"That's an interesting question! Based on my {style} nature, I think...",
                "Great question! Let me share my thoughts on that...",
                "I'm curious about that too! Here's what I think..."
            ],
            'default': [
                f"As someone who tends to be {traits[0] if traits else 'thoughtful'}, I find that fascinating!",
                "That's really interesting! Tell me more about that.",
                f"I love discussing {interests[0] if interests else 'new topics'}! What do you think about..."
            ]
        }
        
        # Determine response type
        message_lower = user_message.lower()
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            response_type = 'greeting'
        elif '?' in user_message:
            response_type = 'question'
        else:
            response_type = 'default'
        
        # Select response template
        import random
        templates = response_templates[response_type]
        base_response = random.choice(templates)
        
        # Add personality-specific ending
        if 'enthusiastic' in traits:
            base_response += " This is so exciting!"
        elif 'thoughtful' in traits:
            base_response += " What are your thoughts on this?"
        elif 'creative' in traits:
            base_response += " I'm always looking for new perspectives!"
        
        return base_response