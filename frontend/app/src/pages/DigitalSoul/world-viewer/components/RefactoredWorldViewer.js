/**
 * Refactored World Viewer for Digital Souls
 * Uses the new modular component system for better organization and maintainability
 */

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import { ArrowLeftIcon, ClipboardIcon } from '@heroicons/react/24/outline';

// Import our new component systems
import AvatarManager from '../avatars/AvatarManager.js';
import WorldEnvironment from '../environments/WorldEnvironment.js';
import CameraController from './CameraController.js';

// Import CSS
import '../../WorldViewer/WorldViewer.css';

const RefactoredWorldViewer = () => {
    const { username } = useParams();
    const navigate = useNavigate();
    
    // React refs
    const mountRef = useRef(null);
    const sceneRef = useRef(null);
    const rendererRef = useRef(null);
    const animationRef = useRef(null);
    
    // Component system refs
    const avatarManagerRef = useRef(null);
    const worldEnvironmentRef = useRef(null);
    const cameraControllerRef = useRef(null);
    
    // State
    const [worldData, setWorldData] = useState(null);
    const [soulData, setSoulData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [walletBalance, setWalletBalance] = useState(0);
    const [lastUpdateTime, setLastUpdateTime] = useState(Date.now());
    const [threeJSInitialized, setThreeJSInitialized] = useState(false);

    // Initialize Three.js scene with new component system
    const initThreeJS = () => {
        if (threeJSInitialized) {
            console.log('Three.js already initialized');
            return;
        }

        console.log('Initializing Three.js with new component system');
        
        if (!mountRef.current) {
            console.error('Mount element not found');
            return;
        }

        // Scene setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x87CEEB); // Sky blue
        sceneRef.current = scene;

        // Camera setup
        const camera = new THREE.PerspectiveCamera(
            45,
            mountRef.current.clientWidth / mountRef.current.clientHeight,
            0.1,
            1000
        );

        // Renderer setup
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.setClearColor(0x87CEEB, 1);
        
        mountRef.current.appendChild(renderer.domElement);
        rendererRef.current = renderer;

        // Initialize component systems
        avatarManagerRef.current = new AvatarManager(scene);
        worldEnvironmentRef.current = new WorldEnvironment(scene);
        cameraControllerRef.current = new CameraController(camera, renderer);

        // Setup environment
        worldEnvironmentRef.current.initializeEnvironment();

        // Mark as initialized
        setThreeJSInitialized(true);
        console.log('Three.js initialization complete');

        // Animation loop
        const animate = () => {
            animationRef.current = requestAnimationFrame(animate);
            
            const currentTime = Date.now();
            const deltaTime = currentTime - lastUpdateTime;
            
            // Update all systems
            if (avatarManagerRef.current) {
                avatarManagerRef.current.updateAvatars(deltaTime);
            }
            
            if (worldEnvironmentRef.current) {
                worldEnvironmentRef.current.update(deltaTime);
            }
            
            if (cameraControllerRef.current) {
                cameraControllerRef.current.update();
            }
            
            renderer.render(scene, camera);
            setLastUpdateTime(currentTime);
        };
        
        animate();
        
        // Handle window resize
        const handleResize = () => {
            if (mountRef.current && cameraControllerRef.current) {
                const width = mountRef.current.clientWidth;
                const height = mountRef.current.clientHeight;
                cameraControllerRef.current.handleResize(width, height);
            }
        };
        
        window.addEventListener('resize', handleResize);
        
        return () => {
            window.removeEventListener('resize', handleResize);
        };
    };

    // Load world data (shared or single soul)
    const loadWorldData = async () => {
        // Wait for Three.js to be initialized
        if (!threeJSInitialized) {
            console.log('Waiting for Three.js initialization before loading world data...');
            return;
        }

        try {
            setLoading(true);
            setError(null);

            console.log(`Loading world for username: ${username}`);

            // Import multiSoulService for shared world
            const { default: multiSoulService } = await import('../../../../services/multiSoulService');
            const result = await multiSoulService.loadSharedWorld(username);
            
            console.log('World data received:', result);

            if (!result.success) {
                throw new Error(result.error || 'Failed to load world');
            }

            const worldData = result.world_data;
            
            // Find and set focused soul data
            const focusedSoul = worldData.souls.find(soul => soul.is_focused);
            if (focusedSoul) {
                setSoulData(focusedSoul);
                console.log('Focused soul data:', focusedSoul);

                // Fetch wallet balance if creator wallet is available
                if (focusedSoul?.creator_wallet) {
                    fetchWalletBalance(focusedSoul.creator_wallet);
                }
            }

            // Set world data and render
            setWorldData(worldData);
            console.log('About to render world, checking component systems...');
            console.log('Avatar Manager:', !!avatarManagerRef.current);
            console.log('World Environment:', !!worldEnvironmentRef.current);
            console.log('Camera Controller:', !!cameraControllerRef.current);
            
            renderWorld(worldData);
            
            console.log(`Loaded world with ${worldData.souls.length} souls`);
            
        } catch (err) {
            console.error('Error loading world data:', err);
            setError('Failed to connect to server');
        } finally {
            setLoading(false);
        }
    };

    // Render world using new component system
    const renderWorld = (worldData) => {
        if (!worldData) {
            console.error('Missing world data');
            return;
        }

        // Wait for component systems to be initialized
        if (!avatarManagerRef.current || !cameraControllerRef.current || !worldEnvironmentRef.current) {
            console.log('Component systems not ready, retrying in 100ms...');
            setTimeout(() => renderWorld(worldData), 100);
            return;
        }

        console.log('Rendering world with new component system:', worldData);

        // Clear existing avatars
        avatarManagerRef.current.clearAllAvatars();

        if (worldData.type === 'multi_soul') {
            renderMultiSoulWorld(worldData);
        } else {
            renderSingleSoulWorld(worldData);
        }
    };

    // Render multi-soul shared world
    const renderMultiSoulWorld = (worldData) => {
        console.log('Rendering multi-soul world with procedural avatars', worldData);

        // Create avatars for all souls
        const avatarPositions = [];
        
        worldData.souls.forEach((soul, index) => {
            console.log(`Creating avatar for soul ${index}:`, soul);
            
            try {
                const avatar = avatarManagerRef.current.createSoulAvatar(
                    soul,
                    soul.position,
                    soul.is_focused
                );
                
                if (avatar) {
                    avatarPositions.push(soul.position);
                    console.log(`Avatar created successfully at position:`, soul.position);
                } else {
                    console.error(`Failed to create avatar for soul:`, soul);
                }
            } catch (error) {
                console.error(`Error creating avatar for soul ${soul.username}:`, error);
            }
        });

        // Position camera to frame all souls
        if (avatarPositions.length > 0) {
            cameraControllerRef.current.frameAllSouls(avatarPositions);
            console.log(`Camera positioned to frame ${avatarPositions.length} avatars`);
        } else {
            console.error('No avatars created, cannot position camera');
        }

        console.log(`Created ${avatarPositions.length} procedural avatars out of ${worldData.souls.length} souls`);
    };

    // Render single soul world (room environment)
    const renderSingleSoulWorld = (worldData) => {
        console.log('Rendering single soul world');

        // Switch to room environment
        worldEnvironmentRef.current.createRoomEnvironment();
        
        // Create single avatar
        const soulPosition = worldData.soul_spawn_point || { x: 0, y: 0, z: 0 };
        avatarManagerRef.current.createSoulAvatar(
            soulData,
            soulPosition,
            true
        );

        // Set camera for room view
        cameraControllerRef.current.setupRoomView();
        cameraControllerRef.current.focusOnSoul(soulPosition);
    };

    // Fetch wallet balance
    const fetchWalletBalance = async (creatorWallet) => {
        try {
            if (!creatorWallet) {
                console.log('No creator wallet provided, skipping balance fetch');
                return;
            }

            const { default: walletService } = await import('../../../../services/api/walletService');
            const balanceInfo = await walletService.getBalance(creatorWallet);
            
            if (balanceInfo && typeof balanceInfo.balance === 'number') {
                setWalletBalance(balanceInfo.balance);
                console.log('Fetched balance for creator wallet:', creatorWallet, 'Balance:', balanceInfo.balance);
            } else {
                console.log('Failed to fetch balance, no valid balance returned:', balanceInfo);
                setWalletBalance(0);
            }
        } catch (error) {
            console.error('Error fetching wallet balance:', error);
            setWalletBalance(0);
        }
    };

    // Utility functions
    const truncateAddress = (address) => {
        if (!address) return '';
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    };

    const copyAddress = async () => {
        if (!soulData?.creator_wallet) return;
        
        try {
            await navigator.clipboard.writeText(soulData.creator_wallet);
            console.log('Address copied to clipboard');
        } catch (err) {
            console.error('Failed to copy address:', err);
        }
    };

    const handleGoBack = () => {
        navigate(`/app/soul/${username}`);
    };

    // Initialize Three.js when component mounts
    useEffect(() => {
        const timeoutId = setTimeout(() => {
            initThreeJS();
        }, 100);
        
        // Store mount ref to avoid stale closure
        const currentMount = mountRef.current;

        return () => {
            clearTimeout(timeoutId);
            
            // Cleanup Three.js resources
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
            
            // Safe cleanup of renderer DOM element  
            if (rendererRef.current?.domElement && currentMount?.contains(rendererRef.current.domElement)) {
                try {
                    currentMount.removeChild(rendererRef.current.domElement);
                    rendererRef.current.dispose();
                } catch (error) {
                    console.warn('Error disposing renderer:', error);
                }
            }
            
            // Cleanup component systems
            if (avatarManagerRef.current) {
                avatarManagerRef.current.clearAllAvatars();
            }
            
            if (worldEnvironmentRef.current) {
                worldEnvironmentRef.current.clearEnvironment();
            }
            
            if (cameraControllerRef.current) {
                cameraControllerRef.current.dispose();
            }
        };
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Load world data when Three.js is initialized
    useEffect(() => {
        if (threeJSInitialized) {
            loadWorldData();
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [threeJSInitialized, username]);

    // Error state
    if (error) {
        return (
            <div className="world-viewer">
                <div className="error-container">
                    <h2>Error Loading World</h2>
                    <p>{error}</p>
                    <button onClick={handleGoBack} className="back-button">
                        <ArrowLeftIcon className="w-4 h-4 mr-2" />
                        Go Back
                    </button>
                </div>
            </div>
        );
    }

    // Loading state
    if (loading) {
        return (
            <div className="world-viewer">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p>Loading world...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="world-viewer">
            {/* Header with soul stats */}
            <div className="header">
                <div className="header-left">
                    <button onClick={handleGoBack} className="back-button">
                        <ArrowLeftIcon className="w-4 h-4 mr-2" />
                        Back
                    </button>
                    <h1 style={{ fontFamily: 'Helvetica, Arial, sans-serif', fontSize: '1.25rem', fontWeight: '600' }}>
                        Digital Soul World: {username}
                    </h1>
                </div>
                
                <div className="header-right">
                    {/* Soul Statistics */}
                    {worldData && worldData.type === 'multi_soul' && (
                        <div className="soul-stats">
                            <div className="stat-item">
                                <span className="stat-label">Total Souls:</span>
                                <span className="stat-value">{worldData.souls?.length || 0}</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">World Size:</span>
                                <span className="stat-value">{worldData.size?.width || 100}m²</span>
                            </div>
                        </div>
                    )}
                    
                    {/* Wallet Information */}
                    <div className="header-bottom">
                        <div className="wallet-balance">
                            <span className="balance-amount">{walletBalance.toFixed(2)} GCN</span>
                        </div>
                        {soulData?.creator_wallet ? (
                            <div className="wallet-address">
                                <span className="address-text">{truncateAddress(soulData.creator_wallet)}</span>
                                <button 
                                    onClick={copyAddress}
                                    className="copy-btn"
                                    title="Copy address"
                                >
                                    <ClipboardIcon className="w-4 h-4" />
                                </button>
                            </div>
                        ) : (
                            <div className="wallet-address">
                                <span className="address-text">No wallet</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* 3D World Container */}
            <div 
                ref={mountRef} 
                className="world-container"
                style={{ 
                    width: '100%', 
                    height: 'calc(100vh - 80px)',
                    position: 'relative',
                    overflow: 'hidden'
                }}
            />

            {/* Debug Info (development only) */}
            {process.env.NODE_ENV === 'development' && worldData && (
                <div className="debug-info">
                    <p>Souls: {worldData.souls?.length || 0}</p>
                    <p>Type: {worldData.type}</p>
                    <p>Procedural Avatars: Enabled</p>
                </div>
            )}
        </div>
    );
};

export default RefactoredWorldViewer;