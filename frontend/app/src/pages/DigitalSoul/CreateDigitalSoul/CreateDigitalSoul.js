import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowRightIcon,
  ArrowLeftIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import digitalSoulService from '../../../services/digitalSoulService';
import './CreateDigitalSoul.css';

const CreateDigitalSoul = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    username: '',
    description: '',
    personalityTraits: [],
    interactionPrice: 5,
    privacy: 'public'
  });
  
  const [estimatedCost, setEstimatedCost] = useState(100);
  const [uploading, setUploading] = useState(false);
  const [errors, setErrors] = useState({});

  const steps = [
    { number: 1, title: 'Basic Information', icon: InformationCircleIcon },
    { number: 2, title: 'Review & Deploy', icon: CheckIcon }
  ];

  const personalityOptions = [
    'Humorous', 'Analytical', 'Creative', 'Empathetic', 'Logical',
    'Optimistic', 'Philosophical', 'Practical', 'Adventurous', 'Calm',
    'Curious', 'Friendly', 'Professional', 'Artistic', 'Technical'
  ];

  const handleInputChange = (field, value) => {
    const newFormData = {
      ...formData,
      [field]: value
    };
    
    setFormData(newFormData);
    
    // Update estimated cost
    if (field === 'personalityTraits') {
      const cost = digitalSoulService.calculateCreationCost(newFormData);
      setEstimatedCost(cost);
    }
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: null
      }));
    }
  };

  const handleUsernameChange = async (value) => {
    // Clean the username: lowercase, remove special chars except underscore
    const cleanUsername = value.toLowerCase().replace(/[^a-z0-9_]/g, '');
    
    const newFormData = {
      ...formData,
      username: cleanUsername
    };
    
    setFormData(newFormData);
    
    // Clear previous error
    if (errors.username) {
      setErrors(prev => ({
        ...prev,
        username: null
      }));
    }
    
    // Validate username format
    if (cleanUsername && (cleanUsername.length < 3 || cleanUsername.length > 20)) {
      setErrors(prev => ({
        ...prev,
        username: 'Username must be 3-20 characters long'
      }));
      return;
    }
    
    // Check availability if username is valid length
    if (cleanUsername && cleanUsername.length >= 3 && cleanUsername.length <= 20) {
      try {
        const result = await digitalSoulService.checkUsernameAvailability(cleanUsername);
        if (result.success && !result.available) {
          setErrors(prev => ({
            ...prev,
            username: 'Username is already taken'
          }));
        }
      } catch (error) {
        console.error('Error checking username availability:', error);
      }
    }
  };


  const togglePersonalityTrait = (trait) => {
    setFormData(prev => ({
      ...prev,
      personalityTraits: prev.personalityTraits.includes(trait)
        ? prev.personalityTraits.filter(t => t !== trait)
        : [...prev.personalityTraits, trait]
    }));
  };

  const validateStep = (step) => {
    if (step === 2) {
      // Final validation using service
      const validation = digitalSoulService.validateSoulData(formData);
      setErrors(validation.errors);
      return validation.isValid;
    }

    const newErrors = {};

    switch (step) {
      case 1:
        if (!formData.name.trim()) newErrors.name = 'Name is required';
        if (!formData.description.trim()) newErrors.description = 'Description is required';
        if (formData.personalityTraits.length < 3) {
          newErrors.personalityTraits = 'Please select at least 3 personality traits';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 2));
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(2)) return;

    // Check if user has a wallet
    if (!digitalSoulService.hasWallet()) {
      setErrors({ submit: 'Please connect a wallet to create a Digital Soul.' });
      return;
    }

    setUploading(true);
    try {
      console.log('Creating Digital Soul on blockchain...');
      
      // Create Digital Soul on blockchain
      const result = await digitalSoulService.createDigitalSoul(formData);
      
      if (result.success) {
        console.log('Digital Soul created successfully:', result);
        
        // Navigate back to Digital Soul page with success message
        navigate('/app/digital-soul', { 
          state: { 
            successMessage: 'Digital Soul created successfully!',
            newSoul: {
              ...formData,
              soulId: result.soul_id,
              creatorWallet: result.creator_wallet,
              creationCost: result.creation_cost,
              trainingDataHash: result.training_data_hash,
              status: result.status
            }
          }
        });
      } else {
        setErrors({ submit: result.error || 'Failed to create Digital Soul.' });
      }
    } catch (error) {
      console.error('Error creating digital soul:', error);
      
      // Parse error message
      let errorMessage = 'Failed to create digital soul. Please try again.';
      if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setErrors({ submit: errorMessage });
    } finally {
      setUploading(false);
    }
  };

  const renderStepIndicator = () => (
    <div className="step-indicator">
      {steps.map((step) => (
        <div
          key={step.number}
          className={`step-item ${currentStep >= step.number ? 'active' : ''} ${currentStep > step.number ? 'completed' : ''}`}
        >
          <div className="step-circle">
            {currentStep > step.number ? (
              <CheckIcon className="step-check" />
            ) : (
              <step.icon className="step-icon" />
            )}
          </div>
          <span className="step-title">{step.title}</span>
        </div>
      ))}
    </div>
  );

  const renderStep1 = () => (
    <div className="form-step">
      <h3>Basic Information</h3>
      <p>Tell us about your digital soul</p>

      <div className="form-group">
        <label htmlFor="name">Soul Name *</label>
        <input
          id="name"
          type="text"
          value={formData.name}
          onChange={(e) => handleInputChange('name', e.target.value)}
          placeholder="Enter a name for your digital soul"
          className={errors.name ? 'error' : ''}
        />
        {errors.name && <span className="error-text">{errors.name}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="username">Username * <span className="username-prefix">@</span></label>
        <input
          id="username"
          type="text"
          value={formData.username}
          onChange={(e) => handleUsernameChange(e.target.value)}
          placeholder="Choose a unique username (3-20 characters)"
          className={errors.username ? 'error' : ''}
        />
        {errors.username && <span className="error-text">{errors.username}</span>}
        {formData.username && !errors.username && (
          <span className="username-preview">Soul will be available at: /app/soul/{formData.username}</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="description">Description *</label>
        <textarea
          id="description"
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          placeholder="Describe your digital soul's purpose and personality"
          rows={4}
          className={errors.description ? 'error' : ''}
        />
        {errors.description && <span className="error-text">{errors.description}</span>}
      </div>

      <div className="form-group">
        <label>Personality Traits * (Select at least 3)</label>
        <div className="personality-grid">
          {personalityOptions.map((trait) => (
            <button
              key={trait}
              type="button"
              onClick={() => togglePersonalityTrait(trait)}
              className={`personality-tag ${formData.personalityTraits.includes(trait) ? 'selected' : ''}`}
            >
              {trait}
            </button>
          ))}
        </div>
        {errors.personalityTraits && <span className="error-text">{errors.personalityTraits}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="interactionPrice">Interaction Price (GCN per minute)</label>
        <input
          id="interactionPrice"
          type="number"
          min="1"
          max="100"
          value={formData.interactionPrice}
          onChange={(e) => handleInputChange('interactionPrice', parseInt(e.target.value))}
        />
      </div>

      <div className="form-group">
        <label htmlFor="privacy">Privacy Setting</label>
        <select
          id="privacy"
          value={formData.privacy}
          onChange={(e) => handleInputChange('privacy', e.target.value)}
        >
          <option value="public">Public - Anyone can interact</option>
          <option value="friends">Friends Only - Invited users only</option>
          <option value="private">Private - You only</option>
        </select>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="form-step">
      <h3>Review & Deploy</h3>
      <p>Review your digital soul before deploying to the blockchain</p>

      <div className="review-summary">
        <div className="summary-item">
          <h4>Basic Information</h4>
          <p><strong>Name:</strong> {formData.name}</p>
          <p><strong>Description:</strong> {formData.description}</p>
          <p><strong>Personality Traits:</strong> {formData.personalityTraits.join(', ')}</p>
          <p><strong>Interaction Price:</strong> {formData.interactionPrice} GCN/min</p>
          <p><strong>Privacy:</strong> {formData.privacy}</p>
        </div>

        <div className="cost-breakdown">
          <h4>Creation Cost</h4>
          <div className="cost-item">
            <span>Basic Soul Creation</span>
            <span>50 GCN</span>
          </div>
          <div className="cost-item">
            <span>Blockchain Storage</span>
            <span>25 GCN</span>
          </div>
          <div className="cost-item">
            <span>3D Avatar Generation</span>
            <span>25 GCN</span>
          </div>
          <div className="cost-total">
            <span><strong>Total</strong></span>
            <span><strong>{estimatedCost} GCN</strong></span>
          </div>
        </div>
      </div>

      {errors.submit && (
        <div className="error-box">
          <ExclamationTriangleIcon className="error-icon" />
          <span>{errors.submit}</span>
        </div>
      )}
    </div>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1: return renderStep1();
      case 2: return renderStep2();
      default: return renderStep1();
    }
  };

  return (
    <div className="create-digital-soul-page">
      <div className="page-header">
        <div className="header-content">
          <button 
            onClick={() => navigate('/app/digital-soul')}
            className="back-button"
          >
            <ArrowLeftIcon className="back-icon" />
            Back to Digital Souls
          </button>
          <h1>Create Digital Soul</h1>
          <p>Transform your personality into an autonomous AI entity</p>
        </div>
      </div>

      {renderStepIndicator()}

      <div className="form-container">
        {renderCurrentStep()}
      </div>

      <div className="form-actions">
        {currentStep > 1 && (
          <button
            type="button"
            onClick={prevStep}
            className="btn-secondary"
            disabled={uploading}
          >
            <ArrowLeftIcon className="btn-icon" />
            Previous
          </button>
        )}

        <div className="spacer"></div>

        {currentStep < 2 ? (
          <button
            type="button"
            onClick={nextStep}
            className="btn-primary"
            disabled={uploading}
          >
            Next
            <ArrowRightIcon className="btn-icon" />
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            className="btn-primary"
            disabled={uploading}
          >
            {uploading ? 'Creating Soul...' : 'Deploy to Blockchain'}
            {!uploading && <ArrowRightIcon className="btn-icon" />}
          </button>
        )}
      </div>
    </div>
  );
};

export default CreateDigitalSoul;