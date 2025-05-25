import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ProfileCard from '../../components/profile/ProfileCard/ProfileCard';
import ProfileEditor from '../../components/profile/ProfileEditor/ProfileEditor';
import Button from '../../components/common/Button/Button';
import profileService from '../../services/api/profileService';
import './Profile.css';

const Profile = () => {
  const { address } = useParams();
  const navigate = useNavigate();
  const [profiles, setProfiles] = useState({});
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // Track which wallet is being edited
  const [error, setError] = useState('');
  
  // Get all wallet addresses from localStorage
  const getAllWalletAddresses = () => {
    const storedWallets = JSON.parse(localStorage.getItem('gcn_wallets') || '[]');
    const currentWallet = localStorage.getItem('gcn_current_wallet');
    
    // Combine and deduplicate
    const allWallets = [...new Set([...storedWallets, currentWallet].filter(Boolean))];
    return allWallets;
  };
  
  const allWalletAddresses = getAllWalletAddresses();
  const currentUserAddress = localStorage.getItem('gcn_current_wallet') || allWalletAddresses[0];
  
  // If viewing a specific address, show only that one, otherwise show all
  const walletsToShow = address ? [address] : allWalletAddresses;
  const isViewingSpecificProfile = !!address;

  useEffect(() => {
    if (walletsToShow.length > 0) {
      loadAllProfiles();
    } else {
      setLoading(false);
      setError('No wallet addresses available. Please create or import a wallet first.');
    }
  }, [address]);

  const loadAllProfiles = async () => {
    setLoading(true);
    setError('');
    
    const profilesData = {};
    
    // Load profiles for all wallets
    await Promise.all(
      walletsToShow.map(async (walletAddress) => {
        try {
          const result = await profileService.getProfile(walletAddress);
          
          if (result.success) {
            profilesData[walletAddress] = result.profile;
          } else {
            profilesData[walletAddress] = null; // No profile exists
          }
        } catch (err) {
          console.error(`Error loading profile for ${walletAddress}:`, err);
          profilesData[walletAddress] = null;
        }
      })
    );
    
    setProfiles(profilesData);
    setLoading(false);
  };

  const handleEditProfile = (walletAddress) => {
    setEditing(walletAddress);
  };

  const handleSaveProfile = async (profileData) => {
    // Update the specific profile in state
    setProfiles(prev => ({
      ...prev,
      [editing]: {
        ...profileData,
        walletAddress: editing,
        lastUpdated: Math.floor(Date.now() / 1000)
      }
    }));
    setEditing(null);
    
    // Refresh the specific profile from blockchain
    try {
      const result = await profileService.getProfile(editing);
      if (result.success) {
        setProfiles(prev => ({
          ...prev,
          [editing]: result.profile
        }));
      }
    } catch (err) {
      console.error('Error refreshing profile:', err);
    }
  };

  const handleCancelEdit = () => {
    setEditing(null);
  };

  const handleCreateProfile = (walletAddress) => {
    setEditing(walletAddress);
  };

  if (loading) {
    return (
      <div className="profile-page">
        <div className="profile-container-full">
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading profiles...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="profile-page">
        <div className="profile-container-full">
          <div className="error-state">
            <h2>Error Loading Profiles</h2>
            <p>{error}</p>
            <Button onClick={loadAllProfiles}>Try Again</Button>
          </div>
        </div>
      </div>
    );
  }

  if (editing) {
    return (
      <div className="profile-page">
        <div className="profile-container-full">
          <div className="profile-editor-container">
            <ProfileEditor
              walletAddress={editing}
              existingProfile={profiles[editing]}
              onSave={handleSaveProfile}
              onCancel={handleCancelEdit}
              isEditing={!!profiles[editing]}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="profile-container-full">
        <div className="profile-header">
          <h1>
            {isViewingSpecificProfile ? 'User Profile' : 'My Wallet Profiles'}
          </h1>
          
          {isViewingSpecificProfile && (
            <Button 
              variant="outline" 
              onClick={() => navigate('/app/profile')}
            >
              View All My Profiles
            </Button>
          )}
        </div>

        <div className="profiles-grid">
          {walletsToShow.map((walletAddress) => {
            const profile = profiles[walletAddress];
            const isOwnWallet = allWalletAddresses.includes(walletAddress);
            const isCurrentWallet = walletAddress === currentUserAddress;

            return (
              <div key={walletAddress} className="profile-item">
                {profile ? (
                  <ProfileCard
                    profile={{ ...profile, walletAddress }}
                    isOwner={isOwnWallet}
                    onEdit={() => handleEditProfile(walletAddress)}
                    showEditButton={isOwnWallet}
                    isCurrent={isCurrentWallet}
                  />
                ) : (
                  <div className="no-profile-card">
                    <div className="no-profile-content">
                      <div className="no-profile-icon">👤</div>
                      <h3>No Profile</h3>
                      <div className="no-profile-address-row">
                        <div className="no-profile-address">
                          {walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}
                        </div>
                        {isCurrentWallet && <span className="current-badge">Current</span>}
                      </div>
                      <p>
                        {isOwnWallet 
                          ? "Create your blockchain identity with a unique alias and profile picture."
                          : "This user hasn't created a profile yet."
                        }
                      </p>
                      {isOwnWallet && (
                        <Button 
                          onClick={() => handleCreateProfile(walletAddress)}
                          size="small"
                        >
                          Create Profile
                        </Button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {walletsToShow.length === 0 && (
          <div className="no-wallets-state">
            <div className="no-profile-icon">💳</div>
            <h2>No Wallets Found</h2>
            <p>Please create or import a wallet to manage profiles.</p>
            <Button onClick={() => navigate('/app/wallet')}>
              Go to Wallet
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Profile;