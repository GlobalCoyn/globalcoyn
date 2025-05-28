"""
Neighborhood Generator for Digital Souls
Expands from single rooms to full city blocks with multiple buildings
"""

import random
import json
import math
from typing import Dict, List, Any, Tuple
from world_generator import MinimalWorldGenerator

class NeighborhoodGenerator:
    """
    Generates neighborhoods with multiple buildings, streets, and public spaces
    """
    
    def __init__(self):
        self.world_generator = MinimalWorldGenerator()
        self.building_types = self._load_building_types()
        self.street_layouts = self._load_street_layouts()
        
    def create_neighborhood(self, neighborhood_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a full neighborhood with multiple buildings and streets
        
        Args:
            neighborhood_config: Configuration for neighborhood generation
                - size: (width, depth) in city blocks
                - population_density: souls per block
                - district_type: residential, commercial, mixed, etc.
                - real_world_location: optional GPS coordinates for real-world mapping
                
        Returns:
            Neighborhood data dictionary for 3D rendering
        """
        
        size = neighborhood_config.get('size', (3, 3))  # 3x3 blocks
        district_type = neighborhood_config.get('district_type', 'mixed')
        population_density = neighborhood_config.get('population_density', 10)
        
        # Generate the neighborhood layout
        neighborhood_data = {
            'neighborhood_id': f"neighborhood_{random.randint(1000, 9999)}",
            'district_type': district_type,
            'size': size,
            'created_at': 1748347992,  # timestamp
            'blocks': self._generate_blocks(size, district_type),
            'streets': self._generate_street_network(size),
            'public_spaces': self._generate_public_spaces(size, district_type),
            'soul_spawn_points': self._generate_soul_spawn_points(size, population_density),
            'boundaries': {
                'min_x': 0, 'max_x': size[0] * 50,  # 50 units per block
                'min_z': 0, 'max_z': size[1] * 50,
                'min_y': 0, 'max_y': 15  # Max building height
            },
            'lighting': self._generate_neighborhood_lighting(district_type),
            'environment': {
                'temperature': 22,
                'weather': 'clear',
                'time_of_day': 'day',
                'ambient_sounds': self._get_ambient_sounds(district_type)
            }
        }
        
        return neighborhood_data
    
    def _generate_blocks(self, size: Tuple[int, int], district_type: str) -> List[Dict[str, Any]]:
        """Generate city blocks with buildings"""
        blocks = []
        block_size = 50  # 50x50 units per block
        
        for x in range(size[0]):
            for z in range(size[1]):
                block_x = x * block_size
                block_z = z * block_size
                
                block = {
                    'block_id': f"block_{x}_{z}",
                    'position': {'x': block_x, 'z': block_z},
                    'size': {'width': block_size, 'depth': block_size},
                    'buildings': self._generate_buildings_for_block(
                        block_x, block_z, block_size, district_type
                    ),
                    'block_type': self._determine_block_type(x, z, size, district_type)
                }
                blocks.append(block)
        
        return blocks
    
    def _generate_buildings_for_block(self, block_x: float, block_z: float, 
                                    block_size: float, district_type: str) -> List[Dict[str, Any]]:
        """Generate buildings within a city block"""
        buildings = []
        
        # Determine number of buildings based on district type
        building_counts = {
            'residential': random.randint(4, 8),
            'commercial': random.randint(2, 4),
            'mixed': random.randint(3, 6),
            'industrial': random.randint(1, 3)
        }
        
        num_buildings = building_counts.get(district_type, 4)
        
        # Generate buildings in a grid pattern within the block
        buildings_per_side = math.ceil(math.sqrt(num_buildings))
        building_width = (block_size - 10) / buildings_per_side  # 10 units for spacing
        
        building_id = 0
        for bx in range(buildings_per_side):
            for bz in range(buildings_per_side):
                if building_id >= num_buildings:
                    break
                
                # Calculate building position within block
                building_x = block_x + 5 + (bx * building_width) + (building_width / 2)
                building_z = block_z + 5 + (bz * building_width) + (building_width / 2)
                
                building = self._create_building(
                    building_x, building_z, building_width * 0.8, district_type, building_id
                )
                buildings.append(building)
                building_id += 1
        
        return buildings
    
    def _create_building(self, x: float, z: float, size: float, 
                        district_type: str, building_id: int) -> Dict[str, Any]:
        """Create a single building with multiple floors/units"""
        
        # Determine building type based on district
        building_types = {
            'residential': ['apartment_complex', 'townhouse', 'single_family'],
            'commercial': ['office_building', 'retail_store', 'restaurant', 'cafe'],
            'mixed': ['mixed_use', 'apartment_complex', 'retail_store'],
            'industrial': ['warehouse', 'factory', 'office_building']
        }
        
        possible_types = building_types.get(district_type, ['apartment_complex'])
        building_type = random.choice(possible_types)
        
        # Generate building dimensions
        width = size
        depth = size
        height = self._get_building_height(building_type)
        floors = max(1, int(height / 3))  # 3 units per floor
        
        building = {
            'building_id': f"building_{building_id}",
            'building_type': building_type,
            'position': {'x': x, 'y': 0, 'z': z},
            'dimensions': {
                'width': width,
                'height': height,
                'depth': depth
            },
            'floors': floors,
            'units': self._generate_building_units(building_type, floors, width, depth),
            'exterior': self._generate_building_exterior(building_type),
            'entrances': self._generate_building_entrances(x, z, width, depth),
            'amenities': self._generate_building_amenities(building_type)
        }
        
        return building
    
    def _generate_building_units(self, building_type: str, floors: int, 
                               width: float, depth: float) -> List[Dict[str, Any]]:
        """Generate individual units/rooms within a building"""
        units = []
        
        if building_type in ['apartment_complex', 'mixed_use']:
            # Multiple residential units
            units_per_floor = 2 if width > 15 else 1
            
            for floor in range(floors):
                for unit_num in range(units_per_floor):
                    unit_width = width / units_per_floor
                    unit_x = (unit_num * unit_width) - (width / 2) + (unit_width / 2)
                    
                    # Generate individual apartment using existing room generator
                    unit_preferences = self._generate_random_preferences()
                    unit_data = self.world_generator._generate_room(unit_preferences)
                    
                    unit = {
                        'unit_id': f"unit_{floor}_{unit_num}",
                        'floor': floor,
                        'unit_type': 'apartment',
                        'position': {
                            'x': unit_x,
                            'y': floor * 3 + 1.5,  # 3 units per floor
                            'z': 0
                        },
                        'dimensions': {
                            'width': unit_width * 0.9,  # Leave space for walls
                            'depth': depth * 0.9,
                            'height': 2.5
                        },
                        'room_data': unit_data,
                        'rent_price': random.randint(50, 200),  # GCN per month
                        'availability': 'available'
                    }
                    units.append(unit)
        
        elif building_type in ['office_building']:
            # Office spaces
            for floor in range(floors):
                unit = {
                    'unit_id': f"office_{floor}",
                    'floor': floor,
                    'unit_type': 'office',
                    'position': {'x': 0, 'y': floor * 3 + 1.5, 'z': 0},
                    'dimensions': {
                        'width': width * 0.9,
                        'depth': depth * 0.9,
                        'height': 2.5
                    },
                    'room_data': self._generate_office_layout(),
                    'rent_price': random.randint(100, 500),
                    'availability': 'available'
                }
                units.append(unit)
        
        elif building_type in ['retail_store', 'restaurant', 'cafe']:
            # Commercial spaces
            unit = {
                'unit_id': f"{building_type}_ground",
                'floor': 0,
                'unit_type': building_type,
                'position': {'x': 0, 'y': 1.5, 'z': 0},
                'dimensions': {
                    'width': width * 0.9,
                    'depth': depth * 0.9,
                    'height': 3
                },
                'room_data': self._generate_commercial_layout(building_type),
                'business_type': building_type,
                'revenue_potential': random.randint(10, 100)  # GCN per day
            }
            units.append(unit)
        
        return units
    
    def _generate_street_network(self, size: Tuple[int, int]) -> Dict[str, Any]:
        """Generate street network connecting blocks"""
        block_size = 50
        streets = {
            'horizontal_streets': [],
            'vertical_streets': [],
            'intersections': [],
            'sidewalks': []
        }
        
        # Generate horizontal streets (running east-west)
        for z in range(size[1] + 1):
            street_z = z * block_size - 2.5  # 5-unit wide streets
            if z == 0:
                street_z = -5
            elif z == size[1]:
                street_z = size[1] * block_size
            
            street = {
                'street_id': f"h_street_{z}",
                'type': 'horizontal',
                'position': {'x': size[0] * block_size / 2, 'y': 0, 'z': street_z},
                'dimensions': {
                    'width': size[0] * block_size + 10,
                    'depth': 5,
                    'height': 0.1
                },
                'lanes': 2,
                'speed_limit': 25
            }
            streets['horizontal_streets'].append(street)
        
        # Generate vertical streets (running north-south) 
        for x in range(size[0] + 1):
            street_x = x * block_size - 2.5
            if x == 0:
                street_x = -5
            elif x == size[0]:
                street_x = size[0] * block_size
            
            street = {
                'street_id': f"v_street_{x}",
                'type': 'vertical',
                'position': {'x': street_x, 'y': 0, 'z': size[1] * block_size / 2},
                'dimensions': {
                    'width': 5,
                    'depth': size[1] * block_size + 10,
                    'height': 0.1
                },
                'lanes': 2,
                'speed_limit': 25
            }
            streets['vertical_streets'].append(street)
        
        # Generate intersections
        for x in range(size[0] + 1):
            for z in range(size[1] + 1):
                intersection = {
                    'intersection_id': f"intersection_{x}_{z}",
                    'position': {
                        'x': x * block_size - 2.5,
                        'y': 0,
                        'z': z * block_size - 2.5
                    },
                    'type': 'four_way',
                    'traffic_control': 'stop_sign'
                }
                streets['intersections'].append(intersection)
        
        return streets
    
    def _generate_public_spaces(self, size: Tuple[int, int], district_type: str) -> List[Dict[str, Any]]:
        """Generate parks, plazas, and other public spaces"""
        public_spaces = []
        
        # Add a central park if neighborhood is large enough
        if size[0] >= 3 and size[1] >= 3:
            center_x = (size[0] * 50) / 2
            center_z = (size[1] * 50) / 2
            
            park = {
                'space_id': 'central_park',
                'space_type': 'park',
                'position': {'x': center_x, 'y': 0, 'z': center_z},
                'dimensions': {'width': 30, 'depth': 30, 'height': 0},
                'features': ['grass', 'trees', 'benches', 'walking_paths'],
                'activities': ['walking', 'socializing', 'relaxing'],
                'capacity': 20  # max souls at once
            }
            public_spaces.append(park)
        
        # Add plaza near commercial areas
        if district_type in ['commercial', 'mixed']:
            plaza = {
                'space_id': 'town_plaza',
                'space_type': 'plaza',
                'position': {'x': 25, 'y': 0, 'z': 25},
                'dimensions': {'width': 20, 'depth': 20, 'height': 0},
                'features': ['fountain', 'seating', 'market_stalls'],
                'activities': ['shopping', 'events', 'socializing'],
                'capacity': 30
            }
            public_spaces.append(plaza)
        
        return public_spaces
    
    def _generate_soul_spawn_points(self, size: Tuple[int, int], density: int) -> List[Dict[str, Any]]:
        """Generate spawn points for souls throughout the neighborhood"""
        spawn_points = []
        block_size = 50
        
        total_souls = size[0] * size[1] * density
        
        for i in range(total_souls):
            # Distribute souls across the neighborhood
            spawn_x = random.uniform(5, size[0] * block_size - 5)
            spawn_z = random.uniform(5, size[1] * block_size - 5)
            
            spawn_point = {
                'spawn_id': f"spawn_{i}",
                'position': {'x': spawn_x, 'y': 0.1, 'z': spawn_z},
                'spawn_type': 'street',  # or 'building' if inside
                'assigned_soul': None,  # Will be assigned when souls are created
                'activity_zone': self._determine_activity_zone(spawn_x, spawn_z, size)
            }
            spawn_points.append(spawn_point)
        
        return spawn_points
    
    # Helper methods
    def _get_building_height(self, building_type: str) -> float:
        """Get appropriate height for building type"""
        heights = {
            'single_family': 6,
            'townhouse': 9,
            'apartment_complex': random.randint(9, 18),
            'office_building': random.randint(12, 24),
            'retail_store': 4,
            'restaurant': 4,
            'cafe': 4,
            'warehouse': 8,
            'factory': 10,
            'mixed_use': random.randint(12, 18)
        }
        return heights.get(building_type, 9)
    
    def _determine_block_type(self, x: int, z: int, size: Tuple[int, int], district_type: str) -> str:
        """Determine what type of block this should be"""
        if district_type == 'mixed':
            # Center blocks are commercial, edges are residential
            center_x, center_z = size[0] // 2, size[1] // 2
            if abs(x - center_x) <= 1 and abs(z - center_z) <= 1:
                return 'commercial'
            else:
                return 'residential'
        return district_type
    
    def _generate_random_preferences(self) -> Dict[str, Any]:
        """Generate random living preferences for apartment units"""
        styles = ['modern', 'vintage', 'minimalist', 'artistic', 'rustic']
        layouts = ['studio', 'one_bedroom', 'two_bedroom']
        
        return {
            'living_style': random.choice(styles),
            'room_layout': random.choice(layouts),
            'wealth_level': random.uniform(0.2, 0.8),
            'social_level': random.uniform(0.1, 0.9),
            'hobbies': random.sample(['reading', 'music', 'cooking', 'gaming', 'fitness'], 
                                   random.randint(1, 3))
        }
    
    def _generate_office_layout(self) -> Dict[str, Any]:
        """Generate office space layout"""
        return {
            'layout_type': 'office',
            'style': 'professional',
            'furniture': [
                {'type': 'desk', 'count': 4},
                {'type': 'chair', 'count': 4},
                {'type': 'filing_cabinet', 'count': 2},
                {'type': 'meeting_table', 'count': 1}
            ],
            'activity_zones': ['work', 'meeting', 'break']
        }
    
    def _generate_commercial_layout(self, business_type: str) -> Dict[str, Any]:
        """Generate commercial space layout"""
        layouts = {
            'restaurant': {
                'furniture': [
                    {'type': 'table', 'count': 6},
                    {'type': 'chair', 'count': 24},
                    {'type': 'kitchen_counter', 'count': 1},
                    {'type': 'register', 'count': 1}
                ],
                'activity_zones': ['dining', 'kitchen', 'service']
            },
            'retail_store': {
                'furniture': [
                    {'type': 'display_shelf', 'count': 8},
                    {'type': 'register', 'count': 1},
                    {'type': 'storage', 'count': 2}
                ],
                'activity_zones': ['shopping', 'checkout', 'storage']
            },
            'cafe': {
                'furniture': [
                    {'type': 'table', 'count': 4},
                    {'type': 'chair', 'count': 16},
                    {'type': 'counter', 'count': 1},
                    {'type': 'coffee_machine', 'count': 1}
                ],
                'activity_zones': ['seating', 'service', 'kitchen']
            }
        }
        
        return layouts.get(business_type, layouts['retail_store'])
    
    def _generate_building_exterior(self, building_type: str) -> Dict[str, Any]:
        """Generate building exterior appearance"""
        materials = {
            'residential': {'material': 'brick', 'color': '#8B4513'},
            'commercial': {'material': 'glass', 'color': '#C0C0C0'},
            'office': {'material': 'concrete', 'color': '#708090'},
            'industrial': {'material': 'metal', 'color': '#696969'}
        }
        
        return materials.get(building_type, materials['residential'])
    
    def _generate_building_entrances(self, x: float, z: float, 
                                   width: float, depth: float) -> List[Dict[str, Any]]:
        """Generate building entrance points"""
        return [
            {
                'entrance_id': 'main',
                'position': {'x': x, 'y': 0, 'z': z - depth/2},
                'type': 'main_entrance',
                'access_level': 'public'
            }
        ]
    
    def _generate_building_amenities(self, building_type: str) -> List[str]:
        """Generate building amenities"""
        amenities = {
            'apartment_complex': ['mailbox', 'laundry', 'parking'],
            'office_building': ['elevator', 'reception', 'parking'],
            'retail_store': ['parking', 'display_window'],
            'restaurant': ['parking', 'outdoor_seating'],
            'mixed_use': ['elevator', 'parking', 'mailbox']
        }
        
        return amenities.get(building_type, [])
    
    def _generate_neighborhood_lighting(self, district_type: str) -> Dict[str, Any]:
        """Generate lighting for the entire neighborhood"""
        lighting_configs = {
            'residential': {
                'ambient_color': '#FFF8DC',
                'ambient_intensity': 0.4,
                'street_lights': True,
                'building_lights': 'warm'
            },
            'commercial': {
                'ambient_color': '#FFFFFF',
                'ambient_intensity': 0.6,
                'street_lights': True,
                'building_lights': 'bright'
            },
            'mixed': {
                'ambient_color': '#FFF8DC',
                'ambient_intensity': 0.5,
                'street_lights': True,
                'building_lights': 'mixed'
            }
        }
        
        return lighting_configs.get(district_type, lighting_configs['mixed'])
    
    def _get_ambient_sounds(self, district_type: str) -> List[str]:
        """Get ambient sounds for the district"""
        sounds = {
            'residential': ['birds', 'wind', 'distant_traffic'],
            'commercial': ['traffic', 'people', 'urban_activity'],
            'mixed': ['moderate_traffic', 'people', 'city_ambience'],
            'industrial': ['machinery', 'trucks', 'industrial_hum']
        }
        
        return sounds.get(district_type, sounds['mixed'])
    
    def _determine_activity_zone(self, x: float, z: float, size: Tuple[int, int]) -> str:
        """Determine what activity zone a position is in"""
        # Simplified zone determination
        center_x, center_z = size[0] * 25, size[1] * 25
        
        distance_from_center = math.sqrt((x - center_x)**2 + (z - center_z)**2)
        
        if distance_from_center < 30:
            return 'commercial'
        elif distance_from_center < 60:
            return 'mixed'
        else:
            return 'residential'
    
    def _load_building_types(self) -> Dict[str, Any]:
        """Load building type definitions (placeholder)"""
        return {}
    
    def _load_street_layouts(self) -> Dict[str, Any]:
        """Load street layout templates (placeholder)"""
        return {}