"""
Minimal World Generator for Digital Souls
Generates basic 3D environments based on soul personality and preferences
"""

import random
import json
from typing import Dict, List, Any, Tuple
import math

class MinimalWorldGenerator:
    """
    Generates minimal 3D worlds for Digital Souls based on their personality and preferences
    """
    
    def __init__(self):
        self.world_size = (100, 100)  # 100x100 unit world
        self.room_templates = self._load_room_templates()
        self.furniture_catalog = self._load_furniture_catalog()
        self.color_palettes = self._load_color_palettes()
        
    def create_basic_world(self, soul_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a basic world for a Digital Soul
        
        Args:
            soul_data: Complete soul data including living preferences
            
        Returns:
            World data dictionary for 3D rendering
        """
        preferences = soul_data.get('living_preferences', {})
        
        # Generate the main room
        room_data = self._generate_room(preferences)
        
        # Create soul spawn point
        spawn_point = self._get_room_center(room_data)
        
        # Generate basic world data
        world_data = {
            'world_id': f"world_{soul_data['soul_id']}",
            'soul_id': soul_data['soul_id'],
            'world_type': 'minimal_room',
            'created_at': soul_data.get('creation_timestamp'),
            'room': room_data,
            'soul_spawn_point': spawn_point,
            'lighting': self._generate_lighting(preferences),
            'environment': {
                'temperature': 22,  # Celsius
                'weather': 'indoor',
                'time_of_day': 'day'
            },
            'boundaries': {
                'min_x': 0, 'max_x': room_data['dimensions']['width'],
                'min_z': 0, 'max_z': room_data['dimensions']['depth'],
                'min_y': 0, 'max_y': room_data['dimensions']['height']
            }
        }
        
        return world_data
    
    def _generate_room(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate room layout and furniture based on preferences"""
        
        layout_type = preferences.get('room_layout', 'studio')
        living_style = preferences.get('living_style', 'modern')
        wealth_level = preferences.get('wealth_level', 0.5)
        
        # Determine room dimensions based on layout and wealth
        dimensions = self._get_room_dimensions(layout_type, wealth_level)
        
        # Generate floor plan
        room_data = {
            'layout_type': layout_type,
            'dimensions': dimensions,
            'style': living_style,
            'color_scheme': preferences.get('color_preferences', {}),
            'walls': self._generate_walls(dimensions, preferences),
            'floor': self._generate_floor(preferences),
            'ceiling': self._generate_ceiling(preferences),
            'furniture': self._place_furniture(dimensions, preferences),
            'decorations': self._place_decorations(preferences),
            'activity_zones': self._create_activity_zones(dimensions, preferences)
        }
        
        return room_data
    
    def _get_room_dimensions(self, layout_type: str, wealth_level: float) -> Dict[str, float]:
        """Calculate room dimensions based on layout type and wealth level"""
        
        base_dimensions = {
            'studio': {'width': 6, 'depth': 8, 'height': 3},
            'one_bedroom': {'width': 8, 'depth': 10, 'height': 3},
            'two_bedroom': {'width': 12, 'depth': 15, 'height': 3}
        }
        
        dims = base_dimensions.get(layout_type, base_dimensions['studio']).copy()
        
        # Scale based on wealth level
        scale_factor = 0.8 + (wealth_level * 0.6)  # 0.8 to 1.4 multiplier
        dims['width'] *= scale_factor
        dims['depth'] *= scale_factor
        
        # Round to reasonable values
        dims['width'] = round(dims['width'], 1)
        dims['depth'] = round(dims['depth'], 1)
        
        return dims
    
    def _generate_walls(self, dimensions: Dict[str, float], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate wall data for the room"""
        
        color_scheme = preferences.get('color_preferences', {})
        wall_color = color_scheme.get('primary', '#F3F4F6')
        
        walls = [
            {
                'id': 'north_wall',
                'position': {'x': dimensions['width']/2, 'y': dimensions['height']/2, 'z': dimensions['depth']},
                'dimensions': {'width': dimensions['width'], 'height': dimensions['height'], 'depth': 0.1},
                'color': wall_color,
                'material': 'paint'
            },
            {
                'id': 'south_wall', 
                'position': {'x': dimensions['width']/2, 'y': dimensions['height']/2, 'z': 0},
                'dimensions': {'width': dimensions['width'], 'height': dimensions['height'], 'depth': 0.1},
                'color': wall_color,
                'material': 'paint'
            },
            {
                'id': 'east_wall',
                'position': {'x': dimensions['width'], 'y': dimensions['height']/2, 'z': dimensions['depth']/2},
                'dimensions': {'width': 0.1, 'height': dimensions['height'], 'depth': dimensions['depth']},
                'color': wall_color,
                'material': 'paint'
            },
            {
                'id': 'west_wall',
                'position': {'x': 0, 'y': dimensions['height']/2, 'z': dimensions['depth']/2},
                'dimensions': {'width': 0.1, 'height': dimensions['height'], 'depth': dimensions['depth']},
                'color': wall_color,
                'material': 'paint'
            }
        ]
        
        return walls
    
    def _generate_floor(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate floor data"""
        
        living_style = preferences.get('living_style', 'modern')
        color_scheme = preferences.get('color_preferences', {})
        
        floor_materials = {
            'modern': {'material': 'hardwood', 'color': '#D4A574'},
            'minimalist': {'material': 'concrete', 'color': '#9CA3AF'},
            'artistic': {'material': 'bamboo', 'color': '#C19A6B'},
            'rustic': {'material': 'wood_plank', 'color': '#8B4513'},
            'vintage': {'material': 'carpet', 'color': '#CD853F'}
        }
        
        floor_style = floor_materials.get(living_style, floor_materials['modern'])
        
        return {
            'material': floor_style['material'],
            'color': floor_style['color'],
            'texture': 'smooth'
        }
    
    def _generate_ceiling(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate ceiling data"""
        
        return {
            'material': 'paint',
            'color': '#FFFFFF',
            'height': preferences.get('room_height', 3.0),
            'lighting_fixtures': []
        }
    
    def _place_furniture(self, dimensions: Dict[str, float], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Place furniture in the room based on preferences"""
        
        furniture = []
        hobbies = preferences.get('hobbies', [])
        wealth_level = preferences.get('wealth_level', 0.5)
        work_env = preferences.get('work_environment', 'home_office')
        furniture_style = preferences.get('furniture_style', 'modern')
        
        # Essential furniture for every room
        furniture.extend(self._place_essential_furniture(dimensions, furniture_style))
        
        # Add hobby-specific furniture
        if 'reading' in hobbies:
            furniture.append(self._create_bookshelf(dimensions, furniture_style))
            furniture.append(self._create_reading_chair(dimensions, furniture_style))
        
        if 'music' in hobbies:
            furniture.append(self._create_piano_or_guitar(dimensions, furniture_style))
        
        if 'cooking' in hobbies:
            furniture.extend(self._create_kitchen_area(dimensions, furniture_style))
        
        if 'gaming' in hobbies or 'tech' in hobbies:
            furniture.extend(self._create_gaming_setup(dimensions, furniture_style))
        
        if 'fitness' in hobbies:
            furniture.append(self._create_exercise_equipment(dimensions, furniture_style))
        
        # Add work environment furniture
        if work_env == 'tech_setup':
            furniture.extend(self._create_tech_workspace(dimensions, furniture_style))
        elif work_env == 'organized_office':
            furniture.extend(self._create_organized_office(dimensions, furniture_style))
        else:
            furniture.extend(self._create_basic_workspace(dimensions, furniture_style))
        
        # Add luxury items based on wealth level
        if wealth_level > 0.7:
            furniture.extend(self._add_luxury_items(dimensions, furniture_style))
        
        return furniture
    
    def _place_essential_furniture(self, dimensions: Dict[str, float], style: str) -> List[Dict[str, Any]]:
        """Place essential furniture items"""
        
        furniture = []
        
        # Bed (against wall)
        bed_pos = self._find_wall_position(dimensions, 'bed', {'width': 2, 'depth': 1.5})
        furniture.append({
            'id': 'bed',
            'type': 'bed',
            'position': bed_pos,
            'dimensions': {'width': 2, 'height': 0.6, 'depth': 1.5},
            'color': '#8B4513',
            'style': style,
            'material': 'wood'
        })
        
        # Desk
        desk_pos = self._find_available_space(dimensions, {'width': 1.2, 'depth': 0.6}, furniture)
        furniture.append({
            'id': 'desk',
            'type': 'desk', 
            'position': desk_pos,
            'dimensions': {'width': 1.2, 'height': 0.75, 'depth': 0.6},
            'color': '#D2691E',
            'style': style,
            'material': 'wood'
        })
        
        # Chair for desk
        chair_pos = {
            'x': desk_pos['x'],
            'y': 0.4,
            'z': desk_pos['z'] - 0.8
        }
        furniture.append({
            'id': 'desk_chair',
            'type': 'chair',
            'position': chair_pos,
            'dimensions': {'width': 0.6, 'height': 0.8, 'depth': 0.6},
            'color': '#4A5568',
            'style': style,
            'material': 'fabric'
        })
        
        return furniture
    
    def _create_bookshelf(self, dimensions: Dict[str, float], style: str) -> Dict[str, Any]:
        """Create a bookshelf"""
        pos = self._find_wall_position(dimensions, 'bookshelf', {'width': 0.4, 'depth': 2})
        
        return {
            'id': 'bookshelf',
            'type': 'bookshelf',
            'position': pos,
            'dimensions': {'width': 0.4, 'height': 2, 'depth': 2},
            'color': '#8B4513',
            'style': style,
            'material': 'wood',
            'contents': ['books', 'decorative_items']
        }
    
    def _create_reading_chair(self, dimensions: Dict[str, float], style: str) -> Dict[str, Any]:
        """Create a comfortable reading chair"""
        pos = self._find_available_space(dimensions, {'width': 0.8, 'depth': 0.8}, [])
        
        return {
            'id': 'reading_chair',
            'type': 'armchair',
            'position': pos,
            'dimensions': {'width': 0.8, 'height': 1, 'depth': 0.8},
            'color': '#2D3748',
            'style': style,
            'material': 'leather'
        }
    
    def _create_piano_or_guitar(self, dimensions: Dict[str, float], style: str) -> Dict[str, Any]:
        """Create musical instrument"""
        instrument = random.choice(['piano', 'guitar_stand'])
        
        if instrument == 'piano':
            pos = self._find_wall_position(dimensions, 'piano', {'width': 1.5, 'depth': 0.6})
            return {
                'id': 'piano',
                'type': 'piano',
                'position': pos,
                'dimensions': {'width': 1.5, 'height': 0.8, 'depth': 0.6},
                'color': '#000000',
                'style': style,
                'material': 'wood'
            }
        else:
            pos = self._find_available_space(dimensions, {'width': 0.3, 'depth': 0.3}, [])
            return {
                'id': 'guitar_stand',
                'type': 'guitar_stand',
                'position': pos,
                'dimensions': {'width': 0.3, 'height': 1.2, 'depth': 0.3},
                'color': '#8B4513',
                'style': style,
                'material': 'wood'
            }
    
    def _create_kitchen_area(self, dimensions: Dict[str, float], style: str) -> List[Dict[str, Any]]:
        """Create basic kitchen area"""
        furniture = []
        
        # Small kitchen counter
        counter_pos = self._find_wall_position(dimensions, 'counter', {'width': 0.6, 'depth': 1.5})
        furniture.append({
            'id': 'kitchen_counter',
            'type': 'counter',
            'position': counter_pos,
            'dimensions': {'width': 0.6, 'height': 0.9, 'depth': 1.5},
            'color': '#D2691E',
            'style': style,
            'material': 'wood'
        })
        
        # Mini fridge
        fridge_pos = self._find_wall_position(dimensions, 'fridge', {'width': 0.6, 'depth': 0.6})
        furniture.append({
            'id': 'mini_fridge',
            'type': 'fridge',
            'position': fridge_pos,
            'dimensions': {'width': 0.6, 'height': 1.2, 'depth': 0.6},
            'color': '#FFFFFF',
            'style': style,
            'material': 'metal'
        })
        
        return furniture
    
    def _create_gaming_setup(self, dimensions: Dict[str, float], style: str) -> List[Dict[str, Any]]:
        """Create gaming/tech setup"""
        furniture = []
        
        # Gaming desk
        desk_pos = self._find_wall_position(dimensions, 'gaming_desk', {'width': 0.8, 'depth': 1.5})
        furniture.append({
            'id': 'gaming_desk',
            'type': 'desk',
            'position': desk_pos,
            'dimensions': {'width': 0.8, 'height': 0.75, 'depth': 1.5},
            'color': '#1A202C',
            'style': 'modern',
            'material': 'metal_glass'
        })
        
        # Gaming chair
        chair_pos = {
            'x': desk_pos['x'],
            'y': 0.5,
            'z': desk_pos['z'] - 0.8
        }
        furniture.append({
            'id': 'gaming_chair',
            'type': 'gaming_chair',
            'position': chair_pos,
            'dimensions': {'width': 0.7, 'height': 1.2, 'depth': 0.7},
            'color': '#E53E3E',
            'style': 'modern',
            'material': 'leather'
        })
        
        return furniture
    
    def _create_exercise_equipment(self, dimensions: Dict[str, float], style: str) -> Dict[str, Any]:
        """Create exercise equipment"""
        pos = self._find_available_space(dimensions, {'width': 0.6, 'depth': 1.2}, [])
        
        return {
            'id': 'exercise_bike',
            'type': 'exercise_equipment',
            'position': pos,
            'dimensions': {'width': 0.6, 'height': 1.2, 'depth': 1.2},
            'color': '#2D3748',
            'style': style,
            'material': 'metal'
        }
    
    def _create_tech_workspace(self, dimensions: Dict[str, float], style: str) -> List[Dict[str, Any]]:
        """Create tech workspace with multiple monitors"""
        return self._create_gaming_setup(dimensions, style)  # Similar setup
    
    def _create_organized_office(self, dimensions: Dict[str, float], style: str) -> List[Dict[str, Any]]:
        """Create organized office space"""
        furniture = []
        
        # Large desk
        desk_pos = self._find_wall_position(dimensions, 'office_desk', {'width': 0.8, 'depth': 1.8})
        furniture.append({
            'id': 'office_desk',
            'type': 'desk',
            'position': desk_pos,
            'dimensions': {'width': 0.8, 'height': 0.75, 'depth': 1.8},
            'color': '#8B4513',
            'style': style,
            'material': 'wood'
        })
        
        # Filing cabinet
        cabinet_pos = self._find_wall_position(dimensions, 'filing_cabinet', {'width': 0.4, 'depth': 0.6})
        furniture.append({
            'id': 'filing_cabinet',
            'type': 'cabinet',
            'position': cabinet_pos,
            'dimensions': {'width': 0.4, 'height': 1.3, 'depth': 0.6},
            'color': '#4A5568',
            'style': style,
            'material': 'metal'
        })
        
        return furniture
    
    def _create_basic_workspace(self, dimensions: Dict[str, float], style: str) -> List[Dict[str, Any]]:
        """Create basic workspace (already handled in essential furniture)"""
        return []  # Essential furniture already includes basic desk
    
    def _add_luxury_items(self, dimensions: Dict[str, float], style: str) -> List[Dict[str, Any]]:
        """Add luxury furniture items"""
        furniture = []
        
        # Luxury sofa
        sofa_pos = self._find_available_space(dimensions, {'width': 1, 'depth': 2.5}, [])
        furniture.append({
            'id': 'luxury_sofa',
            'type': 'sofa',
            'position': sofa_pos,
            'dimensions': {'width': 1, 'height': 0.8, 'depth': 2.5},
            'color': '#2D3748',
            'style': style,
            'material': 'leather'
        })
        
        # Coffee table
        table_pos = {
            'x': sofa_pos['x'] + 1.2,
            'y': 0.2,
            'z': sofa_pos['z']
        }
        furniture.append({
            'id': 'coffee_table',
            'type': 'table',
            'position': table_pos,
            'dimensions': {'width': 0.6, 'height': 0.4, 'depth': 1.2},
            'color': '#8B4513',
            'style': style,
            'material': 'wood'
        })
        
        return furniture
    
    def _place_decorations(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Place decorative items"""
        decorations = []
        hobbies = preferences.get('hobbies', [])
        
        # Add decorations based on hobbies
        if 'art' in hobbies or 'painting' in hobbies:
            decorations.extend([
                {'type': 'wall_art', 'count': 3, 'style': 'modern_art'},
                {'type': 'easel', 'count': 1, 'style': 'wooden'}
            ])
        
        if 'plants' in hobbies or preferences.get('living_style') == 'natural':
            decorations.extend([
                {'type': 'potted_plant', 'count': 2, 'style': 'modern_pot'},
                {'type': 'hanging_plant', 'count': 1, 'style': 'macrame'}
            ])
        
        # Basic decorations for everyone
        decorations.extend([
            {'type': 'wall_clock', 'count': 1, 'style': 'digital'},
            {'type': 'floor_lamp', 'count': 1, 'style': 'modern'},
            {'type': 'window', 'count': 1, 'style': 'large'}
        ])
        
        return decorations
    
    def _create_activity_zones(self, dimensions: Dict[str, float], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create activity zones within the room"""
        zones = []
        
        # Work zone (around desk)
        zones.append({
            'id': 'work_zone',
            'type': 'work',
            'area': {'x': 1, 'z': 1, 'width': 2, 'depth': 2},
            'activities': ['working', 'studying', 'computing']
        })
        
        # Rest zone (around bed)
        zones.append({
            'id': 'rest_zone', 
            'type': 'rest',
            'area': {'x': dimensions['width']-3, 'z': 1, 'width': 2.5, 'depth': 2},
            'activities': ['sleeping', 'relaxing']
        })
        
        # Social zone (if applicable)
        if preferences.get('social_level', 0) > 0.6:
            zones.append({
                'id': 'social_zone',
                'type': 'social', 
                'area': {'x': dimensions['width']/2, 'z': dimensions['depth']-3, 'width': 3, 'depth': 2},
                'activities': ['socializing', 'entertainment']
            })
        
        return zones
    
    def _generate_lighting(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate lighting setup"""
        
        living_style = preferences.get('living_style', 'modern')
        
        lighting_setups = {
            'modern': {
                'ambient_color': '#FFFFFF',
                'ambient_intensity': 0.6,
                'directional_color': '#FFF8DC',
                'directional_intensity': 0.8
            },
            'artistic': {
                'ambient_color': '#FFF8DC',
                'ambient_intensity': 0.4,
                'directional_color': '#FFE4B5',
                'directional_intensity': 0.6
            },
            'minimalist': {
                'ambient_color': '#F8F8FF',
                'ambient_intensity': 0.7,
                'directional_color': '#FFFFFF',
                'directional_intensity': 0.9
            }
        }
        
        return lighting_setups.get(living_style, lighting_setups['modern'])
    
    def _find_wall_position(self, dimensions: Dict[str, float], item_type: str, item_size: Dict[str, float]) -> Dict[str, float]:
        """Find position against a wall for furniture"""
        
        # Simple algorithm - place against walls with some spacing
        wall_positions = [
            {'x': 0.2, 'z': dimensions['depth']/2},  # West wall
            {'x': dimensions['width']-0.2, 'z': dimensions['depth']/2},  # East wall  
            {'x': dimensions['width']/2, 'z': 0.2},  # South wall
            {'x': dimensions['width']/2, 'z': dimensions['depth']-0.2}  # North wall
        ]
        
        # Return first available position (in real implementation, check for collisions)
        pos = random.choice(wall_positions)
        pos['y'] = item_size.get('height', 0.75) / 2
        
        return pos
    
    def _find_available_space(self, dimensions: Dict[str, float], item_size: Dict[str, float], existing_furniture: List[Dict[str, Any]]) -> Dict[str, float]:
        """Find available space for furniture (simplified)"""
        
        # Simple placement in center area
        center_area = {
            'x': dimensions['width']/2 + random.uniform(-1, 1),
            'y': item_size.get('height', 0.75) / 2,
            'z': dimensions['depth']/2 + random.uniform(-1, 1)
        }
        
        # Ensure within bounds
        center_area['x'] = max(1, min(dimensions['width']-1, center_area['x']))
        center_area['z'] = max(1, min(dimensions['depth']-1, center_area['z']))
        
        return center_area
    
    def _get_room_center(self, room_data: Dict[str, Any]) -> Dict[str, float]:
        """Get center point of room for soul spawn"""
        dimensions = room_data['dimensions']
        
        return {
            'x': dimensions['width'] / 2,
            'y': 0.1,  # Just above floor
            'z': dimensions['depth'] / 2
        }
    
    def _load_room_templates(self) -> Dict[str, Any]:
        """Load room templates (placeholder)"""
        return {}
    
    def _load_furniture_catalog(self) -> Dict[str, Any]:
        """Load furniture catalog (placeholder)"""
        return {}
    
    def _load_color_palettes(self) -> Dict[str, Any]:
        """Load color palettes (placeholder)"""
        return {}

# Basic Soul Behavior System
class BasicSoulBehavior:
    """
    Basic autonomous behavior system for Digital Souls in their world
    """
    
    def __init__(self, soul_data: Dict[str, Any], world_data: Dict[str, Any]):
        self.soul = soul_data
        self.world = world_data
        self.current_activity = 'idle'
        self.current_position = world_data['soul_spawn_point'].copy()
        self.activity_cooldown = 0
        self.personality_traits = soul_data.get('personality_traits', [])
        self.energy_level = 1.0
        self.social_need = 0.5
        self.last_activity_time = 0
        
    def get_next_action(self) -> Dict[str, Any]:
        """
        Determine next autonomous action based on soul's personality and current state
        """
        
        if self.activity_cooldown > 0:
            self.activity_cooldown -= 1
            return {'action': 'continue_current', 'activity': self.current_activity}
        
        # Determine action based on personality and needs
        possible_actions = self._get_possible_actions()
        action = self._choose_action(possible_actions)
        
        # Update soul state
        self._update_soul_state(action)
        
        return action
    
    def _get_possible_actions(self) -> List[Dict[str, Any]]:
        """Get list of possible actions based on world and personality"""
        
        actions = []
        
        # Basic actions available to all souls
        actions.extend([
            {'action': 'walk_around', 'duration': 30, 'energy_cost': 0.1},
            {'action': 'sit_and_think', 'duration': 60, 'energy_cost': -0.1},
            {'action': 'look_out_window', 'duration': 20, 'energy_cost': 0.0}
        ])
        
        # Actions based on furniture in room
        furniture = self.world['room']['furniture']
        for item in furniture:
            if item['type'] == 'desk':
                actions.append({'action': 'work_at_desk', 'duration': 120, 'energy_cost': 0.2})
            elif item['type'] == 'bed':
                actions.append({'action': 'rest_on_bed', 'duration': 180, 'energy_cost': -0.3})
            elif item['type'] == 'bookshelf':
                actions.append({'action': 'read_book', 'duration': 90, 'energy_cost': 0.0})
            elif item['type'] == 'piano':
                actions.append({'action': 'play_piano', 'duration': 60, 'energy_cost': 0.1})
            elif item['type'] == 'exercise_equipment':
                actions.append({'action': 'exercise', 'duration': 45, 'energy_cost': 0.3})
        
        # Actions based on personality traits
        for trait in self.personality_traits:
            trait_lower = trait.lower()
            if trait_lower in ['creative', 'artistic']:
                actions.append({'action': 'creative_work', 'duration': 90, 'energy_cost': 0.2})
            elif trait_lower in ['social', 'outgoing']:
                actions.append({'action': 'video_call_friends', 'duration': 45, 'energy_cost': 0.1})
            elif trait_lower in ['organized', 'methodical']:
                actions.append({'action': 'organize_space', 'duration': 60, 'energy_cost': 0.2})
        
        return actions
    
    def _choose_action(self, possible_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Choose action based on current needs and personality"""
        
        # Simple scoring system
        scored_actions = []
        
        for action in possible_actions:
            score = 1.0
            
            # Prefer actions that restore energy if tired
            if self.energy_level < 0.3 and action['energy_cost'] < 0:
                score += 2.0
            elif self.energy_level > 0.8 and action['energy_cost'] > 0:
                score += 1.0
            
            # Personality-based preferences
            action_name = action['action']
            if 'creative' in [t.lower() for t in self.personality_traits]:
                if 'creative' in action_name or 'piano' in action_name:
                    score += 1.5
            
            if 'social' in [t.lower() for t in self.personality_traits]:
                if 'call' in action_name:
                    score += 1.5
            
            # Add some randomness
            score += random.uniform(0, 0.5)
            
            scored_actions.append((score, action))
        
        # Choose highest scoring action
        scored_actions.sort(key=lambda x: x[0], reverse=True)
        chosen_action = scored_actions[0][1]
        
        # Set activity cooldown
        self.activity_cooldown = chosen_action['duration'] // 10  # Simplified time units
        
        return chosen_action
    
    def _update_soul_state(self, action: Dict[str, Any]) -> None:
        """Update soul's internal state based on action"""
        
        # Update energy
        self.energy_level = max(0.0, min(1.0, self.energy_level - action['energy_cost']))
        
        # Update position (simplified)
        if action['action'] == 'walk_around':
            self._move_randomly()
        elif action['action'] in ['work_at_desk', 'read_book']:
            self._move_to_furniture(action['action'])
        
        # Update current activity
        self.current_activity = action['action']
        self.last_activity_time = self.last_activity_time + 1
    
    def _move_randomly(self) -> None:
        """Move randomly within room bounds"""
        room_bounds = self.world['boundaries']
        
        self.current_position['x'] += random.uniform(-0.5, 0.5)
        self.current_position['z'] += random.uniform(-0.5, 0.5)
        
        # Keep within bounds
        self.current_position['x'] = max(room_bounds['min_x'] + 0.5, 
                                       min(room_bounds['max_x'] - 0.5, 
                                           self.current_position['x']))
        self.current_position['z'] = max(room_bounds['min_z'] + 0.5,
                                       min(room_bounds['max_z'] - 0.5,
                                           self.current_position['z']))
    
    def _move_to_furniture(self, action: str) -> None:
        """Move to specific furniture for activity"""
        
        furniture = self.world['room']['furniture']
        target_furniture = None
        
        if 'desk' in action:
            target_furniture = next((f for f in furniture if f['type'] == 'desk'), None)
        elif 'book' in action:
            target_furniture = next((f for f in furniture if f['type'] == 'bookshelf'), None)
        
        if target_furniture:
            self.current_position = {
                'x': target_furniture['position']['x'],
                'y': 0.1,
                'z': target_furniture['position']['z'] - 0.5  # Stand in front
            }
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state of the soul"""
        
        return {
            'position': self.current_position,
            'activity': self.current_activity,
            'energy_level': self.energy_level,
            'social_need': self.social_need,
            'activity_cooldown': self.activity_cooldown
        }