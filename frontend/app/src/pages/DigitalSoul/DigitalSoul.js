import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  SparklesIcon, 
  PlusIcon, 
  EyeIcon,
  CpuChipIcon,
  UserGroupIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import digitalSoulService from '../../services/digitalSoulService';
import './DigitalSoul.css';

const DigitalSoul = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState('overview');
  const [mySouls, setMySouls] = useState([]);
  const [allSouls, setAllSouls] = useState([]);
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    loadDigitalSouls();
    
    // Check for success message from creation page
    if (location.state?.successMessage) {
      setSuccessMessage(location.state.successMessage);
      setActiveTab('my-souls');
      
      // Clear the message after 5 seconds
      setTimeout(() => {
        setSuccessMessage(null);
      }, 5000);
    }
  }, [location.state]);

  const loadDigitalSouls = async () => {
    setLoading(true);
    try {
      // Load user's souls and all public souls in parallel
      const [mySoulsResult, allSoulsResult] = await Promise.all([
        digitalSoulService.getMySouls(),
        digitalSoulService.getAllSouls()
      ]);

      if (mySoulsResult.success) {
        setMySouls(mySoulsResult.souls || []);
      }

      if (allSoulsResult.success) {
        setAllSouls(allSoulsResult.souls || []);
      }

      console.log('Digital souls loaded:', {
        mySouls: mySoulsResult.souls?.length || 0,
        allSouls: allSoulsResult.souls?.length || 0
      });
    } catch (error) {
      console.error('Error loading digital souls:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSoul = () => {
    navigate('/app/create-digital-soul');
  };

  const handleViewSoul = async (username) => {
    // Try to auto-generate world first, then navigate to worldviewer
    try {
      setLoading(true);
      
      // Get soul data first using digitalSoulService
      const soulData = await digitalSoulService.getSoulByUsername(username);
      
      if (soulData.success) {
        // Try to generate world if it doesn't exist
        try {
          const response = await fetch(`${digitalSoulService.getApiUrl()}/api/digital-soul/souls/${soulData.soul.soul_id}/create-world`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ world_type: 'room' })
          });
          const result = await response.json();
          console.log('World generation result:', result);
        } catch (worldError) {
          console.log('World generation failed or already exists:', worldError);
          // Continue to worldviewer even if world generation fails
        }
      }
      
      // Navigate to worldviewer
      navigate(`/app/soul/${username}/world`);
    } catch (error) {
      console.error('Error viewing soul:', error);
      // Navigate anyway in case of errors
      navigate(`/app/soul/${username}/world`);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: SparklesIcon },
    { id: 'my-souls', name: 'My Souls', icon: UserGroupIcon },
    { id: 'explore', name: 'Explore Souls', icon: EyeIcon },
  ];

  const renderOverview = () => (
    <div className="digital-soul-overview">
      <div className="overview-header">
        <div className="header-content">
          <SparklesIcon className="header-icon" />
          <div>
            <h1>Digital Soul Platform</h1>
            <p>Create, interact with, and manage autonomous AI entities on the blockchain</p>
          </div>
        </div>
      </div>

      <div className="overview-grid">
        <div className="overview-card">
          <div className="card-icon">
            <PlusIcon />
          </div>
          <h3>Create Your Digital Soul</h3>
          <p>Upload your personal data, thoughts, and voice to create an AI-powered digital version of yourself</p>
          <button 
            onClick={handleCreateSoul}
            className="btn-primary"
          >
            Get Started
          </button>
        </div>

        <div className="overview-card">
          <div className="card-icon">
            <EyeIcon />
          </div>
          <h3>Explore Soul Worlds</h3>
          <p>Visit 3D worlds inhabited by digital souls. Watch them live their autonomous digital lives</p>
          <button 
            onClick={() => setActiveTab('explore')}
            className="btn-secondary"
          >
            Explore
          </button>
        </div>

        <div className="overview-card">
          <div className="card-icon">
            <CpuChipIcon />
          </div>
          <h3>Autonomous Agents</h3>
          <p>Digital souls can act independently, make decisions, and interact with other souls autonomously</p>
          <button className="btn-secondary" disabled>
            Coming Soon
          </button>
        </div>
      </div>

      <div className="features-section">
        <h2>Key Features</h2>
        <div className="features-grid">
          <div className="feature-item">
            <h4>🧠 AI Personality</h4>
            <p>Advanced AI learns from your data to replicate your personality and thought patterns</p>
          </div>
          <div className="feature-item">
            <h4>🎨 3D Avatars</h4>
            <p>Photorealistic 3D avatars generated from your photos with real-time animations</p>
          </div>
          <div className="feature-item">
            <h4>🔊 Voice Cloning</h4>
            <p>Your digital soul speaks with your voice using advanced voice synthesis technology</p>
          </div>
          <div className="feature-item">
            <h4>⛓️ Blockchain Ownership</h4>
            <p>Your digital soul is permanently stored on the blockchain with cryptographic ownership</p>
          </div>
          <div className="feature-item">
            <h4>💰 Economic Agency</h4>
            <p>Digital souls can earn and spend GCN, making autonomous economic decisions</p>
          </div>
          <div className="feature-item">
            <h4>🤝 Social Interaction</h4>
            <p>Souls can interact with each other, form relationships, and collaborate on projects</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderMySouls = () => (
    <div className="my-souls-section">
      <div className="section-header">
        <h2>My Digital Souls</h2>
        <button 
          onClick={handleCreateSoul}
          className="btn-primary"
        >
          <PlusIcon className="btn-icon" />
          Create New Soul
        </button>
      </div>

      {mySouls.length === 0 ? (
        <div className="empty-state">
          <SparklesIcon className="empty-icon" />
          <h3>No Digital Souls Yet</h3>
          <p>Create your first digital soul to get started with AI-powered personality preservation</p>
          <button 
            onClick={handleCreateSoul}
            className="btn-primary"
          >
            Create Your First Soul
          </button>
        </div>
      ) : (
        <div className="souls-grid">
          {mySouls.map((soul) => (
            <div 
              key={soul.soul_id} 
              className="soul-card clickable"
              onClick={() => handleViewSoul(soul.username)}
            >
              <div className="soul-avatar">
                {soul.avatar_model_hash ? (
                  <img 
                    src={`https://gateway.pinata.cloud/ipfs/${soul.avatar_model_hash}`} 
                    alt={soul.name}
                    onError={(e) => {
                      e.target.src = '/assets/logo.png'; // Fallback image
                    }}
                  />
                ) : (
                  <div className="avatar-placeholder">
                    <SparklesIcon />
                  </div>
                )}
              </div>
              <div className="soul-info">
                <h3 className="soul-name">{soul.name}</h3>
                <p className="soul-username">@{soul.username}</p>
                <p className="soul-viewers">{Math.floor(Math.random() * 1000) + 50} viewers</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderExploreSouls = () => (
    <div className="explore-souls-section">
      <div className="section-header">
        <h2>Explore Digital Souls</h2>
        <div className="filters">
          <select className="filter-select">
            <option value="all">All Categories</option>
            <option value="popular">Most Popular</option>
            <option value="recent">Recently Created</option>
            <option value="affordable">Most Affordable</option>
          </select>
        </div>
      </div>

      {allSouls.length === 0 ? (
        <div className="empty-state">
          <UserGroupIcon className="empty-icon" />
          <h3>No Public Souls Available</h3>
          <p>Be the first to create a digital soul and make it available for others to interact with</p>
        </div>
      ) : (
        <div className="souls-grid">
          {allSouls.map((soul) => (
            <div 
              key={soul.soul_id} 
              className="soul-card clickable"
              onClick={() => handleViewSoul(soul.username)}
            >
              <div className="soul-avatar">
                {soul.avatar_model_hash ? (
                  <img 
                    src={`https://gateway.pinata.cloud/ipfs/${soul.avatar_model_hash}`} 
                    alt={soul.name}
                    onError={(e) => {
                      e.target.src = '/assets/logo.png'; // Fallback image
                    }}
                  />
                ) : (
                  <div className="avatar-placeholder">
                    <SparklesIcon />
                  </div>
                )}
              </div>
              <div className="soul-info">
                <h3 className="soul-name">{soul.name}</h3>
                <p className="soul-username">@{soul.username}</p>
                <p className="soul-viewers">{Math.floor(Math.random() * 1000) + 50} viewers</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );


  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverview();
      case 'my-souls':
        return renderMySouls();
      case 'explore':
        return renderExploreSouls();
      default:
        return renderOverview();
    }
  };

  return (
    <div className="digital-soul-page">
      <div className="page-header">
        <div className="tab-navigation">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              >
                <Icon className="tab-icon" />
                <span>{tab.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="page-content">
        {successMessage && (
          <div className="success-message">
            <CheckCircleIcon className="success-icon" />
            <span>{successMessage}</span>
          </div>
        )}
        
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading digital souls...</p>
          </div>
        ) : (
          renderTabContent()
        )}
      </div>
    </div>
  );
};

export default DigitalSoul;