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
    onBack, 
    onCopyAddress 
}) => {
    
    const truncateAddress = (address) => {
        if (!address) return '';
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
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
                </div>
                
                {/* Connect Wallet on the right */}
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
            </div>
            
            {/* Empty bottom row for spacing */}
            <div style={{ height: '1rem' }}></div>
        </div>
    );
};

export default Header;