/**
 * Digital Soul Service
 * Handles API communication for Digital Soul functionality
 */

import axios from 'axios';

// Environment detection
const ENV_OVERRIDE = localStorage.getItem('gcn_environment');

const isProduction = ENV_OVERRIDE === 'production' || 
                   process.env.REACT_APP_ENV === 'production' || 
                   window.location.hostname === 'globalcoyn.com';

// API Configuration
const API_URLS = {
  primary: isProduction ? 'https://globalcoyn.com' : 'http://localhost:8001',
  secondary: isProduction ? 'https://globalcoyn.com' : 'http://localhost:8002'
};

let currentApiUrl = API_URLS.primary;

// Retry mechanism for API calls
const retryRequest = async (requestFn, maxRetries = 2) => {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await requestFn();
      return response;
    } catch (error) {
      console.warn(`API request failed (attempt ${attempt + 1}):`, error.message);
      
      if (attempt < maxRetries) {
        // Switch to secondary API on retry
        currentApiUrl = currentApiUrl === API_URLS.primary ? API_URLS.secondary : API_URLS.primary;
        console.log(`Retrying with ${currentApiUrl}`);
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before retry
      } else {
        throw error;
      }
    }
  }
};

class DigitalSoulService {
  constructor() {
    this.baseURL = currentApiUrl;
    this.cache = new Map();
    this.cacheTimeout = 30000; // 30 seconds
  }

  /**
   * Get current API URL
   */
  getApiUrl() {
    return currentApiUrl;
  }

  /**
   * Create a new Digital Soul on the blockchain
   * @param {Object} soulData - Soul creation data
   * @returns {Promise<Object>} Creation result
   */
  async createDigitalSoul(soulData) {
    const requestFn = async () => {
      const payload = {
        creator_wallet: this.getCurrentWallet(),
        name: soulData.name,
        username: soulData.username,
        description: soulData.description,
        personality_traits: soulData.personalityTraits,
        interaction_price: soulData.interactionPrice || 5,
        privacy_setting: soulData.privacy || 'public'
      };

      const response = await axios.post(
        `${currentApiUrl}/api/digital-soul/create`,
        payload,
        {
          headers: {
            'Content-Type': 'application/json'
          },
          timeout: 60000 // 60 second timeout for large uploads
        }
      );

      return response.data;
    };

    return await retryRequest(requestFn);
  }

  /**
   * Get all public Digital Souls
   * @returns {Promise<Array>} List of public souls
   */
  async getAllSouls() {
    const cacheKey = 'all_souls';
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    const requestFn = async () => {
      const response = await axios.get(`${currentApiUrl}/api/digital-soul/souls`);
      return response.data;
    };

    const result = await retryRequest(requestFn);
    this.setCache(cacheKey, result);
    return result;
  }

  /**
   * Get Digital Souls created by a specific wallet
   * @param {string} walletAddress - Creator's wallet address
   * @returns {Promise<Array>} List of souls
   */
  async getSoulsByCreator(walletAddress) {
    const cacheKey = `souls_by_creator_${walletAddress}`;
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    const requestFn = async () => {
      const response = await axios.get(
        `${currentApiUrl}/api/digital-soul/souls/creator/${walletAddress}`
      );
      return response.data;
    };

    const result = await retryRequest(requestFn);
    this.setCache(cacheKey, result);
    return result;
  }

  /**
   * Get my Digital Souls (souls created by current wallet)
   * @returns {Promise<Array>} List of my souls
   */
  async getMySouls() {
    const currentWallet = this.getCurrentWallet();
    if (!currentWallet) {
      return { success: true, souls: [], count: 0 };
    }

    return await this.getSoulsByCreator(currentWallet);
  }

  /**
   * Get detailed information about a specific Digital Soul
   * @param {string} soulId - Soul identifier
   * @returns {Promise<Object>} Soul details
   */
  async getSoulDetails(soulId) {
    const cacheKey = `soul_${soulId}`;
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    const requestFn = async () => {
      const response = await axios.get(`${currentApiUrl}/api/digital-soul/souls/${soulId}`);
      return response.data;
    };

    const result = await retryRequest(requestFn);
    this.setCache(cacheKey, result, 10000); // Cache for 10 seconds only
    return result;
  }

