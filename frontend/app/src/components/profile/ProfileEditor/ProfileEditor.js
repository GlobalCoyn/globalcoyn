import React, { useState, useEffect } from 'react';
import ProfileImageUpload from '../ProfileImageUpload/ProfileImageUpload';
import Button from '../../common/Button/Button';
import profileService from '../../../services/api/profileService';
import './ProfileEditor.css';

const ProfileEditor = ({ 
  walletAddress,
  existingProfile = null,
  onSave = () => {},
  onCancel = () => {},
  isEditing = false 
}) => {
  const [formData, setFormData] = useState({
    alias: '',
    bio: '',
    ipfsHash: ''
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [checkingAlias, setCheckingAlias] = useState(false);
  const [aliasAvailable, setAliasAvailable] = useState(null);

  useEffect(() => {
    if (existingProfile) {
      setFormData({
        alias: existingProfile.alias || '',
        bio: existingProfile.bio || '',
        ipfsHash: existingProfile.ipfsHash || ''
      });
    }
  }, [existingProfile]);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.alias.trim()) {
      newErrors.alias = 'Alias is required';
    } else if (formData.alias.length < 3) {
      newErrors.alias = 'Alias must be at least 3 characters';
    } else if (formData.alias.length > 20) {
      newErrors.alias = 'Alias must be less than 20 characters';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.alias)) {
      newErrors.alias = 'Alias can only contain letters, numbers, underscores, and hyphens';
    }

    if (formData.bio && formData.bio.length > 500) {
      newErrors.bio = 'Bio must be less than 500 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const checkAliasAvailability = async (alias) => {
    if (!alias || alias === existingProfile?.alias) {
      setAliasAvailable(null);
      return;
    }

    // Don't check availability for invalid aliases (less than 3 chars)
    if (alias.length < 3) {
      setAliasAvailable(null);
      return;
    }

    setCheckingAlias(true);
    try {
      const available = await profileService.isAliasAvailable(alias);
      setAliasAvailable(available);
    } catch (error) {
      console.error('Error checking alias availability:', error);
      setAliasAvailable(null);
    } finally {
      setCheckingAlias(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear field-specific error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }

    // Check alias availability with debounce
    if (field === 'alias') {
      const timeoutId = setTimeout(() => {
        checkAliasAvailability(value);
      }, 800); // Increased debounce time to reduce API calls
      
      return () => clearTimeout(timeoutId);
    }
  };

  const handleImageUpload = (hash, url) => {
    setFormData(prev => ({
      ...prev,
      ipfsHash: hash
    }));
  };

  const handleImageRemove = () => {
    setFormData(prev => ({
      ...prev,
      ipfsHash: ''
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    if (aliasAvailable === false) {
      setErrors(prev => ({
        ...prev,
        alias: 'This alias is already taken'
      }));
      return;
    }

    setSaving(true);
    
    try {
      const result = await profileService.setProfile(
        walletAddress,
        formData.alias,
        formData.bio,
        formData.ipfsHash
      );

      if (result.success) {
        onSave(formData);
      } else {
        throw new Error(result.error || 'Failed to save profile');
      }
    } catch (error) {
      console.error('Error saving profile:', error);
      setErrors(prev => ({
        ...prev,
        submit: error.message || 'Failed to save profile'
      }));
    } finally {
      setSaving(false);
    }
  };

  const getAliasStatus = () => {
    if (!formData.alias || formData.alias === existingProfile?.alias) return null;
    if (checkingAlias) return 'checking';
    if (aliasAvailable === true) return 'available';
    if (aliasAvailable === false) return 'unavailable';
    return null;
  };

  const aliasStatus = getAliasStatus();

  return (
    <div className="profile-editor">
      <div className="profile-editor-header">
        <h2>{isEditing ? 'Edit Profile' : 'Create Profile'}</h2>
        <p>Set up your blockchain identity with an alias and profile picture</p>
      </div>

      <form onSubmit={handleSubmit} className="profile-form">
        <div className="form-section">
          <h3>Profile Picture</h3>
          <ProfileImageUpload
            currentImage={formData.ipfsHash}
            onImageUpload={handleImageUpload}
            onImageRemove={handleImageRemove}
            disabled={saving}
          />
        </div>

        <div className="form-section">
          <h3>Basic Information</h3>
          
          <div className="form-field">
            <label htmlFor="alias">
              Alias <span className="required">*</span>
            </label>
            <div className="alias-input-container">
              <input
                id="alias"
                type="text"
                value={formData.alias}
                onChange={(e) => handleInputChange('alias', e.target.value)}
                placeholder="Choose a unique alias"
                className={`form-input ${errors.alias ? 'error' : ''} ${aliasStatus === 'available' ? 'success' : ''}`}
                disabled={saving}
              />
              {aliasStatus && (
                <div className={`alias-status ${aliasStatus}`}>
                  {aliasStatus === 'checking' && '⏳'}
                  {aliasStatus === 'available' && '✓'}
                  {aliasStatus === 'unavailable' && '✗'}
                </div>
              )}
            </div>
            {errors.alias && <span className="error-text">{errors.alias}</span>}
            {aliasStatus === 'available' && (
              <span className="success-text">Alias is available!</span>
            )}
            {aliasStatus === 'unavailable' && (
              <span className="error-text">This alias is already taken</span>
            )}
          </div>

          <div className="form-field">
            <label htmlFor="bio">Bio</label>
            <textarea
              id="bio"
              value={formData.bio}
              onChange={(e) => handleInputChange('bio', e.target.value)}
              placeholder="Tell others about yourself (optional)"
              className={`form-textarea ${errors.bio ? 'error' : ''}`}
              rows={4}
              maxLength={500}
              disabled={saving}
            />
            <div className="character-count">
              {formData.bio.length}/500 characters
            </div>
            {errors.bio && <span className="error-text">{errors.bio}</span>}
          </div>
        </div>

        {errors.submit && (
          <div className="error-message">
            {errors.submit}
          </div>
        )}

        <div className="form-actions">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={saving}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            loading={saving}
            disabled={saving || aliasAvailable === false}
          >
            {saving ? 'Saving...' : (isEditing ? 'Update Profile' : 'Create Profile')}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default ProfileEditor;