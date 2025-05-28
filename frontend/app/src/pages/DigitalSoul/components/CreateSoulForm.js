import React, { useState } from 'react';
import { 
  DocumentTextIcon, 
  MicrophoneIcon, 
  PhotoIcon,
  ArrowRightIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import digitalSoulService from '../../../services/digitalSoulService';
import './CreateSoulForm.css';

const CreateSoulForm = ({ onClose, onSubmit }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    textSamples: [],
    audioFiles: [],
    photos: [],
    personalityTraits: [],
    interactionPrice: 5,
    privacy: 'public'
  });
  
  const [estimatedCost, setEstimatedCost] = useState(600);

  const [uploading, setUploading] = useState(false);
  const [errors, setErrors] = useState({});

  const steps = [
    { number: 1, title: 'Basic Information', icon: InformationCircleIcon },
    { number: 2, title: 'Text Samples', icon: DocumentTextIcon },
    { number: 3, title: 'Voice Recordings', icon: MicrophoneIcon },
    { number: 4, title: 'Photos', icon: PhotoIcon },
    { number: 5, title: 'Review & Deploy', icon: CheckIcon }
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

  const handleFileUpload = (field, files) => {
    console.log(`Uploading files for ${field}:`, files);
    const fileArray = Array.from(files);
    console.log(`File array:`, fileArray);
    
    setFormData(prev => ({
      ...prev,
      [field]: [...prev[field], ...fileArray]
    }));
    
    // Clear any existing errors for this field
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: null
      }));
    }
  };

  const removeFile = (field, index) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }));
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
    if (step === 5) {
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
      case 2:
        if (formData.textSamples.length === 0) {
          newErrors.textSamples = 'Please upload at least one text sample';
        }
        break;
      case 3:
        if (formData.audioFiles.length === 0) {
          newErrors.audioFiles = 'Please upload at least one voice recording';
        }
        break;
      case 4:
        if (formData.photos.length === 0) {
          newErrors.photos = 'Please upload at least one photo';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 5));
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(5)) return;

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
        onSubmit({
          ...formData,
          soulId: result.soul_id,
          creatorWallet: result.creator_wallet,
          creationCost: result.creation_cost,
          trainingDataHash: result.training_data_hash,
          status: result.status
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
      <h3>Text Samples</h3>
      <p>Upload text files that represent your writing style and thoughts</p>

      <div className="upload-area">
        <DocumentTextIcon className="upload-icon" />
        <h4>Upload Text Files</h4>
        <p>Supported formats: .txt, .doc, .docx, .pdf</p>
        <input
          type="file"
          multiple
          accept=".txt,.doc,.docx,.pdf"
          onChange={(e) => handleFileUpload('textSamples', e.target.files)}
          className="file-input"
          id="text-files-input"
        />
        <label 
          htmlFor="text-files-input" 
          className="upload-btn"
          onClick={() => console.log('Text files button clicked')}
        >
          Choose Files
        </label>
      </div>

      {formData.textSamples.length > 0 && (
        <div className="file-list">
          <h4>Uploaded Files</h4>
          {formData.textSamples.map((file, index) => (
            <div key={index} className="file-item">
              <DocumentTextIcon className="file-icon" />
              <span>{file.name}</span>
              <button
                type="button"
                onClick={() => removeFile('textSamples', index)}
                className="remove-btn"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {errors.textSamples && <span className="error-text">{errors.textSamples}</span>}

      <div className="info-box">
        <InformationCircleIcon className="info-icon" />
        <p>Upload personal writings like journals, emails, essays, or social media posts. More text provides better personality training.</p>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="form-step">
      <h3>Voice Recordings</h3>
      <p>Upload audio files to clone your voice and speech patterns</p>

      <div className="upload-area">
        <MicrophoneIcon className="upload-icon" />
        <h4>Upload Audio Files</h4>
        <p>Supported formats: .mp3, .wav, .m4a (minimum 5 minutes total)</p>
        <input
          type="file"
          multiple
          accept=".mp3,.wav,.m4a"
          onChange={(e) => handleFileUpload('audioFiles', e.target.files)}
          className="file-input"
          id="audio-files-input"
        />
        <label 
          htmlFor="audio-files-input" 
          className="upload-btn"
          onClick={() => console.log('Audio files button clicked')}
        >
          Choose Files
        </label>
      </div>

      {formData.audioFiles.length > 0 && (
        <div className="file-list">
          <h4>Uploaded Files</h4>
          {formData.audioFiles.map((file, index) => (
            <div key={index} className="file-item">
              <MicrophoneIcon className="file-icon" />
              <span>{file.name}</span>
              <button
                type="button"
                onClick={() => removeFile('audioFiles', index)}
                className="remove-btn"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {errors.audioFiles && <span className="error-text">{errors.audioFiles}</span>}

      <div className="info-box">
        <InformationCircleIcon className="info-icon" />
        <p>Record yourself speaking naturally. Include conversations, presentations, or voice messages for best results.</p>
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="form-step">
      <h3>Photos</h3>
      <p>Upload photos for 3D avatar generation</p>

      <div className="upload-area">
        <PhotoIcon className="upload-icon" />
        <h4>Upload Photos</h4>
        <p>Supported formats: .jpg, .png (minimum 3 clear face photos)</p>
        <input
          type="file"
          multiple
          accept=".jpg,.jpeg,.png"
          onChange={(e) => handleFileUpload('photos', e.target.files)}
          className="file-input"
          id="photo-files-input"
        />
        <label 
          htmlFor="photo-files-input" 
          className="upload-btn"
          onClick={() => console.log('Photo files button clicked')}
        >
          Choose Files
        </label>
      </div>

      {formData.photos.length > 0 && (
        <div className="photo-grid">
          {formData.photos.map((file, index) => (
            <div key={index} className="photo-item">
              <img
                src={URL.createObjectURL(file)}
                alt={`Upload ${index + 1}`}
                className="photo-preview"
              />
              <button
                type="button"
                onClick={() => removeFile('photos', index)}
                className="remove-btn"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {errors.photos && <span className="error-text">{errors.photos}</span>}

      <div className="info-box">
        <InformationCircleIcon className="info-icon" />
        <p>Use clear, well-lit photos showing your face from different angles. Avoid sunglasses or heavy makeup.</p>
      </div>
    </div>
  );

  const renderStep5 = () => (
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

        <div className="summary-item">
          <h4>Uploaded Content</h4>
          <p><strong>Text Samples:</strong> {formData.textSamples.length} files</p>
          <p><strong>Voice Recordings:</strong> {formData.audioFiles.length} files</p>
          <p><strong>Photos:</strong> {formData.photos.length} files</p>
        </div>

        <div className="cost-breakdown">
          <h4>Creation Cost</h4>
          <div className="cost-item">
            <span>AI Training</span>
            <span>300 GCN</span>
          </div>
          <div className="cost-item">
            <span>Voice Cloning</span>
            <span>150 GCN</span>
          </div>
          <div className="cost-item">
            <span>3D Avatar</span>
            <span>100 GCN</span>
          </div>
          <div className="cost-item">
            <span>Blockchain Storage</span>
            <span>50 GCN</span>
          </div>
          {formData.personalityTraits.filter(trait => 
            ['Creative', 'Analytical', 'Technical'].includes(trait)
          ).length > 0 && (
            <div className="cost-item">
              <span>Premium Traits ({formData.personalityTraits.filter(trait => 
                ['Creative', 'Analytical', 'Technical'].includes(trait)
              ).length})</span>
              <span>{formData.personalityTraits.filter(trait => 
                ['Creative', 'Analytical', 'Technical'].includes(trait)
              ).length * 25} GCN</span>
            </div>
          )}
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
      case 3: return renderStep3();
      case 4: return renderStep4();
      case 5: return renderStep5();
      default: return renderStep1();
    }
  };

  return (
    <div className="create-soul-form">
      <div className="form-header">
        <h2>Create Digital Soul</h2>
        <button onClick={onClose} className="close-btn">×</button>
      </div>

      {renderStepIndicator()}

      <div className="form-content">
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
            Previous
          </button>
        )}

        <div className="spacer"></div>

        {currentStep < 5 ? (
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

export default CreateSoulForm;