  /**
   * Get a Digital Soul (alias for getSoulDetails for compatibility)
   * @param {string} soulId - Soul identifier
   * @returns {Promise<Object>} Soul details
   */
  async getSoul(soulId) {
    return await this.getSoulDetails(soulId);
  }

  /**
   * Chat with a Digital Soul's AI
   * @param {string} soulId - Soul to chat with
   * @param {Object} chatData - Chat message data
   * @returns {Promise<Object>} Chat response
   */
  async chatWithSoul(soulId, chatData) {
    const requestFn = async () => {
      const response = await axios.post(
        `${currentApiUrl}/api/digital-soul/souls/${soulId}/chat`,
        chatData
      );
      return response.data;
    };

    return await retryRequest(requestFn);
  }

  /**
   * Get AI statistics for a Digital Soul
   * @param {string} soulId - Soul identifier
   * @returns {Promise<Object>} AI stats
   */
  async getSoulAIStats(soulId) {
    const requestFn = async () => {
      const response = await axios.get(
        `${currentApiUrl}/api/digital-soul/souls/${soulId}/ai-stats`
      );
      return response.data;
    };

    return await retryRequest(requestFn);
  }

  /**
   * Get a Digital Soul by username
   * @param {string} username - Soul username
   * @returns {Promise<Object>} Soul details
   */
  async getSoulByUsername(username) {
    const requestFn = async () => {
      const response = await axios.get(
        `${currentApiUrl}/api/digital-soul/soul/${username}`
      );
      return response.data;
    };

    return await retryRequest(requestFn);
  }

  /**
   * Check if a username is available
   * @param {string} username - Username to check
   * @returns {Promise<Object>} Availability result
   */
  async checkUsernameAvailability(username) {
    const requestFn = async () => {
      const response = await axios.get(
        `${currentApiUrl}/api/digital-soul/check-username/${username}`
      );
      return response.data;
    };

    return await retryRequest(requestFn);
  }

  /**
   * Interact with a Digital Soul
   * @param {string} soulId - Soul to interact with
   * @param {Object} interactionData - Interaction details
   * @returns {Promise<Object>} Interaction result
   */
  async interactWithSoul(soulId, interactionData) {
    const requestFn = async () => {
      const payload = {
        user_wallet: this.getCurrentWallet(),
        conversation_data: interactionData.conversationData,
        duration_minutes: interactionData.durationMinutes,
        interaction_type: interactionData.type || 'chat',
        payment_amount: interactionData.paymentAmount
      };

      const response = await axios.post(
        `${currentApiUrl}/api/digital-soul/souls/${soulId}/interact`,
        payload
      );

      return response.data;
    };

    return await retryRequest(requestFn);
  }

  /**
   * Update Digital Soul AI models after training
   * @param {string} soulId - Soul to update
   * @param {Object} modelHashes - IPFS hashes of trained models
   * @returns {Promise<Object>} Update result
   */
  async updateSoulModels(soulId, modelHashes) {
    const requestFn = async () => {
      const response = await axios.post(
        `${currentApiUrl}/api/digital-soul/souls/${soulId}/update-models`,
        modelHashes
      );
      return response.data;
    };

    return await retryRequest(requestFn);
  }

  /**
   * Get interaction history for a Digital Soul
   * @param {string} soulId - Soul identifier
   * @returns {Promise<Array>} Interaction history
   */
  async getSoulInteractions(soulId) {
    const requestFn = async () => {
      const response = await axios.get(
        `${currentApiUrl}/api/digital-soul/souls/${soulId}/interactions`
      );
      return response.data;
    };

    return await retryRequest(requestFn);
  }

  /**
   * Get Digital Soul platform statistics
   * @returns {Promise<Object>} Platform stats
   */
  async getDigitalSoulStats() {
    const cacheKey = 'digital_soul_stats';
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    const requestFn = async () => {
      const response = await axios.get(`${currentApiUrl}/api/digital-soul/stats`);
      return response.data;
    };

    const result = await retryRequest(requestFn);
    this.setCache(cacheKey, result, 5000); // Cache for 5 seconds
    return result;
  }

