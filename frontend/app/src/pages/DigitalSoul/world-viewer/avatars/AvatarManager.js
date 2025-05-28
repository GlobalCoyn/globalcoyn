/**
 * Avatar Manager for Digital Soul World Viewer
 * Manages multiple avatars in the world, their positioning and activities
 */

import * as THREE from 'three';
import ProceduralAvatar from './ProceduralAvatar.js';

class AvatarManager {
    constructor(scene) {
        this.scene = scene;
        this.avatarSystem = new ProceduralAvatar();
        this.activeAvatars = new Map(); // soul_id -> avatar group
        this.animationMixers = new Map(); // soul_id -> animation mixer
    }

    /**
     * Create and add avatar to scene for a soul
     * @param {Object} soulData - Soul data including personality traits
     * @param {Object} position - World position {x, y, z}
     * @param {boolean} isFocused - Whether this is the focused soul
     * @returns {THREE.Group} Avatar group
     */
    createSoulAvatar(soulData, position, isFocused = false) {
        try {
            // Generate avatar configuration from soul data
            const avatarConfig = this.generateAvatarConfig(soulData, isFocused);
            
            // Create procedural avatar
            const avatarGroup = this.avatarSystem.createAvatar(
                avatarConfig,
                soulData.personality_traits || []
            );

            // Position avatar
            avatarGroup.position.set(position.x, position.y, position.z);

            // Add activity indicator for multi-soul worlds
            if (soulData.current_activity) {
                this.addActivityIndicator(avatarGroup, soulData.current_activity);
            }

            // Add name label
            this.addNameLabel(avatarGroup, soulData.name || soulData.username, isFocused);

            // Store avatar reference
            this.activeAvatars.set(soulData.soul_id || soulData.username, avatarGroup);

            // Add to scene
            this.scene.add(avatarGroup);

            console.log(`Created avatar for soul: ${soulData.username} at position:`, position);
            
            return avatarGroup;

        } catch (error) {
            console.error('Error creating soul avatar:', error);
            // Fallback to simple avatar
            return this.createFallbackAvatar(soulData, position);
        }
    }

    /**
     * Generate avatar configuration from soul data
     */
    generateAvatarConfig(soulData, isFocused) {
        const config = {
            height: 1.7,
            build: 'average',
            skinTone: '#FFDBAC',
            hairColor: '#8B4513',
            eyeColor: '#4B0082',
            clothing: 'casual'
        };

        // Customize based on soul attributes
        if (soulData.avatar_color) {
            config.clothingColor = soulData.avatar_color;
        }

        // Make focused soul slightly more prominent
        if (isFocused) {
            config.height = 1.75;
            config.posture = 'confident';
        }

        // Map personality traits to appearance
        const traits = soulData.personality_traits || [];
        
        if (traits.includes('energetic')) {
            config.build = 'athletic';
            config.clothing = 'sporty';
        }
        
        if (traits.includes('creative')) {
            config.hairColor = '#8B0000'; // Dark red for creativity
            config.clothing = 'artistic';
        }
        
        if (traits.includes('professional')) {
            config.clothing = 'formal';
            config.hairColor = '#2F4F4F'; // Dark slate
        }

        return config;
    }

    /**
     * Add activity indicator above avatar
     */
    addActivityIndicator(avatarGroup, activity) {
        if (!activity) return;

        // Import activity colors (this should match multiSoulService colors)
        const activityColors = {
            'socializing': '#FF6B6B',
            'working': '#4ECDC4', 
            'relaxing': '#45B7D1',
            'exploring': '#96CEB4',
            'learning': '#FECA57',
            'creating': '#FF9FF3',
            'default': '#95E1D3'
        };

        const color = activityColors[activity.type] || activityColors.default;

        // Create floating indicator
        const indicatorGeometry = new THREE.SphereGeometry(0.08, 8, 8);
        const indicatorMaterial = new THREE.MeshLambertMaterial({ color: color });
        const indicator = new THREE.Mesh(indicatorGeometry, indicatorMaterial);
        indicator.position.set(0, 2.2, 0);
        
        // Add glow effect
        const glowGeometry = new THREE.SphereGeometry(0.12, 8, 8);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0.3
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        glow.position.copy(indicator.position);
        
        avatarGroup.add(indicator);
        avatarGroup.add(glow);

        // Animate indicator
        this.animateActivityIndicator(indicator, glow);
    }

