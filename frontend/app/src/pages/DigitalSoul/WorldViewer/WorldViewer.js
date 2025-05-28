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
    
    // State for soul data
    const [worldData, setWorldData] = useState(null);
    const [soulData, setSoulData] = useState(null);
    const [walletBalance, setWalletBalance] = useState(0);
    const [loading, setLoading] = useState(true);
    
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

    // Render procedural avatars
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

                // Position avatar based on soul position
                avatarGroup.position.set(
                    soul.position.x * 0.1, // Scale down positions
                    0,
                    soul.position.z * 0.1
                );

                // Add name label
                addNameLabel(avatarGroup, soul.name || soul.username, soul.is_focused);

                sceneRef.current.add(avatarGroup);
                console.log(`Created procedural avatar for ${soul.username} at position:`, avatarGroup.position);
                
            } catch (error) {
                console.error(`Error creating procedural avatar for ${soul.username}:`, error);
                
                // Fallback to simple avatar
                const fallbackAvatar = createFallbackAvatar(soul);
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

        group.position.set(
            soul.position.x * 0.1,
            0,
            soul.position.z * 0.1
        );

        addNameLabel(group, soul.name || soul.username, soul.is_focused);

        return group;
    };

    useEffect(() => {
        if (!mountRef.current) return;

        // Scene
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x8B7355); // Barren brown-tan color
        scene.fog = new THREE.Fog(0x8B7355, 50, 200); // Add atmospheric fog
        sceneRef.current = scene;

        // Camera
        const camera = new THREE.PerspectiveCamera(
            75,
            mountRef.current.clientWidth / mountRef.current.clientHeight,
            0.1,
            1000
        );
        camera.position.set(15, 12, 15);
        camera.lookAt(0, 0, 0);

        // Renderer
        const renderer = new THREE.WebGLRenderer();
        renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        mountRef.current.appendChild(renderer.domElement);

        // Controls
        const controls = new OrbitControls(camera, renderer.domElement);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        scene.add(directionalLight);

        // Create mountainous terrain
        const createTerrain = () => {
            const terrainSize = 200;
            const terrainResolution = 100;
            
            // Create heightmap for mountains
            const geometry = new THREE.PlaneGeometry(terrainSize, terrainSize, terrainResolution, terrainResolution);
            const vertices = geometry.attributes.position.array;
            
            // Generate mountainous terrain using noise
            for (let i = 0; i < vertices.length; i += 3) {
                const x = vertices[i];
                const z = vertices[i + 1];
                
                // Create multiple layers of noise for realistic mountains
                let height = 0;
                
                // Base mountain ridges
                height += Math.sin(x * 0.02) * Math.cos(z * 0.02) * 8;
                
                // Secondary peaks
                height += Math.sin(x * 0.05) * Math.cos(z * 0.05) * 4;
                
                // Fine detail roughness
                height += (Math.random() - 0.5) * 2;
                
                // Distance-based height falloff for natural look
                const distance = Math.sqrt(x * x + z * z);
                const falloff = Math.max(0, 1 - distance / (terrainSize * 0.3));
                height *= falloff;
                
                vertices[i + 2] = height; // Set Y (height) coordinate
            }
            
            geometry.attributes.position.needsUpdate = true;
            geometry.computeVertexNormals();
            
            // Create barren landscape material
            const material = new THREE.MeshLambertMaterial({ 
                color: 0x8B6F47, // Dark tan/brown
                flatShading: true
            });
            
            const terrain = new THREE.Mesh(geometry, material);
            terrain.rotation.x = -Math.PI / 2;
            terrain.receiveShadow = true;
            terrain.castShadow = true;
            
            return terrain;
        };
        
        const terrain = createTerrain();
        scene.add(terrain);
        
        // Add some scattered rocks for detail
        const createRocks = () => {
            const rockGroup = new THREE.Group();
            
            for (let i = 0; i < 15; i++) {
                const rockGeometry = new THREE.DodecahedronGeometry(
                    0.3 + Math.random() * 0.7, // Varying sizes
                    0 // Low detail for performance
                );
                
                const rockMaterial = new THREE.MeshLambertMaterial({ 
                    color: new THREE.Color().setHSL(0.08, 0.3, 0.2 + Math.random() * 0.2) // Various browns/grays
                });
                
                const rock = new THREE.Mesh(rockGeometry, rockMaterial);
                
                // Random positioning
                rock.position.set(
                    (Math.random() - 0.5) * 30,
                    0.5,
                    (Math.random() - 0.5) * 30
                );
                
                // Random rotation
                rock.rotation.set(
                    Math.random() * Math.PI,
                    Math.random() * Math.PI,
                    Math.random() * Math.PI
                );
                
                // Random scale
                const scale = 0.5 + Math.random() * 1.5;
                rock.scale.set(scale, scale, scale);
                
                rock.castShadow = true;
                rock.receiveShadow = true;
                
                rockGroup.add(rock);
            }
            
            return rockGroup;
        };
        
        const rocks = createRocks();
        scene.add(rocks);

        // Initialize procedural avatar system
        avatarSystemRef.current = new ProceduralAvatar();
        console.log('Procedural avatar system initialized');

        // Animation loop
        const animate = () => {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        };
        animate();

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
                onBack={handleGoBack}
                onCopyAddress={handleCopyAddress}
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