  /**
   * Upload a file directly to IPFS
   * @param {File} file - File to upload
   * @returns {Promise<Object>} Upload result with IPFS hash
   */
  async uploadFileToIPFS(file) {
    const requestFn = async () => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(
        `${currentApiUrl}/api/digital-soul/ipfs/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 30000 // 30 second timeout
        }
      );

      return response.data;
    };

    return await retryRequest(requestFn);
  }

  /**
   * Upload multiple files to IPFS
   * @param {Array<File>} files - Files to upload
   * @returns {Promise<Array>} Array of upload results
   */
  async uploadFilesToIPFS(files) {
    const uploadPromises = files.map(file => this.uploadFileToIPFS(file));
    return await Promise.all(uploadPromises);
  }

  /**
   * Convert files to base64 for API transmission
   * @param {Array<File>} files - Files to convert
   * @returns {Promise<String>} Base64 encoded data
   */
  async filesToBase64(files) {
    if (!files || files.length === 0) return '';

    const filePromises = files.map(file => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = reader.result.split(',')[1]; // Remove data:type;base64, prefix
          resolve({
            filename: file.name,
            size: file.size,
            type: file.type,
            data: base64
          });
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    });

    const fileData = await Promise.all(filePromises);
    return JSON.stringify(fileData);
  }

  /**
   * Get current wallet address from localStorage
   * @returns {string|null} Current wallet address
   */
  getCurrentWallet() {
    // Try different possible localStorage keys for wallet
    return localStorage.getItem('gcn_current_wallet') || 
           localStorage.getItem('currentWallet') || 
           localStorage.getItem('gcn_wallet_address') ||
           '1LVkyzYqPBYYhMEjxFm1dLXsFUox2gtdDr'; // Fallback to platform wallet for testing
  }

  /**
   * Check if user has a wallet
   * @returns {boolean} True if wallet exists
   */
  hasWallet() {
    return !!this.getCurrentWallet();
  }

  /**
   * Cache management
   */
  getFromCache(key) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    this.cache.delete(key);
    return null;
  }

  setCache(key, data, timeout = this.cacheTimeout) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });

    // Auto-expire cache entry
    setTimeout(() => {
      this.cache.delete(key);
    }, timeout);
  }

  clearCache() {
    this.cache.clear();
  }

  /**
   * Validate soul creation data
   * @param {Object} soulData - Soul data to validate
   * @returns {Object} Validation result
   */
  validateSoulData(soulData) {
    const errors = {};

    // Required fields
    if (!soulData.name?.trim()) {
      errors.name = 'Soul name is required';
    }

    if (!soulData.username?.trim()) {
      errors.username = 'Username is required';
    } else if (soulData.username.length < 3 || soulData.username.length > 20) {
      errors.username = 'Username must be 3-20 characters long';
    } else if (!/^[a-zA-Z0-9_]+$/.test(soulData.username)) {
      errors.username = 'Username can only contain letters, numbers, and underscores';
    }

    if (!soulData.description?.trim()) {
      errors.description = 'Description is required';
    }

    if (!soulData.personalityTraits || soulData.personalityTraits.length < 3) {
      errors.personalityTraits = 'At least 3 personality traits are required';
    }

    // Interaction price validation
    if (soulData.interactionPrice < 1 || soulData.interactionPrice > 1000) {
      errors.interactionPrice = 'Interaction price must be between 1 and 1000 GCN';
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors
    };
  }

  /**
   * Calculate estimated creation cost
   * @param {Object} soulData - Soul data
   * @returns {number} Estimated cost in GCN
   */
  calculateCreationCost(soulData) {
    let baseCost = 50; // Basic soul creation
    let storageCost = 25; // Blockchain storage
    let avatarCost = 25; // 3D avatar

    return baseCost + storageCost + avatarCost;
  }
}

// Create and export singleton instance
const digitalSoulService = new DigitalSoulService();
export default digitalSoulService;