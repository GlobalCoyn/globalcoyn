/**
 * World Environment System for Digital Soul World Viewer
 * Handles environment rendering, lighting, and world generation
 */

import * as THREE from 'three';

class WorldEnvironment {
    constructor(scene) {
        this.scene = scene;
        this.worldObjects = [];
        this.lights = [];
    }

    /**
     * Initialize basic world environment
     */
    initializeEnvironment() {
        this.setupLighting();
        this.createGround();
        this.setupSkybox();
    }

    /**
     * Setup realistic lighting system
     */
    setupLighting() {
        // Clear existing lights
        this.lights.forEach(light => this.scene.remove(light));
        this.lights = [];

        // Ambient light for overall illumination
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambientLight);
        this.lights.push(ambientLight);

        // Main directional light (sun)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 50;
        directionalLight.shadow.camera.left = -25;
        directionalLight.shadow.camera.right = 25;
        directionalLight.shadow.camera.top = 25;
        directionalLight.shadow.camera.bottom = -25;
        this.scene.add(directionalLight);
        this.lights.push(directionalLight);

        // Fill light for softer shadows
        const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
        fillLight.position.set(-5, 5, -5);
        this.scene.add(fillLight);
        this.lights.push(fillLight);

        // Optional: Point lights for specific areas
        const pointLight = new THREE.PointLight(0xffffff, 0.5, 20);
        pointLight.position.set(0, 5, 0);
        pointLight.castShadow = true;
        this.scene.add(pointLight);
        this.lights.push(pointLight);
    }

    /**
     * Create world ground/terrain
     */
    createGround() {
        const groundSize = 200; // Large enough for multiple souls
        
        // Main ground plane
        const groundGeometry = new THREE.PlaneGeometry(groundSize, groundSize);
        const groundMaterial = new THREE.MeshLambertMaterial({ 
            color: '#90EE90',
            side: THREE.DoubleSide 
        });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = 0;
        ground.receiveShadow = true;
        
        this.scene.add(ground);
        this.worldObjects.push(ground);

        // Add texture variety
        this.addGroundDetails();
    }

    /**
     * Add ground details like paths, grass patches, etc.
     */
    addGroundDetails() {
        // Central gathering area (stone circle)
        const circleGeometry = new THREE.CircleGeometry(8, 16);
        const stoneMaterial = new THREE.MeshLambertMaterial({ color: '#8B8680' });
        const stoneCircle = new THREE.Mesh(circleGeometry, stoneMaterial);
        stoneCircle.rotation.x = -Math.PI / 2;
        stoneCircle.position.y = 0.01;
        stoneCircle.receiveShadow = true;
        
        this.scene.add(stoneCircle);
        this.worldObjects.push(stoneCircle);

        // Paths connecting different areas
        this.createPaths();
        
        // Natural elements
        this.addNaturalElements();
    }

    /**
     * Create paths throughout the world
     */
    createPaths() {
        const pathMaterial = new THREE.MeshLambertMaterial({ color: '#DEB887' }); // Burlywood

        // Main cross paths
        const pathConfigs = [
            { width: 2, length: 40, position: { x: 0, z: 0 }, rotation: 0 },
            { width: 2, length: 40, position: { x: 0, z: 0 }, rotation: Math.PI / 2 }
        ];

        pathConfigs.forEach(config => {
            const pathGeometry = new THREE.PlaneGeometry(config.width, config.length);
            const path = new THREE.Mesh(pathGeometry, pathMaterial);
            path.rotation.x = -Math.PI / 2;
            path.rotation.z = config.rotation;
            path.position.set(config.position.x, 0.005, config.position.z);
            path.receiveShadow = true;
            
            this.scene.add(path);
            this.worldObjects.push(path);
        });
    }

    /**
     * Add natural elements like trees, rocks, etc.
     */
    addNaturalElements() {
        // Add trees around the world
        const treePositions = [
            { x: 15, z: 15 },
            { x: -15, z: 15 },
            { x: 15, z: -15 },
            { x: -15, z: -15 },
            { x: 25, z: 0 },
            { x: -25, z: 0 },
            { x: 0, z: 25 },
            { x: 0, z: -25 }
        ];

        treePositions.forEach(pos => {
            const tree = this.createTree();
            tree.position.set(pos.x, 0, pos.z);
            this.scene.add(tree);
            this.worldObjects.push(tree);
        });

        // Add some rocks/boulders
        const rockPositions = [
            { x: 12, z: 8 },
            { x: -8, z: 12 },
            { x: 18, z: -6 }
        ];

        rockPositions.forEach(pos => {
            const rock = this.createRock();
            rock.position.set(pos.x, 0, pos.z);
            this.scene.add(rock);
            this.worldObjects.push(rock);
        });
    }

    /**
     * Create a simple tree
     */
    createTree() {
        const group = new THREE.Group();

        // Trunk
        const trunkGeometry = new THREE.CylinderGeometry(0.3, 0.4, 4, 8);
        const trunkMaterial = new THREE.MeshLambertMaterial({ color: '#8B4513' });
        const trunk = new THREE.Mesh(trunkGeometry, trunkMaterial);
        trunk.position.y = 2;
        trunk.castShadow = true;
        group.add(trunk);

        // Leaves (multiple spheres for fuller look)
        const leavesMaterial = new THREE.MeshLambertMaterial({ color: '#228B22' });
        
        const leafConfigs = [
            { radius: 2, position: { x: 0, y: 4.5, z: 0 } },
            { radius: 1.5, position: { x: 0.5, y: 5.5, z: 0.5 } },
            { radius: 1.2, position: { x: -0.3, y: 5.8, z: -0.3 } }
        ];

        leafConfigs.forEach(config => {
            const leavesGeometry = new THREE.SphereGeometry(config.radius, 8, 6);
            const leaves = new THREE.Mesh(leavesGeometry, leavesMaterial);
            leaves.position.set(config.position.x, config.position.y, config.position.z);
            leaves.castShadow = true;
            group.add(leaves);
        });

        return group;
    }

    /**
     * Create a rock/boulder
     */
    createRock() {
        const group = new THREE.Group();

        // Main rock body (irregular shape)
        const rockGeometry = new THREE.SphereGeometry(1, 6, 4);
        const rockMaterial = new THREE.MeshLambertMaterial({ color: '#696969' });
        const rock = new THREE.Mesh(rockGeometry, rockMaterial);
        rock.scale.set(1, 0.6, 1.2); // Make it more rock-like
        rock.position.y = 0.6;
        rock.castShadow = true;
        group.add(rock);

        // Small rocks around it
        for (let i = 0; i < 3; i++) {
            const smallRockGeometry = new THREE.SphereGeometry(0.2 + Math.random() * 0.3, 4, 3);
            const smallRock = new THREE.Mesh(smallRockGeometry, rockMaterial);
            const angle = (i / 3) * Math.PI * 2;
            smallRock.position.set(
                Math.cos(angle) * (1.5 + Math.random() * 0.5),
                0.1,
                Math.sin(angle) * (1.5 + Math.random() * 0.5)
            );
            smallRock.castShadow = true;
            group.add(smallRock);
        }

        return group;
    }

    /**
     * Setup skybox for more realistic environment
     */
    setupSkybox() {
        // Simple gradient sky
        const skyGeometry = new THREE.SphereGeometry(100, 16, 8);
        const skyMaterial = new THREE.MeshBasicMaterial({
            color: 0x87CEEB, // Sky blue
            side: THREE.BackSide
        });
        const sky = new THREE.Mesh(skyGeometry, skyMaterial);
        this.scene.add(sky);
        this.worldObjects.push(sky);

        // Add some clouds
        this.addClouds();
    }

    /**
     * Add simple cloud effects
     */
    addClouds() {
        const cloudMaterial = new THREE.MeshBasicMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.7
        });

        for (let i = 0; i < 8; i++) {
            const cloudGeometry = new THREE.SphereGeometry(3 + Math.random() * 2, 6, 4);
            const cloud = new THREE.Mesh(cloudGeometry, cloudMaterial);
            
            cloud.position.set(
                (Math.random() - 0.5) * 80,
                20 + Math.random() * 10,
                (Math.random() - 0.5) * 80
            );
            
            cloud.scale.set(1, 0.6, 1);
            this.scene.add(cloud);
            this.worldObjects.push(cloud);
        }
    }

    /**
     * Create a room environment (for single soul worlds)
     */
    createRoomEnvironment(roomSize = { width: 10, depth: 10, height: 3 }) {
        this.clearEnvironment();
        
        // Room floor
        const floorGeometry = new THREE.PlaneGeometry(roomSize.width, roomSize.depth);
        const floorMaterial = new THREE.MeshLambertMaterial({ color: '#DEB887' });
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.receiveShadow = true;
        this.scene.add(floor);
        this.worldObjects.push(floor);

        // Room walls
        this.createRoomWalls(roomSize);
        
        // Room lighting
        this.setupRoomLighting();
    }

    /**
     * Create room walls
     */
    createRoomWalls(roomSize) {
        const wallMaterial = new THREE.MeshLambertMaterial({ color: '#F5F5DC' });
        
        // Back wall
        const backWallGeometry = new THREE.PlaneGeometry(roomSize.width, roomSize.height);
        const backWall = new THREE.Mesh(backWallGeometry, wallMaterial);
        backWall.position.set(0, roomSize.height / 2, -roomSize.depth / 2);
        this.scene.add(backWall);
        this.worldObjects.push(backWall);

        // Left wall
        const leftWallGeometry = new THREE.PlaneGeometry(roomSize.depth, roomSize.height);
        const leftWall = new THREE.Mesh(leftWallGeometry, wallMaterial);
        leftWall.rotation.y = Math.PI / 2;
        leftWall.position.set(-roomSize.width / 2, roomSize.height / 2, 0);
        this.scene.add(leftWall);
        this.worldObjects.push(leftWall);

        // Right wall
        const rightWall = new THREE.Mesh(leftWallGeometry, wallMaterial);
        rightWall.rotation.y = -Math.PI / 2;
        rightWall.position.set(roomSize.width / 2, roomSize.height / 2, 0);
        this.scene.add(rightWall);
        this.worldObjects.push(rightWall);
    }

    /**
     * Setup lighting for room environment
     */
    setupRoomLighting() {
        // Clear existing lights
        this.lights.forEach(light => this.scene.remove(light));
        this.lights = [];

        // Ceiling light
        const ceilingLight = new THREE.PointLight(0xffffff, 1, 15);
        ceilingLight.position.set(0, 2.8, 0);
        ceilingLight.castShadow = true;
        this.scene.add(ceilingLight);
        this.lights.push(ceilingLight);

        // Ambient light
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
        this.scene.add(ambientLight);
        this.lights.push(ambientLight);
    }

    /**
     * Clear all environment objects
     */
    clearEnvironment() {
        this.worldObjects.forEach(obj => this.scene.remove(obj));
        this.worldObjects = [];
        
        this.lights.forEach(light => this.scene.remove(light));
        this.lights = [];
    }

    /**
     * Update environment (for animations, day/night cycle, etc.)
     */
    update(deltaTime) {
        // Animate clouds
        this.worldObjects.forEach(obj => {
            if (obj.material && obj.material.transparent) {
                // Simple cloud movement
                obj.position.x += 0.01;
                if (obj.position.x > 50) obj.position.x = -50;
            }
        });
    }

    /**
     * Get center position of the world
     */
    getWorldCenter() {
        return new THREE.Vector3(0, 0, 0);
    }

    /**
     * Get world bounds for camera positioning
     */
    getWorldBounds() {
        return {
            min: new THREE.Vector3(-50, 0, -50),
            max: new THREE.Vector3(50, 10, 50)
        };
    }
}

export default WorldEnvironment;