    /**
     * Add name label above avatar
     */
    addNameLabel(avatarGroup, name, isFocused) {
        // Create text texture
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = 256;
        canvas.height = 64;

        // Clear canvas
        context.clearRect(0, 0, canvas.width, canvas.height);

        // Set font and style
        context.font = isFocused ? 'bold 24px Arial' : '18px Arial';
        context.fillStyle = isFocused ? '#FFD700' : '#FFFFFF'; // Gold for focused, white for others
        context.textAlign = 'center';
        context.textBaseline = 'middle';

        // Add background for readability
        context.fillStyle = 'rgba(0, 0, 0, 0.6)';
        context.fillRect(0, 0, canvas.width, canvas.height);

        // Draw text
        context.fillStyle = isFocused ? '#FFD700' : '#FFFFFF';
        context.fillText(name, canvas.width / 2, canvas.height / 2);

        // Create texture and material
        const texture = new THREE.CanvasTexture(canvas);
        const material = new THREE.SpriteMaterial({ map: texture });
        const sprite = new THREE.Sprite(material);
        
        // Position above avatar
        sprite.position.set(0, 2.5, 0);
        sprite.scale.set(1, 0.25, 1);
        
        avatarGroup.add(sprite);
    }

    /**
     * Animate activity indicator
     */
    animateActivityIndicator(indicator, glow) {
        const animate = () => {
            const time = Date.now() * 0.005;
            
            // Float up and down
            indicator.position.y = 2.2 + Math.sin(time) * 0.1;
            glow.position.copy(indicator.position);
            
            // Pulse glow
            glow.material.opacity = 0.2 + Math.sin(time * 2) * 0.1;
            
            requestAnimationFrame(animate);
        };
        animate();
    }

    /**
     * Update avatar animations
     */
    updateAvatars(deltaTime) {
        this.activeAvatars.forEach((avatarGroup, soulId) => {
            // Apply idle animation
            this.avatarSystem.animateAvatar(avatarGroup, 'idle');
        });
    }

    /**
     * Remove avatar from scene
     */
    removeAvatar(soulId) {
        const avatarGroup = this.activeAvatars.get(soulId);
        if (avatarGroup) {
            this.scene.remove(avatarGroup);
            this.activeAvatars.delete(soulId);
            
            // Clean up animation mixer if exists
            const mixer = this.animationMixers.get(soulId);
            if (mixer) {
                mixer.stopAllAction();
                this.animationMixers.delete(soulId);
            }
        }
    }

    /**
     * Clear all avatars
     */
    clearAllAvatars() {
        this.activeAvatars.forEach((avatarGroup, soulId) => {
            this.scene.remove(avatarGroup);
        });
        this.activeAvatars.clear();
        this.animationMixers.clear();
    }

    /**
     * Get avatar for soul
     */
    getAvatar(soulId) {
        return this.activeAvatars.get(soulId);
    }

    /**
     * Create fallback avatar (simple geometric) if procedural fails
     */
    createFallbackAvatar(soulData, position) {
        const group = new THREE.Group();

        // Simple body (fallback to original system)
        const bodyGeometry = new THREE.CapsuleGeometry(0.15, 0.5, 4, 8);
        const bodyMaterial = new THREE.MeshLambertMaterial({ 
            color: soulData.avatar_color || '#4169E1' 
        });
        const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        body.position.y = 1.0;
        body.castShadow = true;
        group.add(body);

        // Simple head
        const headGeometry = new THREE.SphereGeometry(0.12, 8, 6);
        const headMaterial = new THREE.MeshLambertMaterial({ color: '#FFDBAC' });
        const head = new THREE.Mesh(headGeometry, headMaterial);
        head.position.y = 1.42;
        head.castShadow = true;
        group.add(head);

        group.position.set(position.x, position.y, position.z);
        this.scene.add(group);
        this.activeAvatars.set(soulData.soul_id || soulData.username, group);

        return group;
    }

    /**
     * Focus camera on specific avatar
     */
    focusOnAvatar(soulId, camera, controls) {
        const avatarGroup = this.activeAvatars.get(soulId);
        if (avatarGroup && controls) {
            const position = avatarGroup.position;
            controls.target.set(position.x, position.y + 1, position.z);
            controls.update();
        }
    }

    /**
     * Get all active avatar positions for camera framing
     */
    getAllAvatarPositions() {
        const positions = [];
        this.activeAvatars.forEach((avatarGroup) => {
            positions.push(avatarGroup.position.clone());
        });
        return positions;
    }
}

export default AvatarManager;