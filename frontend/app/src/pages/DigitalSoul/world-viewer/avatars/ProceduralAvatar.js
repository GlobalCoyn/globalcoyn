/**
 * Procedural Avatar System for Digital Souls
 * Generates realistic human avatars based on personality traits and parameters
 */

import * as THREE from 'three';

class ProceduralAvatar {
    constructor() {
        this.defaultConfig = {
            height: 1.7,
            build: 'average', // slim, average, athletic, heavy
            skinTone: '#FFDBAC',
            hairColor: '#8B4513',
            eyeColor: '#4B0082',
            clothing: 'casual'
        };
    }

    /**
     * Create a procedural human avatar
     * @param {Object} config - Avatar configuration
     * @param {Object} personalityTraits - Personality traits that influence appearance
     * @returns {THREE.Group} Avatar group
     */
    createAvatar(config = {}, personalityTraits = {}) {
        const avatarConfig = { ...this.defaultConfig, ...config };
        const group = new THREE.Group();

        // Generate appearance parameters from personality
        const appearance = this.generateAppearanceFromPersonality(personalityTraits, avatarConfig);

        // Create body parts
        const torso = this.createTorso(appearance);
        const head = this.createHead(appearance);
        const arms = this.createArms(appearance);
        const legs = this.createLegs(appearance);

        // Assemble avatar
        group.add(torso);
        group.add(head);
        group.add(arms.left);
        group.add(arms.right);
        group.add(legs.left);
        group.add(legs.right);

        // Add clothing
        const clothing = this.createClothing(appearance);
        if (clothing) {
            group.add(clothing);
        }

        // Add hair
        const hair = this.createHair(appearance);
        if (hair) {
            group.add(hair);
        }

        return group;
    }

    /**
     * Generate appearance parameters from personality traits
     */
    generateAppearanceFromPersonality(traits, baseConfig) {
        const appearance = { ...baseConfig };

        // Map personality traits to physical characteristics
        if (traits.includes('energetic') || traits.includes('outgoing')) {
            appearance.build = 'athletic';
            appearance.posture = 'confident';
        }

        if (traits.includes('creative') || traits.includes('artistic')) {
            appearance.hairStyle = 'creative';
            appearance.clothing = 'artistic';
        }

        if (traits.includes('professional') || traits.includes('analytical')) {
            appearance.clothing = 'formal';
            appearance.posture = 'straight';
        }

        if (traits.includes('calm') || traits.includes('peaceful')) {
            appearance.expressions = 'serene';
        }

        return appearance;
    }

    /**
     * Create realistic human torso
     */
    createTorso(appearance) {
        const group = new THREE.Group();

        // Main torso - more realistic proportions
        const torsoGeometry = new THREE.CapsuleGeometry(0.18, 0.5, 4, 8);
        const torsoMaterial = new THREE.MeshLambertMaterial({ color: appearance.skinTone });
        const torso = new THREE.Mesh(torsoGeometry, torsoMaterial);
        torso.position.y = 1.0;
        torso.castShadow = true;
        group.add(torso);

        // Chest definition for more realistic shape
        const chestGeometry = new THREE.SphereGeometry(0.12, 8, 8);
        const chest = new THREE.Mesh(chestGeometry, torsoMaterial);
        chest.position.y = 1.15;
        chest.scale.set(1.2, 0.8, 0.6);
        chest.castShadow = true;
        group.add(chest);

        return group;
    }

    /**
     * Create realistic human head with facial features
     */
    createHead(appearance) {
        const group = new THREE.Group();

        // Head - more realistic proportions
        const headGeometry = new THREE.SphereGeometry(0.12, 12, 8);
        const headMaterial = new THREE.MeshLambertMaterial({ color: appearance.skinTone });
        const head = new THREE.Mesh(headGeometry, headMaterial);
        head.position.y = 1.42;
        head.scale.set(1, 1.1, 0.9); // Slightly elongated for more human proportions
        head.castShadow = true;
        group.add(head);

        // Facial features
        this.addFacialFeatures(group, appearance);

        return group;
    }

