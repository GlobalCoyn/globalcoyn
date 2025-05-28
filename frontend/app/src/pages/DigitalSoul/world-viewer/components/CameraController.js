/**
 * Camera Controller for Digital Soul World Viewer
 * Handles camera positioning, movement, and controls
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

class CameraController {
    constructor(camera, renderer) {
        this.camera = camera;
        this.renderer = renderer;
        this.controls = null;
        this.isAnimating = false;
        this.animationCallbacks = [];
        
        this.setupControls();
    }

    /**
     * Setup camera controls
     */
    setupControls() {
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.autoRotate = false;
        
        // Configure control limits
        this.controls.minDistance = 5;
        this.controls.maxDistance = 50;
        this.controls.maxPolarAngle = Math.PI / 2.2; // Prevent going under ground
        this.controls.minPolarAngle = Math.PI / 8; // Prevent going too high
        
        // Enable/disable controls
        this.controls.enableRotate = true;
        this.controls.enablePan = true;
        this.controls.enableZoom = true;
    }

    /**
     * Position camera for single soul view
     */
    focusOnSoul(soulPosition, distance = 8) {
        const targetPosition = new THREE.Vector3(
            soulPosition.x,
            soulPosition.y + 1,
            soulPosition.z
        );

        // Camera position (isometric-like view)
        const cameraPosition = new THREE.Vector3(
            soulPosition.x + distance * 0.7,
            soulPosition.y + distance * 0.8,
            soulPosition.z + distance * 0.7
        );

        this.animateToPosition(cameraPosition, targetPosition);
    }

    /**
     * Position camera to show all souls in multi-soul world
     */
    frameAllSouls(soulPositions, padding = 5) {
        if (soulPositions.length === 0) return;

        // Calculate bounding box of all souls
        const bounds = this.calculateBounds(soulPositions);
        
        // Calculate center point
        const center = new THREE.Vector3(
            (bounds.min.x + bounds.max.x) / 2,
            1, // Fixed height for souls
            (bounds.min.z + bounds.max.z) / 2
        );

        // Calculate required distance to frame all souls
        const size = Math.max(
            bounds.max.x - bounds.min.x,
            bounds.max.z - bounds.min.z
        );
        
        const distance = Math.max(15, size / 2 + padding);

        // Position camera
        const cameraPosition = new THREE.Vector3(
            center.x + distance * 0.6,
            center.y + distance * 0.8,
            center.z + distance * 0.6
        );

        this.animateToPosition(cameraPosition, center);
    }

    /**
     * Calculate bounding box for multiple positions
     */
    calculateBounds(positions) {
        const bounds = {
            min: new THREE.Vector3(Infinity, Infinity, Infinity),
            max: new THREE.Vector3(-Infinity, -Infinity, -Infinity)
        };

        positions.forEach(pos => {
            bounds.min.x = Math.min(bounds.min.x, pos.x);
            bounds.min.y = Math.min(bounds.min.y, pos.y);
            bounds.min.z = Math.min(bounds.min.z, pos.z);
            
            bounds.max.x = Math.max(bounds.max.x, pos.x);
            bounds.max.y = Math.max(bounds.max.y, pos.y);
            bounds.max.z = Math.max(bounds.max.z, pos.z);
        });

        return bounds;
    }

    /**
     * Animate camera to position smoothly
     */
    animateToPosition(targetCameraPos, targetLookAt, duration = 1000) {
        if (this.isAnimating) return;

        const startCameraPos = this.camera.position.clone();
        const startLookAt = this.controls.target.clone();
        const startTime = Date.now();

        this.isAnimating = true;

        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Smooth easing function
            const easeProgress = 1 - Math.pow(1 - progress, 3);

            // Interpolate camera position
            this.camera.position.lerpVectors(startCameraPos, targetCameraPos, easeProgress);
            
            // Interpolate look-at target
            const currentTarget = new THREE.Vector3().lerpVectors(startLookAt, targetLookAt, easeProgress);
            this.controls.target.copy(currentTarget);
            
            this.controls.update();

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                this.isAnimating = false;
                this.onAnimationComplete();
            }
        };

        animate();
    }

    /**
     * Set camera for room view
     */
    setupRoomView(roomSize = { width: 10, depth: 10 }) {
        // Position camera for optimal room viewing
        const distance = Math.max(roomSize.width, roomSize.depth) * 0.8;
        
        this.camera.position.set(distance, distance * 0.8, distance);
        this.controls.target.set(0, 1, 0);
        
        // Adjust control limits for room
        this.controls.minDistance = 3;
        this.controls.maxDistance = distance * 1.5;
        
        this.controls.update();
    }

    /**
     * Set camera for open world view
     */
    setupWorldView() {
        // Reset camera for open world
        this.camera.position.set(15, 12, 15);
        this.controls.target.set(0, 0, 0);
        
        // Adjust control limits for world
        this.controls.minDistance = 8;
        this.controls.maxDistance = 50;
        
        this.controls.update();
    }

    /**
     * Follow a moving target (for dynamic soul movement)
     */
    followTarget(targetPosition, offset = new THREE.Vector3(5, 5, 5)) {
        const targetLookAt = targetPosition.clone();
        const targetCameraPos = targetPosition.clone().add(offset);
        
        // Smooth following
        this.camera.position.lerp(targetCameraPos, 0.02);
        this.controls.target.lerp(targetLookAt, 0.02);
        this.controls.update();
    }

    /**
     * Enable/disable auto-rotation
     */
    setAutoRotate(enabled, speed = 0.5) {
        this.controls.autoRotate = enabled;
        this.controls.autoRotateSpeed = speed;
    }

    /**
     * Lock/unlock camera controls
     */
    setControlsEnabled(enabled) {
        this.controls.enabled = enabled;
    }

    /**
     * Get current camera state for saving/restoring
     */
    getCameraState() {
        return {
            position: this.camera.position.clone(),
            target: this.controls.target.clone(),
            zoom: this.camera.zoom
        };
    }

    /**
     * Restore camera state
     */
    setCameraState(state) {
        this.camera.position.copy(state.position);
        this.controls.target.copy(state.target);
        if (state.zoom) this.camera.zoom = state.zoom;
        this.controls.update();
    }

    /**
     * Handle window resize
     */
    handleResize(width, height) {
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    /**
     * Update controls (call in animation loop)
     */
    update() {
        if (this.controls) {
            this.controls.update();
        }
    }

    /**
     * Add callback for when camera animation completes
     */
    onAnimationComplete() {
        this.animationCallbacks.forEach(callback => callback());
        this.animationCallbacks = [];
    }

    /**
     * Add animation complete callback
     */
    addAnimationCallback(callback) {
        this.animationCallbacks.push(callback);
    }

    /**
     * Dispose of controls and cleanup
     */
    dispose() {
        if (this.controls) {
            this.controls.dispose();
        }
    }

    /**
     * Switch to cinematic mode (disable user controls, enable auto-rotate)
     */
    enterCinematicMode() {
        this.setControlsEnabled(false);
        this.setAutoRotate(true, 0.3);
    }

    /**
     * Exit cinematic mode (enable user controls, disable auto-rotate)
     */
    exitCinematicMode() {
        this.setControlsEnabled(true);
        this.setAutoRotate(false);
    }

    /**
     * Quick camera presets
     */
    presets = {
        // Sims-like isometric view
        isometric: (center = new THREE.Vector3(0, 0, 0)) => {
            const distance = 12;
            this.animateToPosition(
                new THREE.Vector3(center.x + distance, center.y + distance, center.z + distance),
                center
            );
        },

        // Top-down view
        topDown: (center = new THREE.Vector3(0, 0, 0)) => {
            this.animateToPosition(
                new THREE.Vector3(center.x, center.y + 20, center.z + 0.1),
                center
            );
        },

        // Side view
        side: (center = new THREE.Vector3(0, 0, 0)) => {
            this.animateToPosition(
                new THREE.Vector3(center.x + 15, center.y + 5, center.z),
                center
            );
        },

        // Close-up view
        closeUp: (center = new THREE.Vector3(0, 0, 0)) => {
            this.animateToPosition(
                new THREE.Vector3(center.x + 3, center.y + 2, center.z + 3),
                center
            );
        }
    };
}

export default CameraController;