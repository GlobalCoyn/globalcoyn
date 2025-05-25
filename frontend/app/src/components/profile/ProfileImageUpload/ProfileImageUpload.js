import React, { useState, useRef } from 'react';
import ipfsService from '../../../services/api/ipfsService';
import './ProfileImageUpload.css';

const ProfileImageUpload = ({ 
  currentImage = null, 
  onImageUpload = () => {}, 
  onImageRemove = () => {},
  disabled = false 
}) => {
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [preview, setPreview] = useState(currentImage);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleImageSelect = async (file) => {
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please select a valid image file');
      return;
    }

    // Validate file size (5MB limit)
    if (file.size > 5 * 1024 * 1024) {
      setError('Image must be less than 5MB');
      return;
    }

    setError('');
    setUploading(true);

    try {
      // Create preview
      const previewUrl = URL.createObjectURL(file);
      setPreview(previewUrl);

      // Upload to IPFS
      const result = await ipfsService.uploadImage(file);
      
      if (result.success) {
        onImageUpload(result.hash, result.url);
      } else {
        throw new Error(result.error || 'Upload failed');
      }
    } catch (err) {
      console.error('Image upload error:', err);
      setError(err.message || 'Failed to upload image');
      setPreview(currentImage);
    } finally {
      setUploading(false);
    }
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleImageSelect(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    
    const file = e.dataTransfer.files[0];
    if (file) {
      handleImageSelect(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragActive(false);
  };

  const handleRemoveImage = () => {
    setPreview(null);
    onImageRemove();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const triggerFileInput = () => {
    if (!disabled && !uploading) {
      fileInputRef.current?.click();
    }
  };

  const getImageUrl = (hash) => {
    if (!hash) return null;
    if (hash.startsWith('blob:')) return hash; // Preview URL
    return `https://gateway.pinata.cloud/ipfs/${hash}`;
  };

  return (
    <div className="profile-image-upload">
      <div 
        className={`upload-area ${dragActive ? 'drag-active' : ''} ${disabled ? 'disabled' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={triggerFileInput}
      >
        {preview ? (
          <div className="image-preview-container">
            <img 
              src={getImageUrl(preview)} 
              alt="Profile preview" 
              className="image-preview"
            />
            <div className="image-overlay">
              {uploading ? (
                <div className="upload-spinner">
                  <div className="spinner"></div>
                  <span>Uploading...</span>
                </div>
              ) : (
                <div className="image-actions">
                  <button 
                    type="button"
                    className="change-image-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      triggerFileInput();
                    }}
                    disabled={disabled}
                  >
                    Change
                  </button>
                  <button 
                    type="button"
                    className="remove-image-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveImage();
                    }}
                    disabled={disabled}
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="upload-placeholder">
            {uploading ? (
              <div className="upload-spinner">
                <div className="spinner"></div>
                <span>Uploading...</span>
              </div>
            ) : (
              <>
                <div className="upload-icon">📷</div>
                <div className="upload-text">
                  <p>Click to upload or drag and drop</p>
                  <p className="upload-subtext">PNG, JPG, GIF up to 5MB</p>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileInput}
        className="file-input"
        disabled={disabled || uploading}
      />

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="upload-info">
        <p>Your image will be stored on IPFS (decentralized storage)</p>
      </div>
    </div>
  );
};

export default ProfileImageUpload;