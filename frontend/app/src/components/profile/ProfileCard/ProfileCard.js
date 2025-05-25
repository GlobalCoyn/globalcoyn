import React from 'react';
import './ProfileCard.css';

const ProfileCard = ({ 
  profile, 
  isOwner = false, 
  onEdit = null,
  showEditButton = false,
  compact = false,
  isCurrent = false
}) => {
  const {
    alias,
    bio,
    ipfsHash,
    lastUpdated,
    walletAddress
  } = profile || {};

  const getProfileImageUrl = (hash) => {
    if (!hash) return null;
    return `https://gateway.pinata.cloud/ipfs/${hash}`;
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return '';
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  if (compact) {
    return (
      <div className="profile-card compact">
        <div className="profile-image-container">
          {ipfsHash ? (
            <img 
              src={getProfileImageUrl(ipfsHash)} 
              alt={alias || 'Profile'} 
              className="profile-image"
            />
          ) : (
            <div className="profile-image-placeholder">
              {alias ? alias.charAt(0).toUpperCase() : '?'}
            </div>
          )}
        </div>
        <div className="profile-info">
          <h4 className="profile-alias">{alias || 'Anonymous'}</h4>
          <div className="profile-address-row">
            <p className="profile-address">{formatAddress(walletAddress)}</p>
            {isCurrent && <span className="current-badge">Current</span>}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-card">
      <div className="profile-card-header">
        <div className="profile-image-container">
          {ipfsHash ? (
            <img 
              src={getProfileImageUrl(ipfsHash)} 
              alt={alias || 'Profile'} 
              className="profile-image"
            />
          ) : (
            <div className="profile-image-placeholder">
              {alias ? alias.charAt(0).toUpperCase() : '?'}
            </div>
          )}
        </div>
        <div className="profile-header-info">
          <h2 className="profile-alias">{alias || 'Anonymous User'}</h2>
          <div className="profile-address-row">
            <p className="profile-address">{formatAddress(walletAddress)}</p>
            {isCurrent && <span className="current-badge">Current</span>}
          </div>
          {lastUpdated && (
            <p className="profile-updated">Updated {formatDate(lastUpdated)}</p>
          )}
        </div>
        {showEditButton && isOwner && onEdit && (
          <button className="edit-profile-btn" onClick={onEdit}>
            Edit Profile
          </button>
        )}
      </div>
      
      {bio && (
        <div className="profile-card-body">
          <h3>About</h3>
          <p className="profile-bio">{bio}</p>
        </div>
      )}
    </div>
  );
};

export default ProfileCard;