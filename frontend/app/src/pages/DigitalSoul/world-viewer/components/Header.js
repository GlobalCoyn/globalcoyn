/**
 * Header Component for Digital Soul World Viewer
 */

import React from 'react';
import { ChevronLeftIcon } from '@heroicons/react/24/solid';
import { ClipboardIcon } from '@heroicons/react/24/outline';

const Header = ({ 
    username, 
    balance = 0, 
    walletAddress = null, 
    worldTime = null,
    cameraView = 'follow',
    onBack, 
    onCopyAddress,
    onCameraViewChange
}) => {
    
    const truncateAddress = (address) => {
        if (!address) return '';
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    };

    const formatWorldTime = (time) => {
        if (!time) return 'Day 1 - 12:00';
        const hour = Math.floor(time.hour);
        const minute = Math.floor(time.minute);
        const period = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
        return `Day ${time.day} - ${displayHour}:${minute.toString().padStart(2, '0')} ${period}`;
    };

    const getCameraViewLabel = (view) => {
        switch (view) {
            case 'follow': return 'Follow';
            case 'front': return 'Front';
            case 'overview': return 'Overview';
            default: return 'Follow';
        }
    };

    return (
        <div className="header" style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 10,
            background: 'transparent',
            padding: '0.5rem 1rem',
            height: '80px'
        }}>
            {/* Top row - Back button, title, and wallet info on left, connect wallet on right */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <button 
                        onClick={onBack}
                        style={{
                            padding: '0.25rem 0.5rem',
                            border: 'none',
                            background: '#e5e7eb',
                            cursor: 'pointer',
                            color: '#000000',
                            borderRadius: '0.375rem',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            minHeight: '1.5rem'
                        }}
                    >
                        <ChevronLeftIcon style={{ width: '1rem', height: '1rem' }} />
                    </button>
                    
                    {/* World Time Display */}
                    <div style={{ 
                        fontSize: '0.75rem', 
                        fontWeight: '400',
                        margin: 0,
                        color: '#000000',
                        background: '#e5e7eb',
                        borderRadius: '0.375rem',
                        padding: '0.25rem 0.5rem'
                    }}>
                        <span style={{ fontWeight: '700' }}>{formatWorldTime(worldTime)}</span>
                    </div>
                    
                    <div style={{ 
                        fontSize: '0.75rem', 
                        fontWeight: '400',
                        margin: 0,
                        color: '#000000',
                        background: '#e5e7eb',
                        borderRadius: '0.375rem',
                        padding: '0.25rem 0.5rem'
                    }}>
                        Soul: <span style={{ fontWeight: '700' }}>{username}</span>
                    </div>
                    
                    {/* Balance */}
                    <div style={{
                        padding: '0.25rem 0.5rem',
                        fontSize: '0.75rem',
                        fontWeight: '400',
                        color: '#000000',
                        background: '#e5e7eb',
                        borderRadius: '0.375rem'
                    }}>
                        <span style={{ fontWeight: '700' }}>{balance.toFixed(2)}</span> GCN
                    </div>
                
                    {/* Wallet Address */}
                    {walletAddress ? (
                        <div style={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: '0.25rem',
                            padding: '0.25rem 0.5rem',
                            background: '#e5e7eb',
                            borderRadius: '0.375rem'
                        }}>
                            <span style={{ 
                                fontSize: '0.75rem', 
                                color: '#fb923c',
                                fontFamily: 'monospace'
                            }}>
                                {truncateAddress(walletAddress)}
                            </span>
                            <button 
                                onClick={onCopyAddress}
                                style={{
                                    padding: '0.125rem',
                                    border: 'none',
                                    background: 'transparent',
                                    cursor: 'pointer',
                                    color: '#000000',
                                    borderRadius: '0.25rem'
                                }}
                                title="Copy address"
                            >
                                <ClipboardIcon style={{ width: '0.75rem', height: '0.75rem' }} />
                            </button>
                        </div>
                    ) : (
                        <span style={{ 
                            fontSize: '0.75rem', 
                            color: '#000000',
                            background: '#e5e7eb',
                            borderRadius: '0.375rem',
                            padding: '0.25rem 0.5rem'
                        }}>
                            No wallet
                        </span>
                    )}
                    
                    {/* Camera View Button */}
                    <button 
                        onClick={onCameraViewChange}
                        style={{
                            padding: '0.25rem 0.5rem',
                            border: 'none',
                            background: '#e5e7eb',
                            cursor: 'pointer',
                            color: '#000000',
                            borderRadius: '0.375rem',
                            fontSize: '0.75rem',
                            fontWeight: '500'
                        }}
                        title="Switch camera view"
                    >
                        📹 {getCameraViewLabel(cameraView)}
                    </button>
                </div>
                
                {/* Connect Wallet and Version Info on the right */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ 
                        fontSize: '0.75rem', 
                        fontWeight: '500',
                        color: '#000000',
                        background: '#e5e7eb',
                        borderRadius: '0.375rem',
                        padding: '0.25rem 0.5rem',
                        cursor: 'pointer'
                    }}>
                        Connect Wallet
                    </div>
                    
                    {/* Version Info */}
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        padding: '0.25rem 0.5rem',
                        background: '#f3f4f6',
                        borderRadius: '0.375rem',
                        fontSize: '0.75rem',
                        color: '#000000'
                    }}>
                        <svg 
                            style={{ width: '0.75rem', height: '0.75rem' }} 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                        >
                            <path 
                                strokeLinecap="round" 
                                strokeLinejoin="round" 
                                strokeWidth={2} 
                                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
                            />
                        </svg>
                        <span style={{ fontWeight: '500' }}>v1.0.0</span>
                    </div>
                </div>
            </div>
            
            {/* Empty bottom row for spacing */}
            <div style={{ height: '1rem' }}></div>
        </div>
    );
};

export default Header;