    /**
     * Add detailed facial features
     */
    addFacialFeatures(group, appearance) {
        // Eyes - more realistic
        const eyeGeometry = new THREE.SphereGeometry(0.025, 8, 8);
        const eyeMaterial = new THREE.MeshLambertMaterial({ color: appearance.eyeColor });
        
        const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
        leftEye.position.set(-0.04, 1.45, 0.1);
        leftEye.scale.set(0.8, 0.6, 1);
        group.add(leftEye);
        
        const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
        rightEye.position.set(0.04, 1.45, 0.1);
        rightEye.scale.set(0.8, 0.6, 1);
        group.add(rightEye);

        // Pupils
        const pupilGeometry = new THREE.SphereGeometry(0.015, 6, 6);
        const pupilMaterial = new THREE.MeshLambertMaterial({ color: '#000000' });
        
        const leftPupil = new THREE.Mesh(pupilGeometry, pupilMaterial);
        leftPupil.position.set(-0.04, 1.45, 0.11);
        group.add(leftPupil);
        
        const rightPupil = new THREE.Mesh(pupilGeometry, pupilMaterial);
        rightPupil.position.set(0.04, 1.45, 0.11);
        group.add(rightPupil);

        // Nose - more defined
        const noseGeometry = new THREE.ConeGeometry(0.015, 0.04, 6);
        const noseMaterial = new THREE.MeshLambertMaterial({ color: appearance.skinTone });
        const nose = new THREE.Mesh(noseGeometry, noseMaterial);
        nose.position.set(0, 1.42, 0.11);
        nose.rotation.x = Math.PI / 2;
        group.add(nose);

        // Mouth - more realistic
        const mouthGeometry = new THREE.SphereGeometry(0.02, 8, 4);
        const mouthMaterial = new THREE.MeshLambertMaterial({ color: '#CD5C5C' });
        const mouth = new THREE.Mesh(mouthGeometry, mouthMaterial);
        mouth.position.set(0, 1.38, 0.1);
        mouth.scale.set(1.5, 0.4, 0.5);
        group.add(mouth);

        // Eyebrows
        const browGeometry = new THREE.CapsuleGeometry(0.005, 0.03, 2, 4);
        const browMaterial = new THREE.MeshLambertMaterial({ color: appearance.hairColor });
        
        const leftBrow = new THREE.Mesh(browGeometry, browMaterial);
        leftBrow.position.set(-0.04, 1.48, 0.09);
        leftBrow.rotation.z = 0.1;
        group.add(leftBrow);
        
        const rightBrow = new THREE.Mesh(browGeometry, browMaterial);
        rightBrow.position.set(0.04, 1.48, 0.09);
        rightBrow.rotation.z = -0.1;
        group.add(rightBrow);
    }

    /**
     * Create realistic arms
     */
    createArms(appearance) {
        const leftArm = this.createSingleArm(appearance, 'left');
        const rightArm = this.createSingleArm(appearance, 'right');
        
        return { left: leftArm, right: rightArm };
    }

    createSingleArm(appearance, side) {
        const group = new THREE.Group();
        const multiplier = side === 'left' ? -1 : 1;

        // Upper arm
        const upperArmGeometry = new THREE.CapsuleGeometry(0.05, 0.3, 4, 8);
        const armMaterial = new THREE.MeshLambertMaterial({ color: appearance.skinTone });
        const upperArm = new THREE.Mesh(upperArmGeometry, armMaterial);
        upperArm.position.set(0.15 * multiplier, 1.1, 0);
        upperArm.rotation.z = 0.2 * multiplier;
        upperArm.castShadow = true;
        group.add(upperArm);

        // Lower arm (forearm)
        const lowerArmGeometry = new THREE.CapsuleGeometry(0.04, 0.25, 4, 8);
        const lowerArm = new THREE.Mesh(lowerArmGeometry, armMaterial);
        lowerArm.position.set(0.25 * multiplier, 0.85, 0);
        lowerArm.rotation.z = 0.1 * multiplier;
        lowerArm.castShadow = true;
        group.add(lowerArm);

        // Hand
        const handGeometry = new THREE.SphereGeometry(0.04, 6, 6);
        const hand = new THREE.Mesh(handGeometry, armMaterial);
        hand.position.set(0.32 * multiplier, 0.68, 0);
        hand.scale.set(1, 1.2, 0.6);
        hand.castShadow = true;
        group.add(hand);

        return group;
    }

    /**
     * Create realistic legs
     */
    createLegs(appearance) {
        const leftLeg = this.createSingleLeg(appearance, 'left');
        const rightLeg = this.createSingleLeg(appearance, 'right');
        
        return { left: leftLeg, right: rightLeg };
    }

