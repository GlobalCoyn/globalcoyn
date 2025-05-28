/**
 * Multi-Soul Service
 * Manages multiple digital souls in a shared world space
 */

class MultiSoulService {
    constructor() {
        this.worldSize = { width: 100, height: 100 };
        this.activeSouls = new Map();
    }

    /**
     * Load all available souls and position them in shared world
     * @param {string} focusedSoulUsername - The main soul to focus on
     * @returns {Promise<Object>} World data with all souls
     */
    async loadSharedWorld(focusedSoulUsername) {
        try {
            // Import digitalSoulService
            const { default: digitalSoulService } = await import('./digitalSoulService');
            
            // Get all available souls
            const allSoulsResult = await digitalSoulService.getAllSouls();
            
            if (!allSoulsResult.success) {
                return { success: false, error: 'Failed to fetch souls' };
            }

            const allSouls = allSoulsResult.souls || [];
            console.log(`Found ${allSouls.length} total souls`);

            // Find focused soul
            const focusedSoul = allSouls.find(soul => soul.username === focusedSoulUsername);
            
            if (!focusedSoul) {
                return { success: false, error: 'Focused soul not found' };
            }

            // Position all souls in the world
            const soulsInWorld = this.positionSoulsInWorld(allSouls, focusedSoulUsername);

            // Create shared world data
            const worldData = {
                id: 'shared_world',
                type: 'multi_soul',
                size: this.worldSize,
                focused_soul: focusedSoulUsername,
                souls: soulsInWorld,
                soul_spawn_point: this.getSoulSpawnPoint(focusedSoul),
                generatedAt: Date.now()
            };

            return {
                success: true,
                world_data: worldData,
                total_souls: allSouls.length
            };

        } catch (error) {
            console.error('Error loading shared world:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Position souls in the world based on their personality and activity
     * @param {Array} souls - All available souls
     * @param {string} focusedSoulUsername - Username of focused soul
     * @returns {Array} Souls with positions and activities
     */
    positionSoulsInWorld(souls, focusedSoulUsername) {
        return souls.map((soul, index) => {
            const isFocused = soul.username === focusedSoulUsername;
            const position = this.generateSoulPosition(soul, index, isFocused, souls.length);
            const activity = this.generateSoulActivity(soul);

            return {
                ...soul,
                position: position,
                current_activity: activity,
                is_focused: isFocused,
                avatar_color: this.getSoulColor(soul.personality_traits),
                last_updated: Date.now()
            };
        });
    }

    /**
     * Generate position for a soul based on personality and focus
     * @param {Object} soul - Soul data
     * @param {number} index - Soul index for distribution
     * @param {boolean} isFocused - Whether this is the focused soul
     * @param {number} totalSouls - Total number of souls to distribute
     * @returns {Object} Position coordinates
     */
    generateSoulPosition(soul, index, isFocused, totalSouls) {
        const centerX = this.worldSize.width / 2;
        const centerZ = this.worldSize.height / 2;

        if (totalSouls === 1) {
            // Single soul goes in center
            return {
                x: centerX,
                y: 0.1,
                z: centerZ
            };
        }

        // Arrange all souls in a circle around center, including focused soul
        const radius = Math.min(15, Math.max(8, totalSouls * 2)); // Dynamic radius based on soul count
        const angle = (index / totalSouls) * Math.PI * 2; // Evenly distribute around circle
        
        // Add small offset for focused soul to distinguish it
        const radiusOffset = isFocused ? -2 : 0; // Focused soul slightly closer to center

        return {
            x: centerX + Math.cos(angle) * (radius + radiusOffset),
            y: 0.1,
            z: centerZ + Math.sin(angle) * (radius + radiusOffset)
        };
    }

    /**
     * Generate current activity for a soul
     * @param {Object} soul - Soul data
     * @returns {Object} Activity data
     */
    generateSoulActivity(soul) {
        const personality = soul.personality_traits || [];
        const currentHour = new Date().getHours();
        
        // Time-based activities
        if (currentHour >= 6 && currentHour <= 9) {
            return { type: 'morning_routine', name: 'Starting the day', duration: 30 };
        } else if (currentHour >= 9 && currentHour <= 12) {
            if (personality.includes('Creative')) {
                return { type: 'creating', name: 'Working on projects', duration: 120 };
            } else if (personality.includes('Social')) {
                return { type: 'socializing', name: 'Meeting friends', duration: 60 };
            } else {
                return { type: 'working', name: 'Daily work', duration: 180 };
            }
        } else if (currentHour >= 12 && currentHour <= 14) {
            return { type: 'eating', name: 'Lunch break', duration: 45 };
        } else if (currentHour >= 14 && currentHour <= 18) {
            if (personality.includes('Fitness')) {
                return { type: 'exercising', name: 'Workout session', duration: 90 };
            } else {
                return { type: 'working', name: 'Afternoon work', duration: 240 };
            }
        } else if (currentHour >= 18 && currentHour <= 22) {
            if (personality.includes('Creative')) {
                return { type: 'streaming', name: 'Live streaming', duration: 120 };
            } else if (personality.includes('Social')) {
                return { type: 'socializing', name: 'Evening hangout', duration: 90 };
            } else {
                return { type: 'relaxing', name: 'Unwinding', duration: 60 };
            }
        } else {
            return { type: 'resting', name: 'Sleeping', duration: 480 };
        }
    }

    /**
     * Get color for soul based on personality
     * @param {Array} personalityTraits - Soul's personality traits
     * @returns {string} Hex color
     */
    getSoulColor(personalityTraits) {
        if (!personalityTraits || personalityTraits.length === 0) {
            return '#4A90E2'; // Default blue
        }

        // Color mapping for personality traits
        const colorMap = {
            'Creative': '#9B59B6',    // Purple
            'Fitness': '#E74C3C',     // Red
            'Social': '#3498DB',      // Blue
            'Technical': '#2ECC71',   // Green
            'Analytical': '#F39C12',  // Orange
            'Adventurous': '#E67E22', // Dark orange
            'Calm': '#1ABC9C',        // Teal
            'Energetic': '#FF6B6B'    // Light red
        };

        // Return color for first matching trait
        for (const trait of personalityTraits) {
            if (colorMap[trait]) {
                return colorMap[trait];
            }
        }

        return '#4A90E2'; // Default
    }

    /**
     * Get spawn point for focused soul
     * @param {Object} focusedSoul - The main soul
     * @returns {Object} Spawn point coordinates
     */
    getSoulSpawnPoint(focusedSoul) {
        return {
            x: this.worldSize.width / 2,
            y: 0.1,
            z: this.worldSize.height / 2
        };
    }

    /**
     * Get activity color for visual indicators
     * @param {string} activityType - Type of activity
     * @returns {string} Hex color
     */
    getActivityColor(activityType) {
        const activityColors = {
            'morning_routine': '#F39C12',  // Orange
            'working': '#3498DB',          // Blue
            'creating': '#9B59B6',         // Purple
            'exercising': '#E74C3C',       // Red
            'eating': '#27AE60',           // Green
            'socializing': '#E67E22',      // Dark orange
            'streaming': '#8E44AD',        // Dark purple
            'relaxing': '#1ABC9C',         // Teal
            'resting': '#34495E'           // Dark gray
        };

        return activityColors[activityType] || '#95A5A6'; // Default gray
    }
}

// Create and export singleton instance
const multiSoulService = new MultiSoulService();
export default multiSoulService;