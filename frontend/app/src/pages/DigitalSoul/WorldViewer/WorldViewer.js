/**
 * WorldViewer.js - Simple World Viewer with Header Component
 */

import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import Header from '../world-viewer/components/Header';
import ProceduralAvatar from '../world-viewer/avatars/ProceduralAvatar';

const WorldViewer = () => {
    const { username } = useParams();
    const navigate = useNavigate();
    const mountRef = useRef(null);
    const sceneRef = useRef(null);
    const avatarSystemRef = useRef(null);
    const focusedSoulRef = useRef(null);
    
    // State for soul data
    const [worldData, setWorldData] = useState(null);
    const [soulData, setSoulData] = useState(null);
    const [walletBalance, setWalletBalance] = useState(0);
    const [loading, setLoading] = useState(true);
    
    // Camera view state
    const [cameraView, setCameraView] = useState('follow'); // 'follow', 'front', 'overview'
    
    // Time system state
    const [worldTime, setWorldTime] = useState({
        day: 1,
        hour: 12, // Start at noon
        minute: 0,
        timeSpeed: 1 // 1 real second = 1 game second (real time)
    });
    
    const handleGoBack = () => {
        navigate('/app/digital-soul');
    };
    
    const handleCopyAddress = async () => {
        if (!soulData?.creator_wallet) return;
        try {
            await navigator.clipboard.writeText(soulData.creator_wallet);
            console.log('Address copied to clipboard');
        } catch (err) {
            console.error('Failed to copy address:', err);
        }
    };

    const handleCameraViewChange = () => {
        const views = ['follow', 'front', 'overview'];
        const currentIndex = views.indexOf(cameraView);
        const nextIndex = (currentIndex + 1) % views.length;
        setCameraView(views[nextIndex]);
        console.log('Camera view changed to:', views[nextIndex]);
    };

    // Load world data
    const loadWorldData = async () => {
        try {
            console.log(`Loading shared world for username: ${username}`);

            const { default: multiSoulService } = await import('../../../services/multiSoulService');
            const result = await multiSoulService.loadSharedWorld(username);
            
            console.log('World data received:', result);

            if (!result.success) {
                throw new Error(result.error || 'Failed to load world');
            }

            const worldData = result.world_data;
            
            // Find focused soul
            const focusedSoul = worldData.souls.find(soul => soul.is_focused);
            if (focusedSoul) {
                setSoulData(focusedSoul);
                console.log('Focused soul data:', focusedSoul);

                // Fetch wallet balance
                if (focusedSoul?.creator_wallet) {
                    fetchWalletBalance(focusedSoul.creator_wallet);
                }
            }

            setWorldData(worldData);
            
            // Render avatars if scene is ready
            if (sceneRef.current && avatarSystemRef.current) {
                renderAvatars(worldData);
            }
            
            console.log(`Loaded world with ${worldData.souls.length} souls`);
        } catch (err) {
            console.error('Error loading world data:', err);
        } finally {
            setLoading(false);
        }
    };

    // Fetch wallet balance
    const fetchWalletBalance = async (creatorWallet) => {
        try {
            if (!creatorWallet) return;

            const { default: walletService } = await import('../../../services/api/walletService');
            const balanceInfo = await walletService.getBalance(creatorWallet);
            
            if (balanceInfo && typeof balanceInfo.balance === 'number') {
                setWalletBalance(balanceInfo.balance);
                console.log('Fetched balance:', balanceInfo.balance);
            } else {
                setWalletBalance(0);
            }
        } catch (error) {
            console.error('Error fetching wallet balance:', error);
            setWalletBalance(0);
        }
    };

    // Store avatar references for animation
    const avatarRefs = useRef(new Map());
    const avatarBehaviors = useRef(new Map());
    const terrainRef = useRef(null);

    // Calculate terrain height at given x, z coordinates
    const getTerrainHeight = (x, z) => {
        let height = 0;
        
        // Major mountain ranges - more dramatic peaks
        height += Math.sin(x * 0.004) * Math.cos(z * 0.006) * 35;
        height += Math.sin(x * 0.007) * Math.cos(z * 0.005) * 25;
        height += Math.sin(x * 0.003) * Math.sin(z * 0.008) * 20;
        
        // Secondary mountain systems
        height += Math.sin(x * 0.015) * Math.cos(z * 0.012) * 15;
        height += Math.cos(x * 0.018) * Math.sin(z * 0.020) * 12;
        
        // Hill systems and ridges
        height += Math.sin(x * 0.035) * Math.cos(z * 0.030) * 8;
        height += Math.cos(x * 0.045) * Math.sin(z * 0.040) * 6;
        
        // Fine detail for rocky texture
        height += Math.sin(x * 0.08) * Math.cos(z * 0.075) * 3;
        height += Math.sin(x * 0.12) * Math.cos(z * 0.11) * 2;
        
        // Micro detail for surface roughness
        height += Math.sin(x * 0.2) * Math.cos(z * 0.18) * 1;
        height += (Math.sin(x * 0.3) * Math.cos(z * 0.25)) * 0.5;
        
        // Valley systems - deeper and more defined
        const valleyEffect1 = Math.sin(x * 0.008) * Math.sin(z * 0.012);
        const valleyEffect2 = Math.cos(x * 0.015) * Math.cos(z * 0.018);
        height += valleyEffect1 * 8;
        height += valleyEffect2 * 6;
        
        // Plateau creation
        const plateauEffect = Math.sin(x * 0.01) * Math.cos(z * 0.01);
        if (plateauEffect > 0.3) {
            height += plateauEffect * 10;
        }
        
        // Distance-based height falloff for natural look
        const terrainSize = 500;
        const distance = Math.sqrt(x * x + z * z);
        const falloff = Math.max(0.2, 1 - distance / (terrainSize * 0.3));
        height *= falloff;
        
        // Ensure walkable areas near center
        const centerDistance = Math.sqrt(x * x + z * z);
        if (centerDistance < 30) {
            height = Math.max(height, -1); // Flatter near center
        } else {
            height = Math.max(height, -5); // Allow deeper valleys further out
        }
        
        return height;
    };

    // Initialize basic avatar behaviors
    const initializeAvatarBehavior = (soul) => {
        const currentX = soul.position.x * 0.1;
        const currentZ = soul.position.z * 0.1;
        
        return {
            targetPosition: {
                x: (Math.random() - 0.5) * 40,
                z: (Math.random() - 0.5) * 40
            },
            currentPosition: {
                x: currentX,
                z: currentZ
            },
            speed: 0.5 + Math.random() * 0.5, // Random walking speed
            waitTime: 0,
            maxWaitTime: Math.random() * 5 + 2, // Wait 2-7 seconds before moving
            isMoving: false,
            personality: soul.personality_traits || []
        };
    };

    // Update avatar movement and behaviors
    const updateAvatarBehaviors = (deltaTime) => {
        avatarBehaviors.current.forEach((behavior, soulId) => {
            const avatar = avatarRefs.current.get(soulId);
            if (!avatar) return;

            if (!behavior.isMoving) {
                // Waiting phase
                behavior.waitTime += deltaTime;
                if (behavior.waitTime >= behavior.maxWaitTime) {
                    // Choose new target position
                    behavior.targetPosition = {
                        x: (Math.random() - 0.5) * 30,
                        z: (Math.random() - 0.5) * 30
                    };
                    behavior.isMoving = true;
                    behavior.waitTime = 0;
                }
            } else {
                // Moving phase
                const dx = behavior.targetPosition.x - behavior.currentPosition.x;
                const dz = behavior.targetPosition.z - behavior.currentPosition.z;
                const distance = Math.sqrt(dx * dx + dz * dz);

                if (distance > 0.5) {
                    // Calculate proposed movement
                    const moveX = (dx / distance) * behavior.speed * deltaTime;
                    const moveZ = (dz / distance) * behavior.speed * deltaTime;
                    
                    const newX = behavior.currentPosition.x + moveX;
                    const newZ = behavior.currentPosition.z + moveZ;
                    
                    // Check if movement is valid (not too steep)
                    const currentHeight = getTerrainHeight(behavior.currentPosition.x, behavior.currentPosition.z);
                    const newHeight = getTerrainHeight(newX, newZ);
                    const heightDifference = Math.abs(newHeight - currentHeight);
                    const maxClimbHeight = 3.0; // Maximum height difference souls can climb
                    
                    // Only move if the terrain isn't too steep
                    if (heightDifference <= maxClimbHeight) {
                        behavior.currentPosition.x = newX;
                        behavior.currentPosition.z = newZ;
                        
                        // Update avatar position with terrain following
                        avatar.position.x = behavior.currentPosition.x;
                        avatar.position.z = behavior.currentPosition.z;
                        avatar.position.y = newHeight + 1.0; // Avatar height above terrain
                    } else {
                        // Terrain too steep, choose new target
                        behavior.isMoving = false;
                        behavior.waitTime = 0;
                        behavior.maxWaitTime = 1; // Try again quickly
                    }
                    
                    // Rotate avatar to face movement direction
                    avatar.rotation.y = Math.atan2(dx, dz);
                    
                    // Add subtle bobbing animation while walking
                    avatar.position.y += Math.sin(Date.now() * 0.005) * 0.05;
                } else {
                    // Reached target, stop moving
                    behavior.isMoving = false;
                    behavior.maxWaitTime = Math.random() * 8 + 3; // Wait 3-11 seconds
                    
                    // Set avatar to terrain height when stationary
                    const terrainHeight = getTerrainHeight(behavior.currentPosition.x, behavior.currentPosition.z);
                    avatar.position.y = terrainHeight + 1.0;
                }
            }
        });
    };

    // Render procedural avatars with behaviors
    const renderAvatars = (worldData) => {
        if (!worldData?.souls || !sceneRef.current || !avatarSystemRef.current) {
            console.log('Missing data for rendering avatars');
            return;
        }

        console.log('Rendering procedural avatars for', worldData.souls.length, 'souls');

        // Clear existing avatars (except ground plane)
        const objectsToRemove = [];
        sceneRef.current.traverse((child) => {
            if (child.userData.isAvatar) {
                objectsToRemove.push(child);
            }
        });
        objectsToRemove.forEach(obj => sceneRef.current.remove(obj));

        // Clear previous references
        avatarRefs.current.clear();
        avatarBehaviors.current.clear();

        // Create procedural avatars for all souls
        worldData.souls.forEach((soul, index) => {
            console.log(`Creating procedural avatar for soul ${index}:`, soul.username);
            
            try {
                // Generate avatar config from soul data
                const avatarConfig = generateAvatarConfig(soul);
                
                // Create procedural avatar
                const avatarGroup = avatarSystemRef.current.createAvatar(
                    avatarConfig,
                    soul.personality_traits || []
                );

                // Mark as avatar for cleanup
                avatarGroup.userData.isAvatar = true;
                avatarGroup.userData.soulId = soul.id || soul.username;
                avatarGroup.userData.soulData = soul; // Store soul data for camera tracking

                // Position avatar based on soul position with terrain height
                const scaledX = soul.position.x * 0.1;
                const scaledZ = soul.position.z * 0.1;
                const terrainHeight = getTerrainHeight(scaledX, scaledZ);
                
                avatarGroup.position.set(
                    scaledX,
                    terrainHeight + 1.0, // Place avatar properly above terrain
                    scaledZ
                );

                // Add name label
                addNameLabel(avatarGroup, soul.name || soul.username, soul.is_focused);

                // Store avatar reference and initialize behavior
                avatarRefs.current.set(soul.id || soul.username, avatarGroup);
                avatarBehaviors.current.set(soul.id || soul.username, initializeAvatarBehavior(soul));

                // Set focused soul reference for camera following
                if (soul.is_focused) {
                    focusedSoulRef.current = avatarGroup;
                    console.log('Set focused soul for camera following:', soul.username);
                }

                sceneRef.current.add(avatarGroup);
                console.log(`Created procedural avatar for ${soul.username} at position:`, avatarGroup.position);
                
            } catch (error) {
                console.error(`Error creating procedural avatar for ${soul.username}:`, error);
                
                // Fallback to simple avatar
                const fallbackAvatar = createFallbackAvatar(soul);
                avatarRefs.current.set(soul.id || soul.username, fallbackAvatar);
                avatarBehaviors.current.set(soul.id || soul.username, initializeAvatarBehavior(soul));
                sceneRef.current.add(fallbackAvatar);
            }
        });

        console.log('Finished rendering procedural avatars');
    };

    // Generate avatar config from soul data
    const generateAvatarConfig = (soul) => {
        const config = {
            height: 1.7,
            build: 'average',
            skinTone: '#FFDBAC',
            hairColor: '#8B4513',
            eyeColor: '#4B0082',
            clothing: 'casual'
        };

        // Customize based on soul attributes
        if (soul.avatar_color) {
            config.clothingColor = soul.avatar_color;
        }

        // Make focused soul slightly more prominent
        if (soul.is_focused) {
            config.height = 1.75;
            config.posture = 'confident';
        }

        // Map personality traits to appearance
        const traits = soul.personality_traits || [];
        if (traits.includes('energetic')) {
            config.build = 'athletic';
            config.clothing = 'sporty';
        }
        if (traits.includes('creative')) {
            config.hairColor = '#8B0000';
            config.clothing = 'artistic';
        }
        if (traits.includes('professional')) {
            config.clothing = 'formal';
            config.hairColor = '#2F4F4F';
        }

        return config;
    };

    // Add name label above avatar
    const addNameLabel = (avatarGroup, name, isFocused) => {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = 256;
        canvas.height = 64;

        context.clearRect(0, 0, canvas.width, canvas.height);
        context.font = isFocused ? 'bold 24px Arial' : '18px Arial';
        context.fillStyle = isFocused ? '#FFD700' : '#FFFFFF';
        context.textAlign = 'center';
        context.textBaseline = 'middle';

        // Background
        context.fillStyle = 'rgba(0, 0, 0, 0.6)';
        context.fillRect(0, 0, canvas.width, canvas.height);

        // Text
        context.fillStyle = isFocused ? '#FFD700' : '#FFFFFF';
        context.fillText(name, canvas.width / 2, canvas.height / 2);

        const texture = new THREE.CanvasTexture(canvas);
        const material = new THREE.SpriteMaterial({ map: texture });
        const sprite = new THREE.Sprite(material);
        
        sprite.position.set(0, 2.5, 0);
        sprite.scale.set(1, 0.25, 1);
        
        avatarGroup.add(sprite);
    };

    // Create fallback avatar if procedural fails
    const createFallbackAvatar = (soul) => {
        const group = new THREE.Group();
        group.userData.isAvatar = true;

        // Simple body
        const bodyGeometry = new THREE.CapsuleGeometry(0.15, 0.5, 4, 8);
        const bodyMaterial = new THREE.MeshLambertMaterial({ 
            color: soul.avatar_color || '#4169E1' 
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

        const scaledX = soul.position.x * 0.1;
        const scaledZ = soul.position.z * 0.1;
        const terrainHeight = getTerrainHeight(scaledX, scaledZ);
        
        group.position.set(
            scaledX,
            terrainHeight + 1.0,
            scaledZ
        );

        addNameLabel(group, soul.name || soul.username, soul.is_focused);

        return group;
    };

    // Time System Functions
    const updateWorldTime = () => {
        setWorldTime(prevTime => {
            let newMinute = prevTime.minute + (prevTime.timeSpeed / 60);
            let newHour = prevTime.hour;
            let newDay = prevTime.day;
            
            if (newMinute >= 60) {
                newHour += Math.floor(newMinute / 60);
                newMinute = newMinute % 60;
            }
            
            if (newHour >= 24) {
                newDay += Math.floor(newHour / 24);
                newHour = newHour % 24;
            }
            
            return {
                ...prevTime,
                day: newDay,
                hour: newHour,
                minute: newMinute
            };
        });
    };

    // Calculate sun position based on time
    const calculateSunPosition = (hour, minute) => {
        const timeRatio = (hour + minute / 60) / 24; // 0 to 1
        const sunAngle = timeRatio * Math.PI * 2 - Math.PI / 2; // Start at dawn
        
        return {
            x: Math.cos(sunAngle) * 120,
            y: Math.sin(sunAngle) * 80 + 30, // Much higher in sky
            z: Math.sin(sunAngle * 0.5) * 30,
            intensity: Math.max(0.1, Math.sin(sunAngle) + 0.4), // Minimum ambient light
            isVisible: Math.sin(sunAngle) > -0.2 // Sun visible when above horizon
        };
    };

    // Update lighting based on time of day
    const updateLighting = (scene, hour, minute) => {
        const sunPos = calculateSunPosition(hour, minute);
        const isNight = hour < 6 || hour > 18;
        
        // Find and update directional light (sun)
        const directionalLight = scene.children.find(child => 
            child.type === 'DirectionalLight'
        );
        
        if (directionalLight) {
            directionalLight.position.set(sunPos.x, sunPos.y, sunPos.z);
            directionalLight.intensity = sunPos.intensity;
            
            // Change light color based on time
            if (hour >= 5 && hour <= 7) { // Dawn
                directionalLight.color.setHex(0xFFB366); // Orange
            } else if (hour >= 17 && hour <= 19) { // Dusk
                directionalLight.color.setHex(0xFF6B35); // Red-orange
            } else if (isNight) { // Night
                directionalLight.color.setHex(0x4169E1); // Blue moonlight
            } else { // Day
                directionalLight.color.setHex(0xFFFFFF); // White
            }
        }
        
        // Find and update visible sun position
        const sunMesh = scene.children.find(child => 
            child.userData && child.userData.isSun
        );
        
        if (sunMesh) {
            sunMesh.position.set(sunPos.x, sunPos.y, sunPos.z);
            sunMesh.visible = sunPos.isVisible;
            
            // Change sun color based on time
            if (hour >= 5 && hour <= 7) { // Dawn
                sunMesh.material.color.setHex(0xFFB366);
                if (sunMesh.material.emissive) {
                    sunMesh.material.emissive.setHex(0xFF8833);
                }
            } else if (hour >= 17 && hour <= 19) { // Dusk
                sunMesh.material.color.setHex(0xFF6B35);
                if (sunMesh.material.emissive) {
                    sunMesh.material.emissive.setHex(0xFF4400);
                }
            } else if (!isNight) { // Day
                sunMesh.material.color.setHex(0xFFFACD);
                if (sunMesh.material.emissive) {
                    sunMesh.material.emissive.setHex(0xFFFF88);
                }
            }
        }
        
        // Update ambient light
        const ambientLight = scene.children.find(child => 
            child.type === 'AmbientLight'
        );
        
        if (ambientLight) {
            if (isNight) {
                ambientLight.intensity = 0.2;
                ambientLight.color.setHex(0x404080); // Blue tint
            } else {
                ambientLight.intensity = 0.6;
                ambientLight.color.setHex(0xFFFFFF);
            }
        }
        
        // Update sky background color based on time
        if (scene.background) {
            if (hour >= 5 && hour <= 7) { // Dawn
                scene.background.setHex(0xFFB366);
            } else if (hour >= 17 && hour <= 19) { // Dusk
                scene.background.setHex(0xFF6B35);
            } else if (isNight) { // Night
                scene.background.setHex(0x191970); // Dark blue
            } else { // Day
                scene.background.setHex(0x87CEEB); // Sky blue
            }
        }
        
        // Update atmospheric fog color to match sky and time
        if (scene.fog) {
            if (hour >= 5 && hour <= 7) { // Dawn
                scene.fog.color.setHex(0xFFE4B5); // Warm dawn mist
            } else if (hour >= 17 && hour <= 19) { // Dusk
                scene.fog.color.setHex(0xFFB366); // Golden dusk haze
            } else if (isNight) { // Night
                scene.fog.color.setHex(0x1a1a2e); // Deep blue night mist
            } else { // Day
                scene.fog.color.setHex(0xa8b8c8); // Atmospheric blue-gray
            }
        }
    };

    // Update camera based on view mode and focused soul
    const updateCamera = (camera, controls, focusedSoul) => {
        if (!focusedSoul) return;

        const soulPosition = {
            x: focusedSoul.position.x,
            y: focusedSoul.position.y, // Use actual soul height (including terrain)
            z: focusedSoul.position.z
        };

        switch (cameraView) {
            case 'follow':
                // Fixed position following focused soul from behind - terrain aware
                const followCameraX = soulPosition.x - 3;
                const followCameraZ = soulPosition.z - 3;
                const followTerrainHeight = getTerrainHeight(followCameraX, followCameraZ);
                const followCameraY = Math.max(soulPosition.y + 2.5, followTerrainHeight + 1.5);
                
                camera.position.set(
                    followCameraX,
                    followCameraY,
                    followCameraZ
                );
                camera.lookAt(soulPosition.x, soulPosition.y + 1.5, soulPosition.z);
                controls.target.set(soulPosition.x, soulPosition.y + 1.5, soulPosition.z);
                controls.enableRotate = false;
                controls.enableZoom = false;
                controls.enablePan = false;
                break;

            case 'front':
                // Front-facing view of the focused soul - terrain aware
                const frontCameraX = soulPosition.x + 2;
                const frontCameraZ = soulPosition.z + 2;
                const frontTerrainHeight = getTerrainHeight(frontCameraX, frontCameraZ);
                const frontCameraY = Math.max(soulPosition.y + 0.8, frontTerrainHeight + 1.0);
                
                camera.position.set(
                    frontCameraX,
                    frontCameraY,
                    frontCameraZ
                );
                camera.lookAt(soulPosition.x, soulPosition.y + 1.5, soulPosition.z);
                controls.target.set(soulPosition.x, soulPosition.y + 1.5, soulPosition.z);
                controls.enableRotate = false;
                controls.enableZoom = false;
                controls.enablePan = false;
                break;

            case 'overview':
                // Zoomed out overview of the world
                camera.position.set(0, 25, 25);
                camera.lookAt(0, 0, 0);
                controls.target.set(0, 0, 0);
                controls.enableRotate = true;
                controls.enableZoom = true;
                controls.enablePan = true;
                break;

            default:
                break;
        }

        controls.update();
    };

    // Store camera and controls refs for camera view updates
    const cameraRef = useRef(null);
    const controlsRef = useRef(null);

    // Update camera when view mode changes
    useEffect(() => {
        if (cameraRef.current && controlsRef.current && focusedSoulRef.current) {
            updateCamera(cameraRef.current, controlsRef.current, focusedSoulRef.current);
        }
    }, [cameraView]);

    useEffect(() => {
        if (!mountRef.current) return;

        // Scene
        const scene = new THREE.Scene();
        sceneRef.current = scene;
        
        // Create simple sky background
        scene.background = new THREE.Color(0x87CEEB); // Sky blue
        
        // Create visible sun
        const createSun = () => {
            const sunGeometry = new THREE.SphereGeometry(3, 16, 16);
            const sunMaterial = new THREE.MeshBasicMaterial({ 
                color: 0xFFFACD,
                emissive: 0xFFFF88,
                emissiveIntensity: 0.3
            });
            const sun = new THREE.Mesh(sunGeometry, sunMaterial);
            sun.userData.isSun = true;
            return sun;
        };
        
        const sun = createSun();
        scene.add(sun);
        
        // Enhanced atmospheric fog for depth and scale perception
        scene.fog = new THREE.Fog(0xa8b8c8, 80, 400); // Atmospheric blue-gray fog

        // Camera
        const camera = new THREE.PerspectiveCamera(
            75,
            mountRef.current.clientWidth / mountRef.current.clientHeight,
            0.1,
            1000
        );
        camera.position.set(15, 12, 15);
        camera.lookAt(0, 0, 0);
        cameraRef.current = camera;

        // Optimized Renderer
        const renderer = new THREE.WebGLRenderer({ 
            antialias: false, // Disable for better performance on lower-end devices
            powerPreference: 'high-performance'
        });
        renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Limit pixel ratio for performance
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.shadowMap.autoUpdate = false; // Manual shadow updates for performance
        mountRef.current.appendChild(renderer.domElement);

        // Controls
        const controls = new OrbitControls(camera, renderer.domElement);
        controlsRef.current = controls;

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        scene.add(directionalLight);

        // Enhanced mountainous terrain generation
        const createTerrain = () => {
            const terrainSize = 500;
            const terrainResolution = 150; // Higher resolution for more detailed mountains
            
            // Create heightmap for dramatic mountainous landscape
            const geometry = new THREE.PlaneGeometry(terrainSize, terrainSize, terrainResolution, terrainResolution);
            const vertices = geometry.attributes.position.array;
            const colors = new Float32Array(vertices.length);
            
            // Generate dramatic mountainous terrain
            for (let i = 0; i < vertices.length; i += 3) {
                const x = vertices[i];
                const z = vertices[i + 1];
                
                // Use the same height calculation as getTerrainHeight
                const height = getTerrainHeight(x, z);
                vertices[i + 2] = height;
                
                // Enhanced color variation based on height and slope
                const heightRatio = Math.max(0, Math.min(1, (height + 10) / 60)); // Normalize for wider height range
                
                // Calculate slope for more realistic coloring
                const nearby1 = getTerrainHeight(x + 1, z);
                const nearby2 = getTerrainHeight(x, z + 1);
                const slope = Math.abs(height - nearby1) + Math.abs(height - nearby2);
                const slopeRatio = Math.min(1, slope / 5);
                
                // Color based on elevation and slope
                let baseR, baseG, baseB;
                
                if (height > 15) {
                    // High peaks - rocky gray/brown
                    baseR = 0.4 + slopeRatio * 0.2;
                    baseG = 0.35 + slopeRatio * 0.15;
                    baseB = 0.3 + slopeRatio * 0.1;
                } else if (height > 5) {
                    // Mid elevation - brown/tan
                    baseR = 0.6 + heightRatio * 0.2;
                    baseG = 0.5 + heightRatio * 0.15;
                    baseB = 0.3 + heightRatio * 0.1;
                } else if (height > -1) {
                    // Lower areas - darker earth tones
                    baseR = 0.45 + heightRatio * 0.15;
                    baseG = 0.4 + heightRatio * 0.1;
                    baseB = 0.25 + heightRatio * 0.05;
                } else {
                    // Valley floors - darker, richer earth
                    baseR = 0.3;
                    baseG = 0.25;
                    baseB = 0.15;
                }
                
                // Add some noise for natural variation
                const noise = (Math.sin(x * 0.1) * Math.cos(z * 0.1)) * 0.1;
                
                colors[i] = Math.max(0.1, Math.min(1, baseR + noise));
                colors[i + 1] = Math.max(0.1, Math.min(1, baseG + noise));
                colors[i + 2] = Math.max(0.1, Math.min(1, baseB + noise));
            }
            
            geometry.attributes.position.needsUpdate = true;
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
            geometry.computeVertexNormals();
            
            // Enhanced material for mountainous terrain
            const material = new THREE.MeshLambertMaterial({ 
                vertexColors: true,
                flatShading: false
            });
            
            const terrain = new THREE.Mesh(geometry, material);
            terrain.rotation.x = -Math.PI / 2;
            terrain.receiveShadow = true;
            terrain.castShadow = true;
            
            return terrain;
        };
        
        const terrain = createTerrain();
        scene.add(terrain);

        // Initialize procedural avatar system
        avatarSystemRef.current = new ProceduralAvatar();
        console.log('Procedural avatar system initialized');

        // Performance-optimized animation loop with time system
        let lastTime = performance.now();
        let lightingUpdateCounter = 0;
        let timeUpdateCounter = 0;
        
        // Local time tracking for immediate updates
        let localWorldTime = {
            day: 1,
            hour: 12,
            minute: 0,
            timeSpeed: 1
        };
        
        
        const animate = (currentTime) => {
            requestAnimationFrame(animate);
            
            const deltaTime = (currentTime - lastTime) / 1000; // Convert to seconds
            lastTime = currentTime;
            
            // Update local world time every frame for immediate lighting updates
            let newMinute = localWorldTime.minute + (localWorldTime.timeSpeed / 60);
            let newHour = localWorldTime.hour;
            let newDay = localWorldTime.day;
            
            if (newMinute >= 60) {
                newHour += Math.floor(newMinute / 60);
                newMinute = newMinute % 60;
            }
            
            if (newHour >= 24) {
                newDay += Math.floor(newHour / 24);
                newHour = newHour % 24;
            }
            
            localWorldTime = {
                ...localWorldTime,
                day: newDay,
                hour: newHour,
                minute: newMinute
            };
            
            // Update React state more frequently for real-time display (every 60 frames = 1 second)
            timeUpdateCounter++;
            if (timeUpdateCounter >= 60) {
                setWorldTime({...localWorldTime});
                timeUpdateCounter = 0;
            }
            
            // Update lighting every frame with local time for immediate visual changes
            updateLighting(scene, localWorldTime.hour, localWorldTime.minute);
            
            // Update avatar behaviors every frame for smooth movement
            updateAvatarBehaviors(deltaTime);
            
            // Update camera based on view mode and focused soul
            if (focusedSoulRef.current && cameraView !== 'overview') {
                updateCamera(camera, controls, focusedSoulRef.current);
            } else if (cameraView === 'overview') {
                updateCamera(camera, controls, null);
            } else {
                controls.update();
            }
            
            renderer.render(scene, camera);
        };
        animate(performance.now());

        // Load world data after scene is set up
        setTimeout(() => {
            loadWorldData();
        }, 200);

        // Cleanup
        return () => {
            try {
                if (mountRef.current && renderer.domElement && mountRef.current.contains(renderer.domElement)) {
                    mountRef.current.removeChild(renderer.domElement);
                }
                renderer.dispose();
            } catch (error) {
                console.warn('Error during cleanup:', error);
            }
        };
    }, []);

    return (
        <div style={{ 
            width: '100vw', 
            height: '100vh', 
            position: 'fixed',
            top: 0,
            left: 0,
            overflow: 'hidden'
        }}>
            <Header 
                username={username}
                balance={walletBalance}
                walletAddress={soulData?.creator_wallet}
                worldTime={worldTime}
                cameraView={cameraView}
                onBack={handleGoBack}
                onCopyAddress={handleCopyAddress}
                onCameraViewChange={handleCameraViewChange}
            />
            <div 
                ref={mountRef} 
                style={{ 
                    width: '100%', 
                    height: '100vh',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    overflow: 'hidden'
                }} 
            />
        </div>
    );
};

export default WorldViewer;