    createSingleLeg(appearance, side) {
        const group = new THREE.Group();
        const multiplier = side === 'left' ? -1 : 1;

        // Upper leg (thigh)
        const thighGeometry = new THREE.CapsuleGeometry(0.07, 0.4, 4, 8);
        const legMaterial = new THREE.MeshLambertMaterial({ color: appearance.skinTone });
        const thigh = new THREE.Mesh(thighGeometry, legMaterial);
        thigh.position.set(0.08 * multiplier, 0.55, 0);
        thigh.castShadow = true;
        group.add(thigh);

        // Lower leg (shin)
        const shinGeometry = new THREE.CapsuleGeometry(0.05, 0.35, 4, 8);
        const shin = new THREE.Mesh(shinGeometry, legMaterial);
        shin.position.set(0.08 * multiplier, 0.15, 0);
        shin.castShadow = true;
        group.add(shin);

        // Foot
        const footGeometry = new THREE.BoxGeometry(0.08, 0.04, 0.15);
        const footMaterial = new THREE.MeshLambertMaterial({ color: '#8B4513' }); // Brown shoes
        const foot = new THREE.Mesh(footGeometry, footMaterial);
        foot.position.set(0.08 * multiplier, 0.02, 0.04);
        foot.castShadow = true;
        group.add(foot);

        return group;
    }

    /**
     * Create hair based on personality and style
     */
    createHair(appearance) {
        const group = new THREE.Group();

        // Base hair shape
        const hairGeometry = new THREE.SphereGeometry(0.13, 8, 6, 0, Math.PI * 2, 0, Math.PI / 2);
        const hairMaterial = new THREE.MeshLambertMaterial({ color: appearance.hairColor });
        const hair = new THREE.Mesh(hairGeometry, hairMaterial);
        hair.position.y = 1.5;
        hair.castShadow = true;
        group.add(hair);

        // Add hair details based on style
        if (appearance.hairStyle === 'creative') {
            // Add some hair strands or accessories
            const strandGeometry = new THREE.CylinderGeometry(0.005, 0.005, 0.1, 4);
            const strand = new THREE.Mesh(strandGeometry, hairMaterial);
            strand.position.set(0.1, 1.55, 0.05);
            strand.rotation.z = 0.3;
            group.add(strand);
        }

        return group;
    }

    /**
     * Create clothing based on personality and style
     */
    createClothing(appearance) {
        const group = new THREE.Group();

        // Basic shirt/top
        let clothingColor = '#4169E1'; // Default blue
        
        if (appearance.clothing === 'formal') {
            clothingColor = '#2F4F4F'; // Dark slate gray
        } else if (appearance.clothing === 'artistic') {
            clothingColor = '#9370DB'; // Medium purple
        } else if (appearance.clothing === 'casual') {
            clothingColor = '#20B2AA'; // Light sea green
        }

        const shirtGeometry = new THREE.CylinderGeometry(0.19, 0.17, 0.5, 8);
        const shirtMaterial = new THREE.MeshLambertMaterial({ color: clothingColor });
        const shirt = new THREE.Mesh(shirtGeometry, shirtMaterial);
        shirt.position.y = 1.0;
        shirt.castShadow = true;
        group.add(shirt);

        // Pants
        const pantsColor = appearance.clothing === 'formal' ? '#000080' : '#8B4513';
        const pantsMaterial = new THREE.MeshLambertMaterial({ color: pantsColor });

        // Left leg pants
        const leftPantGeometry = new THREE.CylinderGeometry(0.08, 0.06, 0.75, 6);
        const leftPant = new THREE.Mesh(leftPantGeometry, pantsMaterial);
        leftPant.position.set(-0.08, 0.375, 0);
        leftPant.castShadow = true;
        group.add(leftPant);

        // Right leg pants
        const rightPantGeometry = new THREE.CylinderGeometry(0.08, 0.06, 0.75, 6);
        const rightPant = new THREE.Mesh(rightPantGeometry, pantsMaterial);
        rightPant.position.set(0.08, 0.375, 0);
        rightPant.castShadow = true;
        group.add(rightPant);

        return group;
    }

    /**
     * Apply animations to the avatar
     */
    animateAvatar(avatarGroup, animationType = 'idle') {
        if (!avatarGroup) return;

        switch (animationType) {
            case 'walking':
                this.animateWalking(avatarGroup);
                break;
            case 'waving':
                this.animateWaving(avatarGroup);
                break;
            case 'idle':
            default:
                this.animateIdle(avatarGroup);
                break;
        }
    }

    animateIdle(avatarGroup) {
        // Subtle breathing animation
        const time = Date.now() * 0.001;
        const breathingOffset = Math.sin(time * 2) * 0.002;
        avatarGroup.position.y += breathingOffset;
    }

    animateWalking(avatarGroup) {
        const time = Date.now() * 0.005;
        // Simple walking cycle - bob up and down
        avatarGroup.position.y = Math.abs(Math.sin(time)) * 0.02;
        avatarGroup.rotation.y = Math.sin(time * 0.5) * 0.1;
    }

    animateWaving(avatarGroup) {
        // Find right arm and animate it
        // This would need more sophisticated rigging for full animation
        const time = Date.now() * 0.01;
        avatarGroup.rotation.z = Math.sin(time) * 0.1;
    }
}

export default ProceduralAvatar;