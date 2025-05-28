/**
 * Simple World Viewer with Procedural Avatars
 * Uses the working structure but with procedural avatar system
 */

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { ArrowLeftIcon, ClipboardIcon } from '@heroicons/react/24/outline';

// Import avatar system
import AvatarManager from '../avatars/AvatarManager.js';
import WorldEnvironment from '../environments/WorldEnvironment.js';

// Import CSS
import '../../WorldViewer/WorldViewer.css';

const SimpleWorldViewer = () => {
    const { username } = useParams();
    const navigate = useNavigate();
    const mountRef = useRef(null);
    const sceneRef = useRef(null);
    const rendererRef = useRef(null);
    const animationRef = useRef(null);
    const controlsRef = useRef(null);
    
    // Component system refs
    const avatarManagerRef = useRef(null);
    const worldEnvironmentRef = useRef(null);
    
    const [worldData, setWorldData] = useState(null);
    const [soulData, setSoulData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [walletBalance, setWalletBalance] = useState(0);

    // Initialize Three.js scene
    const initThreeJS = () => {
        console.log('initThreeJS called');
        if (!mountRef.current) {
            console.error('mountRef.current is null');
            return false;
        }

        console.log('Mount element:', mountRef.current);

        // Scene setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x87CEEB);
        sceneRef.current = scene;
        console.log('Scene created:', scene);

        // Camera setup
        const camera = new THREE.PerspectiveCamera(
            45,
            mountRef.current.clientWidth / mountRef.current.clientHeight,
            0.1,
            1000
        );
        camera.position.set(8, 8, 8);
        camera.lookAt(2, 0, 2);

        // Renderer setup
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        console.log('Renderer created:', renderer);
        
        const width = mountRef.current.clientWidth;
        const height = mountRef.current.clientHeight;
        console.log('Canvas size:', { width, height });
        
        renderer.setSize(width, height);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        
        console.log('Appending canvas to mount element');
        mountRef.current.appendChild(renderer.domElement);
        rendererRef.current = renderer;

        // Controls
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.autoRotate = false;
        controls.enableRotate = false;
        controls.enablePan = true;
        controls.enableZoom = true;
        controls.target.set(2, 0, 2);
        controls.minDistance = 5;
        controls.maxDistance = 15;
        controlsRef.current = controls;

        // Initialize component systems
        try {
            avatarManagerRef.current = new AvatarManager(scene);
            worldEnvironmentRef.current = new WorldEnvironment(scene);
            console.log('Component systems initialized successfully');

            // Setup basic environment
            worldEnvironmentRef.current.initializeEnvironment();
            console.log('World environment initialized');
        } catch (error) {
            console.error('Error initializing component systems:', error);
        }

        // Animation loop
        const animate = () => {
            animationRef.current = requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        };
        animate();
        
        console.log('Three.js initialization complete');
        return true;
    };

    // Load world data
    const loadWorldData = async () => {
        try {
            setLoading(true);
            setError(null);

            console.log(`Loading shared world for username: ${username}`);

            const { default: multiSoulService } = await import('../../../../services/multiSoulService');
            const result = await multiSoulService.loadSharedWorld(username);
            
            console.log('Shared world data received:', result);

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
            renderWorld(worldData);
            
            console.log(`Loaded shared world with ${worldData.souls.length} souls`);
        } catch (err) {
            console.error('Error loading world data:', err);
            setError('Failed to connect to server');
        } finally {
            setLoading(false);
        }
    };

    // Render world
    const renderWorld = (worldData, retryCount = 0) => {
        if (!worldData) {
            console.error('Missing world data');
            return;
        }
        
        if (!sceneRef.current || !avatarManagerRef.current) {
            if (retryCount < 10) {
                console.log(`Scene or avatar manager not ready, retry ${retryCount + 1}/10...`);
                setTimeout(() => renderWorld(worldData, retryCount + 1), 100);
                return;
            } else {
                console.error('Failed to initialize after 10 retries, giving up');
                setError('Failed to initialize 3D world');
                return;
            }
        }

        console.log('renderWorld called with:', worldData);
        console.log('Scene available:', !!sceneRef.current);
        console.log('Avatar Manager available:', !!avatarManagerRef.current);

        // Clear existing avatars
        avatarManagerRef.current.clearAllAvatars();

        if (worldData.type === 'multi_soul') {
            renderMultiSoulWorld(worldData);
        }
    };

    // Render multi-soul world
    const renderMultiSoulWorld = (worldData) => {
        console.log('Rendering multi-soul world with procedural avatars');

        // Create procedural avatars for all souls
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
                }
            } catch (error) {
                console.error(`Error creating avatar for soul ${soul.username}:`, error);
            }
        });

        // Position camera to frame all souls
        if (avatarPositions.length > 0 && controlsRef.current) {
            const center = { x: 50, y: 50 };
            controlsRef.current.target.set(center.x, 0, center.y);
            controlsRef.current.update();
            console.log(`Camera positioned to frame ${avatarPositions.length} avatars`);
        }

        console.log(`Created ${avatarPositions.length} procedural avatars`);
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

    // Effects
    useEffect(() => {
        // Simple delay for DOM to render
        const timeoutId = setTimeout(() => {
            const success = initThreeJS();
            if (success) {
                // Wait for Three.js then load data
                setTimeout(() => {
                    loadWorldData();
                }, 200);
            } else {
                // If init failed, stop loading and show error
                setLoading(false);
                setError('Failed to initialize 3D renderer');
            }
        }, 100);
        
        // Store mount ref to avoid stale closure
        const currentMount = mountRef.current;

        return () => {
            clearTimeout(timeoutId);
            
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
            
            if (rendererRef.current && currentMount) {
                try {
                    if (currentMount.contains(rendererRef.current.domElement)) {
                        currentMount.removeChild(rendererRef.current.domElement);
                    }
                } catch (error) {
                    console.warn('Error removing canvas:', error);
                }
                rendererRef.current.dispose();
            }
        };
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [username]);

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
            {/* Header */}
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
        </div>
    );
};

export default SimpleWorldViewer;